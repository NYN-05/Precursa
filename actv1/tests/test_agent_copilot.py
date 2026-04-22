from uuid import uuid4

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import AgentAction, NotificationRecord, Role, RouteRecord, User


def _auth_headers(client, db_session, role_name: str = "admin") -> dict[str, str]:
    role = db_session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name)
        db_session.add(role)
        db_session.flush()

    username = f"{role_name}-{uuid4().hex[:8]}"
    user = User(
        username=username,
        hashed_password=get_password_hash("secret123"),
        is_active=True,
    )
    user.roles = [role]
    db_session.add(user)
    db_session.commit()

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _ingest_red_shipment(client, headers: dict[str, str], shipment_key: str) -> None:
    response = client.post(
        "/api/v1/ingestion/events",
        headers=headers,
        json={
            "source": "customs",
            "payload": {
                "event_id": f"agent-red-{shipment_key}",
                "shipment_ref": shipment_key,
                "origin_port": "Mumbai",
                "destination_port": "Rotterdam",
                "origin_country": "IN",
                "destination_country": "NL",
                "cargo_type": "Electronics",
                "cargo_value_usd": 100000,
                "weight_kg": 10000,
                "sla_hours": 300,
                "status": "blocked",
                "delay_hours": 72,
                "impact_score": 1.0,
                "updated_at": "2026-04-23T10:00:00+00:00",
            },
        },
    )
    assert response.status_code == 200


def test_red_alert_agent_reroutes_logs_and_notifies(client, db_session):
    headers = _auth_headers(client, db_session)
    shipment_key = f"SHP-AGENT-{uuid4().hex[:6]}"
    _ingest_red_shipment(client, headers, shipment_key)

    response = client.post(f"/api/v1/agent/run/{shipment_key}", headers=headers)

    assert response.status_code == 200
    state = response.json()
    assert state["action_taken"] == "reroute"
    assert state["selected_route"] is not None
    assert state["route_selected_id"] is not None
    assert state["copilot_explanation"]

    action = db_session.scalar(
        select(AgentAction).where(AgentAction.shipment_key == shipment_key)
    )
    assert action is not None
    assert action.action_type == "reroute"

    selected_route = db_session.scalar(
        select(RouteRecord).where(
            RouteRecord.shipment_key == shipment_key,
            RouteRecord.selected.is_(True),
        )
    )
    assert selected_route is not None

    notification = db_session.scalar(
        select(NotificationRecord).where(NotificationRecord.shipment_key == shipment_key)
    )
    assert notification is not None
    assert notification.status == "sent"


def test_override_blocks_autonomous_reroute(client, db_session):
    headers = _auth_headers(client, db_session)
    shipment_key = f"SHP-OVERRIDE-{uuid4().hex[:6]}"
    _ingest_red_shipment(client, headers, shipment_key)

    override = client.post(
        f"/api/v1/agent/override/{shipment_key}",
        headers=headers,
        json={"reason": "manual carrier negotiation", "expires_minutes": 15},
    )
    assert override.status_code == 200

    response = client.post(f"/api/v1/agent/run/{shipment_key}", headers=headers)

    assert response.status_code == 200
    state = response.json()
    assert state["action_taken"] == "override_blocked"
    assert state["ops_override_active"] is True
    assert state["selected_route"] is None


def test_copilot_answer_is_grounded_and_does_not_invent_carbon(client, db_session):
    headers = _auth_headers(client, db_session)
    shipment_key = f"SHP-COPILOT-{uuid4().hex[:6]}"
    _ingest_red_shipment(client, headers, shipment_key)
    run_response = client.post(f"/api/v1/agent/run/{shipment_key}", headers=headers)
    assert run_response.status_code == 200

    response = client.post(
        "/api/v1/copilot",
        headers=headers,
        json={
            "shipment_key": shipment_key,
            "question": "Why was this route chosen, and was carbon the reason?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded_on"]
    assert "carbon" not in payload["answer"].lower()


def test_what_if_simulation_uses_existing_route_and_risk_layers(client, db_session):
    headers = _auth_headers(client, db_session)
    shipment_key = f"SHP-WHATIF-{uuid4().hex[:6]}"
    _ingest_red_shipment(client, headers, shipment_key)

    response = client.post(
        "/api/v1/copilot/what-if",
        headers=headers,
        json={
            "shipment_key": shipment_key,
            "scenario": {"blocked_ports": ["Suez"], "delay_delta_hours": 12},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["projected_dri"], int)
    assert 0 <= payload["projected_dri"] <= 100
    assert "Projected DRI" in payload["explanation"]
