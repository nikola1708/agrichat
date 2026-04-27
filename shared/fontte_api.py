"""
Fonnte WhatsApp API integration
"""
import requests
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FontneAPIClient:
    """Client for Fonnte WhatsApp API"""

    def __init__(self):
        self.api_token = os.getenv("FONNTE_API_TOKEN")
        self.device_id = os.getenv("FONNTE_DEVICE_ID")
        self.base_url = "https://api.fonnte.com"
        
        if not self.api_token or not self.device_id:
            logger.warning("Fonnte API credentials not configured")
        
        self.headers = {
            "Authorization": self.api_token or "",
            "Content-Type": "application/json"
        }

    def send_text_message(self, phone: str, message: str) -> Dict[str, Any]:
        """Send text message via Fonnte"""
        try:
            if not self.api_token:
                logger.warning("Fonnte API token not configured")
                return {"status": "error", "message": "API token not configured"}
            
            payload = {
                "target": phone,
                "message": message,
                "device": self.device_id,
                "delay": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/send",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error sending message to {phone}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def send_image_message(self, phone: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        """Send image message via Fonnte"""
        try:
            if not self.api_token:
                return {"status": "error", "message": "API token not configured"}
            
            payload = {
                "target": phone,
                "image": image_url,
                "caption": caption,
                "device": self.device_id
            }
            
            response = requests.post(
                f"{self.base_url}/send",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error sending image to {phone}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def send_location_message(self, phone: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Send location message via Fonnte"""
        try:
            if not self.api_token:
                return {"status": "error", "message": "API token not configured"}
            
            payload = {
                "target": phone,
                "latitude": latitude,
                "longitude": longitude,
                "device": self.device_id
            }
            
            response = requests.post(
                f"{self.base_url}/send",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error sending location to {phone}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def validate_webhook_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate incoming webhook payload from Fonnte"""
        try:
            # Check required fields
            required_fields = ["sender", "type", "time"]
            return all(field in payload for field in required_fields)
        except Exception as e:
            logger.error(f"Webhook validation error: {str(e)}")
            return False
