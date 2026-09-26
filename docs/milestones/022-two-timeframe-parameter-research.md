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

### Inventory evidence and mechanical protocol correction — 2026-09-26

The bounded history checkpoint search established synchronized Bid/Ask ticks plus native M5/M15 for all five symbols through **2025-08-25**. The next tested checkpoint, **2025-07-28**, failed common synchronized Bid/Ask tick coverage because EURJPY had no qualifying tick rows there. Therefore the conservative common candidate start remains **2025-08-25**.

A full tick-derived-M1 candidate export from 2025-08-25 through the frozen cutoff 2026-09-25 completed successfully, but it **failed the already-frozen accepted-M019 overlap rule**. The failure was specific to tick-derived **Bid M1**:

- EURJPY: maximum Bid OHLC delta **1 point**;
- EURUSD: maximum Bid OHLC delta **1 point**;
- GBPUSD: maximum Bid OHLC delta **5 points**;
- USDJPY: maximum Bid OHLC delta **2 points**;
- GBPJPY: exact Bid overlap.

In the same candidate:

- Ask M1 overlap was exact for all five symbols;
- Bid/Ask overlap indexes matched;
- native M5/M15 overlap frames were exact;
- no parameter/economic result was inspected.

The frozen 0.5-point tolerance is **not relaxed**.

The failure demonstrated a mechanical incompatibility between reconstructing historical Bid M1 from `COPY_TICKS_ALL` and the broker-native M1 bars used by the accepted M019 replay. Before parameter outcomes were inspected, M022 therefore exercised the protocol's allowed mechanical-impossibility correction.

The terminal history-capacity investigation found:

- MT5 `common.ini`: `MaxBars=100000`;
- original config backup SHA-256:
  `c04f195618eea41d7300a2459f0e9aa914967a90c534c449c6bbcf4fcebfbae0`;
- revised config: `MaxBars=500000`;
- revised config SHA-256:
  `22032bc12c27fbb642f9c151f3d2256a733d8ac442772c736dfe7149a9b0fc91`;
- runtime verification: `terminal_info().maxbars == 500000`;
- broker/account: `MetaQuotes-Demo`, USD;
- runtime: MT5 package 5.0.6180 / terminal build 6215 / Python 3.10.11;
- native M1 on 2025-08-25 was exposed for every symbol:
  - EURUSD 1,436 rows;
  - EURJPY 1,437 rows;
  - GBPUSD 1,437 rows;
  - GBPJPY 1,437 rows;
  - USDJPY 1,437 rows.

No real-order API was called, no economic replay ran, and no M021 post-cutoff data was used.

### Replacement inventory acceptance gate — frozen before parameter outcomes

The replacement candidate must preserve accepted replay semantics rather than substitute tick-derived Bid M1:

1. candidate range: conservative start **2025-08-25**, end-exclusive **2026-09-25T00:00:00Z**;
2. **Bid M1:** broker-native MT5 M1;
3. **Ask M1:** observable `COPY_TICKS_ALL` Ask aggregated/aligned to the native M1 index;
4. **M5/M15:** broker-native;
5. M15 remains compatibility/export data only and is never an M022 signal input.

Accepted-M019 overlap must satisfy, for every symbol:

- native Bid M1 overlap index identical to accepted M019;
- native Bid M1 overlap frame exactly identical;
- Ask M1 overlap index identical to accepted M019 and OHLC delta no more than **0.5 symbol point**;
- candidate Ask M1 has zero missing/extra rows versus candidate native Bid M1 over the accepted common replay range;
- native M5 and M15 overlap frames exactly identical;
- Ask manifest source remains `copy_ticks_range`;
- broker/server/account/runtime metadata are recorded;
- candidate manifest and file hashes are recorded.

This replacement gate is a source-parity correction only. It does not weaken the frozen price tolerance, inspect strategy performance, or change any parameter family.

