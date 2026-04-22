from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.observability import metrics
from app.services.resilience import list_dead_letters
from app.services.streaming import run_mock_stream_tick, streaming_status

router = APIRouter(prefix="/ops", tags=["ops"])


class DeadLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    operation: str
    payload: dict[str, Any]
    error_message: str
    retry_count: int
    status: str
    created_at: datetime
    updated_at: datetime


@router.get("/metrics")
def metrics_endpoint(
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> dict[str, Any]:
    return metrics.snapshot()


@router.get("/metrics.prom")
def prometheus_metrics_endpoint() -> Response:
    return Response(metrics.prometheus_text(), media_type="text/plain; version=0.0.4")


@router.get("/streaming/status")
def streaming_status_endpoint(
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> dict[str, Any]:
    return streaming_status()


@router.post("/streaming/mock-tick")
def mock_stream_tick_endpoint(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> dict[str, Any]:
    result = run_mock_stream_tick(db)
    db.commit()
    return result


@router.get("/dead-letter", response_model=list[DeadLetterResponse])
def dead_letter_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[DeadLetterResponse]:
    records = list_dead_letters(db, limit=limit)
    return [DeadLetterResponse.model_validate(record) for record in records]
