import logging
from typing import Any
from .base import BaseAdapter

logger = logging.getLogger(__name__)

class PortAdapter(BaseAdapter):
    def fetch(self, shipment_key: str, fv: dict[str, Any]) -> dict[str, float]:
        # Simulate port congestion based on delay trends in feature vector
        delay_hours = float(fv.get("delay_hours", 0))
        
        # Normalize: if delay is > 48h, congestion is high
        congestion = min(1.0, delay_hours / 48.0)
        
        # Add a baseline of 0.2
        congestion = max(0.2, congestion)
        
        return {"port_congestion": round(congestion, 2)}

    def _mock_data(self) -> dict[str, float]:
        return {"port_congestion": 0.3}
