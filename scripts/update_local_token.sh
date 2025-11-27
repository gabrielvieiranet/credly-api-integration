#!/bin/bash

# Load .env if exists
if [ -f "$(dirname "$0")/../.env" ]; then
    export $(grep -v '^#' "$(dirname "$0")/../.env" | xargs)
fi

TOKEN=${1:-$CREDLY_API_TOKEN}

if [ -z "$TOKEN" ]; then
    echo "Usage: $0 <REAL_TOKEN> or set CREDLY_API_TOKEN env var"
    exit 1
fi
ENDPOINT_URL="http://localhost:4566"

# Disable proxy for LocalStack calls (prevents 502 errors on Linux)
export NO_PROXY="localhost,127.0.0.1"
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy

echo "Updating secret in LocalStack..."
aws --endpoint-url=$ENDPOINT_URL secretsmanager put-secret-value \
    --secret-id my-app/credentials \
    --secret-string "{\"api_token\": \"$TOKEN\", \"client_id\": \"dev_id\", \"client_secret\": \"dev_secret\"}"

echo "Secret updated successfully."
