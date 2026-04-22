from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ingestion import ingest_event
from app.services.observability import metrics

KAFKA_TOPICS = {
    "weather-events": {"producer": "weather_api", "consumer": "flink_dri_pipeline"},
    "port-congestion": {"producer": "port_feed", "consumer": "flink_dri_pipeline"},
    "shipment-positions": {"producer": "ais_api", "consumer": "flink_dri_pipeline"},
    "dri-updates": {"producer": "flink_dri_pipeline", "consumer": "risk_scorer"},
}


def streaming_status() -> dict[str, Any]:
    mode = "kafka" if settings.kafka_bootstrap_servers.strip() else "mock"
    return {
        "mode": mode,
        "mock_mode": mode == "mock",
        "kafka_bootstrap_configured": bool(settings.kafka_bootstrap_servers.strip()),
        "topics": KAFKA_TOPICS,
        "flink_window": "5-minute tumbling feature window",
    }


def run_mock_stream_tick(db: Session) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    payloads = [
        {
            "source": "weather",
            "payload": {
                "event_id": f"mock-weather-{timestamp}",
                "port_code": "Suez",
                "severity_index": 0.78,
                "condition": "storm",
                "observed_at": timestamp,
            },
        },
        {
            "source": "customs",
            "payload": {
                "event_id": f"mock-customs-{timestamp}",
                "shipment_ref": "SHP-STREAM",
                "origin_port": "Mumbai",
                "destination_port": "Rotterdam",
                "origin_country": "IN",
                "destination_country": "NL",
                "status": "delayed",
                "delay_hours": 18,
                "updated_at": timestamp,
            },
        },
    ]
    created = 0
    for item in payloads:
        _, was_created = ingest_event(db, source=item["source"], payload=item["payload"])
        if was_created:
            created += 1
    metrics.increment("mock_stream_ticks_total")
    return {"mode": "mock", "events_processed": len(payloads), "events_created": created}
