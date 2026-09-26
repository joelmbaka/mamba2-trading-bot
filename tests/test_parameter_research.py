"""M022 Phase-1 research machinery tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from mamba2.backtest.broker import SymbolExecutionMetadata
from mamba2.backtest.mt5_dataset import LoadedHistoricalDataset
from mamba2.backtest.parameter_research import (
    DecisionSpreadBrokerProxy,
    M022_PARTITIONS,
    Phase1Arm,
    Phase1Parameters,
    ResearchStrategyWrapper,
    _strict_common_boundary_clock,
    _temporary_research_config,
    reference_arm,
    run_phase1_arm,
    slice_dataset,
)


def _bars(index: pd.DatetimeIndex, base: float = 1.1) -> pd.DataFrame:
    values = [base + i * 0.0001 for i in range(len(index))]
    return pd.DataFrame(
        {
            "open": values,
            "high": [value + 0.0002 for value in values],
            "low": [value - 0.0002 for value in values],
            "close": [value + 0.0001 for value in values],
            "tick_volume": [10] * len(index),
            "spread": [10] * len(index),
            "real_volume": [0] * len(index),
        },
        index=index,
    )


def _ask_bars(index: pd.DatetimeIndex, base: float = 1.1001) -> pd.DataFrame:
    values = [base + i * 0.0001 for i in range(len(index))]
    return pd.DataFrame(
        {
            "open": values,
            "high": [value + 0.0002 for value in values],
            "low": [value - 0.0002 for value in values],
            "close": [value + 0.0001 for value in values],
        },
        index=index,
    )


def test_reference_arm_is_frozen_current_configuration():
    arm = reference_arm()
    assert arm == Phase1Arm(
        experiment_id="M022-P1-REFERENCE",
        family="reference",
        value_label="21/7/7-20/80-ema7-no-spread-gate-atr1x2-all-hours",
        parameters=Phase1Parameters(),
    )
    assert arm.parameters.stochastic_k_period == 21
    assert arm.parameters.stochastic_d_period == 7
    assert arm.parameters.stochastic_slowing == 7
    assert arm.parameters.oversold_level == 20
    assert arm.parameters.overbought_level == 80
    assert arm.parameters.ema_period == 7
    assert arm.parameters.atr_sl_multiplier == 1.0
    assert arm.parameters.atr_tp_multiplier == 2.0
    assert arm.parameters.decision_spread_max_points is None
    assert arm.parameters.block_00_04_utc is False


def test_strategy_default_constructor_matches_reference_config(monkeypatch):
    from mamba2.strategy import triple_cross

    cfg = SimpleNamespace(
        stochastic_timeframes={
            "higher": "M15",
            "trading": "M5",
            "entry": "M1",
        },
        use_higher_tf=False,
        stochastic_k_period=21,
        stochastic_d_period=7,
        stochastic_slowing=7,
    )
    monkeypatch.setattr(triple_cross, "config", cfg)

    default = triple_cross.StochasticTripleTFStrategy("EURUSD")

    assert default.stochastic_k_period == 21
    assert default.stochastic_d_period == 7
    assert default.stochastic_slowing == 7
    assert default.oversold_level == 20.0
    assert default.overbought_level == 80.0
    assert default.ema_period == 7


@pytest.mark.asyncio
async def test_strategy_boundary_and_ema_overrides_are_used(monkeypatch):
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    cfg = SimpleNamespace(
        stochastic_timeframes={
            "higher": "M15",
            "trading": "M5",
            "entry": "M1",
        },
        use_higher_tf=False,
        ENABLE_TREND_CONDITION=False,
        ENABLE_RSI_CONDITION=False,
        position_size=0.1,
        stochastic_k_period=21,
        stochastic_d_period=7,
        stochastic_slowing=7,
    )
    monkeypatch.setattr(triple_cross, "config", cfg)

    def fake_stochastic(*, symbol, timeframe, rate_fetcher, **_kwargs):
        del symbol, rate_fetcher
        if timeframe == "M5":
            k, d = [50.0, 60.0], [50.0, 50.0]
        elif timeframe == "M1":
            k, d = [14.0, 30.0], [20.0, 20.0]
        else:
            raise AssertionError("M15 must stay disabled")
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    ema_periods = []

    def fake_ema(_symbol, _timeframe, period, _kind, _fetcher):
        ema_periods.append(period)
        return 1.1002

    monkeypatch.setattr(moving_average, "get_moving_average", fake_ema)

    class Fetcher:
        def get_rates(self, _symbol, _timeframe):
            return pd.DataFrame(
                {
                    "open": [1.1000, 1.1001],
                    "high": [1.1003, 1.1006],
                    "low": [1.0998, 1.0999],
                    "close": [1.1001, 1.1005],
                }
            )

    class Broker:
        def __init__(self):
            self.order_send = Mock(
                return_value={"retcode": 0, "order": 1, "price": 1.1005}
            )

        def symbol_info_tick(self, _symbol):
            return {"bid": 1.1004, "ask": 1.1005}

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy(
        "EURUSD",
        oversold_level=15,
        overbought_level=85,
        ema_period=9,
    )
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": Fetcher(),
            "position_manager": None,
            "reporting_enabled": False,
        }
    )

    broker.order_send.assert_called_once()
    assert ema_periods == [9]

    broker_blocked = Broker()
    blocked = triple_cross.StochasticTripleTFStrategy(
        "EURUSD",
        oversold_level=10,
        overbought_level=90,
        ema_period=9,
    )
    await blocked.evaluate(
        {
            "broker": broker_blocked,
            "rate_fetcher": Fetcher(),
            "position_manager": None,
            "reporting_enabled": False,
        }
    )
    broker_blocked.order_send.assert_not_called()


def test_slice_dataset_excludes_all_post_development_rows():
    index = pd.date_range(
        "2026-04-20T23:57:00Z",
        "2026-04-21T00:02:00Z",
        freq="min",
    )
    m5_index = pd.DatetimeIndex(
        [
            pd.Timestamp("2026-04-20T23:55:00Z"),
            pd.Timestamp("2026-04-21T00:00:00Z"),
        ]
    )
    m15_index = pd.DatetimeIndex(
        [
            pd.Timestamp("2026-04-20T23:45:00Z"),
            pd.Timestamp("2026-04-21T00:00:00Z"),
        ]
    )
    dataset = LoadedHistoricalDataset(
        m1_bars={"EURUSD": _bars(index)},
        native_timeframe_bars={
            "EURUSD": {
                "M5": _bars(m5_index),
                "M15": _bars(m15_index),
            }
        },
        ask_m1_bars={"EURUSD": _ask_bars(index)},
        symbol_metadata={
            "EURUSD": SymbolExecutionMetadata(
                point_size=0.00001,
                digits=5,
                contract_size=100000.0,
                quote_currency="USD",
                base_currency="EUR",
            )
        },
        account_currency="USD",
        manifest={
            "requested_range": {
                "from_utc": "2025-08-25T00:00:00Z",
                "to_utc": "2026-09-25T00:00:00Z",
            }
        },
    )

    sliced = slice_dataset(dataset, partition="development")
    end = pd.Timestamp(M022_PARTITIONS["development"][1])

    assert sliced.m1_bars["EURUSD"].index.max() < end
    assert sliced.ask_m1_bars["EURUSD"].index.max() < end
    assert sliced.native_timeframe_bars["EURUSD"]["M5"].index.max() < end
    assert sliced.native_timeframe_bars["EURUSD"]["M15"].index.max() < end
    assert sliced.m1_bars["EURUSD"].index.equals(
        sliced.ask_m1_bars["EURUSD"].index
    )


def test_slice_dataset_preserves_symbol_m1_and_builds_shared_boundaries():
    index = pd.date_range(
        "2026-04-20T23:55:00Z",
        "2026-04-20T23:59:00Z",
        freq="min",
    )
    eur_index = index
    jpy_index = index.delete(2)
    m5_index = pd.DatetimeIndex(
        [pd.Timestamp("2026-04-20T23:55:00Z")]
    )
    m15_index = pd.DatetimeIndex(
        [pd.Timestamp("2026-04-20T23:45:00Z")]
    )

    dataset = LoadedHistoricalDataset(
        m1_bars={
            "EURUSD": _bars(eur_index, 1.10),
            "USDJPY": _bars(jpy_index, 145.0),
        },
        native_timeframe_bars={
            "EURUSD": {
                "M5": _bars(m5_index, 1.10),
                "M15": _bars(m15_index, 1.10),
            },
            "USDJPY": {
                "M5": _bars(m5_index, 145.0),
                "M15": _bars(m15_index, 145.0),
            },
        },
        ask_m1_bars={
            "EURUSD": _ask_bars(eur_index, 1.1001),
            "USDJPY": _ask_bars(jpy_index, 145.001),
        },
        symbol_metadata={
            "EURUSD": SymbolExecutionMetadata(
                point_size=0.00001,
                digits=5,
                contract_size=100000.0,
                quote_currency="USD",
                base_currency="EUR",
            ),
            "USDJPY": SymbolExecutionMetadata(
                point_size=0.001,
                digits=3,
                contract_size=100000.0,
                quote_currency="JPY",
                base_currency="USD",
            ),
        },
        account_currency="USD",
        manifest={
            "requested_range": {
                "from_utc": "2025-08-25T00:00:00Z",
                "to_utc": "2026-09-25T00:00:00Z",
            }
        },
    )

    sliced = slice_dataset(dataset, partition="development")
    boundaries = _strict_common_boundary_clock(
        sliced.m1_bars,
        sliced.ask_m1_bars,
        end_exclusive=pd.Timestamp("2026-04-21T00:00:00Z"),
    )

    assert sliced.m1_bars["EURUSD"].index.equals(eur_index)
    assert sliced.m1_bars["USDJPY"].index.equals(jpy_index)
    assert sliced.ask_m1_bars["EURUSD"].index.equals(eur_index)
    assert sliced.ask_m1_bars["USDJPY"].index.equals(jpy_index)
    assert pd.Timestamp("2026-04-20T23:57:00Z") not in boundaries
    assert pd.Timestamp("2026-04-20T23:58:00Z") not in boundaries
    assert pd.Timestamp("2026-04-20T23:59:00Z") in boundaries
    assert pd.Timestamp("2026-04-21T00:00:00Z") in boundaries
    assert sliced.manifest["m022_strict_common_boundary_clock"] is True
    assert sliced.manifest["m022_full_symbol_m1_preserved"] is True
    assert sliced.manifest["m022_replay_boundary_count"] == len(boundaries)
    assert sliced.manifest["m022_replay_boundary_sha256"]


def test_phase1_runner_refuses_validation_before_reading_manifest():
    with pytest.raises(ValueError, match="development-only"):
        run_phase1_arm(
            "/definitely/not/a/manifest.json",
            arm=reference_arm(),
            partition="validation",
        )


def test_temporary_research_config_restores_globals_after_exception():
    from config import config

    original = (
        config.stochastic_k_period,
        config.stochastic_d_period,
        config.stochastic_slowing,
        config.atr_sl_multiplier,
        config.atr_tp_multiplier,
    )
    params = Phase1Parameters(
        stochastic_k_period=9,
        stochastic_d_period=3,
        stochastic_slowing=3,
        atr_sl_multiplier=1.5,
        atr_tp_multiplier=3.0,
    )

    with pytest.raises(RuntimeError, match="synthetic"):
        with _temporary_research_config(params):
            assert config.stochastic_k_period == 9
            assert config.atr_sl_multiplier == 1.5
            raise RuntimeError("synthetic")

    assert (
        config.stochastic_k_period,
        config.stochastic_d_period,
        config.stochastic_slowing,
        config.atr_sl_multiplier,
        config.atr_tp_multiplier,
    ) == original


def test_decision_spread_proxy_uses_current_bid_ask_and_rejects():
    class Broker:
        def __init__(self):
            self.sent = []

        def symbol_info_tick(self, _symbol):
            return {"bid": 1.10000, "ask": 1.10012}

        def get_point_size(self, _symbol):
            return 0.00001

        def order_send(self, request):
            self.sent.append(request)
            return {"retcode": 0, "order": 1}

    broker = Broker()
    proxy = DecisionSpreadBrokerProxy(broker, max_points=10)
    response = proxy.order_send({"symbol": "EURUSD", "price": 1.10012})

    assert response["retcode"] == proxy.RESEARCH_REJECT_CODE
    assert proxy.rejections == 1
    assert proxy.accepted_checks == 0
    assert broker.sent == []
    assert proxy.observations[0]["spread_points"] == pytest.approx(12.0)


@pytest.mark.asyncio
async def test_session_wrapper_blocks_only_00_to_04_utc():
    class Strategy:
        symbol = "EURUSD"

        def __init__(self):
            self.calls = 0

        async def evaluate(self, _market):
            self.calls += 1

    class Fetcher:
        def __init__(self, current_time):
            self.current_time = pd.Timestamp(current_time)

    strategy = Strategy()
    wrapper = ResearchStrategyWrapper(
        strategy,
        block_00_04_utc=True,
        decision_spread_max_points=None,
    )

    await wrapper.evaluate(
        {"rate_fetcher": Fetcher("2026-01-01T02:00:00Z"), "broker": object()}
    )
    await wrapper.evaluate(
        {"rate_fetcher": Fetcher("2026-01-01T04:00:00Z"), "broker": object()}
    )

    assert wrapper.blocked_evaluation_boundaries == 1
    assert strategy.calls == 1
