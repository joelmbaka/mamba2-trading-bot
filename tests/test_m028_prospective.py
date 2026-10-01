"""Synthetic-only tests for M028 prospective decision helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from mamba2.backtest.m027_carry_aware_tsmom import M027_CURRENCIES
from mamba2.backtest.m028_prospective import (
    M028_FIRST_DECISION_UTC,
    assert_first_decision_time,
    previous_completed_month_end,
    signal_snapshot_from_daily,
)


def test_first_decision_time_gate_refuses_early_execution():
    with pytest.raises(RuntimeError, match="time-gated"):
        assert_first_decision_time(
            datetime(2026, 10, 7, 11, 59, 59, tzinfo=timezone.utc)
        )

    assert_first_decision_time(M028_FIRST_DECISION_UTC)


def test_previous_completed_month_end_for_october_decision_is_september():
    assert previous_completed_month_end(M028_FIRST_DECISION_UTC) == pd.Timestamp(
        "2026-09-30T00:00:00Z"
    )


def _synthetic_daily_panel() -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-01",
        "2026-09-30",
        freq="B",
        tz="UTC",
    )
    step = np.arange(len(index), dtype=float)
    data = {}
    for i, currency in enumerate(M027_CURRENCIES):
        if currency == "AUD":
            data[currency] = 0.0003 + np.sin(step / 17.0) * 0.0002
        elif currency == "CAD":
            data[currency] = -0.0003 + np.sin(step / 19.0) * 0.0002
        else:
            data[currency] = (
                0.00005
                + (i % 3) * 0.000001
                + np.sin(step / (23.0 + i)) * 0.0002
            )
    return pd.DataFrame(data, index=index)


def test_signal_snapshot_uses_only_completed_september_month():
    result = signal_snapshot_from_daily(
        _synthetic_daily_panel(),
        decision=M028_FIRST_DECISION_UTC,
    )

    assert result["decision_id"] == "2026-10"
    assert result["formation_month_end"] == "2026-09-30"
    assert result["currencies"]["AUD"]["formation_sign"] == 1
    assert result["currencies"]["CAD"]["formation_sign"] == -1
    assert result["currencies"]["AUD"]["annualized_ex_ante_volatility"] > 0
    assert result["nonflat_signal_eligible_count"] == 8


def test_signal_snapshot_requires_exact_frozen_m027_columns():
    daily = _synthetic_daily_panel().drop(columns=["SEK"])
    with pytest.raises(ValueError, match="frozen M027 currency columns"):
        signal_snapshot_from_daily(
            daily,
            decision=M028_FIRST_DECISION_UTC,
        )
