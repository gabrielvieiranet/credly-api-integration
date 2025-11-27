import os
from typing import Optional


class Settings:
    """
    Centralized configuration management.
    Reads from environment variables.
    """

    @property
    def ENV(self) -> str:
        return os.getenv("ENV", "DEV").upper()

    @property
    def AWS_REGION(self) -> str:
        return os.getenv("AWS_REGION", "us-east-1")

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def SECRETS_MANAGER_KEY(self) -> str:
        """Key name in Secrets Manager where credentials are stored."""
        return os.getenv("SECRETS_MANAGER_KEY", "my-app/credentials")

    @property
    def LOCALSTACK_ENDPOINT(self) -> Optional[str]:
        """Endpoint for LocalStack, used for local development."""
        return os.getenv("LOCALSTACK_ENDPOINT")

    @property
    def HTTP_TIMEOUT(self) -> int:
        return int(os.getenv("HTTP_TIMEOUT", "30"))

    @property
    def MAX_RETRIES(self) -> int:
        return int(os.getenv("MAX_RETRIES", "3"))

    # Credly Specifics
    @property
    def CREDLY_BASE_URL(self) -> str:
        return os.getenv("CREDLY_BASE_URL", "https://api.credly.com/v1")

    @property
    def CREDLY_ORG_ID(self) -> str:
        return os.getenv("CREDLY_ORG_ID", "")

    @property
    def S3_BUCKET_NAME(self) -> str:
        return os.getenv("S3_BUCKET_NAME", "my-datalake-bucket")


settings = Settings()
