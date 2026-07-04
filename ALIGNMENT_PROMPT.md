# Prompt — Align the codebase's Global Tuning Matrix (GTM) with its FSD, without breaking anything

> **How to use this file:** paste it to Claude Code as the task. It is written as an executable,
> phased plan. **Do the analysis phase first and produce a plan for review before writing code.** Every
> phase must leave the repo green (all existing tests pass) and behaviourally identical until an explicit
> cutover. Do **not** delete anything until the deprecation phase.

---

## 0. Role, context, and the single most important rule

You are working in the **AML Detection Framework** (branch `prod-setups`). The **Global Tuning Matrix
(GTM)** is currently mis-modelled in code: it stores **model/layer scoring parameters** that, per the
GTM Functional Specification, do **not** belong in the GTM. Your job is to **relocate those layer
parameters to their proper layers (with storage + serving + admin UI)** and align the GTM to hold only
**business threshold values**, **in a fully backward-compatible, phased way**.

**THE SINGLE MOST IMPORTANT RULE:** *nothing may break at any step.* Every commit keeps the full test
suite green and the runtime behaviour identical until a deliberate, flagged cutover. Prefer **additive**
changes, **dual-read with fallback**, **feature flags**, and **deprecate-don't-delete**. If a step would
change a resolved value or a decision, stop and surface it.

### Authoritative sources (read these first)
- **The GTM FSD** — `docs/gtm/` (28 page images, *GAMMA Framework — Functional Specification: Global
  Tuning Matrix*). This is the design authority.
- **`docs/architecture/L3_L4_SIGNAL_AGGREGATION_AND_RISK_APPETITE.md`** — the design doc that already
  distils the FSD and documents the exact divergences (§3.7, §12). Treat its §3 as the correct GTM model.
- Repo conventions: `docs/DEVELOPER_GUIDE.md`, `CLAUDE.md`, the per-module READMEs.

### Hard scope guardrails
- **ONLY touch production code:** `platform/`, `services/`, `ui/`, `infrastructure/` (for DDL/migrations),
  `airflow_dags/` if strictly needed.
- **DO NOT modify `backend/` or `frontend/`** — they are the POC reference and are frozen. (They contain
  their own copies of these fields; ignore them entirely.)
- Follow repo conventions: **Polars** for data, **Pydantic** contracts as source of truth, services use a
  `src/<pkg>/` layout, the **Risk Typology (`RTxx`)** is the spine, inter-layer payloads live in
  `aml_core/schemas.py`, Delta tables in `aml_core/contracts.py`.

---

## 1. What the FSD says the GTM *is* (the target model)

Ground everything in these FSD facts (all verified against `docs/gtm/`):

1. **The GTM is a Layer-2 control plane.** Every L2 model, before running detection, does a Feature Query
   (L1) **and a Parameter Query to the GTM** (Parameter Query API, Module 0.3). The GTM has **no**
   interface with L3 or L4.
2. **It stores business *named thresholds* by dimension.** Canonical examples from the FSD UI + data model:
   **`Min Amount`** (a monetary amount; aka *Notional Spike Amount*) and **`Recurrence Count`** (an
   integer, e.g. 3). A model may have several named thresholds, each resolved independently.
3. **Authoritative data model (Parameter Store, FSD §5.1.3):** one row per
   `(Model ID, Business Line ID, Threshold ID, Threshold Name, Dimension Key, Threshold Value, Currency
   Code, Effective From/To, Maker, Approver, Justification, Change Type)`. **One numeric value per (model,
   named threshold, dimension combination)**, versioned. **No weights, score bars, or ML parameters exist
   anywhere in the store.**
4. **Dimensions:** 5 core (Country▸top, Client Type, Product Type, Risk Level from KYC, Transaction Profile
   brackets) + custom (0..*, e.g. Currency Pair) + mandatory **Individual Threshold** (most granular).
