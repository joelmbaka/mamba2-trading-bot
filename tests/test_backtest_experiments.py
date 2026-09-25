"""Control-gate and single-treatment tests for the M020 experiment harness."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from mamba2.backtest import experiments


def test_verify_control_hashes_requires_both_artifacts():
    result = {
        "baseline_sha256": "baseline",
        "diagnostic_sha256": "diagnostic",
    }

    accepted = experiments.verify_control_hashes(
        result,
        expected_baseline_sha256="baseline",
        expected_diagnostic_sha256="diagnostic",
    )
    assert accepted["ok"] is True
    assert accepted["baseline_preserved"] is True
    assert accepted["diagnostic_preserved"] is True

    rejected = experiments.verify_control_hashes(
        result,
        expected_baseline_sha256="different",
        expected_diagnostic_sha256="diagnostic",
    )
    assert rejected["ok"] is False
    assert rejected["baseline_preserved"] is False
    assert rejected["diagnostic_preserved"] is True


def test_control_arm_uses_unmodified_diagnostic_baseline(monkeypatch, tmp_path):
    baseline = {
        "aggregate": {
            "accepted_orders": 1,
            "closed_trades": 1,
        }
    }
    diagnostic = {
        "diagnostic_schema_version": 1,
        "source_baseline_sha256": None,
    }

    calls = []

    def fake_run(manifest_path, *, starting_balance):
        calls.append((Path(manifest_path), starting_balance))
        return baseline, diagnostic

    monkeypatch.setattr(experiments, "run_diagnostic_baseline", fake_run)

    result = experiments.run_control_arm(
        tmp_path / "manifest.json",
        baseline_output=tmp_path / "baseline.json",
        diagnostic_output=tmp_path / "diagnostic.json",
        starting_balance=12_345.0,
    )

    assert calls == [(tmp_path / "manifest.json", 12_345.0)]
    assert result["arm"] == "control"
    assert result["experiment_id"] == "M020-A"
    assert diagnostic["source_baseline_sha256"] == result["baseline_sha256"]
    assert Path(result["baseline_path"]).is_file()
    assert Path(result["diagnostic_path"]).is_file()



class _RecordingStrategy:
    def __init__(self):
        self.symbol = "EURUSD"
        self.calls = []

    async def evaluate(self, market):
        self.calls.append(market["rate_fetcher"].current_time)


def test_m020a_filter_blocks_only_0000_through_0359_utc():
    strategy = _RecordingStrategy()
    wrapper = experiments.UtcEntrySessionFilterStrategy(strategy)
    fetcher = SimpleNamespace(current_time=None)
    market = {"rate_fetcher": fetcher}

    for timestamp in (
        "2026-09-01T23:59:00Z",
        "2026-09-02T00:00:00Z",
        "2026-09-02T03:59:00Z",
        "2026-09-02T04:00:00Z",
    ):
        fetcher.current_time = pd.Timestamp(timestamp)
        asyncio.run(wrapper.evaluate(market))

    assert strategy.calls == [
        pd.Timestamp("2026-09-01T23:59:00Z"),
        pd.Timestamp("2026-09-02T04:00:00Z"),
    ]
    assert wrapper.blocked_evaluation_boundaries == 2


def test_m020a_filter_preserves_symbol_and_rejects_invalid_window():
    strategy = _RecordingStrategy()
    wrapper = experiments.UtcEntrySessionFilterStrategy(strategy)
    assert wrapper.symbol == "EURUSD"

    for kwargs in (
        {"start_hour": -1, "end_hour": 4},
        {"start_hour": 0, "end_hour": 25},
        {"start_hour": 4, "end_hour": 4},
    ):
        try:
            experiments.UtcEntrySessionFilterStrategy(strategy, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid session window must be rejected")


def test_treatment_arm_uses_only_m020a_strategy_transform(monkeypatch, tmp_path):
    baseline = {
        "aggregate": {
            "accepted_orders": 1,
            "closed_trades": 1,
        }
    }
    diagnostic = {
        "diagnostic_schema_version": 1,
        "source_baseline_sha256": None,
    }
    captured = {}

    def fake_run(
        manifest_path,
        *,
        starting_balance,
        strategy_transform=None,
    ):
        captured["manifest"] = Path(manifest_path)
        captured["starting_balance"] = starting_balance
        fake_strategy = _RecordingStrategy()
        wrapped = strategy_transform(fake_strategy)
        captured["wrapped"] = wrapped
        wrapped.blocked_evaluation_boundaries = 7
        return baseline, diagnostic

    monkeypatch.setattr(experiments, "run_diagnostic_baseline", fake_run)

    result = experiments.run_m020a_treatment_arm(
        tmp_path / "manifest.json",
        baseline_output=tmp_path / "treatment-baseline.json",
        diagnostic_output=tmp_path / "treatment-diagnostic.json",
    )

    assert captured["manifest"] == tmp_path / "manifest.json"
    assert captured["starting_balance"] == 10_000.0
    assert isinstance(
        captured["wrapped"],
        experiments.UtcEntrySessionFilterStrategy,
    )
    assert result["arm"] == "m020-a-treatment"
    assert result["blocked_evaluation_boundaries"] == 7
    assert result["treatment"] == {
        "blocked_utc_start": "00:00:00",
        "blocked_utc_end_exclusive": "04:00:00",
        "behavior": "suppress new-entry strategy evaluation only",
    }
