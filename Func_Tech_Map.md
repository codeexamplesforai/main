# AML Detection Framework — Functional ↔ Technical Module Map

**Purpose:** Bridge between the *functional spec* (what the system does, in business/compliance terms) and the *technical implementation plan* (services, infra, code). Every functional module maps to one or more technical modules, and every technical module belongs to exactly one functional module (or is a cross-cutting platform concern).

This map is the single artifact that lets a compliance officer, a risk manager, an architect, and an engineer all point at the same thing and mean the same thing.

---

## How to read this document

- **F-modules** (F1, F2, …) are *functional* modules. They are what the business sees. They come from the functional spec.
- **T-modules** are *technical* modules. They are services, libraries, or jobs. They come from the implementation plan.
- **Vertical flow** = the 5 detection layers + the data sources upstream + the investigation system downstream. This is the data pipeline.
- **Cross-cutting** = capabilities that touch many layers: the Tuning Matrix, the Feedback Loop, the Sandbox, Observability, and the Golden Thread / Lineage discipline.

A functional module is "delivered" only when all its technical modules pass their gates. A technical module exists only to serve a functional module — if you can't trace it back, delete it.

---

## Part A — Functional module taxonomy

```
                            ┌─────────────────────────────────────┐
                            │   F0. Data Sources (upstream)       │
                            │   AML Data Layer / TP App / Lists   │
                            └──────────────────┬──────────────────┘
                                               ▼
              ┌─────────────────────────────────────────────────────────┐
              │                  DETECTION FRAMEWORK                     │
              │                                                          │
              │  ┌──────────────────────────────────────────────────┐   │
              │  │  F1. Feature Factory (Layer 1)                   │   │
              │  └──────────────────────────────────────────────────┘   │
              │                       ▼                                  │
              │  ┌──────────────────────────────────────────────────┐   │
              │  │  F2. Model Layer (Layer 2)                       │◄──┤
              │  │     - Targeted + Anomaly + Recurrence            │   │
              │  └──────────────────────────────────────────────────┘   │
              │                       ▼                                  │
              │  ┌──────────────────────────────────────────────────┐   │
              │  │  F3. Signal Aggregator (Layer 3)                 │   │
              │  └──────────────────────────────────────────────────┘   │
              │                       ▼                                  │
              │  ┌──────────────────────────────────────────────────┐   │
              │  │  F4. Risk Appetite (Layer 4)                     │◄──┤  F7. Global Tuning
              │  │     - Track A + Track B + Interactive Learning   │   │      Matrix (cross-cut)
              │  └──────────────────────────────────────────────────┘   │
              │                       ▼                                  │
              │  ┌──────────────────────────────────────────────────┐   │
              │  │  F5. Alerts Packaging & Distribution (Layer 5)   │   │
              │  └──────────────────────────────────────────────────┘   │
              └──────────────────┬──────────────────────────────────────┘
                                 ▼
                            ┌────────────────────────────────┐
                            │   F6. Smart Investigation       │
                            │   (Case Management — downstream)│
                            └────────────┬───────────────────┘
                                         │
                ┌────────────────────────┼────────────────────────┐
                ▼                        ▼                        ▼
    ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
    │  F8. Feedback Loop   │ │  F9. Simulation       │ │ F10. Observability   │
    │  (closed-loop opt.)  │ │      Sandbox          │ │      & Audit         │
    └──────────────────────┘ └──────────────────────┘ └──────────────────────┘
                  (all three are cross-cutting — touch every layer)
```

There are eleven functional modules (F0–F10). Six are vertical (F0–F5 + F6 downstream). Five are cross-cutting (F7–F10 plus the implicit data-contracts/lineage discipline that runs through everything).

---

## Part B — Functional module specifications and technical module assignments

For each F-module, the same structure: business purpose, functional sub-capabilities (verbatim from the spec where possible), the technical modules that implement it, data contracts it owns, UIs that touch it, and the build phase.

### F0. Data Sources

**Functional purpose:** Provide the raw inputs the framework needs. Three primary upstream systems plus reference data.

**Functional sub-capabilities:**
- F0.1 — Raw transactional feeds (AML Data Layer)
- F0.2 — Entity demographics & KYC data (AML Data Layer)
- F0.3 — Transaction profiles & expected behaviour metrics (TP App)
- F0.4 — Watchlists, sanctions, reference data (List Management)

**Technical modules:**

| F-sub | Technical module (from impl. plan) | Path |
|---|---|---|
| F0.1 | Txn Adapter (SFTP / SWIFT MT103 ingestion) | `services/ingestion/adapters/txn_adapter/` |
| F0.2 | KYC Adapter (Debezium CDC) | `services/ingestion/adapters/kyc_adapter/` |
| F0.3 | TP Profile Adapter (REST + webhook) | `services/ingestion/adapters/tp_adapter/` |
| F0.4 | Lists Adapter (Sanctions/PEP/VASP feeds) | `services/ingestion/adapters/lists_adapter/` |
| F0.4 | Adverse Media Adapter | `services/ingestion/adapters/adverse_media_adapter/` |
| F0.* | Validation Gateway (Great Expectations) | `services/ingestion/validation_gateway/` |
| F0.* | Dead Letter Handler | `services/ingestion/dead_letter_handler/` |

