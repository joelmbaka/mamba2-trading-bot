# Next Authorized Task

## Milestone 022 — two-timeframe parameter research

Branch:

`strategy-parameter-research`

M022 protocol:

`docs/milestones/022-two-timeframe-parameter-research.md`

M021 remains independently frozen on:

`prospective-forward-validation`

Do not modify, retune, rebase, or inspect M021 early.

## Objective

Systematically validate the human-selected parameters of the existing **M5 + M1** strategy while preserving its basic entry structure.

Do not add M15/three-timeframe confirmation in M022.

## First required gate — history inventory

Before broad parameter results are inspected, establish the maximum trustworthy common read-only MT5 history available for all five symbols:

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

Required market data:

- M1 Bid;
- Ask M1 / sufficient tick-derived Ask data for truthful spread-aware replay;
- M5;
- M15 only where existing exporter/replay compatibility requires it, never as an M022 signal input.

Record exact UTC ranges, row counts, missing-data diagnostics, artifact hashes, broker/source metadata, and runtime versions.

If enough trustworthy history exists, predeclare chronological **development / validation / untouched historical holdout** partitions before optimization outcomes are interpreted.

If history is too short for meaningful separation, stop and document that limitation rather than brute-force the already-inspected sample.

## Phase 1

Implement experiment-only parameter overrides and deterministic reporting, preserving production defaults.

Screen one family at a time using the bounded grid frozen in the M022 milestone document:

- stochastic tuples;
- symmetric oversold/overbought boundaries;
- EMA period;
- decision-time spread threshold;
- ATR SL/TP protection;
- all-hours vs the already-documented 00:00–03:59 UTC exclusion.

Do not brute-force the full Cartesian product.

## Phase 2

Only after Phase 1 evidence is reviewed:

- freeze a shortlist;
- freeze a bounded combination matrix;
- then run combinations.

Do not select solely by maximum historical P/L. Require robustness across symbols, BUY/SELL, calendar buckets, drawdown, trade count, and nearby parameter values.

## Local execution

Use `local-control` and `local-control-results` for Dell/MT5 work.

Installed service:

`chatgpt-mamba2-local-agent.service`

Prefer cloud execution/review for work that does not require the Dell. For Dell-only operations, use existing fixed allowlisted actions or add narrowly scoped fixed actions. Never expose arbitrary shell execution and never expose a real-order action.

Each local result must identify the exact feature SHA and return deterministic evidence.

## Safety / boundaries

Never:

- modify M021 frozen behavior/protocol;
- use post-Sep-25 M021 outcomes to tune M022;
- add M15 as a signal timeframe;
- change production defaults silently;
- merge to main;
- deploy;
- enable/place/modify/close real MT5 trades from research tooling;
- invent commission/slippage/swap costs.

The accepted M019/M020 regression artifacts must remain protected as specified in the M022 milestone.

## Current checkpoint

The M022 history-inventory gate has **PASSED**. No M022 parameter result has yet been inspected.

Accepted dataset:

`backtest_data/m022-history-inventory-native-m1-v3/manifest.json`

Manifest SHA-256:

`143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558`

Common trading-date-list SHA-256:

`2efcd016d0d346036a33415e794903b5fea86ad610519fbda056ceb2c94feac5`

The replacement M019 overlap gate passed exactly across all five symbols:

- native Bid M1 exact;
- Ask M1 exact;
- native M5 exact;
- native M15 exact;
- zero missing/extra Ask rows.

Frozen chronological partitions:

- development:
  `2025-08-25T00:00:00Z` → `2026-04-21T00:00:00Z`,
  **169** common trading dates;
- validation:
  `2026-04-21T00:00:00Z` → `2026-07-08T00:00:00Z`,
  **56** common trading dates;
- untouched historical holdout:
  `2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`,
  **57** common trading dates.

The holdout remains unopened for economic inspection.

Local-control reliability was hardened on `local-control` at
`d85e51d4a34ec52597e54cd8a1cad92f70fff2bb` by using
`TimeoutStartSec=infinity` and `OnUnitInactiveSec=15s` while retaining the
finite stop timeout and cgroup-wide kill semantics.

### Exact next authorized sequence

1. Synchronize the Dell feature checkout to the latest M022 feature SHA after these documentation updates.
2. Implement experiment-only parameter overrides and deterministic Phase-1 reporting without silently changing production defaults.
3. Add synthetic/unit tests for override/default equivalence and reporting determinism.
4. Preserve accepted M019/M020 regression artifacts.
5. Run Phase 1 on the **development partition only**, one parameter family at a time, relative to the frozen reference configuration:
   - stochastic tuples;
   - symmetric oversold/overbought boundaries;
   - EMA period;
   - decision-time spread threshold;
   - ATR SL/TP protection;
   - all-hours vs 00:00–03:59 UTC exclusion.
6. Do not run the full Cartesian product.
7. Do not inspect validation while selecting within a Phase-1 family except according to a separately frozen shortlist procedure.
8. Do not inspect the historical holdout yet.
9. Freeze the Phase-1 shortlist and Phase-2 matrix before any combination runs.

M021 remains independently frozen and excluded from all M022 tuning.

## Start here

Read the durable handoff docs and M022 milestone, then resume from the exact sequence above.

Do not interpret parameter winners until the historical inventory, partitions, reporting rules, and selection rules are frozen.
