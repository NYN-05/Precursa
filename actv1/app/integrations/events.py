import logging
from typing import Any
from .base import BaseAdapter

logger = logging.getLogger(__name__)

class EventsAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        try:
            # Placeholder for external events (customs delays, news)
            return self._mock_data()
        except Exception as exc:
            logger.warning("Events API failed for %s: %s. Falling back to mock.", shipment_key, exc)
            return self._mock_data()

    def _mock_data(self) -> dict[str, float]:
        # customs_delay (0-1), geo_risk (0-1), trends
        return {
            "customs_delay": 0.15,
            "geo_risk": 0.1,
            "trend_congestion": 0.25,
            "trend_delay": 0.2,
            "route_variability": 0.12
        }
