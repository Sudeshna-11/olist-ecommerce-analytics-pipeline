// S3 bucket for the raw Olist CSVs. The container syncs these to data/raw at
// startup (RAW_DATA_S3_URI) instead of baking them into the image.
// Upload once after apply:  aws s3 sync data/raw s3://<bucket>/raw

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "raw" {
  bucket = "${var.name_prefix}-raw-${data.aws_caller_identity.current.account_id}"

  # Portfolio data is a fixed public dataset; let destroy empty + remove it.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
