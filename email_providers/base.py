"""
邮箱后端抽象基类
"""
import re
import time
from abc import ABC, abstractmethod
from config import EMAIL_CHECK_INTERVAL, MAX_EMAIL_WAIT_TIME
import logger as log


class EmailProvider(ABC):
    """邮箱服务提供商抽象基类"""

    @abstractmethod
    def create_email(self, prefix=None):
        """创建/生成邮箱地址, 返回地址字符串"""
        pass

    @abstractmethod
    def get_messages(self, address):
        """获取邮件列表, 每项至少含 subject, html, text"""
        pass

    def cleanup(self, address):
        """清理邮件 (可选)"""
        pass

    def find_verification_link(self, messages):
        """从邮件列表中查找 Tavily 验证链接"""
        for msg in messages:
            subject = (msg.get("subject") or "").lower()
            if "verify" not in subject and "tavily" not in subject:
                continue

            html = msg.get("html") or ""
            text = msg.get("text") or ""

            links = re.findall(r'href="(https?://[^"]+)"', html)
            if not links:
                links = re.findall(r'https?://[^\s"<>\']+', text)

            skip_patterns = [
                '.png', '.jpg', '.gif', '.css', '.js',
                'cdn.auth0.com', 'unsubscribe', 'privacy',
                'about:blank', 'auth0.com/#',
            ]
            for link in links:
                link_lower = link.lower()
                if any(p in link_lower for p in skip_patterns):
                    continue
                if "email-verification" in link_lower or "verify" in link_lower or "ticket=" in link_lower:
                    return link.rstrip('#')

        return None

    def check_for_verification_email(self, address, max_wait=None, interval=None):
        """轮询等待验证邮件, 返回验证链接"""
        if interval is None:
            interval = EMAIL_CHECK_INTERVAL
        if max_wait is None:
            max_wait = MAX_EMAIL_WAIT_TIME

        max_retries = max_wait // interval
        log.info(f"[email] checking: {address} (max {max_wait}s)")

        for attempt in range(max_retries):
            log.debug(f"[email] poll {attempt + 1}/{max_retries}...")

            messages = self.get_messages(address)
            if messages:
                log.info(f"[email] found {len(messages)} message(s)")
                link = self.find_verification_link(messages)
                if link:
                    log.success(f"[email] verification link found")
                    return link
                else:
                    log.warn("[email] no verification link in messages")
            else:
                log.debug("[email] no messages yet")

            if attempt < max_retries - 1:
                time.sleep(interval)

        log.error("[email] timeout, no verification email")
        return None
