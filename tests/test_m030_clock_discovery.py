"""Synthetic no-trade fixtures for Stage 1H clock discovery."""
import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from mamba2.backtest.m030_clock_discovery import discover_clock_offset


START = datetime(2026, 9, 10, tzinfo=timezone.utc)
END = START + timedelta(minutes=10)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture(tmp_path, *, offset=180, omit_m5=False, m5_bad=False,
                   second_offset=None, duplicate=False, epoch_seconds=False):
    m1 = tmp_path / "M1.csv"
    m5 = tmp_path / "M5.csv"
    probe = tmp_path / "probe.csv"
    header = "time,open,high,low,close\n"
    m1_rows = []
    m5_rows = []
    samples = []
    # Distinct OHLC per bar makes accidental time-offset collision visible.
    for i in range(10):
        stamp = START + timedelta(minutes=i)
        price = 1.10000 + i * 0.0001
        m1_rows.append((stamp, price, price + .0002, price - .0002, price))
        if i in (0, 5):
            m5_rows.append((stamp, price + .001, price + .002,
                            price - .001, price + .001))
    def label(t):
        return t.strftime("%Y.%m.%d %H:%M:%S")
    def write_source(path, rows):
        path.write_text(header + "".join(
            f"{int(t.timestamp()) if epoch_seconds else t.isoformat().replace('+00:00','Z')},{o:.5f},{h:.5f},{l:.5f},{c:.5f}\n"
            for t,o,h,l,c in rows), encoding="utf-8")
    write_source(m1, m1_rows)
    write_source(m5, m5_rows)
    for shift in ([offset] if second_offset is None else [offset, second_offset]):
        for tf, rows in (("M1", m1_rows), ("M5", m5_rows)):
            for t, o, h, l, c in rows:
                if omit_m5 and tf == "M5" and t == START + timedelta(minutes=5):
                    continue
                boundary = t + timedelta(minutes=1 if tf == "M1" else 5)
                raw_open = t.replace(tzinfo=None) + timedelta(minutes=shift)
                raw_boundary = boundary.replace(tzinfo=None) + timedelta(minutes=shift)
                raw_tick = raw_boundary + timedelta(seconds=2)
                if m5_bad and tf == "M5":
                    h += .001
                samples.append((raw_open, f"test,EURUSD,{tf},{label(raw_boundary)},"
                                f"{label(raw_tick)},{label(raw_open)},"
                                f"{o:.5f},{h:.5f},{l:.5f},{c:.5f}\n"))
    samples.sort(key=lambda item: (item[0], item[1]))
    if duplicate:
        samples.append(samples[0])
    probe.write_text(
        "run_id,symbol,timeframe,server_m1_boundary,server_observed_tick,"
        "server_bar_open,open,high,low,close\n" +
        "".join(row for _,row in samples), encoding="utf-8")
    return probe,m1,m5, {"probe":_hash(probe),"M1":_hash(m1),"M5":_hash(m5)}


def _discover(files, *, candidates=range(-240,241,15),
              reference_timestamp_format="iso8601_utc"):
    probe,m1,m5,hashes = files
    return discover_clock_offset(
        probe,m1,m5,run_id="test",expected_sha256=hashes,
        window_start=START,window_end=END,
        expected_counts={"M1":10,"M5":2},
        candidate_offsets_minutes=candidates,
        reference_timestamp_format=reference_timestamp_format)


def test_unique_clock_mapping_requires_both_timeframes(tmp_path):
    result = _discover(_write_fixture(tmp_path,offset=180))
    assert result["status"] == "UNIQUE"
    assert result["offset_minutes"] == 180
    assert result["expected_rows"] == {"M1": 10, "M5": 2}


def test_missing_m5_bar_fails_full_coverage(tmp_path):
    result = _discover(_write_fixture(tmp_path,omit_m5=True))
    assert result["status"] == "NO_MATCH"


def test_matching_m1_but_different_m5_ohlc_rejected(tmp_path):
    result = _discover(_write_fixture(tmp_path,m5_bad=True))
    assert result["status"] == "NO_MATCH"


def test_second_valid_offset_is_ambiguous(tmp_path):
    result = _discover(_write_fixture(tmp_path,offset=60,second_offset=180))
    assert result["status"] == "AMBIGUOUS"
    assert result["matching_candidates"] == [60,180]


def test_hash_mismatch_rejected(tmp_path):
    files = _write_fixture(tmp_path)
    probe,m1,m5,hashes = files
    m1.write_text(m1.read_text() + "\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _discover(files)


def test_duplicate_native_bar_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate or reversed native bar"):
        _discover(_write_fixture(tmp_path,duplicate=True))


def test_missing_reference_rows_rejected(tmp_path):
    files = _write_fixture(tmp_path)
    probe,m1,m5,hashes = files
    with pytest.raises(ValueError, match="incomplete canonical"):
        discover_clock_offset(
            probe,m1,m5,run_id="test",expected_sha256=hashes,
            window_start=START,window_end=END,
            expected_counts={"M1":1440,"M5":288},
            candidate_offsets_minutes=(180,))


def test_canonical_epoch_seconds_without_rewriting_files(tmp_path):
    files = _write_fixture(tmp_path, offset=180, epoch_seconds=True)
    result = _discover(files, reference_timestamp_format="unix_seconds_utc")
    assert result["status"] == "UNIQUE"
    assert result["offset_minutes"] == 180
    with pytest.raises(ValueError, match="invalid UTC timestamp"):
        _discover(files)


def test_reference_format_must_be_explicit_and_valid(tmp_path):
    files = _write_fixture(tmp_path, epoch_seconds=True)
    with pytest.raises(ValueError, match="reference timestamp format"):
        _discover(files, reference_timestamp_format="auto")


def test_epoch_seconds_refuses_misaligned_or_fractional_time(tmp_path):
    files = _write_fixture(tmp_path, epoch_seconds=True)
    probe, m1, m5, hashes = files
    old = m1.read_text()
    first = str(int(START.timestamp()))
    for replacement, message in ((str(int(START.timestamp()) + 1), "minute-aligned"),
                                 (first + ".5", "integer epoch second")):
        m1.write_text(old.replace(first, replacement, 1), encoding="utf-8")
        updated = {**hashes, "M1": _hash(m1)}
        with pytest.raises(ValueError, match=message):
            discover_clock_offset(
                probe, m1, m5, run_id="test", expected_sha256=updated,
                window_start=START, window_end=END,
                expected_counts={"M1": 10, "M5": 2},
                candidate_offsets_minutes=(180,),
                reference_timestamp_format="unix_seconds_utc")
