import boto3
from botocore.exceptions import ClientError

from src.config.settings import settings
from src.utils.logger import logger


class DynamoDBClient:
    def __init__(self):
        self.table_name = settings.METADATA_TABLE_NAME
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.LOCALSTACK_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.table = self.dynamodb.Table(self.table_name)

    def get_metadata(self, table_name: str) -> dict:
        """
        Retrieve metadata for a specific table.
        """
        try:
            response = self.table.get_item(Key={"table_name": table_name})
            return response.get("Item", {})
        except ClientError as e:
            logger.error(f"Failed to get metadata for {table_name}: {e}")
            return {}

    def update_metadata(self, table_name: str, data: dict):
        """
        Update metadata for a specific table.
        """
        try:
            # Add table_name to data as partition key
            item = {"table_name": table_name, **data}
            self.table.put_item(Item=item)
            logger.info(f"Updated metadata for {table_name}")
        except ClientError as e:
            logger.error(f"Failed to update metadata for {table_name}: {e}")
            raise e


dynamodb_client = DynamoDBClient()
