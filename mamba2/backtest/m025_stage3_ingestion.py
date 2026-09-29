"""M025 Stage-3 deterministic source ingestion.

This module is deliberately non-economic.  It downloads only prospectively
frozen public/reference sources, hashes raw bytes, validates H.10 spot-price
schema/continuity, normalizes quote direction, and inspects workbook schema.
It never computes returns, P/L, Sharpe, drawdown, correlations, or rankings.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping, Sequence
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile


H10_FROM = "1971-01-04"
H10_TO = "2026-08-31"
H10_PACKAGE_ID = "60f32914ab61dfab590e0e470153e3ae"
H10_URL = (
    "https://www.federalreserve.gov/datadownload/Output.aspx?"
    "filetype=csv&from=01%2F04%2F1971&label=include&lastObs=&"
    "layout=seriescolumn&rel=H10&series="
    + H10_PACKAGE_ID
    + "&to=08%2F31%2F2026"
)
AQR_URL = (
    "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/"
    "Time-Series-Momentum-Factors-Monthly.xlsx"
)
LRV_URL = (
    "https://finance.wharton.upenn.edu/~nroussan/"
    "CurrencyPortfolios.xls"
)

# (ISO currency, full H.10 unique identifier, source units, invert to USD/FX)
H10_SERIES = (
    ("AUD", "H10/H10/RXI$US_N.B.AL", "USD per AUD", False),
    ("EUR", "H10/H10/RXI$US_N.B.EU", "USD per EUR", False),
    ("NZD", "H10/H10/RXI$US_N.B.NZ", "USD per NZD", False),
    ("GBP", "H10/H10/RXI$US_N.B.UK", "USD per GBP", False),
    ("BRL", "H10/H10/RXI_N.B.BZ", "BRL per USD", True),
    ("CAD", "H10/H10/RXI_N.B.CA", "CAD per USD", True),
    ("CNY", "H10/H10/RXI_N.B.CH", "CNY per USD", True),
    ("DKK", "H10/H10/RXI_N.B.DN", "DKK per USD", True),
    ("HKD", "H10/H10/RXI_N.B.HK", "HKD per USD", True),
    ("INR", "H10/H10/RXI_N.B.IN", "INR per USD", True),
    ("JPY", "H10/H10/RXI_N.B.JA", "JPY per USD", True),
    ("MYR", "H10/H10/RXI_N.B.MA", "MYR per USD", True),
    ("MXN", "H10/H10/RXI_N.B.MX", "MXN per USD", True),
    ("NOK", "H10/H10/RXI_N.B.NO", "NOK per USD", True),
    ("ZAR", "H10/H10/RXI_N.B.SF", "ZAR per USD", True),
    ("SGD", "H10/H10/RXI_N.B.SI", "SGD per USD", True),
    ("KRW", "H10/H10/RXI_N.B.KO", "KRW per USD", True),
    ("LKR", "H10/H10/RXI_N.B.SL", "LKR per USD", True),
    ("SEK", "H10/H10/RXI_N.B.SD", "SEK per USD", True),
    ("CHF", "H10/H10/RXI_N.B.SZ", "CHF per USD", True),
    ("TWD", "H10/H10/RXI_N.B.TA", "TWD per USD", True),
    ("THB", "H10/H10/RXI_N.B.TH", "THB per USD", True),
    ("VES", "H10/H10/RXI_N.B.VES", "VES per USD", True),
)
H10_EXPECTED_IDS = tuple(row[1] for row in H10_SERIES)
H10_SYMBOLS = tuple(row[0] for row in H10_SERIES)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 Mamba2-Research-Ingestion/1.0"
            )
        },
    )
    with urlopen(request, timeout=120) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"empty download from {url}")
    output.write_bytes(data)
    return output


def _parse_date(value: str) -> str:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"invalid H.10 date: {value!r}")


def _month_ordinal(date_text: str) -> int:
    value = datetime.strptime(date_text, "%Y-%m-%d").date()
    return value.year * 12 + value.month


def _longest_consecutive_months(dates: Iterable[str]) -> int:
    months = sorted({_month_ordinal(value) for value in dates})
    if not months:
        return 0
    longest = 1
    current = 1
    for previous, value in zip(months, months[1:]):
        if value == previous + 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def inspect_h10_csv(
    raw_path: str | Path,
    normalized_path: str | Path,
) -> dict[str, Any]:
    """Validate the frozen H.10 package and write normalized USD/FX prices."""

    with Path(raw_path).open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        rows = list(csv.reader(handle))

    unique_row = next(
        (
            row for row in rows
            if row
            and row[0].strip().lower().startswith("unique identifier")
        ),
        None,
    )
    header_index = next(
        (
            index for index, row in enumerate(rows)
            if row and row[0].strip().lower() == "time period"
        ),
        None,
    )
    if unique_row is None or header_index is None:
        raise ValueError("H.10 CSV metadata/header rows are missing")

    observed_ids = tuple(cell.strip() for cell in unique_row[1:])
    if observed_ids != H10_EXPECTED_IDS:
        raise ValueError(
            "H.10 frozen 23-series identifier contract changed"
        )

    header = rows[header_index]
    if len(header) != 24:
        raise ValueError("H.10 data header must contain 23 series")
    if len(set(header[1:])) != 23:
        raise ValueError("H.10 short series headers must be unique")

    by_date: dict[str, list[float | None]] = {}
    for row in rows[header_index + 1 :]:
        if not row or not row[0].strip():
            continue
        date_text = _parse_date(row[0])
        if date_text in by_date:
            raise ValueError(f"duplicate H.10 date: {date_text}")
        if date_text < H10_FROM or date_text > H10_TO:
            raise ValueError(
                "H.10 download escaped frozen source snapshot range"
            )
        cells = list(row[1:])
        if len(cells) < 23:
            cells.extend([""] * (23 - len(cells)))
        if len(cells) > 23:
            raise ValueError("H.10 row has unexpected extra columns")

        parsed: list[float | None] = []
        for cell in cells:
            text = cell.strip()
            if not text or text.upper() == "ND":
                parsed.append(None)
                continue
            value = float(text)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    "H.10 source rates must be positive finite values"
                )
            parsed.append(value)
        by_date[date_text] = parsed

    if not by_date:
        raise ValueError("H.10 download contains no data rows")

    dates = sorted(by_date)
    normalized_path = Path(normalized_path)
    normalized_path.parent.mkdir(parents=True, exist_ok=True)

    nonmissing_dates: dict[str, list[str]] = {
        symbol: [] for symbol in H10_SYMBOLS
    }
    missing_counts = {symbol: 0 for symbol in H10_SYMBOLS}

    with normalized_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(
            handle,
            lineterminator="\n",
        )
        writer.writerow(["date", *H10_SYMBOLS])
        for date_text in dates:
            source_values = by_date[date_text]
            output_row: list[str] = [date_text]
            for index, (symbol, _, _, invert) in enumerate(H10_SERIES):
                source_value = source_values[index]
                if source_value is None:
                    missing_counts[symbol] += 1
                    output_row.append("")
                    continue
                normalized = (
                    1.0 / source_value
                    if invert
                    else source_value
                )
                if not math.isfinite(normalized) or normalized <= 0:
                    raise ValueError(
                        "normalized H.10 prices must be positive and finite"
                    )
                nonmissing_dates[symbol].append(date_text)
                output_row.append(format(normalized, ".15g"))
            writer.writerow(output_row)

    per_series: dict[str, Any] = {}
    gate_passed = True
    for symbol, full_id, source_quote, invert in H10_SERIES:
        present = nonmissing_dates[symbol]
        longest = _longest_consecutive_months(present)
        passed = longest >= 72
        gate_passed = gate_passed and passed
        per_series[symbol] = {
            "unique_identifier": full_id,
            "source_quote": source_quote,
            "normalized_quote": f"USD per {symbol}",
            "inverted": invert,
            "first_nonmissing_date": present[0] if present else None,
            "last_nonmissing_date": present[-1] if present else None,
            "missing_observations": missing_counts[symbol],
            "longest_consecutive_months_with_observation": longest,
            "gate_72_consecutive_months": passed,
        }

    return {
        "source_rows": len(dates),
        "first_source_date": dates[0],
        "last_source_date": dates[-1],
        "source_ids": list(H10_EXPECTED_IDS),
        "normalized_symbols": list(H10_SYMBOLS),
        "normalized_panel_sha256": _sha256(normalized_path),
        "per_series": per_series,
        "gate_72_consecutive_months_all_series": gate_passed,
    }


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOC_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_PKG_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)


def _xml_text(node: ET.Element) -> str:
    return "".join(
        value.text or ""
        for value in node.iter()
        if value.tag.endswith("}t")
    )


def inspect_xlsx_schema(
    path: str | Path,
    *,
    max_rows: int = 40,
) -> dict[str, Any]:
    """Inspect workbook/sheet names and string cells only; ignore numeric cells."""

    workbook_path = Path(path)
    with zipfile.ZipFile(workbook_path, "r") as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{{{_MAIN_NS}}}si"):
                shared.append(_xml_text(item))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        rel_map = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in rels.findall(f"{{{_PKG_REL_NS}}}Relationship")
        }

        sheets: dict[str, list[dict[str, str]]] = {}
        for sheet in workbook.findall(
            f".//{{{_MAIN_NS}}}sheet"
        ):
            name = sheet.attrib["name"]
            rel_id = sheet.attrib[
                f"{{{_DOC_REL_NS}}}id"
            ]
            target = rel_map[rel_id].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(archive.read(target))

            string_cells: list[dict[str, str]] = []
            for cell in root.findall(
                f".//{{{_MAIN_NS}}}c"
            ):
                ref = cell.attrib.get("r", "")
                match = re.search(r"(\d+)$", ref)
                if not match or int(match.group(1)) > max_rows:
                    continue
                cell_type = cell.attrib.get("t")
                text_value: str | None = None
                if cell_type == "s":
                    value_node = cell.find(f"{{{_MAIN_NS}}}v")
                    if (
                        value_node is not None
                        and value_node.text is not None
                    ):
                        index = int(value_node.text)
                        if 0 <= index < len(shared):
                            text_value = shared[index]
                elif cell_type == "inlineStr":
                    inline = cell.find(f"{{{_MAIN_NS}}}is")
                    if inline is not None:
                        text_value = _xml_text(inline)
                elif cell_type == "str":
                    value_node = cell.find(f"{{{_MAIN_NS}}}v")
                    if value_node is not None:
                        text_value = value_node.text or ""

                if text_value is not None:
                    clean = " ".join(text_value.split())
                    if clean:
                        string_cells.append(
                            {"cell": ref, "text": clean}
                        )
            sheets[name] = string_cells

    all_strings = [
        row["text"]
        for rows in sheets.values()
        for row in rows
    ]
    lower = [value.lower() for value in all_strings]
    currency_tokens = [
        value
        for value in all_strings
        if re.search(
            r"\b(currency|currencies|fx|foreign exchange)\b",
            value,
            re.IGNORECASE,
        )
    ]
    portfolio_tokens: dict[str, list[str]] = {}
    for number in range(1, 7):
        pattern = re.compile(
            rf"(^|\b)(p\s*{number}|portfolio\s*{number})(\b|$)",
            re.IGNORECASE,
        )
        portfolio_tokens[f"P{number}"] = [
            value for value in all_strings if pattern.search(value)
        ]
    hml_tokens = [
        value for value in all_strings
        if "hml" in value.lower()
    ]

    return {
        "sheet_names": list(sheets),
        "string_schema_cells": sheets,
        "currency_or_fx_schema_tokens": currency_tokens,
        "currency_specific_schema_present": bool(currency_tokens),
        "portfolio_schema_tokens": portfolio_tokens,
        "p1_through_p6_schema_present": all(
            portfolio_tokens[f"P{number}"]
            for number in range(1, 7)
        ),
        "hml_schema_tokens": hml_tokens,
        "hml_schema_present": bool(hml_tokens),
        "numeric_cells_inspected": False,
    }


def _convert_xls_to_xlsx(
    source: str | Path,
    output_dir: str | Path,
    *,
    libreoffice: str,
) -> Path:
    source_path = Path(source)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    expected = target_dir / f"{source_path.stem}.xlsx"
    result = subprocess.run(
        [
            libreoffice,
            "--headless",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(target_dir),
            str(source_path),
        ],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0 or not expected.is_file():
        raise RuntimeError(
            "LibreOffice LRV schema conversion failed: "
            + result.stderr[-1000:]
        )
    return expected


def run_ingestion(
    output_dir: str | Path,
    *,
    libreoffice: str,
) -> dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    h10_raw = _download(H10_URL, root / "h10-daily-rates.csv")
    aqr_raw = _download(
        AQR_URL,
        root / "Time-Series-Momentum-Factors-Monthly.xlsx",
    )
    lrv_raw = _download(
        LRV_URL,
        root / "CurrencyPortfolios.xls",
    )

    normalized = root / "h10-normalized-usd-per-foreign.csv"
    h10 = inspect_h10_csv(h10_raw, normalized)

    aqr_schema = inspect_xlsx_schema(aqr_raw)
    lrv_xlsx = _convert_xls_to_xlsx(
        lrv_raw,
        root,
        libreoffice=libreoffice,
    )
    lrv_schema = inspect_xlsx_schema(lrv_xlsx)

    report = {
        "schema_version": 1,
        "milestone": "M025",
        "stage": "stage3-ingestion",
        "economic_computation_performed": False,
        "sources": {
            "h10": {
                "url": H10_URL,
                "raw_artifact": h10_raw.name,
                "raw_sha256": _sha256(h10_raw),
                "snapshot_from": H10_FROM,
                "snapshot_through": H10_TO,
                **h10,
            },
            "aqr_tsmom": {
                "url": AQR_URL,
                "raw_artifact": aqr_raw.name,
                "raw_sha256": _sha256(aqr_raw),
                "schema": aqr_schema,
            },
            "lrv_currency_portfolios": {
                "url": LRV_URL,
                "raw_artifact": lrv_raw.name,
                "raw_sha256": _sha256(lrv_raw),
                "converted_schema_artifact": lrv_xlsx.name,
                "schema": lrv_schema,
            },
        },
        "safety": {
            "returns_computed": False,
            "pl_computed": False,
            "sharpe_computed": False,
            "drawdown_computed": False,
            "correlation_computed": False,
            "tracking_error_computed": False,
            "economic_ranking_computed": False,
            "m021_post_cutoff_outcomes_used": False,
            "m023_outcomes_used": False,
            "m024_outcomes_used_to_tune_definitions": False,
            "real_order_api_called": False,
        },
    }
    output = root / "m025-stage3-ingestion.json"
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report_path"] = str(output)
    report["report_sha256"] = _sha256(output)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run non-economic M025 Stage-3 source ingestion."
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--libreoffice", required=True)
    args = parser.parse_args(argv)
    report = run_ingestion(
        args.output_dir,
        libreoffice=args.libreoffice,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "report_path": report["report_path"],
                "report_sha256": report["report_sha256"],
                "economic_computation_performed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
