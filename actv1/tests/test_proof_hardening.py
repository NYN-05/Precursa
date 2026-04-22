from uuid import uuid4

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Role, User


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


def test_ever_given_backtest_flags_before_grounding(client, db_session):
    headers = _auth_headers(client, db_session)

    response = client.post("/api/v1/backtests/ever-given", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "ever_given_2021_suez"
    assert payload["flag_time"] is not None
    assert payload["precursa_lead_minutes"] >= 10
    assert len(payload["timeline"]) > 0


def test_wargame_runs_disturber_and_healer_loop(client, db_session):
    headers = _auth_headers(client, db_session)

    response = client.post(
        "/api/v1/wargame/start",
        headers=headers,
        json={"duration_seconds": 80, "tick_seconds": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "complete"
    assert payload["disturber_events_fired"] >= 8
    assert payload["healer_actions_taken"] >= 8
    assert payload["total_roi_defended_usd"] > 0

    history = client.get(f"/api/v1/wargame/history/{payload['id']}", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) >= payload["disturber_events_fired"]


def test_streaming_mock_mode_and_metrics_are_available(client, db_session):
    headers = _auth_headers(client, db_session)

    status_response = client.get("/api/v1/ops/streaming/status", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["mock_mode"] is True

    tick_response = client.post("/api/v1/ops/streaming/mock-tick", headers=headers)
    assert tick_response.status_code == 200
    assert tick_response.json()["events_processed"] >= 1

    metrics_response = client.get("/api/v1/ops/metrics", headers=headers)
    assert metrics_response.status_code == 200
    assert "counters" in metrics_response.json()
