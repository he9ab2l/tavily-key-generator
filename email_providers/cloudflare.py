#!/usr/bin/env python3
"""
Cloudflare Email Worker 邮箱后端
"""
import random
import string
import requests
from config import EMAIL_API_URL, EMAIL_API_TOKEN, EMAIL_DOMAIN, EMAIL_PREFIX
from .base import EmailProvider


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
            # 兼容两种 API 风格：
            # 1) 临时邮箱系统: GET /api/emails?mailbox=完整地址
            # 2) 标准 Worker: GET /messages?address=xxx
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

            # 临时邮箱系统的列表只有摘要，需要逐封获取详情（含 html_content）
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
                # 回退：使用列表中的字段
                messages.append({
                    "subject": msg.get("subject", ""),
                    "html": msg.get("html", "") or msg.get("html_content", ""),
                    "text": msg.get("text", "") or msg.get("preview", ""),
                })
            return messages
        except Exception as e:
            print(f"❌ 获取邮件失败: {e}")
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
            print(f"🗑️ 已清理 {address} 的邮件")
        except Exception as e:
            print(f"⚠️ 清理邮件失败: {e}")
