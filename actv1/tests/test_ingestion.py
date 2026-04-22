from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Role, User


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


def test_ingest_mock_events_creates_canonical_records(client, db_session):
    headers = _auth_headers(client, db_session)

    response = client.post(
        "/api/v1/ingestion/mock/ais?count=2",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["event"]["source"] == "ais" for item in data)

    list_response = client.get("/api/v1/ingestion/events?source=ais", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 2


@pytest.mark.parametrize("source", ["ais", "weather", "customs", "tariff", "news"])
def test_ingest_mock_events_supports_all_sources(client, db_session, source: str):
    headers = _auth_headers(client, db_session)

    response = client.post(
        f"/api/v1/ingestion/mock/{source}?count=1",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event"]["source"] == source


def test_dedupe_logic_prevents_duplicate_insert(client, db_session):
    headers = _auth_headers(client, db_session)

    payload = {
        "event_id": "customs-fixed-id",
        "shipment_ref": "SHP-2001",
        "port_code": "SGSIN",
        "status": "delayed",
        "delay_hours": 12,
        "updated_at": "2026-04-22T12:00:00+00:00",
    }

    first = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": payload},
    )
    second = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": payload},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["event"]["id"] == second.json()["event"]["id"]
    assert first.json()["event"]["dedupe_key"] == second.json()["event"]["dedupe_key"]


def test_timestamp_fallback_when_source_timestamp_missing(client, db_session):
    headers = _auth_headers(client, db_session)

    payload = {
        "event_id": "news-no-timestamp",
        "headline": "Strike expected at major port",
        "region": "DEHAM",
        "impact_score": 0.77,
    }

    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "news", "payload": payload},
    )

    assert response.status_code == 200
    occurred_at = response.json()["event"]["occurred_at"]
    assert datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))


def test_dedupe_logic_when_source_timestamp_missing(client, db_session):
    headers = _auth_headers(client, db_session)

    payload = {
        "event_id": "news-missing-ts-fixed-id",
        "headline": "Port labor strike escalates",
        "region": "DEHAM",
        "impact_score": 0.81,
    }

    first = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "news", "payload": payload},
    )
    second = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "news", "payload": payload},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["event"]["id"] == second.json()["event"]["id"]


def test_ingestion_rejects_unsupported_source(client, db_session):
    headers = _auth_headers(client, db_session)

    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "unknown-source", "payload": {"event_id": "x"}},
    )

    assert response.status_code == 400
    assert "Unsupported source" in response.json()["detail"]
