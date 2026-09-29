# Milestone 024 — Symbol Specialization Research

Status: **DIAGNOSTIC ACCEPTED — STAGE 2 CAUSAL SYMBOL PROTOCOL FROZEN; NO STAGE-2 ECONOMICS YET**

Protocol date: 2026-09-29

Branch:

`symbol-specialization-research`

Branch point / final M023 closeout:

`ffd33e2ae0534d572c73840cccaa98104b3ad460`

M023 is closed. Its Stage-B result supported zero sessions and its historical
holdout remains sealed.

## Objective

Test whether the accepted M023 BUY-only research behavior contains a stable,
pair-specific structure that could justify a later prospectively frozen causal
symbol-selection experiment.

The primary question is:

**Can restricting the strategy to a stable, predeclared subset of currency
pairs produce strictly positive expectancy without relying on one short
historical period?**

The first M024 gate is descriptive/diagnostic only. It does not answer that
causal question and must not be described as a filtered-strategy backtest.

## Research anchor

Use only accepted M023 Stage-A D-B / BUY-only, all-hours evidence.

Exact strategy anchor:

- P2-08 parameters;
- stochastic: 21 / 7 / 7;
- stochastic boundaries: 20 / 80;
- EMA: 7;
- decision-time spread gate: none;
- ATR SL: 1.5;
- ATR TP: 3.0;
- direction: BUY only;
- all hours;
- M15 disabled;
- position size: 0.1;
- cost contract:
  `SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`.

Accepted Stage-A family result:

`04f8cb971ac56b06739aba594df1a2090745f396`

Accepted Stage-A assessment:

`ed01975c5ea7945d9890d807c58ff133e07a6aa1`

## Fixed seen-research sample

Use exactly:

`2025-08-25T00:00:00Z` → `2026-07-08T00:00:00Z`

Accepted trading dates:

**225**

Ordered date-list SHA-256:

`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`

Reuse the exact five 45-date chronological folds from M023. Do not redraw,
merge, or optimize folds.

Historical holdout remains sealed:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

M021 post-cutoff outcomes remain unavailable for M024 tuning.

## Frozen symbol hypotheses

Exactly four descriptive subsets exist in the first M024 gate:

| ID | Symbols |
|---|---|
| SYM-R | EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY |
| SYM-UJ | USDJPY |
| SYM-JPY | EURJPY, GBPJPY, USDJPY |
| SYM-NONJPY | EURUSD, GBPUSD |

No other subset may be added.

Do not enumerate the 31 non-empty subsets of five symbols.
Do not create a best-two, best-three, or post-result custom basket.
Do not change these groups after diagnostics are inspected.

## Hypothesis source

Accepted D-B full-sample per-symbol economics were:

| Symbol | Closed trades | Net P/L | Mean trade P/L |
|---|---:|---:|---:|
| EURJPY | 1,260 | -$1,826.74 | -$1.44979 |
| EURUSD | 1,318 | -$1,034.03 | -$0.78455 |
| GBPJPY | 1,222 | -$2,707.20 | -$2.21539 |
| GBPUSD | 1,495 | -$1,900.95 | -$1.27154 |
| USDJPY | 1,335 | **+$15.04** | **+$0.01127** |

USDJPY is therefore the only positive full-sample symbol in D-B.

This is only a hypothesis generator. USDJPY fold P/L was approximately:

- F1: -$125.95;
- F2: +$36.28;
- F3: +$58.70;
- F4: -$1.99;
- F5: +$48.00.

Thus positive aggregate USDJPY performance is not equivalent to uniform
chronological profitability and is not a production/live claim.

## Diagnostic-only calculations

Using existing deterministic D-B evidence only, calculate for each frozen
subset:

- closed trades;
- wins/losses/flats where source evidence permits;
- net realized P/L;
- mean trade P/L;
- median trade P/L where source evidence permits;
- share of D-B total activity;
- each of five chronological fold trade counts, net P/L, and mean trade P/L;
- count of positive-P/L folds;
- count of positive-mean folds;
- ISO-week trade count, net P/L, and mean P/L where source evidence permits;
- number/fraction of positive-P/L weeks;
- number/fraction of positive-mean weeks;
- maximum positive-fold concentration;
- symbol contribution inside multi-symbol subsets;
- exact source hashes and deterministic artifact hash.

