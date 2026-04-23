import logging
import requests
from typing import Any
from .base import BaseAdapter
from .fallback_data import get_news_fallback, get_news_fallback_catalog
from .resilience import SlidingWindowRateLimiter, TimedCache
from app.core.config import settings

logger = logging.getLogger(__name__)

NEWS_CACHE = TimedCache(ttl_seconds=1800)
NEWS_RATE_LIMITER = SlidingWindowRateLimiter(max_per_second=3, max_per_hour=25, max_per_day=500)

class NewsAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        if settings.news_api_key:
            try:
                # Query NewsAPI for disruptions related to the specific ports in this shipment
                origin = fv.get("origin_port", "Singapore")
                dest = fv.get("destination_port", "Rotterdam")

                cache_key = f"{origin}:{dest}"
                cached = NEWS_CACHE.get(cache_key)
                if cached is not None:
                    logger.info("NewsAPI cache hit for %s: %s/%s", shipment_key, origin, dest)
                    return cached

                if not NEWS_RATE_LIMITER.allow():
                    logger.warning("NewsAPI rate limit reached for %s (%s/%s), using fallback catalog", shipment_key, origin, dest)
                    return get_news_fallback(shipment_key, origin, dest)
                
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
                    result = {"geo_risk": risk, "news_article_count": float(total_results)}
                    NEWS_CACHE.set(cache_key, result)
                    return result
                else:
                    logger.warning("NewsAPI returned %d: %s", res.status_code, res.text)
            except Exception as exc:
                logger.warning("NewsAPI failed: %s", exc)

        return get_news_fallback(shipment_key, fv.get("origin_port", "Singapore"), fv.get("destination_port", "Rotterdam"))

    def _mock_data(self) -> dict[str, float]:
        return {"geo_risk": 0.1, "news_article_count": 0.0, "source": "news_fallback"}
