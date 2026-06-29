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
