# Custom Airflow image for the Olist pipeline.
#
# Airflow's own environment pins SQLAlchemy 1.4, but the project pins
# SQLAlchemy 2.0 (requirements.txt) and brings dbt + the Snowflake
# connector. Installing those into Airflow's environment would break it.
# So the pipeline's runtime + dbt deps live in an ISOLATED virtualenv at
# /opt/project-venv; the DAG's BashOperators call that interpreter
# directly. Airflow and the pipeline never share a dependency tree.
#
# Build context is the REPO ROOT (see docker-compose.yml) so the COPY
# below can reach requirements.txt / requirements-dev.txt.
ARG AIRFLOW_VERSION=2.10.5
FROM apache/airflow:${AIRFLOW_VERSION}-python3.10

USER root

COPY requirements.txt requirements-dev.txt /tmp/project-reqs/
RUN python -m venv /opt/project-venv \
 && /opt/project-venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/project-venv/bin/pip install --no-cache-dir \
      -r /tmp/project-reqs/requirements.txt \
      -r /tmp/project-reqs/requirements-dev.txt \
 && chown -R airflow:0 /opt/project-venv \
 && rm -rf /tmp/project-reqs

USER airflow