**Data contracts owned:** `RawTransaction`, `IngestMetadata`, `ValidatedTransaction`, raw KYC and lists schemas.

**Storage:** Delta Lake `aml.raw_*` → Validation → Delta Lake `aml.*_validated`. Quarantine to `aml.dlq_*`.

**UI surface:** Admin Portal → Pipeline Status (DAG runs, GE failure counts, DLQ inspector).

**Build phase:** Band B, Phases 5–6.

---

### F1. Feature Factory (Layer 1)

**Functional purpose:** Stateless service that performs feature calculation and storage at the transaction, account, and client levels. The centralized data preparation engine for the entire framework.

**Functional sub-capabilities (from spec):**
- F1.1 — **Transactional Core Features (Immutable):** event-level indicators (HRG flags, tax-haven flags, round-amount, etc.), computed daily, then strictly immutable per transaction.
- F1.2 — **Entity Core Features (Latest State):** client-level attributes (PEP, KYC risk, relationship tenure, active products), refreshed daily.
- F1.3 — **Account-level features** (implicit in axis-based design): rolling-window aggregates (turnover, velocity).
- F1.4 — **Network/Graph features** (implicit, supports L2 GNN models): centrality, communities, UBO chains.
- F1.5 — **Feature Storage:** all features stored centrally (the spec says JSON; the impl. plan recommends flat Parquet for the hot path, JSON sidecar for variable-shape outputs — see §4.7 of impl. plan).
- F1.6 — **API Distribution:** any downstream model can request feature objects on-demand via API.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F1.1 | Txn Feature Engine (TFE) — ~50 features | `services/feature_factory/txn_engine/` |
| F1.2 | Entity Feature Engine (EFE) — ~30 features | `services/feature_factory/entity_engine/` |
| F1.3 | Account Feature Engine (AFE) — ~40 features | `services/feature_factory/account_engine/` |
| F1.4 | Graph Feature Engine (GFE) — ~20 features | `services/feature_factory/graph_engine/` |
| F1.5 | Feast Materializer (offline → online) | `services/feature_factory/feast_materializer/` |
| F1.5 | Feature Registry (Feast metadata CRUD) | `services/feature_factory/feature_registry/` |
| F1.6 | Feature API Service (FastAPI single-entity + Feast batch) | inside `services/model_layer/serving/fastapi_server/` (re-used) |

**Data contracts owned:** `TxnFeatures`, `EntityFeatures`, `AccountFeatures`, `GraphFeatures`.

**Storage:**
- Offline: Delta Lake `aml.features_txn`, `aml.features_entity`, `aml.features_account`, `aml.features_graph`
- Online: Redis (per-entity hash, sub-ms reads)
- Graph: Neo4j node properties

**UI surface:** Admin Portal → Feature Registry browser (definitions, owners, drift state, baselines).

**Build phase:** Band B, Phase 8.

---

### F2. Model Layer (Layer 2)

**Functional purpose:** The framework's purely objective "calculator". Evaluates features at the natural axis of activity, identifies discrete risk occurrences, scores them with a normalized score (0 ≤ S ≤ 1), and consolidates into risk-ranked Signals at the configured aggregated entity level.

**Functional sub-capabilities (from spec):**
- F2.1 — **Independent Feature Requests:** each model pulls only the features it needs, no central data router.
- F2.2 — **Parameter Fetching:** each model queries the Global Tuning Matrix for jurisdictional parameters.
- F2.3 — **Axis-based Evaluation:** Transaction / Account / Client (extensible: Product, Network).
- F2.4 — **Occurrence Qualification & Scoring:** an occurrence is the fundamental unit; gets a localized "closeness to threshold" score; BTL occurrences still recorded.
- F2.5 — **Risk Typology Models — Rule-Based:** binary/structured, closeness-to-threshold scoring.
- F2.6 — **Risk Typology Models — Hybrid:** rule + ML/AI, e.g. jurisdiction check + NLP narrative.
- F2.7 — **Risk Typology Models — ML/AI:** graph/network analytics, micro-networks.
- F2.8 — **Unsupervised Models (Anomaly Detection):** AE/VAE, reconstruction-error scoring for zero-day patterns.
- F2.9 — **Signal Consolidation & Temporal Validation:** recurrence period (sliding window) + recurrence count → ATL vs BTL signal.
- F2.10 — **Signal Payload Output:** comprehensive payload with full occurrence lineage and transaction-ID mapping.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F2.1, F2.2 | Dispatch Coordinator (Spark driver dispatch logic) | `services/model_layer/dispatch_coordinator/` |
| F2.3 | Axis Router (per-model axis selection, in Spark driver) | inside dispatch coordinator |
| F2.4 | Occurrence Qualification logic (per-model, in each model wrapper) | `ml_models/*/features.py` + serving wrappers |
| F2.5 | Rule Engine + Rule DSL + ported Actimize rules | `services/model_layer/rule_engine/` |
| F2.6 | Hybrid models — Structuring, RMF, Velocity, Wire-Stripping | `ml_models/hybrid/*` |
| F2.6 | NLP pipelines (spaCy/HuggingFace) | inside `services/feature_factory/txn_engine/src/nlp/` (features) + per-model NLP layers |
| F2.7 | GNN models — Funnel, Layering, Smurfing, Shell-Network | `ml_models/gnn/*` |
| F2.7 | Neo4j → PyG graph snapshot pipeline | `services/feature_factory/graph_engine/` + DVC versioning |
| F2.8 | AE/VAE models — Dormant, Unusual Cash, ATO Behavioral | `ml_models/ae_vae/*` |
| F2.9 | Recurrence Calculator (consolidation + sliding window) | `services/model_layer/signal_assembler/` |
| F2.10 | Signal Payload Assembler | `services/model_layer/signal_assembler/` |
| F2.* | Multi-model serving — CPU runners | `services/model_layer/serving/bentoml_server/` (CPU runner pool) |
| F2.* | Multi-model serving — GPU runners | `services/model_layer/serving/bentoml_server/` (GPU runner pool) |
| F2.* | On-demand single-entity serving | `services/model_layer/serving/fastapi_server/` |
| F2.* | Tuning Matrix Client (per-model parameter fetch) | `platform/common_utils/gtm_client.py` |

