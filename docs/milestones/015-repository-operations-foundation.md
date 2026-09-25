# Milestone 015 — Repository Operations Foundation

Status: **ACCEPTED**

Date: 2026-09-25

Accepted implementation SHA:

`32da1d846960cbc2b196da1c2f8c8a8561a5c322`

Base accepted main before this milestone:

`40536d96c6ac2119fca3c2cfec92dad889e7c878`

## Purpose

Make project state independent of chat history and reduce manual copy/paste between ChatGPT and the Codex IDE/local workstation.

## Delivered

### Durable agent handoff

Added:

- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `docs/PROJECT_PLAN.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/WORKFLOW.md`
- `docs/MILESTONES.md`
- `docs/CODE_CLEANUP.md`

### Local control

Created permanent GitHub mailbox branches:

- `local-control`
- `local-control-results`

Installed workstation service:

`chatgpt-mamba2-local-agent.service`

Validated safe:

- status;
- clean FF-only sync;
- branch switch;
- repository checks;
- runtime discovery/version checks;
- core native tests;
- full native tests;
- full Wine tests;
- pinned Wine-test-env recovery.

The control plane exposes no arbitrary shell execution.

### Repository cleanup

Removed proven dead/generated artifacts and scaffolding:

- tracked `backtest/market_metrics.csv`;
- tracked `logs/mamba2.log`;
- empty divergence/MQ5 placeholders;
- unused MT5-column diagnostic;
- unused MACD module;
- unused support/resistance module;
- obsolete TraderClient + scaffold test;
- obsolete examples directory;
- stale broker-local README;
- unused private `_registered_lower_lows`;
- direct SciPy dependency.

Root `backtest/` and `logs/` are now generated-output paths and ignored.

## Validation evidence

Core local-control test profile:

**73 passed**

Full native:

**164 passed, 2 skipped**

Full Wine:

**164 passed, 2 skipped**

Wine runtime:

- Python 3.10.11 AMD64
- NumPy 2.2.1
- MetaTrader5 5.0.6180
- pytest 9.1.1

Repository checks:

- `uv lock --check`: PASS
- `git diff --check`: PASS
- divergence: 0/0
- worktree: clean
- `bot_cache.json`: not tracked
- `icon.png`: tracked and unchanged

The suite decreased by one passing test because the obsolete TraderClient scaffold test was intentionally deleted with its dead implementation.

## Deferred cleanup candidates

Not mixed into this milestone:

- unused direct `pydantic` dependency;
- moving `pytest-asyncio` from runtime to dev dependency;
- duplicate `update_pl_periodically` scheduling in `main.py`;
- optional retirement of tested-but-nonproduction trend-line API.

Those require their own review because dependency/runtime or live-behavior implications are broader than dead-file deletion.

## Next milestone

016 — First real five-symbol historical baseline.
