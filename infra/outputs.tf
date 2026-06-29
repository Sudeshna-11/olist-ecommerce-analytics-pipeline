// Outputs are added alongside their resources in later steps, e.g.:
//   - ecs_cluster_name     (step 6)
//   - task_definition_arn  (step 6)
//   - schedule_name        (step 7)

output "ecr_repository_url" {
  description = "Push the pipeline image here; the ECS task definition pulls from it."
  value       = aws_ecr_repository.pipeline.repository_url
}

output "raw_bucket_name" {
  description = "S3 bucket the container syncs raw CSVs from at startup."
  value       = aws_s3_bucket.raw.id
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.pipeline.arn
}

output "task_subnets" {
  description = "Default-VPC subnets the task runs in (for manual run-task)."
  value       = data.aws_subnets.default.ids
}

output "task_security_group_id" {
  value = aws_security_group.task.id
}

output "schedule_name" {
  description = "EventBridge schedule that triggers the daily pipeline run."
  value       = aws_scheduler_schedule.daily.name
}
