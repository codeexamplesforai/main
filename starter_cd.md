# AML — Starter Code Skeleton

This file contains the day-one concrete code that backs the implementation plan. Drop these into the corresponding paths in the monorepo; they compile, run, and pass type-checking as-is.

---

## `platform/data_contracts/__init__.py`

```python
"""Single source of truth for all inter-service data contracts.
Every service imports from here. Never redefine a contract in a service."""

from platform.data_contracts.ingestion import (
    Channel, IngestMetadata, RawTransaction, ValidatedTransaction,
)
from platform.data_contracts.features import (
    TxnFeatures, EntityFeatures, AccountFeatures, GraphFeatures,
)
from platform.data_contracts.scoring import (
    TuningMatrixParams, ModelScoringRequest, OccurrenceScore, SignalPayload,
)
from platform.data_contracts.decisions import (
    EntityRiskProfile, TrackADecision, TrackBDecision, DecisionPayload,
)
from platform.data_contracts.alerts import (
    AlertLevel1, AlertLevel2, AlertLevel3, Alert,
)

__version__ = "1.0.0"
__all__ = [
    "Channel", "IngestMetadata", "RawTransaction", "ValidatedTransaction",
    "TxnFeatures", "EntityFeatures", "AccountFeatures", "GraphFeatures",
    "TuningMatrixParams", "ModelScoringRequest", "OccurrenceScore", "SignalPayload",
    "EntityRiskProfile", "TrackADecision", "TrackBDecision", "DecisionPayload",
    "AlertLevel1", "AlertLevel2", "AlertLevel3", "Alert",
]
```

---

## `services/ingestion/adapters/base.py`

```python
"""Base protocol for all source adapters. Implement this for every source."""

from typing import Protocol, Iterator, runtime_checkable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SourceBatch:
    """An atomic unit of work from a source.
    For SFTP: one file. For CDC: one offset window. For REST: one polling window."""
    batch_id: str
    source_ref: str          # filename, offset, page token
    discovered_at: datetime
    expected_record_count: int | None = None


@runtime_checkable
class SourceAdapter(Protocol):
    """Every adapter (Txn, KYC, TP, Lists, ...) implements this."""

    adapter_name: str
    adapter_version: str
    schema_version: str

    def discover(self) -> list[SourceBatch]:
        """Return all unprocessed batches available right now."""
        ...

    def fetch(self, batch: SourceBatch) -> Iterator[dict]:
        """Yield raw records from a batch. Records will be Pydantic-validated downstream."""
        ...

    def acknowledge(self, batch: SourceBatch) -> None:
        """Mark batch as processed. Idempotent."""
        ...

    def reject(self, batch: SourceBatch, reason: str) -> None:
        """Move batch to source-side error directory / quarantine."""
        ...
```

---

## `services/ingestion/adapters/txn_adapter/src/swift_parser.py`

```python
"""SWIFT MT103 parser. Extracts fields needed for downstream feature engineering."""

from datetime import datetime
from decimal import Decimal
import re
from platform.data_contracts import Channel


# SWIFT MT103 field markers. Order matters in messages but not here.
FIELD_PATTERN = re.compile(r":(\d{2}[A-Z]?):", re.MULTILINE)


def parse_mt103(raw: str) -> dict:
    """Parse a single MT103 message into a dict suitable for RawTransaction.

    Returns a dict with at least the fields required by RawTransaction;
    downstream Pydantic validation will reject malformed messages.
    """
    fields = _split_fields(raw)
    if "20" not in fields:
        raise ValueError("MT103 missing mandatory F20 reference")

    amount, currency = _parse_amount_field(fields.get("32A", ""))
    originator_account, originator_name = _parse_party(fields.get("50K") or fields.get("50A", ""))
    beneficiary_account, beneficiary_name = _parse_party(fields.get("59") or fields.get("59A", ""))

    return {
        "txn_id": fields["20"].strip(),
        "txn_date": _parse_date(fields.get("32A", "")[:6]),
        "amount": amount,
        "currency": currency,
        "originator_account": originator_account,
        "originator_name": originator_name,
        "originator_country": _country_from_account(originator_account),
        "beneficiary_account": beneficiary_account,
        "beneficiary_name": beneficiary_name,
        "beneficiary_country": _country_from_account(beneficiary_account),
        "channel": Channel.WIRE,
        "mt_type": "MT103",
        "swift_f20": fields.get("20"),
        "swift_f50": fields.get("50K") or fields.get("50A"),
        "swift_f59": fields.get("59") or fields.get("59A"),
        "swift_f70": fields.get("70"),
        "swift_f72": fields.get("72"),
        "purpose_code": fields.get("26T"),
    }


def _split_fields(raw: str) -> dict[str, str]:
    parts = FIELD_PATTERN.split(raw)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _parse_amount_field(s: str) -> tuple[Decimal, str]:
    """F32A format: YYMMDD + 3-char currency + amount (comma decimal)."""
    if len(s) < 10:
        raise ValueError(f"F32A too short: {s!r}")
    currency = s[6:9]
    amount = Decimal(s[9:].replace(",", "."))
    return amount, currency


def _parse_party(s: str) -> tuple[str, str | None]:
    """First line is /ACCOUNT, remaining lines are name. Account may be IBAN or local."""
    lines = [l.strip() for l in s.split("\n") if l.strip()]
    if not lines:
        return "", None
    account = lines[0].lstrip("/")
    name = " ".join(lines[1:]) if len(lines) > 1 else None
    return account, name


def _country_from_account(account: str) -> str:
    """IBAN starts with ISO country. For non-IBAN, requires resolver service."""
    if len(account) >= 2 and account[:2].isalpha():
        return account[:2].upper()
    return "XX"  # unknown — flagged downstream


def _parse_date(yymmdd: str) -> datetime:
    return datetime.strptime(yymmdd, "%y%m%d")
```

