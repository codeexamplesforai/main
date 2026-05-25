# AML Detection Framework — Implementation Plan

**Companion to:** `TechDesign-AML_Detection_Framework.pdf`
**Purpose:** Concrete build sequence, module inventory, data contracts, feature factory definitions, Actimize migration map, and UI surface for the production rollout.

---

## 0. How to read this document

The technical design tells you *what* the system looks like. This document tells you *what to build, in what order, and what each module owns*. It is opinionated: ordering, schemas, and feature lists below should be treated as the default unless we have a specific reason to deviate.

Three guiding rules for the build:

1. **No layer is built before its upstream contract is frozen.** Layer 2 cannot start until the Feature Factory's output schema is signed off. Layer 3 cannot start until the Signal Payload schema is signed off. This sounds obvious; it is the most commonly violated rule in ML platforms.
2. **Every module ships with three things from day one**: a Pydantic data contract, a Great Expectations suite, and an Airflow DAG (or DAG stub). If you can't validate input, validate output, and orchestrate it, it isn't a module — it's a notebook.
3. **Actimize parity comes before Actimize replacement.** Phase 1 of model migration is "produce identical alerts to current Actimize for the same data window." Only after parity do we layer ML on top.

---

## 1. Build sequence — phases in order

The 16 phases below are the development order. Phases in the same band can be parallelized by separate squads; phases in different bands are sequential.

### Band A — Foundation (Weeks 1–6, blocking)

| # | Phase | Output | Blocks |
|---|---|---|---|
| 1 | **Infra bootstrap** | K8s cluster with 6 namespaces, RBAC, network policies, storage classes | Everything |
| 2 | **Persistent storage backbone** | MinIO + Delta Lake configured, PostgreSQL HA, Redis cluster, Neo4j cluster | All data writes |
| 3 | **Orchestration & observability skeleton** | Airflow, Spark on K8s, MLflow, Prometheus/Grafana/ELK | All pipelines |
| 4 | **Data contracts library** | Shared Pydantic models, schema registry, JSON Schema export, Great Expectations base suites | All services |

### Band B — Data plane (Weeks 5–12)

| # | Phase | Output | Blocks |
|---|---|---|---|
| 5 | **Ingestion adapters** | Txn (SFTP/MT103), KYC (CDC/Debezium), TP Profile (REST), Lists/Sanctions (file feeds) | Feature Factory |
| 6 | **Validation gateway** | Great Expectations checks, dead-letter routing, raw → validated Delta tables | Feature Factory |
| 7 | **Tuning Matrix & Config Registry** | PostgreSQL schema for GTM, Model Config Registry, Redis cache, Admin Portal config CRUD | Model Layer |
| 8 | **Feature Factory (Layer 1)** | Txn/Entity/Account/Graph engines, Feast offline+online, Feature Registry, materialization DAG | Model Layer |

### Band C — Model plane (Weeks 10–22)

| # | Phase | Output | Blocks |
|---|---|---|---|
| 9 | **Rule Engine + Actimize parity** | Spark SQL rule framework, ports of all current Actimize rules, parity test harness | ML rollout |
| 10 | **Hybrid models (XGBoost + spaCy)** | Structuring, RMF, Velocity, Wire-Stripping; MLflow registry; FastAPI serving | L3 input |
| 11 | **GNN models (PyTorch Geometric)** | Funnel, Layering, Smurfing, Shell-Network; Neo4j → DGL/PyG pipeline | L3 input |
| 12 | **Unsupervised models (AE/VAE)** | Per-entity reconstruction error scoring; baseline window pipeline | L3 input |
| 13 | **Multi-model orchestration + BentoML** | Spark driver dispatch, BentoML CPU/GPU runner pools, Signal Payload assembler | L3 |

### Band D — Decision plane (Weeks 18–28)

| # | Phase | Output | Blocks |
|---|---|---|---|
| 14 | **Signal Aggregator (Layer 3)** | Zingg entity resolution, ATL-only score engine, Entity Risk Matrix | L4 |
| 15 | **Risk Appetite (Layer 4)** | Escalation Router, Track A policy engine, Track B XGBoost classifier, LLM reasoning agent, historical context | L5 |
| 16 | **Alerts Packaging + Feedback Loop + Sandbox + UI** | L5 alert builder, Celery distribution, Ground Truth Ingestor, sandbox engine, Analyst UI + Admin Portal + What-If UI | Go-live |

A realistic timeline at full staffing (3 platform engineers, 4 ML engineers, 2 data engineers, 2 frontend, 1 SRE) is **6–8 months to production parity**, **9–12 months including ML uplift over Actimize**. Compress this only by descoping models, never by compressing the contracts or sandbox.

---

## 2. Actimize → new framework migration map

Each row is a typology / SAM model commonly present in NICE Actimize SAM deployments. The "approach" column reflects the deliberate choice between rule, ML, and ML+LLM. The reasoning column is the most important column on this page.

