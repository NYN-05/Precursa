from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from typing import Any

import xgboost as xgb
from sklearn.ensemble import IsolationForest

from app.db.models import ShipmentSnapshot

FEATURE_NAMES: tuple[str, ...] = (
    "event_count_norm",
    "avg_severity",
    "last_severity",
    "provisional_dri_norm",
    "source_risk",
    "status_risk",
    "delay_risk",
    "impact_risk",
    "recency_score",
)

SOURCE_RISK_PRIOR: dict[str, float] = {
    "ais": 0.35,
    "weather": 0.72,
    "customs": 0.58,
    "tariff": 0.66,
    "news": 0.52,
}

STATUS_RISK_PRIOR: dict[str, float] = {
    "on_time": 0.05,
    "stable": 0.08,
    "inspection": 0.42,
    "delayed": 0.68,
    "blocked": 0.92,
    "storm": 0.88,
    "strike": 0.86,
}

MODEL_VERSION = "chunk4-v1"


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    def __init__(
        self,
        seed: int = 42,
        xgboost_weight: float = 0.78,
        anomaly_weight: float = 0.22,
    ) -> None:
        self._seed = seed
        self._xgboost_weight = xgboost_weight
        self._anomaly_weight = anomaly_weight

        self._booster: xgb.Booster | None = None
        self._anomaly_model: IsolationForest | None = None
        self._anomaly_min = -1.0
        self._anomaly_max = 1.0

    def _build_synthetic_training_set(
        self,
        size: int,
        normal_mode: bool,
    ) -> tuple[list[list[float]], list[float]]:
        rng = Random(self._seed + (11 if normal_mode else 0))
        features: list[list[float]] = []
        targets: list[float] = []

        for _ in range(size):
            if normal_mode:
                event_count_norm = rng.uniform(0.02, 0.35)
                avg_severity = rng.uniform(0.05, 0.45)
                last_severity = rng.uniform(0.05, 0.50)
                provisional_dri_norm = rng.uniform(0.04, 0.42)
                source_risk = rng.uniform(0.20, 0.48)
                status_risk = rng.uniform(0.10, 0.40)
                delay_risk = rng.uniform(0.00, 0.28)
                impact_risk = rng.uniform(0.00, 0.35)
                recency_score = rng.uniform(0.60, 1.00)
            else:
                event_count_norm = rng.uniform(0.00, 1.00)
                avg_severity = rng.uniform(0.00, 1.00)
                last_severity = rng.uniform(0.00, 1.00)
                provisional_dri_norm = rng.uniform(0.00, 1.00)
                source_risk = rng.uniform(0.15, 0.95)
                status_risk = rng.uniform(0.05, 0.95)
                delay_risk = rng.uniform(0.00, 1.00)
                impact_risk = rng.uniform(0.00, 1.00)
                recency_score = rng.uniform(0.00, 1.00)

                if rng.random() < 0.24:
                    delay_risk = _clamp(delay_risk + rng.uniform(0.20, 0.55))
                if rng.random() < 0.18:
                    impact_risk = _clamp(impact_risk + rng.uniform(0.18, 0.45))

            row = [
                event_count_norm,
                avg_severity,
                last_severity,
                provisional_dri_norm,
                source_risk,
                status_risk,
                delay_risk,
                impact_risk,
                recency_score,
            ]

            target = (
                (0.19 * event_count_norm)
                + (0.21 * avg_severity)
                + (0.17 * last_severity)
                + (0.09 * provisional_dri_norm)
                + (0.10 * source_risk)
                + (0.09 * status_risk)
                + (0.08 * delay_risk)
                + (0.05 * impact_risk)
                + (0.02 * recency_score)
            )
            target += 0.08 * (delay_risk * source_risk)
            target += 0.04 * (status_risk * impact_risk)
            target += rng.uniform(-0.02, 0.02)

            if normal_mode:
                target *= rng.uniform(0.35, 0.70)

            features.append([_clamp(v) for v in row])
            targets.append(_clamp(target))

        return features, targets

    def _ensure_models(self) -> None:
        if self._booster is not None and self._anomaly_model is not None:
            return

        training_features, training_targets = self._build_synthetic_training_set(
            size=1200,
            normal_mode=False,
        )

        dtrain = xgb.DMatrix(training_features, label=training_targets, feature_names=list(FEATURE_NAMES))
        self._booster = xgb.train(
            {
                "objective": "reg:squarederror",
                "max_depth": 4,
                "eta": 0.08,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "seed": self._seed,
            },
            dtrain,
            num_boost_round=80,
        )

        normal_features, _ = self._build_synthetic_training_set(size=1400, normal_mode=True)
        self._anomaly_model = IsolationForest(
            n_estimators=120,
            contamination=0.12,
            random_state=self._seed,
        )
        self._anomaly_model.fit(normal_features)

        baseline_scores = self._anomaly_model.score_samples(normal_features)
        self._anomaly_min = float(min(baseline_scores))
        self._anomaly_max = float(max(baseline_scores))

    @staticmethod
    def _hours_since(occurred_at: datetime) -> float:
        current = datetime.now(timezone.utc)
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        elapsed = current - occurred_at.astimezone(timezone.utc)
        return max(elapsed.total_seconds() / 3600.0, 0.0)

    def _extract_features(self, snapshot: ShipmentSnapshot) -> list[float]:
        feature_vector = snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}

        event_count_norm = _clamp(snapshot.event_count / 25.0)
        avg_severity = _clamp(snapshot.avg_severity)
        last_severity = _clamp(snapshot.last_severity)
        provisional_dri_norm = _clamp(snapshot.provisional_dri / 100.0)

        source_risk = _clamp(SOURCE_RISK_PRIOR.get(snapshot.last_source, 0.40))

        status_raw = str(feature_vector.get("status", "")).strip().lower()
        status_risk = _clamp(STATUS_RISK_PRIOR.get(status_raw, 0.30))

        delay_hours = _safe_float(feature_vector.get("delay_hours"), default=0.0)
        delay_risk = _clamp(delay_hours / 72.0)

        impact_score = feature_vector.get("impact_score", feature_vector.get("severity_index", 0.0))
        impact_risk = _safe_float(impact_score, default=0.0)
        if impact_risk > 1.0:
            impact_risk = impact_risk / 100.0
        impact_risk = _clamp(impact_risk)

        recency_score = 1.0 - _clamp(self._hours_since(snapshot.last_occurred_at) / 72.0)

        return [
            event_count_norm,
            avg_severity,
            last_severity,
            provisional_dri_norm,
            source_risk,
            status_risk,
            delay_risk,
            impact_risk,
            recency_score,
        ]

    def _normalize_anomaly_score(self, anomaly_raw_score: float) -> float:
        span = max(self._anomaly_max - self._anomaly_min, 1e-9)
        normalized = (self._anomaly_max - anomaly_raw_score) / span
        return _clamp(normalized)

    @staticmethod
    def _build_top_factors(shap_values: list[float], top_k: int) -> list[RiskFactor]:
        ranked: list[RiskFactor] = []
        for feature_name, shap_value in zip(FEATURE_NAMES, shap_values):
            direction = "increase" if shap_value >= 0 else "decrease"
            ranked.append(
                RiskFactor(
                    feature=feature_name,
                    shap_value=round(float(shap_value), 6),
                    direction=direction,
                )
            )

        ranked.sort(key=lambda factor: abs(factor.shap_value), reverse=True)

        if not ranked:
            return [RiskFactor(feature="baseline", shap_value=0.0, direction="increase")]

        return ranked[:top_k]

    def score_snapshot(self, snapshot: ShipmentSnapshot, top_k: int = 5) -> ShipmentRiskScore:
        self._ensure_models()

        if self._booster is None or self._anomaly_model is None:  # pragma: no cover
            raise RuntimeError("Risk scoring models are not initialized")

        top_k = max(1, min(top_k, len(FEATURE_NAMES) + 1))

        features = self._extract_features(snapshot)
        dmatrix = xgb.DMatrix([features], feature_names=list(FEATURE_NAMES))

        xgboost_score = _clamp(float(self._booster.predict(dmatrix)[0]))

        anomaly_raw = float(self._anomaly_model.score_samples([features])[0])
        anomaly_score = self._normalize_anomaly_score(anomaly_raw)

        combined_score = _clamp(
            (xgboost_score * self._xgboost_weight) + (anomaly_score * self._anomaly_weight)
        )
        dri = int(round(combined_score * 100.0))

        shap_with_bias = self._booster.predict(dmatrix, pred_contribs=True)[0]
        shap_values = [float(value) for value in shap_with_bias[:-1]]
        top_factors = self._build_top_factors(shap_values, top_k=top_k)

        if anomaly_score >= 0.75:
            anomaly_factor = RiskFactor(
                feature="anomaly_signal",
                shap_value=round(anomaly_score - 0.50, 6),
                direction="increase",
            )
            merged = [anomaly_factor, *top_factors]
            merged.sort(key=lambda factor: abs(factor.shap_value), reverse=True)
            top_factors = merged[:top_k]

        return ShipmentRiskScore(
            shipment_key=snapshot.shipment_key,
            dri=dri,
            xgboost_score=round(xgboost_score, 6),
            anomaly_score=round(anomaly_score, 6),
            combined_score=round(combined_score, 6),
            top_factors=top_factors,
            model_version=MODEL_VERSION,
            scored_at=datetime.now(timezone.utc),
        )

    def score_snapshots(
        self,
        snapshots: list[ShipmentSnapshot],
        top_k: int = 5,
    ) -> list[ShipmentRiskScore]:
        return [self.score_snapshot(snapshot, top_k=top_k) for snapshot in snapshots]


risk_scoring_service = RiskScoringService()
