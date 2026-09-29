# Milestone 024 — Symbol Specialization Research

Status: **DIAGNOSTIC PROTOCOL FROZEN — NO FRESH SYMBOL-FILTERED ECONOMICS YET**

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