Only after this gate passes may M022 declare the longest common trustworthy range and materialize the already-frozen 60% / 20% / 20% chronological development / validation / untouched-holdout split.

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

## History inventory accepted and partitions frozen — 2026-09-26

The replacement native-M1 candidate was recovered from the existing versioned
`v3` directory and passed full integrity plus the replacement M019 overlap gate.

Accepted candidate:

`backtest_data/m022-history-inventory-native-m1-v3/manifest.json`

Manifest SHA-256:

`143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558`

Accepted M019 manifest SHA-256:

`595efa4d65e35ae06c464edcc1a8dd4e410f6f7b73dfaf16081e0887346f440f`

Verified source/runtime:

- broker: `MetaQuotes-Demo`;
- account currency: USD;
- terminal build: 6215 / 25 Sep 2026;
- candidate requested range:
  `2025-08-25T00:00:00Z` to
  `2026-09-25T00:00:00Z` end-exclusive;
- common trading dates: **282**;
- common-trading-date-list SHA-256:
  `2efcd016d0d346036a33415e794903b5fea86ad610519fbda056ceb2c94feac5`.

For every one of EURUSD, EURJPY, GBPUSD, GBPJPY, and USDJPY:

- native Bid M1 accepted-M019 overlap index matched exactly;
- native Bid M1 accepted-M019 overlap frame matched exactly;
- Ask M1 accepted-M019 overlap index matched exactly;
- Ask M1 accepted-M019 OHLC delta was **0 points**;
- native M5 overlap frame matched exactly;
- native M15 overlap frame matched exactly;
- candidate Bid/Ask indexes matched with zero missing or extra Ask rows.

Approximate full candidate M1 row counts:

- EURUSD: 404,867;
- EURJPY: 405,196;
- GBPUSD: 404,959;
- GBPJPY: 405,094;
- USDJPY: 405,062.

The already-frozen chronological partition rule was then materialized without
running any strategy/economic replay.

### Frozen M022 partitions

**Development**

- start: `2025-08-25T00:00:00Z`;
- end-exclusive: `2026-04-21T00:00:00Z`;
- trading dates: **169**;
- first trading date: 2025-08-25;
- last trading date: 2026-04-20.

**Validation**

- start: `2026-04-21T00:00:00Z`;
- end-exclusive: `2026-07-08T00:00:00Z`;
- trading dates: **56**;
- first trading date: 2026-04-21;
- last trading date: 2026-07-07.

**Untouched historical holdout**

- start: `2026-07-08T00:00:00Z`;
- end-exclusive: `2026-09-25T00:00:00Z`;
- trading dates: **57**;
- first trading date: 2026-07-08;
- last trading date: 2026-09-24.

Each partition exceeds the predeclared minimum of 20 common trading dates.

Safety evidence for the inventory and partition freeze:

- no economic replay run;
- no parameter result inspected;
- no M021 post-cutoff data used;
- no real-order API called.

The history inventory gate is therefore **PASSED**. Phase 1 may now be
implemented and run **one parameter family at a time on development only**.
Validation remains unused until development screening has produced a frozen
shortlist. Historical holdout remains unopened until the Phase-1 shortlist,
Phase-2 matrix, and finalist acceptance criteria are frozen.

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

## Phase-1 mechanical replay-clock corrections — before accepted results

The first development reference attempt
(`mamba2-m022-phase1-reference-20260926-1708`, `reference-v1`) was
**not accepted**. It terminated with `AccountCurrencyConversionError` at
`2025-09-17T00:01:00Z` when a JPY-denominated exit required JPY→USD
conversion but USDJPY had no completed M1 bar on that exact portfolio
boundary.

This exposed a mechanical property of the accepted extended dataset:

- Bid/Ask M1 indexes are exact **within each symbol**;
- the five symbols do not share every individual M1 timestamp;
- the accepted broker intentionally requires same-boundary historical
  conversion and does not carry an older conversion quote forward.

The conversion rule is **not changed**. In particular M022 will not:

