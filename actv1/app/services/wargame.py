from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ShipmentSnapshot, WargameEvent, WargameSession
from app.services.agent_service import run_agent_for_shipment
from app.services.ingestion import ingest_event
from app.services.observability import metrics
from app.websocket.broadcaster import broadcaster

DISRUPTION_FREQUENCIES = {
    "port_congestion": 0.40,
    "weather_event": 0.30,
    "carrier_failure": 0.15,
    "customs_delay": 0.10,
    "geopolitical": 0.05,
}

DISRUPTION_COSTS = {
    "port_congestion": 45000,
    "weather_event": 62000,
    "carrier_failure": 38000,
    "customs_delay": 28000,
    "geopolitical": 95000,
}

DEMO_SHIPMENTS: tuple[dict[str, Any], ...] = (
    {
        "shipment_ref": "SHP-001",
        "origin_port": "Mumbai",
        "destination_port": "Rotterdam",
        "origin_country": "IN",
        "destination_country": "NL",
        "cargo_type": "Electronics",
        "cargo_value_usd": 120000,
        "weight_kg": 16000,
        "sla_hours": 260,
    },
    {
        "shipment_ref": "SHP-002",
        "origin_port": "Shanghai",
        "destination_port": "Los Angeles",
        "origin_country": "CN",
        "destination_country": "US",
        "cargo_type": "E-commerce",
        "cargo_value_usd": 90000,
        "weight_kg": 14000,
        "sla_hours": 230,
    },
    {
        "shipment_ref": "SHP-003",
        "origin_port": "Chennai",
        "destination_port": "Hamburg",
        "origin_country": "IN",
        "destination_country": "DE",
        "cargo_type": "Automotive",
        "cargo_value_usd": 180000,
        "weight_kg": 21000,
        "sla_hours": 280,
    },
    {
        "shipment_ref": "SHP-004",
        "origin_port": "Nhava Sheva",
        "destination_port": "Felixstowe",
        "origin_country": "IN",
        "destination_country": "GB",
        "cargo_type": "Pharma",
        "cargo_value_usd": 240000,
        "weight_kg": 12000,
        "temp_requirement_celsius": 4.0,
        "sla_hours": 275,
    },
    {
        "shipment_ref": "SHP-005",
        "origin_port": "Hong Kong",
        "destination_port": "Los Angeles",
        "origin_country": "HK",
        "destination_country": "US",
        "cargo_type": "FMCG",
        "cargo_value_usd": 75000,
        "weight_kg": 10000,
        "sla_hours": 210,
    },
)


@dataclass(frozen=True)
class DisturbanceEvent:
    event_type: str
    affected_port: str
    severity: float
    affected_shipment_ids: list[str]
    potential_loss_usd: float
    timestamp: str


