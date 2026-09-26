# Milestone 022 — Two-Timeframe Parameter Research

Status: **IN PROGRESS — HISTORY INVENTORY GATE, NO PARAMETER RESULTS INSPECTED**

Protocol date: 2026-09-26

Branch: `strategy-parameter-research`

## Purpose

Systematically test the hand-selected parameters of the existing M5 + M1 strategy without changing its basic two-timeframe idea.

This milestone is independent of M021 prospective validation. M021 remains frozen on `prospective-forward-validation` and must not be modified, rebased, retuned, or interpreted early.

This milestone does **not** authorize live trading or production promotion.

## Fixed strategy structure

Keep:

- M5 as trading/direction timeframe;
- M1 as entry timeframe;
- M15/higher-TF filter disabled;
- trend filter disabled;
- RSI filter disabled;
- existing M1 stochastic setup and candle/EMA confirmation semantics;
- existing account-currency conversion and replay timing semantics;
- five symbols: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY;
- position size 0.1 for comparability.

Do not add a third timeframe in M022.

## First task — historical data inventory

Before parameter screening, determine the maximum trustworthy read-only MT5 history available for all five symbols for:

- M1 Bid;
- tick-derived/observable Ask M1 needed for spread-aware replay;
- M5;
- M15 only where existing replay/export compatibility requires it; M15 must not become a signal input.

Prefer a materially longer history than the already-inspected 2026-06-23 through 2026-09-25 dataset.

Record exact available UTC ranges, row counts, missing-data/Ask diagnostics, manifest/artifact hashes, broker/source metadata, and runtime versions.

Do not silently fabricate or forward-fill unavailable Ask history.

## Inventory implementation checkpoint — 2026-09-26

The M022 start gate was verified before local execution:

- starting branch: `strategy-parameter-research`;
- starting SHA: `253b6ee840e5489a2c5db27d064500bb44f93e1e`;
- Dell repository gate: clean worktree, local/remote divergence `0/0`, lock check passed;
- no M021 economic result was inspected or used.

Historical M019 evidence showed that broker-native M1 retention must not be treated as the same thing as total trustworthy market-data depth:

- chunked native M1 history reached only to approximately 2026-06-22;
- native M5/M15 history was already available from 2026-06-01;
- synchronized tick samples containing Bid/Ask were also available on 2026-06-01 and 2026-06-15 for all five symbols.

Therefore M022 must separately test whether an older M1 Bid/Ask stream can be truthfully reconstructed from the broker's own ticks. It must not fabricate or forward-fill missing minutes.

The feature branch now contains an **opt-in research/export mode** that reconstructs synchronized Bid and Ask M1 OHLC from the same `COPY_TICKS_ALL` stream while leaving the existing native-M1 export path unchanged by default. Broker-native M5/M15 remain unchanged. This infrastructure requires overlap validation against previously accepted native/tick-derived history before any older tick-derived M1 range can be declared trustworthy.

Local-control now contains fixed M022-only actions for:

- repository/branch gating;
- history-inventory cleanup;
- historical inventory;
- a bounded history-depth probe;
- a fixed tick-derived inventory export with accepted-M019 overlap proof.

The first inventory command was dispatched as:

`mamba2-m022-history-inventory-20260926-1217`

That first implementation attempted to discover the earliest Ask tick from a very old origin before exporting. It became a long-running read-only MT5 operation and **must not be repeated as the preferred discovery method**. Its published result, when available, is evidence only; do not infer history depth from runtime duration.

The replacement depth probe is bounded:

1. inspect retained native M1/M5/M15 depth with fixed `copy_rates_from_pos` limits;
2. compute the common native M5/M15 start;
3. probe synchronized Bid/Ask ticks only from that known common start;
4. report source/broker/runtime metadata;
5. run no strategy replay and compute no economic result.

### Next inventory acceptance gate

Before freezing M022 data partitions:

1. obtain/review the pending first-inventory result;
2. synchronize the Dell checkout to the latest feature SHA;
3. run the feature tests, including the opt-in tick-derived-M1 exporter tests;
4. run the bounded M022 depth probe;
5. if older tick coverage exists, export a fixed candidate history using:
   - tick-derived synchronized Bid/Ask M1;
   - broker-native M5/M15;
