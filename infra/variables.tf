variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "credly-ingestion"
}

variable "environment" {
  description = "Environment name (dev, hom, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for data lake"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "credly-ingestion"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "credly_org_id" {
  description = "Credly organization ID"
  type        = string
}

variable "secrets_manager_key" {
  description = "Secrets Manager key for Credly credentials"
  type        = string
  default     = "credly/credentials"
}

variable "watermark_overlap_minutes" {
  description = "Overlap in minutes for incremental load"
  type        = number
  default     = 15
}

variable "enable_compute" {
  description = "Enable creation of compute resources (Lambda, Step Functions). Set to false for local dev if Docker is not available."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