| Typology (Actimize equivalent) | Approach | Models used | Why this choice | LLM role |
|---|---|---|---|---|
| **Cash Transaction Reporting (CTR)** | **Rule only** | Spark SQL rule | Hard regulatory threshold ($10K US, equivalents elsewhere). Zero discretion permitted. | None |
| **Sanctions screening** | **Rule + NLP** | Fuzzy match (Jaro-Winkler, soundex), spaCy NER for entity extraction | Regulator requires deterministic, reproducible match. ML can rank candidates but cannot reject a match. | None |
| **PEP screening** | **Rule + NLP fuzzy** | Same as sanctions | Same as sanctions. | None |
| **Structuring (CTR avoidance)** | **Hybrid** | XGBoost on aggregated features + threshold-proximity rule | Pure rule produces high FP. ML learns deposit cadence, channel mix, counterparty patterns that distinguish payroll-rounding from intent. | None |
| **Rapid Movement of Funds (RMF)** | **Hybrid + GNN** | XGBoost (account features) + GNN (network features) → ensemble | RMF is half temporal (velocity) and half topological (where the money goes). Two models, weighted by L3. | None |
| **High-Risk Geography (HRG)** | **Rule + ML enrichment** | Country risk lookup + XGBoost corridor model | Country list is a regulatory input. ML refines per-corridor risk (US→PH retail remittance ≠ US→PH corporate trade). | None |
| **Funnel Account** | **GNN only** | GraphSAGE on directed money flow graph | Pure graph topology problem — many-to-one inflow followed by one-to-many or single-exit outflow. Rules cannot express this concisely. | None |
| **Layering / Round-tripping** | **GNN only** | GNN + cycle detection (Cypher) | Graph-native pattern. Detecting cycles and N-hop reachability is what graphs are for. | None |
| **Smurfing** | **GNN + Hybrid** | GNN to find coordinated counterparty clusters + XGBoost on per-transaction features | Smurfing is structuring at network scale. Needs both views. | None |
| **Shell Company Activity** | **Hybrid + GNN + LLM** | NLP on KYC docs + GNN on UBO graph + LLM on narrative | UBO chains are graph. KYC docs are text. Shell determination requires reasoning over both — exactly the LLM-uncertain zone. | **Yes** — narrative synthesis only when L4 uncertain |
| **Trade-Based ML (TBML)** | **Hybrid + LLM** | NLP on invoice/BOL text + XGBoost on price-deviation features + LLM for narrative reconciliation | TBML hinges on document understanding (over/under-invoicing, phantom shipping). Classic LLM use case. | **Yes** — primary reasoner |
| **Dormant Account Reactivation** | **AE/VAE** | Per-account autoencoder, reconstruction error | Unsupervised: "this account is behaving unlike its own history." Labels too sparse for supervised. | None |
| **Unusual Cash Activity** | **AE/VAE + Rule** | Autoencoder on profile + hard ceiling rule | Combines behavioral baseline with a regulator-enforced ceiling. | None |
| **Round Amount Activity** | **Rule** | Simple modulo + frequency rule | Trivially expressible. No ML uplift available. | None |
| **Wire Stripping** | **Hybrid (NLP)** | spaCy NER + pattern rules on SWIFT F70/F72 + XGBoost classifier | Stripping is narrative-based: missing originator, suspicious phrasing. NLP central. | None |
| **Velocity Breaches** | **Hybrid** | Profile-aware z-score + XGBoost | Velocity alone is noisy; ML conditions on profile. | None |
| **KYC Refresh Triggers** | **Rule** | Date arithmetic | Trivial. Don't ML this. | None |
| **Adverse Media** | **Rule + NLP** | Named entity matching + topic classifier | Triggered by external feed, NLP scores relevance. | None |
| **New Relationship Anomaly** | **Hybrid** | XGBoost on first-30-day behavior vs onboarding declarations | Compares declared vs actual. | None |
| **Cash-Intensive Business deviation** | **AE/VAE + Hybrid** | Per-MCC autoencoder + XGBoost | Industry-relative baseline. | None |
| **VASP / Crypto exposure** | **Rule + Hybrid** | VASP list rule + XGBoost on indirect exposure | Direct match is rule; multi-hop exposure needs ML. | None |
| **Account Takeover indicators** | **AE/VAE + Hybrid** | Behavioral AE (device, geo, channel) + XGBoost | Sudden behavioral break. | None |

### The L4 decision step — where ML alone is not enough

L4 is where the framework deliberately uses **ML + LLM together**. The reasoning is precise and worth stating:

- **Score < 0.4**: confidently BTL → no LLM, no escalation.
- **Score > 0.7**: confidently ATL → auto-escalate, LLM only for narrative generation in L5.
- **Score in 0.4–0.7** (the "uncertain zone", roughly 10–15% of cases): the **LLM is invoked as a reasoner**, not a classifier. It receives the entity's full signal portfolio, historical dispositions on similar triads (client × counterparty × typology), and is asked to adjust the score with a written rationale. The adjusted score is bounded (±0.15 of the ML score) and every reasoning step is logged for audit.

ML alone fails in the uncertain zone because the failure mode is heterogeneous: some are model-uncertain because features are missing, some because the case is genuinely novel, some because the historical pattern contradicts the current snapshot. An LLM with structured prompts and fact-grounding can read these three failure modes differently — XGBoost cannot.

### Where the LLM is *not* used (important boundary)

- Never as a classifier on raw features (hallucination risk, no calibration).
- Never on L1 or L2 numeric scoring.
- Never to decide if a sanctions hit is real.
- Never to write SAR narratives without a human in the loop.

---

## 3. Data ingestion architecture

### 3.1 Source matrix

| Source | Protocol | Cadence | Volume estimate | Adapter |
|---|---|---|---|---|
| Core Banking TXN | SFTP file drops (SWIFT MT103/MT202) | Hourly | Millions/day | `txn_adapter` |
| KYC system | Debezium CDC on Postgres/Oracle | Real-time | 10K updates/day | `kyc_adapter` |
| Third-party profile data (TP App) | REST webhooks + polling | Event + hourly | 50K events/day | `tp_adapter` |
| Sanctions/PEP lists | OFAC/UN/EU/FATF file feeds | Daily | Full reload | `lists_adapter` |
| Adverse media | Vendor API (LexisNexis/Refinitiv) | Daily | 100K records/day | `adverse_media_adapter` |
| Internal ops intel | Branch notes, manual flags | Ad-hoc | Low | `ops_intel_adapter` |

### 3.2 Ingestion pattern (uniform across all adapters)

```
Source → Adapter → Raw Delta (aml.raw_*) → Validation Gateway → Validated Delta (aml.*_validated) → Feature Factory
                                                ↓ (on failure)
                                          Dead Letter Delta (aml.dlq_*)
```

Every adapter implements one interface:

```python
class SourceAdapter(Protocol):
    def discover(self) -> list[SourceBatch]: ...
    def fetch(self, batch: SourceBatch) -> Iterator[RawRecord]: ...
    def acknowledge(self, batch: SourceBatch) -> None: ...
```

Every adapter writes a `_ingest_metadata` column alongside the record: source system, source timestamp, ingest timestamp, batch ID, adapter version, schema version. This is non-negotiable — it's the regulator's first question during an audit.

---

## 4. Feature Factory — full specification

This is the section the rest of the system depends on. Get this wrong and every model fails silently.

### 4.1 Feature engine inventory and ownership

| Engine | Owns | Input | Output table | Refresh | Mutability |
|---|---|---|---|---|---|
| **Txn Feature Engine (TFE)** | Per-transaction immutable features | `aml.txn_validated` | `aml.features_txn` | Each batch (delta) | Append-only |
| **Entity Feature Engine (EFE)** | Latest-state client attributes | `aml.kyc_validated`, `aml.client_master`, lists | `aml.features_entity` | Daily, overwrite | Overwrite (latest wins) |
| **Account Feature Engine (AFE)** | Rolling windowed aggregates | `aml.features_txn` (last 90 days) | `aml.features_account` | Each batch | Overwrite per (account, run_date) |
| **Graph Feature Engine (GFE)** | Network metrics | `aml.features_txn` + `aml.features_entity` → Neo4j | `aml.features_graph` + Neo4j node props | Weekly + on-demand | Overwrite per (entity, week) |