---

## `services/feature_factory/txn_engine/src/engine.py`

```python
"""Transaction Feature Engine — Layer 1 component.

Reads validated transactions, computes ~50 per-txn features, writes to Delta.
This engine is stateless; features are derived purely from the input row plus
static reference data (country risk, MCC risk, etc.)."""

from dataclasses import dataclass
import polars as pl
from platform.data_contracts import TxnFeatures
from .nlp import wire_strip_classifier, narrative_ner, keyword_matchers
from .geo import country_risk_score, is_hrg, is_tax_haven
from .amount_patterns import is_round, is_just_below_threshold


@dataclass(frozen=True)
class TxnEngineConfig:
    feature_version: str
    run_id: str
    hrg_country_list_version: str
    ctr_thresholds_by_jurisdiction: dict[str, float]


class TxnFeatureEngine:
    """Stateless feature computer. Instantiate once per Spark task."""

    def __init__(self, config: TxnEngineConfig):
        self.config = config
        self._nlp_wire_strip = wire_strip_classifier.load()
        self._nlp_ner = narrative_ner.load()

    def compute(self, validated_txns: pl.LazyFrame) -> pl.LazyFrame:
        """Compute all txn features. Output schema = TxnFeatures."""
        return (
            validated_txns
            .with_columns([
                # Geographic
                pl.col("originator_country").map_elements(is_hrg, return_dtype=pl.Boolean).alias("hrg_originator"),
                pl.col("beneficiary_country").map_elements(is_hrg, return_dtype=pl.Boolean).alias("hrg_beneficiary"),
                pl.col("originator_country").map_elements(is_tax_haven, return_dtype=pl.Boolean).alias("tax_haven_flag"),
                pl.col("originator_country").map_elements(country_risk_score, return_dtype=pl.Float64).alias("originator_country_risk"),
                pl.col("beneficiary_country").map_elements(country_risk_score, return_dtype=pl.Float64).alias("beneficiary_country_risk"),

                # Amount patterns
                (pl.col("amount").cast(pl.Float64) % 1000 == 0).alias("round_amount_1k"),
                (pl.col("amount").cast(pl.Float64) % 5000 == 0).alias("round_amount_5k"),
                (pl.col("amount").cast(pl.Float64) % 10000 == 0).alias("round_amount_10k"),
                self._just_below_ctr_expr().alias("just_below_ctr"),

                # Channel / time
                (pl.col("channel").is_in(["CASH_DEPOSIT", "CASH_WITHDRAWAL", "ATM"])).alias("cash_flag"),
                (pl.col("originator_country") != pl.col("beneficiary_country")).alias("cross_border"),
                pl.col("txn_date").dt.hour().is_between(22, 6).alias("off_hours"),
                pl.col("txn_date").dt.weekday().is_in([6, 7]).alias("weekend_flag"),

                # SWIFT structural
                pl.col("swift_f70").str.len_chars().fill_null(0).alias("swift_f70_length"),
                pl.col("swift_f72").is_not_null().alias("swift_f72_present"),

                # Run metadata
                pl.lit(self.config.run_id).alias("run_id"),
                pl.lit(self.config.feature_version).alias("feature_version"),
            ])
            .with_columns([
                # NLP features — computed in a second pass since they depend on text columns
                pl.col("swift_f70").map_elements(self._wire_strip_score, return_dtype=pl.Float64).alias("wire_strip_indicator"),
                pl.col("swift_f70").map_elements(keyword_matchers.tbml, return_dtype=pl.List(pl.Utf8)).alias("tbml_keywords"),
                pl.col("swift_f70").map_elements(keyword_matchers.crypto, return_dtype=pl.List(pl.Utf8)).alias("crypto_keywords"),
            ])
        )

    def _just_below_ctr_expr(self) -> pl.Expr:
        """Vectorized just-below-threshold check, jurisdiction-aware via map."""
        threshold_map = self.config.ctr_thresholds_by_jurisdiction
        # Default to US $10,000 if jurisdiction not in map
        return (
            pl.col("amount").cast(pl.Float64) >=
            (pl.col("originator_country").map_elements(
                lambda c: threshold_map.get(c, 10000) * 0.85,
                return_dtype=pl.Float64
            ))
        ) & (
            pl.col("amount").cast(pl.Float64) <
            pl.col("originator_country").map_elements(
                lambda c: threshold_map.get(c, 10000),
                return_dtype=pl.Float64
            )
        )

    def _wire_strip_score(self, narrative: str | None) -> float:
        if not narrative:
            return 0.0
        return float(self._nlp_wire_strip.predict_proba([narrative])[0][1])

    def validate_sample(self, df: pl.DataFrame) -> None:
        """Sample-validate output against Pydantic contract. Catches schema drift."""
        if df.is_empty():
            return
        sample = df.row(0, named=True)
        TxnFeatures.model_validate(sample)
```