**Data contracts owned:** `OccurrenceScore`, `SignalPayload`, `ModelScoringRequest`, `TuningMatrixParams`.

**Storage:** Delta Lake `aml.signal_payloads` (one record per entity containing all occurrences and scores).

**UI surface:**
- Admin Portal → Model Registry browser (MLflow integration), per-model performance dashboards.
- Analyst UI → drill-down into individual occurrences and their decision drivers.

**Build phase:** Band C, Phases 9–13.

---

### F3. Signal Aggregator (Layer 3)

**Functional purpose:** The framework's "Librarian" and "Consolidator". Ingests disparate risk signals from Layer 2, groups them at the configured entity level, builds a holistic Entity Risk Matrix.

**Functional sub-capabilities (from spec):**
- F3.1 — **Ingestion of Targeted & Anomaly Signals** — both ATL and BTL.
- F3.2 — **Unified Entity Mapping** — normalize and group by org hierarchy (Country → Client).
- F3.3 — **Signal Inventory Management** — per-entity store of typology ID, classification, score, drivers.
- F3.4 — **Aggregated Risk Typology Scoring (ATL-Only)** — consolidated score per typology from ATL signals only; BTL retained for lineage.
- F3.5 — **Unsupervised Learning Integration** — anomaly score sits alongside targeted scores (dual-view).
- F3.6 — **Explainability Mapping** — link aggregated scores to underlying decision drivers.
- F3.7 — **BTL Data Preservation** — full BTL payload retained for back-testing/sampling.
- F3.8 — **Entity Risk Matrix Output** — the consolidated profile passed to L4.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F3.1 | Targeted Signal Receiver (reads `aml.signal_payloads`) | `services/signal_aggregator/src/aggregation_engine/` |
| F3.1 | Anomaly Score Receiver | same |
| F3.1 | BTL Vault Writer (preservation path) | `services/signal_aggregator/src/lineage_tracker/` |
| F3.2 | Entity Resolution Engine (Zingg/Splink) | `services/signal_aggregator/src/entity_resolver/` |
| F3.2 | Hierarchy Mapper (Country → Client unification) | `services/signal_aggregator/src/entity_resolver/` |
| F3.3 | Signal Inventory Manager (per-entity typology store) | `services/signal_aggregator/src/aggregation_engine/` |
| F3.4 | ATL-Only Score Engine | `services/signal_aggregator/src/aggregation_engine/` |
| F3.5 | Anomaly Integrator (dual-view assembly) | `services/signal_aggregator/src/anomaly_integrator/` |
| F3.6 | Driver Consolidator (score ↔ drivers map) | `services/signal_aggregator/src/aggregation_engine/` |
| F3.6 | Lineage Tracker (signal → occurrence IDs → txn IDs) | `services/signal_aggregator/src/lineage_tracker/` |
| F3.8 | Entity Risk Matrix Builder | `services/signal_aggregator/src/matrix_builder/` |

**Data contracts owned:** `EntityRiskProfile`.

**Storage:** Delta Lake `aml.entity_risk_profiles`; BTL preservation in `aml.btl_vault`.

**UI surface:** Analyst UI → Entity 360 view (all signals, ATL + BTL, anomaly score, drivers).

**Build phase:** Band D, Phase 14.

---

### F4. Risk Appetite (Layer 4)

**Functional purpose:** The final decisioning tier. Applies the organization's risk tolerance policies to the consolidated entity profile. Does *not* compute new risk scores; determines the **Escalation Path** (ATL Alert vs BTL Sample).

