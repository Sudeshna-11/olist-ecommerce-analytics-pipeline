// STEP 7 — EventBridge Scheduler: the cloud cron that runs the pipeline daily.
//
//   resource "aws_scheduler_schedule" "daily" {
//     schedule_expression = var.schedule_expression   // cron(0 7 * * ? *) UTC
//     flexible_time_window { mode = "OFF" }
//     target {
//       arn      = aws_ecs_cluster.main.arn
//       role_arn = <scheduler invoke role>
//       ecs_parameters {
//         task_definition_arn = aws_ecs_task_definition.pipeline.arn
//         launch_type         = "FARGATE"
//         network_configuration { subnets, security_groups, assign_public_ip = true }
//       }
//     }
//   }
//
// Mirrors the week-5 Airflow schedule (0 7 daily) — Airflow stays the local/dev
// orchestrator; this is the production trigger.
