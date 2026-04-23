from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .resilience import seeded_choice, seeded_sample


WEATHER_PORTS = [
    ("Singapore Strait", 1.2644, 103.8200),
    ("Port Klang", 3.0000, 101.4000),
    ("Mumbai", 18.9220, 72.8347),
    ("Colombo", 6.9271, 79.8612),
    ("Chennai", 13.0827, 80.2707),
    ("Suez", 30.0444, 32.5498),
    ("Rotterdam", 51.9244, 4.4777),
    ("Hamburg", 53.5511, 9.9937),
    ("Antwerp", 51.2194, 4.4025),
    ("Busan", 35.1796, 129.0756),
    ("Shanghai", 31.2304, 121.4737),
    ("Hong Kong", 22.3193, 114.1694),
    ("Los Angeles", 33.7405, -118.2775),
    ("Felixstowe", 51.9542, 1.3511),
    ("Jebel Ali", 24.9857, 55.0272),
    ("Manila", 14.5995, 120.9842),
    ("Dubai", 25.2048, 55.2708),
    ("Durban", -29.8587, 31.0218),
    ("Valencia", 39.4699, -0.3763),
    ("Savannah", 32.0809, -81.0912),
]

WEATHER_CONDITIONS = [
    "clear_skies",
    "light_breeze",
    "coastal_fog",
    "moderate_wind",
    "squall_line",
    "heavy_rain",
    "thunderstorm",
    "cyclone_watch",
    "port_mist",
    "rough_sea",
]

NEWS_HEADLINES = [
    "Port labor negotiations raise congestion risk",
    "Shipping lane inspection slows cargo throughput",
    "Customs backlog delays outbound containers",
    "Severe weather warning impacts maritime scheduling",
    "Regional fuel costs increase carrier pressure",
    "Harbor maintenance temporarily reduces berth capacity",
    "Rail disruption pushes more freight to the port",
    "Canal traffic slowdown affects vessel arrival times",
    "Dockside equipment outage causes handling delays",
    "Regulatory update adds paperwork for cross-border shipments",
]

AIS_SHIP_TYPES = [
    "container",
    "bulk carrier",
    "ro-ro",
    "tanker",
    "feeder",
    "reefer",
]

AIS_FLAGS = [
    "SG",
    "IN",
    "CN",
    "HK",
    "DE",
    "NL",
    "US",
    "GB",
    "AE",
    "FR",
]


@dataclass(frozen=True)
class WeatherFallbackRecord:
    port_name: str
    lat: float
    lon: float
    condition: str
    wind_speed_mps: float
    wind_gust_mps: float
    weather_severity: float


@dataclass(frozen=True)
class NewsFallbackRecord:
    headline: str
    port_name: str
    origin_port: str
    destination_port: str
    total_results: int
    geo_risk: float
    article_count: int


@dataclass(frozen=True)
class AISFallbackRecord:
    vessel_name: str
    mmsi: int
    port_name: str
    vessel_type: str
    flag: str
    vessel_speed: float
    route_deviation: float
    ais_anomaly: float


def _weather_severity_from_wind(wind_speed: float, gust: float) -> float:
    return round(max(min(1.0, wind_speed / 20.0), min(1.0, gust / 30.0)), 3)


WEATHER_FALLBACKS: list[dict[str, Any]] = []
for index in range(100):
    port_name, lat, lon = WEATHER_PORTS[index % len(WEATHER_PORTS)]
    condition = WEATHER_CONDITIONS[index % len(WEATHER_CONDITIONS)]
    wind_speed = round(2.5 + ((index * 3.1) % 18.0), 1)
    wind_gust = round(wind_speed + 4.0 + ((index * 1.7) % 12.0), 1)
    WEATHER_FALLBACKS.append(
        {
            "weather_severity": _weather_severity_from_wind(wind_speed, wind_gust),
            "weather": _weather_severity_from_wind(wind_speed, wind_gust),
            "port_name": port_name,
            "lat": lat,
            "lon": lon,
            "condition": condition,
            "wind_speed_mps": wind_speed,
            "wind_gust_mps": wind_gust,
            "source": "weather_fallback",
        }
    )


NEWS_FALLBACKS: list[dict[str, Any]] = []
for index in range(100):
    origin_port, _, _ = WEATHER_PORTS[index % len(WEATHER_PORTS)]
    destination_port, _, _ = WEATHER_PORTS[(index + 5) % len(WEATHER_PORTS)]
    total_results = 1 + (index % 12)
    geo_risk = round(min(1.0, total_results / 10.0), 3)
    NEWS_FALLBACKS.append(
        {
            "headline": f"{NEWS_HEADLINES[index % len(NEWS_HEADLINES)]} near {origin_port}",
            "port_name": origin_port,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "total_results": total_results,
            "geo_risk": geo_risk,
            "article_count": total_results,
            "source": "news_fallback",
        }
    )


AIS_FALLBACKS: list[dict[str, Any]] = []
for index in range(200):
    port_name, _, _ = WEATHER_PORTS[index % len(WEATHER_PORTS)]
    vessel_type = AIS_SHIP_TYPES[index % len(AIS_SHIP_TYPES)]
    flag = AIS_FLAGS[index % len(AIS_FLAGS)]
    vessel_speed = round(0.3 + ((index * 0.11) % 0.7), 3)
    route_deviation = round(((index * 0.07) % 0.2), 3)
    ais_anomaly = round(((index * 0.05) % 0.18), 3)
    AIS_FALLBACKS.append(
        {
            "vessel_name": f"M/V Horizon {index + 1:03d}",
            "mmsi": 200000000 + index,
            "port_name": port_name,
            "vessel_type": vessel_type,
            "flag": flag,
            "vessel_speed": vessel_speed,
            "route_deviation": route_deviation,
            "ais_anomaly": ais_anomaly,
            "source": "ais_fallback",
        }
    )


def get_weather_fallback(shipment_key: str, port_name: str) -> dict[str, Any]:
    sample = seeded_choice(WEATHER_FALLBACKS, shipment_key, port_name)
    return dict(sample)


def get_weather_fallback_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in WEATHER_FALLBACKS]


def get_news_fallback(shipment_key: str, origin_port: str, destination_port: str) -> dict[str, Any]:
    sample = seeded_choice(NEWS_FALLBACKS, shipment_key, origin_port, destination_port)
    return dict(sample)


def get_news_fallback_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in NEWS_FALLBACKS]


def get_ais_fallback(shipment_key: str, port_name: str) -> dict[str, Any]:
    sample = seeded_choice(AIS_FALLBACKS, shipment_key, port_name)
    return dict(sample)


def get_ais_fallback_catalog(sample_size: int = 200) -> list[dict[str, Any]]:
    return [dict(item) for item in seeded_sample(AIS_FALLBACKS, sample_size, "ais_catalog")]
