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
import time
from typing import Any, Mapping, Sequence

import pandas as pd

from .broker import SymbolExecutionMetadata
from .data import (
    PRICE_BAR_COLUMNS,
    REQUIRED_BAR_COLUMNS,
    HistoricalDataError,
    canonicalize_bars,
    canonicalize_price_bars,
)


DATASET_SCHEMA_VERSION = 2
SUPPORTED_DATASET_SCHEMA_VERSIONS = {1, 2}
TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15}


class DatasetIntegrityError(ValueError):
    """Raised when a persisted historical dataset fails manifest validation."""


@dataclass(frozen=True)
class LoadedHistoricalDataset:
    """Verified dataset ready to construct ReplayFeed/HistoricalBroker."""

    m1_bars: Mapping[str, pd.DataFrame]
    native_timeframe_bars: Mapping[str, Mapping[str, pd.DataFrame]]
    ask_m1_bars: Mapping[str, pd.DataFrame]
    symbol_metadata: Mapping[str, SymbolExecutionMetadata]
    account_currency: str
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

def _fetch_rates_with_history_sync(
    mt5_module: Any,
    *,
    symbol: str,
    mt5_timeframe: Any,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    warmup_count: int,
    sync_wait_seconds: float,
) -> tuple[Any, bool]:
    """Fetch an MT5 range and retry once after a bounded history warm-up.

    MetaTrader 5 can return an empty copy_rates_range result until chart
    history for that symbol/timeframe has been requested. The bounded
    copy_rates_from_pos probe is read-only and gives the terminal one
    opportunity to synchronize history before the exact range is retried.
    """

    rates = mt5_module.copy_rates_range(
        symbol,
        mt5_timeframe,
        start_utc.to_pydatetime(),
        end_utc.to_pydatetime(),
    )
    if rates is not None and len(rates) > 0:
        return rates, False

    mt5_module.copy_rates_from_pos(
        symbol,
        mt5_timeframe,
        0,
        warmup_count,
    )
    if sync_wait_seconds > 0:
        time.sleep(sync_wait_seconds)

    retry = mt5_module.copy_rates_range(
        symbol,
        mt5_timeframe,
        start_utc.to_pydatetime(),
        end_utc.to_pydatetime(),
    )
    return retry, True


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


