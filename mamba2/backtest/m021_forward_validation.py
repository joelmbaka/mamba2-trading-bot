"""Frozen prospective-validation machinery for Milestone 021.

This module deliberately reuses the accepted M020-D broker treatment rather
than changing it.  It refuses economic execution before the frozen cutoff and
produces deterministic control/candidate evidence only for one of the
predeclared prospective windows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .baseline import write_baseline_report
from .diagnostics import run_diagnostic_baseline, write_diagnostic_report
from .m020_spread_treatment import (
    M020_D_MAX_DECISION_SPREAD_POINTS,
    run_m020d_treatment,
)


M021_START_UTC = pd.Timestamp("2026-09-25T00:00:00Z")
M021_PRIMARY_END_UTC = pd.Timestamp("2026-10-23T00:00:00Z")
M021_FROZEN_ENDS_UTC = tuple(
    pd.Timestamp(value)
    for value in (
        "2026-10-23T00:00:00Z",
        "2026-10-30T00:00:00Z",
        "2026-11-06T00:00:00Z",
        "2026-11-13T00:00:00Z",
        "2026-11-20T00:00:00Z",
    )
)
M021_MAX_END_UTC = M021_FROZEN_ENDS_UTC[-1]
M021_COST_LABEL = (
    "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
    "SWAP-UNMODELED"
)
M021_CONTROL_MIN_CLOSED = 1000
M021_CANDIDATE_MIN_CLOSED = 900
M021_CANDIDATE_MIN_CLOSED_PER_SYMBOL = 100
M021_CANDIDATE_MIN_CLOSED_PER_SIDE = 300
M021_SYMBOLS = ("EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY")


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _iso(value: Any) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _sha256_path(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def readiness(
    *,
    now_utc: Any,
    cutoff_utc: Any = M021_PRIMARY_END_UTC,
) -> dict[str, Any]:
    """Return the frozen cutoff readiness without touching market data."""

    now = _utc(now_utc)
    cutoff = _utc(cutoff_utc)
    if cutoff not in M021_FROZEN_ENDS_UTC:
        raise ValueError("cutoff is not one of the frozen M021 cutoffs")
    return {
        "ready": bool(now >= cutoff),
        "now_utc": _iso(now),
        "prospective_start_utc": _iso(M021_START_UTC),
        "cutoff_utc": _iso(cutoff),
        "economic_results_computed": False,
    }


def _manifest_payload(
    manifest_path: str | Path,
    *,
    cutoff_utc: Any,
) -> dict[str, Any]:
    path = Path(manifest_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    requested = payload.get("requested_range") or {}
    expected = {
        "from_utc": _iso(M021_START_UTC),
        "to_utc": _iso(cutoff_utc),
    }
    if requested != expected:
        raise ValueError(
            "M021 manifest range mismatch: "
            f"expected {expected}, got {requested}"
        )
    if set(payload.get("symbols", {})) != set(M021_SYMBOLS):
        raise ValueError("M021 manifest must contain exactly the frozen symbols")
    for symbol in M021_SYMBOLS:
        entry = payload["symbols"][symbol]
        files = entry.get("files") or {}
        if not all(name in files for name in ("M1", "M5", "M15")):
            raise ValueError(f"M021 manifest is missing native bars for {symbol}")
        ask = entry.get("ask_m1") or {}
        if ask.get("source") != "copy_ticks_range":
            raise ValueError(f"M021 Ask M1 is not tick-derived for {symbol}")
    return payload


def _period_index(timestamp: Any, *, cutoff_utc: Any) -> int:
    value = _utc(timestamp)
    cutoff = _utc(cutoff_utc)
    if value < M021_START_UTC or value >= cutoff:
        raise ValueError("trade timestamp falls outside frozen M021 window")
    return int((value - M021_START_UTC) // pd.Timedelta(days=7))


def _trade_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "closed_trades": len(rows),
        "wins": sum(row.get("outcome") == "win" for row in rows),
        "losses": sum(row.get("outcome") == "loss" for row in rows),
        "flats": sum(row.get("outcome") == "flat" for row in rows),
        "net_realized_pl": float(
            sum(float(row.get("net_realized_pl", 0.0)) for row in rows)
        ),
    }


def _group_trade_stats(
    rows: Sequence[Mapping[str, Any]],
    key,
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key(row))].append(row)
    return {
        name: _trade_stats(group)
        for name, group in sorted(grouped.items())
    }


def _period_stats(
    rows: Sequence[Mapping[str, Any]],
    *,
    cutoff_utc: Any,
) -> dict[str, Any]:
    cutoff = _utc(cutoff_utc)
    periods = int((cutoff - M021_START_UTC) // pd.Timedelta(days=7))
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_period_index(row["entry_time_utc"], cutoff_utc=cutoff)].append(
            row
        )
    output = {}
    for index in range(periods):
        start = M021_START_UTC + pd.Timedelta(days=7 * index)
        end = start + pd.Timedelta(days=7)
        output[f"P{index + 1:02d}"] = {
            "from_utc": _iso(start),
            "to_utc": _iso(end),
            **_trade_stats(grouped.get(index, [])),
        }
    return output


def _group_delta(
    candidate: Mapping[str, Mapping[str, Any]],
    control: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    names = sorted(set(control) | set(candidate))
    return {
        name: {
            "control_closed_trades": int(
                (control.get(name) or {}).get("closed_trades", 0)
            ),
            "candidate_closed_trades": int(
                (candidate.get(name) or {}).get("closed_trades", 0)
            ),
            "control_net_realized_pl": float(
                (control.get(name) or {}).get("net_realized_pl", 0.0)
            ),
            "candidate_net_realized_pl": float(
                (candidate.get(name) or {}).get("net_realized_pl", 0.0)
            ),
            "net_realized_pl_delta": float(
                (candidate.get(name) or {}).get("net_realized_pl", 0.0)
                - (control.get(name) or {}).get("net_realized_pl", 0.0)
            ),
        }
        for name in names
    }


def _safety_gates(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    wrong_side = []
    negative_tp = []
    for trade in trades:
        protection = trade.get("initial_protection") or {}
        target = protection.get("applied_tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        if target is not None and entry is not None:
            if (
                side == "BUY" and float(target) <= float(entry)
            ) or (
                side == "SELL" and float(target) >= float(entry)
            ):
                wrong_side.append(int(trade["position_ticket"]))
        if (
            trade.get("exit_reason") == "take_profit"
            and float(trade.get("net_realized_pl", 0.0)) < 0
        ):
            negative_tp.append(int(trade["position_ticket"]))
    return {
        "wrong_side_initial_tp_violation_count": len(wrong_side),
        "wrong_side_initial_tp_position_tickets": wrong_side,
        "negative_pl_take_profit_count": len(negative_tp),
        "negative_pl_take_profit_position_tickets": negative_tp,
    }


def _rejection_stats(
    rejected: Sequence[Mapping[str, Any]],
    *,
    cutoff_utc: Any,
) -> dict[str, Any]:
    spreads = [
        float(row["spread_points"])
        for row in rejected
        if row.get("spread_points") is not None
    ]
    by_symbol: dict[str, int] = defaultdict(int)
    by_side: dict[str, int] = defaultdict(int)
    by_period: dict[str, int] = defaultdict(int)
    invalid = 0
    for row in rejected:
        by_symbol[str(row.get("symbol"))] += 1
        by_side[str(row.get("side"))] += 1
        spread = row.get("spread_points")
        if spread is not None and float(spread) <= M020_D_MAX_DECISION_SPREAD_POINTS:
            invalid += 1
        timestamp = row.get("timestamp_utc")
        if timestamp is not None:
            index = _period_index(timestamp, cutoff_utc=cutoff_utc)
            by_period[f"P{index + 1:02d}"] += 1
    return {
        "rejected_order_count": len(rejected),
        "minimum_rejected_decision_spread_points": min(spreads)
        if spreads
        else None,
        "maximum_rejected_decision_spread_points": max(spreads)
        if spreads
        else None,
        "treatment_rejections_at_or_below_10_points": invalid,
        "by_symbol": dict(sorted(by_symbol.items())),
        "by_side": dict(sorted(by_side.items())),
        "by_period": dict(sorted(by_period.items())),
    }


def _minimum_evidence(
    control_baseline: Mapping[str, Any],
    candidate_baseline: Mapping[str, Any],
    candidate_by_side: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    control_closed = int(control_baseline["aggregate"]["closed_trades"])
    candidate_closed = int(candidate_baseline["aggregate"]["closed_trades"])
    per_symbol = candidate_baseline.get("per_symbol") or {}
    symbol_counts = {
        symbol: int((per_symbol.get(symbol) or {}).get("closed_trades", 0))
        for symbol in M021_SYMBOLS
    }
    side_counts = {
        side: int((candidate_by_side.get(side) or {}).get("closed_trades", 0))
        for side in ("BUY", "SELL")
    }
    checks = {
        "control_closed_trades": control_closed >= M021_CONTROL_MIN_CLOSED,
        "candidate_closed_trades": (
            candidate_closed >= M021_CANDIDATE_MIN_CLOSED
        ),
        "each_symbol": all(
            count >= M021_CANDIDATE_MIN_CLOSED_PER_SYMBOL
            for count in symbol_counts.values()
        ),
        "both_sides": all(
            count >= M021_CANDIDATE_MIN_CLOSED_PER_SIDE
            for count in side_counts.values()
        ),
    }
    return {
        "satisfied": all(checks.values()),
        "checks": checks,
        "observed": {
            "control_closed_trades": control_closed,
            "candidate_closed_trades": candidate_closed,
            "candidate_closed_trades_by_symbol": symbol_counts,
            "candidate_closed_trades_by_side": side_counts,
        },
        "minimums": {
            "control_closed_trades": M021_CONTROL_MIN_CLOSED,
            "candidate_closed_trades": M021_CANDIDATE_MIN_CLOSED,
            "candidate_closed_trades_per_symbol": (
                M021_CANDIDATE_MIN_CLOSED_PER_SYMBOL
            ),
            "candidate_closed_trades_per_side": M021_CANDIDATE_MIN_CLOSED_PER_SIDE,
        },
    }


def _classification(
    *,
    cutoff_utc: Any,
    count_gate: Mapping[str, Any],
    deterministic: bool,
    boundary_ok: bool,
    safety_ok: bool,
    control_baseline: Mapping[str, Any],
    candidate_baseline: Mapping[str, Any],
    symbol_delta: Mapping[str, Mapping[str, Any]],
    side_delta: Mapping[str, Mapping[str, Any]],
    period_delta: Mapping[str, Mapping[str, Any]],
) -> str:
    if not (deterministic and boundary_ok and safety_ok):
        return "INVALID"

    if not count_gate["satisfied"]:
        if _utc(cutoff_utc) >= M021_MAX_END_UTC:
            return "INSUFFICIENT FOR CLASSIFICATION"
        return "EXTEND WITHOUT ECONOMIC INTERPRETATION"

    control = control_baseline["aggregate"]
    candidate = candidate_baseline["aggregate"]

    c_pl = float(candidate["net_realized_pl"])
    ctrl_pl = float(control["net_realized_pl"])
    c_dd = float(candidate["maximum_equity_drawdown"])
    ctrl_dd = float(control["maximum_equity_drawdown"])
    c_dd_pct = float(candidate["maximum_equity_drawdown_pct"])
    ctrl_dd_pct = float(control["maximum_equity_drawdown_pct"])

    if c_pl <= ctrl_pl or (c_dd > ctrl_dd and c_dd_pct > ctrl_dd_pct):
        return "NOT SUPPORTED"

    symbol_nonnegative = sum(
        float(row["net_realized_pl_delta"]) >= 0
        for row in symbol_delta.values()
    )
    side_nonnegative = all(
        float(row["net_realized_pl_delta"]) >= 0
        for row in side_delta.values()
    )
    required_periods = math.ceil(0.75 * len(period_delta))
    period_nonnegative = sum(
        float(row["net_realized_pl_delta"]) >= 0
        for row in period_delta.values()
    )

    if (
        c_pl > 0
        and c_pl > ctrl_pl
        and c_dd <= ctrl_dd
        and c_dd_pct <= ctrl_dd_pct
        and symbol_nonnegative >= 4
        and side_nonnegative
        and period_nonnegative >= required_periods
    ):
        return "FORWARD-SUPPORTED"

    return "MIXED"


def build_m021_report(
    *,
    manifest_path: str | Path,
    cutoff_utc: Any,
    control_baseline: Mapping[str, Any],
    control_diagnostic: Mapping[str, Any],
    candidate_baseline: Mapping[str, Any],
    candidate_diagnostic: Mapping[str, Any],
    candidate_evidence: Mapping[str, Any],
    deterministic: bool,
) -> dict[str, Any]:
    cutoff = _utc(cutoff_utc)
    manifest = _manifest_payload(manifest_path, cutoff_utc=cutoff)

    control_trades = list(control_diagnostic.get("trades", []))
    candidate_trades = list(candidate_diagnostic.get("trades", []))

    control_by_symbol = _group_trade_stats(
        control_trades, lambda row: row["symbol"]
    )
    candidate_by_symbol = _group_trade_stats(
        candidate_trades, lambda row: row["symbol"]
    )
    control_by_side = _group_trade_stats(control_trades, lambda row: row["side"])
    candidate_by_side = _group_trade_stats(
        candidate_trades, lambda row: row["side"]
    )
    control_by_period = _period_stats(control_trades, cutoff_utc=cutoff)
    candidate_by_period = _period_stats(candidate_trades, cutoff_utc=cutoff)

    symbol_delta = _group_delta(candidate_by_symbol, control_by_symbol)
    side_delta = _group_delta(candidate_by_side, control_by_side)
    period_delta = _group_delta(candidate_by_period, control_by_period)

    rejected = list(candidate_evidence.get("rejected_orders", []))
    rejection = _rejection_stats(rejected, cutoff_utc=cutoff)

    accepted_violations = int(
        candidate_evidence.get("accepted_spread_violation_count", 0)
    )
    max_accepted = candidate_evidence.get(
        "maximum_accepted_decision_spread_points"
    )
    boundary_ok = (
        accepted_violations == 0
        and rejection["treatment_rejections_at_or_below_10_points"] == 0
        and (
            max_accepted is None
            or float(max_accepted) <= M020_D_MAX_DECISION_SPREAD_POINTS
        )
        and (
            rejection["minimum_rejected_decision_spread_points"] is None
            or float(rejection["minimum_rejected_decision_spread_points"])
            > M020_D_MAX_DECISION_SPREAD_POINTS
        )
    )

    safety = _safety_gates(candidate_trades)
    treatment = candidate_evidence.get("treatment") or {}
    safety_ok = bool(
        safety["wrong_side_initial_tp_violation_count"] == 0
        and safety["negative_pl_take_profit_count"] == 0
        and treatment.get("m020_a_session_filter_stacked") is False
    )

    count_gate = _minimum_evidence(
        control_baseline,
        candidate_baseline,
        candidate_by_side,
    )

    classification = _classification(
        cutoff_utc=cutoff,
        count_gate=count_gate,
        deterministic=deterministic,
        boundary_ok=boundary_ok,
        safety_ok=safety_ok,
        control_baseline=control_baseline,
        candidate_baseline=candidate_baseline,
        symbol_delta=symbol_delta,
        side_delta=side_delta,
        period_delta=period_delta,
    )

    file_hashes = {}
    for symbol in M021_SYMBOLS:
        entry = manifest["symbols"][symbol]
        file_hashes[symbol] = {
            name: meta["sha256"]
            for name, meta in sorted((entry.get("files") or {}).items())
        }
        file_hashes[symbol]["ASK_M1"] = entry["ask_m1"]["sha256"]

    return {
        "milestone": "M021",
        "protocol": {
            "prospective_start_utc": _iso(M021_START_UTC),
            "cutoff_utc": _iso(cutoff),
            "frozen_candidate": "M020-D decision-time spread >10 rejection",
            "cost_label": M021_COST_LABEL,
        },
        "dataset": {
            "manifest_path": str(manifest_path),
            "manifest_sha256": _sha256_path(manifest_path),
            "requested_range": manifest.get("requested_range"),
            "artifact_sha256": file_hashes,
        },
        "determinism": {"arm_artifacts_byte_identical": deterministic},
        "minimum_evidence": count_gate,
        "spread_boundary": {
            "accepted_spread_violation_count": accepted_violations,
            "maximum_accepted_decision_spread_points": max_accepted,
            **rejection,
            "ok": boundary_ok,
        },
        "safety": {**safety, "m020_a_session_filter_stacked": treatment.get(
            "m020_a_session_filter_stacked"
        ), "ok": safety_ok},
        "control": {
            "aggregate": control_baseline["aggregate"],
            "by_symbol": control_by_symbol,
            "by_side": control_by_side,
            "by_period": control_by_period,
        },
        "candidate": {
            "aggregate": candidate_baseline["aggregate"],
            "by_symbol": candidate_by_symbol,
            "by_side": candidate_by_side,
            "by_period": candidate_by_period,
        },
        "effect": {
            "aggregate": {
                key: float(candidate_baseline["aggregate"][key])
                - float(control_baseline["aggregate"][key])
                for key in (
                    "accepted_orders",
                    "closed_trades",
                    "net_realized_pl",
                    "ending_equity",
                    "maximum_equity_drawdown",
                    "maximum_equity_drawdown_pct",
                )
            },
            "by_symbol": symbol_delta,
            "by_side": side_delta,
            "by_period": period_delta,
        },
        "classification": classification,
        "live_trading_authorized": False,
    }


def _run_control(
    manifest_path: str | Path,
    *,
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    starting_balance: float,
) -> dict[str, Any]:
    baseline, diagnostic = run_diagnostic_baseline(
        manifest_path,
        starting_balance=starting_balance,
    )
    baseline_path = write_baseline_report(baseline, baseline_output)
    baseline_sha = _sha256_path(baseline_path)
    diagnostic["source_baseline_sha256"] = baseline_sha
    diagnostic_path = write_diagnostic_report(diagnostic, diagnostic_output)
    return {
        "baseline_path": str(baseline_path),
        "baseline_sha256": baseline_sha,
        "diagnostic_path": str(diagnostic_path),
        "diagnostic_sha256": _sha256_path(diagnostic_path),
    }


def run_m021_window(
    manifest_path: str | Path,
    *,
    output_dir: str | Path,
    cutoff_utc: Any,
    now_utc: Any,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    """Run the frozen paired window, refusing all pre-cutoff execution."""

    cutoff = _utc(cutoff_utc)
    gate = readiness(now_utc=now_utc, cutoff_utc=cutoff)
    if not gate["ready"]:
        return {
            "ok": False,
            "reason": "frozen M021 cutoff is not complete",
            **gate,
        }

    _manifest_payload(manifest_path, cutoff_utc=cutoff)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    control_runs = []
    candidate_runs = []
    for suffix in ("a", "b"):
        control_runs.append(
            _run_control(
                manifest_path,
                baseline_output=output / f"control-baseline-{suffix}.json",
                diagnostic_output=output / f"control-diagnostic-{suffix}.json",
                starting_balance=starting_balance,
            )
        )
        candidate_runs.append(
            run_m020d_treatment(
                manifest_path,
                baseline_output=output / f"candidate-baseline-{suffix}.json",
                diagnostic_output=output / f"candidate-diagnostic-{suffix}.json",
                evidence_output=output / f"candidate-evidence-{suffix}.json",
                starting_balance=starting_balance,
            )
        )

    artifact_pairs = (
        ("control-baseline", control_runs[0]["baseline_path"], control_runs[1]["baseline_path"]),
        ("control-diagnostic", control_runs[0]["diagnostic_path"], control_runs[1]["diagnostic_path"]),
        ("candidate-baseline", candidate_runs[0]["baseline_path"], candidate_runs[1]["baseline_path"]),
        ("candidate-diagnostic", candidate_runs[0]["diagnostic_path"], candidate_runs[1]["diagnostic_path"]),
        ("candidate-evidence", candidate_runs[0]["evidence_path"], candidate_runs[1]["evidence_path"]),
    )
    pair_hashes = {}
    deterministic = True
    for name, left, right in artifact_pairs:
        left_path = Path(left)
        right_path = Path(right)
        identical = left_path.read_bytes() == right_path.read_bytes()
        deterministic = deterministic and identical
        pair_hashes[name] = {
            "identical": identical,
            "sha256_a": _sha256_path(left_path),
            "sha256_b": _sha256_path(right_path),
        }

    control_baseline = json.loads(
        Path(control_runs[0]["baseline_path"]).read_text(encoding="utf-8")
    )
    control_diagnostic = json.loads(
        Path(control_runs[0]["diagnostic_path"]).read_text(encoding="utf-8")
    )
    candidate_baseline = json.loads(
        Path(candidate_runs[0]["baseline_path"]).read_text(encoding="utf-8")
    )
    candidate_diagnostic = json.loads(
        Path(candidate_runs[0]["diagnostic_path"]).read_text(encoding="utf-8")
    )
    candidate_evidence = json.loads(
        Path(candidate_runs[0]["evidence_path"]).read_text(encoding="utf-8")
    )

    report = build_m021_report(
        manifest_path=manifest_path,
        cutoff_utc=cutoff,
        control_baseline=control_baseline,
        control_diagnostic=control_diagnostic,
        candidate_baseline=candidate_baseline,
        candidate_diagnostic=candidate_diagnostic,
        candidate_evidence=candidate_evidence,
        deterministic=deterministic,
    )
    report["artifact_pairs"] = pair_hashes
    report_path = output / "m021-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": bool(
            deterministic
            and report["spread_boundary"]["ok"]
            and report["safety"]["ok"]
        ),
        "economic_results_computed": True,
        "classification": report["classification"],
        "report_path": str(report_path),
        "report_sha256": _sha256_path(report_path),
        "artifact_pairs": pair_hashes,
        "minimum_evidence": report["minimum_evidence"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen M021 prospective control/candidate pair."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cutoff-utc", required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_m021_window(
        args.manifest,
        output_dir=args.output_dir,
        cutoff_utc=args.cutoff_utc,
        now_utc=args.now_utc,
        starting_balance=args.starting_balance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
