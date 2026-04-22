from abc import ABC, abstractmethod
from typing import Any

class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self, shipment_key: str, feature_vector: dict[str, Any]) -> dict[str, float]:
        pass

    @abstractmethod
    def _mock_data(self) -> dict[str, float]:
        pass