- forward-fill a missing USDJPY conversion bar;
- use a future conversion bar;
- weaken same-boundary conversion semantics;
- treat a failed or superseded partial run as parameter evidence.

An initial correction (`reference-v2`) physically intersected all symbol M1
rows. Before any `reference-v2` economics were inspected, review identified
that this would unnecessarily delete genuine per-symbol M1 bars from
stochastic/EMA/ATR history. `reference-v2` is therefore **superseded and
ineligible for acceptance regardless of whether its already-started local
process eventually exits successfully**.

The accepted correction for the next attempt (`reference-v3`) is instead a
**strict shared replay-boundary clock**:

1. Preserve every genuine per-symbol Bid/Ask M1 row inside the frozen
   development partition.
2. Preserve native M5/M15 histories unchanged.
3. For each interior replay boundary `T`, require every configured symbol to
   have both:
   - completed Bid/Ask M1 open at `T-1 minute`; and
   - execution Bid/Ask M1 open at `T`.
4. Retain the partition-close boundary when `T-1 minute` is common, so the
   final scored M1 bar can be processed without introducing an out-of-
   partition execution bar.
5. Keep the accepted same-boundary currency-conversion semantics unchanged.
6. Never forward-fill or synthesize an M1 price to create a boundary.

This design solves the conversion failure while keeping each symbol's full
causal indicator history intact.

Every accepted Phase-1 artifact must record:

- `strict_common_boundary_clock = true`;
- `full_symbol_m1_preserved = true`;
- exact replay-boundary count;
- first and last replay boundary;
- SHA-256 of the ordered replay-boundary timestamp list.

The failed `reference-v1` directory and superseded `reference-v2` directory
must not be overwritten. The next accepted reference attempt must use
`reference-v3`.

The accepted v3 source dataset begins at the development partition start, so
no pre-partition warm-up history exists inside the accepted artifact. Phase 1
therefore starts flat and allows indicators/ATR to become ready causally from
the partition's own bars. This rule is identical across all arms and is frozen
before successful economic results.

No validation data, historical holdout outcome, M021 prospective outcome,
`reference-v1` partial P/L, or `reference-v2` economics were inspected to
make these corrections.

## Frozen stochastic-family screening rubric — before results

Before inspecting any stochastic-family development result, the following
shortlist rubric is frozen for the nine predeclared tuples.

Mandatory gates for every arm:

- deterministic A/B hashes must match;
- TP/safety invariants must remain clean;
- development partition/hash must match the frozen M022 partition;
- validation and historical holdout must remain unopened;
- closed-trade count must be at least **70% of the reference arm** so an
  apparent improvement cannot come mainly from suppressing activity.

Among arms that pass those gates, shortlist construction is multi-objective,
not a single-score ranking:

1. compare **net realized P/L** (higher is better);
2. compare **maximum equity drawdown USD** (lower is better);
3. compare **non-flat win rate** (higher is better);
4. retain the **Pareto-nondominated** eligible tuples plus the reference tuple;
5. do not promote an isolated development spike directly to Phase 2.

Breadth / concentration checks for any arm whose net realized P/L improves
over reference:

- the positive P/L improvement must appear in at least **two symbols**;
- the positive P/L improvement must appear in at least **two fixed 4-hour UTC
  entry buckets**;
- no single symbol may contribute more than **70%** of the sum of positive
  symbol-level P/L deltas versus reference;
- no single BUY/SELL side may contribute more than **80%** of the sum of
  positive side-level P/L deltas versus reference.

An otherwise Pareto-eligible tuple that fails breadth is labeled
`FRAGILE / CONCENTRATED` and is not promoted to Phase 2 unless a neighboring
tuple later shows the same broad direction. This rule does not authorize new
neighboring runs after results are seen; any extra tuple still requires a
separately documented pre-run addition under the existing milestone rule.

No stochastic tuple is selected merely because it has the highest development
P/L. Validation remains closed while this stochastic shortlist is constructed.

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
