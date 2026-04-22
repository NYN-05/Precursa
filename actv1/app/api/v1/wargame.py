from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.wargame import (
    get_wargame_session,
    list_wargame_events,
    list_wargame_sessions,
    run_wargame,
    stop_wargame,
)

router = APIRouter(prefix="/wargame", tags=["wargame"])


class WargameStartRequest(BaseModel):
    duration_seconds: int = 600
    tick_seconds: int | None = None


class WargameSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: datetime | None
    disturber_events_fired: int
    healer_actions_taken: int
    total_roi_defended_usd: float
    status: str


class WargameEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    actor: str
    event_type: str
    affected_port: str | None
    severity: float
    affected_shipment_ids: list[str]
    potential_loss_usd: float
    roi_defended_usd: float
    payload: dict[str, Any]
    created_at: datetime


@router.post("/start", response_model=WargameSessionResponse)
def start_wargame_endpoint(
    request: WargameStartRequest,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> WargameSessionResponse:
    session = run_wargame(
        db,
        duration_seconds=request.duration_seconds,
        tick_seconds=request.tick_seconds,
    )
    db.commit()
    db.refresh(session)
    return WargameSessionResponse.model_validate(session)


@router.get("/status/{session_id}", response_model=WargameSessionResponse)
def wargame_status_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> WargameSessionResponse:
    session = get_wargame_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="War game session not found",
        )
    return WargameSessionResponse.model_validate(session)


@router.post("/stop/{session_id}", response_model=WargameSessionResponse)
def stop_wargame_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "logistics_manager")),
) -> WargameSessionResponse:
    session = stop_wargame(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="War game session not found",
        )
    db.commit()
    db.refresh(session)
    return WargameSessionResponse.model_validate(session)


@router.get("/history/{session_id}", response_model=list[WargameEventResponse])
def wargame_history_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[WargameEventResponse]:
    if get_wargame_session(db, session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="War game session not found",
        )
    events = list_wargame_events(db, session_id=session_id)
    return [WargameEventResponse.model_validate(event) for event in events]


@router.get("/sessions", response_model=list[WargameSessionResponse])
def wargame_sessions_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[WargameSessionResponse]:
    sessions = list_wargame_sessions(db, limit=limit)
    return [WargameSessionResponse.model_validate(session) for session in sessions]