5. **Resolution:** most-granular-first — Individual → dims (configured order) → Country → **Model-Level
   Default (EUR)**; gaps fall through.
6. **Currency (BR-T01/T02/T03):** local currency when Country active, else EUR; **the GTM does NOT convert
   currency** (maker pre-converts; mismatched currency rejected); **values must be positive numerics**.
7. **Governance:** maker-checker / third-eye on every change (no self-approval; `GTM_Approver` role),
   immutable versioned history (≥7-yr retention), point-in-time reconstruction, and every Query API
   response carries the `version_id` used.
8. **Query API contract (0.3):**
   `request { model_id, threshold_id?, business_line_id, evaluation_date, <active dimension values>,
   custom_dimensions?, focus_id?, focus_type? }` →
   `response { resolved_threshold, currency_code, resolved_at_level, dimension_key_used, version_id,
   effective_from, is_individual_threshold, fallback_used }`.
9. **Change sources:** manual (risk managers/model owners) **and** the **Feedback Loop** (auto-proposed
   threshold changes from signal-conversion/FP analysis, routed through the same maker-checker workflow).

**Corollary — what does NOT belong in the GTM:** closeness-to-threshold normalisation, the recurrence
boost formula, ATL/BTL **score bars**, the **L3 consolidation weight**, the **L4 uncertain bands** and
interactive-learning thresholds, and all ML learned parameters/feature weights. These are **layer logic**.

---

## 2. The current code and the exact divergences

### 2.1 Where the GTM lives today
- `platform/aml_core/aml_core/gtm.py` — `TuningMatrixEntry` (a **flat** Pydantic entry), `specificity_score`,
  `resolve`, `redis_key`, `_synthetic_default`.
- `services/tuning_matrix/` — `api/` (`app.py`, `main.py`, `repository.py`, `sql/tuning_matrix.sql`),
  `version_manager/`, `redis_publisher/`.
- `services/model_layer/dispatch_coordinator/src/gtm_resolver.py` — `resolve_params()` builds a
  `TuningMatrixParams` dict from an entry (currently includes the layer fields).
- `services/signal_aggregator/src/signal_aggregator/gtm_loader.py` — `load_active_gtm_entries()`.

### 2.2 `TuningMatrixEntry` fields — classify each
| Field | Verdict | Target home |
|-------|---------|-------------|
| `id`, `risk_typology`, 5 core dims, `extra_dimensions`, `currency`, `is_active`, `version`, `updated_*` | keep (structural) | GTM |
| `occurrence_amount_min` | **business amount** → keep | GTM (a *Min Amount* named threshold) |
| `expected_amount` | **business amount** (notional denominator) → keep | GTM (a *Notional/Expected Amount* named threshold) |
| `recurrence_count_min` | **business count** → keep | GTM (*Recurrence Count*) |
| `recurrence_period_days` | **business window** → keep | GTM (recurrence window) |
| `occurrence_threshold` (≈0.6) | **layer score bar** → MOVE | **Layer 2** scoring config |
| `btl_threshold` (≈0.3) | **layer score bar** → MOVE | **Layer 2** scoring config |
| `score_weight` (1.0) | **layer consolidation weight** → MOVE | **Layer 3** consolidation config |

