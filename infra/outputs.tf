# ============================================
# Outputs
# ============================================

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.datalake.bucket
}

output "secrets_manager_secret_arn" {
  description = "Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.credly_credentials.arn
}


output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = try(aws_lambda_function.credly_ingestion[0].arn, null)
}

output "step_function_arn" {
  description = "Step Functions state machine ARN"
  value       = try(aws_sfn_state_machine.credly_orchestrator[0].arn, null)
}