6. prove overlap against the accepted M019 dataset using the predeclared acceptance rule:
   - M1 Bid overlap indexes must be identical and OHLC must differ by no more than **0.5 symbol point**;
   - Ask M1 overlap indexes must be identical and OHLC must differ by no more than **0.5 symbol point**;
   - candidate Bid M1 and Ask M1 indexes must be identical with zero missing/extra Ask rows;
   - native M5/M15 overlap frames must remain exactly identical;
   - the M1 manifest source must identify `copy_ticks_range_bid_aggregation`;
7. only then declare a longest common trustworthy range and freeze development / validation / untouched historical-holdout partitions.

No Phase-1 parameter arm is authorized before that gate passes.

## Data separation

Before inspecting optimization results, predeclare chronological partitions.

Use the longest common trustworthy range. Keep at least three chronological roles when the available history permits:

1. **development** — parameter screening and combination search;
2. **validation** — rank/filter candidates chosen from development;
3. **historical holdout** — untouched until finalists and acceptance rules are frozen.

M021 prospective data is not an M022 tuning partition and remains isolated.

If trustworthy history is too short to support meaningful chronological separation, stop and document the limitation before broad optimization.

### Predeclared partition rule — frozen before history-depth result

The partitioning rule is fixed before inspecting the M022 history-depth result:

1. Start from the **longest common trustworthy range** that passes the frozen M019 overlap gate, capped end-exclusive at `2026-09-25T00:00:00Z`.
2. Build the ordered set of UTC trading dates represented in the accepted common M1/M5 data for all five symbols. Partition boundaries must fall at UTC day boundaries; do not choose boundaries after looking at parameter performance.
3. Assign whole trading dates chronologically:
   - **development:** first 60%;
   - **validation:** next 20%;
   - **historical holdout:** final 20%.
   Use floor rounding for the first two allocations and give any remainder to the holdout.
4. Require **at least 20 common trading dates in each partition**. If any partition would have fewer than 20, M022 broad optimization stops and the history limitation is documented instead of weakening the split after seeing results.
5. The historical holdout remains unopened for candidate selection until the Phase-1 shortlist, Phase-2 matrix, and finalist acceptance criteria are frozen.
6. Indicator warm-up may read immediately preceding historical bars needed to establish state at a partition boundary, but:
   - no order may be submitted before the scored partition start;
   - no position may be carried into the scored partition from warm-up;
   - warm-up trades/P&L do not exist and are not scored;
   - validation/holdout warm-up may use only prior **market-data state**, never prior partition outcome-based tuning.
7. M021 prospective observations remain outside all three M022 partitions.

This rule may be changed only for a demonstrated mechanical impossibility discovered before parameter results are inspected; any such change must be documented before the replacement split is executed.

## Parameter families — Phase 1 screening

The initial research grid is deliberately bounded.

### Stochastic

Current reference: 21 / 7 / 7.

Screen coherent tuples rather than every arbitrary K/D/slowing Cartesian product:

- 9 / 3 / 3
- 10 / 4 / 4
- 10 / 6 / 6
- 14 / 3 / 3
- 14 / 5 / 5
- 14 / 7 / 7
- 21 / 5 / 5
- 21 / 7 / 7
- 28 / 7 / 7

The executor may add a **small number** of neighboring tuples only when needed to test whether an observed region is smooth; additions must be documented before their results are inspected.

### M1 oversold / overbought boundaries

Test symmetric pairs:

- 15 / 85
- 20 / 80 — current reference
- 25 / 75

### EMA confirmation period

- 5
- 7 — current reference
- 9
- 12

### Decision-time maximum spread

Include:

- no experimental spread rejection;
- <= 5 points;
- <= 8 points;
- <= 10 points — M020-D reference;
- <= 12 points;
- <= 15 points.

Spread decisions must use only bid/ask observable at submission time. Never use future/fill spread to decide entry.

### ATR protection

SL multiplier:

- 0.75
- 1.00 — current reference
- 1.25
- 1.50

TP multiplier:

- 1.00
- 1.50
- 2.00 — current reference
- 2.50
- 3.00

