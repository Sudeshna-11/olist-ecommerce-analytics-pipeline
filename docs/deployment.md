# Deployment (Terraform + AWS)

How the pipeline runs in the cloud. The runbook (exact commands) lives in
[`infra/README.md`](../infra/README.md); this doc covers the *why*.

## What gets deployed — and what doesn't

The warehouse (Snowflake) is already cloud-hosted, so AWS doesn't store the data.
What AWS provides is the **scheduled compute** that runs the existing week-5
pipeline — `ingest (CSV + FX) → verify → dbt build` — once a day, defined entirely
in Terraform.

```
EventBridge Scheduler  cron(0 7 * * ? *) UTC
        │ ecs:RunTask (FARGATE)
        ▼
ECS Fargate task ──pull── ECR (pipeline image)
   entrypoint: ingest → verify → dbt deps/run/snapshot/run/test  (--target prod)
   ├─ raw CSVs ──── S3  (synced to data/raw at startup)
   ├─ password ──── Secrets Manager → injected as SNOWFLAKE_PASSWORD
   ├─ logs ──────── CloudWatch Logs
   └─ transforms ── Snowflake
Terraform state ── S3 + DynamoDB lock
Networking ─────── default VPC + public subnet (no NAT gateway)
```

## Key decisions

### Scheduled Fargate task, not Airflow-on-AWS or MWAA

The pipeline could run in the cloud three ways. The trade-off is cost vs. how much
of the week goes to infrastructure plumbing:

| Option | What it is | ~Cost | Verdict |
|---|---|---|---|
| **Scheduled Fargate task** | One container, EventBridge triggers it daily | ~$0–2/mo | **Chosen** |
| Airflow on Fargate | The 3-container stack as ECS services + RDS + ALB | ~$50–150/mo | Most plumbing, always-on bill |
| MWAA (managed Airflow) | AWS-managed Airflow | ~$350+/mo floor | Too expensive for a portfolio |

The scheduled task exercises every AWS primitive a data role looks for (ECR, ECS
Fargate, IAM task roles, Secrets Manager, EventBridge, CloudWatch, S3 remote
state) at near-zero cost. **Airflow stays the local/dev orchestrator** (week 5);
EventBridge is the production trigger. That two-tier split — a rich orchestrator
for development, native cloud scheduling for production — is a real pattern, not a
compromise.

### No code change for the cloud

The container runs the *same* `src/`, `scripts/dbt.py`, and `olist_dbt/` as the
CLI and Airflow. `config.load_env()` treats `.env`/`.secrets.env` as optional and
`profiles.yml` reads every credential through `env_var()`, so supplying the values
as environment variables is enough. ECS injects them — non-secrets as plain
`environment`, the password as a `secrets` entry from Secrets Manager.

### Secrets

Only the Snowflake **password** is a true secret; it lives in Secrets Manager and
is injected into the task at runtime. Terraform manages the secret's *metadata*
only (no `aws_secretsmanager_secret_version`), so the password never enters
Terraform state. The value is written out-of-band with `put-secret-value`. The
non-secret connection fields (account, user, role, db, warehouse) are supplied via
a gitignored `terraform.tfvars` — the same public/private split the repo already
uses for `.env` vs `.secrets.env`.

### Networking — default VPC, no NAT

The task runs in the account's default VPC public subnets with a public IP, so it
reaches Snowflake, ECR, S3, and Secrets Manager directly. This deliberately avoids
a NAT gateway (~$32/mo — it would dwarf every other line item). The security group
is egress-only; nothing connects to the task.

### Remote state

Terraform state lives in an S3 bucket with a DynamoDB lock table, created by a
one-time `infra/bootstrap/` config (local state) to solve the chicken-and-egg of
"the backend can't store state in resources that don't exist yet."

## Cost & teardown

Under ~$2/mo if left running (Secrets Manager $0.40/secret; Fargate billed per run
= pennies/day; S3/ECR/DynamoDB negligible). `terraform destroy` removes everything
and stops all spend — the ECR repo and raw bucket use `force_delete`/`force_destroy`
so the teardown is clean even with images/objects present.

## Decisions log

See ADR-009 and ADR-010 in [`architecture.md`](architecture.md).
