import os

import boto3
from dotenv import load_dotenv

load_dotenv()

ENDPOINT_URL = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "my-datalake-bucket")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)


def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def get_all_objects(prefix):
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix)

    objects = []
    for page in pages:
        if "Contents" in page:
            objects.extend(page["Contents"])
    return objects


def process_table(table_name):
    print(f"Processing table: {table_name}")
    prefix = f"raw/{table_name}/"
    objects = get_all_objects(prefix)

    if not objects:
        print(f"No data found for {table_name}")
        return

    import io

    import pandas as pd

    all_dfs = []

    for obj in objects:
        key = obj["Key"]
        if not key.endswith(".parquet"):
            continue

        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response["Body"].read()
        try:
            df = pd.read_parquet(io.BytesIO(content))
            all_dfs.append(df)
        except Exception as e:
            print(f"Error reading Parquet from {key}: {e}")

    if not all_dfs:
        return

    final_df = pd.concat(all_dfs, ignore_index=True)

    output_file = os.path.join(REPORTS_DIR, f"{table_name}.csv")
    final_df.to_csv(output_file, index=False)

    print(f"Generated report: {output_file} ({len(final_df)} records)")


def main():
    ensure_reports_dir()

    tables = ["badges_emitidas", "badges_templates", "badges_templates_activities"]

    print(f"Generating reports from s3://{BUCKET_NAME}...")

    for table in tables:
        process_table(table)

    print("\nDone.")


if __name__ == "__main__":
    main()
