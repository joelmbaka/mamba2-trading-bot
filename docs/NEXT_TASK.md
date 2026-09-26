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

The history-inventory gate is active; **no parameter results have been inspected**.

Verified starting gate:

- branch `strategy-parameter-research`;
- original M022 start SHA `253b6ee840e5489a2c5db27d064500bb44f93e1e`;
- Dell worktree clean;
- divergence `0/0`;
- lock check passed.

Feature-branch inventory infrastructure now includes an opt-in tick-derived M1 path that reconstructs synchronized Bid and Ask M1 from the same MT5 tick stream. The ordinary native-M1 exporter remains the default and production strategy defaults are unchanged.

Why this was added:

- prior M019 evidence showed native M1 retained only to roughly 2026-06-22;
- native M5/M15 and real Bid/Ask tick samples existed earlier;
- M022 must distinguish terminal native-M1 retention from actual trustworthy historical market-data availability.

Pending Dell command:

`mamba2-m022-history-inventory-20260926-1217`

Do not overwrite or redispatch that command while it is still the active unpublished result. Its initial discovery method used a very old tick origin and is not the preferred method for the next probe.

The replacement local-control action `m022_history_depth_probe` is bounded to native retained-history discovery plus a tick check from the common native M5/M15 start.

## Exact next authorized sequence

1. Review the published result for `mamba2-m022-history-inventory-20260926-1217` when present.
2. Synchronize the Dell feature checkout to the latest `strategy-parameter-research` SHA.
3. Re-run repository gates and feature tests, including the tick-derived-M1 exporter tests.
4. Run `m022_history_depth_probe`.
5. If it confirms materially older synchronized Bid/Ask tick coverage, run one fixed extended inventory export using:
   - tick-derived synchronized Bid/Ask M1;
   - native M5/M15;
   - end-exclusive cutoff `2026-09-25T00:00:00Z`.
6. Validate overlap with accepted M019 history before trusting older tick-derived M1.
7. Record exact ranges/counts/gaps/hashes/source/runtime.
8. Freeze development / validation / historical-holdout dates.
9. Only then implement/run Phase-1 parameter arms.

If the resulting trustworthy history is still too short for meaningful chronological separation, stop broad parameter optimization and document that limitation.

## Start here

Read the durable handoff docs and M022 milestone, then resume from the exact sequence above.

Do not interpret parameter winners until the historical inventory, partitions, reporting rules, and selection rules are frozen.