For multi-symbol subsets, aggregate only the already-recorded trades/economics
belonging to those symbols.

## Critical causal limitation

Removing symbols from an existing all-five-symbol artifact is not a fresh
symbol-filtered strategy replay.

A true symbol-restricted strategy may change:

- portfolio occupancy;
- order eligibility;
- shared-account equity;
- later strategy state;
- timing of subsequent entries/exits;
- risk interactions.

Therefore the first-gate output must be labelled **DESCRIPTIVE SUBSET
ATTRIBUTION**, never causal symbol-filtered economics.

## Diagnostic interpretation rules

No subset is "supported" or "profitable strategy" at this gate.

The diagnostic may classify descriptive evidence only as:

- **REFERENCE** — SYM-R;
- **DESCRIPTIVELY PROMISING** — passes every frozen descriptive screen below;
- **DESCRIPTIVELY UNSUPPORTED** — otherwise.

A non-reference subset is DESCRIPTIVELY PROMISING only if:

1. aggregate net P/L > 0;
2. aggregate mean trade P/L > 0;
3. at least 3 of 5 folds have positive net P/L;
4. at least 3 of 5 folds have positive mean trade P/L;
5. no one positive fold contributes >60% of summed positive fold P/L;
6. at least 20 ISO weeks contain >=5 trades for the subset;
7. positive-mean weeks are at least 50% of those eligible weeks.

These gates are descriptive screening only. Passing them does not authorize
holdout or live risk.

## Next-stage rule

After the diagnostic is reviewed:

- if zero non-reference subsets are DESCRIPTIVELY PROMISING, stop M024;
- if one or more are DESCRIPTIVELY PROMISING, freeze a small causal replay
  family before any fresh economics;
- that later family may contain only SYM-R plus subsets already frozen above;
- no new symbol subset may be invented from the diagnostic result;
- fresh symbol-filtered economics require a new prospective protocol-freeze
  commit.

## Isolation from M025

M025 public FX benchmark research is independent.

M024 may not:

- use M025 economic outcomes to choose a symbol subset;
- change its frozen subsets based on public-benchmark performance;
- merge the two research families into one optimization.

Likewise M025's benchmark definitions must not be changed using M024 outcomes.

## Safety / hard boundaries

Never in the diagnostic gate:

- inspect/open M022/M023 historical holdout;
- inspect M021 post-cutoff outcomes;
- run fresh symbol-filtered strategy replay;
- add or remove a symbol hypothesis;
- revive SELL or BOTH as a candidate direction;
- add a session filter;
- add a weekday filter;
- add M15;
- alter production strategy defaults;
- merge to main;
- deploy;
- enable/place/modify/close real MT5 orders;
- expose arbitrary shell execution.

## Authorized implementation sequence

1. implement a pure read-only analyzer for the exact accepted D-B evidence;
2. verify accepted D-B source hashes/metadata before analysis;
3. add exact tests for the four frozen subsets and aggregation semantics;
4. test deterministic output and no unexpected symbol;
5. add only a fixed local-control diagnostic test/action if Dell access is
   genuinely required;
6. run no economic replay;
7. publish deterministic diagnostic evidence;
8. review and mechanically apply the frozen descriptive screens;
9. durably record the diagnostic result;
10. stop before any causal symbol-filtered replay.


## Implementation checkpoint — 2026-09-29

Protocol-freeze commit:

`12c8b93af164f24a719fa6151efb54f838659619`

Read-only analyzer implementation commit:

`2a605aebee379e50df7193f9562b84bbb2edb128`

Implemented files:

- `mamba2/backtest/m024_symbol_specialization.py`;
- `tests/test_m024_symbol_specialization.py`.

The analyzer is deliberately unable to replay the strategy. It reads only:

- `backtest_data/m023-stage-a-direction-v1/D-B/M023-A-D-B-a-summary.json`;
- `backtest_data/m023-stage-a-direction-v1/D-B/M023-A-D-B-b-summary.json`.

Both source summaries must match the accepted SHA-256:

`7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c`

It also revalidates the frozen M023 D-B metadata, exact 225-date partition,
BUY-only invariant, TP safety, holdout isolation, M021 isolation, and absence
of session/weekday filters before producing any M024 attribution.

