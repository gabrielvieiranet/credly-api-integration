import os
import sys
import time

from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Setup Environment BEFORE imports to ensure clients get correct config
os.environ["ENV"] = "DEV"
os.environ["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
if "AWS_SESSION_TOKEN" in os.environ:
    del os.environ["AWS_SESSION_TOKEN"]
os.environ["SECRETS_MANAGER_KEY"] = os.getenv(
    "SECRETS_MANAGER_KEY", "my-app/credentials"
)
os.environ["LOCALSTACK_ENDPOINT"] = os.getenv(
    "LOCALSTACK_ENDPOINT", "http://localhost:4566"
)
os.environ["CREDLY_BASE_URL"] = "https://api.credly.com/v1"
os.environ["CREDLY_ORG_ID"] = os.getenv("CREDLY_ORG_ID", "")
os.environ["S3_BUCKET_NAME"] = os.getenv("S3_BUCKET_NAME", "my-datalake-bucket")
os.environ["METADATA_TABLE_NAME"] = os.getenv(
    "METADATA_TABLE_NAME", "credly-ingestion-metadata-dev"
)

from handlers.credly_ingestion_handler import lambda_handler
from scripts.run_lambda_local import setup_local_secret


def run_test(load_type, mode, max_pages=2):
    """Simulates Step Functions pagination locally."""
    print(f"\n--- Running Test: {load_type} / {mode} (max_pages={max_pages}) ---")

    page = None
    pages_processed = 0
    total_records = 0

    while True:
        event = {"load_type": load_type, "mode": mode}
        if page:
            event["page"] = page

        try:
            start_time = time.time()
            response = lambda_handler(event, None)
            duration = time.time() - start_time

            body = response.get("body", {})
            records = body.get("records_processed", 0)
            next_page = body.get("next_page")

            pages_processed += 1
            total_records += records

            print(
                f"  Page {pages_processed}: {records} records, next_page={'Yes' if next_page else 'No'}"
            )

            # Check continuation conditions
            if not next_page:
                print(
                    f"✓ Complete: {total_records} total records in {pages_processed} pages"
                )
                break

            if pages_processed >= max_pages:
                print(
                    f"⚠ Stopped at {max_pages} pages (local limit). Next page available: {next_page[:50]}..."
                )
                break

            # Continue to next page
            page = next_page
            time.sleep(0.5)  # Brief pause between pages

        except Exception as e:
            print(f"✗ FAILED on page {pages_processed + 1}: {e}")
            break


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
        time.sleep(1)  # Brief pause between scenarios


if __name__ == "__main__":
    main()
