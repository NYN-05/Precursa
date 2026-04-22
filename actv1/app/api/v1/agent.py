from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.models import AgentAction, AgentOverride
from app.db.session import get_db
from app.services.agent_service import (
    clear_agent_override,
    list_agent_actions,
    run_agent_for_shipment,
    run_agent_tick,
    set_agent_override,
)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentStateResponse(BaseModel):
    shipment_id: str
    dri_score: int
    dri_level: str
    shap_factors: list[dict[str, Any]]
    disruption_type: str | None = None
    candidate_routes: list[dict[str, Any]]
    lp_valid_routes: list[dict[str, Any]]
    selected_route: dict[str, Any] | None = None
    action_taken: str
    roi_defended_usd: float
    copilot_explanation: str | None = None
    ops_override_active: bool
    approval_status: str
    route_selected_id: int | None = None
    rejected_routes: list[dict[str, Any]]
    replay_data: dict[str, Any]


class AgentActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    action_type: str
    dri_at_action: int
    route_selected_id: int | None
    shap_top_factor: str | None
    lp_constraints_count: int
    roi_defended_usd: float
    approval_status: str
    overridden_by_ops: bool
    replay_data: dict[str, Any]
    state_snapshot: dict[str, Any]
    executed_at: datetime


class OverrideRequest(BaseModel):
    reason: str
    expires_minutes: int | None = None


class OverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    active: bool
    reason: str
    requested_by: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


@router.post("/run/{shipment_key}", response_model=AgentStateResponse)
def run_agent_endpoint(
    shipment_key: str,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> AgentStateResponse:
    try:
        state = run_agent_for_shipment(db, shipment_key=shipment_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    return AgentStateResponse.model_validate(state)


@router.post("/tick", response_model=list[AgentStateResponse])
def run_agent_tick_endpoint(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> list[AgentStateResponse]:
    states = run_agent_tick(db, limit=limit)
    db.commit()
    return [AgentStateResponse.model_validate(state) for state in states]


@router.get("/actions", response_model=list[AgentActionResponse])
def list_agent_actions_endpoint(
    shipment_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[AgentActionResponse]:
    actions = list_agent_actions(db, shipment_key=shipment_key, limit=limit)
    return [AgentActionResponse.model_validate(action) for action in actions]


@router.post("/override/{shipment_key}", response_model=OverrideResponse)
def set_override_endpoint(
    shipment_key: str,
    request: OverrideRequest,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_roles("admin", "logistics_manager")),
) -> OverrideResponse:
    override = set_agent_override(
        db,
        shipment_key=shipment_key,
        reason=request.reason,
        requested_by=context["username"],
        expires_minutes=request.expires_minutes,
    )
    db.commit()
    db.refresh(override)
    return OverrideResponse.model_validate(override)


@router.post("/override/{shipment_key}/clear", response_model=OverrideResponse)
def clear_override_endpoint(
    shipment_key: str,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_roles("admin", "logistics_manager")),
) -> OverrideResponse:
    override = clear_agent_override(db, shipment_key=shipment_key, requested_by=context["username"])
    if override is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No override found for shipment '{shipment_key}'",
        )
    db.commit()
    db.refresh(override)
    return OverrideResponse.model_validate(override)
