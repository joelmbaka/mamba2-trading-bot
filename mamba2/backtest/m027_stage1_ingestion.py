"""M027 Stage-1 immutable public-source ingestion.

This is non-strategy research plumbing. It snapshots the frozen BIS/OECD
sources, constructs the frozen no-lookahead daily approximation, writes
deterministic artifacts, and reports hashes/schema metadata only.

It does not compute momentum signals or portfolio/economic statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from .m027_carry_aware_tsmom import (
    BIS_XRU_URL,
    OECD_STIR_URL,
    M027_CURRENCIES,
    carry_aware_daily_excess_log_returns,
    parse_bis_daily_spot_zip,
    parse_oecd_monthly_short_rates,
    sha256_bytes,
    source_snapshot_report,
)


USER_AGENT = "Mozilla/5.0 Mamba2-M027-Ingestion/1.0"


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, *, accept: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    request = Request(url, headers=headers)
    with urlopen(request, timeout=180) as response:
        body = response.read()
    if not body:
        raise RuntimeError(f"empty download from {url}")
    return body


def _write_frame(frame: pd.DataFrame, path: Path, *, index_label: str) -> None:
    frame.to_csv(
        path,
        index=True,
        index_label=index_label,
        float_format="%.17g",
        lineterminator="\n",
    )


def run_stage1_ingestion(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    if output.exists():
        raise FileExistsError(f"M027 Stage-1 output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)

    bis_raw = _download(BIS_XRU_URL)
    oecd_raw = _download(
        OECD_STIR_URL,
        accept="text/csv,application/vnd.sdmx.data+csv;version=2.0.0",
    )

    spot = parse_bis_daily_spot_zip(bis_raw)
    rates = parse_oecd_monthly_short_rates(oecd_raw)
    approximate = carry_aware_daily_excess_log_returns(spot, rates)

    raw_bis_path = output / "bis-ws-xru.csv-flat.zip"
    raw_oecd_path = output / "oecd-ir3tib-monthly.csv"
    spot_path = output / "bis-spot-usd-per-fx.csv"
    rates_path = output / "oecd-short-rates-annual-decimal.csv"
    approximate_path = output / "m027-approx-excess-log-returns.csv"
    report_path = output / "m027-stage1-ingestion.json"

    raw_bis_path.write_bytes(bis_raw)
    raw_oecd_path.write_bytes(oecd_raw)
    _write_frame(spot, spot_path, index_label="date")

    rates_for_csv = rates.copy()
    rates_for_csv.index = rates_for_csv.index.astype(str)
    _write_frame(rates_for_csv, rates_path, index_label="month")
    _write_frame(approximate, approximate_path, index_label="date")

    report = source_snapshot_report(
        bis_raw=bis_raw,
        oecd_raw=oecd_raw,
        spot_panel=spot,
        rate_panel=rates,
        approximate_returns=approximate,
    )
    report.update({
        "version": 1,
        "stage": "M027 Stage 1",
        "label": "CARRY-AWARE SPOT TSMOM — PUBLIC-DATA APPROXIMATION",
        "bis_url": BIS_XRU_URL,
        "oecd_url": OECD_STIR_URL,
        "output_files": {
            "bis_raw": raw_bis_path.name,
            "oecd_raw": raw_oecd_path.name,
            "spot_panel": spot_path.name,
            "rate_panel": rates_path.name,
            "approximate_returns": approximate_path.name,
        },
        "output_sha256": {
            "bis_raw": _sha256_file(raw_bis_path),
            "oecd_raw": _sha256_file(raw_oecd_path),
            "spot_panel": _sha256_file(spot_path),
            "rate_panel": _sha256_file(rates_path),
            "approximate_returns": _sha256_file(approximate_path),
        },
        "spot_rows": int(len(spot)),
        "rate_months": int(len(rates)),
        "approximate_rows": int(len(approximate)),
        "currency_count": len(M027_CURRENCIES),
        "safety": {
            "observation_values_reported": False,
            "strategy_signal_computed": False,
            "portfolio_economics_computed": False,
            "m021_post_cutoff_outcomes_used": False,
            "m024_holdout_reused": False,
            "real_order_api_called": False,
        },
    })

    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report_sha256"] = _sha256_file(report_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    report = run_stage1_ingestion(args.output_dir)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
