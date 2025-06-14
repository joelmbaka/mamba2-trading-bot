"""Trader client that loads user strategies and routes calls to broker."""

from importlib import import_module
from types import ModuleType
from typing import Any

from mamba2.strategy.base import Strategy

class TraderClient:
    def __init__(self, broker: Any):
        self.broker = broker
        self.strategy: Strategy | None = None

    def load_strategy(self, dotted_path: str) -> None:
        module: ModuleType = import_module(dotted_path)
        # expecting `StrategyImpl` in module
        cls: type[Strategy] = getattr(module, "StrategyImpl")
        self.strategy = cls()

    def run(self):
        if not self.strategy:
            raise RuntimeError("Strategy not loaded")
        market = self.broker  # simplistic pass-through
        self.strategy.evaluate(market)