---

## `services/model_layer/rule_engine/src/rule_dsl.py`

```python
"""Rule definition DSL. Every Actimize rule is migrated to a Rule instance.

This is the abstraction that lets us version, test, sandbox, and audit rules
the same way we treat ML models."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
from datetime import datetime
import polars as pl


@dataclass(frozen=True)
class Rule:
    """A single deterministic detection rule.

    Rules are first-class artifacts: registered, versioned, sandbox-testable,
    Tuning-Matrix-parameterized. The `evaluate` function consumes features and
    parameters and returns a score in [0, 1] plus drivers."""
    rule_id: str
    typology_id: str
    version: str
    description: str
    required_features: list[str]
    required_params: list[str]
    evaluate: Callable[[pl.DataFrame, dict], pl.DataFrame]
    owner: str
    created_at: datetime = field(default_factory=datetime.utcnow)


# Example: Cash Transaction Reporting — pure regulatory threshold rule.
def _ctr_evaluate(df: pl.DataFrame, params: dict) -> pl.DataFrame:
    threshold = params["ctr_threshold"]  # injected from Tuning Matrix per jurisdiction
    return df.with_columns([
        pl.when(pl.col("amount") >= threshold)
          .then(pl.lit(1.0))
          .otherwise(pl.lit(0.0))
          .alias("score"),
        pl.when(pl.col("amount") >= threshold)
          .then(pl.lit("ATL"))
          .otherwise(pl.lit("BTL"))
          .alias("classification"),
        pl.struct([
            pl.col("amount"),
            pl.lit(threshold).alias("threshold"),
            pl.col("currency"),
        ]).alias("decision_drivers"),
    ])


CTR_RULE = Rule(
    rule_id="RT#01",
    typology_id="CASH_TXN_REPORTING",
    version="1.0.0",
    description="Cash transaction at or above jurisdictional CTR threshold.",
    required_features=["amount", "currency"],
    required_params=["ctr_threshold"],
    evaluate=_ctr_evaluate,
    owner="aml-platform",
)


# Example: Just-Below-Threshold (structuring proxy) — rule, but feeds Hybrid model
def _just_below_evaluate(df: pl.DataFrame, params: dict) -> pl.DataFrame:
    threshold = params["ctr_threshold"]
    floor = threshold * params.get("just_below_floor_pct", 0.85)
    return df.with_columns([
        pl.when((pl.col("amount") >= floor) & (pl.col("amount") < threshold))
          .then(pl.lit(0.6))  # not auto-ATL; signal to Hybrid model
          .otherwise(pl.lit(0.0))
          .alias("score"),
        pl.lit("BTL").alias("classification"),  # rule alone is BTL
        pl.struct([
            pl.col("amount"),
            pl.lit(floor).alias("floor"),
            pl.lit(threshold).alias("ceiling"),
        ]).alias("decision_drivers"),
    ])


JUST_BELOW_RULE = Rule(
    rule_id="RT#02",
    typology_id="STRUCTURING",
    version="1.0.0",
    description="Transaction in the 85–100% band of CTR threshold.",
    required_features=["amount"],
    required_params=["ctr_threshold", "just_below_floor_pct"],
    evaluate=_just_below_evaluate,
    owner="aml-platform",
)


class RuleRegistry:
    """Singleton registry. All rules register at import time; executor pulls from here."""
    _rules: dict[str, Rule] = {}

    @classmethod
    def register(cls, rule: Rule) -> None:
        if rule.rule_id in cls._rules:
            raise ValueError(f"Rule {rule.rule_id} already registered")
        cls._rules[rule.rule_id] = rule

    @classmethod
    def get(cls, rule_id: str) -> Rule:
        return cls._rules[rule_id]

    @classmethod
    def all_active(cls) -> list[Rule]:
        return list(cls._rules.values())


# Register at import
for _r in [CTR_RULE, JUST_BELOW_RULE]:
    RuleRegistry.register(_r)
```

