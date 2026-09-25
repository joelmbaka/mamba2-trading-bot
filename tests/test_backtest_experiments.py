"""Control-gate tests for the M020 experiment harness."""

from pathlib import Path

from mamba2.backtest import experiments


def test_verify_control_hashes_requires_both_artifacts():
    result = {
        "baseline_sha256": "baseline",
        "diagnostic_sha256": "diagnostic",
    }

    accepted = experiments.verify_control_hashes(
        result,
        expected_baseline_sha256="baseline",
        expected_diagnostic_sha256="diagnostic",
    )
    assert accepted["ok"] is True
    assert accepted["baseline_preserved"] is True
    assert accepted["diagnostic_preserved"] is True

    rejected = experiments.verify_control_hashes(
        result,
        expected_baseline_sha256="different",
        expected_diagnostic_sha256="diagnostic",
    )
    assert rejected["ok"] is False
    assert rejected["baseline_preserved"] is False
    assert rejected["diagnostic_preserved"] is True


def test_control_arm_uses_unmodified_diagnostic_baseline(monkeypatch, tmp_path):
    baseline = {
        "aggregate": {
            "accepted_orders": 1,
            "closed_trades": 1,
        }
    }
    diagnostic = {
        "diagnostic_schema_version": 1,
        "source_baseline_sha256": None,
    }

    calls = []

    def fake_run(manifest_path, *, starting_balance):
        calls.append((Path(manifest_path), starting_balance))
        return baseline, diagnostic

    monkeypatch.setattr(experiments, "run_diagnostic_baseline", fake_run)

    result = experiments.run_control_arm(
        tmp_path / "manifest.json",
        baseline_output=tmp_path / "baseline.json",
        diagnostic_output=tmp_path / "diagnostic.json",
        starting_balance=12_345.0,
    )

    assert calls == [(tmp_path / "manifest.json", 12_345.0)]
    assert result["arm"] == "control"
    assert result["experiment_id"] == "M020-A"
    assert diagnostic["source_baseline_sha256"] == result["baseline_sha256"]
    assert Path(result["baseline_path"]).is_file()
    assert Path(result["diagnostic_path"]).is_file()
