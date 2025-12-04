#!/usr/bin/env python3
"""
Simulates Step Functions execution for daily badges ingestion.
This script mimics the Step Functions pagination loop locally.
"""

import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Add project root and app directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "app"))

load_dotenv()

# Setup Environment BEFORE imports
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

from lambda_function import lambda_handler

from scripts.run_lambda_local import setup_local_secret


def simulate_step_function(load_type: str, mode: str, max_pages: int = 2):
    """
    Simulates Step Functions execution with pagination.

    This mimics the actual Step Functions definition:
    - ProcessPage -> CheckForNextPage -> PrepareContinuation (loop)
    """
    print(f"\n{'=' * 80}")
    print(f"Step Functions Simulation: {load_type} / {mode}")
    print(f"Max Pages (local limit): {max_pages}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")

    # Initial state
    state = {"load_type": load_type, "mode": mode}

    page_num = 0
    total_records = 0

    while True:
        page_num += 1
        print(f"\n--- Page {page_num} ---")

        # Prepare event (mimics PrepareContinuation state)
        event = {"load_type": state["load_type"], "mode": state["mode"]}
        if "page" in state:
            event["page"] = state["page"]

        print(
            f"Event: load_type={event['load_type']}, mode={event['mode']}, page={'Present' if 'page' in event else 'None'}"
        )

        try:
            # ProcessPage state (Lambda invocation)
            start_time = time.time()
            response = lambda_handler(event, None)
            duration = time.time() - start_time

            # Extract result
            if response.get("statusCode") != 200:
                print(f"✗ Lambda failed with status {response.get('statusCode')}")
                break

            body = response.get("body", {})
            records = body.get("records_processed", 0)
            next_page = body.get("next_page")

            total_records += records

            print(f"✓ Processed {records} records in {duration:.2f}s")
            print(f"  Next page: {'Yes' if next_page else 'No'}")

            # CheckForNextPage state
            if not next_page:
                print(f"\n{'=' * 80}")
                print(f"✓ Step Functions SUCCEEDED")
                print(f"Total records: {total_records}")
                print(f"Total pages: {page_num}")
                print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 80}\n")
                break

            # Check local limit
            if page_num >= max_pages:
                print(f"\n{'=' * 80}")
                print(f"⚠ Stopped at local limit ({max_pages} pages)")
                print(f"Total records so far: {total_records}")
                print(f"Next page URL: {next_page[:80]}...")
                print(f"{'=' * 80}\n")
                break

            # PrepareContinuation state (prepare for next iteration)
            state = {"load_type": load_type, "mode": mode, "page": next_page}

            time.sleep(0.5)  # Brief pause between pages

        except Exception as e:
            print(f"\n{'=' * 80}")
            print(f"✗ Step Functions FAILED")
            print(f"Error: {e}")
            print(f"{'=' * 80}\n")
            break


import argparse


def main():
    parser = argparse.ArgumentParser(description="Simulate Step Functions execution.")
    parser.add_argument(
        "--load-type",
        choices=["badges", "templates", "all"],
        default="all",
        help="Type of load to simulate (default: all)",
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "historical"],
        default="daily",
        help="Ingestion mode (default: daily)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=2,
        help="Maximum number of pages to process (default: 2)",
    )

    args = parser.parse_args()

    print("\n🚀 Step Functions Local Simulator")
    print("This script simulates Step Functions pagination loop\n")

    setup_local_secret()

    if args.load_type in ["badges", "all"]:
        simulate_step_function(
            load_type="badges",
            mode=args.mode,
            max_pages=args.max_pages,
        )

    if args.load_type in ["templates", "all"]:
        simulate_step_function(
            load_type="templates",
            mode=args.mode,
            max_pages=args.max_pages,
        )


if __name__ == "__main__":
    main()
