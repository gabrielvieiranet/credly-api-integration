import json
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from src.config.settings import settings
from src.utils.logger import logger


class SSMClient:
    def __init__(self):
        self.client = boto3.client(
            "ssm",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.LOCALSTACK_ENDPOINT
            if settings.ENV == "DEV"
            else None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def get_parameter(
        self, name: str, default: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Retrieves a JSON parameter from SSM.
        Returns 'default' if parameter does not exist.
        """
        try:
            response = self.client.get_parameter(Name=name, WithDecryption=False)
            value = response["Parameter"]["Value"]
            return json.loads(value)
        except self.client.exceptions.ParameterNotFound:
            logger.info(f"Parameter {name} not found. Returning default.")
            return default or {}
        except Exception as e:
            logger.error(f"Error getting parameter {name}: {e}")
            raise

    def put_parameter(self, name: str, value: Dict[str, Any], description: str = ""):
        """
        Saves a JSON parameter to SSM.
        Always overwrites (Overwrite=True).
        ParamierType is 'String' (we store JSON string).
        """
        try:
            value_str = json.dumps(value)
            self.client.put_parameter(
                Name=name,
                Value=value_str,
                Type="String",
                Overwrite=True,
                Description=description,
            )
            logger.info(f"Successfully updated parameter {name}")
        except Exception as e:
            logger.error(f"Error updating parameter {name}: {e}")
            raise


ssm_client = SSMClient()
