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

Verified evidence:

- branch `strategy-parameter-research`;
- original M022 start SHA `253b6ee840e5489a2c5db27d064500bb44f93e1e`;
- current reviewed feature SHA before the next export:
  `0da93c9a5ecb84dd61e5ad7bf3b9e6a714daad46`;
- Dell worktree/repo gate clean and divergence `0/0`;
- synchronized Bid/Ask ticks + native M5/M15 proven through 2025-08-25 for all five symbols;
- 2025-07-28 failed common synchronized tick coverage because EURJPY lacked qualifying ticks;
- the full tick-derived Bid/Ask M1 candidate was rejected by the frozen M019 overlap gate: Ask + M5/M15 matched, but tick-derived Bid M1 differed by 1–5 points on four symbols;
- the 0.5-point gate was **not** relaxed;
- MT5 `MaxBars` was safely raised from 100000 to 500000 with the original config backed up;
- runtime `maxbars=500000` was verified;
- native M1 for 2025-08-25 is now available for all five symbols;
- no economic M022 result has been inspected;
- M021 remains isolated.

### Exact next authorized sequence

1. Synchronize the Dell feature checkout to the latest `strategy-parameter-research` documentation SHA.
2. Run the repository gate.
3. Export a fresh versioned candidate using:
   - native MT5 Bid M1;
   - tick-derived Ask M1 aligned to native M1;
   - native M5/M15;
   - conservative start 2025-08-25;
   - end-exclusive cutoff 2026-09-25T00:00:00Z.
4. Apply the replacement frozen overlap gate recorded in the M022 milestone:
   - native Bid M1 overlap index/frame exact;
   - Ask overlap index exact and OHLC <= 0.5 point;
   - zero candidate Ask-vs-Bid index mismatch;
   - native M5/M15 exact;
   - Ask source `copy_ticks_range`.
5. Record exact ranges, counts, gaps, hashes, broker/runtime metadata.
6. If the gate passes, materialize the already-frozen chronological 60% / 20% / 20% development / validation / untouched-holdout split at whole UTC trading-day boundaries and verify >=20 common trading dates per partition.
7. Freeze the resulting exact dates/hashes in docs.
8. Only then implement/run Phase-1 parameter arms one family at a time.

Do not revisit the failed tick-derived-Bid candidate by weakening tolerance.

## Start here

Read the durable handoff docs and M022 milestone, then resume from the exact sequence above.

Do not interpret parameter winners until the historical inventory, partitions, reporting rules, and selection rules are frozen.