> Optional nuance to raise with the maintainer: the FSD allows an **ML static "minimum escalation score"**
> to live in the GTM. `occurrence_threshold` is *not* that (it's the rule closeness bar), so it moves to L2.
> If a genuine ML escalation cut-off is later needed, add it to the GTM as a named threshold — do not
> conflate it with `occurrence_threshold`.

### 2.3 Consumers to migrate (production only — ignore `backend/`)
- `score_weight` → `services/signal_aggregator/.../aggregation_engine/engine.py`,
  `dispatch_coordinator/src/gtm_resolver.py`, `signal_aggregator/.../gtm_loader.py`.
- `occurrence_threshold` + `btl_threshold` → `model_layer/rule_engine/.../executor.py`,
  `rule_engine/.../rule_dsl.py`, `dispatch_coordinator/src/gtm_resolver.py`,
  `model_layer/serving/fastapi_server/src/aml_serving/runners/rule_runner.py`.
- (Keep-in-GTM fields have many consumers — leave those reads unchanged.)

### 2.4 UIs today (`ui/admin_portal/src/pages/`)
`TuningMatrixPage.tsx` (GTM editing), `PolicyEditorPage.tsx` (L4 zero-tolerance matrix),
`ModelRegistryPage.tsx`, `FeatureRegistryPage.tsx`.

---

## 3. Target architecture — new homes for the moved parameters

Create **one small config surface per layer**, each with: a Postgres table + a Pydantic contract + a
loader/resolver + an admin API + an admin UI. Keep them typology-keyed (and optionally dimension-aware,
mirroring the GTM's context) so they can vary per segment if needed.

### 3.1 Layer 2 — Model Scoring Config (`occurrence_threshold`, `btl_threshold`)
- **Store:** `model_layer.scoring_config` — `(risk_typology, [optional dimension context], occurrence_threshold,
  btl_threshold, version, is_active, updated_at, updated_by)`. Start typology-keyed (dimension-context
  optional, future-proofed).
- **Contract:** `ScoringConfig` in `aml_core/schemas.py` (or a new `aml_core/model_config.py`), with a
  `resolve_scoring(typology, context)` helper mirroring GTM `resolve()` (defaults preserve today's 0.6/0.3).
- **Consume:** `rule_engine` (`executor.py`, `rule_dsl.py`) and the serving `rule_runner.py` read the bars
  from `ScoringConfig`, not from the GTM params.
- **UI:** a new `ModelScoringConfigPage.tsx` (or a "Scoring" tab on `ModelRegistryPage.tsx`).

### 3.2 Layer 3 — Consolidation Weights (`score_weight`)
- **Store:** `signal_aggregator.consolidation_weight` — `(risk_typology, [optional dimension context],
  weight, version, is_active, updated_at, updated_by)`.
- **Contract:** `ConsolidationWeight` + a `resolve_weight(typology, context)` helper (default 1.0,
  `MIN_WEIGHT=0.01` floor stays in the aggregation engine).
- **Consume:** `aggregation_engine/engine.py` reads `wᵢ` from here instead of `entry.score_weight`.
- **UI:** a new `ConsolidationWeightsPage.tsx` (typology → weight grid).

### 3.3 Layer 4 — Risk Appetite Config (bands + interactive-learning thresholds)
- These are currently hardcoded constants in `risk_appetite` (`UNCERTAIN_LOW=0.40`, `UNCERTAIN_HIGH=0.70`,
  `FP_DAMPEN_THRESHOLD=0.80`, `TP_BOOST_THRESHOLD=0.60`, `MIN_SUPPORT=3`) — not in the GTM and not in the
  DB. Externalise them too, so L4 has one config home.
- **Store:** `risk_appetite.appetite_config` — a small keyed config (global + optional per-jurisdiction).
- **Contract:** `AppetiteConfig`; loaders in `escalation_router` / `historical_context` read from it (with
  the current constants as defaults).
- **UI:** extend `PolicyEditorPage.tsx` with an "Appetite bands & learning thresholds" section.

> All three stores follow the **same shape and the same governance** as the GTM would ideally have
> (versioned, `updated_by`, `is_active`). You may reuse the GTM `resolve()` specificity logic for the
> optional dimension-aware variants.

---

## 4. Phased execution plan (each phase = green tests, no behaviour change)

### Phase 0 — Analysis & plan (no code changes)
1. Read `docs/gtm/` and the L3/L4 doc §3/§7/§12.
2. Produce a written **impact map**: every read/write of `score_weight`, `occurrence_threshold`,
   `btl_threshold` in production code (files + line refs), plus the serving/`gtm_resolver` serialization
   and the `tuning_matrix` SQL/API/UI.
3. Confirm the field classification in §2.2 and the target stores in §3.
4. **Present the plan (phases, files, migrations, flags) for review before writing any code.**

### Phase 1 — Add the new layer config stores (additive, dormant)
- Add the 3 tables (DDL/migrations under `services/<svc>/.../sql/` or `infrastructure/`), the Pydantic
  contracts, the loaders/resolvers, and the admin API endpoints.
- **Seed each new store from the *current* GTM values** so that, at cutover, resolved values are identical.
  (Read the active GTM entries and project `score_weight`/`occurrence_threshold`/`btl_threshold` into the
  new tables.)
- Nothing consumes them yet. All existing tests still pass.

### Phase 2 — Dual-read migration of consumers (flagged, behaviour-preserving)
- In each consumer, introduce a **dual-read with fallback**:
  `value = layer_config.resolve(...) ?? gtm_entry.<field>` behind a feature flag
  (`AML_USE_LAYER_CONFIG_L2`, `_L3`, `_L4`; default **off** → reads GTM exactly as today).
- Add **parity tests**: for a representative set of typologies/contexts, assert the resolved bar/weight is
  **identical** whether read from the GTM field or the new store (because Phase 1 seeded them equal).
- Keep `gtm_resolver.resolve_params()` and `resolve()` **signatures stable**. `resolve_params()` may still
  return the params dict, but source the moved fields from the layer stores when the flag is on.
- Flip the flags **on** only after parity tests pass; the full suite must stay green with flags both off
  and on.

### Phase 3 — Admin UIs for the new configs
- Build `ModelScoringConfigPage.tsx`, `ConsolidationWeightsPage.tsx`, and the `PolicyEditorPage.tsx`
  appetite section. Reuse `@aml/shared` (DataTable, forms, `useAsync`, RBAC). Wire routes + nav in each
  app's `App.tsx`. Respect the UI gotchas in `ui/CLAUDE.md` (`useAsync().error` is a string; add any new
  lucide icons to the local `shared.ts` allow-list; keep `tsc` clean).
- Keep the existing `TuningMatrixPage.tsx` working (it will lose the moved fields in Phase 4).

### Phase 4 — Deprecate the moved fields in the GTM (still no deletion of data)
- With flags on and stable in an environment, mark `score_weight`, `occurrence_threshold`, `btl_threshold`
  on `TuningMatrixEntry` as **deprecated** (docstring + `Field(deprecated=True)` if supported), stop
  writing them from the GTM UI, and remove them from `gtm_resolver.resolve_params()` and the GTM UI form.
- Remove the columns from the GTM SQL/`gtm_loader` **only after** confirming no production consumer reads
  them and a release has baked. Provide a migration that drops them (reversible; keep a backup/export).

### Phase 5 — (Optional, larger) Reshape GTM to the FSD data model
Only if the maintainer approves (this is a structural change): introduce the FSD **named-threshold ×
dimension-key** model — `gtm.named_threshold(model_id, threshold_id, threshold_name, primary?)` +
`gtm.threshold_value(threshold_id, dimension_key, value, currency_code, effective_from, effective_to,
maker, approver, change_type)` — with an **adapter** that preserves the existing `resolve()` /
`resolve_params()` interface so L2 keeps working. Add the FSD governance (maker-checker, no self-approval,
`version_id` in responses, point-in-time reconstruction), currency rules (local/EUR, no conversion,
positive-only), the Model-Level Default, and (optionally) the 6 FSD UI screens. Keep the old flat table as
a compatibility view during migration.

---

## 5. Cross-cutting requirements

- **Backward compatibility:** the `resolve()`/`resolve_params()` public interfaces must not break; add,
  don't change, wherever possible. Every phase behind a flag defaulting to current behaviour.
- **Seeding = identical behaviour:** Phase-1 seeds must reproduce today's resolved values exactly. Add a
  one-shot script that reads active GTM entries and writes the layer stores.
- **Currency & validation (when you touch GTM values):** enforce **positive-only** threshold values and the
  **local-currency/EUR** rule; never auto-convert currency.
- **Feedback-loop link:** the feedback loop's threshold recommendations target **GTM business thresholds**
  (amounts/counts) — keep that intact; it must **not** propose changes to the moved layer params.
- **Golden Thread / audit:** the new config stores must be versioned + `updated_by` and, ideally, follow the
  GTM's maker-checker pattern so risk managers retain governance over weights and bars too.
- **Contracts first:** update `aml_core` contracts and the relevant module READMEs + `docs/DEVELOPER_GUIDE.md`
  and `CLAUDE.md` files to reflect the new layer config homes and the corrected GTM boundary.

---

## 6. Acceptance criteria (definition of done)

- [ ] `TuningMatrixEntry` no longer *sources* `score_weight`/`occurrence_threshold`/`btl_threshold` for
      runtime (deprecated, then removed in Phase 4); the GTM holds only business values.
- [ ] L2 reads its score bars from `model_layer.scoring_config`; L3 reads its weight from
      `signal_aggregator.consolidation_weight`; L4 reads its bands from `risk_appetite.appetite_config`.
- [ ] Each new config has: table + Pydantic contract + resolver + admin API + admin UI (versioned,
      RBAC-guarded, maker-checker-aligned).
- [ ] **Parity tests prove resolved values/decisions are identical** before vs after cutover on a seeded
      dataset.
- [ ] The **entire existing test suite stays green** with flags off *and* on. No behaviour change until
      cutover; no data deleted before Phase 4's reversible migration.
- [ ] `backend/` and `frontend/` are untouched.
- [ ] Docs updated: `docs/architecture/L3_L4_SIGNAL_AGGREGATION_AND_RISK_APPETITE.md` §3.7/§12,
      the affected module READMEs, and the relevant `CLAUDE.md` files.

---

## 7. Verification commands (run at every phase — must stay green)

```bash
# platform libs
pip install -e platform/aml_core -e platform/common_utils -e platform/data_contracts

# the directly-affected suites (each service uses src/<pkg>; --import-mode=importlib)
PYTHONPATH=services/model_layer/rule_engine/src pytest services/model_layer/rule_engine/tests --import-mode=importlib
PYTHONPATH=services/model_layer/composition   pytest services/model_layer/composition/tests   --import-mode=importlib
PYTHONPATH=services/signal_aggregator/src     pytest services/signal_aggregator/tests          --import-mode=importlib
PYTHONPATH=services/risk_appetite/src         pytest services/risk_appetite/tests              --import-mode=importlib
PYTHONPATH=services/tuning_matrix/api         pytest services/tuning_matrix/api/tests          --import-mode=importlib
# (on this machine: export POLARS_SKIP_CPU_CHECK=1 and use polars-lts-cpu, per CLAUDE.md)

# UI (each app standalone)
cd ui/admin_portal && npm install && npm run build   # tsc must be clean; repeat for touched apps
```

---

## 8. Guardrails / stop conditions
- **Stop and ask** before: deleting any column/field/data; changing a `resolve()` signature; flipping a
  feature flag on by default; or any change that alters a resolved value or a disposition.
- If a parity test fails, **do not proceed** — the seed or the dual-read is wrong; fix it first.
- Keep each phase in its own commit(s) with a clear message; do not bundle a behaviour change with a
  refactor.
- We are on `prod-setups`; do not commit to `main`. Commit only when asked.

---

## 9. Deliverables
1. The Phase-0 impact map + plan (for review).
2. The three layer config stores + contracts + resolvers + admin APIs + UIs.
3. The seed/migration scripts and the dual-read + feature flags.
4. Parity tests + green suites at every phase.
5. Updated docs (L3/L4 doc, READMEs, CLAUDE.md).
6. (Optional, if approved) Phase-5 FSD-aligned GTM data model + governance + screens.
