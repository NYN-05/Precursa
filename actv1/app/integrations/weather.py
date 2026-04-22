import logging
import requests
from typing import Any
from .base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

class WeatherAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        # Try real API if key exists
        if settings.openweather_api_key:
            try:
                # Mock location for demo (e.g. from origin_port)
                # In real scenario, use PORTS lookup from route_intelligence
                res = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid={settings.openweather_api_key}",
                    timeout=2
                )
                if res.status_code == 200:
                    data = res.json()
                    wind_speed = data.get("wind", {}).get("speed", 0)
                    # Normalize: assume 20 m/s is high risk
                    severity = min(1.0, wind_speed / 20.0)
                    logger.info("Fetched real weather for %s: %f", shipment_key, severity)
                    return {"weather_severity": severity}
            except Exception as exc:
                logger.warning("OpenWeather failed: %s", exc)

        # Fallback to Open-Meteo (No key required)
        try:
            res = requests.get(
                "https://api.open-meteo.com/v1/forecast?latitude=18.92&longitude=72.83&current_weather=true",
                timeout=2
            )
            if res.status_code == 200:
                data = res.json()
                wind_speed = data.get("current_weather", {}).get("windspeed", 0)
                # Open-meteo usually km/h. Assume 72 km/h (20 m/s) is high risk.
                severity = min(1.0, wind_speed / 72.0)
                logger.info("Fetched Open-Meteo weather for %s: %f", shipment_key, severity)
                return {"weather_severity": severity}
        except Exception as exc:
            logger.warning("Open-Meteo failed: %s", exc)

        return self._mock_data()

    def _mock_data(self) -> dict[str, float]:
        return {"weather_severity": 0.2}