Fixed local-control support was added on `local-control` at:

`b0acf22ff8271a96f926dd9250b85418034053c4`

New allowlisted actions:

- `m024_symbol_specialization_tests`;
- `m024_symbol_specialization_diagnostic`.

The diagnostic action builds A/B artifacts under:

`backtest_data/m024-symbol-specialization-v1/`

and requires byte-identical SHA-256 output before publishing a result.

### Recovery state at this checkpoint

A branch-switch command has been published:

`mamba2-m024-switch-symbol-specialization-v1`

No M024 diagnostic result has yet been accepted at the time of this checkpoint.

No M024 economic replay has run.

If resuming from a fresh chat:

1. read `AGENTS.md`, `docs/CURRENT_STATE.md`,
   `docs/NEXT_TASK.md`, and this milestone file;
2. inspect `local-control-results` for the branch-switch result;
3. sync Dell to the exact current `symbol-specialization-research` HEAD if
   needed;
4. run `m024_symbol_specialization_tests`;
5. if focused tests pass, run `m024_symbol_specialization_diagnostic`;
6. independently review the published subset classifications and artifact hash;
7. run full native regression before closing the diagnostic gate;
8. durably document the accepted result before authorizing any causal replay.

Do not skip directly to fresh symbol-filtered economics.


## Accepted diagnostic result — 2026-09-29

Focused native-test result commit:

`7bed8ad0173916f61b488c2d1ffe3742f9051446`

Focused result:

- **7 passed / 0 failed**;
- exact feature SHA:
  `f403124a31464f6b42768f6a1d985abe290cbc4c`;
- economic replay: **no**;
- historical holdout access: **no**;
- M021 post-cutoff use: **no**;
- M025 outcome use: **no**;
- real-order API: **no**.

Deterministic diagnostic result commit:

`0473b8f149a15516c6d7b4e2f1b0585482be7eef`

Accepted deterministic artifact pair:

- `backtest_data/m024-symbol-specialization-v1/m024-symbol-specialization-a.json`;
- `backtest_data/m024-symbol-specialization-v1/m024-symbol-specialization-b.json`.

Both artifact SHA-256:

`108752dfdb7430efb2c3b4b971d16d6affb1c43e2aacc1bc5ef8e276db2d6410`

Internal canonical report SHA-256:

`335fd223b503b4c19b34bf923658a9bb8615be9c590001466b71acd7a3945c4f`

Accepted source-summary SHA-256:

`7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c`

Full native regression result commit:

`1bed8eb23b6bca980d076dbf9173f6479f53239d`

Full native result:

**283 passed / 2 skipped**

### Frozen-subset classifications

| ID | Symbols | Closed trades | Net P/L | Mean/trade | Positive folds | Positive-mean weeks |
|---|---|---:|---:|---:|---:|---:|
| SYM-R | all five | 6,630 | -$7,453.88 | -$1.12427 | 0/5 | 5/46 |
| SYM-UJ | USDJPY | 1,335 | **+$15.04** | **+$0.01127** | **3/5** | **23/46 (50.0%)** |
| SYM-JPY | EURJPY + GBPJPY + USDJPY | 3,817 | -$4,518.89 | -$1.18389 | 0/5 | 8/46 |
| SYM-NONJPY | EURUSD + GBPUSD | 2,813 | -$2,934.99 | -$1.04336 | 0/5 | 8/46 |

Mechanical classification:

- **SYM-R — REFERENCE**
- **SYM-UJ — DESCRIPTIVELY PROMISING**
- **SYM-JPY — DESCRIPTIVELY UNSUPPORTED**
- **SYM-NONJPY — DESCRIPTIVELY UNSUPPORTED**

SYM-UJ passed all prospectively frozen descriptive screens:

- aggregate net P/L > 0;
- aggregate mean trade P/L > 0;
- positive net P/L in 3/5 folds;
- positive mean trade P/L in 3/5 folds;
- maximum positive-fold P/L share:
  **41.05198% <= 60%**;
- eligible ISO weeks: **46 >= 20**;
- positive-mean eligible weeks:
  **23/46 = 50.0%**.

