import logging
import requests
from typing import Any
from .base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

class NewsAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        if settings.news_api_key:
            try:
                # Query NewsAPI for shipping disruptions
                res = requests.get(
                    f"https://newsapi.org/v2/everything?q=shipping+disruption+OR+port+strike&apiKey={settings.news_api_key}",
                    timeout=2
                )
                if res.status_code == 200:
                    data = res.json()
                    total_results = data.get("totalResults", 0)
                    # Normalize: more than 50 recent articles is high risk
                    risk = min(1.0, total_results / 50.0)
                    logger.info("NewsAPI results for %s: %d articles. Geo Risk: %f", shipment_key, total_results, risk)
                    return {"geo_risk": risk}
            except Exception as exc:
                logger.warning("NewsAPI failed: %s", exc)

        return self._mock_data()

    def _mock_data(self) -> dict[str, float]:
        return {"geo_risk": 0.1}
