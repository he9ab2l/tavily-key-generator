"""
Cloudflare Email Worker 邮箱后端
"""
import random
import string
import requests
from config import EMAIL_API_URL, EMAIL_API_TOKEN, EMAIL_DOMAIN, EMAIL_PREFIX
from .base import EmailProvider
import logger as log


class CloudflareEmailProvider(EmailProvider):
    """基于 Cloudflare Email Worker 的邮箱服务"""

    def __init__(self):
        self.api_url = EMAIL_API_URL
        self.headers = {"Authorization": f"Bearer {EMAIL_API_TOKEN}"}

    def create_email(self, prefix=None):
        """生成 catch-all 邮箱地址"""
        if prefix is None:
            prefix = EMAIL_PREFIX
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}-{suffix}@{EMAIL_DOMAIN}"

    def get_messages(self, address):
        """通过 Cloudflare Email Worker API 获取邮件"""
        try:
            # 兼容两种 API 风格
            resp = requests.get(
                f"{self.api_url}/api/emails",
                params={"mailbox": address},
                headers=self.headers,
                timeout=15,
            )
            if resp.status_code == 404:
                resp = requests.get(
                    f"{self.api_url}/messages",
                    params={"address": address},
                    headers=self.headers,
                    timeout=15,
                )

            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict):
                data = data.get("messages", [])

            messages = []
            for msg in data:
                msg_id = msg.get("id")
                if msg_id:
                    try:
                        detail = requests.get(
                            f"{self.api_url}/api/email/{msg_id}",
                            headers=self.headers,
                            timeout=15,
                        )
                        if detail.status_code == 200:
                            d = detail.json()
                            messages.append({
                                "subject": d.get("subject", ""),
                                "html": d.get("html_content", ""),
                                "text": d.get("content", "") or d.get("preview", ""),
                            })
                            continue
                    except Exception:
                        pass
                messages.append({
                    "subject": msg.get("subject", ""),
                    "html": msg.get("html", "") or msg.get("html_content", ""),
                    "text": msg.get("text", "") or msg.get("preview", ""),
                })
            return messages
        except Exception as e:
            log.error(f"[cloudflare] get messages failed: {e}")
            return []

    def cleanup(self, address):
        """清理邮箱"""
        try:
            resp = requests.delete(
                f"{self.api_url}/messages",
                params={"address": address},
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            log.debug(f"[cloudflare] cleaned up: {address}")
        except Exception as e:
            log.warn(f"[cloudflare] cleanup failed: {e}")