**Functional sub-capabilities (from spec):**
- F4.1 — **Track A: Deterministic Auto-Escalation** — high-priority ATL signals (sanctions hit, zero-tolerance breach) bypass further modelling, trigger immediate ATL alert.
- F4.2 — **Track B: Probabilistic ML Consolidator** — supervised ML classifier on the combined ATL+BTL profile, decides if the *combination* warrants escalation.
- F4.3 — **Interactive Learning (Historical Contextual Querying)** — real-time query of investigation system for past dispositions on the same client-counterparty-typology triad; scores adjusted (dampened on FP history, boosted on TP history).
- F4.4 — **Final Alert Classification** — ATL Alert (→ case mgmt) vs BTL Classification (→ sampling pool).
- F4.5 — **Decision Payload (Golden Thread)** — final disposition, escalation track, risk priority, full nested lineage, policy metadata.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F4.* | Escalation Router (routes to Track A or B) | `services/risk_appetite/escalation_router/` |
| F4.1 | Policy Engine (Track A — zero-tolerance rules) | `services/risk_appetite/policy_engine/` |
| F4.2 | ML Classifier (Track B — XGBoost/LightGBM) | `services/risk_appetite/ml_classifier/` + `ml_models/l4_classifier/` |
| F4.2/4.3 | LLM Reasoning Agent (uncertain-zone reasoner) | `services/risk_appetite/llm_reasoner/` |
| F4.2/4.3 | LLM Gateway (unified API, schema enforcement) | `services/llm/llm_gateway/` |
| F4.2/4.3 | LLM Server (on-prem vLLM) | `services/llm/llm_server/` |
| F4.2/4.3 | Prompt Registry (Git-versioned prompts) | `services/llm/prompt_registry/` |
| F4.2/4.3 | Guardrails Engine (fact validator, output schema) | `services/llm/guardrails_engine/` |
| F4.3 | Historical Context Engine (triad lookup) | `services/risk_appetite/historical_context/` |
| F4.3 | Score Adjustment Engine (FP dampening + TP boost) | `services/risk_appetite/decision_builder/` |
| F4.5 | Decision Payload Builder | `services/risk_appetite/decision_builder/` |
| F4.5 | Golden Thread serializer (lineage JSON assembly) | shared in `platform/common_utils/lineage.py` |

**Data contracts owned:** `TrackADecision`, `TrackBDecision`, `DecisionPayload`.

**Storage:** Delta Lake `aml.decisions`. LLM reasoning chain stored immutably in `aml.llm_audit` (ELK-mirrored).

**UI surface:**
- Admin Portal → Risk Appetite Matrix editor, Zero-tolerance policy editor (two-person approval), Track A vs Track B routing metrics.
- Analyst UI → decision explainability view (which track, what evidence, LLM reasoning if invoked).

**Build phase:** Band D, Phase 15.

---

### F5. Alerts Packaging & Distribution (Layer 5)

**Functional purpose:** Outbound gateway. Decouples internal detection logic from downstream investigation-system format. Constructs the comprehensive Alert Object and sends it via API.

**Functional sub-capabilities (from spec):**
- F5.1 — **Typology-Specific Alert Templates** — each risk typology has its own template; not one-size-fits-all.
- F5.2 — **Alert Object Construction** — hierarchical payload:
  - Level 1 (Executive Summary) — entity/jurisdiction context + primary escalation reason
  - Level 2 (Typology Breakdown) — per-typology evidence, scores, thresholds, recurrence, drivers
  - Level 3 (Zero-Day Context) — unsupervised anomaly score + loss contributors
- F5.3 — **API Distribution Gateway** — system-agnostic router; bulk push for batch, sync screen-return for on-demand UI.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F5.1 | Template Engine (Jinja2 per-typology templates) | `services/alerts_packaging/template_engine/` |
| F5.2 | Alert Builder (L1/L2/L3 assembly) | `services/alerts_packaging/alert_builder/` |
| F5.2 | LLM Narrative Generator (L1 executive summary) | `services/alerts_packaging/narrative_generator/` |
| F5.3 | Celery + RabbitMQ Distributor (async batch push) | `services/alerts_packaging/celery_distributor/` |
| F5.3 | API Gateway integration (Kong routing to Case Mgmt) | `services/alerts_packaging/case_mgmt_client/` |
| F5.3 | Synchronous Screen-Return endpoint (FastAPI) | `services/alerts_packaging/case_mgmt_client/` (sync mode) |

**Data contracts owned:** `Alert`, `AlertLevel1`, `AlertLevel2`, `AlertLevel3`.

**Storage:** Delta Lake `aml.alerts_published` (record of every alert sent, with response/ack from case mgmt).

**UI surface:** Analyst UI consumes Alert objects directly (L1 → L3 drill-down screens map directly to AlertLevel1/2/3).

**Build phase:** Band D, Phase 16.

---

### F6. Smart Investigation (downstream)

