from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.ingestion.normalizer import SUPPORTED_SOURCES
from app.services.ingestion import (
    ingest_event as ingest_event_service,
    ingest_mock_events,
    list_ingestion_events,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestEventRequest(BaseModel):
    source: str
    payload: dict[str, Any]


class IngestionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_event_id: str | None
    dedupe_key: str
    event_type: str
    entity_id: str | None
    severity: float
    occurred_at: datetime
    ingested_at: datetime
    payload: dict[str, Any]


class IngestEventResult(BaseModel):
    created: bool
    event: IngestionEventResponse


def _validate_source(source: str) -> str:
    normalized = source.strip().lower()
    if normalized not in SUPPORTED_SOURCES:
        allowed = ", ".join(sorted(SUPPORTED_SOURCES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported source '{source}'. Allowed sources: {allowed}",
        )
    return normalized


@router.post("/events", response_model=IngestEventResult)
def ingest_event_endpoint(
    request: IngestEventRequest,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> IngestEventResult:
    source = _validate_source(request.source)
    event, created = ingest_event_service(db, source=source, payload=request.payload)
    return IngestEventResult(
        created=created,
        event=IngestionEventResponse.model_validate(event),
    )


@router.post("/mock/{source}", response_model=list[IngestEventResult])
def ingest_mock_events_endpoint(
    source: str,
    count: int = Query(default=1, ge=1, le=50),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager")),
) -> list[IngestEventResult]:
    validated_source = _validate_source(source)
    ingested = ingest_mock_events(db, source=validated_source, count=count)
    return [
        IngestEventResult(created=created, event=IngestionEventResponse.model_validate(event))
        for event, created in ingested
    ]


@router.get("/events", response_model=list[IngestionEventResponse])
def list_events_endpoint(
    source: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[IngestionEventResponse]:
    normalized_source = _validate_source(source) if source else None
    events = list_ingestion_events(db, source=normalized_source, limit=limit)
    return [IngestionEventResponse.model_validate(event) for event in events]
