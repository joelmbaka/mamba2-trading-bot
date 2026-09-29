"""M025 Stage-3 non-economic ingestion tests."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import zipfile

import pytest

from mamba2.backtest.m025_stage3_ingestion import (
    AQR_URL,
    H10_EXPECTED_IDS,
    H10_FROM,
    H10_SERIES,
    H10_SDMX_CURRENCY_ALIASES,
    H10_TO,
    H10_URL,
    LRV_URL,
    inspect_h10_sdmx_zip,
    inspect_xlsx_schema,
)


def _month_rows(count: int = 73):
    year = 2010
    month = 1
    rows = []
    for _ in range(count):
        rows.append(date(year, month, 15).isoformat())
        month += 1
        if month == 13:
            month = 1
            year += 1
    return rows


def _write_h10_zip(
    path: Path,
    *,
    omit_last_id: bool = False,
    currency_overrides: dict[str, str] | None = None,
):
    rows = list(H10_SERIES)
    if omit_last_id:
        rows = rows[:-1]

    series_xml = []
    overrides = currency_overrides or {}
    for symbol, full_id, _, _ in rows:
        short_name = full_id.rsplit("/", 1)[-1]
        source_currency = overrides.get(short_name, symbol)
        observations = "".join(
            (
                f'<Obs TIME_PERIOD="{date_text}" '
                'OBS_VALUE="2.0" OBS_STATUS="A"/>'
            )
            for date_text in _month_rows()
        )
        series_xml.append(
            (
                f'<Series SERIES_NAME="{short_name}" '
                f'CURRENCY="{source_currency}" FREQ="B" FX="{symbol}" '
                'UNIT="Currency" UNIT_MULT="1">'
                f"{observations}</Series>"
            )
        )

    data_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<CompactData><DataSet>'
        + "".join(series_xml)
        + '</DataSet></CompactData>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("H10_data.xml", data_xml)
        archive.writestr("H10_struct.xml", "<Structure/>")
        archive.writestr("H10_H10.xsd", "<schema/>")
        archive.writestr("frb_common.xsd", "<schema/>")


def _write_minimal_xlsx(path: Path):
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Returns" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    cells = [
        "Currencies",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "HML-FX",
    ]
    sheet_cells = "".join(
        f'<c r="{chr(65+i)}1" t="inlineStr"><is><t>{value}</t></is></c>'
        for i, value in enumerate(cells)
    )
    sheet = f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData><row r="1">{sheet_cells}</row>
<row r="2"><c r="A2"><v>999.0</v></c></row></sheetData>
</worksheet>"""

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_stage3_sources_and_snapshot_are_frozen():
    assert H10_FROM == "1971-01-04"
    assert H10_TO == "2026-08-31"
    assert H10_URL.endswith("Output.aspx?filetype=zip&rel=h10")
    assert "series=" not in H10_URL
    assert AQR_URL.endswith("Time-Series-Momentum-Factors-Monthly.xlsx")
    assert LRV_URL.endswith("CurrencyPortfolios.xls")
    assert len(H10_SERIES) == 23


def test_h10_parser_normalizes_quote_direction_without_returns(tmp_path):
    raw = tmp_path / "h10.zip"
    normalized = tmp_path / "normalized.csv"
    _write_h10_zip(raw)

    result = inspect_h10_sdmx_zip(raw, normalized)

    assert result["gate_72_consecutive_months_all_series"] is True
    assert result["source_ids"] == list(H10_EXPECTED_IDS)

    with normalized.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    header = rows[0]
    first = rows[1]
    aud = header.index("AUD")
    cad = header.index("CAD")
    assert float(first[aud]) == pytest.approx(2.0)
    assert float(first[cad]) == pytest.approx(0.5)


def test_h10_parser_refuses_series_contract_drift(tmp_path):
    raw = tmp_path / "h10.zip"
    normalized = tmp_path / "normalized.csv"
    _write_h10_zip(raw, omit_last_id=True)

    with pytest.raises(ValueError, match="23-series identifier"):
        inspect_h10_sdmx_zip(raw, normalized)


def test_xlsx_schema_scanner_reads_strings_but_not_numeric_cells(tmp_path):
    workbook = tmp_path / "schema.xlsx"
    _write_minimal_xlsx(workbook)

    result = inspect_xlsx_schema(workbook)

    assert result["sheet_names"] == ["Returns"]
    assert result["currency_specific_schema_present"] is True
    assert result["p1_through_p6_schema_present"] is True
    assert result["hml_schema_present"] is True
    assert result["numeric_cells_inspected"] is False
    strings = [
        row["text"]
        for row in result["string_schema_cells"]["Returns"]
    ]
    assert "999.0" not in strings


def test_ingestion_module_has_no_economic_benchmark_imports():
    import mamba2.backtest.m025_stage3_ingestion as ingestion

    forbidden = {
        "tsmom_weights_from_excess_returns",
        "tsmom_spot_proxy_weights",
        "currency_momentum_weights",
        "carry_weights",
    }
    assert forbidden.isdisjoint(ingestion.__dict__)



def test_h10_parser_accepts_only_documented_ves_vEB_alias(tmp_path):
    raw = tmp_path / "h10-ves-alias.zip"
    normalized = tmp_path / "normalized.csv"
    _write_h10_zip(
        raw,
        currency_overrides={"RXI_N.B.VES": "VEB"},
    )

    result = inspect_h10_sdmx_zip(raw, normalized)

    assert result["gate_72_consecutive_months_all_series"] is True
    assert H10_SDMX_CURRENCY_ALIASES["RXI_N.B.VES"] == frozenset(
        {"VES", "VEB"}
    )


def test_h10_parser_rejects_unapproved_currency_metadata_drift(tmp_path):
    raw = tmp_path / "h10-bad-currency.zip"
    normalized = tmp_path / "normalized.csv"
    _write_h10_zip(
        raw,
        currency_overrides={"RXI_N.B.CA": "USD"},
    )

    with pytest.raises(ValueError, match="currency metadata changed"):
        inspect_h10_sdmx_zip(raw, normalized)
