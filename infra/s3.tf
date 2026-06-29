// STEP 4 — S3 bucket for the raw Olist CSVs.
//
// The container syncs these down at startup instead of baking them into the
// image. Upload once after apply:  aws s3 sync ../data/raw s3://<bucket>/raw
//
//   resource "aws_s3_bucket" "raw" { ... }
//   resource "aws_s3_bucket_public_access_block" "raw" { ... }
