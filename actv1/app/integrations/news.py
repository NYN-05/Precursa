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
                # Query NewsAPI for disruptions related to the specific ports in this shipment
                origin = fv.get("origin_port", "Singapore")
                dest = fv.get("destination_port", "Rotterdam")
                
                query = f'({origin} OR {dest}) AND (port strike OR shipping disruption OR maritime congestion)'
                
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&pageSize=10&apiKey={settings.news_api_key}"
                
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    total_results = data.get("totalResults", 0)
                    
                    # Risk mapping: 0 articles = 0.0, 5+ relevant articles = high risk
                    risk = min(1.0, total_results / 5.0)
                    
                    logger.info("NewsAPI for %s: found %d relevant articles for %s/%s. Risk: %f", 
                                shipment_key, total_results, origin, dest, risk)
                    return {"geo_risk": risk}
                else:
                    logger.warning("NewsAPI returned %d: %s", res.status_code, res.text)
            except Exception as exc:
                logger.warning("NewsAPI failed: %s", exc)

        return self._mock_data()

    def _mock_data(self) -> dict[str, float]:
        return {"geo_risk": 0.1}
