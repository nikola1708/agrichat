"""
Cosmos DB operations for farmer profiles and interaction history
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os

logger = logging.getLogger(__name__)


class CosmosDBManager:
    """Manage Cosmos DB operations for TaniWise Bot"""

    def __init__(self):
        self.connection_string = os.getenv("COSMOS_CONNECTION_STRING")
        self.database_id = os.getenv("COSMOS_DATABASE_ID", "taniwise-prod")
        
        if not self.connection_string:
            logger.warning("COSMOS_CONNECTION_STRING not configured")
            self.client = None
            self.db = None
            return

        try:
            self.client = CosmosClient.from_connection_string(self.connection_string)
            self.db = self.client.get_database_client(self.database_id)
            logger.info(f"Connected to Cosmos DB: {self.database_id}")
        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {str(e)}")
            self.client = None
            self.db = None

    def _ensure_container(self, container_name: str, partition_key: str) -> Optional[Any]:
        """Ensure container exists, create if not"""
        if not self.db:
            return None

        try:
            return self.db.get_container_client(container_name)
        except exceptions.CosmosResourceNotFoundError:
            try:
                logger.info(f"Creating container: {container_name}")
                return self.db.create_container(
                    id=container_name,
                    partition_key=PartitionKey(path=f"/{partition_key}")
                )
            except Exception as e:
                logger.error(f"Failed to create container {container_name}: {str(e)}")
                return None

    def save_farmer_profile(self, phone: str, profile: Dict[str, Any]) -> bool:
        """Save farmer profile to Cosmos DB"""
        try:
            container = self._ensure_container("petani", "phone")
            if not container:
                return False

            profile["id"] = phone
            profile["phone"] = phone
            profile["updated_at"] = datetime.utcnow().isoformat()

            container.upsert_item(profile)
            logger.info(f"Saved farmer profile: {phone}")
            return True
        except Exception as e:
            logger.error(f"Error saving farmer profile: {str(e)}")
            return False

    def get_farmer_profile(self, phone: str) -> Optional[Dict[str, Any]]:
        """Retrieve farmer profile from Cosmos DB"""
        try:
            container = self._ensure_container("petani", "phone")
            if not container:
                return None

            item = container.read_item(item=phone, partition_key=phone)
            logger.info(f"Retrieved farmer profile: {phone}")
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.info(f"No profile found for: {phone}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving farmer profile: {str(e)}")
            return None

    def save_diagnosis_history(self, phone: str, diagnosis: Dict[str, Any]) -> bool:
        """Save plant diagnosis history"""
        try:
            container = self._ensure_container("diagnosis_history", "phone")
            if not container:
                return False

            diagnosis["id"] = f"{phone}_{datetime.utcnow().timestamp()}"
            diagnosis["phone"] = phone
            diagnosis["timestamp"] = datetime.utcnow().isoformat()

            container.create_item(diagnosis)
            logger.info(f"Saved diagnosis for: {phone}")
            return True
        except Exception as e:
            logger.error(f"Error saving diagnosis: {str(e)}")
            return False

    def save_weather_alert(self, phone: str, alert: Dict[str, Any]) -> bool:
        """Save weather alert history"""
        try:
            container = self._ensure_container("weather_alerts", "phone")
            if not container:
                return False

            alert["id"] = f"{phone}_{datetime.utcnow().timestamp()}"
            alert["phone"] = phone
            alert["timestamp"] = datetime.utcnow().isoformat()

            container.create_item(alert)
            logger.info(f"Saved weather alert for: {phone}")
            return True
        except Exception as e:
            logger.error(f"Error saving weather alert: {str(e)}")
            return False

    def get_interaction_history(self, phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get farmer interaction history"""
        try:
            container = self._ensure_container("diagnosis_history", "phone")
            if not container:
                return []

            query = "SELECT TOP @limit * FROM c WHERE c.phone = @phone ORDER BY c.timestamp DESC"
            items = list(container.query_items(
                query=query,
                parameters=[
                    {"name": "@phone", "value": phone},
                    {"name": "@limit", "value": limit}
                ]
            ))
            logger.info(f"Retrieved {len(items)} interaction records for: {phone}")
            return items
        except Exception as e:
            logger.error(f"Error retrieving interaction history: {str(e)}")
            return []
