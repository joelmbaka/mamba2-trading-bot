"""M027 Stage-1 ingestion plumbing tests."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from mamba2.backtest import m027_stage1_ingestion as ingestion


def _bis_bytes() -> bytes:
    fields = [
        "FREQ:Frequency",
        "REF_AREA:Reference area",
        "CURRENCY:Currency",
        "COLLECTION:Collection",
        "TIME_PERIOD:Time period or range",
        "OBS_VALUE:Observation value",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows([
        {
            "FREQ:Frequency": "D:Daily",
            "REF_AREA:Reference area": "AU:Australia",
            "CURRENCY:Currency": "AUD:Australian dollar",
            "COLLECTION:Collection": "A:Average",
            "TIME_PERIOD:Time period or range": "2020-01-31",
            "OBS_VALUE:Observation value": "2.0",
        },
        {
            "FREQ:Frequency": "D:Daily",
            "REF_AREA:Reference area": "AU:Australia",
            "CURRENCY:Currency": "AUD:Australian dollar",
            "COLLECTION:Collection": "A:Average",
            "TIME_PERIOD:Time period or range": "2020-02-03",
            "OBS_VALUE:Observation value": "1.98",
        },
    ])
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("WS_XRU.csv", buf.getvalue())
    return out.getvalue()


def _oecd_bytes() -> bytes:
    fields = [
        "REF_AREA",
        "FREQ",
        "MEASURE",
        "UNIT_MEASURE",
        "TIME_PERIOD",
        "OBS_VALUE",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for ref, value in (("USA", "2.0"), ("AUS", "6.0")):
        writer.writerow({
            "REF_AREA": ref,
            "FREQ": "M",
            "MEASURE": "IR3TIB",
            "UNIT_MEASURE": "PA",
            "TIME_PERIOD": "2020-01",
            "OBS_VALUE": value,
        })
    return buf.getvalue().encode()


def test_ingestion_writes_immutable_non_economic_artifacts(tmp_path, monkeypatch):
    bis = _bis_bytes()
    oecd = _oecd_bytes()

    def fake_download(url, *, accept=None):
        del accept
        if url == ingestion.BIS_XRU_URL:
            return bis
        if url == ingestion.OECD_STIR_URL:
            return oecd
        raise AssertionError(url)

    monkeypatch.setattr(ingestion, "_download", fake_download)
    output = tmp_path / "m027"

    report = ingestion.run_stage1_ingestion(output)

    expected = {
        "bis-ws-xru.csv-flat.zip",
        "oecd-ir3tib-monthly.csv",
        "bis-spot-usd-per-fx.csv",
        "oecd-short-rates-annual-decimal.csv",
        "m027-approx-excess-log-returns.csv",
        "m027-stage1-ingestion.json",
    }
    assert {path.name for path in output.iterdir()} == expected
    assert report["strategy_signal_computed"] is False
    assert report["portfolio_economics_computed"] is False
    assert report["safety"]["observation_values_reported"] is False
    assert report["output_sha256"]["bis_raw"]
    assert report["output_sha256"]["approximate_returns"]

    persisted = json.loads(
        (output / "m027-stage1-ingestion.json").read_text(encoding="utf-8")
    )
    assert persisted["currency_count"] == 25
    assert persisted["strategy_signal_computed"] is False


def test_ingestion_refuses_existing_output_directory(tmp_path):
    output = tmp_path / "m027"
    output.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        ingestion.run_stage1_ingestion(output)