class MonteCarloDisturber:
    def __init__(self, intensity: float = 0.7, seed: int = 20260423) -> None:
        self.intensity = intensity
        self._rng = random.Random(seed)

    def generate_event(self, active_shipments: list[dict[str, Any]]) -> DisturbanceEvent:
        event_type = self._rng.choices(
            population=list(DISRUPTION_FREQUENCIES.keys()),
            weights=list(DISRUPTION_FREQUENCIES.values()),
            k=1,
        )[0]
        severity = round(min(1.0, max(0.05, self._rng.betavariate(2, 2) * self.intensity)), 2)
        selected_shipment = self._rng.choice(active_shipments)
        route = selected_shipment["route"]
        affected_port = self._rng.choice(route)
        affected_shipments = [
            shipment["id"] for shipment in active_shipments if affected_port in shipment["route"]
        ]
        potential_loss = DISRUPTION_COSTS[event_type] * severity * max(1, len(affected_shipments))
        return DisturbanceEvent(
            event_type=event_type,
            affected_port=affected_port,
            severity=severity,
            affected_shipment_ids=affected_shipments,
            potential_loss_usd=round(potential_loss, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def ensure_demo_shipments(db: Session) -> None:
    existing_count = db.scalar(select(ShipmentSnapshot).limit(1))
    if existing_count is not None:
        return
    for index, payload in enumerate(DEMO_SHIPMENTS, start=1):
        seeded = {
            **payload,
            "event_id": f"demo-seed-{payload['shipment_ref']}",
            "status": "on_time",
            "delay_hours": 2,
            "updated_at": f"2026-04-23T00:{index:02d}:00+00:00",
        }
        ingest_event(db, "customs", seeded)


def get_active_shipments(db: Session) -> list[dict[str, Any]]:
    ensure_demo_shipments(db)
    snapshots = list(db.scalars(select(ShipmentSnapshot)).all())
    active: list[dict[str, Any]] = []
    for snapshot in snapshots:
        feature_vector = (
            snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
        )
        route = feature_vector.get("current_route")
        if not isinstance(route, list):
            origin = feature_vector.get("origin_port")
            destination = feature_vector.get("destination_port")
            route = [port for port in (origin, destination) if port]
        if route:
            active.append(
                {
                    "id": snapshot.shipment_key,
                    "route": route,
                    "feature_vector": feature_vector,
                }
            )
    return active


def _apply_disruption_to_shipments(
    db: Session,
    event: DisturbanceEvent,
    tick: int,
) -> None:
    for shipment_id in event.affected_shipment_ids:
        snapshot = db.scalar(
            select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == shipment_id)
        )
        if snapshot is None:
            continue
        feature_vector = (
            snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}
        )
        payload = {
            **feature_vector,
            "event_id": f"wargame-{tick}-{shipment_id}-{event.event_type}",
            "shipment_ref": shipment_id,
            "status": "delayed" if event.severity >= 0.45 else "inspection",
            "delay_hours": max(12, round(event.severity * 84)),
            "impact_score": event.severity,
            "affected_port": event.affected_port,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        ingest_event(db, "customs", payload)


def _log_wargame_event(
    db: Session,
    session: WargameSession,
    actor: str,
    event_type: str,
    affected_port: str | None,
    severity: float,
    affected_shipment_ids: list[str],
    potential_loss_usd: float,
    roi_defended_usd: float,
    payload: dict[str, Any],
) -> WargameEvent:
    record = WargameEvent(
        session_id=session.id,
        actor=actor,
        event_type=event_type,
        affected_port=affected_port,
        severity=severity,
        affected_shipment_ids=affected_shipment_ids,
        potential_loss_usd=potential_loss_usd,
        roi_defended_usd=roi_defended_usd,
        payload=payload,
    )
    db.add(record)
    db.flush()
    broadcaster.publish(
        "wargame_tick",
        {
            "session_id": session.id,
            "actor": actor,
            "event_type": event_type,
            "affected_port": affected_port,
            "severity": severity,
            "affected_shipment_ids": affected_shipment_ids,
            "potential_loss_usd": potential_loss_usd,
            "roi_defended_usd": roi_defended_usd,
        },
    )
    return record


def run_wargame(
    db: Session,
    duration_seconds: int = 600,
    tick_seconds: int | None = None,
) -> WargameSession:
    tick_seconds = tick_seconds or settings.wargame_tick_seconds
    tick_count = max(8, duration_seconds // max(1, tick_seconds))
    ensure_demo_shipments(db)
    session = WargameSession(status="running")
    db.add(session)
    db.flush()

    disturber = MonteCarloDisturber(intensity=settings.wargame_disturber_intensity)
    for tick in range(tick_count):
        active_shipments = get_active_shipments(db)
        event = disturber.generate_event(active_shipments)
        _apply_disruption_to_shipments(db, event, tick=tick)
        session.disturber_events_fired += 1
        _log_wargame_event(
            db,
            session=session,
            actor="disturber",
            event_type=event.event_type,
            affected_port=event.affected_port,
            severity=event.severity,
            affected_shipment_ids=event.affected_shipment_ids,
            potential_loss_usd=event.potential_loss_usd,
            roi_defended_usd=0.0,
            payload=event.__dict__,
        )

        per_shipment_loss = event.potential_loss_usd / max(1, len(event.affected_shipment_ids))
        for shipment_id in event.affected_shipment_ids:
            state = run_agent_for_shipment(
                db,
                shipment_key=shipment_id,
                roi_context_usd=per_shipment_loss,
                replay_data={"wargame_session_id": session.id, "disturber_event": event.__dict__},
            )
            roi_defended = float(state.get("roi_defended_usd", 0.0))
            session.healer_actions_taken += 1
            session.total_roi_defended_usd += roi_defended
            _log_wargame_event(
                db,
                session=session,
                actor="healer",
                event_type=str(state.get("action_taken")),
                affected_port=event.affected_port,
                severity=event.severity,
                affected_shipment_ids=[shipment_id],
                potential_loss_usd=per_shipment_loss,
                roi_defended_usd=roi_defended,
                payload=dict(state),
            )

    session.status = "complete"
    session.ended_at = datetime.now(timezone.utc)
    db.add(session)
    db.flush()
    metrics.increment("wargame_sessions_completed_total")
    metrics.increment("wargame_roi_defended_usd", session.total_roi_defended_usd)
    return session


def stop_wargame(db: Session, session_id: int) -> WargameSession | None:
    session = db.get(WargameSession, session_id)
    if session is None:
        return None
    if session.status == "running":
        session.status = "stopped"
        session.ended_at = datetime.now(timezone.utc)
        db.add(session)
        db.flush()
    return session


def get_wargame_session(db: Session, session_id: int) -> WargameSession | None:
    return db.get(WargameSession, session_id)


def list_wargame_events(db: Session, session_id: int) -> list[WargameEvent]:
    query = (
        select(WargameEvent)
        .where(WargameEvent.session_id == session_id)
        .order_by(WargameEvent.created_at, WargameEvent.id)
    )
    return list(db.scalars(query).all())


def list_wargame_sessions(db: Session, limit: int = 20) -> list[WargameSession]:
    query = select(WargameSession).order_by(
        desc(WargameSession.started_at),
        desc(WargameSession.id),
    ).limit(limit)
    return list(db.scalars(query).all())
