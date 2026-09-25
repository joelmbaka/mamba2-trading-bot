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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


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
        "arm": "control",
        "baseline_path": str(baseline_path),
        "baseline_sha256": baseline_sha,
        "diagnostic_path": str(diagnostic_path),
        "diagnostic_sha256": diagnostic_sha,
        "aggregate": baseline_report["aggregate"],
    }


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
        description="Run the deterministic M020 experiment control arm."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline-output", required=True)
    parser.add_argument("--diagnostic-output", required=True)
    parser.add_argument("--expected-baseline-sha256", required=True)
    parser.add_argument("--expected-diagnostic-sha256", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

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


if __name__ == "__main__":
    raise SystemExit(main())