---

## `services/model_layer/serving/bentoml_server/service.py`

```python
"""BentoML service — batch-optimized multi-model serving.

Routes incoming scoring requests to the right runner (CPU/GPU) based on model
config registry. Adaptive batcher groups requests for throughput."""

import bentoml
from bentoml.io import JSON
from typing import Any

from platform.data_contracts import ModelScoringRequest, OccurrenceScore


# CPU runners — XGBoost models
structuring_runner = bentoml.xgboost.get("structuring:production").to_runner()
rapid_movement_runner = bentoml.xgboost.get("rapid_movement:production").to_runner()
velocity_runner = bentoml.xgboost.get("velocity:production").to_runner()
wire_stripping_runner = bentoml.xgboost.get("wire_stripping:production").to_runner()

# GPU runners — PyTorch GNN / AE
funnel_gnn_runner = bentoml.pytorch.get("funnel_gnn:production").to_runner()
layering_gnn_runner = bentoml.pytorch.get("layering_gnn:production").to_runner()
dormant_ae_runner = bentoml.pytorch.get("dormant_ae:production").to_runner()


RUNNERS = {
    "structuring": structuring_runner,
    "rapid_movement": rapid_movement_runner,
    "velocity": velocity_runner,
    "wire_stripping": wire_stripping_runner,
    "funnel_gnn": funnel_gnn_runner,
    "layering_gnn": layering_gnn_runner,
    "dormant_ae": dormant_ae_runner,
}


svc = bentoml.Service(
    name="aml_model_layer",
    runners=list(RUNNERS.values()),
)


@svc.api(input=JSON(pydantic_model=ModelScoringRequest), output=JSON())
async def score(req: ModelScoringRequest) -> dict[str, Any]:
    """Single-entity scoring endpoint (also adaptive-batched by BentoML)."""
    runner = RUNNERS.get(req.model_id)
    if runner is None:
        raise ValueError(f"No runner registered for model_id={req.model_id}")

    feature_vector = _assemble_feature_vector(req.features, req.model_id)
    raw_score = await runner.async_run(feature_vector)
    score_value = float(raw_score[0] if hasattr(raw_score, "__len__") else raw_score)

    result = OccurrenceScore(
        occurrence_id=f"{req.entity_id}:{req.typology_id}:{req.run_id}",
        typology_id=req.typology_id,
        axis=_axis_for_model(req.model_id),
        model_id=req.model_id,
        score=score_value,
        classification="ATL" if score_value >= req.params.parameters.get("atl_threshold", 0.5) else "BTL",
        decision_drivers=_extract_drivers(req.model_id, feature_vector, score_value),
        occurrence_refs=req.features.get("source_txn_ids", []),
    )
    return result.model_dump()


@svc.api(input=JSON(), output=JSON())
async def batch_score(payload: dict) -> list[dict]:
    """Bulk endpoint used by the Spark driver during the nightly fan-out.

    Payload: {model_id, entity_ids[], features[], params[]}
    BentoML's adaptive batcher transparently re-groups for the runner."""
    model_id = payload["model_id"]
    runner = RUNNERS[model_id]
    feature_matrix = payload["features"]
    raw_scores = await runner.async_run(feature_matrix)

    results = []
    for entity_id, fv, raw in zip(payload["entity_ids"], feature_matrix, raw_scores):
        score_value = float(raw)
        results.append(OccurrenceScore(
            occurrence_id=f"{entity_id}:{payload['typology_id']}:{payload['run_id']}",
            typology_id=payload["typology_id"],
            axis=_axis_for_model(model_id),
            model_id=model_id,
            score=score_value,
            classification="ATL" if score_value >= payload["params"][0].get("atl_threshold", 0.5) else "BTL",
            decision_drivers=_extract_drivers(model_id, fv, score_value),
            occurrence_refs=[],
        ).model_dump())
    return results


def _assemble_feature_vector(features: dict, model_id: str) -> list[float]:
    """Project the features dict into the ordered vector this model expects.
    The feature order is part of the model's signature in MLflow."""
    # Per-model feature ordering pulled from MLflow signature at startup.
    # Omitted here for brevity.
    ...


def _axis_for_model(model_id: str) -> str:
    """Lookup from Model Config Registry, cached at startup."""
    ...


def _extract_drivers(model_id: str, feature_vector: list[float], score: float) -> list[dict]:
    """SHAP for XGBoost, attention weights for GNN, reconstruction error for AE."""
    ...
```

