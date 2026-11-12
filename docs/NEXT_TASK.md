# Next Authorized Task — M030 Stage 1P Python parity-gap audit (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1O COMPLETED — ACCOUNT-FREE NATIVE MT5 TESTER PATH PAUSED**

## Accepted findings

Codex Stage 1O read-only inspection confirmed repeating the blank, sandboxed MT5 startup under Wine 11.21 produced consistent but unexplained shutdown (outer status 69, internal exit 0, shutdown 10053). The cause is **not established**. No supported standalone agent startup contract, account-free native EURUSD history portability, verified historical server-to-UTC mapping, or native OHLC parity was found. Do not repeat blank terminal attempts or run `metatester64.exe` based on guesses. See `docs/milestones/030-stage1o-stop-standalone.md`.

Prior independent no-order MQL5 decision and clock probes compiled; focused Python/synthetic tests passed. Compilations and synthetic tests are **not** independent native MT5 parity or trading-profit evidence.

## Next bounded Codex task — read-only Python correctness inventory

1. Verify clean synchronized `scalping-recovery`, read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and the Stage 1O stop decision.
2. Read existing Python production strategy, stochastic 21/7/7, EMA7 and ATR14 code, replay feed, position manager, broker, backtest runner, and M030 event signal observer.
3. Inventory currently asserted **synthetic** behavior and gaps for M5/M1 completed-bar eligibility, recent-ten-K extremes (not crossover), EMA warm-up, ATR14 exact TR, candidate action vs account/position-blocking order, SL/TP attachment timing, trailing/closure lifecycle, price-source assumptions and event ordering.
4. Create a prioritized **read-only report** recommending narrowly scoped synthetic unit/property tests or source-only corrections, with exact file/line references where available. Identify invariants that cannot be proven without native MT5 observations or broker costs/tick data. Avoid claiming reproducibility/profitability from tests.
5. Do not run historical price replay, Strategy Tester, Wine/MetaEditor/MT5, order simulations, broker connections, or downloads. Do not change source/files or branch; return findings for GitHub-only fixes after separate review.

## Prohibited pending new evidence

No more blank-terminal retries or undocumented bare tester starts; no copying account-specific MT5 history/config, broker login, network history synchronization, simulated/live orders, strategy/economic optimization, installs, reset/force-push/branch creation or local-control.

## Future split

- **Track A**: strengthen deterministic Python strategy correctness and execution state invariants, starting read-only.
- **Track B**: native MT5 time/bar/tick parity remains explicitly blocked until a genuinely new, vetted data interface or privacy-preserving independent native export is available.
