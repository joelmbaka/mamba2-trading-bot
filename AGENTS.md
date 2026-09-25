# Mamba2 Agent Operating Contract

The two primary working agents are:

- **ChatGPT** — architecture, review, milestone ownership, acceptance criteria, and local-control orchestration.
- **Codex IDE agent** — local implementation/execution on the physical development machine.

A fresh agent must not depend on chat history.

## Required reading order

Before changing code:

1. `docs/CURRENT_STATE.md`
2. `docs/NEXT_TASK.md`
3. `docs/BACKTEST_SEMANTICS.md`
4. `docs/WORKFLOW.md`
5. `docs/MILESTONES.md`

If checked-out branch, HEAD, or working-tree state disagrees with the docs, stop and report the mismatch.

## Safety

- Never rewrite Git history, force-push, reset away work, or auto-stash.
- Never switch branches with a dirty worktree.
- Preserve `icon.png`.
- `bot_cache.json` must remain untracked.
- Never print/persist MT5 credentials or account metadata.
- Never enable real MT5 trading integration unless the authorized task explicitly requires it.
- Never place, modify, or close a real MT5 order during backtest/validation work.
- Historical MT5 access is read-only unless explicitly authorized.
- Do not silently change strategy, execution, accounting, ATR, spread, conversion, or cost semantics.

## Accepted Wine runtime

- Python 3.10.11 x64
- NumPy 2.2.1
- MetaTrader5 5.0.6180

Do not casually upgrade these pins.

## Authorization rule

Implement only `docs/NEXT_TASK.md`.

A milestone closes only after implementation, validation, exact implementation SHA capture, documentation update, and next-task handoff.
