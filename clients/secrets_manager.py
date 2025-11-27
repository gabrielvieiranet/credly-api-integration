import json
import os
from typing import Any, Dict

import boto3

from config.settings import settings
from utils.logger import logger


class SecretsManagerClient:
    _instance = None
    _secrets_cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecretsManagerClient, cls).__new__(cls)
            ak = os.getenv("AWS_ACCESS_KEY_ID", "test")
            sk = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
            print(
                f"DEBUG: SecretsManagerClient using AK={ak}, SK={sk}, Endpoint={settings.LOCALSTACK_ENDPOINT}"
            )
            cls._instance._client = boto3.client(
                "secretsmanager",
                region_name=settings.AWS_REGION,
                endpoint_url=settings.LOCALSTACK_ENDPOINT,
                aws_access_key_id=ak,
                aws_secret_access_key=sk,
            )
        return cls._instance

    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieves a secret from AWS Secrets Manager.
        Implements simple in-memory caching to avoid repeated calls.
        """
        if secret_name in self._secrets_cache:
            logger.info(f"Cache hit for secret: {secret_name}")
            return self._secrets_cache[secret_name]

        logger.info(f"Cache miss for secret: {secret_name}. Fetching from AWS.")
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
            if "SecretString" in response:
                secret = json.loads(response["SecretString"])
                self._secrets_cache[secret_name] = secret
                return secret
            else:
                # Handle binary secrets if necessary, for now assume JSON string
                raise ValueError("Secret is not a string")
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
            raise e


secrets_client = SecretsManagerClient()
