from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import NotificationRecord
from app.services.observability import metrics
from app.websocket.broadcaster import broadcaster


def send_notification(
    db: Session,
    shipment_key: str,
    channel: str,
    payload: dict[str, Any],
    recipient: str | None = None,
) -> NotificationRecord:
    record = NotificationRecord(
        shipment_key=shipment_key,
        channel=channel,
        recipient=recipient or settings.notification_default_recipient,
        status="sent",
        payload=payload,
    )
    db.add(record)
    db.flush()
    metrics.increment("notifications_sent_total")
    broadcaster.publish(
        "notification_sent",
        {
            "id": record.id,
            "shipment_key": shipment_key,
            "channel": channel,
            "recipient": record.recipient,
            "status": record.status,
            "payload": payload,
        },
    )
    return record


def list_notifications(
    db: Session,
    shipment_key: str | None = None,
    limit: int = 50,
) -> list[NotificationRecord]:
    query = select(NotificationRecord)
    if shipment_key:
        query = query.where(NotificationRecord.shipment_key == shipment_key)
    query = query.order_by(
        desc(NotificationRecord.created_at),
        desc(NotificationRecord.id),
    ).limit(limit)
    return list(db.scalars(query).all())
