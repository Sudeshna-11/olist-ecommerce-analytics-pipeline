variable "aws_region" {
  description = "AWS region for all week-6 resources."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to resource names (ECR repo, S3 bucket, ECS cluster, etc.)."
  type        = string
  default     = "olist"
}

variable "schedule_expression" {
  description = "EventBridge Scheduler cron for the daily pipeline run (UTC)."
  type        = string
  default     = "cron(0 7 * * ? *)"
}

variable "task_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  type        = string
  default     = "512"
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = string
  default     = "1024"
}

# --- Snowflake connection (non-secret; password lives in Secrets Manager) ----
# account + user have no defaults: set them in terraform.tfvars (gitignored) so
# they don't land in the public repo. The rest already appear in profiles.yml.

variable "snowflake_account" {
  description = "Snowflake account identifier (e.g. ab12345.us-east-1)."
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake username."
  type        = string
}

variable "snowflake_role" {
  description = "Snowflake role."
  type        = string
  default     = "ACCOUNTADMIN"
}

variable "snowflake_database" {
  description = "Snowflake database."
  type        = string
  default     = "OLIST"
}

variable "snowflake_schema" {
  description = "Raw landing schema for the ingest step (dbt reads from it, writes to ANALYTICS)."
  type        = string
  default     = "raw"
}

variable "snowflake_warehouse" {
  description = "Snowflake warehouse."
  type        = string
  default     = "COMPUTE_WH"
}
