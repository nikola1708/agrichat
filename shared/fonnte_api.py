"""
Fonnte WhatsApp API client
"""
import logging
import requests
from typing import Optional, Dict, Any
import os
import json

logger = logging.getLogger(__name__)


class FontneAPIClient:
    """Client for Fonnte WhatsApp API"""

    def __init__(self):
        self.api_token = os.getenv("FONNTE_API_TOKEN")
        self.device_id = os.getenv("FONNTE_DEVICE_ID")
        self.base_url = "https://api.fonnte.com"

    def send_text_message(self, phone: str, message: str) -> bool:
        """Send text message via Fonnte"""
        if not self.api_token or not self.device_id:
            logger.warning("Fonnte API credentials not configured")
            return False

        try:
            url = f"{self.base_url}/send"
            headers = {
                "Authorization": self.api_token,
                "Content-Type": "application/json"
            }
            payload = {
                "target": phone,
                "message": message,
                "device": self.device_id
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Fonnte message: {str(e)}")
            return False

    def send_image_message(
        self,
        phone: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Send image message via Fonnte"""
        if not self.api_token or not self.device_id:
            logger.warning("Fonnte API credentials not configured")
            return False

        try:
            url = f"{self.base_url}/send"
            headers = {
                "Authorization": self.api_token,
                "Content-Type": "application/json"
            }
            payload = {
                "target": phone,
                "image": image_url,
                "caption": caption or "",
                "device": self.device_id
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Image sent successfully to {phone}")
                return True
            else:
                logger.error(f"Failed to send image: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Fonnte image: {str(e)}")
            return False

    def send_location_message(
        self,
        phone: str,
        latitude: float,
        longitude: float,
        label: Optional[str] = None
    ) -> bool:
        """Send location message via Fonnte"""
        if not self.api_token or not self.device_id:
            logger.warning("Fonnte API credentials not configured")
            return False

        try:
            url = f"{self.base_url}/send"
            headers = {
                "Authorization": self.api_token,
                "Content-Type": "application/json"
            }
            payload = {
                "target": phone,
                "latitude": latitude,
                "longitude": longitude,
                "label": label or "Lokasi",
                "device": self.device_id
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Location sent successfully to {phone}")
                return True
            else:
                logger.error(f"Failed to send location: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Fonnte location: {str(e)}")
            return False

    @staticmethod
    def validate_webhook_payload(payload: Dict[str, Any]) -> bool:
        """Validate incoming webhook payload from Fonnte"""
        required_fields = ["sender", "type"]
        
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field: {field}")
                return False

        valid_types = ["text", "image", "location", "file"]
        if payload.get("type") not in valid_types:
            logger.warning(f"Invalid message type: {payload.get('type')}")
            return False

        return True
