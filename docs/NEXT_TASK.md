# Next Authorized Task — M030 Stage 1Q synthetic test validation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1Q TEST SOURCE COMMITTED; EXECUTION/VALIDATION PENDING**

## What changed on GitHub

Stage 1P audit identified missing real production ten-candle signal semantics tests, first-source EMA seed boundaries, stochastic warm-up and ATR14 gap sensitivity. Codex then produced a read-only implementation plan, confirming exact production path `mamba2/strategy/triple_cross.py` and public ATR14 insufficient-history **0.0** sentinel.

ChatGPT implemented **test-only** Stage 1Q on GitHub:
- `tests/test_triple_cross_condition_semantics.py`: real production BUY and SELL ten-M1-K sequences, older extreme vs deleted extreme, no fresh last-candle K/D cross, M5 direction, EMA/candle filter and untouched initial SL/TP=0.
- `tests/test_m030_stage1q_boundaries.py`: direct M030 observer candidate cases and explicit public `get_stochastic` 34/35 rows, `get_moving_average` EMA7 long-vs-short-prefix seeding, `get_atr` 14/15 bars including prior-close gap.
- `tests/test_m030_incremental_contract.py`: removed always-true EMA divergence assertion.
- `docs/milestones/030-stage1q-test-implementation.md`: scope and review notes.

**All new test changes remain UNTESTED.** Production strategy and indicators, M030 probes, broker/runner, frozen datasets and MT5 installation were NOT changed.

## Next bounded Codex validation under explicit instruction

1. Verify clean synchronized `scalping-recovery`, read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this document and Stage 1Q milestone.
2. Run `PYTHONPATH=. ./.venv/bin/pytest tests/test_triple_cross_condition_semantics.py tests/test_m030_stage1q_boundaries.py tests/test_m030_incremental_contract.py -q` and relevant stochastic, EMA, ATR, M030 parity and regression tests; Python syntax compilation.
3. Static-review the synthetic ten-bar no-fresh-crossover scenarios, real strategy/observer calls, mocked broker/reporting path, first-source EMA divergent seed, ATR14 public 0.0 sentinel and gap-sensitive TR mean.
4. Return exact test counts and failure traces, with source path/line defects; do not repair source locally or change production rules. If any test fails, send evidence for a GitHub-only test correction/contract review.
5. Confirm original terminal/workstation and original historical dataset unchanged. No MT5/Wine/Tester operations.

## Following gate

After all source/test validation passes, Stage 1R should address ordered M030 M1_CLOSE→SIGNAL→SUBMIT→FILL→SLTP_MODIFY→EXIT streams and real production strategy position-blocking integration using only deterministic synthetic fixtures.

## Prohibited

No Python historical economic replay, Wine/MT5/MetaEditor/Strategy Tester launch, native history import/copy, broker login or network data access, simulated/live trading, production strategy tuning, package installs, local source modifications, reset/force push/new branch or local-control. Native MT5 parity remains blocked under Stage 1O.
