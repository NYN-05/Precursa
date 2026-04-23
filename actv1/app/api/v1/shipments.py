from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.models import ShipmentSnapshot
from app.db.session import get_db
from app.services.feature_state import list_shipment_snapshots
from app.services.route_intelligence import PORTS
from app.services.risk_scoring import risk_scoring_service

router = APIRouter(prefix="/shipments", tags=["shipments"])


class DashboardRiskFactor(BaseModel):
    name: str
    impact: int


class DashboardRecommendation(BaseModel):
    route: str
    time_saved: str
    cost_impact: int


class DashboardShipment(BaseModel):
    id: str
    lat: float
    lon: float
    dri: int
    status: str
    top_factors: list[DashboardRiskFactor]
    recommendation: DashboardRecommendation


def _status(dri: int) -> str:
    if dri > 75:
        return "high"
    if dri >= 40:
        return "medium"
    return "low"


def _stable_offset(seed: str, axis: str) -> float:
    value = 0
    for char in f"{seed}:{axis}":
        value = (value * 31 + ord(char)) % 1000
    return (value / 1000 - 0.5) * 0.9


def _coords(snapshot: ShipmentSnapshot, feature_vector: dict[str, Any]) -> tuple[float, float]:
    port = (
        feature_vector.get("origin_port")
        or feature_vector.get("affected_port")
        or feature_vector.get("port_name")
        or "Singapore"
    )
    port_info = PORTS.get(str(port), PORTS["Singapore"])
    lat = feature_vector.get("lat", port_info["lat"] + _stable_offset(snapshot.shipment_key, "lat"))
    lon = feature_vector.get("lon", port_info["lon"] + _stable_offset(snapshot.shipment_key, "lon"))
    return float(lat), float(lon)


def _fallback_factors(snapshot: ShipmentSnapshot, feature_vector: dict[str, Any]) -> list[DashboardRiskFactor]:
    factors: list[DashboardRiskFactor] = []
    delay_hours = float(feature_vector.get("delay_hours") or 0)
    if delay_hours > 0:
        factors.append(DashboardRiskFactor(name=f"delay_{round(delay_hours)}_hours", impact=40))
    if snapshot.last_event_type:
        factors.append(DashboardRiskFactor(name=snapshot.last_event_type, impact=25))
    if feature_vector.get("origin_port"):
        factors.append(DashboardRiskFactor(name="port_congestion", impact=20))
    if feature_vector.get("destination_country"):
        factors.append(DashboardRiskFactor(name="geo_risk", impact=15))
    return factors or [
        DashboardRiskFactor(name="port_congestion", impact=35),
        DashboardRiskFactor(name="weather", impact=25),
    ]


def _scored_factors(snapshot: ShipmentSnapshot, feature_vector: dict[str, Any]) -> tuple[int, list[DashboardRiskFactor]]:
    try:
        score = risk_scoring_service.score_snapshot(snapshot, top_k=3)
    except Exception:
        return snapshot.provisional_dri, _fallback_factors(snapshot, feature_vector)

    raw_factors = score.top_factors
    total = sum(abs(factor.shap_value) for factor in raw_factors) or 1
    factors = [
        DashboardRiskFactor(
            name=factor.feature,
            impact=max(1, round(abs(factor.shap_value) / total * 100)),
        )
        for factor in raw_factors
    ]
    return score.dri, factors or _fallback_factors(snapshot, feature_vector)


def _recommendation(dri: int, feature_vector: dict[str, Any]) -> DashboardRecommendation:
    recommended_route = feature_vector.get("recommended_route")
    if not recommended_route:
        recommended_route = "Port Klang" if dri > 75 else feature_vector.get("destination_port") or "Current route"

    if dri > 75:
        return DashboardRecommendation(route=str(recommended_route), time_saved="8 hours", cost_impact=12000)
    if dri >= 40:
        return DashboardRecommendation(route=str(recommended_route), time_saved="4 hours", cost_impact=6500)
    return DashboardRecommendation(route=str(recommended_route), time_saved="0 hours", cost_impact=0)


def _to_dashboard_shipment(snapshot: ShipmentSnapshot) -> DashboardShipment:
    feature_vector = snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
    dri, factors = _scored_factors(snapshot, feature_vector)
    lat, lon = _coords(snapshot, feature_vector)
    return DashboardShipment(
        id=snapshot.shipment_key,
        lat=lat,
        lon=lon,
        dri=dri,
        status=_status(dri),
        top_factors=factors[:3],
        recommendation=_recommendation(dri, feature_vector),
    )


@router.get("", response_model=list[DashboardShipment])
def list_dashboard_shipments(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[DashboardShipment]:
    snapshots = list_shipment_snapshots(db, limit=limit)
    return [_to_dashboard_shipment(snapshot) for snapshot in snapshots]
