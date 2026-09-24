"""Tests for read-only MT5 history export and verified dataset loading."""

from types import SimpleNamespace

import pandas as pd
import pytest

from mamba2.backtest.mt5_dataset import (
    DatasetIntegrityError,
    _mt5_initialize_kwargs,
    export_mt5_dataset,
    load_mt5_dataset,
)


class FakeMT5:
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15

    def __init__(self):
        self._bars = {
            1: self._make_bars("2025-01-02 10:00", 16, "1min", 1.1000),
            5: self._make_bars("2025-01-02 10:00", 4, "5min", 1.2000),
            15: self._make_bars("2025-01-02 10:00", 2, "15min", 1.3000),
        }

    @staticmethod
    def _make_bars(start, count, freq, base):
        times = pd.date_range(start, periods=count, freq=freq, tz="UTC")
        rows = []
        for index, timestamp in enumerate(times):
            price = base + index * 0.001
            rows.append(
                {
                    "time": int(timestamp.timestamp()),
                    "open": price,
                    "high": price + 0.0008,
                    "low": price - 0.0004,
                    "close": price + 0.0002,
                    "tick_volume": 10 + index,
                    "spread": 12,
                    "real_volume": 0,
                }
            )
        return rows

    def account_info(self):
        return SimpleNamespace(currency="USD", server="Example-Demo")

    def version(self):
        return (500, 6180, "test")

    def symbol_select(self, symbol, enable=True):
        return symbol == "EURUSD" and enable

    def symbol_info(self, symbol):
        if symbol != "EURUSD":
            return None
        return SimpleNamespace(
            digits=5,
            point=0.00001,
            trade_contract_size=100000.0,
            currency_base="EUR",
            currency_profit="USD",
            currency_margin="EUR",
        )

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        assert symbol == "EURUSD"
        assert date_from.tzinfo is not None
        assert date_to.tzinfo is not None
        return self._bars[timeframe]


def export_fixture(tmp_path):
    return export_mt5_dataset(
        FakeMT5(),
        symbols=["EURUSD"],
        timeframes=["M1", "M5", "M15"],
        start_utc="2025-01-02T10:00:00Z",
        end_utc="2025-01-02T10:15:00Z",
        output_dir=tmp_path,
        exported_at_utc="2025-01-03T00:00:00Z",
        history_sync_wait_seconds=0,
    )


def test_export_manifest_filters_incomplete_bars_and_records_checksums(tmp_path):
    manifest_path = export_fixture(tmp_path)
    loaded = load_mt5_dataset(manifest_path)

    manifest = loaded.manifest
    assert manifest["timestamp_semantics"] == "bar_open_utc"
    assert manifest["availability_rule"] == "bar_open + timeframe <= replay_time"
    assert manifest["account_currency"] == "USD"
    assert manifest["broker_server"] == "Example-Demo"

    files = manifest["symbols"]["EURUSD"]["files"]
    assert files["M1"]["rows"] == 15
    assert files["M5"]["rows"] == 3
    assert files["M15"]["rows"] == 1
    assert files["M15"]["last_bar_available_utc"] == "2025-01-02T10:15:00Z"
    assert all(len(entry["sha256"]) == 64 for entry in files.values())


def test_verified_loader_returns_native_timeframes_and_execution_metadata(tmp_path):
    dataset = load_mt5_dataset(export_fixture(tmp_path))

    assert list(dataset.m1_bars) == ["EURUSD"]
    assert set(dataset.native_timeframe_bars["EURUSD"]) == {"M5", "M15"}
    assert dataset.native_timeframe_bars["EURUSD"]["M5"].iloc[0]["open"] == pytest.approx(1.2)

    metadata = dataset.symbol_metadata["EURUSD"]
    assert metadata.point_size == pytest.approx(0.00001)
    assert metadata.digits == 5
    assert metadata.contract_size == pytest.approx(100000.0)
    assert metadata.quote_currency == "USD"


