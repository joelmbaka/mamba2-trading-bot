# ChatGPT ↔ Codex IDE Workflow

## Roles

### ChatGPT
Architecture, milestone boundaries, review, acceptance criteria, remote GitHub operations, local-control commands, and milestone acceptance.

### Codex IDE
Physical-machine implementation/execution, native/Wine tests, authorized read-only MT5 exports, and exact evidence reporting.

The user should not need to relay long routine test/status transcripts once local-control is installed.

## Fresh-session handoff

Read:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/MILESTONES.md`

## Milestone lifecycle

1. Start from accepted SHA on named branch.
2. Implement only authorized scope.
3. Validate.
4. Record exact implementation SHA.
5. Add milestone record.
6. Update `CURRENT_STATE.md` and `NEXT_TASK.md` in a docs-only closeout commit.
7. Fast-forward `main`; never rewrite history.
8. Transition to next branch.

The implementation SHA and later docs-closeout SHA must both remain identifiable.

## Local-control architecture

Use the proven RentPayor/Milliol GitHub-mailbox pattern:

- `local-control`: command + whitelisted agent code + bootstrap.
- `local-control-results`: structured result JSON.

The workstation systemd user agent polls GitHub, safely auto-fast-forwards a clean current app branch, executes only enumerated actions, and publishes results.

No arbitrary shell action.

## Git safety

Refuse dirty tree, detached HEAD, divergence, missing remote target, or target branch with local-only commits.

Never auto-stash, reset, force-switch, delete work, rewrite history, or force-push.

## Initial Mamba2 actions

- `status`
- `sync`
- `switch_branch`
- `repo_checks`
- `runtime_versions`
- `test_core`
- `test_full_native`
- `test_full_wine`

Baseline-specific workflows can be added later as fixed actions.

## Trading safety

The local agent must never place/modify/close MT5 orders, set `MAMBA_RUN_MT5_INTEGRATION=1`, or publish credentials/account metadata.
