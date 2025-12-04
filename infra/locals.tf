locals {
  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  )

  dynamodb_metadata_table_name = "${var.project_name}-metadata-${var.environment}"

  step_function_name = "${var.project_name}-orchestrator-${var.environment}"

  lambda_env_vars = {
    ENV                   = upper(var.environment)
    AWS_REGION            = var.aws_region
    S3_BUCKET_NAME        = var.s3_bucket_name
    CREDLY_ORG_ID         = var.credly_org_id
    CREDLY_BASE_URL       = "https://api.credly.com/v1"
    SECRETS_MANAGER_KEY   = var.secrets_manager_key
    METADATA_TABLE_NAME   = local.dynamodb_metadata_table_name
    WATERMARK_OVERLAP_MIN = var.watermark_overlap_minutes
  }

  localstack_endpoint = var.localstack_endpoint
}
