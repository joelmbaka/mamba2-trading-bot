"""Offline historical broker with deterministic position lifecycle semantics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from .feed import ReplayFeed


@dataclass(frozen=True)
class SymbolExecutionMetadata:
    """Explicit price and contract metadata used by the offline broker."""

    point_size: float = 0.00001
    digits: int = 5
    contract_size: float = 100_000.0
    quote_currency: str = ""
    base_currency: str = ""


class AccountCurrencyConversionError(ValueError):
    """Raised when quote-currency P/L cannot be converted deterministically."""


@dataclass(frozen=True)
class ExecutionCostModel:
    """Explicit deterministic transaction costs for one replay symbol.

    Commission is denominated in account currency and charged independently
    on entry and exit. Slippage is an adverse point offset applied to broker-
    derived execution prices; zero remains the default because historical
    OHLC/ticks cannot reconstruct actual fill slippage.
    """

    commission_per_lot_per_side: float = 0.0
    slippage_points: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("commission_per_lot_per_side", self.commission_per_lot_per_side),
            ("slippage_points", self.slippage_points),
        ):
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class ClosedTrade:
    """Immutable record of one completed position."""

    order_id: int
    position_ticket: int
    symbol: str
    side: int
    volume: float
    open_time: int
    open_price: float
    close_time: int
    close_price: float
    realized_pl: float
    exit_reason: str
    contract_size: float
    gross_realized_pl: float = 0.0
    commission: float = 0.0


class HistoricalBroker:
    """Deterministic broker ledger; intentionally independent of MetaTrader5.

    Market orders are accepted into a pending queue and fill at the open of
    the next available M1 candle. Historical MT5 OHLC is treated as Bid-side
    data and each bar's integer spread is converted from points using the
    symbol point size. BUY entries fill at Ask; SELL entries fill at Bid.
    BUY positions are marked/exited on Bid and SELL positions on synthetic Ask.
    Raw P/L is ``price_delta * direction * lots * contract_size`` in the
    traded symbol's quote currency. It is then converted into account currency
    using historical conversion prices from the same replay boundary.

    When tick-derived Ask M1 OHLC is available it is preferred. Otherwise the
    bar spread is applied uniformly to Bid OHLC as a deterministic fallback.
    Optional execution costs are explicit: commission is account-currency
    per-lot per-side, while slippage is a deterministic adverse point offset.
    Both default to zero rather than inventing broker-specific costs.

    If a candle touches both SL and TP, the stop is assumed to have occurred
    first. An adverse gap fills at the next-bar open; a target gap is capped at
    the target level. OHLC data cannot establish a more precise intrabar path.
    """

    def __init__(
        self,
        feed: ReplayFeed,
        *,
        balance: float = 10_000.0,
        symbol_metadata: Mapping[str, SymbolExecutionMetadata] | None = None,
        account_currency: str = "USD",
        execution_costs: Mapping[str, ExecutionCostModel] | None = None,
    ):
        self.feed = feed
        self.connected = False
        self._balance = float(balance)
        self._realized_pl = 0.0
        self._commission_paid = 0.0
        self.account_currency = str(account_currency).upper()
        if not self.account_currency:
            raise ValueError("account_currency must be non-empty")
        defaults = symbol_metadata or {}
        self._metadata = {
            symbol: defaults.get(symbol, SymbolExecutionMetadata())
            for symbol in feed.symbols
        }
        configured_costs = execution_costs or {}
        self._execution_costs = {
            symbol: configured_costs.get(symbol, ExecutionCostModel())
            for symbol in feed.symbols
        }
        self._positions: list[dict[str, Any]] = []
        self._pending: list[dict[str, Any]] = []
        self._closed_trades: list[ClosedTrade] = []
        self._next_position_ticket = 1
        self._next_order_id = 1

    def initialize(self) -> bool:
        self.connected = True
        return True

    def shutdown(self) -> None:
        self.connected = False

    def advance(self):
        timestamp = self.feed.advance()
        self._process_exits()
        self._mark_positions()
        self.settle_pending_orders()
        return timestamp

    def settle_pending_orders(self) -> None:
        """Fill orders eligible at the current replay boundary."""
        self._fill_pending()

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        return enable and symbol in self.feed.symbols

    def symbol_info_tick(self, symbol: str) -> dict[str, float] | None:
        bar = self.feed.current_bar(symbol)
        if bar is None:
            return None
        bid = self._bid_price(bar, "close")
        ask_bar = self.feed.current_ask_bar(symbol)
        ask = self._ask_price(symbol, bar, "close", ask_bar=ask_bar)
        return {"bid": bid, "ask": ask, "last": bid}

    def get_rates(self, symbol: str, timeframe: str | int):
        return self.feed.get_rates(symbol, timeframe)

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int):
        frame = self.feed.get_rates(symbol, f"M{timeframe}")
        if start_pos:
            frame = frame.iloc[:-start_pos]
        frame = frame.tail(count)
        bars = []
        for timestamp, row in frame.iterrows():
            bar = {"time": int(timestamp.timestamp())}
            bar.update({column: row[column] for column in frame.columns})
            bars.append(bar)
        return bars

    def account_info(self) -> dict[str, float | str]:
        unrealized = self._unrealized_pl()
        return {
            "balance": self._balance,
            "realized_profit": self._realized_pl,
            "unrealized_profit": unrealized,
            "profit": unrealized,
            "equity": self._balance + unrealized,
            "currency": self.account_currency,
            "commission_paid": self._commission_paid,
            "margin": 0.0,
            "free_margin": self._balance,
        }

    async def positions_get(self, symbol: str = "", ticket: int = 0) -> list[dict[str, Any]]:
        return [
            position.copy()
            for position in self._positions
            if (not symbol or position["symbol"] == symbol)
            and (not ticket or position["ticket"] == ticket)
        ]

    def positions_total(self) -> int:
        return len(self._positions)

    def position_get_ticket(self, ticket: int) -> dict[str, Any] | None:
        for position in self._positions:
            if position["ticket"] == ticket:
                return position.copy()
        return None

    @property
    def closed_trades(self) -> tuple[ClosedTrade, ...]:
        return tuple(self._closed_trades)

    @property
    def pending_orders(self) -> tuple[dict[str, Any], ...]:
        return tuple(order.copy() for order in self._pending)

    def get_point_size(self, symbol: str) -> float:
        return self._metadata[symbol].point_size

    def order_check(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"retcode": 0, "comment": "accepted by offline broker"}

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        order_id = self._next_order_id
        self._next_order_id += 1
        order = {
            "order_id": order_id,
            "request": request.copy(),
            "submitted_at": self.feed.current_time,
        }
        self._pending.append(order)
        return {
            "retcode": 10008,
            "deal": 0,
            "order": order_id,
            "price": 0.0,
            "comment": "pending next M1 bar",
        }

    async def order_modify(self, ticket: int, sl: float = 0.0, tp: float = 0.0):
        for position in self._positions:
            if position["ticket"] == ticket:
                position["sl"], position["tp"] = float(sl), float(tp)
                return {"retcode": 0, "comment": "modified"}
        return {"retcode": 1, "comment": "position not found"}

    def position_close(self, ticket: int, *, price: float | None = None, reason: str = "manual") -> bool:
        position = next((item for item in self._positions if item["ticket"] == ticket), None)
        if position is None:
            return False
        if reason not in {"manual", "stop_loss", "take_profit"}:
            raise ValueError(f"unsupported exit reason: {reason}")

        explicit_price = price is not None
        if price is None:
            bar = self.feed.current_bar(position["symbol"])
            if bar is None:
                return False
            price = self._closing_price(
                position,
                bar,
                "close",
                ask_bar=self.feed.current_ask_bar(position["symbol"]),
            )
        if not explicit_price:
            price = self._apply_adverse_slippage(
                position["symbol"],
                float(price),
                side=position["type"],
                is_entry=False,
            )
        self._close_position(
            position,
            float(price),
            reason,
            conversion_phase="current",
            conversion_field="close",
        )
        return True

    async def position_by_ticket(self, ticket: int):
        return self.position_get_ticket(ticket)

    def _fill_pending(self) -> None:
        current = self.feed.current_time
        if current is None:
            return
        remaining = []
        for order in self._pending:
            submitted_at = order["submitted_at"]
            if submitted_at is not None and current < submitted_at:
                remaining.append(order)
                continue
            request = order["request"]
            bar = self.feed.execution_bar(request["symbol"])
            if bar is None:
                remaining.append(order)
                continue
            symbol = request["symbol"]
            side = request.get("type", 0)
            bid_open = self._bid_price(bar, "open")
            ask_open = self._ask_price(
                symbol,
                bar,
                "open",
                ask_bar=self.feed.execution_ask_bar(symbol),
            )
            market_fill = ask_open if side == 0 else bid_open
            fill_price = self._apply_adverse_slippage(
                symbol,
                market_fill,
                side=side,
                is_entry=True,
            )
            current_price = bid_open if side == 0 else ask_open
            volume = float(request.get("volume", 1.0))
            entry_commission = self._commission_for(symbol, volume)
            position = {
                "ticket": self._next_position_ticket,
                "order_id": order["order_id"],
                "time": int(current.timestamp()),
                "symbol": symbol,
                "type": side,
                "volume": volume,
                "price_open": fill_price,
                "sl": float(request.get("sl", 0.0)),
                "tp": float(request.get("tp", 0.0)),
                "price_current": current_price,
                "profit": 0.0,
                "entry_commission": entry_commission,
            }
            position["profit"] = self._calculate_pl(
                position,
                current_price,
                conversion_phase="execution",
                conversion_field="open",
            )
            self._charge_commission(entry_commission)
            self._next_position_ticket += 1
            self._positions.append(position)
        self._pending = remaining

    def _mark_positions(self) -> None:
        for position in self._positions:
            bar = self.feed.completed_bar(position["symbol"])
            if bar is None:
                continue
            current = self._closing_price(
                position,
                bar,
                "close",
                ask_bar=self.feed.completed_ask_bar(position["symbol"]),
            )
            position["price_current"] = current
            position["profit"] = self._calculate_pl(
                position,
                current,
                conversion_phase="completed",
                conversion_field="close",
            )

    def _process_exits(self) -> None:
        for position in list(self._positions):
            bar = self.feed.completed_bar(position["symbol"])
            if bar is None:
                continue
            ask_bar = self.feed.completed_ask_bar(position["symbol"])
            reason = self._exit_reason(position, bar, ask_bar=ask_bar)
            if reason is None:
                continue
            price = self._exit_price(
                position,
                bar,
                reason,
                ask_bar=ask_bar,
            )
            self._close_position(
                position,
                price,
                reason,
                conversion_phase="completed",
                conversion_field="close",
            )

    def _exit_reason(
        self,
        position: dict[str, Any],
        bar,
        *,
        ask_bar=None,
    ) -> str | None:
        symbol = position["symbol"]
        sl, tp = position["sl"], position["tp"]
        if position["type"] == 0:
            low = self._bid_price(bar, "low")
            high = self._bid_price(bar, "high")
            stop_hit = sl > 0 and low <= sl
            target_hit = tp > 0 and high >= tp
        else:
            low = self._ask_price(symbol, bar, "low", ask_bar=ask_bar)
            high = self._ask_price(symbol, bar, "high", ask_bar=ask_bar)
            stop_hit = sl > 0 and high >= sl
            target_hit = tp > 0 and low <= tp
        if stop_hit:
            return "stop_loss"
        if target_hit:
            return "take_profit"
        return None

    def _exit_price(
        self,
        position: dict[str, Any],
        bar,
        reason: str,
        *,
        ask_bar=None,
    ) -> float:
        opening = self._closing_price(
            position,
            bar,
            "open",
            ask_bar=ask_bar,
        )
        level = position["sl"] if reason == "stop_loss" else position["tp"]
        if position["type"] == 0:
            adverse_gap = reason == "stop_loss" and opening <= level
        else:
            adverse_gap = reason == "stop_loss" and opening >= level
        market_price = opening if adverse_gap else float(level)
        return self._apply_adverse_slippage(
            position["symbol"],
            market_price,
            side=position["type"],
            is_entry=False,
        )

    def _close_position(
        self,
        position: dict[str, Any],
        price: float,
        reason: str,
        *,
        conversion_phase: str,
        conversion_field: str,
    ) -> None:
        gross_realized = self._calculate_pl(
            position,
            price,
            conversion_phase=conversion_phase,
            conversion_field=conversion_field,
        )
        close_time = self.feed.current_time
        if close_time is None:
            raise RuntimeError("cannot close a position before replay starts")

        exit_commission = self._commission_for(
            position["symbol"],
            position["volume"],
        )
        entry_commission = float(position.get("entry_commission", 0.0))
        total_commission = entry_commission + exit_commission
        net_trade_pl = gross_realized - total_commission

        # Entry commission was already charged at fill, so only gross P/L and
        # the exit-side commission move balance here.
        self._realized_pl += gross_realized - exit_commission
        self._balance += gross_realized - exit_commission
        self._commission_paid += exit_commission

        self._positions.remove(position)
        self._closed_trades.append(
            ClosedTrade(
                order_id=position["order_id"],
                position_ticket=position["ticket"],
                symbol=position["symbol"],
                side=position["type"],
                volume=position["volume"],
                open_time=position["time"],
                open_price=position["price_open"],
                close_time=int(close_time.timestamp()),
                close_price=price,
                realized_pl=net_trade_pl,
                exit_reason=reason,
                contract_size=self._metadata[position["symbol"]].contract_size,
                gross_realized_pl=gross_realized,
                commission=total_commission,
            )
        )

    def _commission_for(self, symbol: str, volume: float) -> float:
        model = self._execution_costs[symbol]
        return float(model.commission_per_lot_per_side) * float(volume)

    def _charge_commission(self, amount: float) -> None:
        if amount == 0:
            return
        self._commission_paid += amount
        self._realized_pl -= amount
        self._balance -= amount

    def _apply_adverse_slippage(
        self,
        symbol: str,
        price: float,
        *,
        side: int,
        is_entry: bool,
    ) -> float:
        model = self._execution_costs[symbol]
        points = float(model.slippage_points)
        if points == 0:
            return float(price)

        metadata = self._metadata[symbol]
        offset = points * metadata.point_size

        # BUY entry and SELL exit pay upward slippage. SELL entry and BUY exit
        # pay downward slippage. This always worsens the realized fill.
        upward = (is_entry and side == 0) or (not is_entry and side == 1)
        slipped = float(price) + offset if upward else float(price) - offset
        return round(slipped, metadata.digits)

    def _unrealized_pl(self) -> float:
        return sum(position["profit"] for position in self._positions)

    @staticmethod
    def _bid_price(bar, field: str) -> float:
        return float(bar[field])

    def _ask_price(
        self,
        symbol: str,
        bar,
        field: str,
        *,
        ask_bar=None,
    ) -> float:
        metadata = self._metadata[symbol]
        if ask_bar is not None:
            return round(float(ask_bar[field]), metadata.digits)
        spread = float(bar["spread"]) * metadata.point_size
        return round(float(bar[field]) + spread, metadata.digits)

    def _closing_price(
        self,
        position: dict[str, Any],
        bar,
        field: str,
        *,
        ask_bar=None,
    ) -> float:
        if position["type"] == 0:
            return self._bid_price(bar, field)
        return self._ask_price(
            position["symbol"],
            bar,
            field,
            ask_bar=ask_bar,
        )

    def _calculate_quote_pl(
        self,
        position: dict[str, Any],
        price: float,
    ) -> float:
        metadata = self._metadata[position["symbol"]]
        direction = 1 if position["type"] == 0 else -1
        return (
            (price - position["price_open"])
            * direction
            * position["volume"]
            * metadata.contract_size
        )

    def _symbol_currencies(self, symbol: str) -> tuple[str, str]:
        metadata = self._metadata[symbol]
        base = str(metadata.base_currency).upper()
        quote = str(metadata.quote_currency).upper()
        if not base and len(symbol) >= 6:
            candidate = symbol[:6].upper()
            if candidate.isalpha():
                base = candidate[:3]
                if not quote:
                    quote = candidate[3:6]
        return base, quote

    def _conversion_pair(
        self,
        from_currency: str,
        to_currency: str,
    ) -> tuple[str, str]:
        """Find one historical FX pair for a single conversion leg.

        Direct means the pair is TO/FROM, so converting FROM into TO divides
        by the appropriate Ask/Bid. Inverse means the pair is FROM/TO, so
        conversion multiplies by Bid/Ask.
        """

        source = from_currency.upper()
        target = to_currency.upper()
        if not source or not target or source == target:
            raise AccountCurrencyConversionError(
                f"invalid conversion leg {source}->{target}"
            )

        direct_name = f"{target}{source}"
        inverse_name = f"{source}{target}"
        if direct_name in self._metadata:
            return direct_name, "direct"
        if inverse_name in self._metadata:
            return inverse_name, "inverse"

        for symbol in self._metadata:
            base, quote = self._symbol_currencies(symbol)
            if base == target and quote == source:
                return symbol, "direct"
            if base == source and quote == target:
                return symbol, "inverse"

        raise AccountCurrencyConversionError(
            f"no historical conversion pair for {source}->{target}"
        )

    def _conversion_bar(
        self,
        symbol: str,
        *,
        phase: str,
    ):
        if phase == "execution":
            bid_bar = self.feed.execution_bar(symbol)
            ask_bar = self.feed.execution_ask_bar(symbol)
        elif phase == "completed":
            bid_bar = self.feed.completed_bar(symbol)
            ask_bar = self.feed.completed_ask_bar(symbol)
        elif phase == "current":
            bid_bar = self.feed.current_bar(symbol)
            ask_bar = self.feed.current_ask_bar(symbol)
        else:
            raise ValueError(f"unsupported conversion phase: {phase}")

        if bid_bar is None:
            current = self.feed.current_time
            raise AccountCurrencyConversionError(
                f"no {phase} conversion bar for {symbol} at {current}"
            )
        return bid_bar, ask_bar

    def _convert_currency_leg(
        self,
        amount: float,
        *,
        from_currency: str,
        to_currency: str,
        phase: str,
        field: str,
    ) -> float:
        """Convert one FX leg using only same-boundary historical Bid/Ask."""

        if amount == 0.0 or from_currency.upper() == to_currency.upper():
            return amount

        symbol, route = self._conversion_pair(
            from_currency,
            to_currency,
        )
        bid_bar, ask_bar = self._conversion_bar(symbol, phase=phase)
        bid = self._bid_price(bid_bar, field)
        ask = self._ask_price(
            symbol,
            bid_bar,
            field,
            ask_bar=ask_bar,
        )
        if bid <= 0 or ask <= 0:
            raise AccountCurrencyConversionError(
                f"invalid conversion price for {symbol}"
            )

        if route == "direct":
            rate = ask if amount > 0 else bid
            return amount / rate

        rate = bid if amount > 0 else ask
        return amount * rate

    def _conversion_intermediates(
        self,
        *,
        from_currency: str,
        to_currency: str,
    ) -> tuple[str, ...]:
        currencies = set()
        for symbol in self._metadata:
            base, quote = self._symbol_currencies(symbol)
            if base:
                currencies.add(base)
            if quote:
                currencies.add(quote)
        currencies.discard(from_currency.upper())
        currencies.discard(to_currency.upper())
        return tuple(sorted(currencies))

    def _convert_quote_pl(
        self,
        amount: float,
        *,
        quote_currency: str,
        phase: str,
        field: str,
    ) -> float:
        quote = quote_currency.upper()
        account = self.account_currency
        if amount == 0.0 or quote == account:
            return amount
        if not quote:
            raise AccountCurrencyConversionError(
                "position quote currency is missing"
            )

        direct_error = None
        try:
            return self._convert_currency_leg(
                amount,
                from_currency=quote,
                to_currency=account,
                phase=phase,
                field=field,
            )
        except AccountCurrencyConversionError as exc:
            direct_error = exc

        # Preserve same-boundary conversion when a direct pair has a sparse
        # M1 gap by using an observed two-leg route on this exact phase.
        # No prior or future quote is carried forward.
        for intermediate in self._conversion_intermediates(
            from_currency=quote,
            to_currency=account,
        ):
            try:
                converted = self._convert_currency_leg(
                    amount,
                    from_currency=quote,
                    to_currency=intermediate,
                    phase=phase,
                    field=field,
                )
                return self._convert_currency_leg(
                    converted,
                    from_currency=intermediate,
                    to_currency=account,
                    phase=phase,
                    field=field,
                )
            except AccountCurrencyConversionError:
                continue

        current = self.feed.current_time
        raise AccountCurrencyConversionError(
            f"no same-boundary historical conversion route for "
            f"{quote}->{account} during {phase} at {current}; "
            f"direct failure: {direct_error}"
        )

    def _calculate_pl(
        self,
        position: dict[str, Any],
        price: float,
        *,
        conversion_phase: str,
        conversion_field: str,
    ) -> float:
        _base_currency, quote_currency = self._symbol_currencies(
            position["symbol"]
        )
        quote_pl = self._calculate_quote_pl(position, price)
        return self._convert_quote_pl(
            quote_pl,
            quote_currency=quote_currency,
            phase=conversion_phase,
            field=conversion_field,
        )
