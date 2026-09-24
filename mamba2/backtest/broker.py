"""Offline historical broker with next-M1-bar market-order fills."""

from __future__ import annotations

from typing import Any

from .feed import ReplayFeed, TIMEFRAME_MINUTES


class HistoricalBroker:
    """Deterministic broker ledger; intentionally independent of MetaTrader5.

    ``order_send`` records a pending market order. It is filled at the open
    of the next available M1 candle when ``advance`` is called. Thus a signal
    observed at candle T cannot fill at T or at any earlier price.
    """

    def __init__(self, feed: ReplayFeed, *, balance: float = 10_000.0):
        self.feed = feed
        self.connected = False
        self._balance = float(balance)
        self._positions: list[dict[str, Any]] = []
        self._pending: list[dict[str, Any]] = []
        self._next_ticket = 1
        self._next_order = 1

    def initialize(self) -> bool:
        self.connected = True
        return True

    def shutdown(self) -> None:
        self.connected = False

    def advance(self):
        timestamp = self.feed.advance()
        self._fill_pending()
        self._mark_positions()
        return timestamp

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        return enable and symbol in self.feed.symbols

    def symbol_info_tick(self, symbol: str) -> dict[str, float] | None:
        bar = self.feed.current_bar(symbol)
        if bar is None:
            return None
        return {"bid": float(bar["close"]), "ask": float(bar["close"]), "last": float(bar["close"])}

    def get_rates(self, symbol: str, timeframe: str | int):
        return self.feed.get_rates(symbol, timeframe)

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int):
        frame = self.feed.get_rates(symbol, f"M{timeframe}")
        if start_pos:
            frame = frame.iloc[:-start_pos]
        frame = frame.tail(count)
        return [
            {"time": int(row.Index.timestamp()), **{column: row[column] for column in frame.columns}}
            for row in frame.itertuples()
        ]

    def account_info(self) -> dict[str, float | str]:
        unrealized = sum(position["profit"] for position in self._positions)
        return {
            "balance": self._balance,
            "equity": self._balance + unrealized,
            "currency": "USD",
            "margin": 0.0,
            "free_margin": self._balance,
        }

    def positions_get(self, symbol: str = "") -> list[dict[str, Any]]:
        return [p.copy() for p in self._positions if not symbol or p["symbol"] == symbol]

    def positions_total(self) -> int:
        return len(self._positions)

    def position_get_ticket(self, ticket: int) -> dict[str, Any] | None:
        for position in self._positions:
            if position["ticket"] == ticket:
                return position.copy()
        return None

    def order_check(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"retcode": 0, "comment": "accepted by offline broker"}

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        order = {"ticket": self._next_order, "request": request.copy(), "submitted_at": self.feed.current_time}
        self._next_order += 1
        self._pending.append(order)
        return {"retcode": 10008, "deal": 0, "order": order["ticket"], "price": 0.0, "comment": "pending next M1 bar"}

    def _fill_pending(self) -> None:
        current = self.feed.current_time
        if current is None:
            return
        remaining = []
        for order in self._pending:
            if order["submitted_at"] is not None and current <= order["submitted_at"]:
                remaining.append(order)
                continue
            request = order["request"]
            bar = self.feed.current_bar(request["symbol"])
            if bar is None:
                remaining.append(order)
                continue
            position = {
                "ticket": self._next_ticket,
                "time": int(current.timestamp()),
                "symbol": request["symbol"],
                "type": request.get("type", 0),
                "volume": float(request.get("volume", 1.0)),
                "price_open": float(bar["open"]),
                "sl": float(request.get("sl", 0.0)),
                "tp": float(request.get("tp", 0.0)),
                "price_current": float(bar["open"]),
                "profit": 0.0,
            }
            self._next_ticket += 1
            self._positions.append(position)
        self._pending = remaining

    def _mark_positions(self) -> None:
        for position in self._positions:
            bar = self.feed.current_bar(position["symbol"])
            if bar is None:
                continue
            current = float(bar["close"])
            position["price_current"] = current
            direction = 1 if position["type"] == 0 else -1
            position["profit"] = (current - position["price_open"]) * direction * position["volume"]

    async def position_by_ticket(self, ticket: int):
        return self.position_get_ticket(ticket)

    async def order_modify(self, ticket: int, sl: float = 0.0, tp: float = 0.0):
        position = self.position_get_ticket(ticket)
        if position is None:
            return {"retcode": 1, "comment": "position not found"}
        for stored in self._positions:
            if stored["ticket"] == ticket:
                stored["sl"], stored["tp"] = sl, tp
        return {"retcode": 0, "comment": "modified"}
