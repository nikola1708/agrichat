"""
Telegram Bot API client for sending messages and downloading files.
"""
import logging
import os
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class TelegramAPIClient:
    """Client for Telegram Bot API."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN environment variable not set")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def send_text_message(self, chat_id: str, message: str) -> bool:
        """Send a text message via Telegram."""
        if not self.api_url:
            logger.warning("Telegram bot token not configured")
            return False

        try:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "disable_web_page_preview": True,
            }
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Telegram message sent successfully to chat {chat_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    def get_file_path(self, file_id: str) -> Optional[str]:
        """Retrieve the Telegram file path for a file ID."""
        if not self.api_url:
            logger.warning("Telegram bot token not configured")
            return None

        try:
            response = requests.get(f"{self.api_url}/getFile", params={"file_id": file_id}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                return data["result"].get("file_path")
            logger.error(f"Telegram getFile failed: {data}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Telegram file path: {str(e)}")
            return None

    def get_file_url(self, file_path: str) -> Optional[str]:
        """Build the direct Telegram file URL from a file path."""
        if not self.bot_token:
            return None
        return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"

    @staticmethod
    def validate_webhook_payload(payload: Dict[str, Any]) -> bool:
        """Validate incoming Telegram webhook payload."""
        message = payload.get("message") or payload.get("edited_message")
        return isinstance(message, dict) and isinstance(message.get("chat"), dict)
