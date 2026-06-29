// STEP 6 — ECS Fargate cluster, task definition, and CloudWatch log group.
//
//   resource "aws_cloudwatch_log_group" "pipeline" { ... }
//   resource "aws_ecs_cluster" "main" { ... }
//   resource "aws_ecs_task_definition" "pipeline" {
//     requires_compatibilities = ["FARGATE"]
//     cpu / memory from var.task_cpu / var.task_memory
//     container: image = ECR repo, command runs deploy/entrypoint.sh,
//       environment = { TARGET = "snowflake", ...non-secret SNOWFLAKE_* },
//       secrets     = SNOWFLAKE_PASSWORD (+ any other secret keys) from Secrets Manager,
//       logConfiguration -> the log group above.
//   }
//
// No aws_ecs_service: this is a run-to-completion task, launched on demand by
// the EventBridge schedule (step 7), not a long-running service.
