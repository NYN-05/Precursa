from uuid import uuid4

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Role, User


def _create_role_user(db_session, role_name: str, password: str = "secret123") -> User:
    role = db_session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name)
        db_session.add(role)
        db_session.flush()

    username = f"{role_name}-{uuid4().hex[:8]}"
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


def _auth_headers(client, db_session, role_name: str = "admin") -> dict[str, str]:
    user = _create_role_user(db_session, role_name=role_name)
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.username, "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _ingest_event(client, headers: dict[str, str], payload: dict) -> None:
    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={"source": "customs", "payload": payload},
    )
    assert response.status_code == 200


def test_reroute_returns_top_feasible_routes(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_event(
        client,
        headers,
        {
            "event_id": "route-1001",
            "shipment_ref": "SHP-5001",
            "origin_port": "Mumbai",
            "destination_port": "Rotterdam",
            "origin_country": "IN",
            "destination_country": "NL",
            "sla_hours": 260,
            "max_risk_tolerance": 0.5,
            "cargo_value_usd": 80000,
            "updated_at": "2026-04-23T10:00:00+00:00",
        },
    )

    response = client.post(
        "/api/v1/routes/reroute/SHP-5001?max_paths=12&top_k=3",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["shipment_key"] == "SHP-5001"
    assert payload["solver_status"] in {"optimal", "fallback-feasible"}
    assert payload["message"] == "Feasible reroute options generated"

    top_routes = payload["top_routes"]
    assert 1 <= len(top_routes) <= 3
    assert any(route["selected_best"] is True for route in top_routes)

    scores = [route["composite_score"] for route in top_routes]
    assert scores == sorted(scores)


def test_reroute_rejects_invalid_routes_with_reasons(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_event(
        client,
        headers,
        {
            "event_id": "route-1002",
            "shipment_ref": "SHP-5002",
            "origin_port": "Mumbai",
            "destination_port": "Rotterdam",
            "origin_country": "IN",
            "destination_country": "NL",
            "sla_hours": 120,
            "temp_requirement_celsius": 4.0,
            "sanctioned_ports": ["Suez", "Jebel Ali"],
            "updated_at": "2026-04-23T10:05:00+00:00",
        },
    )

    response = client.post(
        "/api/v1/routes/reroute/SHP-5002?max_paths=12&top_k=3",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["top_routes"] == []
    assert payload["message"] == "All candidate routes were rejected by hard constraints"
    assert len(payload["rejected_routes"]) >= 1

    reason_blob = " ".join(
        " ".join(route["reasons"]) for route in payload["rejected_routes"]
    ).lower()
    assert (
        "sanctioned" in reason_blob
        or "cold-chain" in reason_blob
        or "sla" in reason_blob
    )


def test_reroute_returns_422_when_ports_missing(client, db_session):
    headers = _auth_headers(client, db_session)

    _ingest_event(
        client,
        headers,
        {
            "event_id": "route-1003",
            "shipment_ref": "SHP-5003",
            "origin_country": "IN",
            "destination_country": "NL",
            "updated_at": "2026-04-23T10:10:00+00:00",
        },
    )

    response = client.post("/api/v1/routes/reroute/SHP-5003", headers=headers)

    assert response.status_code == 422
    assert "Missing origin_port or destination_port" in response.json()["detail"]


def test_reroute_respects_role_guards(client, db_session):
    admin_headers = _auth_headers(client, db_session, role_name="admin")
    auditor_headers = _auth_headers(client, db_session, role_name="auditor")

    _ingest_event(
        client,
        admin_headers,
        {
            "event_id": "route-1004",
            "shipment_ref": "SHP-5004",
            "origin_port": "Mumbai",
            "destination_port": "Hamburg",
            "origin_country": "IN",
            "destination_country": "DE",
            "updated_at": "2026-04-23T10:15:00+00:00",
        },
    )

    response = client.post("/api/v1/routes/reroute/SHP-5004", headers=auditor_headers)
    assert response.status_code == 403
