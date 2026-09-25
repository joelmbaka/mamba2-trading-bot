# Mamba2 Remote Local Control

This branch is a GitHub-mailbox control plane for the physical Mamba2 checkout.

## Branches

- commands: `local-control:.local-control/command.json`
- results: `local-control-results:.local-control/result.json`

## Safety model

- The workstation agent polls GitHub every five seconds.
- It may automatically fast-forward only the branch already checked out locally.
- Automatic sync refuses dirty trees, detached HEAD, missing remotes, and divergence.
- Branch switching is explicit only.
- Branch switching refuses dirty trees and any target branch with local-only commits.
- No stash, reset, force checkout, history rewrite, branch deletion, arbitrary shell execution, or application-branch push exists.
- Test actions are fixed allowlisted workflows.
- Test subprocesses remove the real-MT5 integration opt-in and MT5 login/password/server variables.
- The control plane never places, modifies, or closes MT5 orders.
- Runtime/test output is bounded before publication.
- `bot_cache.json` contents are never read by control actions.

## Initial actions

```text
status
sync
switch_branch
repo_checks
bootstrap_wine_test_env
runtime_discovery
runtime_versions
test_core
test_full_native
test_full_wine
first_baseline_cleanup
first_baseline_export
first_baseline_run_pair
baseline_diagnostic_run_pair
```

`switch_branch` requires:

```json
{"branch":"branch-name"}
```

## Bootstrap

From the physical Mamba2 checkout:

```bash
git fetch origin local-control local-control-results
bash <(git show origin/local-control:.local-control/bootstrap.sh)
```

Re-run the same bootstrap command to update the installed control agent.

Service:

```text
chatgpt-mamba2-local-agent.service
```

Installed files live under:

```text
~/.local/share/chatgpt-mamba2-local-agent/
```

The application checkout is never converted into a control worktree. Results use a separate isolated worktree.


`bootstrap_wine_test_env` is a fixed recovery action. It creates only `.venv-wine` from the pinned Wine Python/constraints and never initializes MT5 or reads account state.


## First-baseline workflows

These are fixed milestone-016 actions, not arbitrary commands.

- `first_baseline_cleanup` removes only `backtest_data/first-baseline-20260901-20260925`.
- `first_baseline_export` performs the read-only MT5 export for Sep 1–24, 2026 using the five configured symbols, M1/M5/M15, and tick-derived Ask.
- `first_baseline_run_pair` runs the accepted baseline twice, verifies byte-identical reports/SHA-256, and publishes only compact report metrics.

The exporter clears credential environment variables and uses the already-authenticated terminal session. These actions never enable the live MT5 integration marker and never place/modify/close orders.

## Baseline-diagnosis workflow

`baseline_diagnostic_run_pair` is the fixed milestone-017 action. It requires
`backtest-baseline-diagnosis`, reuses the accepted M016 dataset, runs the
trade-level diagnostic replay twice, proves that the ordinary baseline report
still has the accepted M016 SHA-256, and requires both diagnostic JSON artifacts
to be byte-identical before publishing compact analysis evidence.


## Proven-defect review workflow

`defect_review_diagnostic_run_pair` is the fixed M018 acceptance action. It
requires `backtest-proven-defect-review`, reuses the accepted M016 dataset,
runs the corrected diagnostic replay twice, requires byte-identical corrected
baseline and diagnostic artifacts, compares aggregate results to accepted M016,
and verifies that no initial take-profit remains on the wrong side of its fill.
