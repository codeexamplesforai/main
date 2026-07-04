# Prompt — Remove RabbitMQ; deliver alerts to a third party via JSON (non-breaking)

> Paste to Claude Code. **Analyze first, show the plan before editing.** Do **not** touch `backend/` or
> `frontend/`. Keep public function signatures stable; keep tests green; commit only when asked.

**Context:** We have no RabbitMQ. RabbitMQ is used at only two *edge* points — outbound alert delivery
and inbound feedback ingestion — never in the detection core (L1–L4 use Delta). We push alerts to a
third-party investigation system as a **JSON payload**; they investigate and (optionally) return
TP/FP outcomes. Keep the existing `CaseMgmtClient` (it already POSTs the alert JSON) and the feedback
`handle_message()` (it's transport-agnostic).

**Chosen design (implement this — not one of several options): Outbox + Airflow HTTP push.**
L5 writes each alert's JSON to a durable **outbox** (S3/Delta or Postgres — stores we already have); an
**Airflow task** reads pending rows and **HTTP-POSTs** them to the third party via `CaseMgmtClient`, with
retries/backoff and a `FAILED` state as the dead-letter. Do **not** use a Redis broker, Celery, Kafka, or
a direct synchronous POST from the pipeline — the outbox + Airflow push is the decided approach because it
preserves RabbitMQ's guarantees (durability, retry, DLQ, backpressure) using existing infrastructure.

## 1. Outbound — replace the Celery/RabbitMQ distributor with an Outbox + push
- Add an **outbox** table `aml.alert_outbox` (Delta via `aml_core/contracts.py` `TABLES`, or a Postgres
  table) with `{alert_id, alert_json, status(PENDING|DELIVERED|FAILED), attempts, last_error,
  created_at, updated_at, namespace}`. L5 (`alerts_packaging`) writes each packaged alert here as
  `PENDING` instead of enqueuing a Celery task.
- Add a **delivery worker as an Airflow task** (`airflow_dags/`) that: selects `PENDING` (and retry-due
  `FAILED`) rows, POSTs each via the existing **`CaseMgmtClient`** (repoint it at the third-party endpoint
  + auth), marks `DELIVERED` on 2xx, increments `attempts`/records `last_error` on failure with
  exponential backoff, and leaves retry-exhausted rows in `FAILED` for operator review (the DLQ
  equivalent). Idempotent by `alert_id`.
- **Remove** `celery_distributor/distributor.py`'s Celery app/broker usage; keep a thin
  `deliver_alert(alert_json)` that calls `CaseMgmtClient` directly (so existing callers/tests still work).
- Delete `celery`/`kombu` from `services/alerts_packaging/pyproject.toml` + its Dockerfile once unused.

## 2. Inbound — replace the RabbitMQ consumer with a webhook OR batch import
- Keep `feedback_loop/ground_truth_ingestor/ingestor.py::handle_message()` unchanged (transport-agnostic).
- Replace `consume_forever()` (the `pika` AMQP loop) with **one** of:
  - **(a) Webhook** — a small FastAPI endpoint (e.g. `POST /v1/feedback/outcomes`) that the third party
    calls with an outcome JSON; it invokes `handle_message()`. Add auth + validation.
  - **(b) Batch import** — an Airflow task that reads outcome files/an export the third party drops, and
    calls `handle_message()` per record.
- Delete `pika` from `services/feedback_loop/pyproject.toml` once unused.
- **Note in the plan:** without a return channel the feedback loop's outcome-driven learning (threshold
  optimization, interactive-learning boost/dampen) is starved — pick (a) or (b).

## 3. Config + infra cleanup
- In `platform/common_utils/common_utils/config.py`: remove/deprecate `rabbitmq_url`; add
  `third_party_alert_url`, its auth (token/mTLS), and outbox settings (batch size, max attempts, backoff).
  Keep a no-op alias if anything still imports `rabbitmq_url`.
- Infra: delete `kubernetes/aml-app/rabbitmq.yaml`; remove RabbitMQ from `aml-app/kustomization.yaml`,
  `app-services.yaml`, and the base `networkpolicies.yaml` / `resourcequotas.yaml` / `priorityclasses.yaml`
  / `storageclasses.yaml`. Add a **NetworkPolicy egress** allowing `alerts_packaging` (and the webhook, if
  used) to reach the **third-party endpoint**; add ingress for the webhook if used. Remove the RabbitMQ
  StatefulSet + PVCs.

## Guardrails
- Detection core (L1–L4) must be untouched. Keep `CaseMgmtClient` + `handle_message()` behaviour.
- Feature-flag the transport if helpful; keep `deliver_alert`/`handle_message` importable so existing
  tests pass. Run `alerts_packaging` + `feedback_loop` test suites green.
- Preserve RabbitMQ's guarantees via the outbox: durability (persisted rows), retry (attempts+backoff),
  DLQ (FAILED status), backpressure (pipeline writes rows regardless of third-party availability).
- Scope: `platform/`, `services/`, `infrastructure/`, `airflow_dags/`, `ui/` (add an admin view of the
  outbox/DLQ if trivial). Not `backend/`/`frontend/`.
