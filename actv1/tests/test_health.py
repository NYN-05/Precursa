from app.api.v1 import health as health_router


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_ok(client, monkeypatch):
    async def fake_ready_ok() -> dict[str, str]:
        return {"status": "ok", "database": "ok", "redis": "ok"}

    monkeypatch.setattr(health_router, "check_readiness", fake_ready_ok)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint_degraded(client, monkeypatch):
    async def fake_ready_degraded() -> dict[str, str]:
        return {"status": "degraded", "database": "ok", "redis": "down"}

    monkeypatch.setattr(health_router, "check_readiness", fake_ready_degraded)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
