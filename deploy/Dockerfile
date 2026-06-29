# Pipeline image: runs ingest -> verify -> dbt build in one shot on ECS Fargate.
#
# Unlike the Airflow image (which sandboxes the project in a separate venv to
# dodge Airflow's SQLAlchemy 1.4 pin), this container runs ONLY the pipeline, so
# deps install straight into the system site-packages.
#
# Build context is the repo root so the COPYs below can reach src/, scripts/,
# olist_dbt/. Build for amd64 (Fargate's default):
#   docker build -f deploy/Dockerfile -t olist-pipeline .
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# AWS CLI v2 as an isolated bundle (not pip — avoids botocore/urllib3 conflicts
# with the Snowflake connector). Used by the entrypoint to pull raw CSVs from S3.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl unzip ca-certificates \
 && curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip \
 && unzip -q /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip \
 && apt-get purge -y --auto-remove curl unzip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/project

# Deps first for layer caching. requirements-dev brings dbt-core/dbt-snowflake
# (needed at runtime); pytest/dbt-postgres ride along harmlessly.
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

# Project code, dbt project, and the entrypoint.
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY olist_dbt/ ./olist_dbt/
COPY deploy/entrypoint.sh ./deploy/entrypoint.sh
RUN chmod +x ./deploy/entrypoint.sh

ENTRYPOINT ["./deploy/entrypoint.sh"]
