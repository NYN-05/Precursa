from typing import Any
import logging
from .weather import WeatherAdapter
from .ais import AISAdapter
from .news import NewsAdapter
from .port import PortAdapter

logger = logging.getLogger(__name__)

class IntegrationFactory:
    def __init__(self):
        self.weather = WeatherAdapter()
        self.ais = AISAdapter()
        self.news = NewsAdapter()
        self.port = PortAdapter()

    def fetch_all(self, shipment_key: str, feature_vector: dict[str, Any]) -> dict[str, float]:
        """Fetch and merge all external data signals."""
        external_data = {}
        
        # 1. Weather
        external_data.update(self.weather.fetch(shipment_key, feature_vector))
        
        # 2. AIS / Vessel
        external_data.update(self.ais.fetch(shipment_key, feature_vector))
        
        # 3. News / Geo
        external_data.update(self.news.fetch(shipment_key, feature_vector))
        
        # 4. Port Congestion
        external_data.update(self.port.fetch(shipment_key, feature_vector))

        # 5. Fixed/Trend placeholders (Step 6)
        # In a real system, these would come from historic DB trends
        external_data.update({
            "carrier_reliability": 0.88,
            "customs_delay": 0.12,
            "trend_congestion": 0.22,
            "trend_delay": 0.18,
            "route_variability": 0.05
        })

        # Ensure all required keys exist and are bounded (0-1)
        required_keys = [
            "port_congestion", "weather", "carrier_reliability", 
            "customs_delay", "geo_risk", "trend_congestion", 
            "trend_delay", "route_variability"
        ]
        
        # Mapping compatibility
        if "weather_severity" in external_data and "weather" not in external_data:
            external_data["weather"] = external_data.pop("weather_severity")

        normalized_data = {}
        for key in required_keys:
            val = external_data.get(key, 0.0)
            normalized_data[key] = max(0.0, min(1.0, float(val)))

        logger.info("Integrated signals for %s: %s", shipment_key, normalized_data)
        return normalized_data

integration_factory = IntegrationFactory()