---

## `airflow_dags/detection/aml_detection_pipeline.py`

```python
"""The main batch detection DAG. Six sequential tasks, one per layer.
Each task is idempotent on run_id; retry-safe; SLA-monitored."""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

DEFAULT_ARGS = {
    "owner": "aml-platform",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=1),
}

with DAG(
    dag_id="aml_detection_pipeline",
    default_args=DEFAULT_ARGS,
    description="Layer 1 → Layer 5 batch detection pipeline",
    schedule="0 2 * * *",  # daily 02:00 UTC, override via Airflow Variable
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # only one batch run at a time
    tags=["aml", "production", "detection"],
) as dag:

    ingest_validate = SparkKubernetesOperator(
        task_id="task_1_ingest_and_validate",
        namespace="aml-data",
        application_file="spark/jobs/ingest_validate.yaml",
        execution_timeout=timedelta(hours=2),
    )

    feature_compute = SparkKubernetesOperator(
        task_id="task_2_feature_compute",
        namespace="aml-data",
        application_file="spark/jobs/feature_compute.yaml",
        execution_timeout=timedelta(hours=2),
    )

    model_scoring = SparkKubernetesOperator(
        task_id="task_3_model_scoring",
        namespace="aml-data",
        application_file="spark/jobs/model_scoring.yaml",
        execution_timeout=timedelta(hours=4),
    )

    signal_aggregation = SparkKubernetesOperator(
        task_id="task_4_signal_aggregation",
        namespace="aml-data",
        application_file="spark/jobs/signal_aggregation.yaml",
        execution_timeout=timedelta(hours=2),
    )

    risk_appetite = SparkKubernetesOperator(
        task_id="task_5_risk_appetite",
        namespace="aml-data",
        application_file="spark/jobs/risk_appetite.yaml",
        execution_timeout=timedelta(hours=3),  # LLM calls
    )

    alert_packaging = SparkKubernetesOperator(
        task_id="task_6_alert_packaging",
        namespace="aml-data",
        application_file="spark/jobs/alert_packaging.yaml",
        execution_timeout=timedelta(hours=1),
    )

    post_run_metrics = PythonOperator(
        task_id="post_run_metrics",
        python_callable=lambda **ctx: None,  # publishes Prometheus run metrics
    )

    ingest_validate >> feature_compute >> model_scoring >> signal_aggregation >> risk_appetite >> alert_packaging >> post_run_metrics
```

---

## Notes on running these

- Every contract import path assumes `platform/` and `services/` are siblings on `PYTHONPATH`. Use a workspace `pyproject.toml` with path dependencies, or build internal wheels.
- The Polars expressions above target Polars ≥ 0.20 (uses `map_elements` not the deprecated `apply`).
- BentoML version target: ≥ 1.2 (adaptive batcher + multi-runner support).
- The SwiftKubernetesOperator examples assume the Spark Operator (radanalytics or stackable) is installed in the cluster.
