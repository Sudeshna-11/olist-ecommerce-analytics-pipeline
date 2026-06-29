// These three values populate ../backend.hcl so the main config can find its
// remote state. Print them after apply:  terraform -chdir=infra/bootstrap output

output "state_bucket_name" {
  description = "S3 bucket holding the main config's Terraform state."
  value       = aws_s3_bucket.tfstate.id
}

output "lock_table_name" {
  description = "DynamoDB table used for state locking."
  value       = aws_dynamodb_table.tfstate_lock.name
}

output "region" {
  description = "Region the state bucket and lock table live in."
  value       = var.aws_region
}
