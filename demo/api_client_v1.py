import requests
import logging
from typing import Dict, Any, Optional

class AnalyticsClient:
    """A production-grade client for the Analytics API v1."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.logger = logging.getLogger("AnalyticsClient")

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch user profile information from the API."""
        url = f"{self.base_url}/users/{user_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

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

    def legacy_authenticate(self, user: str, passw: str) -> str:
        """DEPRECATED: Old authentication method using basic credentials."""
        url = f"{self.base_url}/auth/legacy"
        resp = self.session.post(url, json={"u": user, "p": passw})
        return resp.json().get("token")
