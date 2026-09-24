"""Deterministic orchestration for replaying the current strategy offline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from .broker import HistoricalBroker
from .feed import ReplayFeed


class BacktestBrokerAdapter:
    """Expose a strategy-compatible broker without changing fill timing.

    ``HistoricalBroker`` returns MT5's queued-order code ``10008``. The
    current strategy only treats ``0``/``10009`` as accepted, so this adapter
    translates only the response code to ``0``. The underlying order remains
    pending and is still filled only when the runner advances to the next
    available M1 candle; no future price is included in the response.
    """

    def __init__(self, broker: HistoricalBroker):
        self.broker = broker
        self.accepted_responses: list[dict[str, Any]] = []

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self.broker.order_send(request)
        if response.get("retcode") == 10008:
            response = {**response, "retcode": 0, "comment": "accepted; pending next M1 candle"}
        self.accepted_responses.append(response.copy())
        return response

    def __getattr__(self, name: str):
        return getattr(self.broker, name)


@dataclass
class BacktestResult:
    """Observable replay results without performance conclusions."""

    evaluations: int = 0
    timestamps: list[Any] = field(default_factory=list)
    accepted_orders: list[dict[str, Any]] = field(default_factory=list)


class BacktestRunner:
    """Advance the replay clock, then evaluate one strategy step."""

    def __init__(
        self,
        feed: ReplayFeed,
        broker: HistoricalBroker,
        strategy: Any,
        *,
        position_manager: Any | None = None,
        rate_fetcher: Any | None = None,
    ):
        self.feed = feed
        self.broker = broker
        self.strategy = strategy
        self.position_manager = position_manager
        self.rate_fetcher = rate_fetcher or feed
        self.strategy_broker = BacktestBrokerAdapter(broker)

    def market_context(self) -> dict[str, Any]:
        context = {
            "broker": self.strategy_broker,
            "rate_fetcher": self.rate_fetcher,
        }
        if self.position_manager is not None:
            context["position_manager"] = self.position_manager
        return context

    async def run_async(self, *, max_steps: int | None = None) -> BacktestResult:
        result = BacktestResult()
        while not self.feed.finished and (max_steps is None or result.evaluations < max_steps):
            timestamp = self.broker.advance()
            await self.strategy.evaluate(self.market_context())
            self.broker.settle_pending_orders()
            result.evaluations += 1
            result.timestamps.append(timestamp)
        result.accepted_orders = list(self.strategy_broker.accepted_responses)
        return result

    def run(self, *, max_steps: int | None = None) -> BacktestResult:
        """Run without wall-clock sleeps or MT5 initialization."""
        return asyncio.run(self.run_async(max_steps=max_steps))