def _normalize_tick_ask_bars(
    ticks: Any,
    *,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    m1_index: pd.DatetimeIndex,
) -> tuple[pd.DataFrame, dict[str, int | float | None]]:
    """Aggregate historical ticks into exact per-minute Ask OHLC."""

    if ticks is None:
        raise HistoricalDataError("MT5 returned no tick history object")

    frame = pd.DataFrame(ticks)
    if frame.empty:
        raise HistoricalDataError("MT5 returned no ticks for Ask reconstruction")
    if "ask" not in frame.columns:
        raise HistoricalDataError("MT5 ticks are missing ask")

    if "time_msc" in frame.columns:
        frame["_time"] = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
    elif "time" in frame.columns:
        frame["_time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    else:
        raise HistoricalDataError("MT5 ticks are missing time/time_msc")

    frame["ask"] = pd.to_numeric(frame["ask"], errors="coerce")
    if "bid" in frame.columns:
        frame["bid"] = pd.to_numeric(frame["bid"], errors="coerce")

    frame = frame.loc[
        (frame["_time"] >= start_utc)
        & (frame["_time"] < end_utc)
        & frame["ask"].notna()
        & (frame["ask"] > 0)
    ].copy()
    if frame.empty:
        raise HistoricalDataError("no valid Ask ticks in requested UTC range")

    frame["_minute"] = frame["_time"].dt.floor("min")
    grouped = frame.groupby("_minute", sort=True)["ask"]
    ask = pd.DataFrame(
        {
            "open": grouped.first(),
            "high": grouped.max(),
            "low": grouped.min(),
            "close": grouped.last(),
        }
    )
    ask.index.name = "time"
    ask = ask.loc[ask.index.isin(m1_index)]
    if ask.empty:
        raise HistoricalDataError("tick Ask history does not overlap exported M1 bars")
    ask = canonicalize_price_bars(ask)

    quality: dict[str, int | float | None] = {
        "valid_ticks": int(len(frame)),
        "covered_m1_rows": int(len(ask)),
        "missing_m1_rows": int(len(m1_index.difference(ask.index))),
        "spread_points_min": None,
        "spread_points_max": None,
        "zero_spread_ticks": 0,
    }
    if "bid" in frame.columns:
        spread = frame.loc[
            frame["bid"].notna() & (frame["bid"] > 0),
            "ask",
        ] - frame.loc[
            frame["bid"].notna() & (frame["bid"] > 0),
            "bid",
        ]
        point = None
        if not spread.empty:
            # Raw price spread is recorded here; integer-point quality is
            # filled by the caller because symbol point size lives in metadata.
            quality["_spread_price_min"] = float(spread.min())
            quality["_spread_price_max"] = float(spread.max())
            quality["_spread_price_zero_count"] = int((spread == 0).sum())
    return ask, quality


def _write_price_csv(frame: pd.DataFrame, path: Path) -> None:
    output = frame.reset_index()
    output["time"] = (
        output["time"].astype("int64") // 1_000_000_000
    ).astype("int64")
    output.to_csv(
        path,
        index=False,
        columns=["time", *PRICE_BAR_COLUMNS],
        float_format="%.12g",
        lineterminator="\n",
    )


def _fetch_tick_chunks(
    mt5_module: Any,
    *,
    symbol: str,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    flags: Any,
    chunk_minutes: int,
    warmup_count: int,
    sync_wait_seconds: float,
) -> tuple[pd.DataFrame, bool]:
    """Fetch read-only ticks in bounded chunks with one sync retry if needed."""

    if chunk_minutes < 1:
        raise ValueError("tick_chunk_minutes must be at least 1")

    chunks: list[pd.DataFrame] = []
    history_sync_retry = False
    cursor = start_utc
    warmed = False

    while cursor < end_utc:
        chunk_end = min(
            cursor + pd.Timedelta(minutes=chunk_minutes),
            end_utc,
        )
        ticks = mt5_module.copy_ticks_range(
            symbol,
            cursor.to_pydatetime(),
            chunk_end.to_pydatetime(),
            flags,
        )
        if (ticks is None or len(ticks) == 0) and not warmed:
            mt5_module.copy_ticks_from(
                symbol,
                cursor.to_pydatetime(),
                warmup_count,
                flags,
            )
            warmed = True
            history_sync_retry = True
            if sync_wait_seconds > 0:
                time.sleep(sync_wait_seconds)
            ticks = mt5_module.copy_ticks_range(
                symbol,
                cursor.to_pydatetime(),
                chunk_end.to_pydatetime(),
                flags,
            )

        if ticks is not None and len(ticks) > 0:
            chunks.append(pd.DataFrame(ticks))

        cursor = chunk_end

    if not chunks:
        raise HistoricalDataError("MT5 returned no tick history")

    combined = pd.concat(chunks, ignore_index=True)
    dedupe_columns = [
        column
        for column in ("time_msc", "time", "bid", "ask", "last", "volume", "flags")
        if column in combined.columns
    ]
    if dedupe_columns:
        combined = combined.drop_duplicates(subset=dedupe_columns, keep="first")
    return combined, history_sync_retry


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
    history_warmup_count: int = 5000,
    history_sync_wait_seconds: float = 2.0,
    include_tick_ask: bool = False,
    tick_chunk_minutes: int = 1440,
) -> Path:
    """Export completed native MT5 bars without invoking any trading API."""
    start = _utc_timestamp(start_utc)
    end = _utc_timestamp(end_utc)
    if end <= start:
        raise ValueError("end_utc must be later than start_utc")
    if not symbols:
        raise ValueError("at least one symbol is required")
    if history_warmup_count < 1:
        raise ValueError("history_warmup_count must be at least 1")
    if history_sync_wait_seconds < 0:
        raise ValueError("history_sync_wait_seconds cannot be negative")
    if tick_chunk_minutes < 1:
        raise ValueError("tick_chunk_minutes must be at least 1")

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

        exported_frames: dict[str, pd.DataFrame] = {}
        for timeframe in normalized_timeframes:
            mt5_timeframe = _timeframe_value(mt5_module, timeframe)
            rates, history_sync_retry = _fetch_rates_with_history_sync(
                mt5_module,
                symbol=symbol,
                mt5_timeframe=mt5_timeframe,
                start_utc=start,
                end_utc=end,
                warmup_count=history_warmup_count,
                sync_wait_seconds=history_sync_wait_seconds,
            )
            frame = _normalize_rates(
                rates,
                timeframe=timeframe,
                start_utc=start,
                end_utc=end,
            )

            exported_frames[timeframe] = frame

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
                "history_sync_retry": history_sync_retry,
            }

        if include_tick_ask:
            if not hasattr(mt5_module, "copy_ticks_range"):
                raise RuntimeError(
                    "MT5 module does not expose copy_ticks_range required "
                    "for tick-derived Ask history"
                )
            if not hasattr(mt5_module, "copy_ticks_from"):
                raise RuntimeError(
                    "MT5 module does not expose copy_ticks_from required "
                    "for tick-history synchronization"
                )
            if not hasattr(mt5_module, "COPY_TICKS_ALL"):
                raise RuntimeError(
                    "MT5 module does not expose COPY_TICKS_ALL"
                )

            ticks, tick_sync_retry = _fetch_tick_chunks(
                mt5_module,
                symbol=symbol,
                start_utc=start,
                end_utc=end,
                flags=mt5_module.COPY_TICKS_ALL,
                chunk_minutes=tick_chunk_minutes,
                warmup_count=history_warmup_count,
                sync_wait_seconds=history_sync_wait_seconds,
            )
            ask_frame, tick_quality = _normalize_tick_ask_bars(
                ticks,
                start_utc=start,
                end_utc=end,
                m1_index=exported_frames["M1"].index,
            )

            point = float(info.point)
            spread_min_price = tick_quality.pop("_spread_price_min", None)
            spread_max_price = tick_quality.pop("_spread_price_max", None)
            zero_count = tick_quality.pop("_spread_price_zero_count", 0)
            if spread_min_price is not None and point > 0:
                tick_quality["spread_points_min"] = int(
                    round(float(spread_min_price) / point)
                )
                tick_quality["spread_points_max"] = int(
                    round(float(spread_max_price) / point)
                )
                tick_quality["zero_spread_ticks"] = int(zero_count)

            ask_filename = f"{symbol}_M1_ask.csv"
            ask_path = output / ask_filename
            _write_price_csv(ask_frame, ask_path)
            symbol_entry["ask_m1"] = {
                "path": ask_filename,
                "sha256": _sha256(ask_path),
                "rows": int(len(ask_frame)),
                "first_bar_open_utc": _iso_utc(ask_frame.index[0]),
                "last_bar_open_utc": _iso_utc(ask_frame.index[-1]),
                "source": "copy_ticks_range",
                "flags": "COPY_TICKS_ALL",
                "history_sync_retry": tick_sync_retry,
                **tick_quality,
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
    if manifest.get("schema_version") not in SUPPORTED_DATASET_SCHEMA_VERSIONS:
        raise DatasetIntegrityError("unsupported dataset schema version")
    if manifest.get("source") != "MetaTrader5":
        raise DatasetIntegrityError("unsupported dataset source")
    if manifest.get("timestamp_semantics") != "bar_open_utc":
        raise DatasetIntegrityError("unsupported timestamp semantics")

    root = manifest_file.parent
    m1_bars: dict[str, pd.DataFrame] = {}
    native: dict[str, dict[str, pd.DataFrame]] = {}
    ask_m1: dict[str, pd.DataFrame] = {}
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
            base_currency=str(symbol_entry.get("base_currency", "")),
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

        ask_entry = symbol_entry.get("ask_m1")
        if ask_entry is not None:
            ask_path = root / ask_entry["path"]
            if not ask_path.is_file():
                raise DatasetIntegrityError(
                    f"missing dataset file: {ask_path.name}"
                )
            if _sha256(ask_path) != ask_entry["sha256"]:
                raise DatasetIntegrityError(
                    f"checksum mismatch: {ask_path.name}"
                )
            ask_frame = pd.read_csv(ask_path)
            if "time" not in ask_frame.columns:
                raise DatasetIntegrityError(
                    f"missing time column: {ask_path.name}"
                )
            ask_frame["time"] = pd.to_datetime(
                ask_frame["time"],
                unit="s",
                utc=True,
            )
            try:
                canonical_ask = canonicalize_price_bars(ask_frame)
            except HistoricalDataError as exc:
                raise DatasetIntegrityError(str(exc)) from exc
            if len(canonical_ask) != int(ask_entry["rows"]):
                raise DatasetIntegrityError(
                    f"row-count mismatch: {ask_path.name}"
                )
            if _iso_utc(canonical_ask.index[0]) != ask_entry["first_bar_open_utc"]:
                raise DatasetIntegrityError(
                    f"first timestamp mismatch: {ask_path.name}"
                )
            if _iso_utc(canonical_ask.index[-1]) != ask_entry["last_bar_open_utc"]:
                raise DatasetIntegrityError(
                    f"last timestamp mismatch: {ask_path.name}"
                )
            if symbol in m1_bars and not canonical_ask.index.isin(
                m1_bars[symbol].index
            ).all():
                raise DatasetIntegrityError(
                    f"Ask M1 timestamps are not a subset of Bid M1: {symbol}"
                )
            ask_m1[symbol] = canonical_ask

    if not m1_bars:
        raise DatasetIntegrityError("dataset contains no M1 histories")

    account_currency = str(manifest.get("account_currency") or "").upper()
    if not account_currency:
        raise DatasetIntegrityError("dataset account currency is missing")

    return LoadedHistoricalDataset(
        m1_bars=m1_bars,
        native_timeframe_bars=native,
        ask_m1_bars=ask_m1,
        symbol_metadata=metadata,
        account_currency=account_currency,
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
    parser.add_argument("--history-warmup-count", type=int, default=5000)
    parser.add_argument("--history-sync-wait-seconds", type=float, default=2.0)
    parser.add_argument(
        "--include-tick-ask",
        action="store_true",
        help="Export tick-derived M1 Ask OHLC for spread-accurate replay.",
    )
    parser.add_argument("--tick-chunk-minutes", type=int, default=1440)
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
            history_warmup_count=args.history_warmup_count,
            history_sync_wait_seconds=args.history_sync_wait_seconds,
            include_tick_ask=args.include_tick_ask,
            tick_chunk_minutes=args.tick_chunk_minutes,
        )
        print(manifest)
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
