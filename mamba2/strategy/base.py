"""Strategy interface users must implement."""

from abc import ABC, abstractmethod
from typing import Any

class Strategy(ABC):
    @abstractmethod
    def evaluate(self, market: Any) -> None:
        """Evaluate market conditions and place / manage orders."""
        raise NotImplementedError
