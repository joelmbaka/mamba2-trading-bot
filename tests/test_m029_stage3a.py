"""Stage 3A mock-only checks: no external IO, MT5 or paper decisions."""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from mamba2.backtest.m027_carry_aware_tsmom import BIS_XRU_URL, OECD_STIR_URL
from mamba2.backtest.m028_forward_paper import M028_FIXED_MAPPING
from mamba2.backtest.m029_stage3a import (
    EvidenceRefused,
    check_isolated_runtime_manifest,
    metadata_rehearsal,
)


OPEN = datetime(2026, 12, 7, 12, tzinfo=timezone.utc)
CLOSE = datetime(2026, 12, 7, 12, 10, tzinfo=timezone.utc)
TICK = datetime(2026, 12, 7, 12, 1, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


class Clock:
    def __init__(self, at=TICK):
        self.at = at
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.at


class MockBroker:
    def __init__(self, tick_time=TICK):
        self.calls = []
        self.tick_time = tick_time
        self.changed_symbol = None
        self.bad_margin = None
        self.on_info = None

    def symbol_info(self, symbol):
        self.calls.append(("symbol_info", symbol))
        if self.on_info is not None:
            self.on_info()
        return {
            "symbol": self.changed_symbol if symbol == "AUDUSD" and self.changed_symbol else symbol,
            "contract_size": 100000.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
        }

    def symbol_info_tick(self, symbol):
        self.calls.append(("symbol_info_tick", symbol))
        return {
            "bid": 1.0, "ask": 1.0001,
            "quote_timestamp_utc": iso(self.tick_time),
        }

    def order_calc_margin(self, side, symbol, lots, price):
        self.calls.append(("order_calc_margin", side, symbol, lots, price))
        assert side in ("BUY", "SELL")
        assert lots == 1.0
        if symbol == self.bad_margin:
            return None
        return 1000.0


def bis_parse(_raw):
    return pd.DataFrame(
        {"AUD": [1.0]},
        index=pd.DatetimeIndex(["2026-11-30"], tz="UTC"),
    )


def oecd_parse(_raw):
    return pd.DataFrame(
        {"USA": [3.0]},
        index=pd.period_range("2026-10", periods=1, freq="M"),
    )


class Download:
    def __init__(self, clock=None, after=None):
        self.calls = []
        self.clock = clock
        self.after = after

    def __call__(self, url):
        self.calls.append(url)
        if self.after is not None:
            self.after(url)
        if url == BIS_XRU_URL:
            return b"synthetic BIS bytes"
        if url == OECD_STIR_URL:
            return b"synthetic OECD bytes"
        raise AssertionError("unexpected download URL")


def run(clock=None, download=None, broker=None, month="2026-12",
        bis_parser=bis_parse, oecd_parser=oecd_parse):
    clock = clock or Clock()
    download = download or Download()
    broker = broker or MockBroker()
    return metadata_rehearsal(
        month,
        clock=clock,
        downloader=download,
        broker=broker,
        bis_parser=bis_parser,
        oecd_parser=oecd_parser,
    )


def test_mock_readiness_records_two_source_provenances_and_eight_symbols():
    clock = Clock()
    download = Download()
    broker = MockBroker()
    result = run(clock, download, broker)
    assert result["readiness_only"] is True
    assert result["classification"] == "METADATA_READY_ONLY"
    assert result["source_gate_pass"] is True
    assert result["broker_gate_pass"] is True
    assert result["broker"]["viable_count"] == 8
    assert result["safety"]["strategy_signal_computed"] is False
    assert result["safety"]["target_lots_computed"] is False
    assert result["safety"]["paper_decision_written"] is False
    assert download.calls == [BIS_XRU_URL, OECD_STIR_URL]
    assert set(row["symbol"] for row in result["broker"]["currencies"].values()) == set(
        M028_FIXED_MAPPING.values()
    )
    assert len(broker.calls) == 8 * 4
    assert {x[0] for x in broker.calls} == {
        "symbol_info", "symbol_info_tick", "order_calc_margin"
    }
    assert result["source"]["BIS"]["raw_sha256"]
    assert result["source"]["OECD"]["normalized_sha256"]
    assert result["source"]["required_spot_through"] == "2026-11-30"
    assert result["source"]["required_rate_month"] == "2026-10"
    assert all(
        row["quote_observed_at_utc"] == iso(TICK)
        and row["quote_timestamp_utc"] == iso(TICK)
        for row in result["broker"]["currencies"].values()
    )


@pytest.mark.parametrize(("month", "at", "code"), [
    ("2026-10", OPEN, "INELIGIBLE_HISTORICAL_MONTH"),
    ("2026-11", OPEN, "INELIGIBLE_HISTORICAL_MONTH"),
    ("2026-12", OPEN - timedelta(seconds=1), "WINDOW_NOT_OPEN"),
    ("2026-12", CLOSE, "MISSED_WINDOW"),
    ("2026-12", CLOSE + timedelta(seconds=1), "MISSED_WINDOW"),
])
def test_scheduler_dryrun_refuses_before_any_source_or_broker_call(month, at, code):
    clock = Clock(at)
    downloader = Download()
    broker = MockBroker()
    with pytest.raises(EvidenceRefused, match=code):
        run(clock, downloader, broker, month=month)
    assert downloader.calls == []
    assert broker.calls == []


def test_source_download_crossing_close_aborts_immediately():
    clock = Clock(CLOSE - timedelta(microseconds=1))
    def crossed(_url):
        clock.at = CLOSE
    download = Download(after=crossed)
    broker = MockBroker()
    with pytest.raises(EvidenceRefused, match="MISSED_WINDOW"):
        run(clock, download, broker)
    assert download.calls == [BIS_XRU_URL]
    assert broker.calls == []


def test_broker_crossing_close_aborts_before_margin_calls():
    clock = Clock(CLOSE - timedelta(microseconds=1))
    broker = MockBroker(tick_time=CLOSE - timedelta(seconds=5))
    broker.on_info = lambda: setattr(clock, "at", CLOSE)
    with pytest.raises(EvidenceRefused, match="MISSED_WINDOW"):
        run(clock, Download(), broker)
    assert len(broker.calls) == 1


def test_collect_actual_elapsed_timestamps_not_supplied_decision_time():
    clock = Clock(OPEN)
    def increase(_url):
        clock.at += timedelta(seconds=20)
    capture = run(clock, Download(after=increase))
    bis = capture["source"]["BIS"]
    oecd = capture["source"]["OECD"]
    assert bis["fetch_started_at_utc"] == iso(OPEN)
    assert bis["fetch_finished_at_utc"] == iso(OPEN + timedelta(seconds=20))
    assert oecd["fetch_started_at_utc"] == iso(OPEN + timedelta(seconds=20))
    assert oecd["fetch_finished_at_utc"] == iso(OPEN + timedelta(seconds=40))
    assert capture["broker"]["query_started_at_utc"] == iso(
        OPEN + timedelta(seconds=40)
    )


def test_broker_refuses_pre_window_tick_even_if_under_five_minutes():
    clock = Clock(OPEN + timedelta(seconds=30))
    result = run(clock, broker=MockBroker(tick_time=OPEN - timedelta(seconds=1)))
    assert result["classification"] == "BROKER_NOT_READY"
    assert result["broker"]["viable_count"] == 0


def test_broker_refuses_future_or_stale_tick():
    future = run(broker=MockBroker(tick_time=TICK + timedelta(seconds=1)))
    assert future["broker"]["viable_count"] == 0
    stale = run(
        clock=Clock(OPEN + timedelta(minutes=9)),
        broker=MockBroker(tick_time=OPEN + timedelta(seconds=1))
    )
    assert stale["broker"]["viable_count"] == 0


def test_wrong_broker_symbol_and_missing_margin_cannot_be_viable():
    broker = MockBroker()
    broker.changed_symbol = "EURUSD"
    broker.bad_margin = "USDSEK"
    result = run(broker=broker)
    assert result["broker"]["viable_count"] == 6
    assert result["broker"]["currencies"]["AUD"]["quote_viable"] is False
    assert result["broker"]["currencies"]["SEK"]["quote_viable"] is False


def test_under_four_quotes_results_in_broker_not_ready():
    class Partial(MockBroker):
        def symbol_info(self, symbol):
            if symbol not in list(M028_FIXED_MAPPING.values())[:3]:
                return None
            return super().symbol_info(symbol)
    result = run(broker=Partial())
    assert result["classification"] == "BROKER_NOT_READY"
    assert result["broker"]["viable_count"] == 3


def test_incomplete_month_is_metadata_not_ready_without_signal():
    def old_bis(raw):
        return pd.DataFrame(
            {"AUD": [1.0]},
            index=pd.DatetimeIndex(["2026-11-27"], tz="UTC"),
        )
    result = run(bis_parser=old_bis)
    assert result["classification"] == "SOURCE_NOT_READY"
    assert result["safety"]["strategy_signal_computed"] is False


def test_empty_or_missing_source_cannot_be_treated_as_paper_not_ready():
    def missing(_):
        return b""
    with pytest.raises(EvidenceRefused, match="SOURCE_BYTES_UNAVAILABLE"):
        run(download=missing)
    with pytest.raises(EvidenceRefused, match="SOURCE_PANEL_EMPTY"):
        run(bis_parser=lambda raw: pd.DataFrame())


def test_parser_exception_aborts_before_broker_or_strategy():
    broker = MockBroker()
    def broken_parser(raw):
        raise ValueError("synthetic decode failure")
    with pytest.raises(ValueError, match="synthetic decode failure"):
        run(broker=broker, bis_parser=broken_parser)
    assert broker.calls == []


def test_naive_or_backward_clock_aborts():
    with pytest.raises(EvidenceRefused, match="CLOCK_NOT_UTC_AWARE"):
        run(clock=lambda: datetime(2026, 12, 7, 12))

    clock = Clock(OPEN + timedelta(seconds=20))
    def reversed_time(_url):
        clock.at = OPEN + timedelta(seconds=10)
    with pytest.raises(EvidenceRefused, match="CLOCK_MOVED_BACKWARD"):
        run(clock=clock, download=Download(after=reversed_time))


def test_runtime_manifest_refuses_shared_original_prefix():
    good = check_isolated_runtime_manifest(
        wine_binary="/opt/wine-11.21/bin/wine",
        wine_prefix="/tmp/isolated-m029-prefix",
        system_wine_binary="/usr/bin/wine",
        original_prefix="/home/example/.mt5",
        bridge_python="/tmp/isolated-m029-prefix/drive_c/Python310/python.exe",
    )
    assert good["python_import_tested"] is False
    assert good["runtime_executed"] is False
    with pytest.raises(EvidenceRefused, match="ISOLATION_NOT_PROVEN"):
        check_isolated_runtime_manifest(
            wine_binary="/usr/bin/wine",
            wine_prefix="/home/example/.mt5",
            system_wine_binary="/usr/bin/wine",
            original_prefix="/home/example/.mt5",
            bridge_python="/tmp/py",
        )
