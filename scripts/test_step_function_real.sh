#!/bin/bash

# Script to test Step Functions + Lambda in LocalStack
# This enables compute resources and deploys them to LocalStack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "=================================================="
echo "Testing Step Functions + Lambda in LocalStack"
echo "=================================================="

# Step 1: Enable compute resources temporarily
echo ""
echo "Step 1: Enabling compute resources in Terraform..."
cd "$INFRA_DIR"

# Create temporary override to enable compute
cat > terraform_compute.tfvars << EOF
enable_compute = true
EOF

echo "✓ Created terraform_compute.tfvars"

# Step 2: Deploy infrastructure
echo ""
echo "Step 2: Deploying infrastructure to LocalStack..."
terraform apply -var-file=terraform.tfvars -var-file=terraform_compute.tfvars -auto-approve

# Get outputs
LAMBDA_ARN=$(terraform output -raw lambda_function_arn 2>/dev/null || echo "")
SFN_ARN=$(terraform output -raw step_function_arn 2>/dev/null || echo "")

if [ -z "$LAMBDA_ARN" ] || [ -z "$SFN_ARN" ]; then
    echo "✗ Failed to get Lambda or Step Function ARN"
    echo "Lambda ARN: $LAMBDA_ARN"
    echo "SFN ARN: $SFN_ARN"
    exit 1
fi

echo "✓ Infrastructure deployed"
echo "  Lambda ARN: $LAMBDA_ARN"
echo "  Step Function ARN: $SFN_ARN"

# Step 3: Execute Step Function
echo ""
echo "Step 3: Executing Step Function for daily badges ingestion..."

EXECUTION_NAME="daily-badges-$(date +%s)"
INPUT_JSON='{
  "load_type": "badges",
  "mode": "daily"
}'

echo "Execution name: $EXECUTION_NAME"
echo "Input: $INPUT_JSON"

# Start execution
EXECUTION_ARN=$(aws stepfunctions start-execution \
    --endpoint-url http://localhost:4566 \
    --region us-east-1 \
    --state-machine-arn "$SFN_ARN" \
    --name "$EXECUTION_NAME" \
    --input "$INPUT_JSON" \
    --query 'executionArn' \
    --output text)

echo "✓ Execution started: $EXECUTION_ARN"

# Step 4: Monitor execution
echo ""
echo "Step 4: Monitoring execution..."
echo ""

MAX_WAIT=120  # 2 minutes
ELAPSED=0
SLEEP_INTERVAL=2

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(aws stepfunctions describe-execution \
        --endpoint-url http://localhost:4566 \
        --region us-east-1 \
        --execution-arn "$EXECUTION_ARN" \
        --query 'status' \
        --output text)
    
    echo "[$ELAPSED s] Status: $STATUS"
    
    if [ "$STATUS" = "SUCCEEDED" ]; then
        echo ""
        echo "=================================================="
        echo "✓ Step Function execution SUCCEEDED!"
        echo "=================================================="
        
        # Get execution output
        echo ""
        echo "Execution output:"
        aws stepfunctions describe-execution \
            --endpoint-url http://localhost:4566 \
            --region us-east-1 \
            --execution-arn "$EXECUTION_ARN" \
            --query 'output' \
            --output text | jq .
        
        # Get execution history
        echo ""
        echo "Execution history:"
        aws stepfunctions get-execution-history \
            --endpoint-url http://localhost:4566 \
            --region us-east-1 \
            --execution-arn "$EXECUTION_ARN" \
            --max-results 10
        
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "TIMED_OUT" ] || [ "$STATUS" = "ABORTED" ]; then
        echo ""
        echo "=================================================="
        echo "✗ Step Function execution $STATUS"
        echo "=================================================="
        
        # Get execution details
        aws stepfunctions describe-execution \
            --endpoint-url http://localhost:4566 \
            --region us-east-1 \
            --execution-arn "$EXECUTION_ARN"
        
        exit 1
    fi
    
    sleep $SLEEP_INTERVAL
    ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠ Execution still running after $MAX_WAIT seconds"
    echo "Check manually with:"
    echo "aws stepfunctions describe-execution --endpoint-url http://localhost:4566 --region us-east-1 --execution-arn $EXECUTION_ARN"
fi

# Cleanup
echo ""
echo "Cleaning up terraform_compute.tfvars..."
rm -f terraform_compute.tfvars

echo ""
echo "Test complete!"
