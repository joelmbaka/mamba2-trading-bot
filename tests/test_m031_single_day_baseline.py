"""Synthetic, non-economic M031 baseline contract tests."""

import json

import pandas as pd
import pytest

from mamba2.backtest.m031_single_day_baseline import (
    BaselineInputError,
    _indicator_trace_record,
    _decision_boundaries,
    _utc,
    _validate_source_arguments,
    _write_exclusive,
)
from mamba2.backtest.mt5_dataset import LoadedHistoricalDataset


def _bars():
    index = pd.date_range("2026-09-10 00:00", periods=3, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [1.1, 1.101, 1.102],
            "high": [1.101, 1.102, 1.103],
            "low": [1.099, 1.100, 1.101],
            "close": [1.1005, 1.1015, 1.1025],
            "tick_volume": [1, 1, 1],
            "spread": [2, 2, 2],
            "real_volume": [0, 0, 0],
        },
        index=index,
    )
    return frame


def test_utc_requires_explicit_z_suffix():
    assert _utc("2026-09-10T00:00:00Z") == pd.Timestamp("2026-09-10T00:00:00Z")
    with pytest.raises(BaselineInputError):
        _utc("2026-09-10T00:00:00+00:00")


def test_decision_boundaries_are_next_minute_and_include_end():
    boundaries = _decision_boundaries(
        pd.Timestamp("2026-09-10T00:00:00Z"),
        pd.Timestamp("2026-09-11T00:00:00Z"),
    )
    assert len(boundaries) == 1440
    assert boundaries[0] == pd.Timestamp("2026-09-10T00:01:00Z")
    assert boundaries[-1] == pd.Timestamp("2026-09-11T00:00:00Z")


def test_blocked_candidate_is_observation_not_signal():
    observation = {
        "schema_version": "m030.events.v1",
        "source_engine": "python",
        "event_kind": "SIGNAL",
        "signal": "BUY",
        "m1_k": 25.0,
    }
    record = _indicator_trace_record(observation, blocked_by_position=True)
    assert record["record_type"] == "indicator_observation"
    assert record["candidate_signal"] == "BUY"
    assert record["signal"] == "NONE"
    assert "schema_version" not in record
    assert "event_kind" not in record


def test_output_writer_is_immutable(tmp_path):
    path = tmp_path / "summary.json"
    _write_exclusive(path, json.dumps({"schema_version": 1}) + "\n")
    with pytest.raises(FileExistsError):
        _write_exclusive(path, "{}\n")


def test_input_validator_requires_manifest_referenced_paths(tmp_path, monkeypatch):
    root = tmp_path / "dataset"
    root.mkdir()
    manifest_path = root / "manifest.json"
    m1_path = root / "EURUSD_M1.csv"
    ask_path = root / "EURUSD_M1_ask.csv"
    m5_path = root / "EURUSD_M5.csv"
    for path in (m1_path, ask_path, m5_path):
        path.write_text("synthetic\n", encoding="utf-8")

    manifest = {
        "schema_version": 2,
        "source": "MetaTrader5",
        "timestamp_semantics": "bar_open_utc",
        "account_currency": "USD",
        "symbols": {
            "EURUSD": {
                "point": 0.00001,
                "digits": 5,
                "contract_size": 100000,
                "quote_currency": "USD",
                "files": {
                    "M1": {"path": m1_path.name},
                    "M5": {"path": m5_path.name},
                },
                "ask_m1": {"path": ask_path.name, "source": "copy_ticks_range"},
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    dataset = LoadedHistoricalDataset(
        m1_bars={"EURUSD": _bars()},
        native_timeframe_bars={"EURUSD": {"M5": _bars()}},
        ask_m1_bars={"EURUSD": _bars().loc[:, ["open", "high", "low", "close"]]},
        symbol_metadata={},
        account_currency="USD",
        manifest=manifest,
    )
    monkeypatch.setattr(
        "mamba2.backtest.m031_single_day_baseline.load_mt5_dataset",
        lambda _path: dataset,
    )

    with pytest.raises(BaselineInputError, match="manifest hash mismatch"):
        _validate_source_arguments(
            manifest_path,
            m1_path,
            ask_path,
            m5_path,
            expected_manifest_sha256="wrong",
        )
