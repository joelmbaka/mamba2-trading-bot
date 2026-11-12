# Mamba2 Agent Operating Contract

## Responsibilities (operator-approved, 2026-11-12)

- **ChatGPT** — GitHub read-only research and review, architecture, writing/editing source and documentation directly on GitHub, commits and safe branch management.
- **Codex IDE on the Dell workstation** — **all executions**: local commands, dependency installs, tests, backtests, Wine/MT5 launches, terminal GUI/mouse/screenshot interaction, data availability checks and runtime diagnostics.
- **Operator** — approves strategy-semantic changes, execution/integration scope and any live-trading action.

Do **not** issue commands to the GitHub-mailbox `local-control` agent, consume it to operate the machine, or use `local-control-results` as the execution workflow. Those two existing remote branches are preserved but inactive. Do not create new branches for ordinary work while `scalping-recovery` is the active branch.

## Required reading order

1. `docs/CURRENT_STATE.md`
2. `docs/NEXT_TASK.md`
3. `docs/BACKTEST_SEMANTICS.md`
4. `docs/WORKFLOW.md`
5. `docs/MILESTONES.md`
6. `docs/milestones/030-scalping-parity-audit.md`

Check checked-out branch, HEAD and working-tree status before executing anything locally. If contradictory, stop and report.

## Safety

- Never rewrite Git history, force-push, reset away work, auto-stash or switch branches with a dirty worktree.
- Preserve `icon.png`; `bot_cache.json` must remain untracked.
- Never print/persist MT5 credentials or sensitive account metadata.
- Do not enable real MT5 trading, place/modify/close real orders, or initiate a monthly paper schedule without explicit authorization.
- Historical MT5 access is read-only unless approved separately.
- Do not silently change trading timeframes, signal rules, execution scheduling, accounting, ATR, spread, conversion, protection, trailing, or cost semantics.
- Maintain original M5-direction/M1-entry scalping strategy as the current research baseline, not as a live-approved system.
- Any simulated order must be isolated within the MT5 Strategy Tester (never a connected trading account).

## Known legacy Wine runtime pins

Historical environment: Python 3.10.11 x64, NumPy 2.2.1, MetaTrader5 5.0.6180. Do not casually upgrade or provision these. A separate Wine 11.21 MT5 GUI proof exists, but a standalone Windows Python bridge is not installed.

## Authorization

Implement only the scope permitted by `docs/NEXT_TASK.md`. Stage 0 is read-only research and documentation; executable parity harness/strategy changes require a separately authorized stage. Codex executes local tasks and reports exact results to the conversation for review.