Exact SYM-UJ fold economics:

| Fold | Closed trades | Net P/L | Mean/trade |
|---|---:|---:|---:|
| F1 | 284 | -$125.95 | -$0.44348 |
| F2 | 282 | +$36.28 | +$0.12867 |
| F3 | 296 | +$58.70 | +$0.19830 |
| F4 | 261 | -$1.99 | -$0.00762 |
| F5 | 212 | +$48.00 | +$0.22642 |

The accepted analyzer output matched an independent reviewer-side
recalculation from the published M023 Stage-A family result.

### Interpretation boundary

SYM-UJ is **not yet a proven USDJPY-only strategy**.

It passed a descriptive attribution screen over already-seen research evidence.
Its total edge is small and two of five folds remain negative. The result only
authorizes a separately frozen causal symbol-filtered replay stage.

No historical holdout is authorized by this diagnostic result.


## Stage 2 protocol freeze — causal USDJPY specialization

Status: **FROZEN BEFORE STAGE-2 ECONOMICS**

Exactly two causal arms exist:

| ID | Strategy symbols | Market-data universe |
|---|---|---|
| C-R | EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY | all five |
| C-UJ | USDJPY only | all five |

No other symbol subset may be added.

### Strategy anchor

Both arms use the exact accepted M023 D-B strategy settings:

- P2-08 parameters;
- stochastic: 21 / 7 / 7;
- boundaries: 20 / 80;
- EMA: 7;
- decision-time spread gate: none;
- ATR SL: 1.5;
- ATR TP: 3.0;
- direction: BUY only;
- all hours;
- M15 disabled;
- position size: 0.1;
- unchanged trailing/protection semantics;
- unchanged conversion semantics;
- cost contract:
  `SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`.

### Exact causal symbol semantics

C-R must instantiate and evaluate all five strategies exactly as accepted D-B.

C-UJ must:

- retain all five symbols' historical market-data streams;
- retain the exact common replay-boundary clock;
- retain all five symbols as available account-currency conversion data;
- instantiate/evaluate **only USDJPY** for strategy entries;
- create no strategy orders for EURUSD, EURJPY, GBPUSD, or GBPJPY;
- preserve all USDJPY open-position management outside entry evaluation;
- preserve fixed 0.1-lot size and all broker/account semantics.

Do not implement C-UJ by deleting non-USDJPY market data.

### Exact Stage-2 seen-research partition

Use exactly:

`2025-08-25T00:00:00Z` → `2026-07-08T00:00:00Z`

Accepted trading dates:

**225**

Date-list SHA-256:

`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`

Reuse the existing five 45-date folds unchanged.

Historical holdout remains sealed:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

### C-R reference-equivalence gate

C-R must reproduce accepted M023 D-B exactly for at least:

- closed trades;
- net realized P/L;
- mean trade P/L;
- non-flat win rate;
- maximum equity drawdown;
- per-symbol economics;
- five-fold economics;
- ISO-week economics;
- TP safety;
- exact partition/source/replay hashes.

If C-R reference equivalence fails, stop before interpreting C-UJ.

### Mandatory C-UJ gates

C-UJ must pass all of:

1. deterministic A/B baseline hash equality;
2. deterministic A/B diagnostic hash equality;
3. deterministic A/B summary hash equality;
4. exact P2-08 parameters;
5. BUY only;
6. zero accepted SELL entries;
7. strategy-entry universe exactly USDJPY;
8. market-data universe still all five symbols;
9. exact 225-date partition and date-list hash;
10. strict common replay-boundary clock unchanged;
11. source manifest unchanged;
12. M15 disabled;
13. session filter absent;
14. weekday filter absent;
15. wrong-side initial TP = 0;
16. negative-P/L TP exits = 0;
17. historical holdout untouched;
18. M021 post-cutoff outcomes unused;
19. M025 outcomes unused;
20. no real-order API.

### C-UJ representation gate

Relative to the accepted descriptive SYM-UJ evidence, require:

1. causal closed trades >= **80%** of 1,335;
2. every fold causal closed trades >= **70%** of that fold's descriptive
   USDJPY trade count;
3. causal trades occur in >= **80%** of the 46 descriptive USDJPY trade weeks.

These are representation checks only and may not be lowered after economics.

