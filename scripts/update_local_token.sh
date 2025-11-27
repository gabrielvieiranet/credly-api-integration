#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <REAL_TOKEN>"
    exit 1
fi

TOKEN=$1
ENDPOINT_URL="http://localhost:4566"

echo "Updating secret in LocalStack..."
aws --endpoint-url=$ENDPOINT_URL secretsmanager put-secret-value \
    --secret-id my-app/credentials \
    --secret-string "{\"api_token\": \"$TOKEN\", \"client_id\": \"dev_id\", \"client_secret\": \"dev_secret\"}"

echo "Secret updated successfully."
