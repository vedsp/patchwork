import requests
import logging
import time
from typing import Dict, Any, Optional, List

class AnalyticsClient:
    """A production-grade client for the Analytics API v2."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.logger = logging.getLogger("AnalyticsClient")

    def get_user_profile(self, user_id: str, retries: int = 3) -> Dict[str, Any]:
        """
        Fetch user profile with exponential backoff retry logic.
        MODIFIED: Added robust retry handling and logging.
        """
        url = f"{self.base_url}/users/{user_id}"
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=5)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        return {}

    def create_event(self, event_type: str, metadata: Dict[str, Any]) -> bool:
        """Log a new event to the analytics stream."""
        url = f"{self.base_url}/events"
        payload = {"type": event_type, "data": metadata}
        response = self.session.post(url, json=payload)
        return response.status_code == 201

    def delete_data_request(self, request_id: str) -> None:
        """Submit a request to delete user data (GDPR compliance)."""
        url = f"{self.base_url}/requests/{request_id}"
        self.session.delete(url).raise_for_status()

    def query_historical_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        ADDED: New analytical query capability for historical ranges.
        """
        url = f"{self.base_url}/query"
        params = {"from": start_date, "to": end_date}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get("results", [])

    # DELETED: legacy_authenticate has been removed for security.
