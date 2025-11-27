#!/bin/bash

ENDPOINT_URL="http://localhost:4566"
BUCKET_NAME="my-datalake-bucket"

echo "Listing files in s3://$BUCKET_NAME..."
aws --endpoint-url=$ENDPOINT_URL s3 ls s3://$BUCKET_NAME --recursive

echo ""
echo "To download and view a specific file:"
echo "aws --endpoint-url=$ENDPOINT_URL s3 cp s3://$BUCKET_NAME/<KEY> -"

# Optional: automatically show the last file if any
LAST_FILE=$(aws --endpoint-url=$ENDPOINT_URL s3 ls s3://$BUCKET_NAME --recursive | sort | tail -n 1 | awk '{print $4}')

if [ -n "$LAST_FILE" ]; then
    echo ""
    echo "--- Content of latest file: $LAST_FILE ---"
    aws --endpoint-url=$ENDPOINT_URL s3 cp s3://$BUCKET_NAME/$LAST_FILE - | head -n 20
    echo ""
    echo "(Showing first 20 lines)"
fi