def test_loader_rejects_tampered_csv(tmp_path):
    manifest_path = export_fixture(tmp_path)
    csv_path = tmp_path / "EURUSD_M1.csv"
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="checksum mismatch"):
        load_mt5_dataset(manifest_path)


def test_exporter_surface_is_read_only_by_construction(tmp_path):
    # FakeMT5 intentionally implements only read-only market-data/metadata calls.
    # The export succeeds, proving no order-management API is required.
    manifest_path = export_fixture(tmp_path)
    assert manifest_path.is_file()


def test_mt5_initialize_kwargs_allow_existing_terminal_session():
    config = SimpleNamespace(
        login=None,
        password="",
        server="",
        path="",
        timeout=60000,
        portable=False,
    )

    assert _mt5_initialize_kwargs(config) == {
        "timeout": 60000,
        "portable": False,
    }


def test_mt5_initialize_kwargs_require_complete_explicit_credentials():
    partial = SimpleNamespace(
        login=123456,
        password="",
        server="Example-Demo",
        path="",
        timeout=60000,
        portable=False,
    )
    with pytest.raises(RuntimeError, match="partial environment configuration"):
        _mt5_initialize_kwargs(partial)

    complete = SimpleNamespace(
        login=123456,
        password="placeholder-secret",
        server="Example-Demo",
        path=r"C:\\Example\\terminal64.exe",
        timeout=45000,
        portable=True,
    )
    kwargs = _mt5_initialize_kwargs(complete)

    assert kwargs == {
        "path": r"C:\\Example\\terminal64.exe",
        "login": 123456,
        "password": "placeholder-secret",
        "server": "Example-Demo",
        "timeout": 45000,
        "portable": True,
    }


class SyncingFakeMT5(FakeMT5):
    def __init__(self):
        super().__init__()
        self._synced = set()
        self.range_calls = {1: 0, 5: 0, 15: 0}
        self.warmup_calls = []

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        self.range_calls[timeframe] += 1
        if timeframe not in self._synced:
            return []
        return super().copy_rates_range(symbol, timeframe, date_from, date_to)

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        assert symbol == "EURUSD"
        assert start_pos == 0
        self.warmup_calls.append((timeframe, count))
        self._synced.add(timeframe)
        return self._bars[timeframe]


def test_exporter_warms_empty_mt5_history_once_then_retries_exact_range(tmp_path):
    mt5 = SyncingFakeMT5()
    manifest_path = export_mt5_dataset(
        mt5,
        symbols=["EURUSD"],
        timeframes=["M1", "M5", "M15"],
        start_utc="2025-01-02T10:00:00Z",
        end_utc="2025-01-02T10:15:00Z",
        output_dir=tmp_path,
        exported_at_utc="2025-01-03T00:00:00Z",
        history_warmup_count=321,
        history_sync_wait_seconds=0,
    )

    manifest = load_mt5_dataset(manifest_path).manifest
    files = manifest["symbols"]["EURUSD"]["files"]

    assert mt5.warmup_calls == [(1, 321), (5, 321), (15, 321)]
    assert mt5.range_calls == {1: 2, 5: 2, 15: 2}
    assert all(files[timeframe]["history_sync_retry"] is True for timeframe in files)


def test_exporter_skips_history_warmup_when_range_is_already_available(tmp_path):
    mt5 = FakeMT5()
    manifest_path = export_mt5_dataset(
        mt5,
        symbols=["EURUSD"],
        timeframes=["M1", "M5", "M15"],
        start_utc="2025-01-02T10:00:00Z",
        end_utc="2025-01-02T10:15:00Z",
        output_dir=tmp_path,
        exported_at_utc="2025-01-03T00:00:00Z",
        history_sync_wait_seconds=0,
    )

    manifest = load_mt5_dataset(manifest_path).manifest
    assert all(
        entry["history_sync_retry"] is False
        for entry in manifest["symbols"]["EURUSD"]["files"].values()
    )
