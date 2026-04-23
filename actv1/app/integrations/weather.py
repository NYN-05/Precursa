import logging
import requests
from typing import Any
from .base import BaseAdapter
from app.core.config import settings
from app.services.route_intelligence import PORTS

logger = logging.getLogger(__name__)

class WeatherAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        # Try Tomorrow.io if key exists
        if settings.tomorrow_io_api_key:
            try:
                # Use current port or origin port to get coordinates
                port_name = fv.get("origin_port", "Singapore")
                port_info = PORTS.get(port_name, PORTS["Singapore"])
                lat, lon = port_info["lat"], port_info["lon"]

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
                    return {"weather_severity": severity}
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

        return self._mock_data()

    def _mock_data(self) -> dict[str, float]:
        return {"weather_severity": 0.2}
