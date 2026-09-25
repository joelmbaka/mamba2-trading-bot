"""Deterministic control/treatment experiment harness for historical replay.

M020 starts by proving that the control arm is byte-identical to the accepted
M019 replay before any treatment is introduced.  Treatment support is added
only after that control gate is accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from .baseline import write_baseline_report
from .diagnostics import run_diagnostic_baseline, write_diagnostic_report


@dataclass(frozen=True)
class ExperimentDefinition:
    """Immutable metadata for one controlled experiment."""

    experiment_id: str
    hypothesis: str


M020_A = ExperimentDefinition(
    experiment_id="M020-A",
    hypothesis=(
        "New entries during 00:00-03:59 UTC are a persistently harmful "
        "exposure."
    ),
)


class UtcEntrySessionFilterStrategy:
    """Experiment-only wrapper that suppresses new entries in one UTC window.

    The wrapper does not alter market data, existing positions, ATR refresh,
    position management, or the wrapped strategy outside the blocked interval.
    PortfolioBacktestRunner still runs PositionManager once per boundary.
    """

    def __init__(
        self,
        strategy: Any,
        *,
        start_hour: int = 0,
        end_hour: int = 4,
    ):
        if not 0 <= start_hour <= 23:
            raise ValueError("start_hour must be between 0 and 23")
        if not 1 <= end_hour <= 24:
            raise ValueError("end_hour must be between 1 and 24")
        if start_hour >= end_hour:
            raise ValueError("start_hour must be earlier than end_hour")
        self.strategy = strategy
        self.symbol = strategy.symbol
        self.start_hour = int(start_hour)
        self.end_hour = int(end_hour)
        self.blocked_evaluation_boundaries = 0

    @staticmethod
    def _utc_timestamp(value: Any) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    async def evaluate(self, market: dict[str, Any]) -> None:
        current = getattr(market["rate_fetcher"], "current_time", None)
        if current is not None:
            hour = self._utc_timestamp(current).hour
            if self.start_hour <= hour < self.end_hour:
                self.blocked_evaluation_boundaries += 1
                return
        await self.strategy.evaluate(market)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _persist_arm_reports(
    *,
    arm: str,
    baseline_report: dict[str, Any],
    diagnostic_report: dict[str, Any],
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_path = write_baseline_report(
        baseline_report,
        baseline_output,
    )
    baseline_sha = _sha256_path(baseline_path)

    # Match the accepted diagnostic CLI contract exactly: diagnostics identify
    # the baseline bytes they were derived from.
    diagnostic_report["source_baseline_sha256"] = baseline_sha
    diagnostic_path = write_diagnostic_report(
        diagnostic_report,
        diagnostic_output,
    )
    diagnostic_sha = _sha256_path(diagnostic_path)

    return {
        "experiment_id": M020_A.experiment_id,
        "hypothesis": M020_A.hypothesis,
        "arm": arm,
        "baseline_path": str(baseline_path),
        "baseline_sha256": baseline_sha,
        "diagnostic_path": str(diagnostic_path),
        "diagnostic_sha256": diagnostic_sha,
        "aggregate": baseline_report["aggregate"],
        **(extra or {}),
    }


def run_control_arm(
    manifest_path: str | Path,
    *,
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    """Run the unchanged accepted strategy and persist deterministic evidence."""

    baseline_report, diagnostic_report = run_diagnostic_baseline(
        manifest_path,
        starting_balance=starting_balance,
    )
    return _persist_arm_reports(
        arm="control",
        baseline_report=baseline_report,
        diagnostic_report=diagnostic_report,
        baseline_output=baseline_output,
        diagnostic_output=diagnostic_output,
    )


def run_m020a_treatment_arm(
    manifest_path: str | Path,
    *,
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    """Run only the M020-A 00:00-03:59 UTC new-entry suppression."""

    wrappers: list[UtcEntrySessionFilterStrategy] = []

    def transform(strategy: Any) -> UtcEntrySessionFilterStrategy:
        wrapper = UtcEntrySessionFilterStrategy(
            strategy,
            start_hour=0,
            end_hour=4,
        )
        wrappers.append(wrapper)
        return wrapper

    baseline_report, diagnostic_report = run_diagnostic_baseline(
        manifest_path,
        starting_balance=starting_balance,
        strategy_transform=transform,
    )
    return _persist_arm_reports(
        arm="m020-a-treatment",
        baseline_report=baseline_report,
        diagnostic_report=diagnostic_report,
        baseline_output=baseline_output,
        diagnostic_output=diagnostic_output,
        extra={
            "treatment": {
                "blocked_utc_start": "00:00:00",
                "blocked_utc_end_exclusive": "04:00:00",
                "behavior": "suppress new-entry strategy evaluation only",
            },
            "blocked_evaluation_boundaries": sum(
                wrapper.blocked_evaluation_boundaries
                for wrapper in wrappers
            ),
        },
    )


def verify_control_hashes(
    result: dict[str, Any],
    *,
    expected_baseline_sha256: str,
    expected_diagnostic_sha256: str,
) -> dict[str, Any]:
    """Require exact accepted-M019 control bytes before treatment work."""

    baseline_ok = (
        result["baseline_sha256"] == expected_baseline_sha256
    )
    diagnostic_ok = (
        result["diagnostic_sha256"] == expected_diagnostic_sha256
    )
    return {
        **result,
        "expected_baseline_sha256": expected_baseline_sha256,
        "expected_diagnostic_sha256": expected_diagnostic_sha256,
        "baseline_preserved": baseline_ok,
        "diagnostic_preserved": diagnostic_ok,
        "ok": bool(baseline_ok and diagnostic_ok),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic M020 control or treatment arm."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline-output", required=True)
    parser.add_argument("--diagnostic-output", required=True)
    parser.add_argument(
        "--arm",
        choices=("control", "m020-a"),
        default="control",
    )
    parser.add_argument("--expected-baseline-sha256")
    parser.add_argument("--expected-diagnostic-sha256")
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    if args.arm == "control":
        if (
            not args.expected_baseline_sha256
            or not args.expected_diagnostic_sha256
        ):
            parser.error(
                "control arm requires both expected accepted-M019 hashes"
            )
        result = run_control_arm(
            args.manifest,
            baseline_output=args.baseline_output,
            diagnostic_output=args.diagnostic_output,
            starting_balance=args.starting_balance,
        )
        verified = verify_control_hashes(
            result,
            expected_baseline_sha256=args.expected_baseline_sha256,
            expected_diagnostic_sha256=args.expected_diagnostic_sha256,
        )
        print(json.dumps(verified, sort_keys=True))
        return 0 if verified["ok"] else 2

    result = run_m020a_treatment_arm(
        args.manifest,
        baseline_output=args.baseline_output,
        diagnostic_output=args.diagnostic_output,
        starting_balance=args.starting_balance,
    )
    print(json.dumps({**result, "ok": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
