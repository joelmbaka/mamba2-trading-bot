# Next Authorized Task — M030 Stage 1E-II isolated compiler retry after completed wineboot

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1E-I STARTUP DIAGNOSIS ACCEPTED; FRESH COMPILE RETRY ONLY**

## Evidence

Stage 1E Python validation passed 39 focused and 45 regression tests. The revised no-order MQL5 EA's attempt timed out (status 124, empty log, no EX5). Stage 1E-I read-only inspection found an unfinished `wineboot.exe --init` and related disposable prefix-specific Wine initialization processes after timeout, along with smaller prefix registry files than on successful previous runs. The likely failure is incomplete new-prefix startup, **not a proven MQL5 compiler error**. Original MT5 PID `71219` remained untouched. Source SHA-256: `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`.

See `docs/milestones/030-stage1e-validation.md` and `docs/milestones/030-stage1ei-wine-startup-diagnosis.md`.

## Next task for Codex under explicit instruction

1. Confirm the branch is clean/synchronized. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md` and the Stage 1E-I diagnosis.
2. Allocate a new disposable root, initialize a brand-new prefix with a bounded `wineboot -u` using the installed Wine 11.21 runtime, confirm initialization finished and no unfinished wineboot initialization remains. Stop if initialization times out; do **not** run MetaEditor before it succeeds.
3. Protect original environment: separate app and prefix, remove/restrict broad `Z:` mapping and host home-directory links in disposable prefix, use only minimal copied MetaEditor/support files + exact unchanged EA source. Never clone original Wine prefix or copy accounts, history, config, profiles, logs or common files.
4. In that successfully initialized disposable context only, compile no-order `mql5/M030_DecisionProbe.mq5`. Report source/EX5 hashes, compiler build/log/error/warning counts, CLI exit status, remaining prefix processes and original terminal unchanged. If compilation fails, report exact diagnostics; do not edit source locally.
5. Do not reuse the failed Stage 1E prefix, change original terminal or launch Strategy Tester.

## Prohibited

No historical replay/backtest, simulated/live trades, broker login/init, market-data downloads, installations, performance tuning, repository source modifications, new branch, force-push or local-control.

## Subsequent decision

Only after successful independent compiler evidence may the team assess real MT5 source-history availability and independently verified UTC/server clock before separately authorizing a no-order decision-only tester run.