**Functional purpose:** Where alerts go to be investigated and dispositioned. This is the downstream Case Management System. The framework owns the *contract* with it, not the system itself.

**Functional sub-capabilities:**
- F6.1 — L1/L2/L3 Case Management consumption (receives Alert Object).
- F6.2 — Investigator disposition workflow (TP/FP/Escalated/Routine).
- F6.3 — Outcome feedback back to the framework.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F6.1 | Case Mgmt Client (outbound API) | `services/alerts_packaging/case_mgmt_client/` |
| F6.2 | Analyst UI (the *framework's* interface to investigators) | `ui/analyst_ui/` |
| F6.3 | Ground Truth Ingestor (consumes case dispositions, see F8.1) | `services/feedback_loop/ground_truth_ingestor/` |

**Note:** the Case Management System itself is upstream-of-us-as-consumers but downstream-of-us-as-producers. We integrate with it; we do not build it. The Analyst UI in our framework is what investigators actually look at when working an alert; the CMS provides the workflow scaffolding (queues, SLAs, escalation chains).

**Build phase:** UI in Band D; CMS integration is platform work in Band B.

---

### F7. Global Tuning Matrix (cross-cutting)

**Functional purpose:** Dynamic configuration and calibration engine for the Model Layer. *Not* a static lookup; a dimensional, versioned, parameter store with extensible dimensions.

**Functional sub-capabilities (from spec):**
- F7.1 — **Dimensional Flexibility** — five core dimensions (Country, Client Type, Product Type, Risk Level, Txn Profile) + extensible additional dimensions.
- F7.2 — **Variable Granularity** — a model may use all dimensions or a focused 2–3.
- F7.3 — **Parameter Injection** — models query the matrix for localized parameters (currency thresholds, expected averages).
- F7.4 — **Logic Calibration** — model code stays global/agnostic; sensitivity is tailored per jurisdiction/product via the matrix.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F7.* | Tuning Matrix API (FastAPI CRUD + versioning) | `services/tuning_matrix/api/` |
| F7.* | Tuning Matrix Version Manager (semver, audit) | `services/tuning_matrix/version_manager/` |
| F7.3 | Redis Publisher (cache for sub-ms reads) | `services/tuning_matrix/redis_publisher/` |
| F7.3 | Tuning Matrix Client library (used by every model) | `platform/common_utils/gtm_client.py` |
| F7.* | PostgreSQL schema (`gtm.parameters` table + JSONB params) | DDL in `infrastructure/postgresql/` |
| F7.* | GitOps config flow (changes go through PR + risk-manager approval + ArgoCD) | `infrastructure/argocd/` + Admin Portal |

**Data contracts owned:** `TuningMatrixParams`.

**Storage:** PostgreSQL (source of truth, JSONB params), Redis (cache, sub-ms reads).

**UI surface:** Admin Portal → Global Tuning Matrix editor (per-dimension parameter CRUD with version diff, approval workflow, propagation status).

**Build phase:** Band B, Phase 7 (must exist before model serving).

**Critical:** every model that takes a parameter MUST take it from the GTM. No hard-coded thresholds, no environment variables, no per-jurisdiction model forks. The matrix is the lever; the model is the engine.

---

### F8. Feedback Loop (cross-cutting)

**Functional purpose:** Closed-loop optimization engine. Ensures investigative outcomes directly influence future detection accuracy and policy thresholds.

**Functional sub-capabilities (from spec):**
- F8.1 — **Ingesting Ground Truth (Interactive Learning)** — continuously consume alert fates and dispositions from the investigation system.
- F8.2 — **Feature Identification & Enhancement** — analyze TPs vs FPs, identify predictive features, refine the Feature Factory (promote high-value, de-prioritize noisy).
- F8.3 — **Data-Driven Recommendations** — automated back-testing against the Tuning Matrix; recommend threshold/recurrence-count adjustments.
- F8.4 — **BTL Sampling & Back-testing** — periodic manual review of BTL classifications; root-cause analysis on any TPs found.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F8.1 | Ground Truth Ingestor (Case Mgmt → outcome store) | `services/feedback_loop/ground_truth_ingestor/` |
| F8.1 | Score Adjustment feed back to F4.3 Historical Context | (no new module — F4.3 reads from outcome store) |
| F8.2 | Feature Analyzer (SHAP on TP vs FP) | `services/feedback_loop/feature_analyzer/` |
| F8.2 | Feature promotion/demotion PR workflow | Git + Feast feature registry CI |
| F8.3 | Threshold Optimizer (Bayesian back-test) | `services/feedback_loop/threshold_optimizer/` |
| F8.3 | Recommendation Engine (formal proposal generator) | `services/feedback_loop/recommendation_engine/` |
| F8.4 | BTL Sampler (smart ranking by proximity to threshold) | `services/feedback_loop/btl_sampler/` |
| F8.4 | Manual Review Router (sends sampled BTL to analyst queue) | inside `btl_sampler/` |
| F8.4 | Root Cause Analyzer (on TP found in BTL) | `services/feedback_loop/btl_sampler/rca/` |
| F8.* | Retrain Trigger (publishes to Airflow sensor) | `services/feedback_loop/retrain_trigger/` |
| F8.* | Drift Detection (Evidently AI integration) | `observability/evidently_configs/` |

**Data contracts owned:** outcome events, recommendation proposals.

**Storage:** Delta Lake `aml.outcomes`, `aml.recommendations`, `aml.btl_review_queue`.

**UI surface:**
- Admin Portal → Recommendation review inbox (accept/reject/comment), Feature drift dashboard.
- Analyst UI → BTL review queue.

**Build phase:** Band D, Phase 16 (parallel with F5).

**The four spec sub-capabilities map to three feedback paths in the impl plan:**
- F8.1 → Path C (Model Retraining, via outcome ingest)
- F8.2 → Path A (Feature Tuning)
- F8.3 → Path B (Threshold Tuning → GTM)
- F8.4 → Path D (BTL Safety Net)

---

### F9. Simulation Sandbox (cross-cutting)

**Functional purpose:** Production-mirror execution environment for risk-free testing of new typologies, thresholds, and models on real production data before going live.

**Functional sub-capabilities (from spec):**
- F9.1 — **Production-Mirror Execution** — isolated env; thresholds and matrix params freely adjusted; runs against real historical production data.
- F9.2 — **Non-Invasive 'Shadow' Alerts** — same logic and data as live; outputs strictly partitioned and flagged as "Simulation Outputs"; never routed to analysts as ATL.
- F9.3 — **Distinct Output Visualization** — clear UI distinction; side-by-side what-if comparison.
- F9.4 — **Rapid Promotion to Production** — successful simulation transitions to live with minimal recoding.

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F9.1 | Config Override Manager (parameter, model, scope overrides) | `services/sandbox/config_override_manager/` |
| F9.1 | Sandbox Engine (executes L1→L5 in `aml-sandbox` namespace) | `services/sandbox/sandbox_engine/` |
| F9.1 | Sandbox Spark cluster (read-only on prod data, separate quotas) | K8s `aml-sandbox` namespace |
| F9.1 | Sandbox MLflow (separate experiment tracker) | `aml-sandbox/sandbox-mlflow` |
| F9.2 | Shadow Store Writer (partitioned Delta tables, `simulation_run_id` tag) | `services/sandbox/shadow_store_writer/` |
| F9.2 | Network policy enforcing no-write-to-prod | K8s NetworkPolicy in `infrastructure/policies/` |
| F9.3 | Output Viewer (sim vs prod comparator) | `services/sandbox/output_viewer/` |
| F9.3 | What-If UI (Streamlit) | `ui/whatif_ui/` |
| F9.4 | Promotion Gate (eval checks + RM approval + compliance review) | `services/sandbox/promotion_gate/` |
| F9.4 | GitOps Promotion (config PR → ArgoCD → canary) | `infrastructure/argocd/` |

**Data contracts owned:** `SimulationRunConfig`, `SimulationOutput`, `PromotionRequest`.

**Storage:** Shadow Delta Lake partitions tagged with `simulation_run_id`; sandbox MLflow experiments.

**UI surface:** What-If UI (primary); Admin Portal → Promotion Gate.

**Build phase:** Band D, Phase 16.

---

### F10. Observability & Audit (cross-cutting, implicit in spec)

**Functional purpose:** Continuous visibility into system health, model performance, data quality, and an immutable audit trail. The spec does not call this out as a layer but it is required by every functional module.

**Functional sub-capabilities:**
- F10.1 — Infrastructure & pipeline health monitoring.
- F10.2 — Data quality monitoring.
- F10.3 — Model performance monitoring (drift, PSI, ATL/BTL ratios).
- F10.4 — Business KPI monitoring (alert volume, TP/FP, SAR rate, analyst workload).
- F10.5 — Immutable audit trail (regulatory requirement).
- F10.6 — Automated response triggers (P1–P4 priorities).

**Technical modules:**

| F-sub | Technical module | Path |
|---|---|---|
| F10.1 | Prometheus (metrics collection) | `observability/prometheus/` |
| F10.1 | Grafana (dashboards) | `observability/grafana_dashboards/` |
| F10.2 | Great Expectations runner | already in F0 — Validation Gateway |
| F10.3 | Evidently AI (data + concept drift) | `observability/evidently_configs/` |
| F10.3 | Model performance dashboards | `observability/grafana_dashboards/model_perf/` |
| F10.4 | Business KPI dashboards | `observability/grafana_dashboards/business_kpi/` |
| F10.5 | ELK Stack (immutable audit log) | `observability/elk_pipelines/` |
| F10.6 | Alertmanager / PagerDuty integration | `observability/prometheus/alertmanager/` |

**UI surface:** Grafana dashboards (read), Admin Portal → audit trail viewer, drift alerts inbox.

**Build phase:** Band A, Phase 3 (skeleton); thickens throughout build.

---

## Part C — Cross-cutting concerns the spec emphasizes

These are not functional modules — they are *disciplines* that every functional module must honor. They are called out in the functional spec and need a corresponding technical mechanism in every module.

| Concept (from spec) | What it means functionally | Technical mechanism |
|---|---|---|
| **Closeness to Threshold scoring** | No binary outputs anywhere; every signal is normalized 0–1 based on how close (or far over) the threshold | Standard scoring contract in `OccurrenceScore.score: float`; rule DSL bakes this into every rule; ML models post-process to 0–1 |
| **ATL vs BTL retention** | BTL signals are never discarded — they're preserved for sampling, back-testing, and the safety net | Every layer writes both ATL and BTL to Delta Lake; F3 keeps BTL in `aml.btl_vault`; F8.4 samples from it |
| **The Golden Thread** | Every alert must be traceable back through L5→L4→L3→L2→L1→raw txn IDs with no break in lineage | Every contract carries `_run_id`, `_feature_version`, `_model_version`; the Lineage Tracker (F3.6) and Decision Payload Builder (F4.5) assemble the chain |
| **Occurrence as the fundamental unit** | The smallest detection event, scored individually before aggregation | `OccurrenceScore` is its own Pydantic type; every model output is `list[OccurrenceScore]` not just a number |
| **Axis-based evaluation** | No premature aggregation; each model evaluates at its natural axis | Model Config Registry stores `axis` per model; dispatcher routes axis-specific features only |
| **Recurrence validation** | A single occurrence rarely makes an alert; recurrence period + count must be met | F2.9 Recurrence Calculator owns this; recurrence params live in the GTM |
| **Stateless services** | Feature Factory is stateless; models are stateless | All services scale horizontally on K8s; state lives only in storage layer |
| **Global, agnostic model code** | Same code runs everywhere; localization is via Tuning Matrix | F7 GTM is the only source of jurisdictional parameters; CI rejects models with hard-coded thresholds |

---

## Part D — Reverse map: technical module → functional module

Quick lookup for engineers: "I'm working on `services/X/` — which F-module owns me?"

| Technical module path | Functional module | F-sub |
|---|---|---|
| `services/ingestion/adapters/txn_adapter/` | F0. Data Sources | F0.1 |
| `services/ingestion/adapters/kyc_adapter/` | F0 | F0.2 |
| `services/ingestion/adapters/tp_adapter/` | F0 | F0.3 |
| `services/ingestion/adapters/lists_adapter/` | F0 | F0.4 |
| `services/ingestion/adapters/adverse_media_adapter/` | F0 | F0.4 |
| `services/ingestion/validation_gateway/` | F0 + F10 | F0.* / F10.2 |
| `services/ingestion/dead_letter_handler/` | F0 + F10 | F0.* / F10.2 |
| `services/feature_factory/txn_engine/` | F1. Feature Factory | F1.1 |
| `services/feature_factory/entity_engine/` | F1 | F1.2 |
| `services/feature_factory/account_engine/` | F1 | F1.3 |
| `services/feature_factory/graph_engine/` | F1 | F1.4 |
| `services/feature_factory/feast_materializer/` | F1 | F1.5 |
| `services/feature_factory/feature_registry/` | F1 | F1.5 |
| `services/model_layer/rule_engine/` | F2. Model Layer | F2.5 |
| `services/model_layer/dispatch_coordinator/` | F2 | F2.1, F2.3 |
| `services/model_layer/signal_assembler/` | F2 | F2.9, F2.10 |
| `services/model_layer/serving/fastapi_server/` | F2 (also F1.6 API) | F2.* |
| `services/model_layer/serving/bentoml_server/` | F2 | F2.* |
| `ml_models/hybrid/*` | F2 | F2.6 |
| `ml_models/gnn/*` | F2 | F2.7 |
| `ml_models/ae_vae/*` | F2 | F2.8 |
| `ml_models/l4_classifier/*` | F4. Risk Appetite | F4.2 |
| `services/signal_aggregator/src/entity_resolver/` | F3. Signal Aggregator | F3.2 |
| `services/signal_aggregator/src/aggregation_engine/` | F3 | F3.3, F3.4, F3.6 |
| `services/signal_aggregator/src/anomaly_integrator/` | F3 | F3.5 |
| `services/signal_aggregator/src/lineage_tracker/` | F3 | F3.6, F3.7 |
| `services/signal_aggregator/src/matrix_builder/` | F3 | F3.8 |
| `services/risk_appetite/escalation_router/` | F4 | F4.* |
| `services/risk_appetite/policy_engine/` | F4 | F4.1 |
| `services/risk_appetite/ml_classifier/` | F4 | F4.2 |
| `services/risk_appetite/llm_reasoner/` | F4 | F4.2, F4.3 |
| `services/risk_appetite/historical_context/` | F4 | F4.3 |
| `services/risk_appetite/decision_builder/` | F4 | F4.5 |
| `services/llm/*` | F4 (primary), F5 (narrative) | F4.2/3, F5.2 |
| `services/alerts_packaging/template_engine/` | F5. Alerts Packaging | F5.1 |
| `services/alerts_packaging/alert_builder/` | F5 | F5.2 |
| `services/alerts_packaging/narrative_generator/` | F5 | F5.2 |
| `services/alerts_packaging/celery_distributor/` | F5 | F5.3 |
| `services/alerts_packaging/case_mgmt_client/` | F5 + F6 | F5.3 / F6.1 |
| `services/tuning_matrix/*` | F7. Global Tuning Matrix | F7.* |
| `services/feedback_loop/ground_truth_ingestor/` | F8. Feedback Loop | F8.1 |
| `services/feedback_loop/feature_analyzer/` | F8 | F8.2 |
| `services/feedback_loop/threshold_optimizer/` | F8 | F8.3 |
| `services/feedback_loop/recommendation_engine/` | F8 | F8.3 |
| `services/feedback_loop/btl_sampler/` | F8 | F8.4 |
| `services/feedback_loop/retrain_trigger/` | F8 | F8.* |
| `services/sandbox/*` | F9. Sandbox | F9.* |
| `observability/*` | F10. Observability | F10.* |
| `ui/analyst_ui/` | F6 (primary user) | F6.2 |
| `ui/admin_portal/` | F7, F8, F4, F10 | (cross-cut) |
| `ui/whatif_ui/` | F9 | F9.3 |

---

## Part E — UI ↔ functional module map

The four UIs are functional surfaces, not modules of their own. Each one is the visible face of multiple F-modules.

| UI | Primary functional modules surfaced | Primary users |
|---|---|---|
| **Analyst UI** | F5 (alerts), F3 (entity 360), F2 (occurrence drill-down), F6 (disposition), F8.4 (BTL review) | Investigators |
| **Admin Portal** | F7 (Tuning Matrix), F8.3 (recommendations), F2 (model registry), F9.4 (promotion gate), F10 (drift, audit) | Risk managers, ML ops |
| **What-If UI** | F9 (sandbox configuration, comparison) | Risk managers, data scientists |
| **Data Scientist Workspace** (JupyterHub) | F1 (feature exploration), F2 (model dev), F8.2 (feature analysis) | ML engineers |

---

## Part F — Build sequence checked against functional modules

Sanity-check that every functional module has technical modules in the right build phase.

| Functional module | Earliest tech module | Latest tech module | Band |
|---|---|---|---|
| F0. Data Sources | Adapters (Phase 5) | DLQ (Phase 6) | B |
| F1. Feature Factory | All engines (Phase 8) | Feast Materializer (Phase 8) | B |
| F2. Model Layer | Rule Engine (Phase 9) | BentoML orchestration (Phase 13) | C |
| F3. Signal Aggregator | Phase 14 | Phase 14 | D |
| F4. Risk Appetite | Phase 15 | Phase 15 (LLM last) | D |
| F5. Alerts Packaging | Phase 16 | Phase 16 | D |
| F6. Smart Investigation | Analyst UI (Phase 16) | Ground Truth Ingestor (Phase 16) | D |
| F7. Global Tuning Matrix | Phase 7 (must precede F2) | Phase 7 | B |
| F8. Feedback Loop | Phase 16 | Phase 16 | D |
| F9. Sandbox | Phase 16 | Phase 16 | D |
| F10. Observability | Phase 3 (skeleton) | Ongoing | A → continuous |

**Critical ordering invariants this confirms:**
- F7 (GTM) must exist before F2 — no model can run without parameters.
- F0/F1 must exist before F2 — no model can run without features.
- F2 → F3 → F4 → F5 is strictly sequential (each consumes the previous layer's output).
- F8 and F9 can be developed in parallel with F5 once F4 stabilizes.
- F10 must be skeletal from day one — you cannot retrofit observability.

---

## Part G — A note on what the functional spec gets right that the technical doc understates

Three concepts from the functional spec deserve more emphasis in implementation than the technical doc gives them:

1. **"Closeness to threshold" as the default scoring philosophy.** The spec explicitly says scores are 0–1 normalized based on closeness to threshold. This is a cultural rule for engineers writing rules and models — no binary outputs *anywhere*. Code review must reject any model output that is `bool` or `{0, 1}`. Even rules return floats.

2. **"Occurrence" as a first-class noun.** Engineers tend to think in terms of "signals" or "alerts." The spec is precise: the atomic unit is the *occurrence*. A signal is a recurrence-validated collection of occurrences. An alert is an escalated signal. These three are different objects, with different lifecycles. Our Pydantic schema reflects this (`OccurrenceScore` → `SignalPayload` → `Alert`); review should ensure no service collapses two of them into one.

3. **"Golden Thread" is a non-functional requirement, not a feature.** It's tempting to treat lineage as a feature of L4 alone. The functional spec says lineage must be preserved through every layer. Concretely: every Pydantic contract in `platform/data_contracts/` must include `_run_id`, `_feature_version`, `_model_version` (where applicable), and a reference to upstream IDs. We do not "add lineage later." It's day one.

These three are worth printing and pinning to the wall.
