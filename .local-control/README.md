# Mamba2 Remote Local Control

This branch is a GitHub-mailbox control plane for the physical Mamba2 checkout.

## Branches

- commands: `local-control:.local-control/command.json`
- results: `local-control-results:.local-control/result.json`

## Safety model

- A systemd timer invokes a fresh one-shot worker every 15 seconds.
- Before each invocation, the permanent runner refreshes and compiles the latest control code from `local-control` and atomically installs it.
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
controlled_experiment_control_pair
controlled_experiment_m020a_pair
controlled_experiment_m020b_diagnostic
controlled_experiment_m020c_pair
controlled_experiment_m020d_pair
m021_forward_readiness
m021_historical_regression
m021_primary_export
m021_primary_pair
m022_history_depth_probe
m022_history_inventory_cleanup
m022_history_inventory
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

Bootstrap is install-once. The installed timer runner refreshes and compiles the latest allowlisted `agent.py` and `validation.py` from `local-control` before every poll, so future milestone actions do not require another bootstrap.

Worker and timer:

```text
chatgpt-mamba2-local-agent.service
chatgpt-mamba2-local-agent.timer
```

The service is a one-shot allowlisted worker. The timer is the persistent
polling mechanism, which avoids stale long-running process state and prevents
overlapping command execution. The validation module is the canonical action
allowlist; the worker derives its allowed validation actions from that module.

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

## Broader-history workflow

M019 uses four fixed actions on `backtest-broader-history`:

- `broader_history_coverage_probe` — read-only MT5 M1/M5/M15 availability
  plus distributed tick-history samples for the fixed Jun 23–Sep 25 UTC window;
- `broader_history_cleanup` — removes only the fixed M019 dataset directory;
- `broader_history_export` — exports the fixed real-data window, validates
  manifest integrity and one-for-one M1/Ask coverage, and requires the
  Sep 1–24 overlap to equal the accepted M016 dataset;
- `broader_history_run_pair` — runs corrected diagnostic replay twice and
  requires byte-identical baseline/diagnostic artifacts, zero wrong-side
  initial TPs, and zero negative take-profit exits.

These actions never enable live MT5 integration and never place, modify, or
close orders.


## Controlled-experiment workflow

M020 begins with the fixed `controlled_experiment_control_pair` action on
`backtest-controlled-experiments`. It runs the control-only experiment harness
twice against the immutable M019 dataset and requires both baseline and
diagnostic outputs to be byte-identical to the accepted M019 hashes before any
treatment result is interpreted.

The action is historical/read-only, strips MT5 credential/integration
environment variables, and never enables real trading.


After the control gate is accepted, `controlled_experiment_m020a_pair` runs
the single documented M020-A treatment twice on the same immutable dataset.
It requires deterministic treatment baseline/diagnostic artifacts, zero
00:00–03:59 UTC entries, the existing wrong-side-TP and negative-TP safety
gates, and no new strategy-reporting artifacts. It returns control/treatment
aggregate, per-symbol, side, and calendar-subperiod comparisons without
changing any other strategy parameter.

`controlled_experiment_m020b_diagnostic` is a read-only M020-B reporting action. It consumes the accepted M019/M020 control diagnostic artifact, produces deterministic spread-band and percentile summaries for the 00:00–03:59 UTC population versus all other entry times, and does not run or modify strategy behavior.


### M020-C decision-time spread workflow

`controlled_experiment_m020c_pair` runs the causal decision-time spread
diagnostic twice on `backtest-controlled-experiments`. It requires both runs
to reproduce the accepted M019 baseline and diagnostic hashes exactly, requires
the new decision-spread artifacts to be byte-identical, and refuses missing
decision-spread rows or any new strategy-reporting artifact. It is historical,
read-only, and never filters or rejects an order.
