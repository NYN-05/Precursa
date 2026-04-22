from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.feature_state import (
    get_cached_shipment_state,
    get_shipment_snapshot,
    list_shipment_snapshots,
)

router = APIRouter(prefix="/state", tags=["state"])


class ShipmentSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    latest_event_id: int | None
    last_source: str
    last_event_type: str
    last_entity_id: str | None
    event_count: int
    avg_severity: float
    last_severity: float
    last_occurred_at: datetime
    provisional_dri: int
    feature_vector: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CachedStateResponse(BaseModel):
    shipment_key: str
    cached_state: dict[str, Any]


@router.get("/snapshots", response_model=list[ShipmentSnapshotResponse])
def list_snapshots_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[ShipmentSnapshotResponse]:
    snapshots = list_shipment_snapshots(db, limit=limit)
    return [ShipmentSnapshotResponse.model_validate(snapshot) for snapshot in snapshots]


@router.get("/snapshots/{shipment_key}", response_model=ShipmentSnapshotResponse)
def get_snapshot_endpoint(
    shipment_key: str,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> ShipmentSnapshotResponse:
    snapshot = get_shipment_snapshot(db, shipment_key=shipment_key)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment snapshot not found for key '{shipment_key}'",
        )

    return ShipmentSnapshotResponse.model_validate(snapshot)


@router.get("/cache/{shipment_key}", response_model=CachedStateResponse)
def get_cached_state_endpoint(
    shipment_key: str,
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> CachedStateResponse:
    cached_state = get_cached_shipment_state(shipment_key)
    if cached_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached live state found for key '{shipment_key}'",
        )

    return CachedStateResponse(shipment_key=shipment_key, cached_state=cached_state)
