terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.100.0" # Locked for cross-platform compatibility (Linux + macOS)
    }
  }
}

provider "aws" {
  region = var.aws_region
}
