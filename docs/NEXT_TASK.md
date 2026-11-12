# Next Authorized Task — Scalping Recovery

Date: 2026-11-12
Branch: `scalping-recovery`
Status: M030 STAGE 0 SOURCE AUDIT DOCUMENTED — CODE/EXECUTION NOT AUTHORIZED

## Owner-approved strategy direction

Restore **intraday Forex scalping** as the primary Mamba2 research objective:
- M5 is the direction/trading timeframe; M1 is the entry/execution timeframe.
- The original five FX symbols are the starting research universe, not a commitment to trade every symbol.
- Treat historical M019–M024 experiments as closed evidence, not as adopted production rules.
- Preserve monthly M025–M029 strategy, evidence, protocols and implementation for historical reference; do not resume its prospective paper schedule or silently remove anything.
- Do not interpret a target near 50% win rate as sufficient: also require positive net expectancy *after* costs, robustness and acceptable drawdown.
- Do not modify real production trading behavior, enable MT5 orders, or change trading account credentials.

## Stage 0 — GitHub source audit completed; workstation evidence outstanding

1. Confirm the local checkout on `scalping-recovery`, a clean worktree and 0/0 divergence with `origin/scalping-recovery`.
2. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/WORKFLOW.md`, `docs/CURRENT_STATE.md`, and M019–M024 milestone records.
3. Audit how original M5/M1 signals, stochastic, EMA, ATR, stop/target, trailing, spread, order scheduling and reporting are implemented.
4. Inventory what Python replay actually knows about Bid/Ask, tick timing, execution time, spread, commissions, slippage and stop-first ambiguity; distinguish measured broker conditions from placeholders.
5. Inventory MT5 visual Strategy Tester feasibility under the existing isolated Wine environment: whether a compatible MQL5 Expert Advisor test harness is required, and whether the relevant tick/data set and broker symbol settings are reproducible. Do not connect to a broker, install software, drive the mouse, or issue orders at Stage 0.
6. Design an independent Python-vs-MT5 trade-level parity contract: same historical input, UTC decision/fill times, symbol digits/point/pip conventions, price, volume, protective orders, modifications, exit reason, raw cost and converted P/L. Define exact matches where possible and tolerances / expected differences for tick-vs-OHLC cases. Include first-divergence report and screenshot/journal evidence.
7. Identify a single fixed one-symbol one-day sample plus adversarial examples (wide spread, SL/TP in same M1 bar, trailing modification, rollover) *before* looking at comparative outcomes. Then propose a deterministic expansion set.
8. Report the exact paths requiring future changes, test plan, constraints and milestone gates. No economic optimization at this stage.

## Stage 0 source audit outcome

Read `docs/milestones/030-scalping-parity-audit.md`. It identifies historical M1/M5 implementation, priority signal/fill/trailing/cost risks, real-tick versus OHLC limitations, an independent Python-vs-MT5 trade-event ledger, and the proposed fixed EURUSD 2026-09-10 UTC one-day test window.

The read-only GitHub audit and operating-contract documentation were completed. **No code was executed**, so no claims of parity, historical tick completeness, MT5 tester compatibility, or visual result matching have been made. Next workstation evidence collection must be delegated to Codex, not the local-control mailbox, and must be explicitly scoped to read-only preflight before any test EA runs or simulated trade execution.

## Later stages — NOT YET AUTHORIZED

Stage 1: instrumented Python replay plus independent MQL5/MT5 tester parity harness.
Stage 2: cross-engine comparison and visual inspection; resolve execution divergences before tuning.
Stage 3: predeclared, one-hypothesis-at-a-time scalping research on development data.
Stage 4: unseen historical validation and forward demo-paper testing.
Stage 5: only after separately approved risk and live-trading gates, consider any production deployment.

## Safety and branch hygiene

- Retain only `main`, active `scalping-recovery`, and the operational GitHub-mailbox branches `local-control` and `local-control-results`.
- Do not create another feature branch for this work.
- All changes to signal/entry/exit or cost semantics require explicit review and separate authorization.
- Do not reset, rebase, force-push, rewrite history, auto-stash or delete protected work.
- No real order send/modify/close. No unintended monthly paper schedule or monthly broker session.
- Keep `icon.png`, cache privacy, approved local-control allowlists and existing data intact.

## Acceptance for Stage 0

A written, source-linked implementation and parity specification with risks, interfaces, data availability and test criteria. **No strategy or MT5 integration code change.**
