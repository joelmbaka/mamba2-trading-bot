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

The stochastic, boundary, EMA, and decision-time-spread Phase-1 families are
complete.

Accepted Phase-1 shortlists so far:

- stochastic:
  - **14 / 7 / 7**;
  - **21 / 7 / 7** reference;
  - **28 / 7 / 7**;
- boundary:
  - **20 / 80 reference only**;
- EMA:
  - **7 reference**;
  - **9**;
  - **12**;
- decision-time spread:
  - **none** — reference;
  - **<=12 points**.

Accepted spread execution:

- family command:
  `mamba2-m022-spread-family-20260927-1317`;
- mechanical assessment:
  `mamba2-m022-spread-assessment-20260927-1541`;
- reviewed feature SHA:
  `823a761c93d3f6df1162a5bb934190e461daf1de`.

Spread assessment details:

- <=5: **INELIGIBLE**, 54.37% activity;
- <=8: **INELIGIBLE**, 59.05% activity;
- <=10: **INELIGIBLE**, 67.87% activity;
- <=12: **SHORTLIST**, 72.93% activity, broad improvement across all five
  symbols, both sides, and all six UTC buckets;
- <=15: **DOMINATED**.

The next authorized Phase-1 family is **ATR-SL only**:

- **0.75x**;
- **1.00x** reference;
- **1.25x**;
- **1.50x**.

The fixed reference remains stochastic 21/7/7, boundaries 20/80, EMA7,
no experimental spread gate, ATR SL 1.0x / TP 2.0x, all hours.

The ATR-SL execution/assessment protocol is frozen in the M022 milestone
before outcomes:

- TP fixed at 2.0x;
- reuse accepted reference-v3 evidence;
- deterministic A/B for 0.75x, 1.25x, and 1.50x;
- maximum two concurrent independent non-reference arms;
- development only;
- 70% reference trade-count floor;
- Pareto objectives: net P/L, max drawdown USD, non-flat win rate;
- same symbol/calendar/side breadth limits for improving arms.

ATR-TP is not yet authorized. Do not combine Phase-1 candidates yet.

## Start here

Read the durable handoff docs and the M022 milestone. Resume from the
ATR-SL implementation/sync/run/assessment sequence above.

Do not start Phase 2, validation, historical holdout, M15 research, merge,
deployment, or live trading.
