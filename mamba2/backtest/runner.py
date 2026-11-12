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
        self.accepted_order_records: list[dict[str, Any]] = []

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self.broker.order_send(request)
        if response.get("retcode") == 10008:
            response = {**response, "retcode": 0, "comment": "accepted; pending next M1 candle"}
        if response.get("retcode") == 0:
            self.accepted_responses.append(response.copy())
            self.accepted_order_records.append(
                {
                    "symbol": request.get("symbol"),
                    "response": response.copy(),
                }
            )
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
        atr_manager: Any | None = None,
        rate_fetcher: Any | None = None,
    ):
        self.feed = feed
        self.broker = broker
        self.strategy = strategy
        self.position_manager = position_manager
        self.atr_manager = (
            atr_manager
            if atr_manager is not None
            else getattr(position_manager, "atr_manager", None)
        )
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

    async def _strategy_is_blocked_by_open_position(self) -> bool:
        """Mirror live one-position semantics, including queued replay fills.

        MT5 market orders are normally accepted/executed synchronously from the
        strategy's perspective. HistoricalBroker may need to queue an accepted
        order until the next symbol execution bar exists. While that synthetic
        queue is pending, treating the symbol as free would allow duplicate
        submissions that cannot occur in the live path.
        """
        if self.position_manager is None:
            return False

        symbol = getattr(self.strategy, "symbol", None)
        if not symbol:
            return False

        if await self.broker.positions_get(symbol=symbol):
            return True

        return any(
            order.get("request", {}).get("symbol") == symbol
            for order in self.broker.pending_orders
        )

    async def run_async(self, *, max_steps: int | None = None) -> BacktestResult:
        result = BacktestResult()
        while not self.feed.finished and (
            max_steps is None or result.evaluations < max_steps
        ):
            timestamp = self.broker.advance()

            if self.atr_manager is not None:
                self.atr_manager.refresh_once()

            if not await self._strategy_is_blocked_by_open_position():
                await self.strategy.evaluate(self.market_context())

            self.broker.settle_pending_orders()

            if self.position_manager is not None:
                await self.position_manager.update_once()

            result.evaluations += 1
            result.timestamps.append(timestamp)

        result.accepted_orders = list(self.strategy_broker.accepted_responses)
        return result

    def run(self, *, max_steps: int | None = None) -> BacktestResult:
        """Run without wall-clock sleeps or MT5 initialization."""
        return asyncio.run(self.run_async(max_steps=max_steps))



@dataclass
class PortfolioBacktestResult:
    """Observable state from one shared-account multi-symbol replay."""

    evaluations: int = 0
    timestamps: list[Any] = field(default_factory=list)
    per_symbol_evaluations: dict[str, int] = field(default_factory=dict)
    accepted_orders_by_symbol: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )
    open_positions_by_symbol: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )
    pending_orders_by_symbol: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )
    closed_trade_count_by_symbol: dict[str, int] = field(default_factory=dict)
    account_snapshots: list[dict[str, Any]] = field(default_factory=list)
    final_account: dict[str, Any] = field(default_factory=dict)

    @property
    def accepted_order_count(self) -> int:
        return sum(
            len(orders)
            for orders in self.accepted_orders_by_symbol.values()
        )

    @property
    def accepted_order_count_by_symbol(self) -> dict[str, int]:
        return {
            symbol: len(orders)
            for symbol, orders in self.accepted_orders_by_symbol.items()
        }


