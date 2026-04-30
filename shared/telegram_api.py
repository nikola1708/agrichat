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

    def _split_message(self, text: str, max_length: int = 4000) -> list:
        """
        Split a long message into multiple parts respecting Telegram's 4096 limit.
        Tries to split at newlines to keep formatting intact.
        """
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        for line in text.split("\n"):
            if len(current_part) + len(line) + 1 > max_length:
                if current_part:
                    parts.append(current_part.rstrip())
                    current_part = ""
                
                # If a single line is too long, force split it
                if len(line) > max_length:
                    # Split the long line into chunks
                    for i in range(0, len(line), max_length):
                        parts.append(line[i:i+max_length])
                else:
                    current_part = line
            else:
                if current_part:
                    current_part += "\n" + line
                else:
                    current_part = line
        
        if current_part:
            parts.append(current_part.rstrip())
        
        return parts

    def send_text_message(self, chat_id: str, message: str) -> bool:
        """
        Send a text message via Telegram.
        Automatically splits messages longer than 4000 chars into multiple messages.
        """
        if not self.api_url:
            logger.warning("Telegram bot token not configured")
            return False

        try:
            # Split message if it's too long
            message_parts = self._split_message(message, max_length=4000)
            
            if len(message_parts) > 1:
                logger.info(f"Message too long ({len(message)} chars), splitting into {len(message_parts)} parts")
            
            success = True
            for i, part in enumerate(message_parts):
                if len(part) > 4096:
                    logger.warning(f"Part {i+1} is still {len(part)} chars, truncating to 4096")
                    part = part[:4093] + "..."
                
                payload = {
                    "chat_id": chat_id,
                    "text": part,
                    "disable_web_page_preview": True,
                }
                
                response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
                response.raise_for_status()
                
                if i == 0:
                    logger.info(f"Telegram message sent successfully to chat {chat_id} ({len(message_parts)} part(s))")
            
            return success
            
        except requests.exceptions.RequestException as e:
            response = getattr(e, "response", None)
            if response is not None:
                logger.error(
                    "Error sending Telegram message to chat %s: %s | status=%s | body=%s",
                    chat_id,
                    str(e),
                    response.status_code,
                    response.text[:500],
                )
            else:
                logger.error(f"Error sending Telegram message to chat {chat_id}: {str(e)}")
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
