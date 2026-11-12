"""Read-only M020-B spread-confound diagnostic tests."""

import hashlib
import json

from mamba2.backtest import m020_diagnostics


def _trade(
    *,
    timestamp,
    spread,
    pl,
    outcome,
    symbol="EURUSD",
    side="BUY",
):
    hour = int(timestamp[11:13])
    return {
        "entry_time_utc": timestamp,
        "entry_utc_hour": hour,
        "entry_spread": {"spread_points": spread},
        "net_realized_pl": pl,
        "outcome": outcome,
        "symbol": symbol,
        "side": side,
    }


def test_spread_bands_are_fixed_and_boundary_stable():
    cases = {
        0.0: "00 <=2",
        2.0: "00 <=2",
        2.1: "01 >2-5",
        5.0: "01 >2-5",
        5.1: "02 >5-10",
        10.0: "02 >5-10",
        10.1: "03 >10-20",
        20.0: "03 >10-20",
        20.1: "04 >20-50",
        50.0: "04 >20-50",
        50.1: "05 >50-100",
        100.0: "05 >50-100",
        100.1: "06 >100",
    }
    for spread, expected in cases.items():
        assert m020_diagnostics._spread_band(spread) == expected


def test_m020b_diagnostic_separates_session_without_strategy_change():
    trades = [
        _trade(
            timestamp="2026-06-23T00:10:00Z",
            spread=2.0,
            pl=-5.0,
            outcome="loss",
            symbol="EURUSD",
            side="BUY",
        ),
        _trade(
            timestamp="2026-07-10T03:59:00Z",
            spread=25.0,
            pl=-20.0,
            outcome="loss",
            symbol="GBPJPY",
            side="SELL",
        ),
        _trade(
            timestamp="2026-08-02T04:00:00Z",
            spread=2.0,
            pl=8.0,
            outcome="win",
            symbol="EURUSD",
            side="BUY",
        ),
        _trade(
            timestamp="2026-09-03T20:00:00Z",
            spread=25.0,
            pl=-2.0,
            outcome="loss",
            symbol="GBPJPY",
            side="SELL",
        ),
    ]

    report = m020_diagnostics.build_m020b_spread_diagnostic(
        {"trades": trades}
    )

    assert report["strategy_behavior_changed"] is False
    blocked = report["blocked_session"]
    outside = report["outside_blocked_session"]
    assert blocked["summary"]["closed_trades"] == 2
    assert blocked["summary"]["net_realized_pl"] == -25.0
    assert outside["summary"]["closed_trades"] == 2
    assert outside["summary"]["net_realized_pl"] == 6.0
    assert blocked["by_spread_band"]["00 <=2"]["closed_trades"] == 1
    assert blocked["by_spread_band"]["04 >20-50"]["closed_trades"] == 1
    assert blocked["by_symbol_and_spread_band"]["GBPJPY"][
        "04 >20-50"
    ]["net_realized_pl"] == -20.0
    assert blocked["by_side_and_spread_band"]["BUY"]["00 <=2"][
        "net_realized_pl"
    ] == -5.0
    assert blocked["by_entry_month_and_spread_band"]["2026-07"][
        "04 >20-50"
    ]["closed_trades"] == 1


def test_m020b_reports_fixed_percentiles():
    trades = [
        _trade(
            timestamp=f"2026-07-01T0{hour}:00:00Z",
            spread=spread,
            pl=-1.0,
            outcome="loss",
        )
        for hour, spread in enumerate((1.0, 2.0, 3.0, 100.0))
    ]

    report = m020_diagnostics.build_m020b_spread_diagnostic(
        {"trades": trades}
    )
    percentiles = report["blocked_session"]["spread_percentiles"]

    assert percentiles["p00"] == 1.0
    assert percentiles["p25"] == 1.75
    assert percentiles["p50"] == 2.5
    assert percentiles["p75"] == 27.25
    assert percentiles["p100"] == 100.0


def test_m020b_file_runner_requires_accepted_control_hash(
    tmp_path,
):
    source = tmp_path / "control-diagnostic.json"
    output = tmp_path / "m020b.json"
    payload = {
        "trades": [
            _trade(
                timestamp="2026-07-01T00:00:00Z",
                spread=4.0,
                pl=-3.0,
                outcome="loss",
            )
        ]
    }
    source.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    accepted_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    rejected = m020_diagnostics.run_m020b_diagnostic(
        source,
        output=output,
        expected_control_diagnostic_sha256="wrong",
    )
    assert rejected["ok"] is False
    assert not output.exists()

    first = m020_diagnostics.run_m020b_diagnostic(
        source,
        output=output,
        expected_control_diagnostic_sha256=accepted_sha,
    )
    first_bytes = output.read_bytes()
    second = m020_diagnostics.run_m020b_diagnostic(
        source,
        output=output,
        expected_control_diagnostic_sha256=accepted_sha,
    )

    assert first["ok"] is True
    assert first["strategy_behavior_changed"] is False
    assert first["output_sha256"] == second["output_sha256"]
    assert output.read_bytes() == first_bytes