### 4.2 Feature list — Transaction Feature Engine (~50 features)

**Storage format**: One row per transaction, flat columns (not JSON blob — this is hot read for the model layer). Written as Delta Parquet, partitioned by `(date, jurisdiction)`. JSON blob columns reserved for non-tabular outputs (NLP token spans, SWIFT field dumps).

**Input columns used**: `txn_id, txn_date, txn_time, amount, currency, originator_account, originator_country, beneficiary_account, beneficiary_country, beneficiary_name, channel, mt_type, swift_f20, swift_f50, swift_f59, swift_f70, swift_f72, purpose_code, mcc, ...`

| Feature | Type | Logic |
|---|---|---|
| `hrg_originator` | bool | originator_country ∈ FATF high-risk list |
| `hrg_beneficiary` | bool | beneficiary_country ∈ FATF high-risk list |
| `tax_haven_flag` | bool | jurisdiction ∈ OECD non-cooperative list |
| `round_amount_1k` | bool | amount % 1000 == 0 |
| `round_amount_5k` | bool | amount % 5000 == 0 |
| `round_amount_10k` | bool | amount % 10000 == 0 |
| `just_below_ctr` | bool | amount in [ctr_threshold * 0.85, ctr_threshold) |
| `cross_border` | bool | originator_country ≠ beneficiary_country |
| `currency_conversion` | bool | originator currency ≠ beneficiary currency |
| `cash_flag` | bool | channel ∈ {CASH_DEPOSIT, CASH_WITHDRAWAL, ATM} |
| `off_hours` | bool | txn_time outside 06:00–22:00 local |
| `weekend_flag` | bool | day_of_week ∈ {Sat, Sun} |
| `swift_f70_length` | int | character length of SWIFT remittance info |
| `swift_f70_keywords` | list[str] | NLP-extracted risk keywords from F70 |
| `swift_f72_present` | bool | F72 (bank-to-bank info) populated |
| `wire_strip_indicator` | float | NLP classifier score for wire stripping |
| `tbml_keywords` | list[str] | trade-finance risk vocabulary matches |
| `crypto_keywords` | list[str] | crypto / VASP / wallet vocabulary matches |
| `originator_country_risk` | float | risk score 0–1 from country matrix |
| `beneficiary_country_risk` | float | risk score 0–1 |
| `iban_valid` | bool | IBAN check digit valid |
| `bic_valid` | bool | BIC exists in directory |
| `narrative_sentiment` | float | spaCy sentiment on free-text |
| `narrative_entities` | list[dict] | NER output: persons, orgs, locations |
| `purpose_code_risk` | float | risk weight of purpose code |
| `mcc_risk` | float | counterparty MCC risk score |
| `vasp_counterparty` | bool | counterparty name matches VASP registry |
| `charity_ngo_counterparty` | bool | counterparty matches charity registry |
| `cash_intensive_mcc` | bool | counterparty MCC ∈ cash-intensive list |
| `multi_currency_same_day` | bool | account had ≥2 currencies on same day |
| `same_day_reversal` | bool | matching opposite txn within 24h |
| `originator_new_counterparty` | bool | first interaction with this beneficiary |
| `txn_size_zscore` | float | (amount − account_mean) / account_std |
| `time_since_account_open_days` | int | days from account_open_date |
| `is_first_txn_after_dormancy` | bool | first txn after 90+ day gap |
| `pass_through_indicator` | float | similar-amount counter-transaction within 24h |
| `originator_country_velocity_score` | float | recent ramp in this corridor |
| `entity_resolution_confidence` | float | from Zingg, on beneficiary name |
| `nlp_pii_strip_required` | bool | true if NLP detected unstripped PII |
| `_run_id` | str | batch run identifier |
| `_feature_version` | str | semver of TFE logic |

