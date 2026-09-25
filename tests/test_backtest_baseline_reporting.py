"""Deterministic baseline reporting over the portfolio replay result."""

from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import pytest

from mamba2.backtest import (
    COST_ASSUMPTION_LABEL,
    ClosedTrade,
    HistoricalBroker,
    PortfolioBacktestResult,
    ReplayFeed,
    SymbolExecutionMetadata,
    build_baseline_report,
    format_baseline_summary,
)
from mamba2.backtest.mt5_dataset import LoadedHistoricalDataset


def frame(symbol, base):
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=3,
        freq="min",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "time": times,
            "open": [base, base, base],
            "high": [base + 0.001] * 3,
            "low": [base - 0.001] * 3,
            "close": [base, base, base],
            "tick_volume": [10] * 3,
            "spread": [0] * 3,
            "real_volume": [0] * 3,
        }
    )


def dataset(symbols):
    bars = {symbol: frame(symbol, 1.1) for symbol in symbols}
    metadata = {
        symbol: SymbolExecutionMetadata(
            point_size=0.00001,
            digits=5,
            contract_size=100_000.0,
            base_currency=symbol[:3],
            quote_currency=symbol[3:6],
        )
        for symbol in symbols
    }
    return LoadedHistoricalDataset(
        m1_bars=bars,
        native_timeframe_bars={},
        ask_m1_bars={},
        symbol_metadata=metadata,
        account_currency="USD",
        manifest={
            "schema_version": 2,
            "source": "MetaTrader5",
            "timestamp_semantics": "bar_open_utc",
            "requested_range": {
                "from_utc": "2025-01-02T10:00:00Z",
                "to_utc": "2025-01-02T10:03:00Z",
            },
        },
    )


def closed_trade(symbol, ticket, realized, gross=None, commission=0.0):
    return ClosedTrade(
        order_id=ticket,
        position_ticket=ticket,
        symbol=symbol,
        side=0,
        volume=0.1,
        open_time=1,
        open_price=1.0,
        close_time=2,
        close_price=1.0,
        realized_pl=realized,
        exit_reason="manual",
        contract_size=100_000.0,
        gross_realized_pl=realized if gross is None else gross,
        commission=commission,
    )


def test_baseline_report_uses_shared_equity_curve_and_trade_ledger(monkeypatch):
    import mamba2.backtest.baseline as baseline_module

    symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
    monkeypatch.setattr(
        baseline_module,
        "config",
        SimpleNamespace(
            symbols=symbols,
            position_size=0.1,
            ENABLE_TREND_CONDITION=False,
            ENABLE_RSI_CONDITION=False,
            use_higher_tf=False,
            stochastic_timeframes={
                "higher": "M15",
                "trading": "M5",
                "entry": "M1",
            },
            stochastic_k_period=14,
            atr_period=14,
            atr_timeframe="M5",
            atr_sl_multiplier=1.0,
            atr_tp_multiplier=2.0,
        ),
    )

    feed = ReplayFeed({"EURUSD": frame("EURUSD", 1.1)})
    broker = HistoricalBroker(
        feed,
        balance=10_000.0,
        symbol_metadata={
            "EURUSD": SymbolExecutionMetadata(
                base_currency="EUR",
                quote_currency="USD",
            )
        },
    )
    broker._closed_trades = [
        closed_trade("EURUSD", 1, 120.0, gross=124.0, commission=4.0),
        closed_trade("EURUSD", 2, -50.0, gross=-46.0, commission=4.0),
        closed_trade("GBPUSD", 3, 0.0, gross=0.0, commission=0.0),
    ]
    broker._balance = 10_070.0
    broker._realized_pl = 70.0
    broker._commission_paid = 8.0

    result = PortfolioBacktestResult(
        evaluations=3,
        accepted_orders_by_symbol={
            "EURUSD": [{}, {}],
            "EURJPY": [],
            "GBPUSD": [{}],
            "GBPJPY": [],
            "USDJPY": [],
        },
        open_positions_by_symbol={symbol: [] for symbol in symbols},
        pending_orders_by_symbol={symbol: [] for symbol in symbols},
        closed_trade_count_by_symbol={
            "EURUSD": 2,
            "EURJPY": 0,
            "GBPUSD": 1,
            "GBPJPY": 0,
            "USDJPY": 0,
        },
        account_snapshots=[
            {
                "timestamp": pd.Timestamp("2025-01-02 10:01", tz="UTC"),
                "balance": 10_000.0,
                "realized_profit": 0.0,
                "unrealized_profit": 100.0,
                "equity": 10_100.0,
                "commission_paid": 0.0,
            },
            {
                "timestamp": pd.Timestamp("2025-01-02 10:02", tz="UTC"),
                "balance": 10_070.0,
                "realized_profit": 70.0,
                "unrealized_profit": -170.0,
                "equity": 9_900.0,
                "commission_paid": 8.0,
            },
            {
                "timestamp": pd.Timestamp("2025-01-02 10:03", tz="UTC"),
                "balance": 10_070.0,
                "realized_profit": 70.0,
                "unrealized_profit": -20.0,
                "equity": 10_050.0,
                "commission_paid": 8.0,
            },
        ],
        final_account={
            "balance": 10_070.0,
            "realized_profit": 70.0,
            "unrealized_profit": -20.0,
            "equity": 10_050.0,
            "commission_paid": 8.0,
            "currency": "USD",
        },
    )

    report = build_baseline_report(
        dataset=dataset(symbols),
        result=result,
        broker=broker,
        starting_balance=10_000.0,
    )

    aggregate = report["aggregate"]
    assert aggregate["accepted_orders"] == 3
    assert aggregate["closed_trades"] == 3
    assert aggregate["winning_closed_trades"] == 1
    assert aggregate["losing_closed_trades"] == 1
    assert aggregate["flat_closed_trades"] == 1
    assert aggregate["win_rate_nonflat_pct"] == pytest.approx(50.0)
    assert aggregate["gross_realized_pl"] == pytest.approx(78.0)
    assert aggregate["commission"] == pytest.approx(8.0)
    assert aggregate["net_realized_pl"] == pytest.approx(70.0)
    assert aggregate["largest_closed_trade_gain"] == pytest.approx(120.0)
    assert aggregate["largest_closed_trade_loss"] == pytest.approx(-50.0)
    assert aggregate["maximum_equity_drawdown"] == pytest.approx(200.0)
    assert aggregate["maximum_equity_drawdown_pct"] == pytest.approx(
        200.0 / 10_100.0 * 100.0
    )
    assert report["cost_assumptions"]["label"] == COST_ASSUMPTION_LABEL
    assert report["per_symbol"]["EURUSD"]["net_realized_pl"] == pytest.approx(70.0)
    assert len(report["equity_curve"]) == 3
    assert "2025-01-02T10:01:00Z" == report["equity_curve"][0]["timestamp"]


