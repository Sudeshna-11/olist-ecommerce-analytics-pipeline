# Demo / Loom Walkthrough Script

A scene-by-scene script for a **6–8 minute** recorded walkthrough of the project.
Each scene lists what to **show** on screen and the **talking points** to say over
it. Aim for a confident, plain-spoken tone — explain *why*, not just *what*.

> **Goal of the video:** in under 8 minutes, convince a viewer you can design and
> build a production-shaped data pipeline *and* explain the decisions behind it.
> Lead with the architecture and the business value; keep code on screen brief.

## Before you record (2-minute prep)

- [ ] `docker compose up -d` — local Postgres running (for any live query).
- [ ] Open tabs/windows: GitHub repo README · `docs/architecture.md` (rendered
      diagram) · the Power BI report (or screenshots in `dashboards/`) · GitHub
      Actions page (green CI run) · a terminal in the repo root.
- [ ] Close anything showing credentials. Never show `.secrets.env` or the
      Snowflake connection dialog / account locator.
- [ ] Have `docs/business-insights.md` open for the findings.
- [ ] Test mic + screen recording. Record at 1080p, share the whole screen.

## Scene 1 — Hook & overview · 0:00–0:45

**Show:** the GitHub README top (title, badges, architecture diagram).

**Say:**
- "This is an end-to-end analytics pipeline on a real Brazilian e-commerce dataset
  — about 100,000 orders across nine source tables."
- "It goes from raw CSVs, through Python ingestion, into a dbt star schema running
  on both Postgres and Snowflake, orchestrated by Airflow and deployed to AWS,
  with CI and data-quality checks on every change."
- "I'll walk through the architecture, show it running, and end on the business
  insights it produces." Point at the CI badge: "and yes — it's green."

## Scene 2 — Architecture & the key decisions · 0:45–2:30

**Show:** the rendered diagram in `docs/architecture.md`; scroll the data-flow
table and the ADR log.

**Say:**
- "The design follows the **medallion** pattern — bronze, silver, gold — with a
  **Kimball star schema** at the gold layer." Trace the flow on the diagram:
  CSVs → raw → staging → star schema → aggregates → BI.
- "A few decisions I'd call out." Pick **2–3**, don't read the whole log:
  - "**One codebase, two warehouses.** The same dbt models run on Postgres for
    fast local iteration and Snowflake for production — and the 127 tests pass
    identically on both."
  - "**Two orchestrators on purpose.** Airflow runs the DAG locally; in the cloud
    a scheduled Fargate task runs the *same* container once a day. No always-on
    compute — it costs a couple of dollars a month."
  - "**SCD2 on products** so I can join an order line to the product *as it was*
    when the order was placed."
- "I keep an ADR log so every choice has a written rationale — that's what this
  table is."

## Scene 3 — The pipeline running · 2:30–4:00

**Show:** terminal. Run a quick slice (don't wait on a full build live — either
pre-build or show a `--select`):

```bash
python scripts/dbt.py build --select staging
python scripts/ge_validate.py     # raw-layer data quality gate
```

**Say:**
- "Ingestion is Python — a loader that dispatches to Postgres or Snowflake behind
  one environment switch, with a row-count check after every load."
- "Transforms are dbt. Here's the lineage" — *(optionally show `dbt docs serve`
  graph)* — "staging views, ephemeral rollups, then the facts and dimensions."
- "Data quality is two layers. **Great Expectations** validates the **raw** data
  the moment it lands — a source contract: keys present, review scores 1 to 5,
  no negative prices." (Let the green `ge_validate` summary show.)
- "And **dbt's 127 tests** own the modelled layers — uniqueness, relationships,
  accepted values. Each failure points at the right layer."

## Scene 4 — CI/CD · 4:00–5:00

**Show:** the GitHub Actions run page (3 green jobs); briefly,
`.github/workflows/ci.yml`.

**Say:**
- "Every push runs the whole thing in CI — with no credentials."
- "The trick: the real CSVs are gitignored, so I commit a **small,
  referentially-consistent sample**. CI spins up a throwaway Postgres, runs the
  full pipeline against the sample, and all 127 dbt tests pass exactly like
  production."
- "Three jobs: lint and unit tests, the full pipeline on the sample, and a build
  of the deployment image so the cloud container can't silently break."

## Scene 5 — Dashboards & business insights · 5:00–7:00

**Show:** the Power BI report (or `dashboards/` screenshots); then
`docs/business-insights.md`.

**Say (lead with the insight, not the chart):**
- "The whole point is decisions, so here's what the data says."
- "**Delivery is the single biggest driver of satisfaction.** On-time orders
  average 4.3 stars; late ones average 2.6, and nearly half get a 1-star review.
  Hitting the delivery date is almost the entire satisfaction story."
- "**Retention is about 3%.** Measured on the true customer key, only 3 in 100
  customers ever buy again — this is an acquisition business, and that's the
  biggest untapped opportunity."
- "**Revenue is concentrated** — São Paulo alone is 37% of GMV and the top three
  states are 62%. SP is also the fastest to deliver, which is exactly why it
  converts and retains better."
- "Every number there is queried live from the gold marts — nothing hand-typed."

## Scene 6 — Close · 7:00–7:45

**Show:** back to the README (roadmap all-green) or your face cam.

**Say:**
- "So that's the project: ingestion, a tested two-warehouse dbt star schema,
  Airflow and a Fargate cloud deploy, CI with data-quality gates, and a BI layer
  that answers real business questions."
- "It's all on GitHub with docs and an ADR log for every decision. Thanks for
  watching — links are in the description."

## Delivery tips

- **Don't read code line by line.** Show it for a beat, narrate the idea.
- **Pre-build** anything slow; never watch a progress bar on camera.
- If you fumble a sentence, pause and redo the sentence — trim in post.
- Keep energy up on Scene 5; that's the part a hiring manager remembers.
- Put the repo link and a 2-line summary in the Loom description.
