from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_roles
from app.db.session import get_db
from app.services.notifications import list_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_key: str
    channel: str
    recipient: str
    status: str
    payload: dict[str, Any]
    created_at: datetime


@router.get("", response_model=list[NotificationResponse])
def list_notifications_endpoint(
    shipment_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_roles("admin", "ops_analyst", "logistics_manager", "auditor")),
) -> list[NotificationResponse]:
    records = list_notifications(db, shipment_key=shipment_key, limit=limit)
    return [NotificationResponse.model_validate(record) for record in records]
