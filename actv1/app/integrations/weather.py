import logging
import requests
from typing import Any
from .base import BaseAdapter
from .fallback_data import get_weather_fallback, get_weather_fallback_catalog
from .resilience import SlidingWindowRateLimiter, TimedCache
from app.core.config import settings
from app.services.route_intelligence import PORTS
import time
import os

# ===== WEATHER CACHE =====
WEATHER_CACHE = TimedCache(ttl_seconds=900)
TOMORROW_CACHE = TimedCache(ttl_seconds=1800)
TOMORROW_RATE_LIMITER = SlidingWindowRateLimiter(max_per_second=3, max_per_hour=25, max_per_day=500)

logger = logging.getLogger(__name__)

class WeatherAdapter(BaseAdapter):
    def _cached_tomorrow_weather(self, port_name: str, now: float) -> dict[str, float] | None:
        return TOMORROW_CACHE.get(port_name)

    def _store_tomorrow_weather(self, port_name: str, result: dict[str, float], now: float) -> None:
        TOMORROW_CACHE.set(port_name, result)

    def fetch_weather_by_region(region, lat, lon):
        now = time.time()

    # ===== CACHE CHECK =====
        cached = WEATHER_CACHE.get(region)
        if cached is not None:
            return cached

        # ===== API CALL =====
        api_key = os.getenv("OPENWEATHER_API_KEY")

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

            response = requests.get(url, timeout=2)
            data = response.json()

            wind_speed = data.get("wind", {}).get("speed", 0)

            weather_severity = min(wind_speed / 20, 1.0)

            result = {
                "weather": weather_severity
            }

            # ===== SAVE CACHE =====
            WEATHER_CACHE.set(region, result)

            return result

        except Exception:
            # ===== FALLBACK =====
            return {"weather": 0.5}
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        # Try Tomorrow.io if key exists
        if settings.tomorrow_io_api_key:
            try:
                # Use current port or origin port to get coordinates
                port_name = fv.get("origin_port", "Singapore")
                port_info = PORTS.get(port_name, PORTS["Singapore"])
                lat, lon = port_info["lat"], port_info["lon"]

                cached = self._cached_tomorrow_weather(port_name, time.time())
                if cached is not None:
                    logger.info(
                        "Tomorrow.io cache hit for %s (%s): %f",
                        shipment_key,
                        port_name,
                        cached["weather_severity"],
                    )
                    return cached

                if not TOMORROW_RATE_LIMITER.allow():
                    logger.warning(
                        "Tomorrow.io rate limit reached, using fallback weather for %s (%s)",
                        shipment_key,
                        port_name,
                    )
                    return get_weather_fallback(shipment_key, port_name)

                url = f"https://api.tomorrow.io/v4/weather/realtime?location={lat},{lon}&apikey={settings.tomorrow_io_api_key}"
                headers = {"accept": "application/json"}
                
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    # tomorrow.io returns windSpeed in m/s by default
                    values = data.get("data", {}).get("values", {})
                    wind_speed = values.get("windSpeed", 0)
                    wind_gust = values.get("windGust", 0)
                    
                    # Normalize: 20m/s wind or 30m/s gust is high risk
                    severity = max(min(1.0, wind_speed / 20.0), min(1.0, wind_gust / 30.0))
                    
                    logger.info("Tomorrow.io weather for %s (%s): %f", shipment_key, port_name, severity)
                    result = {"weather_severity": severity}
                    self._store_tomorrow_weather(port_name, result, time.time())
                    return result
                else:
                    logger.warning("Tomorrow.io API returned %d: %s", res.status_code, res.text)
            except Exception as exc:
                logger.warning("Tomorrow.io failed: %s", exc)

        # Fallback to Open-Meteo (No key required)
        try:
            # Re-using coordinates logic
            port_name = fv.get("origin_port", "Singapore")
            port_info = PORTS.get(port_name, PORTS["Singapore"])
            lat, lon = port_info["lat"], port_info["lon"]
            
            res = requests.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                wind_speed = data.get("current_weather", {}).get("windspeed", 0)
                # Open-meteo usually km/h. Assume 72 km/h (20 m/s) is high risk.
                severity = min(1.0, wind_speed / 72.0)
                logger.info("Open-Meteo weather for %s (%s): %f", shipment_key, port_name, severity)
                return {"weather_severity": severity}
        except Exception as exc:
            logger.warning("Open-Meteo failed: %s", exc)

        return get_weather_fallback(shipment_key, fv.get("origin_port", "Singapore"))

    def _mock_data(self) -> dict[str, float]:
        return {"weather_severity": 0.2, "weather": 0.2, "source": "weather_fallback"}
