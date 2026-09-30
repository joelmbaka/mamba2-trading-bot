"""M027 deterministic public-data approximation machinery.

Stage 1 only: parse the frozen BIS/OECD source contracts, normalize quotes/rates,
align the previous completed month's rate differential without lookahead, and
construct daily approximate currency excess log returns.

This module intentionally contains no momentum signal, portfolio, P/L, Sharpe,
drawdown, or strategy-evaluation machinery.
"""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Mapping
import zipfile

import numpy as np
import pandas as pd


BIS_XRU_URL = "https://data.bis.org/static/bulk/WS_XRU_csv_flat.zip"
OECD_STIR_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/"
    ".M.IR3TIB.PA....."
    "?startPeriod=1950-01&dimensionAtObservation=AllDimensions"
)

M027_TRADING_DAYS = 261
M027_UNIVERSE_SHA256 = (
    "db9e1f4438fd582a0c2903f2459e290e30450bfc76365f2bbe91553d45b51c00"
)
M027_COST_LABEL = (
    "GROSS SPOT-PLUS-CARRY APPROXIMATION / TRANSACTION COSTS UNMODELED"
)

# Frozen after the metadata-only Stage-0 universe gate.
# currency -> (OECD rate reference area, BIS reference area)
M027_IDENTITIES: Mapping[str, tuple[str, str]] = {
    "AUD": ("AUS", "AU"),
    "CAD": ("CAN", "CA"),
    "CHF": ("CHE", "CH"),
    "CLP": ("CHL", "CL"),
    "CNY": ("CHN", "CN"),
    "COP": ("COL", "CO"),
    "CZK": ("CZE", "CZ"),
    "DKK": ("DNK", "DK"),
    "EUR": ("EA20", "XM"),
    "GBP": ("GBR", "GB"),
    "HUF": ("HUN", "HU"),
    "IDR": ("IDN", "ID"),
    "INR": ("IND", "IN"),
    "ISK": ("ISL", "IS"),
    "ILS": ("ISR", "IL"),
    "JPY": ("JPN", "JP"),
    "KRW": ("KOR", "KR"),
    "MXN": ("MEX", "MX"),
    "NOK": ("NOR", "NO"),
    "NZD": ("NZL", "NZ"),
    "PLN": ("POL", "PL"),
    "RON": ("ROU", "RO"),
    "RUB": ("RUS", "RU"),
    "SEK": ("SWE", "SE"),
    "ZAR": ("ZAF", "ZA"),
}
M027_CURRENCIES = tuple(M027_IDENTITIES)
M027_RATE_REFS = ("USA",) + tuple(
    dict.fromkeys(ref for ref, _ in M027_IDENTITIES.values())
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code_prefix(value: object) -> str:
    text = str(value or "").strip()
    return text.split(":", 1)[0].strip() if ":" in text else text


def _row_value(row: Mapping[str, object], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None:
            return str(value).strip()
    return ""


def _parse_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text or text in {".", "..", "NA", "N/A"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if np.isfinite(number) else None


def parse_bis_daily_spot_zip(raw_bytes: bytes) -> pd.DataFrame:
    """Parse frozen BIS daily XRU series into USD per foreign-currency unit.

    BIS XRU is published as the value of one USD in the foreign currency, so
    every admitted non-USD series is mechanically inverted.
    """

    rows: list[tuple[pd.Timestamp, str, float]] = []
    seen: set[tuple[pd.Timestamp, str]] = set()

    with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as archive:
        csv_names = sorted(
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
        )
        if not csv_names:
            raise ValueError("BIS XRU ZIP contains no CSV")

        with archive.open(csv_names[0], "r") as raw:
            reader = csv.DictReader(
                io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            )
            for row in reader:
                if _code_prefix(row.get("FREQ:Frequency")) != "D":
                    continue
                if _code_prefix(row.get("COLLECTION:Collection")) != "A":
                    continue

                currency = _code_prefix(row.get("CURRENCY:Currency"))
                identity = M027_IDENTITIES.get(currency)
                if identity is None:
                    continue

                _, expected_bis_ref = identity
                bis_ref = _code_prefix(row.get("REF_AREA:Reference area"))
                if bis_ref != expected_bis_ref:
                    continue

                date_text = _row_value(
                    row,
                    "TIME_PERIOD:Time period or range",
                    "TIME_PERIOD",
                )
                if not date_text:
                    continue
                try:
                    timestamp = pd.Timestamp(date_text, tz="UTC")
                except (TypeError, ValueError):
                    continue

                observed = _parse_float(
                    _row_value(
                        row,
                        "OBS_VALUE:Observation Value",
                        "OBS_VALUE:Observation value",
                        "OBS_VALUE",
                    )
                )
                if observed is None:
                    continue
                if observed <= 0:
                    raise ValueError(
                        f"BIS spot must be strictly positive for {currency}"
                    )

                key = (timestamp, currency)
                if key in seen:
                    raise ValueError(
                        f"duplicate BIS daily observation for {currency} "
                        f"on {timestamp.date()}"
                    )
                seen.add(key)
                rows.append((timestamp, currency, 1.0 / observed))

    if not rows:
        raise ValueError("no frozen M027 BIS daily observations found")

    long = pd.DataFrame(rows, columns=["date", "currency", "usd_per_fx"])
    panel = long.pivot(index="date", columns="currency", values="usd_per_fx")
    panel = panel.reindex(columns=M027_CURRENCIES).sort_index()
    panel.columns.name = None
    return panel.astype(float)


def parse_oecd_monthly_short_rates(raw_bytes: bytes) -> pd.DataFrame:
    """Parse OECD IR3TIB monthly percent-per-annum values to decimals."""

    text = raw_bytes.decode("utf-8-sig", errors="strict")
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    if "TIME_PERIOD" not in fields:
        raise ValueError("OECD response lacks TIME_PERIOD")
    if "REF_AREA" not in fields:
        raise ValueError("OECD response lacks REF_AREA")
    if "OBS_VALUE" not in fields:
        raise ValueError("OECD response lacks OBS_VALUE")

    accepted_refs = set(M027_RATE_REFS)
    rows: list[tuple[pd.Period, str, float]] = []
    seen: set[tuple[pd.Period, str]] = set()

    for row in reader:
        ref = str(row.get("REF_AREA", "")).strip()
        if ref not in accepted_refs:
            continue

        freq = str(row.get("FREQ", "")).strip()
        if freq and freq != "M":
            continue
        measure = str(row.get("MEASURE", "")).strip()
        if measure and measure != "IR3TIB":
            continue
        unit = str(row.get("UNIT_MEASURE", "")).strip()
        if unit and unit != "PA":
            continue

        period_text = str(row.get("TIME_PERIOD", "")).strip()
        try:
            period = pd.Period(period_text, freq="M")
        except (TypeError, ValueError):
            continue

        observed = _parse_float(row.get("OBS_VALUE"))
        if observed is None:
            continue

        key = (period, ref)
        if key in seen:
            raise ValueError(
                f"duplicate OECD monthly rate for {ref} in {period}"
            )
        seen.add(key)
        # OECD IR3TIB unit PA is percent per annum.
        rows.append((period, ref, observed / 100.0))

    if not rows:
        raise ValueError("no frozen M027 OECD short-rate observations found")

    long = pd.DataFrame(rows, columns=["month", "ref_area", "annual_decimal"])
    panel = long.pivot(
        index="month",
        columns="ref_area",
        values="annual_decimal",
    )
    panel = panel.reindex(columns=M027_RATE_REFS).sort_index()
    panel.columns.name = None
    return panel.astype(float)


def _validate_spot_panel(spot: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(spot.index, pd.DatetimeIndex):
        raise TypeError("spot panel must use a DatetimeIndex")
    if spot.index.has_duplicates:
        raise ValueError("spot panel dates must be unique")
    clean = spot.reindex(columns=M027_CURRENCIES).sort_index().astype(float)
    finite = clean.to_numpy(dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size and np.any(finite <= 0):
        raise ValueError("normalized spot values must be strictly positive")
    return clean


def _validate_rate_panel(rates: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(rates.index, pd.PeriodIndex):
        raise TypeError("rate panel must use a monthly PeriodIndex")
    if rates.index.freqstr != "M":
        raise ValueError("rate panel must use monthly periods")
    if rates.index.has_duplicates:
        raise ValueError("rate panel months must be unique")
    missing = [ref for ref in M027_RATE_REFS if ref not in rates.columns]
    if missing:
        raise ValueError(f"rate panel missing frozen references: {missing}")
    return rates.reindex(columns=M027_RATE_REFS).sort_index().astype(float)


def carry_aware_daily_excess_log_returns(
    spot_usd_per_fx: pd.DataFrame,
    monthly_rates_decimal: pd.DataFrame,
) -> pd.DataFrame:
    """Construct the frozen M027 daily approximation with prior-month carry.

    For every observation date in month M, carry uses foreign and USD rates
    from completed month M-1. Missing inputs remain missing.
    """

    spot = _validate_spot_panel(spot_usd_per_fx)
    rates = _validate_rate_panel(monthly_rates_decimal)

    log_spot = np.log(spot)
    spot_log_return = log_spot.diff()

    current_months = spot.index.tz_convert("UTC").tz_localize(None).to_period("M")
    prior_months = current_months - 1

    aligned_rates = rates.reindex(prior_months)
    aligned_rates.index = spot.index

    out = pd.DataFrame(
        np.nan,
        index=spot.index,
        columns=M027_CURRENCIES,
        dtype=float,
    )
    usd_rate = aligned_rates["USA"]

    for currency, (foreign_ref, _) in M027_IDENTITIES.items():
        carry = aligned_rates[foreign_ref] - usd_rate
        out[currency] = (
            spot_log_return[currency]
            + carry / M027_TRADING_DAYS
        )

    return out


def source_snapshot_report(
    *,
    bis_raw: bytes,
    oecd_raw: bytes,
    spot_panel: pd.DataFrame,
    rate_panel: pd.DataFrame,
    approximate_returns: pd.DataFrame,
) -> dict[str, object]:
    """Return non-economic immutable-source/schema metadata only."""

    return {
        "bis_raw_sha256": sha256_bytes(bis_raw),
        "oecd_raw_sha256": sha256_bytes(oecd_raw),
        "universe_sha256": M027_UNIVERSE_SHA256,
        "currencies": list(M027_CURRENCIES),
        "currency_count": len(M027_CURRENCIES),
        "spot_first_date": (
            None if spot_panel.empty else spot_panel.index.min().date().isoformat()
        ),
        "spot_last_date": (
            None if spot_panel.empty else spot_panel.index.max().date().isoformat()
        ),
        "rate_first_month": (
            None if rate_panel.empty else str(rate_panel.index.min())
        ),
        "rate_last_month": (
            None if rate_panel.empty else str(rate_panel.index.max())
        ),
        "approx_first_date": (
            None
            if approximate_returns.empty
            else approximate_returns.index.min().date().isoformat()
        ),
        "approx_last_date": (
            None
            if approximate_returns.empty
            else approximate_returns.index.max().date().isoformat()
        ),
        "observation_values_reported": False,
        "strategy_signal_computed": False,
        "portfolio_economics_computed": False,
    }
