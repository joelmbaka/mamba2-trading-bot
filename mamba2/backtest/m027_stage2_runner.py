"""M027 deterministic Stage-2 economic report runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .m027_stage2 import (
    M027_FROZEN_MONTH_LIST_SHA256,
    load_frozen_approximate_returns,
    stage2_economics,
)


def build_report(input_path: str | Path) -> dict[str, object]:
    daily = load_frozen_approximate_returns(input_path)
    return stage2_economics(
        daily,
        expected_month_list_sha256=M027_FROZEN_MONTH_LIST_SHA256,
    )


def write_report(input_path: str | Path, output_path: str | Path) -> dict[str, object]:
    report = build_report(input_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = write_report(args.input, args.output)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
