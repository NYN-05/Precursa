from math import isclose
from uuid import uuid4

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Role, ShipmentSnapshot, User


def _create_admin_user(db_session, password: str = "secret123") -> User:
    role = db_session.scalar(select(Role).where(Role.name == "admin"))
    if role is None:
        role = Role(name="admin")
        db_session.add(role)
        db_session.flush()

    username = f"admin-{uuid4().hex[:8]}"
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    user.roles = [role]
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(client, db_session) -> dict[str, str]:
    user = _create_admin_user(db_session)
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.username, "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ingestion_updates_shipment_snapshot_and_live_cache(client, db_session):
    headers = _auth_headers(client, db_session)

    payload = {
        "event_id": "customs-snapshot-1",
        "shipment_ref": "SHP-3001",
        "port_code": "SGSIN",
        "status": "delayed",
        "delay_hours": 24,
        "updated_at": "2026-04-22T12:00:00+00:00",
    }

    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": payload},
    )

    assert response.status_code == 200
    assert response.json()["created"] is True

    snapshot = db_session.scalar(
        select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == "SHP-3001")
    )
    assert snapshot is not None
    assert snapshot.event_count == 1
    assert isclose(snapshot.avg_severity, 0.5, rel_tol=1e-6)
    assert snapshot.provisional_dri == 50
    assert snapshot.feature_vector["shipment_ref"] == "SHP-3001"

    snapshot_response = client.get("/api/v1/state/snapshots/SHP-3001", headers=headers)
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["event_count"] == 1

    cache_response = client.get("/api/v1/state/cache/SHP-3001", headers=headers)
    assert cache_response.status_code == 200
    assert cache_response.json()["cached_state"]["provisional_dri"] == 50


def test_subsequent_events_update_feature_vector_and_provisional_dri(client, db_session):
    headers = _auth_headers(client, db_session)

    first_payload = {
        "event_id": "customs-snapshot-2a",
        "shipment_ref": "SHP-3002",
        "port_code": "SGSIN",
        "status": "inspection",
        "delay_hours": 12,
        "updated_at": "2026-04-22T12:00:00+00:00",
    }
    second_payload = {
        "event_id": "customs-snapshot-2b",
        "shipment_ref": "SHP-3002",
        "port_code": "SGSIN",
        "status": "delayed",
        "delay_hours": 24,
        "updated_at": "2026-04-22T13:00:00+00:00",
    }

    first = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": first_payload},
    )
    second = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": second_payload},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created"] is True
    assert second.json()["created"] is True

    snapshot = db_session.scalar(
        select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == "SHP-3002")
    )
    assert snapshot is not None
    assert snapshot.event_count == 2
    assert isclose(snapshot.avg_severity, 0.375, rel_tol=1e-6)
    assert isclose(snapshot.last_severity, 0.5, rel_tol=1e-6)
    assert snapshot.provisional_dri == 44
    assert snapshot.feature_vector["event_count"] == 2


def test_state_layer_uses_fallback_key_for_non_shipment_events(client, db_session):
    headers = _auth_headers(client, db_session)

    payload = {
        "event_id": "weather-snapshot-1",
        "port_code": "DEHAM",
        "condition": "storm",
        "severity_index": 0.9,
        "observed_at": "2026-04-22T14:00:00+00:00",
    }

    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "weather", "payload": payload},
    )

    assert response.status_code == 200
    assert response.json()["created"] is True

    snapshot = db_session.scalar(
        select(ShipmentSnapshot).where(ShipmentSnapshot.shipment_key == "port:DEHAM")
    )
    assert snapshot is not None
    assert snapshot.feature_vector["port_code"] == "DEHAM"

    snapshot_response = client.get("/api/v1/state/snapshots/port:DEHAM", headers=headers)
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["shipment_key"] == "port:DEHAM"
