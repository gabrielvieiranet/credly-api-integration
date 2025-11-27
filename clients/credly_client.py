from typing import Any, Dict

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
        self, params: Dict[str, Any] = None, page_url: str = None
    ) -> tuple[list[Dict[str, Any]], str | None]:
        """
        Fetches a single page of badges.
        Returns: (items, next_page_url)
        """
        endpoint = f"organizations/{self.org_id}/high_volume_issued_badge_search"
        return self._fetch_page(endpoint, params, page_url)

    def get_templates(
        self, params: Dict[str, Any] = None, page_url: str = None
    ) -> tuple[list[Dict[str, Any]], str | None]:
        """
        Fetches a single page of templates.
        Returns: (items, next_page_url)
        """
        endpoint = f"organizations/{self.org_id}/badge_templates"
        return self._fetch_page(endpoint, params, page_url)

    def _fetch_page(
        self, endpoint: str, params: Dict[str, Any] = None, page_url: str = None
    ) -> tuple[list[Dict[str, Any]], str | None]:
        """
        Fetches a single page from the API.
        Returns: (items, next_page_url)
        """
        # Use provided page_url or construct from endpoint
        url = page_url or f"{self.base_url}/{endpoint}"
        current_params = {} if page_url else (params or {})

        headers = self.auth_provider.get_auth_headers()
        headers["Content-Type"] = "application/json"

        try:
            observability.increment_metric("credly_api_requests")
            response = http_client.get(url, headers=headers, params=current_params)
            response.raise_for_status()

            data = response.json()

            # Credly API response structure: { "data": [...], "metadata": { "next_page_url": "..." } }
            items = data.get("data", [])
            next_page_url = data.get("metadata", {}).get("next_page_url")

            # Ensure badge_format is always minimal in next_page_url
            if next_page_url and "badge_format=default" in next_page_url:
                next_page_url = next_page_url.replace(
                    "badge_format=default", "badge_format=minimal"
                )

            return items, next_page_url

        except Exception as e:
            logger.error(f"Error fetching from Credly: {str(e)}")
            raise e


credly_client = CredlyClient()
