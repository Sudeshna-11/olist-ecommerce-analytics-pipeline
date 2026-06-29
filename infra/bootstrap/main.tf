// Bootstrap: the remote-state backend itself.
//
// Chicken-and-egg problem: the main config in ../ stores its state in S3 with a
// DynamoDB lock, but those resources don't exist on a fresh account. This tiny
// config runs FIRST with *local* state to create them, then the main config
// points its backend at the bucket/table created here.
//
// Run once:  terraform -chdir=infra/bootstrap init && terraform -chdir=infra/bootstrap apply
// Its own state (terraform.tfstate) stays local and is gitignored.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project   = "olist-data-eng"
      ManagedBy = "terraform"
      Component = "tfstate-bootstrap"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  # Bucket names are globally unique; the account id suffix guarantees it.
  state_bucket = "${var.name_prefix}-tfstate-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "tfstate" {
  bucket = local.state_bucket

  # State is the source of truth for live infra — block accidental deletion.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tfstate_lock" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST" # on-demand: ~$0 at this lock volume
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
