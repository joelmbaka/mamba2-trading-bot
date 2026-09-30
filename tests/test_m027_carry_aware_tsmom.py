"""M027 Stage-1 deterministic approximation tests."""

from __future__ import annotations

import csv
import io
import math
import zipfile

import numpy as np
import pandas as pd
import pytest

from mamba2.backtest.m027_carry_aware_tsmom import (
    M027_CURRENCIES,
    M027_IDENTITIES,
    M027_UNIVERSE_SHA256,
    carry_aware_daily_excess_log_returns,
    parse_bis_daily_spot_zip,
    parse_oecd_monthly_short_rates,
    sha256_bytes,
)


def _bis_zip(rows: list[dict[str, str]]) -> bytes:
    fields = [
        "FREQ:Frequency",
        "REF_AREA:Reference area",
        "CURRENCY:Currency",
        "COLLECTION:Collection",
        "TIME_PERIOD:Time period or range",
        "OBS_VALUE:Observation Value",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("WS_XRU.csv", buf.getvalue())
    return out.getvalue()


def _oecd_csv(rows: list[dict[str, str]]) -> bytes:
    fields = [
        "REF_AREA",
        "FREQ",
        "MEASURE",
        "UNIT_MEASURE",
        "TIME_PERIOD",
        "OBS_VALUE",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def test_frozen_universe_is_exact_and_excludes_crc():
    assert len(M027_CURRENCIES) == 25
    assert M027_CURRENCIES == (
        "AUD", "CAD", "CHF", "CLP", "CNY", "COP", "CZK", "DKK", "EUR",
        "GBP", "HUF", "IDR", "INR", "ISK", "ILS", "JPY", "KRW", "MXN",
        "NOK", "NZD", "PLN", "RON", "RUB", "SEK", "ZAR",
    )
    assert "CRC" not in M027_CURRENCIES
    assert M027_UNIVERSE_SHA256 == (
        "db9e1f4438fd582a0c2903f2459e290e30450bfc76365f2bbe91553d45b51c00"
    )


def test_bis_parser_inverts_foreign_per_usd_quote():
    raw = _bis_zip([
        {
            "FREQ:Frequency": "D:Daily",
            "REF_AREA:Reference area": "AU:Australia",
            "CURRENCY:Currency": "AUD:Australian dollar",
            "COLLECTION:Collection": "A:Average",
            "TIME_PERIOD:Time period or range": "2020-01-02",
            "OBS_VALUE:Observation Value": "2.0",
        },
        {
            "FREQ:Frequency": "D:Daily",
            "REF_AREA:Reference area": "JP:Japan",
            "CURRENCY:Currency": "JPY:Yen",
            "COLLECTION:Collection": "A:Average",
            "TIME_PERIOD:Time period or range": "2020-01-02",
            "OBS_VALUE:Observation Value": "100.0",
        },
    ])

    panel = parse_bis_daily_spot_zip(raw)

    assert panel.loc[pd.Timestamp("2020-01-02", tz="UTC"), "AUD"] == pytest.approx(0.5)
    assert panel.loc[pd.Timestamp("2020-01-02", tz="UTC"), "JPY"] == pytest.approx(0.01)
    assert panel["CAD"].isna().all()


def test_bis_parser_refuses_duplicate_currency_date():
    row = {
        "FREQ:Frequency": "D:Daily",
        "REF_AREA:Reference area": "AU:Australia",
        "CURRENCY:Currency": "AUD:Australian dollar",
        "COLLECTION:Collection": "A:Average",
        "TIME_PERIOD:Time period or range": "2020-01-02",
        "OBS_VALUE:Observation Value": "2.0",
    }
    with pytest.raises(ValueError, match="duplicate BIS daily observation"):
        parse_bis_daily_spot_zip(_bis_zip([row, row]))


def test_oecd_parser_converts_percent_per_annum_to_decimal():
    raw = _oecd_csv([
        {
            "REF_AREA": "USA",
            "FREQ": "M",
            "MEASURE": "IR3TIB",
            "UNIT_MEASURE": "PA",
            "TIME_PERIOD": "2020-01",
            "OBS_VALUE": "2.0",
        },
        {
            "REF_AREA": "AUS",
            "FREQ": "M",
            "MEASURE": "IR3TIB",
            "UNIT_MEASURE": "PA",
            "TIME_PERIOD": "2020-01",
            "OBS_VALUE": "6.0",
        },
    ])

    rates = parse_oecd_monthly_short_rates(raw)

    assert rates.loc[pd.Period("2020-01", freq="M"), "USA"] == pytest.approx(0.02)
    assert rates.loc[pd.Period("2020-01", freq="M"), "AUS"] == pytest.approx(0.06)


def test_previous_completed_month_rate_is_used_without_lookahead():
    dates = pd.DatetimeIndex([
        pd.Timestamp("2020-01-31", tz="UTC"),
        pd.Timestamp("2020-02-03", tz="UTC"),
        pd.Timestamp("2020-02-04", tz="UTC"),
    ])
    spot = pd.DataFrame(np.nan, index=dates, columns=M027_CURRENCIES)
    spot["AUD"] = [1.0, math.exp(0.01), math.exp(0.02)]

    index = pd.period_range("2020-01", "2020-02", freq="M")
    rates = pd.DataFrame(np.nan, index=index, columns=("USA",) + tuple(
        dict.fromkeys(ref for ref, _ in M027_IDENTITIES.values())
    ))
    rates.loc[pd.Period("2020-01", "M"), "USA"] = 0.02
    rates.loc[pd.Period("2020-01", "M"), "AUS"] = 0.06
    # Deliberately extreme current-month values: February returns must not use them.
    rates.loc[pd.Period("2020-02", "M"), "USA"] = -0.50
    rates.loc[pd.Period("2020-02", "M"), "AUS"] = 0.90

    result = carry_aware_daily_excess_log_returns(spot, rates)
    expected = 0.01 + (0.06 - 0.02) / 261.0

    assert result.loc[dates[1], "AUD"] == pytest.approx(expected)
    assert result.loc[dates[2], "AUD"] == pytest.approx(expected)


def test_future_rate_mutation_cannot_change_earlier_month_returns():
    dates = pd.DatetimeIndex([
        pd.Timestamp("2020-01-31", tz="UTC"),
        pd.Timestamp("2020-02-03", tz="UTC"),
        pd.Timestamp("2020-03-02", tz="UTC"),
    ])
    spot = pd.DataFrame(np.nan, index=dates, columns=M027_CURRENCIES)
    spot["AUD"] = [1.0, 1.01, 1.02]

    refs = ("USA",) + tuple(dict.fromkeys(
        ref for ref, _ in M027_IDENTITIES.values()
    ))
    rates = pd.DataFrame(
        np.nan,
        index=pd.period_range("2020-01", "2020-03", freq="M"),
        columns=refs,
    )
    rates.loc[:, "USA"] = [0.01, 0.02, 0.03]
    rates.loc[:, "AUS"] = [0.04, 0.05, 0.06]

    control = carry_aware_daily_excess_log_returns(spot, rates)
    mutated = rates.copy()
    mutated.loc[pd.Period("2020-02", "M"), "AUS"] = 9.99
    treatment = carry_aware_daily_excess_log_returns(spot, mutated)

    feb = pd.Timestamp("2020-02-03", tz="UTC")
    assert treatment.loc[feb, "AUD"] == pytest.approx(control.loc[feb, "AUD"])
    assert treatment.loc[dates[2], "AUD"] != pytest.approx(control.loc[dates[2], "AUD"])


def test_missing_spot_is_not_forward_filled():
    dates = pd.date_range("2020-01-31", periods=3, freq="B", tz="UTC")
    spot = pd.DataFrame(np.nan, index=dates, columns=M027_CURRENCIES)
    spot["AUD"] = [1.0, np.nan, 1.02]

    refs = ("USA",) + tuple(dict.fromkeys(
        ref for ref, _ in M027_IDENTITIES.values()
    ))
    rates = pd.DataFrame(
        np.nan,
        index=pd.period_range("2019-12", "2020-01", freq="M"),
        columns=refs,
    )
    rates.loc[pd.Period("2019-12", "M"), ["USA", "AUS"]] = [0.01, 0.03]

    result = carry_aware_daily_excess_log_returns(spot, rates)

    assert pd.isna(result.loc[dates[1], "AUD"])
    assert pd.isna(result.loc[dates[2], "AUD"])


def test_missing_prior_month_rate_remains_missing():
    dates = pd.DatetimeIndex([
        pd.Timestamp("2020-01-31", tz="UTC"),
        pd.Timestamp("2020-02-03", tz="UTC"),
    ])
    spot = pd.DataFrame(np.nan, index=dates, columns=M027_CURRENCIES)
    spot["AUD"] = [1.0, 1.01]

    refs = ("USA",) + tuple(dict.fromkeys(
        ref for ref, _ in M027_IDENTITIES.values()
    ))
    rates = pd.DataFrame(
        np.nan,
        index=pd.period_range("2020-01", "2020-01", freq="M"),
        columns=refs,
    )
    rates.loc[pd.Period("2020-01", "M"), "USA"] = 0.01
    # AUS deliberately missing.

    result = carry_aware_daily_excess_log_returns(spot, rates)
    assert pd.isna(result.loc[dates[1], "AUD"])


def test_source_hash_is_byte_deterministic():
    assert sha256_bytes(b"m027") == sha256_bytes(b"m027")
    assert sha256_bytes(b"m027") != sha256_bytes(b"M027")
