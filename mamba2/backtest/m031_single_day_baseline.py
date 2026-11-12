"""Fail-closed, source-only one-day M031 baseline.

This module deliberately does not derive M5 from M1.  It loads the sealed
canonical M1, minute Ask, and native M5 files, fast-forwards the replay clock
without evaluating the strategy, and evaluates only the selected day's
completed-M1 boundaries.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import pandas as pd

from config import config
from mamba2.crew.position_manager import PositionManager
from mamba2.indicators.atr import get_atr
from mamba2.backtest.broker import ExecutionCostModel, HistoricalBroker
from mamba2.backtest.feed import ReplayFeed
from mamba2.backtest.m030_parity import EventSink, event, utc_millis
from mamba2.backtest.m030_signal_observer import observe_candidate
from mamba2.backtest.mt5_dataset import (
    DatasetIntegrityError,
    load_mt5_dataset,
)
from mamba2.backtest.runner import BacktestBrokerAdapter
from mamba2.strategy.triple_cross import StochasticTripleTFStrategy


EXPECTED_MANIFEST_SHA256 = (
    "cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b"
)
EXPECTED_FILE_SHA256 = {
    "m1": "19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe",
    "m1_ask": "7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c",
    "m5": "c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9",
}
EXPECTED_ROWS = {"m1": 405283, "m1_ask": 405283, "m5": 81036}
EXPECTED_START = pd.Timestamp("2026-09-10T00:00:00Z")
EXPECTED_END = pd.Timestamp("2026-09-11T00:00:00Z")


class BaselineInputError(DatasetIntegrityError):
    """Raised before any replay when the sealed input contract fails."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc(value: str) -> pd.Timestamp:
    if not value.endswith("Z"):
        raise BaselineInputError("timestamps must be explicit UTC ISO values ending in Z")
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise BaselineInputError("timestamps must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _iso(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _write_exclusive(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def _repo_head() -> str | None:
    """Return the checked-out commit without making it an input dependency."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def _validate_source_arguments(
    manifest_path: Path,
    m1_path: Path,
    ask_path: Path,
    m5_path: Path,
    *,
    expected_manifest_sha256: str = EXPECTED_MANIFEST_SHA256,
    expected_file_sha256: Mapping[str, str] = EXPECTED_FILE_SHA256,
    expected_rows: Mapping[str, int] = EXPECTED_ROWS,
) -> tuple[Any, dict[str, Any]]:
    """Validate hashes, manifest references, and canonical row metadata."""
    paths = {
        "manifest": manifest_path,
        "m1": m1_path,
        "m1_ask": ask_path,
        "m5": m5_path,
    }
    for label, path in paths.items():
        if not path.is_file():
            raise BaselineInputError(f"missing {label} source: {path}")

    actual_manifest_hash = _sha256(manifest_path)
    if actual_manifest_hash != expected_manifest_sha256:
        raise BaselineInputError(
            f"manifest hash mismatch: expected {expected_manifest_sha256}, "
            f"got {actual_manifest_hash}"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbol = manifest.get("symbols", {}).get("EURUSD")
    if not symbol:
        raise BaselineInputError("manifest has no EURUSD entry")
    files = symbol.get("files", {})
    ask_entry = symbol.get("ask_m1")
    expected_paths = {
        "m1": manifest_path.parent / files.get("M1", {}).get("path", ""),
        "m5": manifest_path.parent / files.get("M5", {}).get("path", ""),
        "m1_ask": manifest_path.parent / (ask_entry or {}).get("path", ""),
    }
    for label, path in (("m1", m1_path), ("m5", m5_path), ("m1_ask", ask_path)):
        if path.resolve() != expected_paths[label].resolve():
            raise BaselineInputError(
                f"{label} argument is not the manifest-referenced canonical file"
            )
        actual = _sha256(path)
        if actual != expected_file_sha256[label]:
            raise BaselineInputError(
                f"{label} hash mismatch: expected {expected_file_sha256[label]}, got {actual}"
            )

    if ask_entry is None or ask_entry.get("source") != "copy_ticks_range":
        raise BaselineInputError("M1 Ask source is not the sealed tick-derived sidecar")
    if manifest.get("timestamp_semantics") != "bar_open_utc":
        raise BaselineInputError("manifest timestamp semantics are not bar_open_utc")

    for label, path in paths.items():
        if label in expected_rows and expected_rows[label] <= 0:
            raise BaselineInputError(f"invalid expected row count for {label}")

    # The existing loader verifies every file checksum, timestamp, OHLC bound,
    # and manifest row/first/last metadata.  It intentionally reads canonical
    # M5 as a native timeframe; no M1 aggregation is performed here.
    dataset = load_mt5_dataset(manifest_path)
    if "EURUSD" not in dataset.m1_bars or "EURUSD" not in dataset.ask_m1_bars:
        raise BaselineInputError("sealed dataset lacks EURUSD M1 or Ask history")
    native_m5 = dataset.native_timeframe_bars.get("EURUSD", {}).get("M5")
    if native_m5 is None:
        raise BaselineInputError("sealed dataset lacks canonical EURUSD M5 history")
    if len(dataset.m1_bars["EURUSD"]) != expected_rows["m1"]:
        raise BaselineInputError("M1 row count does not match the sealed contract")
    if len(dataset.ask_m1_bars["EURUSD"]) != expected_rows["m1_ask"]:
        raise BaselineInputError("M1 Ask row count does not match the sealed contract")
    if len(native_m5) != expected_rows["m5"]:
        raise BaselineInputError("M5 row count does not match the sealed contract")

    return dataset, {
        "manifest_sha256": actual_manifest_hash,
        "files": {
            label: {
                "path": str(path),
                "sha256": _sha256(path),
                "rows": int(expected_rows[label]),
            }
            for label, path in (("m1", m1_path), ("m1_ask", ask_path), ("m5", m5_path))
        },
    }


def _validate_selected_day(dataset: Any, start: pd.Timestamp, end: pd.Timestamp) -> None:
    """Require exact contiguous M1/M5/Ask coverage for the selected day."""
    m1 = dataset.m1_bars["EURUSD"]
    ask = dataset.ask_m1_bars["EURUSD"]
    m5 = dataset.native_timeframe_bars["EURUSD"]["M5"]
    expected_m1 = pd.date_range(start, end - pd.Timedelta(minutes=1), freq="min", tz="UTC")
    expected_m5 = pd.date_range(start, end - pd.Timedelta(minutes=5), freq="5min", tz="UTC")
    for label, actual, expected in (("M1", m1.index, expected_m1), ("M1 Ask", ask.index, expected_m1), ("M5", m5.index, expected_m5)):
        selected = actual[(actual >= start) & (actual < end)]
        if list(selected) != list(expected):
            raise BaselineInputError(
                f"selected-day {label} coverage is incomplete or misaligned"
            )


class _SingleSymbolATRManager:
    """Production ATR calculation with a one-symbol deterministic cache."""

    def __init__(self, rate_fetcher: ReplayFeed, symbol: str):
        self.rate_fetcher = rate_fetcher
        self.symbol = symbol
        self.cache: float | None = None

    def refresh_once(self) -> int:
        value = get_atr(
            symbol=self.symbol,
            timeframe=config.atr_timeframe,
            atr_period=config.atr_period,
            rate_fetcher=self.rate_fetcher,
        )
        if value is None:
            return 0
        self.cache = float(value)
        return 1

    def get_atr(self, symbol: str, timeframe: str) -> float | None:
        if symbol == self.symbol and timeframe == config.atr_timeframe:
            return self.cache
        return None

    def is_ready(self) -> bool:
        return self.cache is not None


def _indicator_trace_record(
    observation: Mapping[str, Any],
    *,
    blocked_by_position: bool,
) -> dict[str, Any]:
    record = dict(observation)
    record.pop("schema_version", None)
    record.pop("source_engine", None)
    record.pop("event_kind", None)
    record["record_type"] = "indicator_observation"
    record["blocked_by_position"] = bool(blocked_by_position)
    record["candidate_signal"] = record.get("signal", "NONE")
    record["signal"] = "NONE" if blocked_by_position else record.get("signal", "NONE")
    return record


def _decision_boundaries(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DatetimeIndex:
    """Return completed-M1 decision boundaries for a half-open source day."""
    return pd.date_range(
        start=start + pd.Timedelta(minutes=1),
        end=end,
        freq="min",
        inclusive="both",
    )


def _fast_forward_to_sample(feed: ReplayFeed, broker: HistoricalBroker) -> None:
    first_boundary = EXPECTED_START + pd.Timedelta(minutes=1)
    while not feed.finished and (feed.current_time is None or feed.current_time < first_boundary):
        broker.advance()
    if feed.current_time != first_boundary:
        raise BaselineInputError(
            f"replay cannot reach first sample boundary: {_iso(feed.current_time)}"
        )


def run_single_day_baseline(
    *,
    manifest_path: str | Path,
    m1_path: str | Path,
    m1_ask_path: str | Path,
    m5_path: str | Path,
    symbol: str = "EURUSD",
    start: str = "2026-09-10T00:00:00Z",
    end: str = "2026-09-11T00:00:00Z",
    output_dir: str | Path,
    fail_on_input_mismatch: bool = False,
) -> dict[str, Any]:
    """Run the bounded baseline and write four immutable evidence files."""
    if symbol != "EURUSD":
        raise BaselineInputError("M031 Stage 2 is sealed for EURUSD only")
    start_ts, end_ts = _utc(start), _utc(end)
    if start_ts != EXPECTED_START or end_ts != EXPECTED_END:
        raise BaselineInputError("M031 Stage 2 is sealed for the September 10, 2026 UTC day")
    if end_ts <= start_ts:
        raise BaselineInputError("end must be after start")

    output = Path(output_dir)
    if output.exists():
        raise FileExistsError(f"refusing to reuse output directory: {output}")

    dataset, input_identity = _validate_source_arguments(
        Path(manifest_path), Path(m1_path), Path(m1_ask_path), Path(m5_path)
    )
    _validate_selected_day(dataset, start_ts, end_ts)
    if not fail_on_input_mismatch:
        # The sealed contract is always fail-closed; the flag is retained as an
        # explicit CLI acknowledgement and cannot disable hash validation.
        raise BaselineInputError("--fail-on-input-mismatch is required by the sealed contract")

    feed = ReplayFeed(
        {symbol: dataset.m1_bars[symbol]},
        native_timeframe_bars={symbol: {"M5": dataset.native_timeframe_bars[symbol]["M5"]}},
        ask_m1_bars={symbol: dataset.ask_m1_bars[symbol]},
    )
    sink = EventSink()
    broker = HistoricalBroker(
        feed,
        balance=10_000.0,
        symbol_metadata={symbol: dataset.symbol_metadata[symbol]},
        account_currency=dataset.account_currency,
        execution_costs={symbol: ExecutionCostModel()},
        event_sink=sink,
    )
    atr_manager = _SingleSymbolATRManager(feed, symbol)
    position_manager = PositionManager(broker, atr_manager=atr_manager, rates_fetcher=feed)
    strategy = StochasticTripleTFStrategy(symbol)
    strategy_broker = BacktestBrokerAdapter(broker)

    _fast_forward_to_sample(feed, broker)
    trace: list[dict[str, Any]] = []
    decision_boundaries = 0
    while feed.current_time is not None and feed.current_time <= end_ts:
        boundary = feed.current_time
        opening = boundary - pd.Timedelta(minutes=1)
        sink.emit(event(
            engine="python", kind="M1_CLOSE", symbol=symbol,
            utc_time_ms=utc_millis(boundary.to_pydatetime()),
            m1_source_open_utc=_iso(opening),
        ))
        atr_manager.refresh_once()
        blocked = bool(
            broker.positions_total()
            or any(order.get("request", {}).get("symbol") == symbol for order in broker.pending_orders)
        )
        observation = observe_candidate(feed, symbol)
        trace.append(_indicator_trace_record(observation, blocked_by_position=blocked))
        if not blocked:
            if observation.get("signal") in {"BUY", "SELL"}:
                sink.emit(observation)
            asyncio.run(strategy.evaluate({
                "broker": strategy_broker,
                "rate_fetcher": feed,
                "position_manager": position_manager,
                "reporting_enabled": False,
            }))
        broker.settle_pending_orders()
        asyncio.run(position_manager.update_once())
        decision_boundaries += 1
        if feed.finished:
            break
        broker.advance()

    unresolved = []
    for position in asyncio.run(broker.positions_get(symbol=symbol)):
        unresolved.append({
            "symbol": position["symbol"], "side": "BUY" if position["type"] == 0 else "SELL",
            "volume_lots": float(position["volume"]), "open_time_utc": _iso(pd.Timestamp(position["time"], unit="s", tz="UTC")),
            "open_price": float(position["price_open"]), "sl": float(position["sl"]), "tp": float(position["tp"]),
        })
    output.mkdir(parents=True)
    boundaries = _decision_boundaries(start_ts, end_ts)
    if decision_boundaries != len(boundaries):
        raise BaselineInputError(
            f"replay boundary count mismatch: expected {len(boundaries)}, "
            f"observed {decision_boundaries}"
        )
    manifest_record = {
        "schema_version": 1,
        "executed": True,
        "engine": "python",
        "repo_head": _repo_head(),
        "symbol": symbol,
        "source_interval_utc": {"start": _iso(start_ts), "end": _iso(end_ts)},
        "decision_boundaries": {"first": _iso(boundaries[0]), "last": _iso(boundaries[-1]), "count": decision_boundaries},
        "warmup": {"trading": "indicator_only", "flat_account_at_first_boundary": True},
        "input_identity": input_identity,
        "canonical_m5": {"source": "direct_manifest_reference", "derived_from_m1": False},
        "cost_assumptions": {"commission_per_lot_per_side": 0.0, "slippage_points": 0.0, "swap": "not_modeled"},
        "event_schema": "m030.events.v1",
        "comparison": {"full_prefix_m1_to_m5_ohlc": "FAILED_BY_STAGE_1_SEAL", "sample_day_ohlc": "SEALED"},
    }
    summary = {
        "schema_version": 1,
        "decision_boundaries": decision_boundaries,
        "event_counts": {kind: sum(event["event_kind"] == kind for event in sink.events) for kind in sorted({event["event_kind"] for event in sink.events})},
        "indicator_observations": len(trace),
        "blocked_candidate_observations": sum(row["blocked_by_position"] for row in trace),
        "unresolved_positions": unresolved,
        "account": broker.account_info(),
        "economic_interpretation": "none; bounded parity baseline only",
    }
    _write_exclusive(output / "input_manifest.json", json.dumps(manifest_record, indent=2, sort_keys=True) + "\n")
    _write_exclusive(output / "indicator_trace.jsonl", "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in trace))
    _write_exclusive(output / "events.jsonl", "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in sink.events))
    _write_exclusive(output / "summary.json", json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return {"output_dir": str(output), "summary": summary, "input_manifest": manifest_record}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M031 sealed one-day Python baseline")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--m1", required=True)
    parser.add_argument("--m1-ask", required=True)
    parser.add_argument("--m5", required=True)
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--start", default="2026-09-10T00:00:00Z")
    parser.add_argument("--end", default="2026-09-11T00:00:00Z")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fail-on-input-mismatch", action="store_true")
    args = parser.parse_args(argv)
    result = run_single_day_baseline(
        manifest_path=args.manifest, m1_path=args.m1, m1_ask_path=args.m1_ask,
        m5_path=args.m5, symbol=args.symbol, start=args.start, end=args.end,
        output_dir=args.output_dir, fail_on_input_mismatch=args.fail_on_input_mismatch,
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    print(result["output_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
