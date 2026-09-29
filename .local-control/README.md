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
m022_inventory_tests
m022_history_checkpoint_probe
m022_history_depth_probe (retired)
m022_tick_inventory_cleanup
m022_tick_inventory
m022_history_inventory_cleanup
m022_history_inventory  # retired refusal; do not use for new work
m022_phase1_ema_family
m022_phase1_ema_assessment
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

M022 fixed Phase-1 spread actions:

- `m022_phase1_spread_family`
- `m022_phase1_spread_assessment`

M022 fixed Phase-1 ATR-SL actions:

- `m022_phase1_atr_sl_family`
- `m022_phase1_atr_sl_assessment`

M022 fixed Phase-1 ATR-TP actions:

- `m022_phase1_atr_tp_family`
- `m022_phase1_atr_tp_assessment`

M022 fixed Phase-1 session actions:

- `m022_phase1_session_family`
- `m022_phase1_session_assessment`

M022 fixed Phase-2 development actions:

- `m022_phase2_development_family`
- `m022_phase2_development_assessment`

These actions expose development-only execution for the pre-frozen P2-R/P2-01…P2-12 matrix. They do not expose validation, holdout, arbitrary shell, or real-order operations.

M022 fixed Phase-2 validation actions:

- `m022_phase2_validation_family`
- `m022_phase2_validation_assessment`

These actions expose validation only for the frozen entrants P2-R, P2-01, P2-03, and P2-08. Historical-holdout execution is not exposed. Arbitrary shell and real-order operations remain unavailable.

## M023 fixed diagnostic actions

- `m023_direction_session_tests` — narrow native tests for the read-only analyzer.
- `m023_direction_session_diagnostic` — reads only the six exact accepted M022 P2-R/P2-03/P2-08 development/validation diagnostic JSONs, verifies their hashes, builds the frozen EAT/London/New-York/day/fold attribution twice, and requires byte-identical artifacts.

These actions do not run strategy replay, do not inspect historical holdout, do not inspect M021, and expose no real-order or arbitrary-shell capability.

## M023 Stage-A direction actions

- `m023_stage_a_direction_family` — exact P2-08 anchor on the fixed 225-date seen-research partition; D-R runs first, then D-S/D-B with at most two non-reference processes. Produces deterministic A/B baseline/diagnostic/summary artifacts and refuses partial artifacts or invariant drift.
- `m023_stage_a_direction_assessment` — reads only the completed Stage-A artifacts, applies the prospectively frozen activity/quality/concentration/weekly gates, classifies D-S/D-B, and mechanically fixes exactly one Stage-B direction. It does not execute Stage B.

No M023 holdout action, session execution action, weekday execution action, arbitrary shell action, or real-order action is exposed.

## M023 Stage-B session actions

- `m023_stage_b_session_family` — runs S-R first, requires exact accepted D-B economic equivalence, then and only then runs S-ACTIVE/S-MORNING/S-MIDDAY/S-AFTERNOON with at most two non-reference processes. Session filters affect new BUY entry eligibility only.
- `m023_stage_b_session_assessment` — reads completed Stage-B artifacts only, applies the prospectively frozen same-window representation, strict-positive profitability, fold/symbol/week breadth, concentration, and deterministic reduction rules, and fixes one supported session or zero.

No historical-holdout action and no weekday execution action is exposed.


## M024 Symbol Specialization actions

- `m024_symbol_specialization_tests` — runs only the focused native tests for
  the M024 read-only symbol attribution analyzer on
  `symbol-specialization-research`.
- `m024_symbol_specialization_diagnostic` — verifies the exact accepted M023
  Stage-A D-B deterministic summary pair and its frozen SHA-256, builds the
  four predeclared M024 descriptive subsets twice, requires byte-identical
  output artifacts, and mechanically reports the prospectively frozen
  descriptive screen.

These actions do not run a strategy replay, do not open historical holdout, do
not inspect M021 post-cutoff outcomes, do not use M025 outcomes, and expose no
arbitrary-shell or real-order capability.


## M024 Stage-2 causal symbol actions

- `m024_stage2_symbol_tests` — focused native tests for the frozen C-R/C-UJ
  causal symbol family and supporting M023 reference machinery.
- `m024_stage2_symbol_family` — runs C-R first, requires exact accepted M023
  D-B equivalence, then runs the sole C-UJ / USDJPY-only strategy arm while
  retaining all-five market-data and conversion streams.
- `m024_stage2_symbol_assessment` — reads completed Stage-2 artifacts only
  and mechanically applies the frozen representation, profitability,
  fold-concentration, and weekly-stability gates.

No M024 historical-holdout action exists. These actions do not inspect M021
post-cutoff outcomes, do not use M025 outcomes, expose no arbitrary shell, and
cannot place/modify/close real orders.


## M024 historical-holdout readiness

- `m024_holdout_readiness_tests` — runs only focused non-economic readiness
  and causal-symbol contract tests.
- `m024_holdout_readiness` — verifies the accepted source manifest and frozen
  57-date historical-holdout coverage, derives the exact ordered date/block
  hashes and strict replay-clock hash twice, and requires byte-identical
  metadata artifacts.

The readiness action cannot construct a broker, strategy, order, trade, P/L,
drawdown, or win-rate result. It does not expose holdout economic execution,
does not use M021/M025 outcomes, exposes no arbitrary shell, and cannot call
real-order APIs.


## M024 one-shot H-UJ holdout

- `m024_holdout_tests` — focused native tests for the frozen H-UJ runner,
  readiness lock, and mechanical assessment.
- `m024_holdout_h_uj_pair` — the only holdout economic action. It requires
  the exact accepted readiness A/B SHA, exact source manifest, and runs exactly
  one candidate: USDJPY-only strategy with all-five market/conversion data.
- `m024_holdout_assessment` — reads completed H-UJ artifacts only and applies
  the prospectively frozen representation/economic classification rules.

No alternate holdout candidate, partition, session, weekday, direction,
parameter set, M15 setting, spread gate, or position size is exposed. The
assessment cannot rerun economics. No action can place/modify/close real orders.


## M025 public benchmark Stage-1 controls

- `m025_switch_public_benchmarks` — clean-worktree-only switch to
  `public-strategy-benchmarks`; creates the local tracking branch when absent,
  permits only fast-forward synchronization, and refuses local divergence.
- `m025_public_benchmark_tests` — runs only
  `tests/test_public_benchmarks.py` on the exact remote feature HEAD.

These actions expose no M025 historical economic replay, no arbitrary shell,
no M021/M023/M024 outcome consumption for benchmark selection, and no real
order capability.


## M025 Stage-3 ingestion controls

- `m025_stage3_runtime_probe` — checks only the fixed spreadsheet parser/
  converter capabilities needed by Stage 3.
- `m025_stage3_ingestion_tests` — runs non-economic ingestion/parser tests
  plus the accepted Stage-1 public-benchmark tests.
- `m025_stage3_ingestion` — downloads only the prospectively frozen H.10,
  AQR TSMOM, and LRV artifacts; freezes raw hashes; normalizes H.10 quote
  direction; validates missingness/72-month continuity; converts legacy LRV
  XLS with installed LibreOffice solely for schema inspection; and publishes
  an immutable ingestion report.

No Stage-3 action computes returns, P/L, Sharpe, drawdown, correlation,
tracking error, ranking, or real orders.
