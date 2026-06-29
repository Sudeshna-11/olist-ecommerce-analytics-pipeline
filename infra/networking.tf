// STEP 6 — networking.
//
// Uses the account's default VPC + its public subnets via data sources (no NAT
// gateway = no ~$32/mo charge; the task gets a public IP to reach Snowflake,
// ECR, S3 and Secrets Manager). Plus one egress-only security group.
//
//   data "aws_vpc" "default" { default = true }
//   data "aws_subnets" "default" { ... }
//   resource "aws_security_group" "task" { ... }
