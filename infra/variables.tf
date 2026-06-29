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
