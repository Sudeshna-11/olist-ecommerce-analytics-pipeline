// STEP 6 — IAM roles.
//
//   - task execution role: pull from ECR, write CloudWatch logs, read the
//     Snowflake secret for env injection (ecs-tasks.amazonaws.com).
//   - task role: app-level perms the container itself needs — read the raw S3
//     bucket.
//   - scheduler invoke role (STEP 7): lets EventBridge Scheduler call
//     ecs:RunTask + iam:PassRole on the two roles above.
