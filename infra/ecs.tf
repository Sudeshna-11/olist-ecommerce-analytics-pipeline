// ECS Fargate cluster, CloudWatch log group, and the run-to-completion task
// definition. No aws_ecs_service: the task is launched on demand by the
// EventBridge schedule (step 7), not kept running.

resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/ecs/${var.name_prefix}-pipeline"
  retention_in_days = 14
}

resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster"
}

resource "aws_ecs_task_definition" "pipeline" {
  family                   = "${var.name_prefix}-pipeline"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "pipeline"
      image     = "${aws_ecr_repository.pipeline.repository_url}:latest"
      essential = true

      # Non-secret config as plain env; the password is injected from Secrets
      # Manager below. config.load_env() + profiles.yml read all of these via
      # the environment, so no code change is needed for the cloud.
      environment = [
        { name = "TARGET", value = "snowflake" },
        { name = "RAW_DATA_S3_URI", value = "s3://${aws_s3_bucket.raw.id}/raw" },
        { name = "SNOWFLAKE_ACCOUNT", value = var.snowflake_account },
        { name = "SNOWFLAKE_USER", value = var.snowflake_user },
        { name = "SNOWFLAKE_ROLE", value = var.snowflake_role },
        { name = "SNOWFLAKE_DATABASE", value = var.snowflake_database },
        { name = "SNOWFLAKE_SCHEMA", value = var.snowflake_schema },
        { name = "SNOWFLAKE_WAREHOUSE", value = var.snowflake_warehouse },
      ]

      secrets = [
        {
          name      = "SNOWFLAKE_PASSWORD"
          valueFrom = aws_secretsmanager_secret.snowflake_password.arn
        },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.pipeline.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "pipeline"
        }
      }
    }
  ])
}
