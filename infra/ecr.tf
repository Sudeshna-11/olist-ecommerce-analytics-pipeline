// STEP 3 — ECR repository for the pipeline image.
//
//   resource "aws_ecr_repository" "pipeline" { ... }
//   resource "aws_ecr_lifecycle_policy" "pipeline" { ... }  // expire untagged
//
// Image is built from ../deploy/Dockerfile and pushed before the ECS task def
// references it.
