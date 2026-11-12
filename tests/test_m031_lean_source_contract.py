"""Read-only source contract checks for the unexecuted independent LEAN path."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
LEAN = ROOT / "lean" / "M031"


def test_lean_sources_do_not_import_mamba2_implementation():
    for path in LEAN.glob("*.cs"):
        source = path.read_text(encoding="utf-8")
        assert "using mamba2" not in source.lower()
        assert "mamba2.indicators" not in source.lower()
        assert "mamba2.strategy" not in source.lower()


def test_lean_contract_pins_direct_sources_and_causal_rules():
    data = (LEAN / "M031FrozenData.cs").read_text(encoding="utf-8")
    algorithm = (LEAN / "M031FrozenBaselineAlgorithm.cs").read_text(encoding="utf-8")
    for token in ("FromUnixTimeSeconds", "LocalFile", "M1_ASK", "M5", "EndTime"):
        assert token in data
    for token in (
        "KPeriod = 21",
        "DPeriod = 7",
        "Slowing = 7",
        "EmaPeriod = 7",
        "AtrPeriod = 14",
        "TakeLast(10)",
        "canonical_m5_direct",
        "m030.events.v1",
        "SLTP_MODIFY",
        "IsBlocked",
        "ValidateInputSeal",
        "ExpectedM1Sha256",
        "ExpectedM1AskSha256",
        "ExpectedM5Sha256",
    ):
        assert token in algorithm


def test_lean_contract_uses_same_comparison_keys():
    algorithm = (LEAN / "M031FrozenBaselineAlgorithm.cs").read_text(encoding="utf-8")
    for token in (
        "utc_time_ms",
        "m1_source_open_utc",
        "m5_source_open_utc",
        "m1_k",
        "m1_d",
        "m5_k",
        "m5_d",
        "entry_or_exit_price",
        "request_id",
        "position_id",
    ):
        assert token in algorithm
