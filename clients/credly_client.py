from typing import Any, Dict, Generator

from auth.token_provider import get_token_provider
from clients.http_client import http_client
from config.settings import settings
from utils.logger import logger
from utils.observability import observability


class CredlyClient:
    def __init__(self):
        self.auth_provider = get_token_provider()
        self.base_url = settings.CREDLY_BASE_URL
        self.org_id = settings.CREDLY_ORG_ID

    def get_badges(
        self, params: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetches badges using high_volume_issued_badge_search.
        """
        endpoint = f"organizations/{self.org_id}/high_volume_issued_badge_search"
        yield from self._paginate(endpoint, params)

    def get_templates(
        self, params: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetches badge templates.
        """
        endpoint = f"organizations/{self.org_id}/badge_templates"
        yield from self._paginate(endpoint, params)

    def _paginate(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        url = f"{self.base_url}/{endpoint}"
        current_params = params or {}

        while url:
            headers = self.auth_provider.get_auth_headers()
            headers["Content-Type"] = "application/json"

            try:
                observability.increment_metric("credly_api_requests")
                response = http_client.get(url, headers=headers, params=current_params)
                response.raise_for_status()

                data = response.json()

                # Credly API response structure: { "data": [...], "metadata": { "next_page_url": "..." } }
                items = data.get("data", [])
                if items:
                    yield items

                url = data.get("metadata", {}).get("next_page_url")

                # Clear params for subsequent pages as they are in the URL
                if url:
                    current_params = {}

            except Exception as e:
                logger.error(f"Error fetching from Credly: {str(e)}")
                raise e


credly_client = CredlyClient()