Do not immediately test all SL x TP combinations. Screen the protection family first, then carry only stable regions into Phase 2.

### Session

Do not perform unrestricted hour-by-hour data mining.

Phase 1 may compare only:

- all hours;
- block 00:00–03:59 UTC (the previously documented M020-A hypothesis).

Any additional session window requires a separately documented hypothesis before its result is inspected.

### Trailing

Preserve existing directional trailing semantics during initial screening. Trailing variants are deferred until the entry/protection parameter families above have been screened, unless evidence shows trailing is the dominant unresolved mechanism.

## Phase 1 method

Change one parameter family at a time relative to a fixed documented reference configuration.

For every arm record at minimum:

- exact parameter set and experiment ID;
- dataset partition and artifact hashes;
- accepted/closed trades;
- wins/losses/flats and non-flat win rate;
- net realized P/L;
- ending balance/equity;
- maximum drawdown USD and percent;
- per-symbol trade count and P/L;
- BUY/SELL trade count and P/L;
- fixed calendar-bucket trade count and P/L;
- rejected-order counts where applicable;
- remaining positions;
- existing TP/safety invariants;
- deterministic A/B hashes.

Do not select an arm solely by highest P/L.

## Phase 2 — bounded combinations

Only parameter values/regions that show useful and reasonably stable Phase 1 behavior may enter Phase 2.

Before running Phase 2:

1. publish the shortlist;
2. publish the exact combination matrix;
3. cap the matrix to a manageable number of serious candidates;
4. state the selection criteria before results are inspected.

Prefer combinations that improve multiple dimensions without collapsing trade count or concentrating the benefit in one symbol, one side, or one short calendar period.

## Robustness / anti-overfit rules

A candidate is more credible when neighboring parameter values also behave reasonably. Treat isolated spikes as fragile.

Do not choose a candidate merely because it is the historical maximum.

Report concentration of improvement by symbol, side, and period.

Preserve an untouched historical holdout for finalists whenever data availability permits.

Do not use M021 prospective outcomes to tune M022.

## Cost contract

Historical comparisons must state exactly which costs are modeled.

At minimum preserve the existing truthful label where applicable:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`

Do not invent broker commission, slippage, or swap.

## Regression and safety

Before accepting research machinery:

- preserve accepted M019 historical hashes where the unchanged control path applies;
- preserve accepted M020-D artifacts where executable replay semantics overlap;
- keep MT5 historical/market-data access read-only;
- never place, modify, or close a real MT5 order from research/local-control actions;
- never alter M021 frozen protocol or its branch;
- never silently change production strategy behavior.

## Local-control workflow

Use permanent branches:

- `local-control`
- `local-control-results`

The Dell workstation service is:

`chatgpt-mamba2-local-agent.service`

Cloud review/execution should do everything possible through GitHub and existing/fixed local-control actions. Add narrowly allowlisted local-control actions only when a required Dell/MT5 operation cannot be performed in the cloud. No arbitrary-shell or real-order action is permitted.

Every local run must return enough evidence to identify:

- command/action ID;
- feature branch and exact SHA;
- clean/divergence state;
- runtime;
- dataset/manifest hashes;
- outputs and hashes;
- test totals;
- safety result.

## Immediate authorized work

The next executor may:

1. inspect the branch/docs and existing replay/export architecture;
2. document the historical-data inventory plan;
3. implement deterministic parameter overrides for experiment-only replay without changing production defaults;
4. implement bounded Phase 1 experiment definitions/reporting;
5. add synthetic/unit tests;
6. add narrowly fixed local-control actions required for history inventory/export and research runs;
7. use Dell read-only MT5 access to establish available historical depth;
8. predeclare chronological data partitions before parameter results are interpreted;
9. execute Phase 1 only after those gates are documented.

Do **not** start M15/three-timeframe research.

Do **not** merge to main.

Do **not** modify the frozen M021 branch.

Do **not** deploy or enable real trading.

## Handoff / documentation

Keep this milestone file authoritative for M022. Record material decisions and accepted evidence here as the work progresses.

A fresh session should read:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`
6. `docs/MILESTONES.md`
7. this file

before changing code or authorizing local runs.
