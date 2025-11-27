import base64
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests

from clients.secrets_manager import secrets_client
from config.settings import settings
from utils.logger import logger


class CredlyAuthProvider(ABC):
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Returns the authorization headers."""
        pass


class StaticTokenProvider(CredlyAuthProvider):
    """
    For DEV/HOM environments.
    Fetches a static token from Secrets Manager and caches it indefinitely.
    """

    def __init__(self):
        self._token: Optional[str] = None

    def get_auth_headers(self) -> Dict[str, str]:
        if not self._token:
            logger.info("Fetching static token from Secrets Manager")
            secrets = secrets_client.get_secret(settings.SECRETS_MANAGER_KEY)
            self._token = secrets.get("api_token")

            if not self._token:
                raise ValueError("api_token not found in secrets")

        # Credly expects Basic Auth for the Organization Token (token as username, empty password)
        auth_str = f"{self._token}:"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        return {"Authorization": f"Basic {b64_auth}"}


class OAuth2Provider(CredlyAuthProvider):
    """
    For PROD environment.
    Implements OAuth 2.0 Client Credentials flow.
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._buffer_seconds = 60

    def get_auth_headers(self) -> Dict[str, str]:
        current_time = time.time()
        if self._access_token and current_time < (
            self._token_expires_at - self._buffer_seconds
        ):
            return {"Authorization": f"Bearer {self._access_token}"}

        logger.info("OAuth token expired or missing. Refreshing...")
        self._refresh_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _refresh_token(self):
        secrets = secrets_client.get_secret(settings.SECRETS_MANAGER_KEY)
        client_id = secrets.get("client_id")
        client_secret = secrets.get("client_secret")
        token_url = secrets.get("token_url", "https://api.credly.com/v1/oauth/token")

        if not all([client_id, client_secret]):
            raise ValueError("Missing OAuth credentials in secrets")

        # Credly typically expects Basic Auth for the client credentials in the token request
        auth_str = f"{client_id}:{client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        try:
            response = requests.post(
                token_url,
                headers={
                    "Authorization": f"Basic {b64_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
                timeout=settings.HTTP_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["data"][
                "token"
            ]  # Credly response structure check needed
            # Assuming standard OAuth response or Credly specific.
            # Credly docs: POST /v1/oauth/token -> { "data": { "token": "...", "refresh_token": "..." } }
            # Note: Credly might not return 'expires_in' in all responses, or it might be in a different field.
            # If not present, we might need a default or check 'exp' in JWT if it is one.
            # For safety, let's assume a default short life if not provided, or parse if possible.
            # Here assuming 24h default if not found.
            expires_in = data.get("data", {}).get("expires_in", 86400)

            self._token_expires_at = time.time() + expires_in

            logger.info("Successfully refreshed OAuth token")
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {str(e)}")
            raise


def get_token_provider() -> CredlyAuthProvider:
    if settings.ENV == "PROD":
        return OAuth2Provider()
    else:
        return StaticTokenProvider()
