// IAM roles for the Fargate task.
//
//   - task_execution: used by the ECS agent to pull the image, write logs, and
//     read the Snowflake secret for env injection.
//   - task: the container's own runtime permissions (read the raw S3 bucket).

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# --- Task execution role -----------------------------------------------------

resource "aws_iam_role" "task_execution" {
  name               = "${var.name_prefix}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

# AWS-managed policy: ECR pull + CloudWatch Logs write.
resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Let the execution role read ONLY the Snowflake secret (for env injection).
data "aws_iam_policy_document" "read_secret" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.snowflake_password.arn]
  }
}

resource "aws_iam_role_policy" "task_execution_secret" {
  name   = "read-snowflake-secret"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.read_secret.json
}

# --- Task role ---------------------------------------------------------------

resource "aws_iam_role" "task" {
  name               = "${var.name_prefix}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

# The container reads raw CSVs from the data bucket at startup.
data "aws_iam_policy_document" "read_raw_bucket" {
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.raw.arn,
      "${aws_s3_bucket.raw.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "task_read_raw" {
  name   = "read-raw-bucket"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.read_raw_bucket.json
}
