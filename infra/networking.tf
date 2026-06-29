// Networking: reuse the account's default VPC + its public subnets. The task
// gets a public IP (assign_public_ip in the schedule target) to reach Snowflake,
// ECR, S3, Secrets Manager and the Frankfurter API — so no NAT gateway is needed
// (that would be ~$32/mo). Egress-only security group; nothing connects in.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "task" {
  name_prefix = "${var.name_prefix}-task-"
  description = "Egress-only SG for the Fargate pipeline task"
  vpc_id      = data.aws_vpc.default.id

  egress {
    description = "All outbound (Snowflake, ECR, S3, Secrets Manager, FX API)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name_prefix}-task" }

  lifecycle {
    create_before_destroy = true
  }
}
