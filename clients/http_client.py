import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings


class HttpClient:
    def __init__(self):
        self.session = requests.Session()

        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, headers: dict = None, params: dict = None):
        return self.session.get(
            url, headers=headers, params=params, timeout=settings.HTTP_TIMEOUT
        )

    def post(self, url: str, headers: dict = None, json: dict = None):
        return self.session.post(
            url, headers=headers, json=json, timeout=settings.HTTP_TIMEOUT
        )


# Global instance
http_client = HttpClient()
