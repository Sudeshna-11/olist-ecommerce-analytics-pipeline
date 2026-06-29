// Remote state in S3 with DynamoDB locking, created by ./bootstrap.
//
// Partial config: bucket / region / dynamodb_table vary per account, so they
// are supplied at init time from backend.hcl (copy backend.hcl.example, fill in
// the bootstrap outputs):
//
//     terraform init -backend-config=backend.hcl
//
// key + encrypt are constant and live here.

terraform {
  backend "s3" {
    key     = "infra/terraform.tfstate"
    encrypt = true
  }
}
