from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any

SUPPORTED_SOURCES = {"ais", "weather", "customs", "tariff", "news"}


@dataclass
class CanonicalEvent:
    source: str
    source_event_id: str | None
    event_type: str
    entity_id: str | None
    severity: float
    occurred_at: datetime
    dedupe_key: str
    payload: dict[str, Any]


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            pass

    return datetime.now(UTC)


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _dedupe_key(
    source: str,
    source_event_id: str | None,
    event_type: str,
    entity_id: str | None,
    occurred_at: datetime,
    payload: dict[str, Any],
) -> str:
    basis = {
        "source": source,
        "source_event_id": source_event_id,
        "event_type": event_type,
        "entity_id": entity_id,
        "occurred_at": occurred_at.isoformat(),
        "payload": payload,
    }
    serialized = json.dumps(basis, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _normalize_ais(payload: dict[str, Any]) -> tuple[str | None, str, str | None, float, datetime]:
    source_event_id = payload.get("event_id")
    entity_id = str(payload.get("mmsi")) if payload.get("mmsi") is not None else None
    event_type = "vessel_position_update"
    speed_knots = _as_float(payload.get("speed_knots"), 0.0)
    severity = _clamp(speed_knots / 25.0)
    occurred_at = _parse_timestamp(payload.get("timestamp"))
    return source_event_id, event_type, entity_id, severity, occurred_at


def _normalize_weather(payload: dict[str, Any]) -> tuple[str | None, str, str | None, float, datetime]:
    source_event_id = payload.get("event_id")
    entity_id = payload.get("port_code")
    event_type = "weather_alert"
    severity = _clamp(_as_float(payload.get("severity_index"), 0.0))
    occurred_at = _parse_timestamp(payload.get("observed_at"))
    return source_event_id, event_type, entity_id, severity, occurred_at


def _normalize_customs(payload: dict[str, Any]) -> tuple[str | None, str, str | None, float, datetime]:
    source_event_id = payload.get("event_id")
    entity_id = payload.get("shipment_ref")
    event_type = "customs_status"
    delay_hours = _as_float(payload.get("delay_hours"), 0.0)
    severity = _clamp(delay_hours / 48.0)
    occurred_at = _parse_timestamp(payload.get("updated_at"))
    return source_event_id, event_type, entity_id, severity, occurred_at


def _normalize_tariff(payload: dict[str, Any]) -> tuple[str | None, str, str | None, float, datetime]:
    source_event_id = payload.get("event_id")
    entity_id = payload.get("shipment_ref")
    event_type = "tariff_update"
    tariff_percent = _as_float(payload.get("tariff_percent"), 0.0)
    severity = _clamp(tariff_percent / 100.0)
    occurred_at = _parse_timestamp(payload.get("effective_from"))
    return source_event_id, event_type, entity_id, severity, occurred_at


def _normalize_news(payload: dict[str, Any]) -> tuple[str | None, str, str | None, float, datetime]:
    source_event_id = payload.get("event_id")
    entity_id = payload.get("region")
    event_type = "news_signal"
    severity = _clamp(_as_float(payload.get("impact_score"), 0.0))
    occurred_at = _parse_timestamp(payload.get("published_at"))
    return source_event_id, event_type, entity_id, severity, occurred_at


def normalize_event(source: str, payload: dict[str, Any]) -> CanonicalEvent:
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    if source == "ais":
        source_event_id, event_type, entity_id, severity, occurred_at = _normalize_ais(payload)
    elif source == "weather":
        source_event_id, event_type, entity_id, severity, occurred_at = _normalize_weather(payload)
    elif source == "customs":
        source_event_id, event_type, entity_id, severity, occurred_at = _normalize_customs(payload)
    elif source == "tariff":
        source_event_id, event_type, entity_id, severity, occurred_at = _normalize_tariff(payload)
    else:
        source_event_id, event_type, entity_id, severity, occurred_at = _normalize_news(payload)

    dedupe_key = _dedupe_key(
        source=source,
        source_event_id=source_event_id,
        event_type=event_type,
        entity_id=entity_id,
        occurred_at=occurred_at,
        payload=payload,
    )

    return CanonicalEvent(
        source=source,
        source_event_id=source_event_id,
        event_type=event_type,
        entity_id=entity_id,
        severity=severity,
        occurred_at=occurred_at,
        dedupe_key=dedupe_key,
        payload=payload,
    )
