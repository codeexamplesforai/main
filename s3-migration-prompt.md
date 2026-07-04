# Prompt — Migrate the object store from MinIO to on-prem S3 (non-breaking)

> Paste to Claude Code. Config-first, backward-compatible. **Analyze the impact and show the plan
> before editing.** Do **not** touch `backend/` or `frontend/` (POC, frozen). Commit only when asked.

**Task (AML Detection Framework, branch `prod-setups`):** swap the object store from **MinIO → our
on-prem S3-compatible store**, non-breaking.

1. **Config** — in `platform/common_utils/common_utils/config.py`, generalise the `minio_*` settings to
   S3 (`s3_endpoint`, `s3_access_key`, `s3_secret_key`; keep `lakehouse_bucket`), and **keep the old
   `minio_*` names as aliases** so existing env/deploys don't break. All env-driven (`AML_` prefix).

2. **Paths (s3a vs s3)** — in `platform/aml_core/aml_core/contracts.py`, make `path()` read the bucket
   from `settings.lakehouse_bucket` (not the hardcoded `aml-lakehouse`), and expose both a `s3a://` form
   (Spark/S3A) and a `s3://` form (the **`deltalake`/`object_store`** path expects `s3://`, not `s3a://`).

3. **`deltalake` Python package — declare + configure for S3.** This is the Rust-backed package Polars'
   `write_delta`/`scan_delta` use to read/write Delta directly on S3 (no Spark). Today it's declared in
   only 5 services but **NOT** in the shared write path — fix that:
   - **Declare it where the writes happen:** add `deltalake>=0.18.0` (pin a version verified against your
     on-prem store) + `polars-lts-cpu` to `platform/delta_helpers/pyproject.toml` **and**
     `platform/data_contracts/pyproject.toml`, so every Delta consumer gets it transitively; audit/dedupe
     the existing per-service pins (alerts_packaging, feedback_loop, risk_appetite, sandbox,
     signal_aggregator) and the undeclared consumers (feature_factory engines, ingestion, model_layer).
   - **Install it** in every service image that does Delta I/O (already handled once it's a declared dep).
   - **Configure its S3 access** (separate from Spark's S3A) — in `platform/delta_helpers/delta_helpers/io.py`,
     pass `storage_options` to the Polars `write_delta`/`scan_delta` calls, sourced from settings:
     `aws_endpoint_url`, `aws_region`, `aws_access_key_id`/`aws_secret_access_key` (or IRSA / the AWS creds
     chain), `aws_virtual_hosted_style_request` (`false` = path-style, common on-prem), `aws_allow_http`
     (`true` if the endpoint is plain http). (Equivalently via `AWS_*` env vars.)
   - **On-prem write gotcha:** unlike AWS, arbitrary S3-compatible stores may not guarantee atomic commits,
     so the deltalake writer needs a lock provider **or** `AWS_S3_ALLOW_UNSAFE_RENAME=true`. This pipeline
     writes **one job per table (single-writer)**, which is safe with that flag — set + document it; do
     **not** set it if two writers can ever hit the same table concurrently.

4. **Remove MinIO from infra** — drop `kubernetes/aml-storage/minio.yaml` from the kustomization; set
   `minio.enabled=false` and remove the minio subchart in
   `helm/aml-platform/{Chart.yaml,values.yaml,values-dev.yaml}`; remove the MinIO PVCs/StorageClass.
   Repoint **`kubernetes/aml-storage/init-jobs.yaml`** (bucket + `aml/prod/sandbox/backups` prefixes +
   **versioning** + IAM) at the external S3 (replace `mc` with `aws s3`/vendor equivalents; keep the
   Postgres-schema part). Update `secrets.example.yaml` to the S3 creds (or IRSA). Repoint every S3
   endpoint reference (`spark.yaml`, `airflow.yaml`, `flink.yaml`, `mlflow.yaml`, `serving.yaml`,
   `wandb.yaml`, `evidently.yaml`, `sandbox.yaml`, `feast_repo/feature_store.yaml`,
   `docker-compose.dev.yml`, `instance-setup/*`). Add a **NetworkPolicy egress** allowing the workload
   namespaces to reach the external S3 endpoint (replacing the in-cluster `minio.aml-storage.svc` allow).

5. **Bucket policy** — `aml-lakehouse` with **versioning ON** + an S3 lifecycle rule to **expire
   noncurrent versions after N days**. **No Object-Lock/WORM on this bucket** (it breaks Delta
   `VACUUM`/`OPTIMIZE`); reserve WORM for a separate write-once archive bucket. Note: **Delta tables are
   created on first write** — no per-table S3 setup (the `delta-spark` jars are in the Spark image; the
   `deltalake` Python package is set up in step 3).

**Guardrails:** keep `resolve()`/`write_delta*`/config public interfaces stable; keep `minio_*` aliases;
run the affected service tests green (`rule_engine`, `signal_aggregator`, `tuning_matrix`, and the
`delta_helpers` consumers); scope edits to `platform/`, `services/`, `infrastructure/`, `ui/` only.

---

### Why these specifics (context for the agent)
- The object store is already **S3-API abstracted**; MinIO was only the on-prem S3 implementation, so this
  is a config + provisioning change, not an app rewrite.
- `contracts.py` currently hardcodes `s3a://aml-lakehouse/...`; Spark/S3A wants `s3a://` but
  Polars/`deltalake` wants `s3://` — hence the dual-scheme helper.
- Delta is **not installed on S3** — it's a compute-side format (`delta-spark` jars + the `deltalake`
  Python package) writing a `_delta_log/` into the bucket; tables appear on first write.
- **Versioning, not WORM**, on the live lakehouse: Delta maintenance (`VACUUM`/`OPTIMIZE`/log-cleanup)
  deletes/rewrites objects, which Object-Lock blocks; versioning is compatible and gives physical
  recovery. Control bloat with a lifecycle rule expiring noncurrent versions.
- On AWS, prefer **IRSA** over static keys (`fs.s3a.aws.credentials.provider=WebIdentityTokenCredentialsProvider`).
