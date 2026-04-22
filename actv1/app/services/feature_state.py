from datetime import timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import IngestionEvent, ShipmentSnapshot
from app.services.state_cache import live_state_cache


def _extract_payload(event: IngestionEvent) -> dict[str, Any]:
    if isinstance(event.payload, dict):
        return event.payload
    return {}


def derive_shipment_key(event: IngestionEvent) -> str:
    payload = _extract_payload(event)

    shipment_ref = payload.get("shipment_ref")
    if shipment_ref:
        return str(shipment_ref)

    if event.entity_id:
        if event.source in {"weather", "news"}:
            return f"port:{event.entity_id}"
        if event.source == "ais":
            return f"vessel:{event.entity_id}"
        return str(event.entity_id)

    port_code = payload.get("port_code")
    if port_code:
        return f"port:{port_code}"

    region = payload.get("region")
    if region:
        return f"port:{region}"

    mmsi = payload.get("mmsi")
    if mmsi:
        return f"vessel:{mmsi}"

    if event.source_event_id:
        return f"{event.source}:{event.source_event_id}"

    return f"{event.source}:event-{event.id}"


def _calculate_provisional_dri(avg_severity: float, last_severity: float, event_count: int) -> int:
    severity_score = ((avg_severity * 0.6) + (last_severity * 0.4)) * 100
    volume_bonus = min(10, max(0, event_count - 1))
    normalized = max(0.0, min(100.0, severity_score + volume_bonus))
    return int(round(normalized))


def _build_feature_vector(snapshot: ShipmentSnapshot, event: IngestionEvent) -> dict[str, Any]:
    payload = _extract_payload(event)

    feature_vector: dict[str, Any] = {
        "shipment_key": snapshot.shipment_key,
        "event_count": snapshot.event_count,
        "avg_severity": round(snapshot.avg_severity, 4),
        "last_severity": round(snapshot.last_severity, 4),
        "last_source": snapshot.last_source,
        "last_event_type": snapshot.last_event_type,
        "last_entity_id": snapshot.last_entity_id,
        "last_occurred_at": snapshot.last_occurred_at.astimezone(timezone.utc).isoformat(),
        "source_event_id": event.source_event_id,
    }

    for field in (
        "shipment_ref",
        "port_code",
        "region",
        "status",
        "condition",
        "cargo_type",
        "origin_port",
        "destination_port",
        "origin_country",
        "destination_country",
        "cargo_value_usd",
        "weight_kg",
        "sla_hours",
        "delay_hours",
        "impact_score",
        "severity_index",
        "temp_requirement_celsius",
        "max_risk_tolerance",
        "tariff_priority_weight",
        "policy_priority_weight",
        "sanctioned_ports",
    ):
        value = payload.get(field)
        if value is not None:
            feature_vector[field] = value

    return feature_vector


def build_live_state_payload(snapshot: ShipmentSnapshot) -> dict[str, Any]:
    updated_at = snapshot.updated_at or snapshot.last_occurred_at
    return {
        "shipment_key": snapshot.shipment_key,
        "latest_event_id": snapshot.latest_event_id,
        "event_count": snapshot.event_count,
        "provisional_dri": snapshot.provisional_dri,
        "feature_vector": snapshot.feature_vector,
        "updated_at": updated_at.astimezone(timezone.utc).isoformat(),
    }


def upsert_shipment_snapshot(db: Session, event: IngestionEvent) -> ShipmentSnapshot:
    shipment_key = derive_shipment_key(event)

    snapshot = db.scalar(
        select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_key)
    )

    if snapshot is None:
        snapshot = ShipmentSnapshot(
            shipment_key=shipment_key,
            latest_event_id=event.id,
            last_source=event.source,
            last_event_type=event.event_type,
            last_entity_id=event.entity_id,
            event_count=1,
            avg_severity=event.severity,
            last_severity=event.severity,
            last_occurred_at=event.occurred_at,
        )
    else:
        previous_count = snapshot.event_count
        snapshot.event_count = previous_count + 1
        snapshot.avg_severity = (
            (snapshot.avg_severity * previous_count) + event.severity
        ) / snapshot.event_count
        snapshot.latest_event_id = event.id
        snapshot.last_source = event.source
        snapshot.last_event_type = event.event_type
        snapshot.last_entity_id = event.entity_id
        snapshot.last_severity = event.severity
        snapshot.last_occurred_at = event.occurred_at

    snapshot.provisional_dri = _calculate_provisional_dri(
        avg_severity=snapshot.avg_severity,
        last_severity=snapshot.last_severity,
        event_count=snapshot.event_count,
    )
    snapshot.feature_vector = _build_feature_vector(snapshot, event)

    db.add(snapshot)
    return snapshot


def cache_shipment_snapshot(snapshot: ShipmentSnapshot) -> None:
    live_state_cache.set_state(snapshot.shipment_key, build_live_state_payload(snapshot))


def list_shipment_snapshots(db: Session, limit: int) -> list[ShipmentSnapshot]:
    query = (
        select(ShipmentSnapshot)
        .order_by(desc(ShipmentSnapshot.updated_at), desc(ShipmentSnapshot.id))
        .limit(limit)
    )
    return list(db.scalars(query).all())


def get_shipment_snapshot(db: Session, shipment_key: str) -> ShipmentSnapshot | None:
    return db.scalar(select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_key))


def get_cached_shipment_state(shipment_key: str) -> dict[str, Any] | None:
    return live_state_cache.get_state(shipment_key)
