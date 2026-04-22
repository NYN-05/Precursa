from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import logging

from app.db.models import ShipmentSnapshot
from app.integrations.factory import integration_factory
from app.ml.pipeline.pipeline import compute_dri_pipeline

logger = logging.getLogger(__name__)

# Legacy FEATURE_NAMES for backwards compatibility if needed
FEATURE_NAMES: tuple[str, ...] = (
    "port_congestion",
    "weather",
    "carrier_reliability",
    "customs_delay",
    "geo_risk",
    "trend_congestion",
    "trend_delay",
    "route_variability",
)

MODEL_VERSION = "ml-pipeline-v1"


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class RiskFactor:
    feature: str
    shap_value: float
    direction: str


@dataclass(frozen=True)
class ShipmentRiskScore:
    shipment_key: str
    dri: int
    xgboost_score: float
    anomaly_score: float
    combined_score: float
    top_factors: list[RiskFactor]
    model_version: str
    scored_at: datetime


class RiskScoringService:
    def __init__(self) -> None:
        pass

    def score_snapshot(self, snapshot: ShipmentSnapshot, top_k: int = 5) -> ShipmentRiskScore:
        # 1. Fetch external data
        feature_vector = snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
        external_data = integration_factory.fetch_all(snapshot.shipment_key, feature_vector)
        
        # 2. Run ML Pipeline
        # We pass snapshot as a dict to the pipeline
        snapshot_dict = {
            "shipment_key": snapshot.shipment_key,
            "event_count": snapshot.event_count,
            "avg_severity": snapshot.avg_severity,
            "feature_vector": feature_vector
        }
        
        ml_output = compute_dri_pipeline(snapshot_dict, external_data)
        
        # 3. Build top factors from ML top_features
        top_factors = [
            RiskFactor(feature=feat, shap_value=0.1, direction="increase")
            for feat in ml_output["top_features"]
        ]

        # 4. Log change
        old_dri = snapshot.provisional_dri
        if ml_output["dri"] != old_dri:
            logger.info(
                "DRI updated for %s: %d -> %d (ML Pipeline)", 
                snapshot.shipment_key, old_dri, ml_output["dri"]
            )

        return ShipmentRiskScore(
            shipment_key=snapshot.shipment_key,
            dri=ml_output["dri"],
            xgboost_score=ml_output["context_score"],
            anomaly_score=ml_output["anomaly_score"],
            combined_score=ml_output["dri"] / 100.0,
            top_factors=top_factors[:top_k],
            model_version=MODEL_VERSION,
            scored_at=datetime.now(timezone.utc),
        )

    def score_snapshots(
        self,
        snapshots: list[ShipmentSnapshot],
        top_k: int = 5,
    ) -> list[ShipmentRiskScore]:
        return [self.score_snapshot(snapshot, top_k=top_k) for snapshot in snapshots]


def compute_dri_full(combined_data: dict[str, Any]) -> int:
    """Legacy API support."""
    # Since combined_data already has external+shipment, we can simulate the pipeline
    # But for a single call, we just use the pipeline logic
    ml_output = compute_dri_pipeline(combined_data, combined_data)
    return ml_output["dri"]


risk_scoring_service = RiskScoringService()
