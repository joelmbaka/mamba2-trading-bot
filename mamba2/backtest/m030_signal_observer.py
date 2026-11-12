"""Opt-in M030 candidate-signal snapshot on causal completed bars.

This independently observes the original baseline conditions using the
existing Python indicator arithmetic. It never sends orders. A candidate
signal is NOT an actual accepted trade; blocked positions are reported by the
runner and the independent MT5 probe does not yet model position blocking.
"""
from __future__ import annotations

from typing import Any

from config import config
from mamba2.indicators.stochastic import get_stochastic
from mamba2.indicators.moving_average import get_moving_average
from mamba2.indicators.atr import get_atr
from .m030_parity import event, utc_millis


def observe_candidate(feed: Any, symbol: str) -> dict[str, Any]:
    if (config.ENABLE_RSI_CONDITION or config.ENABLE_TREND_CONDITION
            or config.use_higher_tf):
        raise ValueError("M030 frozen baseline requires optional signal filters disabled")
    boundary = feed.current_time
    if boundary is None:
        raise ValueError("replay not advanced")
    from datetime import timedelta
    opening = boundary - timedelta(minutes=1)
    m1 = feed.get_visible_rates_for_indicator(symbol, "M1")
    m5 = feed.get_visible_rates_for_indicator(symbol, "M5")
    fields = dict(
        engine="python", kind="SIGNAL", symbol=symbol,
        utc_time_ms=utc_millis(boundary.to_pydatetime()),
        m1_source_open_utc=opening.strftime("%Y-%m-%dT%H:%M:%SZ"),
        signal="NONE",
        reason_or_error_code="INSUFFICIENT_HISTORY",
    )
    if m1.empty or m5.empty:
        return event(**fields)
    fields["m5_source_open_utc"] = m5.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ")
    params = dict(k_period=config.stochastic_k_period,
                  d_period=config.stochastic_d_period,
                  slowing=config.stochastic_slowing,rate_fetcher=feed)
    s1 = get_stochastic(symbol=symbol, timeframe="M1", lookback_period=10, **params)
    s5 = get_stochastic(symbol=symbol, timeframe="M5", **params)
    if s1 is None or s5 is None:
        return event(**fields)
    k1,d1 = float(s1["k"].iloc[-1]),float(s1["d"].iloc[-1])
    k5,d5 = float(s5["k"].iloc[-1]),float(s5["d"].iloc[-1])
    ema = get_moving_average(symbol, "M1", 7, "ema", feed)
    atr = get_atr(symbol=symbol, timeframe="M5", atr_period=14, rate_fetcher=feed)
    fields.update(m1_k=k1,m1_d=d1,m5_k=k5,m5_d=d5,
                  ema=float(ema) if ema is not None else None,
                  atr=float(atr) if atr is not None else None)
    if ema is None:
        fields["reason_or_error_code"]="MISSING_EMA"
        return event(**fields)
    candle = m1.iloc[-1]
    buy = k5>d5 and bool((s1["k"]<20).any()) and k1>d1
    sell = k5<d5 and bool((s1["k"]>80).any()) and k1<d1
    if buy and candle["close"]>ema and candle["close"]>candle["open"]:
        fields["signal"]="BUY"
        fields["reason_or_error_code"]="ENTRY_CONDITIONS"
    elif sell and candle["close"]<ema and candle["close"]<candle["open"]:
        fields["signal"]="SELL"
        fields["reason_or_error_code"]="ENTRY_CONDITIONS"
    elif buy or sell:
        fields["reason_or_error_code"]="EMA_CANDLE_FILTER"
    else:
        fields["reason_or_error_code"]="NO_SIGNAL"
    return event(**fields)
