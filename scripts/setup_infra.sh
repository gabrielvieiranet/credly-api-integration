#!/bin/bash
set -e

echo "========================================="
echo "Infrastructure Setup Script"
echo "========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra"

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT_URL="http://localhost:4566"

# ============================================
# CLEANUP: Delete existing resources via AWS CLI
# ============================================

echo ""
echo "--- CLEANUP: Deleting existing resources ---"

BUCKET_NAME="my-datalake-bucket"
SECRET_NAME="my-app/credentials"
METADATA_TABLE="credly-ingestion-metadata-dev"

# Delete S3 bucket (with all objects)
echo "Deleting S3 bucket: s3://$BUCKET_NAME..."
aws --endpoint-url=$ENDPOINT_URL s3 rb s3://$BUCKET_NAME --force 2>/dev/null || true

# Delete DynamoDB table
echo "Deleting DynamoDB table: $METADATA_TABLE..."
aws --endpoint-url=$ENDPOINT_URL dynamodb delete-table --table-name $METADATA_TABLE 2>/dev/null || true

# Delete Secrets Manager secret
echo "Deleting secret: $SECRET_NAME..."
aws --endpoint-url=$ENDPOINT_URL secretsmanager delete-secret --secret-id $SECRET_NAME --force-delete-without-recovery 2>/dev/null || true

echo "Cleanup complete!"
sleep 2

# ============================================
# TERRAFORM: Initialize and Apply
# ============================================

echo ""
echo "--- Initializing Terraform ---"
cd "$INFRA_DIR"

# Initialize Terraform (if not already initialized)
terraform init -reconfigure

echo ""
echo "--- Applying Terraform Configuration ---"
# Disable compute resources (Lambda/SFN) for LocalStack due to Docker limitations
terraform apply -auto-approve -var="enable_compute=false"

# ============================================
# DONE
# ============================================

echo ""
echo "========================================="
echo "Infrastructure setup complete!"
echo "========================================="
echo "All resources created via Terraform:"
echo "  - S3 Bucket: s3://$BUCKET_NAME"
echo "  - Secrets Manager: $SECRET_NAME"
echo "  - DynamoDB Table: $METADATA_TABLE (watermarks + payload hashes)"
echo "  - Lambda Function"
echo "  - Step Functions"
echo ""

# ============================================
# Update Credly API Token
# ============================================

echo "--- Updating Credly API Token ---"
if [ -f "$SCRIPT_DIR/update_local_token.sh" ]; then
    "$SCRIPT_DIR/update_local_token.sh"
else
    echo "Warning: update_local_token.sh not found, skipping token update"
fi

echo ""
echo "Setup complete! Infrastructure is ready to use."
echo ""
