# Infrastructure (week 6 — Terraform + AWS)

Terraform-managed deployment of the Olist pipeline to **AWS ECS Fargate**, run
daily by **EventBridge Scheduler**. Snowflake stays the warehouse; AWS hosts the
compute that runs `ingest → verify → dbt build` on a schedule.

The week-5 Airflow stack is unchanged and remains the **local/dev** orchestrator.
This is the **production** trigger.

## Architecture

```
EventBridge Scheduler  cron(0 7 * * ? *)
        │ ecs:RunTask (FARGATE)
        ▼
ECS Fargate task ──pull── ECR (pipeline image)
   entrypoint: ingest → verify → dbt build --target prod
   ├─ raw CSVs ──── S3 (raw bucket)
   ├─ creds ─────── Secrets Manager → injected as SNOWFLAKE_* env vars
   ├─ logs ──────── CloudWatch Logs
   └─ transforms ── Snowflake
Terraform state ── S3 + DynamoDB lock   (created by ./bootstrap)
Networking ─────── default VPC + public subnet (no NAT gateway)
```

## Layout

| Path | Purpose | Step |
|---|---|---|
| `bootstrap/` | Creates the state S3 bucket + DynamoDB lock (local state) | 1 |
| `providers.tf` `variables.tf` `locals.tf` `backend.tf` | Main config foundation | 1 |
| `networking.tf` | Default VPC lookup + task security group | 6 |
| `ecr.tf` | Image repository | 3 |
| `s3.tf` | Raw-CSV bucket | 4 |
| `secrets.tf` | Snowflake credentials secret | 5 |
| `iam.tf` | Task execution / task / scheduler roles | 6 |
| `ecs.tf` | Cluster + task definition + log group | 6 |
| `schedule.tf` | EventBridge daily trigger | 7 |

## Prerequisites

- **Terraform** ≥ 1.5 and **AWS CLI v2** installed (neither is on this machine yet).
- **Docker** running (already installed).
- An AWS account with credentials configured: `aws configure` (region `us-east-1`).

## Usage

```bash
# 1. Bootstrap remote state (once per account)
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap apply
terraform -chdir=infra/bootstrap output     # copy values into backend.hcl

# 2. Point the main config at that state
cd infra
cp backend.hcl.example backend.hcl          # fill in bucket / region / table
terraform init -backend-config=backend.hcl

# 3..7  build image, push to ECR, upload CSVs, put the secret, apply  (later steps)

# Run it once on demand
aws ecs run-task --cluster <cluster> --task-definition <td> --launch-type FARGATE ...

# Tear everything down when done (stops all spend)
terraform destroy
terraform -chdir=infra/bootstrap destroy    # remove prevent_destroy on the bucket first
```

## Cost

Under ~$2/mo if left running (Secrets Manager $0.40/secret; Fargate billed per
run = pennies/day; S3/ECR/DynamoDB negligible). **~$0 after `terraform destroy`.**
No NAT gateway by design.
