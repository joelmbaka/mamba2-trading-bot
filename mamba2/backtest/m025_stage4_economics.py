"""M025 Stage-4 frozen economic execution machinery.

Definitions, source hashes, units, timing, metrics and comparisons are frozen
in docs/milestones/025-public-fx-strategy-benchmarks.md before this module may
be executed on the accepted Stage-3 artifacts.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd
import xlrd

from .public_benchmarks import tsmom_spot_proxy_weights


STAGE3_REPORT_SHA256 = (
    "d5f05a7aed82d1cac275bcb222913ec61a38f00b2df74b3727e479d7a4324505"
)
H10_RAW_SHA256 = (
    "38b941973dd7e6570e590291a34ebd27873ef98c7d09fcb0e3097ee76e793046"
)
H10_NORMALIZED_SHA256 = (
    "015e61cffd504f61853167bfab1511ecd92c51e87abd21c935ee70b064f43419"
)
AQR_RAW_SHA256 = (
    "33470930e2269c0d97be4732ec2d9c27ddbc69ac8133b059a263e27400263eeb"
)
LRV_RAW_SHA256 = (
    "e08676e399a3c80714e55bd980350892785e8091f483af0784197fd815612d74"
)
LRV_FROZEN_UNIT_SCALE_TO_DECIMAL = 0.01
LRV_FROZEN_UNIT_EVIDENCE = (
    "author data page identifies CurrencyPortfolios.xls as monthly currency "
    "excess returns; workbook Notes identifies the series as returns in levels; "
    "the author paper states those level returns are reported in percentage "
    "points and annualized by multiplying excess returns by 12"
)

H10_LABEL = "TSMOM SPOT PROXY — FED H.10"
H10_COST_LABEL = (
    "GROSS SPOT-PRICE PROXY / TRANSACTION COSTS UNMODELED / "
    "CARRY AND FINANCING UNMODELED"
)
AQR_LABEL = "AQR TSMOM^FX — DERIVED REFERENCE"
LRV_LABEL = "LRV HML-FX — DERIVED REFERENCE — ALL CURRENCIES NET"

H10_SYMBOLS = (
    "AUD", "EUR", "NZD", "GBP", "BRL", "CAD", "CNY", "DKK", "HKD",
    "INR", "JPY", "MYR", "MXN", "NOK", "ZAR", "SGD", "KRW", "LKR",
    "SEK", "CHF", "TWD", "THB", "VES",
)

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOC_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
_PKG_REL_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha(path: str | Path, expected: str, *, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_file():
        raise FileNotFoundError(f"{label} artifact missing: {candidate}")
    observed = _sha256(candidate)
    if observed != expected:
        raise ValueError(f"{label} SHA changed: {observed}")
    return candidate


def _month_end_index(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return index.to_period("M").to_timestamp("M").tz_localize("UTC")


def _canonical_monthly_series(series: pd.Series, *, name: str) -> pd.Series:
    clean = pd.Series(series, copy=True).astype(float)
    if not isinstance(clean.index, pd.DatetimeIndex):
        raise TypeError(f"{name} index must be DatetimeIndex")
    if clean.index.tz is None:
        clean.index = clean.index.tz_localize("UTC")
    else:
        clean.index = clean.index.tz_convert("UTC")
    clean.index = _month_end_index(clean.index)
    if clean.index.has_duplicates:
        raise ValueError(f"{name} contains duplicate calendar months")
    clean = clean.sort_index()
    finite = np.isfinite(clean.to_numpy(dtype=float))
    clean = clean[finite]
    clean.name = name
    return clean


def load_h10_normalized_panel(path: str | Path) -> pd.DataFrame:
    panel_path = _require_sha(
        path,
        H10_NORMALIZED_SHA256,
        label="H.10 normalized panel",
    )
    frame = pd.read_csv(
        panel_path,
        parse_dates=["date"],
        na_values=[""],
        keep_default_na=True,
    )
    if list(frame.columns) != ["date", *H10_SYMBOLS]:
        raise ValueError("H.10 normalized panel column contract changed")
    if frame["date"].duplicated().any():
        raise ValueError("H.10 normalized panel has duplicate dates")
    frame = frame.set_index("date").sort_index()
    frame.index = pd.DatetimeIndex(frame.index).tz_localize("UTC")
    values = frame.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size and np.any(finite <= 0):
        raise ValueError("H.10 normalized prices must remain positive")
    return frame.astype(float)


def h10_tsmom_spot_proxy(
    daily_prices: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    if tuple(daily_prices.columns) != H10_SYMBOLS:
        raise ValueError("H.10 proxy requires the exact frozen 23-series universe")
    prices = daily_prices.astype(float)
    daily_returns = prices.pct_change(fill_method=None)
    monthly_returns = (
        (1.0 + daily_returns)
        .resample("ME")
        .prod(min_count=1)
        - 1.0
    )
    weights = tsmom_spot_proxy_weights(prices).weights
    weights = weights.reindex(
        index=monthly_returns.index,
        columns=monthly_returns.columns,
    )
    valid = (
        np.isfinite(weights.to_numpy(dtype=float))
        & np.isfinite(monthly_returns.to_numpy(dtype=float))
    )
    contributions = weights * monthly_returns
    contributions = contributions.where(pd.DataFrame(
        valid, index=contributions.index, columns=contributions.columns
    ))
    valid_counts = contributions.notna().sum(axis=1).astype(int)
    portfolio = contributions.mean(axis=1, skipna=True)
    portfolio = portfolio.where(valid_counts > 0)
    portfolio = _canonical_monthly_series(portfolio, name=H10_LABEL)
    valid_counts = valid_counts.reindex(portfolio.index).astype(int)
    valid_counts.name = "valid_instrument_count"
    return portfolio, valid_counts


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    values: list[str] = []
    if "xl/sharedStrings.xml" not in archive.namelist():
        return values
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    for item in root.findall(f"{{{_MAIN_NS}}}si"):
        text = "".join(
            node.text or ""
            for node in item.iter()
            if node.tag.endswith("}t")
        )
        values.append(text)
    return values


def _xlsx_sheet_target(
    archive: zipfile.ZipFile,
    *,
    sheet_name: str,
) -> tuple[str, ET.Element]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in rels.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }
    target: str | None = None
    for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib[f"{{{_DOC_REL_NS}}}id"]
            target = rel_map[rel_id].lstrip("/")
            break
    if target is None:
        raise ValueError(f"AQR sheet missing: {sheet_name}")
    if not target.startswith("xl/"):
        target = "xl/" + target
    return target, workbook


def _xlsx_number_formats(archive: zipfile.ZipFile) -> list[str | None]:
    root = ET.fromstring(archive.read("xl/styles.xml"))
    custom: dict[int, str] = {}
    numfmts = root.find(f"{{{_MAIN_NS}}}numFmts")
    if numfmts is not None:
        for node in numfmts.findall(f"{{{_MAIN_NS}}}numFmt"):
            custom[int(node.attrib["numFmtId"])] = node.attrib["formatCode"]
    builtins = {
        0: "General",
        1: "0",
        2: "0.00",
        9: "0%",
        10: "0.00%",
        14: "m/d/yy",
        15: "d-mmm-yy",
        16: "d-mmm",
        17: "mmm-yy",
        22: "m/d/yy h:mm",
    }
    cell_xfs = root.find(f"{{{_MAIN_NS}}}cellXfs")
    if cell_xfs is None:
        raise ValueError("AQR workbook has no cellXfs")
    out: list[str | None] = []
    for xf in cell_xfs.findall(f"{{{_MAIN_NS}}}xf"):
        numfmt_id = int(xf.attrib.get("numFmtId", "0"))
        out.append(custom.get(numfmt_id, builtins.get(numfmt_id)))
    return out


def _xlsx_cell_text(
    cell: ET.Element,
    shared: Sequence[str],
) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        node = cell.find(f"{{{_MAIN_NS}}}v")
        if node is None or node.text is None:
            return None
        index = int(node.text)
        return shared[index]
    if cell_type == "inlineStr":
        node = cell.find(f"{{{_MAIN_NS}}}is")
        if node is None:
            return None
        return "".join(
            child.text or ""
            for child in node.iter()
            if child.tag.endswith("}t")
        )
    if cell_type == "str":
        node = cell.find(f"{{{_MAIN_NS}}}v")
        return None if node is None else node.text
    return None


def _xlsx_cell_number(cell: ET.Element) -> float | None:
    cell_type = cell.attrib.get("t")
    if cell_type not in (None, "n"):
        return None
    node = cell.find(f"{{{_MAIN_NS}}}v")
    if node is None or node.text is None or not node.text.strip():
        return None
    return float(node.text)


def _is_percent_format(format_code: str | None) -> bool:
    if not format_code:
        return False
    # Literal escaped percent symbols also denote percentage display.
    return "%" in format_code


def _excel_serial_to_timestamp(value: float, *, date1904: bool) -> pd.Timestamp:
    if not math.isfinite(value):
        raise ValueError("non-finite Excel date serial")
    base = datetime(1904, 1, 1) if date1904 else datetime(1899, 12, 30)
    return pd.Timestamp(base + timedelta(days=float(value)), tz="UTC")


def parse_aqr_tsmom_fx(path: str | Path) -> pd.Series:
    workbook_path = _require_sha(path, AQR_RAW_SHA256, label="AQR workbook")
    with zipfile.ZipFile(workbook_path, "r") as archive:
        shared = _xlsx_shared_strings(archive)
        target, workbook = _xlsx_sheet_target(
            archive,
            sheet_name="TSMOM Factors",
        )
        formats = _xlsx_number_formats(archive)
        workbook_pr = workbook.find(f"{{{_MAIN_NS}}}workbookPr")
        date1904 = (
            workbook_pr is not None
            and workbook_pr.attrib.get("date1904", "0") in {"1", "true", "True"}
        )
        sheet = ET.fromstring(archive.read(target))
        cells = {
            cell.attrib["r"]: cell
            for cell in sheet.findall(f".//{{{_MAIN_NS}}}c")
            if cell.attrib.get("r")
        }
        header = cells.get("F18")
        if header is None or _xlsx_cell_text(header, shared) != "TSMOM^FX":
            raise ValueError("AQR TSMOM^FX frozen header contract changed")

        rows: list[tuple[pd.Timestamp, float]] = []
        row_numbers = sorted({
            int(match.group(1))
            for ref in cells
            if (match := re.match(r"^[A-Z]+(\d+)$", ref))
            and int(match.group(1)) > 18
        })
        for row in row_numbers:
            date_cell = cells.get(f"A{row}")
            value_cell = cells.get(f"F{row}")
            if date_cell is None or value_cell is None:
                continue
            date_number = _xlsx_cell_number(date_cell)
            value = _xlsx_cell_number(value_cell)
            if date_number is None or value is None:
                continue
            style_index = int(value_cell.attrib.get("s", "0"))
            if style_index >= len(formats):
                raise ValueError("AQR TSMOM^FX cell style is out of range")
            format_code = formats[style_index]
            if not _is_percent_format(format_code):
                raise ValueError(
                    "UNIT SCHEMA INELIGIBLE: AQR TSMOM^FX is not "
                    f"percentage-formatted ({format_code!r})"
                )
            timestamp = _excel_serial_to_timestamp(
                date_number,
                date1904=date1904,
            )
            if not math.isfinite(value):
                raise ValueError("AQR TSMOM^FX contains non-finite value")
            rows.append((timestamp, float(value)))

    if not rows:
        raise ValueError("AQR TSMOM^FX has no admitted monthly observations")
    series = pd.Series(
        [value for _, value in rows],
        index=pd.DatetimeIndex([date for date, _ in rows]),
        name=AQR_LABEL,
        dtype=float,
    )
    return _canonical_monthly_series(series, name=AQR_LABEL)


def _normalized_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _is_percent_xlrd_format(format_code: str | None) -> bool:
    return bool(format_code and "%" in format_code)


def _xlrd_format_for_cell(
    book: xlrd.book.Book,
    cell: xlrd.sheet.Cell,
) -> str | None:
    xf_index = getattr(cell, "xf_index", None)
    if xf_index is None or xf_index >= len(book.xf_list):
        return None
    format_key = book.xf_list[xf_index].format_key
    fmt = book.format_map.get(format_key)
    return None if fmt is None else fmt.format_str


@dataclass(frozen=True)
class LRVLayout:
    sheet_name: str
    header_row: int
    date_col: int
    portfolio_cols: tuple[int, int, int, int, int, int]
    hml_col: int | None


def locate_lrv_layout(book: xlrd.book.Book) -> LRVLayout:
    if "All currencies (net)" not in book.sheet_names():
        raise ValueError("LRV exact sheet missing: All currencies (net)")
    sheet = book.sheet_by_name("All currencies (net)")

    header_row: int | None = None
    portfolio_cols: dict[int, int] = {}
    hml_col: int | None = None
    for row in range(min(sheet.nrows, 120)):
        found: dict[int, int] = {}
        row_hml: int | None = None
        for col in range(sheet.ncols):
            cell = sheet.cell(row, col)
            if cell.ctype != xlrd.XL_CELL_TEXT:
                continue
            text = _normalized_header(cell.value)
            match = re.fullmatch(r"portfolio([1-6])", text)
            if match:
                found[int(match.group(1))] = col
            if text in {"hml", "hmlfx"}:
                row_hml = col
        if set(found) == {1, 2, 3, 4, 5, 6}:
            header_row = row
            portfolio_cols = found
            hml_col = row_hml
            break
    if header_row is None:
        raise ValueError("LRV P1-P6 header row not found")

    sheet = book.sheet_by_name("All currencies (net)")
    date_col: int | None = None
    for col in range(min(portfolio_cols.values())):
        count = 0
        for row in range(header_row + 1, min(sheet.nrows, header_row + 60)):
            if sheet.cell(row, col).ctype == xlrd.XL_CELL_DATE:
                count += 1
        if count >= 3:
            date_col = col
            break
    if date_col is None:
        raise ValueError("LRV monthly date column not found")

    return LRVLayout(
        sheet_name="All currencies (net)",
        header_row=header_row,
        date_col=date_col,
        portfolio_cols=tuple(portfolio_cols[i] for i in range(1, 7)),
        hml_col=hml_col,
    )


def _lrv_unit_scale(
    book: xlrd.book.Book,
    sheet: xlrd.sheet.Sheet,
    layout: LRVLayout,
) -> float:
    formats: set[str] = set()
    for row in range(layout.header_row + 1, sheet.nrows):
        for col in layout.portfolio_cols:
            cell = sheet.cell(row, col)
            if cell.ctype in (xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_DATE):
                fmt = _xlrd_format_for_cell(book, cell)
                if fmt:
                    formats.add(fmt)
        if formats:
            break
    if formats and all(_is_percent_xlrd_format(fmt) for fmt in formats):
        return 1.0
    if any(_is_percent_xlrd_format(fmt) for fmt in formats):
        raise ValueError("UNIT SCHEMA INELIGIBLE: mixed LRV return formats")

    metadata_strings = []
    for row in range(min(sheet.nrows, 80)):
        for col in range(sheet.ncols):
            cell = sheet.cell(row, col)
            if cell.ctype == xlrd.XL_CELL_TEXT:
                metadata_strings.append(str(cell.value).lower())
    explicit_percent_points = any(
        "percent" in text or "percentage" in text
        for text in metadata_strings
    )
    if explicit_percent_points:
        return 0.01
    raise ValueError(
        "UNIT SCHEMA INELIGIBLE: LRV return unit is not explicit"
    )


def _lrv_scale_from_frozen_external_evidence(*, workbook_sha256: str) -> float:
    """Return the prospectively frozen unit scale for the exact LRV workbook."""

    if workbook_sha256 != LRV_RAW_SHA256:
        raise ValueError("LRV external unit evidence is authorized only for the frozen workbook")
    return LRV_FROZEN_UNIT_SCALE_TO_DECIMAL


def parse_lrv_hml_fx(path: str | Path) -> tuple[pd.Series, dict[str, Any]]:
    workbook_path = _require_sha(path, LRV_RAW_SHA256, label="LRV workbook")
    book = xlrd.open_workbook(
        str(workbook_path),
        formatting_info=True,
        on_demand=False,
    )
    layout = locate_lrv_layout(book)
    sheet = book.sheet_by_name(layout.sheet_name)
    try:
        scale = _lrv_unit_scale(book, sheet, layout)
        unit_evidence = "workbook metadata"
    except ValueError as exc:
        if str(exc) != "UNIT SCHEMA INELIGIBLE: LRV return unit is not explicit":
            raise
        scale = _lrv_scale_from_frozen_external_evidence(
            workbook_sha256=LRV_RAW_SHA256,
        )
        unit_evidence = LRV_FROZEN_UNIT_EVIDENCE

    dates: list[pd.Timestamp] = []
    p1_values: list[float] = []
    p6_values: list[float] = []
    published_hml: list[float | None] = []

    for row in range(layout.header_row + 1, sheet.nrows):
        date_cell = sheet.cell(row, layout.date_col)
        if date_cell.ctype != xlrd.XL_CELL_DATE:
            continue
        p1 = sheet.cell(row, layout.portfolio_cols[0])
        p6 = sheet.cell(row, layout.portfolio_cols[5])
        if p1.ctype != xlrd.XL_CELL_NUMBER or p6.ctype != xlrd.XL_CELL_NUMBER:
            continue
        timestamp = pd.Timestamp(
            xlrd.xldate.xldate_as_datetime(
                date_cell.value,
                book.datemode,
            ),
            tz="UTC",
        )
        p1_value = float(p1.value) * scale
        p6_value = float(p6.value) * scale
        if not math.isfinite(p1_value) or not math.isfinite(p6_value):
            raise ValueError("LRV P1/P6 contains non-finite value")
        dates.append(timestamp)
        p1_values.append(p1_value)
        p6_values.append(p6_value)
        if layout.hml_col is None:
            published_hml.append(None)
        else:
            hml_cell = sheet.cell(row, layout.hml_col)
            if hml_cell.ctype == xlrd.XL_CELL_NUMBER:
                published_hml.append(float(hml_cell.value) * scale)
            else:
                published_hml.append(None)

    if not dates:
        raise ValueError("LRV exact net sheet has no admitted monthly returns")
    hml = pd.Series(
        np.asarray(p6_values) - np.asarray(p1_values),
        index=pd.DatetimeIndex(dates),
        name=LRV_LABEL,
        dtype=float,
    )
    hml = _canonical_monthly_series(hml, name=LRV_LABEL)

    if layout.hml_col is not None:
        published = pd.Series(
            published_hml,
            index=pd.DatetimeIndex(dates),
            dtype=float,
        )
        published = published.reindex(hml.index)
        mask = published.notna()
        if mask.any():
            maximum_error = float(
                np.max(np.abs(published[mask].to_numpy() - hml[mask].to_numpy()))
            )
            if maximum_error > 1e-10:
                raise ValueError(
                    "LRV published HML does not equal P6-P1 "
                    f"(max error {maximum_error})"
                )

    metadata = {
        "sheet_name": layout.sheet_name,
        "header_row_zero_based": layout.header_row,
        "date_col_zero_based": layout.date_col,
        "portfolio_cols_zero_based": list(layout.portfolio_cols),
        "hml_col_zero_based": layout.hml_col,
        "unit_scale_to_decimal": scale,
        "unit_evidence": unit_evidence,
        "canonical_definition": "P6 - P1",
    }
    return hml, metadata


def summarize_monthly_returns(
    series: pd.Series,
    *,
    label: str,
) -> dict[str, Any]:
    clean = _canonical_monthly_series(series, name=label).dropna()
    if len(clean) < 2:
        raise ValueError(f"{label} requires at least two monthly observations")
    values = clean.to_numpy(dtype=float)
    mean_monthly = float(np.mean(values))
    annualized_mean = 12.0 * mean_monthly
    annualized_vol = math.sqrt(12.0) * float(np.std(values, ddof=1))
    annualized_sharpe = (
        annualized_mean / annualized_vol
        if annualized_vol > 0
        else None
    )
    wealth = (1.0 + clean).cumprod()
    running_max = wealth.cummax()
    drawdowns = wealth / running_max - 1.0
    return {
        "label": label,
        "first_month": clean.index[0].date().isoformat(),
        "last_month": clean.index[-1].date().isoformat(),
        "observations": int(len(clean)),
        "mean_monthly_return": mean_monthly,
        "annualized_arithmetic_mean": annualized_mean,
        "annualized_volatility": annualized_vol,
        "annualized_sharpe": annualized_sharpe,
        "terminal_cumulative_wealth": float(wealth.iloc[-1]),
        "maximum_drawdown": float(drawdowns.min()),
        "positive_month_fraction": float(np.mean(values > 0)),
    }


def compare_monthly_returns(
    proxy: pd.Series,
    reference: pd.Series,
) -> dict[str, Any]:
    joined = pd.concat(
        [
            _canonical_monthly_series(proxy, name="proxy"),
            _canonical_monthly_series(reference, name="reference"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    if len(joined) < 2:
        raise ValueError("proxy/reference comparison requires two common months")
    diff = joined["proxy"] - joined["reference"]
    return {
        "common_start_month": joined.index[0].date().isoformat(),
        "common_end_month": joined.index[-1].date().isoformat(),
        "common_observations": int(len(joined)),
        "pearson_correlation": float(
            joined["proxy"].corr(joined["reference"])
        ),
        "annualized_mean_return_difference": 12.0 * float(diff.mean()),
        "annualized_tracking_error": (
            math.sqrt(12.0) * float(diff.std(ddof=1))
        ),
    }


def _series_rows(series: pd.Series) -> list[dict[str, Any]]:
    clean = _canonical_monthly_series(series, name=series.name or "series")
    return [
        {
            "month": timestamp.date().isoformat(),
            "return": float(value),
        }
        for timestamp, value in clean.items()
    ]


def build_stage4_report(
    *,
    ingestion_dir: str | Path,
) -> dict[str, Any]:
    root = Path(ingestion_dir)
    report_path = _require_sha(
        root / "m025-stage3-ingestion.json",
        STAGE3_REPORT_SHA256,
        label="Stage-3 ingestion report",
    )
    _require_sha(root / "h10-all-data.zip", H10_RAW_SHA256, label="H.10 raw")
    _require_sha(
        root / "Time-Series-Momentum-Factors-Monthly.xlsx",
        AQR_RAW_SHA256,
        label="AQR workbook",
    )
    _require_sha(
        root / "CurrencyPortfolios.xls",
        LRV_RAW_SHA256,
        label="LRV workbook",
    )
    # Ensure the accepted report remains valid JSON and points to Stage 3.
    stage3 = json.loads(report_path.read_text(encoding="utf-8"))
    if stage3.get("stage") != "stage3-ingestion":
        raise ValueError("Stage-3 ingestion report contract changed")

    h10_prices = load_h10_normalized_panel(
        root / "h10-normalized-usd-per-foreign.csv"
    )
    h10_returns, valid_counts = h10_tsmom_spot_proxy(h10_prices)
    aqr_returns = parse_aqr_tsmom_fx(
        root / "Time-Series-Momentum-Factors-Monthly.xlsx"
    )
    lrv_returns, lrv_metadata = parse_lrv_hml_fx(
        root / "CurrencyPortfolios.xls"
    )

    return {
        "schema_version": 1,
        "milestone": "M025",
        "stage": "stage4-economics",
        "inputs": {
            "stage3_report_sha256": STAGE3_REPORT_SHA256,
            "h10_raw_sha256": H10_RAW_SHA256,
            "h10_normalized_sha256": H10_NORMALIZED_SHA256,
            "aqr_raw_sha256": AQR_RAW_SHA256,
            "lrv_raw_sha256": LRV_RAW_SHA256,
        },
        "series": {
            "h10_spot_proxy": {
                "label": H10_LABEL,
                "cost_label": H10_COST_LABEL,
                "summary": summarize_monthly_returns(
                    h10_returns,
                    label=H10_LABEL,
                ),
                "monthly_returns": _series_rows(h10_returns),
                "valid_instrument_count": [
                    {
                        "month": timestamp.date().isoformat(),
                        "count": int(value),
                    }
                    for timestamp, value in valid_counts.items()
                ],
            },
            "aqr_tsmom_fx": {
                "label": AQR_LABEL,
                "summary": summarize_monthly_returns(
                    aqr_returns,
                    label=AQR_LABEL,
                ),
                "monthly_returns": _series_rows(aqr_returns),
            },
            "lrv_hml_fx": {
                "label": LRV_LABEL,
                "summary": summarize_monthly_returns(
                    lrv_returns,
                    label=LRV_LABEL,
                ),
                "parser_metadata": lrv_metadata,
                "monthly_returns": _series_rows(lrv_returns),
            },
        },
        "comparisons": {
            "h10_vs_aqr_tsmom_fx": compare_monthly_returns(
                h10_returns,
                aqr_returns,
            )
        },
        "safety": {
            "definitions_tuned_after_economics": False,
            "source_replaced_after_economics": False,
            "lag_search_run": False,
            "sign_search_run": False,
            "subperiod_search_run": False,
            "currency_subset_search_run": False,
            "m021_post_cutoff_outcomes_used": False,
            "m023_outcomes_used": False,
            "m024_outcomes_used_to_tune_m025": False,
            "real_order_api_called": False,
        },
    }


def _write_json(report: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def run_stage4_pair(
    *,
    ingestion_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for label in ("a", "b"):
        report = build_stage4_report(ingestion_dir=ingestion_dir)
        path = _write_json(
            report,
            root / f"m025-stage4-{label}.json",
        )
        artifacts.append({
            "label": label,
            "path": str(path),
            "sha256": _sha256(path),
        })
    deterministic = artifacts[0]["sha256"] == artifacts[1]["sha256"]
    return {
        "ok": deterministic,
        "deterministic": deterministic,
        "a": artifacts[0],
        "b": artifacts[1],
    }
