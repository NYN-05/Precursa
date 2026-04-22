from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.feature_state import get_shipment_snapshot, list_shipment_snapshots
from app.services.risk_scoring import RiskFactor, ShipmentRiskScore, risk_scoring_service

router = APIRouter(prefix="/risk", tags=["risk"])


class RiskFactorResponse(BaseModel):
    feature: str
    shap_value: float
    direction: str


class ShipmentRiskScoreResponse(BaseModel):
    shipment_key: str
    dri: int
    xgboost_score: float
    anomaly_score: float
    combined_score: float
    model_version: str
    scored_at: datetime
    top_factors: list[RiskFactorResponse]


def _to_factor_response(factor: RiskFactor) -> RiskFactorResponse:
    return RiskFactorResponse(
        feature=factor.feature,
        shap_value=factor.shap_value,
        direction=factor.direction,
    )


def _to_score_response(score: ShipmentRiskScore) -> ShipmentRiskScoreResponse:
    return ShipmentRiskScoreResponse(
        shipment_key=score.shipment_key,
        dri=score.dri,
        xgboost_score=score.xgboost_score,
        anomaly_score=score.anomaly_score,
        combined_score=score.combined_score,
        model_version=score.model_version,
        scored_at=score.scored_at,
        top_factors=[_to_factor_response(factor) for factor in score.top_factors],
    )


@router.get("/shipments/{shipment_key}", response_model=ShipmentRiskScoreResponse)
def score_shipment_endpoint(
    shipment_key: str,
    top_k: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> ShipmentRiskScoreResponse:
    snapshot = get_shipment_snapshot(db, shipment_key=shipment_key)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment snapshot not found for key '{shipment_key}'",
        )

    score = risk_scoring_service.score_snapshot(snapshot, top_k=top_k)
    return _to_score_response(score)


@router.get("/shipments", response_model=list[ShipmentRiskScoreResponse])
def score_shipments_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    top_k: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[ShipmentRiskScoreResponse]:
    snapshots = list_shipment_snapshots(db, limit=limit)
    scores = risk_scoring_service.score_snapshots(snapshots, top_k=top_k)
    return [_to_score_response(score) for score in scores]
