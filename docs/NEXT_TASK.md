# Next Authorized Task — M030 Stage 1H-II canonical CSV parser validation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1H-I TESTS AND ISOLATED EA COMPILATION PASSED; PYTHON FORMAT FIX UNTESTED**

## Evidence accepted

At source HEAD `cfa0bc7ac4eea21f32be279e13c8eab35f628194`, Codex passed 46 focused tests, 59 regressions, Python syntax checks, and isolated MetaEditor 6316 compilation of the standalone no-order `M030_ClockBarProbe.mq5` (0 errors/warnings, EX5 SHA-256 `59cf2288212bc8d215b32f23a7bda89c9faf25dbcd486706999ad5251c5f2496`). The copied source hash was `9b6b4782402c0eea268ccea8325ca81bf03b0e265054d58904c598137834a2fe`. Wine CLI code 1 is the existing anomaly; no tester was launched.

Codex additionally discovered that canonical EURUSD M1/M5 CSV files use integer Unix epoch seconds in `time`, not ISO text. ChatGPT corrected `mamba2/backtest/m030_clock_discovery.py` to support an **explicit** `reference_timestamp_format="unix_seconds_utc"` parameter with strict minute alignment and hash verification, plus synthetic format tests. The existing MQL5 source was not changed. See `docs/milestones/030-stage1hi-validation.md`.

## Next Codex task under explicit bounded instruction

1. Verify clean, synchronized `scalping-recovery`; read `AGENTS.md`, this file and Stage 1H-I milestone.
2. Run `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_clock_discovery.py tests/test_m030_parity.py tests/test_m030_incremental_contract.py -q`, report exact counts/failures, Python syntax and relevant regressions.
3. **Read-only, offline** inspect canonical original M1/M5 CSVs with the new explicit epoch reader. Confirm hashes `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` (M1) and `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` (M5), correct first timestamps, sample rows 1,440/288, and no parsing errors. Do not generate/rewrite CSVs or silently infer UTC from numeric values; record that exporter semantics are an unverified timestamp claim.
4. Confirm original `M030_ClockBarProbe.mq5` SHA-256 remains `9b6b4782402c0eea268ccea8325ca81bf03b0e265054d58904c598137834a2fe`; no MQL5 recompile necessary unless source changes.
5. Return evidence and remaining blockers, and a plan for proving an isolated offline tester can access native EURUSD history without copying account data or allowing network access. **Do not create a tester or attempt data provisioning.**

## Not authorized

No Wine/MT5/MetaEditor/Strategy Tester launch, Python historical backtest or trades, broker connections, data download/import, package installation, source edits locally, original terminal modifications, new branches, or local-control. A separate explicit authorization is mandatory before any decision-free tester discovery exercise.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1g-provenance.md`
- `docs/milestones/030-stage1h-clock-probe.md`
- `docs/milestones/030-stage1hi-validation.md`
