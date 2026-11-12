# ChatGPT ↔ Codex IDE Workflow — Mamba2

## Current division of responsibilities

**ChatGPT**: inspect GitHub directly, design architecture and experiments, create/edit GitHub source and documentation, commit changes on the active branch, review results.

**Codex IDE**: local terminal commands, branch checkout/sync on the workstation, dependency provisioning, unit/integration tests, backtests, native/Wine execution, MT5 Strategy Tester interaction (including GUI/screenshots), and result extraction.

**Operator**: approves milestone boundaries, trading strategy semantic changes, brokerage/data access, risk and any live trading.

Do **not** dispatch any local work using the `local-control` / `local-control-results` branches. They remain preserved but inactive. Local executions must happen explicitly through Codex, and the outcome must be returned to the ChatGPT conversation. GitHub operations by ChatGPT are allowed without workstation execution.

## Fresh-session handoff

Read in order: `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/NEXT_TASK.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/MILESTONES.md`, `docs/milestones/030-scalping-parity-audit.md`.

## Milestone lifecycle

1. Work on the existing `scalping-recovery` branch. Do not create another branch merely to advance a milestone.
2. Confirm exact GitHub HEAD and clean local worktree.
3. ChatGPT implements source/document changes only within explicitly authorized scope.
4. Codex fetches those changes without overwriting local work and runs authorized validation on the Dell.
5. Codex reports command results, exact SHAs, tests, reproducibility evidence and any failures here.
6. ChatGPT records acceptance and subsequent task boundaries in GitHub.
7. Merge to `main` only when ready; delete obsolete branches as part of deliberate consolidation, never force-delete or rewrite history.

## Git and trading safety

Refuse dirty tree, detached HEAD, unexpected divergence, missing remote target or local-only commits before a risky switch or merge. Never auto-stash, reset away work, force-push, or silently modify broker credentials.

Use MT5 Strategy Tester for simulated trades; never execute real-account orders in verification work. Real market-data access requires separate authorization. Keep environments isolated, and do not accidentally resume previous monthly momentum paper execution.

## Current authorized task

M030 Stage 0: read-only GitHub audit and independent Python/MT5 parity design. Runtime audit and test execution are reserved for a subsequent explicitly authorized Codex step.
