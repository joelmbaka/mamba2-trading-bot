# Next Authorized Task — M030 Stage 1E-I MetaEditor startup diagnostic

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **PYTHON VALIDATION PASSED; REVISED MQL5 EX5 NOT BUILT; READ-ONLY STARTUP DIAGNOSTIC NEXT**

## Stage 1E validation

- Source HEAD `13f8aa22446e4ce4fe6a6cf99affaf300db99812`, clean and synced.
- Synthetic tests: **39 passed**; regressions: **45 passed**; Python syntax passed.
- Static review found no order/account/broker execution functionality in the tester-only probe; incremental 48-bar windows and full first-history EMA seed were reviewed.
- Disposable MetaEditor 5.0.0.6316 timed out before compiler output: CLI status `124`, empty log, no EX5. Source hash `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`; copied source matched. No warnings/errors can be inferred. Original MT5 terminal remained unchanged.

Evidence: `docs/milestones/030-stage1e-validation.md`.

## Immediate next bounded task — Stage 1E-I

Codex, after explicit instruction, performs **read-only diagnosis** of disposable Wine/MetaEditor startup failure. Verify branch clean/origin synced, no failed compiler processes remain, inspect existing available logs and metadata, original terminal isolation, compare Stage 1B-II/1D successful startup evidence, and identify safe startup-only retry conditions. Do not run MetaEditor or Wine in this read-only stage.

Report exact evidence, whether failure is prefix startup/GUI/locking/dependency related if provable, remaining uncertainty, and a proposed minimal next isolated compiler retry. Do not interpret timeout as MQL5 compilation failure.

## Following gate

Only after read-only diagnosis and explicit separate authorization may Codex create a fresh disposable prefix/app and retry compiling the **same exact source**. Never use the original running MT5 prefix/app, trading profiles or accounts.

## Forbidden

No MT5 Strategy Tester run, Python historical replay, orders even simulated, broker connection/login, downloads, package installs, production strategy changes, original-terminal interruption, optimization, force-push/reset/stash/new branches, or `local-control`/`local-control-results`.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1d-validation.md`
- `docs/milestones/030-stage1e-incremental-engine.md`
- `docs/milestones/030-stage1e-validation.md`
