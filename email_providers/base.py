#!/usr/bin/env python3
"""
邮箱后端抽象基类
"""
import re
import time
from abc import ABC, abstractmethod
from config import EMAIL_CHECK_INTERVAL, MAX_EMAIL_WAIT_TIME


class EmailProvider(ABC):
    """邮箱服务提供商抽象基类"""

    @abstractmethod
    def create_email(self, prefix=None):
        """创建/生成邮箱地址，返回地址字符串"""
        pass

    @abstractmethod
    def get_messages(self, address):
        """获取邮件列表，每项至少含 subject, html, text"""
        pass

    def cleanup(self, address):
        """清理邮件（可选，子类可覆盖）"""
        pass

    def find_verification_link(self, messages):
        """从邮件列表中查找 Tavily 验证链接"""
        for msg in messages:
            subject = (msg.get("subject") or "").lower()
            if "verify" not in subject and "tavily" not in subject:
                continue

            html = msg.get("html") or ""
            text = msg.get("text") or ""

            # 优先从 HTML href 属性中提取链接
            links = re.findall(r'href="(https?://[^"]+)"', html)
            if not links:
                links = re.findall(r'https?://[^\s"<>\']+', text)

            # 过滤无关链接
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
        """轮询等待验证邮件，返回验证链接"""
        if interval is None:
            interval = EMAIL_CHECK_INTERVAL
        if max_wait is None:
            max_wait = MAX_EMAIL_WAIT_TIME

        max_retries = max_wait // interval
        print(f"📧 开始检查验证邮件，目标: {address}")
        print(f"⏳ 最大等待 {max_wait} 秒，每 {interval} 秒检查一次")

        for attempt in range(max_retries):
            print(f"🔄 第 {attempt + 1}/{max_retries} 次检查...")

            messages = self.get_messages(address)
            if messages:
                print(f"📋 找到 {len(messages)} 封邮件")
                link = self.find_verification_link(messages)
                if link:
                    print(f"✅ 找到验证链接: {link}")
                    return link
                else:
                    print("⚠️ 邮件中未找到验证链接")
            else:
                print("📭 暂无邮件")

            if attempt < max_retries - 1:
                print(f"⏳ 等待 {interval} 秒后重试...")
                time.sleep(interval)

        print("❌ 超时，未找到验证邮件")
        return None
