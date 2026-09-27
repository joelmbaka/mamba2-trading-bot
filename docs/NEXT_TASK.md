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

The M022 history/data gate has passed and the first scientifically accepted
development economic reference has now passed.

Accepted source dataset:

`backtest_data/m022-history-inventory-native-m1-v3/manifest.json`

Source manifest SHA-256:

`143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558`

Frozen partitions remain:

- development:
  `2025-08-25T00:00:00Z` → `2026-04-21T00:00:00Z`,
  **169** trading dates;
- validation:
  `2026-04-21T00:00:00Z` → `2026-07-08T00:00:00Z`,
  **56** trading dates;
- untouched historical holdout:
  `2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`,
  **57** trading dates.

Validation and historical holdout remain closed for economic inspection.

### Accepted reference-v3

Command:

`mamba2-m022-phase1-reference-v3-20260926-1859`

Feature SHA:

`3136d2143f79e80ea0ce9688559b7e7aaaca7ef5`

Reference evidence:

- deterministic A/B: PASS;
- replay boundaries: **241,474**;
- replay-boundary SHA:
  `17685ae6a08ce8e6e4f3af215f4215f92fe87de24f5a934d7935778634d47e28`;
- closed trades: **12,006**;
- net realized P/L: **-$15,499.3611**;
- ending realized balance: **-$5,499.3611**;
- max equity drawdown: **$15,501.9142 / 155.0054%**;
- non-flat win rate: **32.8667%**;
- remaining open positions: **3**;
- TP/safety invariants: PASS;
- validation used: no;
- historical holdout used: no;
- M021 outcomes used: no;
- live orders: no.

Reference artifact hashes:

- baseline:
  `55630b2ff48b8594f04ed2d7ebb2012ef7c39db5f7b3b50f2fb1212049418530`;
- diagnostic:
  `ae124fea75ead8f6d1e5e50cf090fb6db401ad5cdef6316f6851641f034205c7`;
- summary:
  `4f73542c73d90d5d36ae2eb811fe438eb3c3bb56e742c22cf6a0886ed17de3a6`.

### Current authorized gate

The stochastic Phase-1 family is complete.

Accepted stochastic execution:

- family command:
  `mamba2-m022-stochastic-family-20260927-0552`;
- mechanical assessment:
  `mamba2-m022-stochastic-assessment-20260927`;
- reviewed feature SHA:
  `db88bcc145754c50b6d7ad87a9ddef071ed2d9c5`;
- shortlist:
  - **14 / 7 / 7**;
  - **21 / 7 / 7** reference;
  - **28 / 7 / 7**.

28/7/7 improved net P/L and drawdown versus reference while retaining
**81.61%** of reference closed trades and passing all frozen breadth/
concentration checks. 14/7/7 remained Pareto-nondominated because of its
higher non-flat win rate. All other stochastic tuples were dominated.

The next authorized Phase-1 family is the frozen **M1 oversold/overbought
boundary** screen only:

- 15 / 85;
- 20 / 80 reference;
- 25 / 75.

The fixed Phase-1 reference remains stochastic 21/7/7, boundaries 20/80,
EMA7, no experimental spread gate, ATR 1.0x/2.0x, all hours. Do **not**
combine stochastic shortlist values with boundary variants yet; interactions
belong to Phase 2.

The boundary execution/assessment protocol is frozen in the M022 milestone
before outcomes:

- reuse accepted 20/80 reference-v3 evidence;
- deterministic A/B for 15/85 and 25/75;
- maximum two concurrent independent arms;
- development only;
- 70% reference trade-count floor;
- Pareto objectives: net P/L, max drawdown USD, non-flat win rate;
- same symbol/calendar/side breadth limits for improving arms.

After boundary-family evidence and its mechanical assessment are accepted,
continue to the next still-frozen Phase-1 family. Do not open validation or
historical holdout and do not use M021 outcomes.

## Start here

Read the durable handoff docs and the M022 milestone. Resume from the
boundary-family sync/run/assessment sequence above.

Do not start Phase 2, validation, historical holdout, M15 research, merge,
deployment, or live trading.
