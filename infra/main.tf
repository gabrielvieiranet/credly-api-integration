# ============================================
# S3 Bucket
# ============================================


resource "aws_s3_bucket" "datalake" {
  bucket = var.s3_bucket_name

  tags = merge(
    local.common_tags,
    {
      Name = var.s3_bucket_name
    }
  )
}

# ============================================
# Secrets Manager
# ============================================

resource "aws_secretsmanager_secret" "credly_credentials" {
  name = var.secrets_manager_key

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "credly_credentials" {
  secret_id = aws_secretsmanager_secret.credly_credentials.id
  secret_string = jsonencode({
    api_token     = "PLACEHOLDER_TOKEN"
    client_id     = "dev_id"
    client_secret = "dev_secret"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# ============================================
# DynamoDB Tables
# ============================================

# Metadata table for watermarks and payload hashes
resource "aws_dynamodb_table" "table_metadata" {
  name         = local.dynamodb_metadata_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "table_name"

  attribute {
    name = "table_name"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = false
  }

  tags = merge(
    local.common_tags,
    {
      Name = local.dynamodb_metadata_table_name
    }
  )
}

# ============================================
# IAM Roles and Policies
# ============================================

# Lambda execution role
resource "aws_iam_role" "lambda" {
  count              = var.enable_compute ? 1 : 0
  name               = "${var.project_name}-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = local.common_tags
}

# Lambda policy
resource "aws_iam_role_policy" "lambda" {
  count = var.enable_compute ? 1 : 0
  name  = "${var.project_name}-lambda-policy-${var.environment}"
  role  = aws_iam_role.lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.table_metadata.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.secrets_manager_key}*"
      }
    ]
  })
}

# Step Functions execution role
resource "aws_iam_role" "step_function" {
  count              = var.enable_compute ? 1 : 0
  name               = "${var.project_name}-sfn-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.step_function_assume_role.json

  tags = local.common_tags
}

# Step Functions policy
resource "aws_iam_role_policy" "step_function" {
  count = var.enable_compute ? 1 : 0
  name  = "${var.project_name}-sfn-policy-${var.environment}"
  role  = aws_iam_role.step_function[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.credly_ingestion[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================
# Lambda Function
# ============================================

resource "aws_lambda_function" "credly_ingestion" {
  count         = var.enable_compute ? 1 : 0
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda[0].arn

  # For LocalStack, we can use a dummy deployment package
  # For production, replace with actual deployment package
  filename         = "${path.module}/lambda_dummy.zip"
  source_code_hash = fileexists("${path.module}/lambda_dummy.zip") ? filebase64sha256("${path.module}/lambda_dummy.zip") : base64sha256("dummy")

  handler     = "handlers.credly_ingestion_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = local.lambda_env_vars
  }

  tags = local.common_tags
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  count             = var.enable_compute ? 1 : 0
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 7

  tags = local.common_tags
}

# ============================================
# Step Functions State Machine
# ============================================

resource "aws_sfn_state_machine" "credly_orchestrator" {
  count    = var.enable_compute ? 1 : 0
  name     = local.step_function_name
  role_arn = aws_iam_role.step_function[0].arn

  definition = templatefile("${path.module}/step_function_definition.json.tftpl", {
    lambda_arn = aws_lambda_function.credly_ingestion[0].arn
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_function[0].arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = local.common_tags
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "step_function" {
  count             = var.enable_compute ? 1 : 0
  name              = "/aws/states/${local.step_function_name}"
  retention_in_days = 7

  tags = local.common_tags
}