### C-UJ support rule

C-UJ is **SUPPORTED FOR HOLDOUT CHECKPOINT ONLY** if every condition holds:

1. mandatory gates pass;
2. representation gate passes;
3. net realized P/L > 0;
4. mean closed-trade P/L > 0;
5. positive net P/L in at least **3 of 5** folds;
6. positive mean trade P/L in at least **3 of 5** folds;
7. no one positive fold contributes more than **60%** of summed positive
   fold P/L;
8. at least **30** ISO weeks are eligible, where an eligible week contains at
   least 5 C-UJ closed trades;
9. at least **50%** of eligible ISO weeks have positive mean trade P/L.

Also report, but do not use as post-result substitute gates:

- win rate;
- maximum drawdown USD/%;
- C-UJ versus descriptive SYM-UJ trade-count/economic parity;
- exact entry/exit/trade evidence differences where available.

### Stage-2 classification and stop rule

- C-R: **REFERENCE**.
- Mandatory/reference failure: **INELIGIBLE**.
- Eligible C-UJ failing any support rule: **NOT SUPPORTED**.
- C-UJ passing every support rule:
  **SUPPORTED FOR HOLDOUT CHECKPOINT ONLY**.

If C-UJ is NOT SUPPORTED:

- close M024;
- do not open historical holdout.

If C-UJ is SUPPORTED:

- durably record the exact fixed USDJPY-only strategy and Stage-2 evidence;
- stop;
- do **not** immediately open historical holdout;
- a separate prospective holdout protocol/acceptance checkpoint is required.

### Stage-2 implementation sequence

1. implement experiment-only causal strategy-symbol selection;
2. production defaults remain all five symbols and unchanged;
3. add tests for exact C-R/C-UJ symbol universes and all-five data retention;
4. add tests proving non-USDJPY strategies cannot submit C-UJ entries;
5. add exact partition/holdout-refusal and deterministic-reporting tests;
6. expose only fixed local-control Stage-2 family and assessment actions;
7. run focused native tests;
8. sync Dell to exact feature SHA;
9. run C-R first and require D-B reference equivalence;
10. only then run C-UJ;
11. run the frozen mechanical Stage-2 assessment;
12. run full native regression;
13. durably record result;
14. stop before historical holdout.

### Hard boundaries

Do not:

- add another currency pair/subset;
- add a session or weekday filter;
- change BUY-only direction;
- change P2-08 parameters;
- add M15;
- use M020-D spread filtering;
- inspect/open historical holdout;
- inspect M021 post-cutoff outcomes;
- use M025 outcomes for tuning;
- alter production defaults;
- merge/deploy;
- enable/place/modify/close real MT5 orders.


## Stage-2 implementation checkpoint — 2026-09-29

Causal runner implementation:

`d0dff1fc66e6bc1b60200a4aeaa27990bd1322fc`

Invariant-hardening repair:

`ea49b23f72b0e857538c77a6f469920248cfde6a`

Implemented feature files:

- `mamba2/backtest/m024_symbol_causal_research.py`;
- `tests/test_m024_symbol_causal_research.py`.

The implementation preserves all-five market data and conversion streams for
both arms. C-UJ changes only the strategy-instantiation universe to USDJPY.

Fixed local-control Stage-2 support:

`0226b4e807480ed7e754c362d72e0adf05d5f25d`

Allowlisted Stage-2 actions:

- `m024_stage2_symbol_tests`;
- `m024_stage2_symbol_family`;
- `m024_stage2_symbol_assessment`.

No M024 historical-holdout action exists.

### Recovery state

A Dell sync to the current `symbol-specialization-research` branch has been
queued. No Stage-2 focused-test result, Stage-2 family economics, or Stage-2
assessment result is accepted at this checkpoint.

If resuming:

1. verify Dell is clean and exactly matches the current remote feature HEAD;
2. run `m024_stage2_symbol_tests`;
3. require PASS before economic replay;
4. run `m024_stage2_symbol_family`;
5. require C-R exact accepted D-B equivalence before reading C-UJ;
6. run `m024_stage2_symbol_assessment`;
7. run full native regression;
8. durably document the final Stage-2 classification;
9. stop before historical holdout even if C-UJ is supported.
