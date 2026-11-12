from __future__ import annotations

import pytest

from mamba2.backtest.m024_symbol_causal_research import (
    M024_MARKET_DATA_SYMBOLS,
    M024_STAGE2_ARMS,
    Stage2SymbolArm,
    _symbol_entry_counts,
    stage2_arm,
)


def test_stage2_matrix_is_exact_and_bounded():
    assert M024_STAGE2_ARMS == {
        "C-R": M024_MARKET_DATA_SYMBOLS,
        "C-UJ": ("USDJPY",),
    }

    assert stage2_arm("C-R").strategy_symbols == M024_MARKET_DATA_SYMBOLS
    assert stage2_arm("C-UJ").strategy_symbols == ("USDJPY",)

    with pytest.raises(ValueError, match="outside the frozen"):
        stage2_arm("C-JPY")


def test_arm_rejects_post_freeze_symbol_mutation():
    with pytest.raises(ValueError, match="outside the frozen"):
        Stage2SymbolArm(
            arm_id="C-UJ",
            strategy_symbols=("EURJPY", "USDJPY"),
        )


def test_market_data_universe_remains_all_five_even_for_usdjpy_arm():
    arm = stage2_arm("C-UJ")
    assert arm.strategy_symbols == ("USDJPY",)
    assert M024_MARKET_DATA_SYMBOLS == (
        "EURUSD",
        "EURJPY",
        "GBPUSD",
        "GBPJPY",
        "USDJPY",
    )


def test_symbol_entry_counts_refuse_unexpected_symbols():
    rows = [
        {"symbol": "USDJPY"},
        {"symbol": "USDJPY"},
    ]
    counts = _symbol_entry_counts(rows)
    assert counts["USDJPY"] == 2
    assert counts["EURUSD"] == 0

    with pytest.raises(ValueError, match="unexpected M024 trade symbol"):
        _symbol_entry_counts([{"symbol": "AUDUSD"}])


def test_c_uj_excluded_symbols_are_all_non_usdjpy():
    arm = stage2_arm("C-UJ")
    excluded = tuple(
        symbol
        for symbol in M024_MARKET_DATA_SYMBOLS
        if symbol not in arm.strategy_symbols
    )
    assert excluded == ("EURUSD", "EURJPY", "GBPUSD", "GBPJPY")
