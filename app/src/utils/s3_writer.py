import datetime
import json
import os
from typing import Any, Dict, List

import boto3

from src.config.settings import settings
from src.utils.logger import logger


class S3Writer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(S3Writer, cls).__new__(cls)
            cls._instance._client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                endpoint_url=settings.LOCALSTACK_ENDPOINT,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            )
        return cls._instance

    def clear_partition(self, table_name: str, partition_date: datetime.date):
        """
        Deletes all objects in the partition to ensure overwrite.
        """
        anomesdia = partition_date.strftime("%Y%m%d")
        prefix = f"raw/{table_name}/anomesdia={anomesdia}/"

        try:
            # List objects
            paginator = self._client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=settings.S3_BUCKET_NAME, Prefix=prefix)

            objects_to_delete = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        objects_to_delete.append({"Key": obj["Key"]})

            if objects_to_delete:
                logger.info(f"Clearing {len(objects_to_delete)} objects from {prefix}")
                # Delete in batches of 1000 (S3 limit)
                for i in range(0, len(objects_to_delete), 1000):
                    batch = objects_to_delete[i : i + 1000]
                    self._client.delete_objects(
                        Bucket=settings.S3_BUCKET_NAME,
                        Delete={"Objects": batch, "Quiet": True},
                    )
        except Exception as e:
            logger.error(f"Failed to clear partition {prefix}: {str(e)}")
            # Don't raise, just log. Overwrite might fail or result in duplicates if this fails.

    def write_parquet(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        partition_date: datetime.date,
        part_number: int,
    ):
        """
        Writes a list of dicts to S3 as a Parquet file.
        """
        if not data:
            logger.info(f"No data to write for {table_name}")
            return

        import io

        import pandas as pd

        anomesdia = partition_date.strftime("%Y%m%d")
        # Use part number for filename
        filename = f"part-{part_number:05d}.parquet"
        key = f"raw/{table_name}/anomesdia={anomesdia}/{filename}"

        try:
            df = pd.DataFrame(data)
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)

            self._client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                Body=buffer.getvalue(),
                ContentType="application/x-parquet",
            )
            logger.info(
                f"Successfully wrote {len(data)} records to s3://{settings.S3_BUCKET_NAME}/{key}"
            )
        except Exception as e:
            logger.error(f"Failed to write to S3: {str(e)}")
            raise e


s3_writer = S3Writer()
