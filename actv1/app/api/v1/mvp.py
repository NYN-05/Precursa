from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.db.models import ShipmentSnapshot, IngestionEvent
from app.services.feature_state import cache_shipment_snapshot
from app.services.agent_service import run_agent_for_shipment

router = APIRouter(prefix="/mvp", tags=["mvp"])

class CreateShipmentRequest(BaseModel):
    shipment_key: str
    origin_port: str
    destination_port: str
    cargo_type: str = "general"

@router.post("/shipments")
def create_shipment(
    request: CreateShipmentRequest,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst")),
):
    existing = db.query(ShipmentSnapshot).filter(ShipmentSnapshot.shipment_key == request.shipment_key).first()
    if existing:
        return existing

    snapshot = ShipmentSnapshot(
        shipment_key=request.shipment_key,
        last_source="manual",
        last_event_type="initial_load",
        event_count=1,
        last_occurred_at=datetime.now(timezone.utc),
        feature_vector={
            "origin_port": request.origin_port,
            "destination_port": request.destination_port,
            "cargo_type": request.cargo_type,
            "status": "in_transit",
            "current_route": [request.origin_port, request.destination_port]
        }
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    cache_shipment_snapshot(snapshot)
    return snapshot

@router.post("/trigger-disruption/{shipment_key}")
def trigger_disruption(
    shipment_key: str,
    severity: float = 0.8,
    event_type: str = "storm",
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst")),
):
    snapshot = db.query(ShipmentSnapshot).filter(ShipmentSnapshot.shipment_key == shipment_key).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Update snapshot with disruption
    snapshot.event_count += 1
    snapshot.avg_severity = (snapshot.avg_severity * (snapshot.event_count - 1) + severity) / snapshot.event_count
    snapshot.last_severity = severity
    snapshot.last_event_type = event_type
    snapshot.last_source = "weather"
    snapshot.last_occurred_at = datetime.now(timezone.utc)
    
    # Update feature vector for DRI impact
    fv = dict(snapshot.feature_vector)
    fv["status"] = "delayed"
    fv["delay_hours"] = fv.get("delay_hours", 0) + (severity * 48)
    snapshot.feature_vector = fv
    
    db.commit()
    db.refresh(snapshot)
    cache_shipment_snapshot(snapshot)
    
    return {"message": f"Disruption triggered for {shipment_key}", "dri": snapshot.provisional_dri}

@router.post("/reroute/{shipment_key}")
def manual_reroute(
    shipment_key: str,
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst")),
):
    try:
        state = run_agent_for_shipment(db, shipment_key)
        db.commit()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
