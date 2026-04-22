from datetime import UTC, datetime
from random import choice, randint, uniform
from uuid import uuid4

SOURCE_PORTS = ["SGSIN", "CNSHA", "NLRTM", "DEHAM", "USLAX"]
WEATHER_TYPES = ["storm", "high_wind", "high_wave", "cyclone_watch"]
CUSTOMS_STATUSES = ["cleared", "inspection", "delayed"]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def mock_ais_event() -> dict:
    port = choice(SOURCE_PORTS)
    return {
        "event_id": f"ais-{uuid4().hex}",
        "mmsi": str(randint(100000000, 999999999)),
        "vessel_name": f"MV-{randint(100, 999)}",
        "port_code": port,
        "lat": round(uniform(-70.0, 70.0), 5),
        "lon": round(uniform(-170.0, 170.0), 5),
        "speed_knots": round(uniform(0.0, 24.0), 2),
        "timestamp": _now_iso(),
    }


def mock_weather_event() -> dict:
    return {
        "event_id": f"weather-{uuid4().hex}",
        "port_code": choice(SOURCE_PORTS),
        "condition": choice(WEATHER_TYPES),
        "severity_index": round(uniform(0.2, 1.0), 2),
        "observed_at": _now_iso(),
    }


def mock_customs_event() -> dict:
    return {
        "event_id": f"customs-{uuid4().hex}",
        "shipment_ref": f"SHP-{randint(1000, 9999)}",
        "port_code": choice(SOURCE_PORTS),
        "status": choice(CUSTOMS_STATUSES),
        "delay_hours": randint(0, 48),
        "updated_at": _now_iso(),
    }


def mock_tariff_event() -> dict:
    return {
        "event_id": f"tariff-{uuid4().hex}",
        "shipment_ref": f"SHP-{randint(1000, 9999)}",
        "origin_country": choice(["CN", "IN", "VN", "MX", "DE"]),
        "destination_country": choice(["US", "EU", "GB", "AE"]),
        "tariff_percent": round(uniform(0.0, 45.0), 2),
        "effective_from": _now_iso(),
    }


def mock_news_event() -> dict:
    region = choice(SOURCE_PORTS)
    return {
        "event_id": f"news-{uuid4().hex}",
        "headline": f"Operational disruption reported near {region}",
        "region": region,
        "impact_score": round(uniform(0.2, 0.95), 2),
        "published_at": _now_iso(),
    }


def generate_mock_payload(source: str) -> dict:
    if source == "ais":
        return mock_ais_event()
    if source == "weather":
        return mock_weather_event()
    if source == "customs":
        return mock_customs_event()
    if source == "tariff":
        return mock_tariff_event()
    if source == "news":
        return mock_news_event()

    raise ValueError(f"Unsupported source: {source}")
