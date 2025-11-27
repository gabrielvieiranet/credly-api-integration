#!/bin/bash

ENDPOINT_URL="http://localhost:4566"
BUCKET_NAME="my-datalake-bucket"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/reports"

# NOTE: This script cleans DATA (S3 objects, local reports).
# To clean INFRASTRUCTURE (buckets, tables), use setup_infra.sh (which recreates them)
# or manually delete via AWS CLI.

echo "Cleaning S3 bucket s3://$BUCKET_NAME..."
aws --endpoint-url=$ENDPOINT_URL s3 rm s3://$BUCKET_NAME --recursive

if [ -d "$REPORTS_DIR" ]; then
    echo "Cleaning reports directory..."
    rm -f "$REPORTS_DIR"/*.csv
    echo "Reports deleted."
else
    echo "Reports directory not found."
fi

echo "Cleanup complete."