(Full list of ~50 features is the engine's exhaustive output; the above is representative. Each feature has a registered entry in the Feature Registry with owner, baseline, drift threshold.)

### 4.3 Feature list — Entity Feature Engine (~30 features)

**Storage format**: One row per entity, **overwrite mode** (latest snapshot). Partitioned by `jurisdiction`. Mutable.

| Feature | Type | Logic |
|---|---|---|
| `pep_status` | enum | NONE / DIRECT / FAMILY / ASSOCIATE |
| `pep_match_score` | float | fuzzy match confidence |
| `sanctions_match_score` | float | highest fuzzy match score against any list |
| `kyc_risk_rating` | enum | LOW / MEDIUM / HIGH (from KYC system) |
| `kyc_last_refresh_date` | date | most recent refresh |
| `kyc_days_overdue` | int | days past required refresh cadence |
| `kyc_completeness` | float | 0–1, fraction of required fields populated |
| `active_products` | list[str] | currently active product codes |
| `active_product_count` | int | size of above |
| `relationship_tenure_days` | int | days since onboarding |
| `ubo_depth_max` | int | max layers in UBO chain |
| `ubo_country_set` | list[str] | distinct UBO jurisdictions |
| `ubo_high_risk_country_present` | bool | any UBO in FATF list |
| `ubo_undeclared_flag` | bool | UBO chain incomplete |
| `industry_risk_score` | float | MCC/NAICS-derived |
| `geo_risk_score` | float | home country risk |
| `client_classification` | enum | RETAIL / SME / CORPORATE / CORRESPONDENT / FI |
| `related_entity_count` | int | from entity resolution |
| `related_entity_max_risk` | float | max risk of any related entity |
| `adverse_media_flag` | bool | hit in last 12 months |
| `adverse_media_severity` | enum | NONE / LOW / MEDIUM / HIGH |
| `court_records_flag` | bool | known legal proceedings |
| `source_of_wealth_documented` | bool | |
| `source_of_funds_documented` | bool | |
| `tax_residency_count` | int | declared tax residencies |
| `multi_jurisdiction_flag` | bool | ≥2 tax residencies |
| `dormant_flag` | bool | no activity 90+ days |
| `_kyc_version` | str | snapshot version |
| `_run_id` | str | |
| `_feature_version` | str | |

### 4.4 Feature list — Account Feature Engine (~40 features)

**Storage format**: One row per `(account_id, run_date)`, partitioned by `run_date`. Rolling windowed aggregates.

| Feature | Type | Logic |
|---|---|---|
| `turnover_30d` | decimal | sum(abs(amount)) last 30d |
| `turnover_60d` | decimal | last 60d |
| `turnover_90d` | decimal | last 90d |
| `net_flow_30d` | decimal | sum(inflows − outflows) |
| `inflow_outflow_ratio_30d` | float | |
| `txn_count_30d` | int | |
| `txn_count_90d` | int | |
| `unique_counterparty_30d` | int | |
| `counterparty_herfindahl_30d` | float | concentration index |
| `new_counterparty_count_30d` | int | counterparties not seen in 90d before window start |
| `cross_border_ratio_30d` | float | fraction cross-border |
| `cash_ratio_30d` | float | fraction cash channel |
| `round_amount_ratio_30d` | float | fraction round amounts |
| `just_below_ctr_count_30d` | int | structuring proxy |
| `hrg_exposure_pct_30d` | float | % volume to/from HRG |
| `tax_haven_exposure_pct_30d` | float | |
| `avg_txn_size_30d` | decimal | |
| `txn_size_std_30d` | decimal | |
| `txn_size_p95_30d` | decimal | |
| `txn_size_median_30d` | decimal | |
| `velocity_vs_profile_zscore` | float | (current velocity − declared profile) / σ |
| `turnover_vs_profile_zscore` | float | |
| `same_day_in_out_count_30d` | int | pass-through indicator |
| `pass_through_volume_30d` | decimal | |
| `wire_to_cash_count_30d` | int | |
| `atm_freq_30d` | int | |
| `atm_amount_total_30d` | decimal | |
| `channel_diversity_30d` | float | normalized Shannon entropy over channels |
| `off_hours_ratio_30d` | float | |
| `weekend_ratio_30d` | float | |
| `dormant_to_active_flag` | bool | |
| `max_single_day_turnover_30d` | decimal | |
| `concentration_top5_counterparties` | float | volume to top 5 / total |
| `outgoing_only_flag` | bool | no inflows in window |
| `incoming_only_flag` | bool | no outflows in window |
| `layering_chain_depth_30d` | int | from graph engine cache |
| `unique_jurisdictions_30d` | int | |
| `_run_id` | str | |
| `_feature_version` | str | |

### 4.5 Feature list — Graph Feature Engine (~20 features)

**Storage format**: One row per `(entity_id, week_ending)`, partitioned by `week_ending`. Also written as Neo4j node properties for graph queries by L2 GNN models.

| Feature | Type | Logic |
|---|---|---|
| `pagerank` | float | PageRank centrality |
| `betweenness_centrality` | float | |
| `closeness_centrality` | float | |
| `degree_in` | int | |
| `degree_out` | int | |
| `degree_total` | int | |
| `clustering_coefficient` | float | |
| `community_id` | str | Louvain community |
| `community_size` | int | |
| `two_hop_max_risk` | float | max risk score of any 2-hop neighbor |
| `three_hop_high_risk_count` | int | high-risk entities reachable within 3 hops |
| `cycle_membership_count` | int | distinct cycles entity is part of (length ≤ 5) |
| `triangle_count` | int | |
| `bridge_node` | bool | removing this entity disconnects components |
| `flow_concentration` | float | top-edge volume / total volume |
| `shell_layering_depth` | int | chain of pass-through accounts |
| `velocity_in_subgraph` | float | subgraph-level money velocity |
| `roundtripping_indicator` | bool | net flow ≈ 0 with high gross flow in cycle |
| `reachable_jurisdiction_count` | int | distinct countries in N-hop ego graph |
| `counterparty_risk_avg` | float | mean risk of direct counterparties |

### 4.6 Storage choices summary

| What | Where | Format | Why |
|---|---|---|---|
| Per-txn features | Delta Lake `aml.features_txn` | Parquet, flat cols + JSON for NLP outputs | Hot read for L2, append-only fits Delta |
| Entity features | Delta Lake `aml.features_entity` | Parquet, flat | Latest-state, small per row |
| Account features | Delta Lake `aml.features_account` | Parquet, flat | Time-partitioned reads |
| Graph features | Delta Lake `aml.features_graph` + Neo4j props | Parquet + property graph | Dual read path: tabular for L2 ensemble, graph for GNN |
| Online lookup | Redis | Hash per entity | Sub-ms lookup for on-demand scoring |
| Feast registry | Feast metadata in Postgres + MinIO | Standard Feast | Point-in-time joins for training |

### 4.7 Why JSON is *not* the default

The original design hints at JSON storage for features. **Resist this for the hot path**. Flat columnar Parquet beats JSON for: predicate pushdown, schema enforcement, compression, vectorized reads in Spark/Polars, and feature drift detection (Evidently needs typed columns). JSON is reserved for genuinely variable-shape outputs: NLP spans, SWIFT field dumps, explainability traces. Use a sidecar JSON column on those rows, not a JSON-as-row pattern.

---

## 5. Data contracts — Pydantic schemas

These are the contracts every inter-module boundary must enforce. The full library lives in `platform/data-contracts/` and is imported by every service. Versioning is semver; breaking changes require a migration DAG.

### 5.1 Ingestion layer

```python
# platform/data_contracts/ingestion.py
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal

class Channel(str, Enum):
    WIRE = "WIRE"
    ACH = "ACH"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    ATM = "ATM"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    DIGITAL = "DIGITAL"
    CHECK = "CHECK"

class IngestMetadata(BaseModel):
    """Stamped on every raw record by every adapter."""
    source_system: str
    source_timestamp: datetime
    ingest_timestamp: datetime
    batch_id: str
    adapter_version: str
    schema_version: str

class RawTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")  # strict
    txn_id: str
    txn_date: datetime
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    originator_account: str
    originator_name: Optional[str] = None
    originator_country: str = Field(min_length=2, max_length=2)
    beneficiary_account: str
    beneficiary_name: Optional[str] = None
    beneficiary_country: str = Field(min_length=2, max_length=2)
    channel: Channel
    mt_type: Optional[str] = None
    swift_f20: Optional[str] = None
    swift_f50: Optional[str] = None
    swift_f59: Optional[str] = None
    swift_f70: Optional[str] = None
    swift_f72: Optional[str] = None
    purpose_code: Optional[str] = None
    mcc: Optional[str] = None
    _ingest: IngestMetadata

class ValidatedTransaction(RawTransaction):
    """Same shape; presence of this type asserts GE checks passed."""
    _validation_run_id: str
    _validation_timestamp: datetime
```

### 5.2 Feature contracts

```python
# platform/data_contracts/features.py
from pydantic import BaseModel, Field
from typing import Optional

class TxnFeatures(BaseModel):
    txn_id: str
    run_id: str
    feature_version: str
    # Geographic
    hrg_originator: bool
    hrg_beneficiary: bool
    tax_haven_flag: bool
    originator_country_risk: float = Field(ge=0, le=1)
    beneficiary_country_risk: float = Field(ge=0, le=1)
    # Amount patterns
    round_amount_1k: bool
    round_amount_5k: bool
    round_amount_10k: bool
    just_below_ctr: bool
    txn_size_zscore: float
    # Channel/time
    cash_flag: bool
    cross_border: bool
    currency_conversion: bool
    off_hours: bool
    weekend_flag: bool
    # SWIFT/NLP
    swift_f70_length: int
    swift_f70_keywords: list[str]
    wire_strip_indicator: float = Field(ge=0, le=1)
    tbml_keywords: list[str]
    crypto_keywords: list[str]
    narrative_entities: list[dict]
    # Counterparty
    vasp_counterparty: bool
    cash_intensive_mcc: bool
    originator_new_counterparty: bool
    # ... (full list per section 4.2)

class EntityFeatures(BaseModel):
    entity_id: str
    run_id: str
    feature_version: str
    pep_status: str
    pep_match_score: float = Field(ge=0, le=1)
    sanctions_match_score: float = Field(ge=0, le=1)
    kyc_risk_rating: str
    kyc_days_overdue: int
    ubo_depth_max: int
    ubo_high_risk_country_present: bool
    # ... (full list per section 4.3)

class AccountFeatures(BaseModel):
    account_id: str
    run_date: str
    run_id: str
    feature_version: str
    turnover_30d: float
    turnover_60d: float
    turnover_90d: float
    velocity_vs_profile_zscore: float
    # ... (full list per section 4.4)

class GraphFeatures(BaseModel):
    entity_id: str
    week_ending: str
    pagerank: float
    community_id: str
    cycle_membership_count: int
    shell_layering_depth: int
    # ... (full list per section 4.5)
```

### 5.3 Model scoring contracts

```python
# platform/data_contracts/scoring.py
from pydantic import BaseModel
from typing import Optional, Literal

class TuningMatrixParams(BaseModel):
    typology_id: str
    country: str
    client_type: str
    product_type: str
    risk_level: str
    txn_profile: str
    parameters: dict  # JSONB; per-typology shape
    version: int
    effective_from: str

class ModelScoringRequest(BaseModel):
    entity_id: str
    typology_id: str
    model_id: str
    model_version: str
    features: dict  # axis-specific feature subset
    params: TuningMatrixParams
    run_id: str

class OccurrenceScore(BaseModel):
    occurrence_id: str
    typology_id: str
    axis: Literal["txn", "account", "client", "product", "network"]
    model_id: str
    score: float  # 0..1
    classification: Literal["ATL", "BTL"]
    decision_drivers: list[dict]  # SHAP / rule trace
    occurrence_refs: list[str]  # underlying txn_ids etc.

class SignalPayload(BaseModel):
    entity_id: str
    run_id: str
    timestamp: str
    scores: list[OccurrenceScore]
```

### 5.4 Decision contracts

```python
# platform/data_contracts/decisions.py
from pydantic import BaseModel
from typing import Literal, Optional

class EntityRiskProfile(BaseModel):
    entity_id: str
    run_id: str
    aggregated_score: float
    anomaly_score: float
    typology_scores: dict[str, float]
    contributing_signals: list[OccurrenceScore]
    lineage_id: str  # traceback to all source txns

class TrackADecision(BaseModel):
    track: Literal["A"] = "A"
    policy_matched: str
    auto_escalate: bool = True

class TrackBDecision(BaseModel):
    track: Literal["B"] = "B"
    ml_score: float
    uncertain_zone: bool
    llm_invoked: bool
    llm_adjusted_score: Optional[float] = None
    llm_reasoning: Optional[str] = None
    llm_evidence_refs: Optional[list[str]] = None
    final_score: float

class DecisionPayload(BaseModel):
    entity_id: str
    run_id: str
    decision: Literal["ATL", "BTL"]
    track: Literal["A", "B"]
    detail: TrackADecision | TrackBDecision
    historical_context_used: bool
    priority: Literal["P1", "P2", "P3", "P4"]
    golden_thread: dict  # full traceability
```

### 5.5 Alert contracts

```python
# platform/data_contracts/alerts.py
from pydantic import BaseModel
from typing import Literal

class AlertLevel1(BaseModel):
    """Executive summary — for senior reviewers."""
    headline: str
    score: float
    priority: str
    typologies_triggered: list[str]
    one_line_rationale: str

class AlertLevel2(BaseModel):
    """Typology detail — for investigators."""
    per_typology_evidence: list[dict]
    contributing_signals: list[OccurrenceScore]
    counterparty_summary: dict

class AlertLevel3(BaseModel):
    """Full lineage — for audit / SAR drafting."""
    all_underlying_txn_ids: list[str]
    shap_traces: list[dict]
    rule_traces: list[dict]
    llm_reasoning_chain: Optional[str] = None
    feature_snapshot_ref: str  # DVC hash

class Alert(BaseModel):
    alert_id: str
    entity_id: str
    run_id: str
    created_at: str
    level_1: AlertLevel1
    level_2: AlertLevel2
    level_3: AlertLevel3
```

---

## 6. Polars usage pattern for feature engineering

PySpark handles distributed batch. Polars is used for:

1. **Local feature unit-testing** — load a Delta partition, run feature logic, assert outputs.
2. **The L2 in-pod feature assembly** — when BentoML's runner needs to assemble axis-specific feature vectors from several Feast fetches, Polars in the runner pod is ~5–10× faster than Pandas for the join-and-reshape step.
3. **Analyst on-demand evaluation** — Flink wrapper around Polars for single-entity scoring.

### Pattern: Polars LazyFrame for feature engineering

```python
# services/feature_factory/account_engine/rolling.py
import polars as pl
from datetime import date, timedelta

def compute_account_features(
    txn_features: pl.LazyFrame,
    as_of: date,
    windows: list[int] = (30, 60, 90),
) -> pl.LazyFrame:
    """
    Computes rolling account features as of a given date.
    Uses LazyFrame so the planner pushes filters and aggregations.
    """
    lf = txn_features.filter(
        (pl.col("txn_date") <= as_of)
        & (pl.col("txn_date") > as_of - timedelta(days=max(windows)))
    )

    agg_exprs = []
    for w in windows:
        window_start = as_of - timedelta(days=w)
        masked = pl.col("txn_date") > window_start

        agg_exprs.extend([
            pl.col("amount").filter(masked).abs().sum().alias(f"turnover_{w}d"),
            pl.col("amount").filter(masked).sum().alias(f"net_flow_{w}d"),
            pl.col("txn_id").filter(masked).count().alias(f"txn_count_{w}d"),
            pl.col("beneficiary_account").filter(masked).n_unique().alias(f"unique_counterparty_{w}d"),
            pl.col("cross_border").filter(masked).mean().alias(f"cross_border_ratio_{w}d"),
            pl.col("cash_flag").filter(masked).mean().alias(f"cash_ratio_{w}d"),
            pl.col("just_below_ctr").filter(masked).sum().alias(f"just_below_ctr_count_{w}d"),
        ])

    return (
        lf.group_by("account_id")
          .agg(agg_exprs)
          .with_columns(pl.lit(str(as_of)).alias("run_date"))
    )
```

The Pydantic contract is enforced *at the boundary*:

```python
from platform.data_contracts.features import AccountFeatures

def write_account_features(lf: pl.LazyFrame, path: str) -> None:
    df = lf.collect()
    # validate one row through Pydantic to catch schema drift early
    sample = df.row(0, named=True)
    AccountFeatures.model_validate(sample)
    df.write_delta(path, mode="overwrite", delta_write_options={"partition_by": ["run_date"]})
```

---

## 7. Repository / code structure

Monorepo, one Git repo, multiple deployable services. CI per-service.

```
aml-detection-framework/
├── README.md
├── pyproject.toml                    # workspace root, shared tooling
├── docs/
│   ├── architecture/                 # the design PDFs + diagrams
│   ├── runbooks/                     # ops procedures
│   └── adr/                          # architecture decision records
│
├── infrastructure/
│   ├── kubernetes/                   # raw manifests
│   ├── helm/                         # Helm charts per service
│   ├── terraform/                    # cluster, network, IAM
│   ├── argocd/                       # app-of-apps GitOps
│   └── policies/                     # network policies, OPA, PSP
│
├── platform/                         # shared libraries (published as internal wheels)
│   ├── data_contracts/               # Pydantic models — single source of truth
│   │   ├── ingestion.py
│   │   ├── features.py
│   │   ├── scoring.py
│   │   ├── decisions.py
│   │   ├── alerts.py
│   │   └── tests/
│   ├── common_utils/                 # logging, metrics, tracing, config loaders
│   ├── delta_helpers/                # opinionated Delta wrappers
│   ├── feast_helpers/                # feature retrieval shims
│   ├── ge_suites/                    # base Great Expectations suites
│   └── airflow_lib/                  # custom operators, hooks
│
├── airflow_dags/                     # all DAGs in one place, deployed to airflow ns
│   ├── ingestion/
│   │   ├── txn_ingest_dag.py
│   │   ├── kyc_cdc_dag.py
│   │   ├── lists_refresh_dag.py
│   │   └── tp_app_dag.py
│   ├── feature_factory/
│   │   ├── feature_materialize_dag.py
│   │   └── graph_features_weekly_dag.py
│   ├── detection/
│   │   └── aml_detection_pipeline.py  # the main 6-task DAG
│   ├── training/
│   │   ├── hybrid_models/
│   │   ├── gnn_models/
│   │   ├── ae_vae_models/
│   │   └── l4_classifier_dag.py
│   ├── feedback/
│   │   ├── ground_truth_ingest_dag.py
│   │   ├── feature_analyzer_dag.py
│   │   ├── threshold_optimizer_dag.py
│   │   └── drift_retrain_sensor_dag.py
│   └── sandbox/
│       └── simulation_runner_dag.py
│
├── services/                         # deployable services
│   ├── ingestion/
│   │   ├── adapters/
│   │   │   ├── txn_adapter/
│   │   │   │   ├── src/
│   │   │   │   │   ├── adapter.py        # implements SourceAdapter protocol
│   │   │   │   │   ├── swift_parser.py   # MT103 parsing
│   │   │   │   │   └── main.py           # entrypoint
│   │   │   │   ├── tests/
│   │   │   │   ├── Dockerfile
│   │   │   │   └── pyproject.toml
│   │   │   ├── kyc_adapter/
│   │   │   ├── tp_adapter/
│   │   │   ├── lists_adapter/
│   │   │   └── adverse_media_adapter/
│   │   ├── validation_gateway/       # Great Expectations runner
│   │   └── dead_letter_handler/
│   │
│   ├── feature_factory/
│   │   ├── txn_engine/
│   │   │   ├── src/
│   │   │   │   ├── nlp/              # spaCy pipelines
│   │   │   │   ├── geo/              # country risk lookups
│   │   │   │   ├── swift/            # MT field extraction
│   │   │   │   ├── amount_patterns.py
│   │   │   │   └── engine.py
│   │   │   └── tests/
│   │   ├── entity_engine/
│   │   ├── account_engine/
│   │   │   └── src/rolling.py        # Polars/Spark rolling aggregates
│   │   ├── graph_engine/
│   │   │   └── src/cypher/           # parameterized Cypher queries
│   │   ├── feast_materializer/
│   │   └── feature_registry/         # CRUD against Feast metadata
│   │
│   ├── model_layer/
│   │   ├── rule_engine/
│   │   │   └── src/
│   │   │       ├── rule_dsl.py       # rule definition DSL
│   │   │       ├── executor.py       # Spark SQL executor
│   │   │       └── rules/            # one file per rule (CTR, HRG, ...)
│   │   ├── serving/
│   │   │   ├── fastapi_server/
│   │   │   │   └── src/
│   │   │   │       ├── routes/
│   │   │   │       └── runners/      # per-model runner wrappers
│   │   │   └── bentoml_server/
│   │   │       └── bentofile.yaml
│   │   ├── dispatch_coordinator/     # Spark driver dispatch logic
│   │   └── signal_assembler/         # collects model outputs → SignalPayload
│   │
│   ├── signal_aggregator/
│   │   └── src/
│   │       ├── entity_resolver/      # Zingg wrapper
│   │       ├── aggregation_engine/
│   │       ├── anomaly_integrator/
│   │       ├── lineage_tracker/
│   │       └── matrix_builder/
│   │
│   ├── risk_appetite/
│   │   ├── escalation_router/
│   │   ├── policy_engine/            # Track A
│   │   ├── ml_classifier/            # Track B XGBoost
│   │   ├── llm_reasoner/             # Track B LLM
│   │   ├── historical_context/
│   │   └── decision_builder/
│   │
│   ├── alerts_packaging/
│   │   ├── alert_builder/
│   │   ├── template_engine/          # Jinja2 templates per typology
│   │   ├── narrative_generator/      # LLM-backed L1 summaries
│   │   ├── celery_distributor/
│   │   └── case_mgmt_client/         # Kong → Case Mgmt
│   │
│   ├── feedback_loop/
│   │   ├── ground_truth_ingestor/
│   │   ├── feature_analyzer/         # SHAP
│   │   ├── threshold_optimizer/      # Bayesian back-test
│   │   ├── recommendation_engine/
│   │   ├── btl_sampler/
│   │   └── retrain_trigger/
│   │
│   ├── sandbox/
│   │   ├── config_override_manager/
│   │   ├── sandbox_engine/
│   │   ├── shadow_store_writer/
│   │   ├── output_viewer/
│   │   └── promotion_gate/
│   │
│   ├── tuning_matrix/
│   │   ├── api/                      # FastAPI CRUD on GTM
│   │   ├── version_manager/
│   │   └── redis_publisher/
│   │
│   └── llm/
│       ├── llm_server/               # on-prem vLLM
│       ├── llm_gateway/              # unified API
│       ├── prompt_registry/          # Git-backed prompt templates
│       ├── guardrails_engine/        # fact validator, schema enforcer
│       └── reasoning_cache/
│
├── ml_models/                        # model code, training scripts
│   ├── hybrid/
│   │   ├── structuring/
│   │   │   ├── train.py
│   │   │   ├── features.py
│   │   │   ├── evaluate.py
│   │   │   └── sweep.yaml            # W&B sweep config
│   │   ├── rapid_movement/
│   │   ├── velocity/
│   │   └── wire_stripping/
│   ├── gnn/
│   │   ├── funnel/
│   │   ├── layering/
│   │   ├── smurfing/
│   │   └── shell_network/
│   ├── ae_vae/
│   │   ├── dormant_reactivation/
│   │   ├── unusual_cash/
│   │   └── ato_behavioral/
│   ├── l4_classifier/
│   │   └── xgboost_supervised/
│   └── shared/
│       ├── base_trainer.py
│       ├── data_loader.py
│       └── evaluators.py
│
├── ui/
│   ├── analyst_ui/                   # React/Next, investigators
│   ├── admin_portal/                 # React, risk managers
│   ├── whatif_ui/                    # Streamlit, sandbox
│   └── shared/                       # design system, auth client
│
├── observability/
│   ├── prometheus/
│   ├── grafana_dashboards/
│   ├── evidently_configs/
│   └── elk_pipelines/
│
└── tests/
    ├── integration/                  # cross-service tests
    ├── parity/                       # Actimize parity harness
    ├── load/                         # k6 / locust
    └── chaos/                        # litmus
```

Key principles enforced by structure:

- **Data contracts live once.** `platform/data_contracts` is the only place schemas are defined. Every service imports from it. No service redefines `Alert` or `SignalPayload`.
- **One service = one Dockerfile = one Helm chart.** No mega-images.
- **Airflow DAGs live with the platform, not the services.** This avoids the trap where DAG code drifts from service code; DAGs only call APIs / submit Spark jobs.
- **ML model code is separate from serving.** Training lives in `ml_models/`. Serving wrappers live in `services/model_layer/serving/`. They share Pydantic feature contracts only.

---

## 8. Training pipelines — per model family

Every training DAG is structurally identical (same 4 tasks per the design doc). The differences live in the model code.

### 8.1 Hybrid (XGBoost) — e.g. Structuring

- **Input features**: TFE (~12 features: round-amount flags, just-below-CTR, channel, time-of-day) + AFE (~15 features: structuring proxies, velocity, counterparty diversity)
- **Label source**: investigation outcomes (`aml.outcomes`, disposition ∈ {TP, FP}) on historical structuring alerts
- **Splits**: time-based, 70/15/15 with 30-day gap between val and test
- **HP sweep**: W&B Bayesian, ~30 runs, search over `learning_rate, max_depth, n_estimators, scale_pos_weight, subsample, colsample_bytree`
- **Primary metric**: AUC-PR (class imbalance)
- **Business gate**: must recall ≥95% of historically confirmed structuring TPs at FP rate ≤ current Actimize FP rate
- **Compute**: CPU, 8 cores, ~2h
- **Retrain trigger**: monthly + drift

### 8.2 GNN — e.g. Funnel detection

- **Input graph**: directed money-flow graph from Neo4j, last 6 months, nodes = entities, edges = aggregated txn flows, edge weights = volume and frequency
- **Node features**: EFE features + GFE features (PageRank, centrality, etc.)
- **Architecture**: 3-layer GraphSAGE or GAT, hidden_dim 64–256 (swept)
- **Label source**: semi-supervised — confirmed funnel cases + structural priors (high in-degree, low out-degree, fast turnover)
- **HP sweep**: hidden_channels, num_layers, conv_type (GCN/GAT/GraphSAGE), attention_heads, dropout
- **Compute**: 1× A100 GPU, ~4h
- **Retrain trigger**: bi-weekly (graph evolves)
- **Critical**: graph snapshot is DVC-versioned, no exceptions

### 8.3 AE/VAE — e.g. Dormant Reactivation

- **Input**: 90-day behavioral baseline window per account (channel mix, time-of-day distribution, amount distribution, counterparty diversity)
- **Architecture**: 5-layer dense autoencoder, latent_dim 8–32 (swept), or β-VAE for VAE variant
- **Training**: only "normal" accounts (no historical alerts), reconstruction loss
- **Inference**: high reconstruction error → anomaly. Threshold set per-jurisdiction via Tuning Matrix.
- **Compute**: 1× A100, ~3h
- **Retrain trigger**: weekly (baseline drifts)

### 8.4 L4 Classifier (XGBoost) — the supervised dispositioner

- **Input features**: full entity risk profile from L3 (typology scores, anomaly score, network features, historical context indicators)
- **Label source**: investigation dispositions (TP/FP) on past alerts
- **Critical**: this model has access to the L1–L3 outputs, so it learns to disposition the ensemble
- **HP sweep**: standard XGBoost set
- **Compute**: CPU, 8 cores, ~2h
- **Retrain trigger**: monthly or on outcome drift

---

## 9. Agentic LLM — design decisions

The LLM exists in three spots only (per the design doc). The implementation should reflect three distinct prompt families, three guardrail profiles:

1. **L2 Narrative Scorer** (feature-enhancement role): reads SWIFT F70/F72, produces a structured score. Determinism enforced (temperature 0). Fact validator checks every claim against the SWIFT input. **No reasoning**, this is extraction.

2. **L4 Reasoning Agent** (decisioning role): uncertain-zone reasoner. Receives full signal portfolio + historical context, returns adjusted score with rationale. **Bounded adjustment** (±0.15). Schema-enforced output. Latency circuit breaker (15s per entity; fallback to ML-only on timeout).

3. **L5 Narrative Generator** (content role): generates investigator-readable summaries from structured L4 output. Template-anchored, no free-form claims, every sentence traceable to a source field.

Build order: L5 first (lowest risk, content-only), L2 second (extraction, narrow scope), L4 last (decisioning, highest risk).

---

## 10. UI surface — what gets built and for whom

The system has four user populations. Each gets its own UI; they share a design system.

### 10.1 Analyst UI (investigators) — React/Next

Primary user: Compliance investigator working alerts.

| Screen | Purpose |
|---|---|
| Alert queue | Filter/sort by priority, typology, jurisdiction, age. Real-time updates. |
| Alert detail (L1/L2/L3 drill-down) | Executive summary → typology evidence → full lineage. SHAP/rule trace visible. |
| Entity 360 | All historical alerts, KYC snapshot, UBO graph (D3 force-directed), txn timeline |
| Network graph view | Neo4j-backed interactive graph; expand/collapse N-hop; highlight cycles/communities |
| Disposition workflow | TP/FP/Escalate/Routine with required justification text; writes to feedback loop |
| On-demand re-eval | Trigger single-entity rescore via Flink path; result back in seconds |
| SAR drafting assistant | LLM-generated narrative draft (L5), human-editable, audit-logged |
| Case notes & attachments | Investigation notes, document upload, integrated with Case Mgmt |

### 10.2 Admin Portal (risk managers + ML ops) — React

Primary user: Risk manager controlling production config, ML platform owner.

| Screen | Purpose |
|---|---|
| Global Tuning Matrix editor | Per-dimension parameter CRUD with version diff, approval workflow |
| Threshold recommendation review | Recommendation Engine proposals (Path B output) with accept/reject/comment |
| Model registry browser | All MLflow models, stage transitions, approve promotion |
| Sandbox runs dashboard | List of simulation runs, status, comparison reports |
| Promotion gate | Sandbox run → side-by-side comparison vs prod → approve/reject |
| Feature registry browser | Feature definitions, owners, baselines, drift state |
| Pipeline status | Airflow DAG status, SLA breaches, retry/clear |
| Drift alerts inbox | Evidently alerts, drill into affected features/models |
| Audit trail viewer | ELK-backed search over all config changes, model promotions, decisions |
| Policy & zero-tolerance editor | Track A policy CRUD with two-person approval |

### 10.3 What-If UI (sandbox) — Streamlit (per design doc)

Primary user: Risk manager exploring config changes.

| Screen | Purpose |
|---|---|
| Simulation configurator | Parameter overrides, model selection, scope, date range, run ID |
| Sim vs Prod comparator | Alert count delta, score distribution shift, newly escalated, newly suppressed |
| Regression check | List of historically confirmed TPs and whether sim still catches them |
| Population impact heatmap | Which jurisdictions/segments most affected |
| Submit for promotion | Hands off to Admin Portal's promotion gate |

### 10.4 Data Scientist Workspace — JupyterHub + W&B

Not strictly "UI we build" — JupyterHub deployment in `aml-ml` ns with mounted Feast offline store access and MLflow/W&B integration. Notebooks → training DAGs via a "promote to DAG" template.

### 10.5 Shared components

- **Auth**: SSO via internal IdP, OIDC, RBAC enforced via Kong + per-app middleware.
- **Design system**: shared React component library (tables, charts, graph viz, form builders).
- **Notifications**: in-app + email + Slack via a unified notification service.
- **Audit hooks**: every mutation in any UI emits an audit event to ELK; no exceptions.

---

## 11. Critical implementation decisions to make early

These are decisions that are cheap now and expensive later.

| # | Decision | Default recommendation | Why |
|---|---|---|---|
| 1 | Spark on K8s vs YARN | K8s | Whole stack is K8s; one operational surface |
| 2 | Delta Lake vs Iceberg | Delta | Better Spark-native integration, ACID for our update patterns |
| 3 | Feast offline backend | Delta on MinIO | Aligns with rest of stack, no dual storage |
| 4 | Online feature store | Redis cluster | Sub-ms; design doc commits to this |
| 5 | Self-hosted LLM model | Llama-3.x-70B or Mistral-Large; quantized | Cost, data residency; vLLM serving |
| 6 | GNN framework | PyTorch Geometric over DGL | Wider community, better Neo4j connectors |
| 7 | Entity resolution | Zingg over Splink | Spark-native, scales to our volume |
| 8 | Prompt versioning | Git-backed, per-prompt semver | Auditable, diffable, reviewable |
| 9 | Sandbox isolation | Logical (namespace) over physical | Cost; design doc commits |
| 10 | CI for ML models | Trigger eval + sandbox on every model PR | Catches regressions before MLflow staging |
| 11 | Model serialization | ONNX for cross-runtime, native for fast path | Hedge against PyTorch version upgrades |
| 12 | Test data for parity | Frozen 30-day window from production with masking | Reproducible Actimize parity tests |

---

## 12. What "done" looks like for each band

A phase is done when:

- **Foundation (Band A)**: smoke pipeline (test record in → test alert out) runs end-to-end through all six namespaces. All contracts published, all dashboards green.
- **Data plane (Band B)**: Feature Factory produces all ~140 features for one full day's production data, all Great Expectations checks pass, Feast online lookup returns sub-10ms p99.
- **Model plane (Band C)**: Actimize parity test passes (>99% alert overlap on a 30-day frozen window). Each ML model has a champion in MLflow Production stage. BentoML serves 500K+ entities in batch window.
- **Decision plane (Band D)**: full L1→L5 batch run produces alerts indistinguishable from a target investigator-grade output on the parity window. Sandbox can run a config override and produce a comparison report. All four UIs are usable end-to-end.

After Band D, the system is in production. **Then** the ML uplift work begins: model tuning, drift response, new typologies. The system is built to make that the *easy* phase.

---

## 13. Things this plan deliberately omits

To be explicit about scope:

- **SAR filing workflow** (regulatory submission) — outside the framework; integrates with existing case-management system.
- **CRM / customer outreach** — outside the framework.
- **Fraud detection** (real-time transaction blocking) — different latency profile; this design is detection, not interdiction.
- **Sanctions screening of new customers at onboarding** — that's a separate real-time screening service; this framework consumes its outputs.
- **Trade surveillance / market abuse** — different problem domain.

If any of these are in scope, they're follow-on projects with their own designs.
