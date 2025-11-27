import os
import sys
import time

from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Setup Environment
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

from handlers.credly_ingestion_handler import lambda_handler
from scripts.run_lambda_local import setup_local_secret


def run_test(load_type, mode, page_limit=2):
    print(f"\n--- Running Test: {load_type} / {mode} (page_limit={page_limit}) ---")
    event = {"load_type": load_type, "mode": mode, "page_limit": page_limit}
    try:
        start_time = time.time()
        response = lambda_handler(event, None)
        duration = time.time() - start_time
        print(f"Status: {response['statusCode']}")
        print(f"Duration: {duration:.2f}s")
        print(f"Message: {response['body']['message']}")
    except Exception as e:
        print(f"FAILED: {e}")


def main():
    print("DEBUG: Starting main()")
    setup_local_secret()

    scenarios = [
        ("badges", "historical"),
        ("badges", "daily"),
        ("templates", "historical"),
        ("templates", "daily"),
    ]

    for load_type, mode in scenarios:
        run_test(load_type, mode)
        time.sleep(1)  # Brief pause


if __name__ == "__main__":
    main()