def test_drawdown_peak_includes_starting_equity(monkeypatch):
    import mamba2.backtest.baseline as baseline_module

    monkeypatch.setattr(
        baseline_module,
        "config",
        SimpleNamespace(
            symbols=["EURUSD"],
            position_size=0.1,
            ENABLE_TREND_CONDITION=False,
            ENABLE_RSI_CONDITION=False,
            use_higher_tf=False,
            stochastic_timeframes={"higher": "M15", "trading": "M5", "entry": "M1"},
            stochastic_k_period=14,
            atr_period=14,
            atr_timeframe="M5",
            atr_sl_multiplier=1.0,
            atr_tp_multiplier=2.0,
        ),
    )
    feed = ReplayFeed({"EURUSD": frame("EURUSD", 1.1)})
    broker = HistoricalBroker(feed)
    result = PortfolioBacktestResult(
        evaluations=1,
        accepted_orders_by_symbol={"EURUSD": []},
        open_positions_by_symbol={"EURUSD": []},
        pending_orders_by_symbol={"EURUSD": []},
        closed_trade_count_by_symbol={"EURUSD": 0},
        account_snapshots=[
            {
                "timestamp": pd.Timestamp("2025-01-02 10:01", tz="UTC"),
                "balance": 10_000.0,
                "realized_profit": 0.0,
                "unrealized_profit": -100.0,
                "equity": 9_900.0,
                "commission_paid": 0.0,
            }
        ],
        final_account={
            "balance": 10_000.0,
            "realized_profit": 0.0,
            "unrealized_profit": -100.0,
            "equity": 9_900.0,
            "commission_paid": 0.0,
            "currency": "USD",
        },
    )
    report = build_baseline_report(
        dataset=dataset(["EURUSD"]),
        result=result,
        broker=broker,
        starting_balance=10_000.0,
    )
    assert report["aggregate"]["maximum_equity_drawdown"] == pytest.approx(100.0)
    assert report["aggregate"]["maximum_equity_drawdown_pct"] == pytest.approx(1.0)


def test_terminal_summary_is_stable(monkeypatch):
    report = {
        "aggregate": {
            "global_replay_boundaries": 20,
            "accepted_orders": 2,
            "closed_trades": 1,
            "remaining_open_positions": 1,
            "ending_realized_balance": 10010.0,
            "ending_equity": 10005.5,
            "maximum_equity_drawdown": 25.0,
            "maximum_equity_drawdown_pct": 0.25,
        }
    }
    assert format_baseline_summary(report) == (
        "boundaries=20 orders=2 closed=1 open=1 "
        "balance=10010.00 equity=10005.50 max_dd=25.00 (0.25%)"
    )
