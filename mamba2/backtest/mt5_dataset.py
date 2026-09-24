"""Read-only MT5 historical dataset export and verified native loading.

The exporter is intentionally separated from the live broker/order path. It
uses only MT5 market-data and metadata APIs, writes deterministic CSV files,
and records a manifest with SHA-256 checksums and bar-open UTC semantics.

MetaTrader5 is imported only inside ``main`` so this module remains importable
in the native Linux backtest environment where the Windows-only package is not
installed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .broker import SymbolExecutionMetadata
from .data import REQUIRED_BAR_COLUMNS, HistoricalDataError, canonicalize_bars


DATASET_SCHEMA_VERSION = 1
TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15}


class DatasetIntegrityError(ValueError):
    """Raised when a persisted historical dataset fails manifest validation."""


@dataclass(frozen=True)
class LoadedHistoricalDataset:
    """Verified dataset ready to construct ReplayFeed/HistoricalBroker."""

    m1_bars: Mapping[str, pd.DataFrame]
    native_timeframe_bars: Mapping[str, Mapping[str, pd.DataFrame]]
    symbol_metadata: Mapping[str, SymbolExecutionMetadata]
    manifest: Mapping[str, Any]


def _utc_timestamp(value: str | datetime | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def _iso_utc(timestamp: pd.Timestamp) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timeframe_value(mt5_module: Any, timeframe: str) -> Any:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported export timeframe: {timeframe}")
    name = f"TIMEFRAME_{timeframe}"
    if not hasattr(mt5_module, name):
        raise RuntimeError(f"MT5 module does not expose {name}")
    return getattr(mt5_module, name)


def _normalize_rates(
    rates: Any,
    *,
    timeframe: str,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
) -> pd.DataFrame:
    if rates is None:
        raise HistoricalDataError("MT5 returned no rates object")

    frame = pd.DataFrame(rates)
    if frame.empty:
        raise HistoricalDataError(f"MT5 returned no {timeframe} bars")
    if "time" not in frame.columns:
        raise HistoricalDataError("MT5 rates are missing time")

    frame = frame.loc[:, ["time", *REQUIRED_BAR_COLUMNS]].copy()
    frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)

    minutes = TIMEFRAME_MINUTES[timeframe]
    visible = frame.loc[
        (frame["time"] >= start_utc)
        & (frame["time"] + pd.Timedelta(minutes=minutes) <= end_utc)
    ].copy()
    if visible.empty:
        raise HistoricalDataError(
            f"no completed {timeframe} bars in requested UTC range"
        )

    canonical = canonicalize_bars(visible)
    aligned = canonical.index == canonical.index.floor(f"{minutes}min")
    if not aligned.all():
        raise HistoricalDataError(
            f"{timeframe} contains non-aligned bar-open timestamps"
        )
    return canonical


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    output = frame.reset_index()
    output["time"] = (output["time"].astype("int64") // 1_000_000_000).astype("int64")
    for column in ("tick_volume", "spread", "real_volume"):
        output[column] = output[column].astype("int64")
    output.to_csv(
        path,
        index=False,
        columns=["time", *REQUIRED_BAR_COLUMNS],
        float_format="%.12g",
        lineterminator="\n",
    )


def export_mt5_dataset(
    mt5_module: Any,
    *,
    symbols: Sequence[str],
    timeframes: Sequence[str] = ("M1", "M5", "M15"),
    start_utc: str | datetime | pd.Timestamp,
    end_utc: str | datetime | pd.Timestamp,
    output_dir: str | Path,
    exported_at_utc: str | datetime | pd.Timestamp | None = None,
) -> Path:
    """Export completed native MT5 bars without invoking any trading API."""
    start = _utc_timestamp(start_utc)
    end = _utc_timestamp(end_utc)
    if end <= start:
        raise ValueError("end_utc must be later than start_utc")
    if not symbols:
        raise ValueError("at least one symbol is required")

    normalized_timeframes = tuple(dict.fromkeys(timeframes))
    if "M1" not in normalized_timeframes:
        raise ValueError("M1 is required because it drives replay time")
    for timeframe in normalized_timeframes:
        if timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"unsupported export timeframe: {timeframe}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    account_info = mt5_module.account_info()
    account_currency = getattr(account_info, "currency", None)
    broker_server = getattr(account_info, "server", None)
    terminal_version = list(mt5_module.version()) if hasattr(mt5_module, "version") else None

    exported_at = _utc_timestamp(
        exported_at_utc or datetime.now(timezone.utc)
    )
    manifest: dict[str, Any] = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "source": "MetaTrader5",
        "timestamp_semantics": "bar_open_utc",
        "availability_rule": "bar_open + timeframe <= replay_time",
        "exported_at_utc": _iso_utc(exported_at),
        "requested_range": {
            "from_utc": _iso_utc(start),
            "to_utc": _iso_utc(end),
        },
        "account_currency": account_currency,
        "broker_server": broker_server,
        "terminal_version": terminal_version,
        "symbols": {},
    }

    for symbol in symbols:
        if not mt5_module.symbol_select(symbol, True):
            raise RuntimeError(f"MT5 could not select symbol: {symbol}")
        info = mt5_module.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"MT5 returned no symbol metadata for {symbol}")

        symbol_entry: dict[str, Any] = {
            "digits": int(info.digits),
            "point": float(info.point),
            "contract_size": float(info.trade_contract_size),
            "base_currency": str(getattr(info, "currency_base", "")),
            "quote_currency": str(getattr(info, "currency_profit", "")),
            "margin_currency": str(getattr(info, "currency_margin", "")),
            "files": {},
        }

        for timeframe in normalized_timeframes:
            mt5_timeframe = _timeframe_value(mt5_module, timeframe)
            rates = mt5_module.copy_rates_range(
                symbol,
                mt5_timeframe,
                start.to_pydatetime(),
                end.to_pydatetime(),
            )
            frame = _normalize_rates(
                rates,
                timeframe=timeframe,
                start_utc=start,
                end_utc=end,
            )

            filename = f"{symbol}_{timeframe}.csv"
            path = output / filename
            _write_csv(frame, path)
            minutes = TIMEFRAME_MINUTES[timeframe]
            symbol_entry["files"][timeframe] = {
                "path": filename,
                "sha256": _sha256(path),
                "rows": int(len(frame)),
                "first_bar_open_utc": _iso_utc(frame.index[0]),
                "last_bar_open_utc": _iso_utc(frame.index[-1]),
                "last_bar_available_utc": _iso_utc(
                    frame.index[-1] + pd.Timedelta(minutes=minutes)
                ),
            }

        manifest["symbols"][symbol] = symbol_entry

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def load_mt5_dataset(manifest_path: str | Path) -> LoadedHistoricalDataset:
    """Load a dataset only after checksum, schema, and row metadata validation."""
    manifest_file = Path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != DATASET_SCHEMA_VERSION:
        raise DatasetIntegrityError("unsupported dataset schema version")
    if manifest.get("source") != "MetaTrader5":
        raise DatasetIntegrityError("unsupported dataset source")
    if manifest.get("timestamp_semantics") != "bar_open_utc":
        raise DatasetIntegrityError("unsupported timestamp semantics")

    root = manifest_file.parent
    m1_bars: dict[str, pd.DataFrame] = {}
    native: dict[str, dict[str, pd.DataFrame]] = {}
    metadata: dict[str, SymbolExecutionMetadata] = {}

    for symbol, symbol_entry in manifest.get("symbols", {}).items():
        files = symbol_entry.get("files", {})
        if "M1" not in files:
            raise DatasetIntegrityError(f"{symbol} is missing M1 data")

        metadata[symbol] = SymbolExecutionMetadata(
            point_size=float(symbol_entry["point"]),
            digits=int(symbol_entry["digits"]),
            contract_size=float(symbol_entry["contract_size"]),
            quote_currency=str(symbol_entry["quote_currency"]),
        )

        native_symbol: dict[str, pd.DataFrame] = {}
        for timeframe, file_entry in files.items():
            if timeframe not in TIMEFRAME_MINUTES:
                raise DatasetIntegrityError(
                    f"{symbol} has unsupported timeframe {timeframe}"
                )
            path = root / file_entry["path"]
            if not path.is_file():
                raise DatasetIntegrityError(f"missing dataset file: {path.name}")
            if _sha256(path) != file_entry["sha256"]:
                raise DatasetIntegrityError(f"checksum mismatch: {path.name}")

            frame = pd.read_csv(path)
            if "time" not in frame.columns:
                raise DatasetIntegrityError(f"missing time column: {path.name}")
            frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
            try:
                canonical = canonicalize_bars(frame)
            except HistoricalDataError as exc:
                raise DatasetIntegrityError(str(exc)) from exc

            if len(canonical) != int(file_entry["rows"]):
                raise DatasetIntegrityError(f"row-count mismatch: {path.name}")
            first = _iso_utc(canonical.index[0])
            last = _iso_utc(canonical.index[-1])
            if first != file_entry["first_bar_open_utc"]:
                raise DatasetIntegrityError(f"first timestamp mismatch: {path.name}")
            if last != file_entry["last_bar_open_utc"]:
                raise DatasetIntegrityError(f"last timestamp mismatch: {path.name}")

            if timeframe == "M1":
                m1_bars[symbol] = canonical
            else:
                native_symbol[timeframe] = canonical

        if native_symbol:
            native[symbol] = native_symbol

    if not m1_bars:
        raise DatasetIntegrityError("dataset contains no M1 histories")

    return LoadedHistoricalDataset(
        m1_bars=m1_bars,
        native_timeframe_bars=native,
        symbol_metadata=metadata,
        manifest=manifest,
    )


def _mt5_initialize_kwargs(config: Any) -> dict[str, Any]:
    """Build safe MT5 initialize kwargs for the read-only exporter.

    The exporter may use an already authenticated terminal session when login,
    password, and server are all absent. If any credential field is supplied,
    all three are required so a partial configuration cannot silently select
    an unintended account.
    """

    credentials = {
        "MAMBA_MT5_LOGIN": config.login,
        "MAMBA_MT5_PASSWORD": config.password,
        "MAMBA_MT5_SERVER": config.server,
    }
    provided = [name for name, value in credentials.items() if value]
    missing = [name for name, value in credentials.items() if not value]

    if provided and missing:
        raise RuntimeError(
            "MT5 historical export received partial environment configuration; "
            "provide all of: MAMBA_MT5_LOGIN, MAMBA_MT5_PASSWORD, "
            "MAMBA_MT5_SERVER, or leave all three unset to use the terminal "
            "session already authenticated in MT5."
        )

    kwargs: dict[str, Any] = {
        "timeout": config.timeout,
        "portable": config.portable,
    }
    if config.path:
        kwargs["path"] = config.path

    if not missing:
        kwargs.update(
            login=config.login,
            password=config.password,
            server=config.server,
        )

    return kwargs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export read-only MT5 M1/M5/M15 history with checksums."
    )
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=["M1", "M5", "M15"],
        choices=tuple(TIMEFRAME_MINUTES),
    )
    parser.add_argument("--from-utc", required=True)
    parser.add_argument("--to-utc", required=True)
    parser.add_argument("--output-dir", default="backtest_data/mt5")
    args = parser.parse_args(argv)

    from config import mt5 as mt5_config

    initialize_kwargs = _mt5_initialize_kwargs(mt5_config)
    try:
        import MetaTrader5 as mt5
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MT5 historical export requires the Windows-only MetaTrader5 package"
        ) from exc

    if not mt5.initialize(**initialize_kwargs):
        raise ConnectionError(f"Failed to initialize MT5: {mt5.last_error()}")

    try:
        manifest = export_mt5_dataset(
            mt5,
            symbols=args.symbols,
            timeframes=args.timeframes,
            start_utc=args.from_utc,
            end_utc=args.to_utc,
            output_dir=args.output_dir,
        )
        print(manifest)
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
