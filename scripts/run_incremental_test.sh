#!/bin/bash

# Script to run incremental load test (badges only).
# Simulates two consecutive daily runs to verify watermark logic.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configure AWS CLI for Localstack
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

echo "=================================================="
echo "Running Incremental Load Test (Badges Only)"
echo "=================================================="

# Step 1: Reset Environment (Clean State)
echo ""
echo "Step 1: Resetting Environment..."
"$SCRIPT_DIR/reset_environment.sh"

# Step 2: First Run (Simulate "Yesterday")
echo ""
echo "Step 2: First Run (Simulate Initial Daily Load)..."
# This should default to start_date = yesterday (no watermark)
uv run python "$SCRIPT_DIR/simulate_step_function.py" --load-type badges --mode daily --max-pages 2

# Step 3: Verify Watermark Created
echo ""
echo "Step 3: Verifying Watermark Creation..."
WATERMARK=$(aws --endpoint-url=http://localhost:4566 --region us-east-1 dynamodb get-item \
    --table-name credly-ingestion-metadata-dev \
    --key '{"table_name": {"S": "badges_watermark"}}' \
    --query 'Item.watermark.S' --output text)

if [ "$WATERMARK" == "None" ] || [ -z "$WATERMARK" ]; then
    echo "✗ Watermark NOT found after first run!"
    exit 1
else
    echo "✓ Watermark found: $WATERMARK"
fi

# Step 4: Second Run (Simulate "Today")
echo ""
echo "Step 4: Second Run (Simulate Subsequent Daily Load)..."
# This should use the watermark from Step 3
uv run python "$SCRIPT_DIR/simulate_step_function.py" --load-type badges --mode daily --max-pages 2

# Step 5: Verify Watermark Updated
echo ""
echo "Step 5: Verifying Watermark Update..."
NEW_WATERMARK=$(aws --endpoint-url=http://localhost:4566 --region us-east-1 dynamodb get-item \
    --table-name credly-ingestion-metadata-dev \
    --key '{"table_name": {"S": "badges_watermark"}}' \
    --query 'Item.watermark.S' --output text)

if [ "$NEW_WATERMARK" == "$WATERMARK" ]; then
    echo "✗ Watermark did NOT update!"
    echo "Old: $WATERMARK"
    echo "New: $NEW_WATERMARK"
    exit 1
else
    echo "✓ Watermark updated: $NEW_WATERMARK"
fi

echo ""
echo "=================================================="
echo "✓ Incremental Test Complete"
echo "=================================================="
