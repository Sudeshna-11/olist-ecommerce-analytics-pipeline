// STEP 5 — Secrets Manager secret for the Snowflake credentials.
//
// Terraform creates the empty secret; the VALUE is put out-of-band so the
// password never lands in state-as-plaintext-in-chat or the repo:
//   aws secretsmanager put-secret-value --secret-id <name> --secret-string file://...
//
// The ECS task definition injects each key as an env var via `secrets`
// (valueFrom = "<secret-arn>:SNOWFLAKE_PASSWORD::"), so the pipeline picks them
// up through the existing env_var() path — no code change.
//
//   resource "aws_secretsmanager_secret" "snowflake" { ... }