class PortfolioBacktestRunner:
    """Replay multiple symbol strategies on one shared clock and account.

    The production DayTrader evaluates configured symbols sequentially against
    one broker/account. This runner mirrors that orchestration deterministically
    without changing the existing single-strategy BacktestRunner API.
    """

    def __init__(
        self,
        feed: ReplayFeed,
        broker: HistoricalBroker,
        strategies: list[Any] | tuple[Any, ...],
        *,
        position_manager: Any | None = None,
        atr_manager: Any | None = None,
        rate_fetcher: Any | None = None,
        strategy_reporting_enabled: bool = True,
    ):
        self.feed = feed
        self.broker = broker
        self.strategies = tuple(strategies)
        if not self.strategies:
            raise ValueError("at least one strategy is required")

        symbols = [getattr(strategy, "symbol", None) for strategy in self.strategies]
        if any(not symbol for symbol in symbols):
            raise ValueError("every portfolio strategy must expose a symbol")
        if len(set(symbols)) != len(symbols):
            raise ValueError("portfolio strategy symbols must be unique")

        self.symbols = tuple(symbols)
        self.position_manager = position_manager
        self.atr_manager = (
            atr_manager
            if atr_manager is not None
            else getattr(position_manager, "atr_manager", None)
        )
        self.rate_fetcher = rate_fetcher or feed
        self.strategy_reporting_enabled = bool(strategy_reporting_enabled)
        self.strategy_broker = BacktestBrokerAdapter(broker)

    def market_context(self) -> dict[str, Any]:
        context = {
            "broker": self.strategy_broker,
            "rate_fetcher": self.rate_fetcher,
            "reporting_enabled": self.strategy_reporting_enabled,
        }
        if self.position_manager is not None:
            context["position_manager"] = self.position_manager
        return context

    async def _symbol_is_blocked(self, symbol: str) -> bool:
        if await self.broker.positions_get(symbol=symbol):
            return True
        return any(
            order.get("request", {}).get("symbol") == symbol
            for order in self.broker.pending_orders
        )

    async def _snapshot(
        self,
        result: PortfolioBacktestResult,
    ) -> None:
        result.accepted_orders_by_symbol = {
            symbol: [] for symbol in self.symbols
        }
        for record in self.strategy_broker.accepted_order_records:
            symbol = record.get("symbol")
            if symbol in result.accepted_orders_by_symbol:
                result.accepted_orders_by_symbol[symbol].append(
                    record["response"].copy()
                )

        result.open_positions_by_symbol = {
            symbol: await self.broker.positions_get(symbol=symbol)
            for symbol in self.symbols
        }

        result.pending_orders_by_symbol = {
            symbol: [
                order
                for order in self.broker.pending_orders
                if order.get("request", {}).get("symbol") == symbol
            ]
            for symbol in self.symbols
        }

        closed_counts = {symbol: 0 for symbol in self.symbols}
        for trade in self.broker.closed_trades:
            if trade.symbol in closed_counts:
                closed_counts[trade.symbol] += 1
        result.closed_trade_count_by_symbol = closed_counts
        result.final_account = self.broker.account_info().copy()

    async def run_async(
        self,
        *,
        max_steps: int | None = None,
    ) -> PortfolioBacktestResult:
        result = PortfolioBacktestResult(
            per_symbol_evaluations={
                symbol: 0 for symbol in self.symbols
            },
            accepted_orders_by_symbol={
                symbol: [] for symbol in self.symbols
            },
        )

        while not self.feed.finished and (
            max_steps is None or result.evaluations < max_steps
        ):
            timestamp = self.broker.advance()

            if self.atr_manager is not None:
                self.atr_manager.refresh_once()

            for strategy in self.strategies:
                symbol = strategy.symbol
                if await self._symbol_is_blocked(symbol):
                    continue

                await strategy.evaluate(self.market_context())
                result.per_symbol_evaluations[symbol] += 1

                # MT5 market orders execute synchronously from DayTrader's
                # perspective. Settle this strategy's replay order before
                # moving to the next symbol when an execution bar is present.
                self.broker.settle_pending_orders()

            if self.position_manager is not None:
                await self.position_manager.update_once()

            account = self.broker.account_info()
            result.account_snapshots.append(
                {
                    "timestamp": timestamp,
                    "balance": float(account["balance"]),
                    "realized_profit": float(account["realized_profit"]),
                    "unrealized_profit": float(account["unrealized_profit"]),
                    "equity": float(account["equity"]),
                    "commission_paid": float(account.get("commission_paid", 0.0)),
                }
            )

            result.evaluations += 1
            result.timestamps.append(timestamp)

        await self._snapshot(result)
        return result

    def run(
        self,
        *,
        max_steps: int | None = None,
    ) -> PortfolioBacktestResult:
        """Run a shared-account portfolio replay without wall-clock sleeps."""
        return asyncio.run(self.run_async(max_steps=max_steps))
