# Next Authorized Task — M030 Stage 1Q deterministic signal/indicator boundary tests

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1P READ-ONLY PYTHON AUDIT ACCEPTED; P0 TEST IMPLEMENTATION NEXT**

## Evidence

Stage 1P Codex found strong existing deterministic coverage for completed-bar semantics, synthetic runner position/pending-order guards, stochastic 21/7/7 arithmetic, EMA/ATR caching, stop/target exits, trailing and M030 schema. Four main gaps remain: real production ten-candle extreme *not fresh crossover*, indicator warm-up/first-source seeding, full M030 lifecycle event ordering and real strategy + runner position blocking. Full ranked audit: `docs/milestones/030-stage1p-python-gap-audit.md`.

The original standalone MT5 account-free launcher/tester attempt remains stopped under `docs/milestones/030-stage1o-stop-standalone.md`. No native historical clock, native OHLC/ticks or broker execution parity has been established.

## Next task — ChatGPT GitHub source only: Stage 1Q

1. Add **synthetic tests** calling actual production strategy or `m030_signal_observer.py` for BUY/SELL using a full ten-candle M1 stochastic K sequence. An earlier oversold/overbought K plus valid latest K/D, M5 direction and EMA/candle filter must emit ENTRY without requiring a fresh K/D crossover. Change only earlier extreme and assert no signal.
2. Explicitly test Stochastic(21,7,7) public-API 34-row insufficient-history and 35-row first eligible boundary; decision cannot use pre-warm-up K/D.
3. Replace tautological short-prefix EMA test with an intentionally discriminating first-source/short-source vector and assert a nonzero divergence while correctly seeded recurrence equals `ewm(adjust=False)`.
4. Explicitly test ATR14 14 vs 15 completed M5-bar availability and a gap-sensitive hand-computed TR mean.
5. Do **not** modify frozen production strategy, settings, dataset, historical timestamp mapping or trading execution code just to satisfy a test. If expected semantics conflict with actual implementation, record the precise discrepancy for review rather than silently changing behavior.
6. After GitHub source-only implementation, hand to Codex for focused synthetic tests, regressions and syntax/static analysis. No MT5/Wine/Tester run.

## Subsequent task

Stage 1R (separate gate): M030 lifecycle event ordering and production strategy position-blocking integration, only after Stage 1Q validation.

## Prohibited

No historical Python economic backtest, Strategy Tester/Wine/MT5, order execution even simulated outside bounded synthetic mocks, broker connection, data downloads, optimization, production strategy edits without review, native account/history copies, reset/force-push/branch creation or local-control.
