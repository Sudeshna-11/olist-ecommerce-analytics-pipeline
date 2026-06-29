// ECR repository for the pipeline image (built from ../deploy/Dockerfile).
// The ECS task definition (step 6) pulls from here.

resource "aws_ecr_repository" "pipeline" {
  name                 = "${var.name_prefix}-pipeline"
  image_tag_mutability = "MUTABLE"

  # Let `terraform destroy` remove the repo even when it still holds images.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the repo tidy: drop untagged layers a week after they're superseded.
resource "aws_ecr_lifecycle_policy" "pipeline" {
  repository = aws_ecr_repository.pipeline.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Expire untagged images after 7 days"
      selection = {
        tagStatus   = "untagged"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 7
      }
      action = { type = "expire" }
    }]
  })
}
