"""Static preflight for the *uncompiled*, observation-only M031 LEAN port.

These tests deliberately cannot prove C# API compatibility or indicator parity.
The next validator must compile a pinned LEAN runtime and compare actual traces.
"""
from pathlib import Path

ROOT = Path(__file__).parents[1]
LEAN = ROOT / "lean" / "M031"
DATA = LEAN / "M031FrozenData.cs"
ALGORITHM = LEAN / "M031FrozenBaselineAlgorithm.cs"


def test_independent_source_has_no_python_strategy_imports():
    for path in LEAN.glob("*.cs"):
        source = path.read_text(encoding="utf-8").lower()
        assert "using mamba2." not in source
        assert "mamba2.indicators" not in source
        assert "mamba2.strategy" not in source


def test_csv_parser_has_utc_bar_time_and_daily_date_guard():
    source = DATA.read_text(encoding="utf-8")
    for fragment in (
        "FromUnixTimeSeconds", "timestamp.Date != date.Date",
        "result.Time = timestamp", "result.EndTime = timestamp.AddMinutes",
        "result.Value = close", "SubscriptionTransportMedium.LocalFile",
        '"M1_ASK"', '"M5"',
    ):
        assert fragment in source


def test_independent_candidate_comparator_is_strictly_observation_only():
    source = ALGORITHM.read_text(encoding="utf-8")
    # The first parity gate compares raw candidates and indicators, not fills.
    for disallowed in (
        "MarketOrder(", "LimitOrder(", "StopMarketOrder(",
        "OnOrderEvent(", "SetHoldings(", "Liquidate(", "OrderTicket",
    ):
        assert disallowed not in source
    assert 'mode = "independent_candidate_signal_parity_only"' in source
    assert "execution_comparison_ready = false" in source
    assert "actual_submits = 0" in source


def test_exact_one_day_boundary_and_full_prefix_notional_guard():
    source = ALGORITHM.read_text(encoding="utf-8")
    assert "boundary <= SealedStart" in source
    assert "boundary > SealedEnd" in source
    assert "_boundaryCount != 1440" in source
    assert "_sampleM1Count != 1440" in source
    assert "_sampleM5Count != 288" in source
    assert "_sampleAskCount != 1440" in source
    assert "SealedStart.AddMinutes(1)" in source
    assert "_lastBoundary != DateTime.MinValue && boundary != _lastBoundary.AddMinutes(1)" in source
    assert "canonical_m5_direct = true" in source


def test_incremental_indicators_and_sealed_input_contract():
    source = ALGORITHM.read_text(encoding="utf-8")
    for fragment in (
        "class StochasticState", "class AtrState", "private decimal _ema",
        "0.25m * m1.Close + 0.75m * _ema",
        "21 + 7 + 7", "RecentK.Any(k => k < 20m)",
        "RecentK.Any(k => k > 80m)", "Value = total / 14m",
        "ValidateSource(", "ExpectedM1Sha256", "ExpectedM1AskSha256",
        "ExpectedM5Sha256", "ObjectStore.ContainsKey", "SaveExclusive",
    ):
        assert fragment in source
    # There must be no per-boundary full-history stochastic recalculation.
    assert "Stochastic(m1)" not in source
    assert "_m5.Select(" not in source


def test_common_comparison_keys_and_outputs_are_present():
    source = ALGORITHM.read_text(encoding="utf-8")
    for field in (
        "utc_time_ms", "m1_source_open_utc", "m5_source_open_utc",
        "m1_k", "m1_d", "m5_k", "m5_d", "ema", "atr",
        "candidate_signal", "reason_or_error_code", "blocked_by_position",
        "indicator_trace.jsonl", "events.jsonl", "input_manifest.json",
        "summary.json", "m030.events.v1",
    ):
        assert field in source
