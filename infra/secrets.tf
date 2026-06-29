// Secrets Manager secret for the Snowflake password.
//
// Terraform manages only the secret's METADATA (no aws_secretsmanager_secret_version
// here) so the password never enters Terraform state. The value is put
// out-of-band:
//   aws secretsmanager put-secret-value --secret-id olist/snowflake/password ...
//
// The ECS task definition (step 6) injects it as the SNOWFLAKE_PASSWORD env var
// via `secrets` valueFrom = this ARN.

resource "aws_secretsmanager_secret" "snowflake_password" {
  name        = "${var.name_prefix}/snowflake/password"
  description = "Snowflake password for the Olist pipeline. Value set out-of-band; not in TF state."

  # Delete immediately on destroy instead of the default 30-day recovery window,
  # so a later re-apply can reuse the same name without a scheduled-deletion clash.
  recovery_window_in_days = 0
}

output "snowflake_secret_arn" {
  description = "ARN of the Snowflake password secret (value managed out-of-band)."
  value       = aws_secretsmanager_secret.snowflake_password.arn
}
