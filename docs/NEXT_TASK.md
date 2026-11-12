# Next Authorized Task — M030 Stage 1E incremental indicator engine

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1D PYTHON TESTS AND DISPOSABLE MQL5 COMPILATION ACCEPTED; TESTER BLOCKED BY FULL-PREFIX COST**

## Evidence

Codex validated source `f878cbd65389ae4f1ccb490ecbfd3af93bba96ca` on clean synced `scalping-recovery`: 13 M030 tests passed; 45 relevant regressions passed; Python syntax passed. Independent revised no-order MQL5 probe compiled in a disposable Wine environment with MetaEditor 6316 and 0 warnings/errors, EX5 SHA-256 `dd019f9769c66b229b31b81ffe1bf9a0ac619dd3d4f01a6f4f2e5f1272d374a1`. CLI status `1` remains an evidence caveat. Original terminal PID 71219 stayed untouched. Complete report: `docs/milestones/030-stage1d-validation.md`.

Codex estimated approximately 19 billion inner-loop operations for a one-day run because the EA re-reads/recalculates the full 389k M1 / 78k M5 warm-up prefixes each minute. This is an analytical estimate, not a measured benchmark. **Do not run Strategy Tester.**

## Next source work — ChatGPT GitHub

Build **M030 Stage 1E**, a persistent, causal indicator-state engine inside the independent MQL5 diagnostic EA:

- Consume the complete independently seeded M1 and M5 prefixes once, retaining Python's exact EMA initial close and stochastic 21/7/7 smoothing behavior; incremental M1/M5 updates thereafter.
- Preserve native M5 ATR14 as rolling TR mean; preserve newest-ten-M1 stochastic extreme checks, current M5 K/D, completed candles, and original trend/EMA branch semantics.
- Strictly verify timestamp chronology and expected latest closed bars; reject missing, duplicated, misordered or unavailable prefixes rather than inventing data.
- Keep explicit historical server-to-UTC offset and independent M1/M5 source starts; do not auto-infer broker clock or change evaluation date.
- Keep optional bar audit and no-order tester-only safeguards.
- Add synthetic indicator-vector regression tests; document technical performance and memory constraints.
- No source changes outside GitHub, no new branches, no strategy tuning, no broker connections, no automated tester launch.

After implementation, independently ask Codex to run synthetic Python tests and *compile only* the revised EA in a new disposable isolated MetaEditor context.

## Not authorized

Do not run historical Python/MT5 replay, tester GUI, simulated/live orders, broker initialization, downloads, installs, optimization, original-terminal modifications, or local-control workflow. Full MT5 data/clock identity remains unverified.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1c-data-provenance.md`
- `docs/milestones/030-stage1d-alignment-contract.md`
- `docs/milestones/030-stage1d-validation.md`
