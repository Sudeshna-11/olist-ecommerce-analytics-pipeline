variable "aws_region" {
  description = "AWS region for all week-6 resources."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix for resource names. Keep in sync with the main config."
  type        = string
  default     = "olist"
}

variable "lock_table_name" {
  description = "DynamoDB table name for Terraform state locking."
  type        = string
  default     = "olist-tfstate-lock"
}
