from uuid import uuid4

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


def _ingest_customs_event(
    client,
    headers: dict[str, str],
    shipment_ref: str,
    event_id: str,
    status: str,
    delay_hours: int,
) -> None:
    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={
            "source": "customs",
            "payload": {
                "event_id": event_id,
                "shipment_ref": shipment_ref,
                "port_code": "SGSIN",
                "status": status,
                "delay_hours": delay_hours,
                "updated_at": "2026-04-22T12:00:00+00:00",
            },
        },
    )
    assert response.status_code == 200


def test_score_shipment_returns_dri_and_top_factors(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_customs_event(
        client,
        headers,
        shipment_ref="SHP-4001",
        event_id="risk-score-1a",
        status="inspection",
        delay_hours=8,
    )
    _ingest_customs_event(
        client,
        headers,
        shipment_ref="SHP-4001",
        event_id="risk-score-1b",
        status="delayed",
        delay_hours=28,
    )

    response = client.get("/api/v1/risk/shipments/SHP-4001?top_k=5", headers=headers)

    assert response.status_code == 200
    payload = response.json()

    assert payload["shipment_key"] == "SHP-4001"
    assert isinstance(payload["dri"], int)
    assert 0 <= payload["dri"] <= 100
    assert 0.0 <= payload["xgboost_score"] <= 1.0
    assert 0.0 <= payload["anomaly_score"] <= 1.0
    assert payload["model_version"] == "chunk4-v1"

    factors = payload["top_factors"]
    assert 1 <= len(factors) <= 5

    magnitudes = [abs(factor["shap_value"]) for factor in factors]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_score_shipment_is_repeatable_for_same_snapshot(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_customs_event(
        client,
        headers,
        shipment_ref="SHP-4002",
        event_id="risk-score-2a",
        status="delayed",
        delay_hours=18,
    )

    first = client.get("/api/v1/risk/shipments/SHP-4002?top_k=4", headers=headers)
    second = client.get("/api/v1/risk/shipments/SHP-4002?top_k=4", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["dri"] == second_payload["dri"]
    assert first_payload["top_factors"] == second_payload["top_factors"]


def test_score_shipment_returns_404_for_missing_snapshot(client, db_session):
    headers = _auth_headers(client, db_session)

    response = client.get("/api/v1/risk/shipments/does-not-exist", headers=headers)

    assert response.status_code == 404
    assert "Shipment snapshot not found" in response.json()["detail"]


def test_score_shipments_batch_endpoint(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_customs_event(
        client,
        headers,
        shipment_ref="SHP-4003",
        event_id="risk-score-3a",
        status="inspection",
        delay_hours=6,
    )
    _ingest_customs_event(
        client,
        headers,
        shipment_ref="SHP-4004",
        event_id="risk-score-4a",
        status="delayed",
        delay_hours=32,
    )

    response = client.get("/api/v1/risk/shipments?limit=20&top_k=3", headers=headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 2

    keyed = {row["shipment_key"]: row for row in rows}
    assert "SHP-4003" in keyed
    assert "SHP-4004" in keyed

    for row in keyed.values():
        assert isinstance(row["dri"], int)
        assert 0 <= row["dri"] <= 100
        assert len(row["top_factors"]) <= 3
