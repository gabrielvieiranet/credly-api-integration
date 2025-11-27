import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Setup Environment for Local Execution BEFORE importing app modules
os.environ["ENV"] = "DEV"
os.environ["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_SESSION_TOKEN"] = ""
os.environ["SECRETS_MANAGER_KEY"] = os.getenv(
    "SECRETS_MANAGER_KEY", "my-app/credentials"
)
os.environ["LOCALSTACK_ENDPOINT"] = os.getenv(
    "LOCALSTACK_ENDPOINT", "http://localhost:4566"
)
os.environ["CREDLY_BASE_URL"] = "https://api.credly.com/v1"
os.environ["CREDLY_ORG_ID"] = os.getenv("CREDLY_ORG_ID", "")
os.environ["S3_BUCKET_NAME"] = os.getenv("S3_BUCKET_NAME", "my-datalake-bucket")

# Import handler AFTER env vars are set so settings.py picks them up
from handlers.credly_ingestion_handler import lambda_handler


def setup_local_secret():
    """
    Ensures the secret exists in LocalStack with the token from .env
    """
    token = os.getenv("CREDLY_API_TOKEN")
    print(f"DEBUG: CREDLY_API_TOKEN present: {bool(token)}")
    if not token:
        print(
            "WARNING: CREDLY_API_TOKEN not found in .env. Secret might be missing or empty."
        )
        return

    secret_name = os.environ["SECRETS_MANAGER_KEY"]
    endpoint = os.environ["LOCALSTACK_ENDPOINT"]

    client = boto3.client(
        "secretsmanager",
        region_name=os.environ["AWS_REGION"],
        endpoint_url=endpoint,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    secret_string = json.dumps(
        {"api_token": token, "client_id": "dev_id", "client_secret": "dev_secret"}
    )

    try:
        print(f"Updating secret {secret_name} in LocalStack...")
        client.put_secret_value(SecretId=secret_name, SecretString=secret_string)
    except client.exceptions.ResourceNotFoundException:
        print(f"Secret {secret_name} not found. Creating it...")
        client.create_secret(Name=secret_name, SecretString=secret_string)
    except Exception as e:
        print(f"Failed to update secret: {e}")


def run():
    setup_local_secret()
    print("Running Lambda Locally...")

    # Event Payload
    event = {
        "load_type": "badges",
        "mode": "historical",
        "limit": 50,  # Sample limit
    }

    try:
        response = lambda_handler(event, None)
        print("\nLambda Output:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"\nLambda Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if ORG_ID is set
    if not os.environ["CREDLY_ORG_ID"]:
        print(
            "WARNING: CREDLY_ORG_ID env var is not set. API calls might fail if not using a valid ID."
        )
        # You might want to hardcode one for testing or ask user to export it

    run()
