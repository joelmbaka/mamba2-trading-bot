# Milestone 021 — Prospective Paper/Forward Validation

Status: **IN PROGRESS — PROTOCOL FROZEN, OUTCOMES NOT YET INSPECTED**

Protocol date: 2026-09-26

Branch:

`prospective-forward-validation`

Protocol base / accepted M020 docs HEAD:

`5bb586709399c903a5d351ab4159b5a65ac64b95`

Frozen executable implementation carried forward from M020:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

## Purpose

Test the M020-D candidate on genuinely later market data using a protocol fixed
before any post-cutoff economic outcomes are inspected.

This milestone is paper/backtest validation only. It does not authorize live
trading or production strategy promotion.

## Prospective cutoff and observation window

The accepted M019/M020 historical dataset ends at:

`2026-09-25T00:00:00Z`

Only genuinely later observations may contribute to M021 classification.

The prospective source-data window starts at:

`2026-09-25T00:00:00Z`

Because M1 bars are bar-open timestamps and become visible only after the bar
completes, the first eligible strategy decision is strictly after the accepted
historical cutoff. The earliest possible M1 decision boundary is:

`2026-09-25T00:01:00Z`

No strategy decision at or before `2026-09-25T00:00:00Z` may contribute to
M021 classification.

Primary observation window:

`[2026-09-25T00:00:00Z, 2026-10-23T00:00:00Z)`

This is four complete seven-day UTC periods.

## Minimum evidence rule

Do not classify the candidate before the primary four-week window is complete.

At the primary cutoff, classification additionally requires all of:

- at least **1,000** closed control trades;
- at least **900** closed M020-D candidate trades;
- at least **100** closed candidate trades for each of the five symbols;
- at least **300** closed candidate BUY trades;
- at least **300** closed candidate SELL trades.

If the four-week window is complete but any count threshold is unmet, extend
the window only in fixed seven-day increments:

- 5 weeks: `2026-10-30T00:00:00Z`
- 6 weeks: `2026-11-06T00:00:00Z`
- 7 weeks: `2026-11-13T00:00:00Z`
- 8 weeks: `2026-11-20T00:00:00Z`

The first cutoff that satisfies all count thresholds becomes the final M021
classification window.

Do not use P/L, drawdown, win rate, symbol performance, side performance, or
any other economic outcome to decide whether to extend the window.

If the count thresholds are still unmet at the eight-week cutoff, classify:

**INSUFFICIENT FOR CLASSIFICATION**

and close M021 without tuning the candidate.

## Frozen arms

### Control

Use the accepted M019 strategy behavior unchanged, through the accepted M020
replay/reporting implementation.

No M020 experimental entry filter is active.

### Candidate

Use exactly the independent M020-D rule:

- observe broker bid/ask at order-submission time;
- compute decision-time spread in points;
- reject a new order only when decision-time spread is **>10 points**;
- allow **<=10 points**.

The candidate may not inspect next-bar fill spread when deciding whether to
reject an order.

### Forbidden changes

Do not:

- stack M020-A;
- change the 10-point boundary;
- add symbol filters;
- add BUY/SELL filters;
- add UTC-session filters;
- change position size;
- change stochastic, EMA, RSI, trend, or higher-timeframe settings;
- change ATR, SL, TP, or trailing semantics;
- change replay timing or account-currency conversion;
- add a second execution treatment;
- tune from M021 results.

## Dataset isolation and provenance

Prospective market data must be exported/read-only and stored separately from
the accepted M019/M020 dataset.

For the final M021 window, record:

- exact UTC start and end;
- symbol set;
- row counts for M1 Bid, Ask M1, M5, and M15;
- source/manifest path;
- SHA-256 for the manifest;
- SHA-256 for every market-data artifact used by the replay;
- any missing-bar or missing-Ask diagnostics;
- exact Git implementation SHA;
- exact runtime versions.

Do not backfill the classification window with any observation at or before the
accepted M019/M020 cutoff.

## Determinism and regression gates

Before interpreting forward outcomes:

1. the ordinary historical control path must still reproduce the accepted M019
   baseline SHA-256 exactly:
   `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
2. the ordinary historical diagnostic path must still reproduce the accepted
   M019 diagnostic SHA-256 exactly:
   `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
3. if M021 requires executable code changes, the accepted M020-D historical
   treatment artifacts must also remain byte-identical:
   - baseline:
     `94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`;
   - diagnostic:
     `45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`;
   - evidence:
     `e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`.

For the final prospective window, run both control and candidate twice.

Require byte-identical A/B artifacts within each arm.

Record SHA-256 for at least:

- control baseline report;
- control diagnostic/evidence report;
- candidate baseline report;
- candidate diagnostic/evidence report;
- candidate spread-treatment evidence;
- prospective dataset manifest.

## Required economic reporting

For both control and candidate report:

- accepted orders;
- closed trades;
- wins;
- losses;
- flats;
- non-flat win rate;
- net realized P/L in USD;
- ending realized balance;
- unrealized P/L;
- ending equity;
- maximum equity drawdown in USD;
- maximum equity drawdown in percent;
- remaining open positions.

Report candidate minus control deltas for:

- net realized P/L;
- ending equity;
- maximum drawdown USD;
- maximum drawdown percent;
- trade count.

## Required stability reporting

Use fixed views only.

### Symbols

Report trade count and net P/L for:

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

### Sides

Report trade count and net P/L for:

- BUY
- SELL

### Calendar periods

Use fixed seven-day UTC buckets beginning at the prospective source-data start:

- period 1: Sep 25 00:00 -> Oct 2 00:00
- period 2: Oct 2 00:00 -> Oct 9 00:00
- period 3: Oct 9 00:00 -> Oct 16 00:00
- period 4: Oct 16 00:00 -> Oct 23 00:00

If the window is extended, append consecutive seven-day buckets without
changing earlier bucket boundaries.

Do not create outcome-driven subperiods.

## Spread-treatment enforcement

For the candidate record:

- total rejected order attempts;
- count of accepted entries with decision-time spread >10 points;
- maximum accepted decision-time spread;
- minimum rejected decision-time spread;
- count of treatment rejections at <=10 points;
- rejected attempts by symbol;
- rejected attempts by side;
- rejected attempts by fixed seven-day period.

Required boundary invariants:

- accepted entries with decision-time spread >10: **0**;
- treatment rejections at decision-time spread <=10: **0**;
- maximum accepted decision-time spread: **<=10 points**;
- minimum treatment-rejected decision-time spread: **>10 points**.

## Existing safety gates

Require:

- wrong-side initial TP violations: **0**;
- negative-P/L take-profit exits: **0**;
- new production/live strategy artifacts: **0**;
- real MT5 orders placed/modified/closed: **0**;
- M020-A stacked: **false**.

End-of-data remains non-liquidating. Any remaining position must be reported
rather than force-closed for convenience.

## Cost assumptions

Freeze the M021 cost label as:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`

Historical/prospective Bid/Ask spread is included through the accepted replay
semantics.

Commission per lot per side remains explicitly zero.

Adverse slippage remains explicitly zero.

Swap remains unmodeled.

Do not invent broker costs after seeing M021 outcomes. Therefore even a
positive M021 result is not evidence of profitability after unknown real
commission, slippage, and swap.

## Predeclared classification rule

Apply the following order.

### 1. INVALID

Classify **INVALID** if any of the following occurs:

- post-cutoff data provenance is not reproducible;
- deterministic A/B artifacts differ within an arm;
- accepted historical regression hashes change without an explicitly reviewed
  semantic milestone;
- a spread-boundary invariant fails;
- a trading-safety invariant fails;
- the frozen control/candidate definitions were changed after outcome
  inspection.

Do not interpret economic performance from an invalid run.

### 2. INSUFFICIENT FOR CLASSIFICATION

Classify **INSUFFICIENT FOR CLASSIFICATION** if the eight-week cap is reached
without all minimum evidence counts.

### 3. FORWARD-SUPPORTED

Classify **FORWARD-SUPPORTED** only if all of the following are true on the
final predeclared window:

- candidate net realized P/L is **> USD 0**;
- candidate net realized P/L is **greater than control**;
- candidate maximum equity drawdown in USD is **<= control**;
- candidate maximum equity drawdown percent is **<= control**;
- candidate-minus-control net P/L is **>= 0** in at least **4 of 5 symbols**;
- candidate-minus-control net P/L is **>= 0** for **both BUY and SELL**;
- candidate-minus-control net P/L is **>= 0** in at least **75%** of the fixed
  seven-day calendar periods, rounded up to the next whole period;
- all determinism, treatment-boundary, and safety gates pass.

This classification still does **not** authorize live trading.

### 4. NOT SUPPORTED

Classify **NOT SUPPORTED** if either:

- candidate net realized P/L is **<= control net realized P/L**; or
- both candidate drawdown USD and candidate drawdown percent are worse than
  control.

### 5. MIXED

Classify **MIXED** for every valid, sufficiently sized result that satisfies
neither FORWARD-SUPPORTED nor NOT SUPPORTED.

Examples include an aggregate improvement that remains loss-making, an
aggregate improvement with weaker cross-symbol/side/period stability, or an
aggregate improvement accompanied by one worsened drawdown measure.

## Interpretation boundary

M021 is one prospectively frozen forward window, not proof of durable live
profitability.

No M021 classification may be used to:

- change the >10-point threshold;
- optimize a second parameter;
- stack M020-A;
- enable real MT5 trading;
- bypass a later explicit review before any live-risk milestone.

## Protocol-freeze statement

This protocol is to be committed before post-`2026-09-25T00:00:00Z`
economic outcomes are inspected.

After the protocol commit exists, subsequent M021 work may implement only the
data-export, replay, deterministic-reporting, and local-control machinery needed
to execute this frozen protocol.


## Machinery implementation acceptance — 2026-09-26

The protocol above was frozen before this implementation work and before any
post-cutoff economic outcome was inspected.

Accepted M021 machinery implementation SHA:

`f53d38b93434eb52b19f0f12a441e4439822e39e`

Feature paths added/updated through that SHA:

- `docs/NEXT_TASK.md`
- `docs/milestones/021-prospective-forward-validation.md`
- `mamba2/backtest/m021_forward_validation.py`
- `tests/test_m021_forward_validation.py`

The accepted M020-D implementation itself was not modified.

Local-control M021 action implementation commit:

`e8d992595146c168d0efd83f20f342415557bcc6`

Validation:

- repository gate:
  `mamba2-m021-repo-checks-20260926-1103` — **PASS**, clean, divergence
  `0/0`;
- full native:
  `mamba2-m021-full-native-20260926-1104` —
  **206 passed, 2 skipped**;
- full Wine:
  `mamba2-m021-full-wine-20260926-1106` —
  **206 passed, 2 skipped**;
- historical byte-preservation:
  `mamba2-m021-historical-regression-20260926-1108` — **PASS**;
- readiness gate:
  `mamba2-m021-readiness-20260926-1127` — **PASS**;
- early primary export:
  `mamba2-m021-primary-export-refusal-20260926-1128` —
  **REFUSED AS REQUIRED**;
- early primary paired replay:
  `mamba2-m021-primary-pair-refusal-20260926-1129` —
  **REFUSED AS REQUIRED**.

Historical preservation reproduced all accepted bytes exactly:

- M019 control baseline:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- M019 control diagnostic:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- M020-D baseline:
  `94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`;
- M020-D diagnostic:
  `45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`;
- M020-D evidence:
  `e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`.

No new strategy artifact appeared during the historical regression.

At `2026-09-26T08:27:43Z`, the readiness gate reported:

- primary cutoff: `2026-10-23T00:00:00Z`;
- ready: **false**;
- economic results computed: **false**.

The actual local-control export action then returned:

- `ready=false`;
- `refused_before_cutoff=true`;
- `export_attempted=false`;
- `economic_results_computed=false`.

The actual local-control paired-replay action then returned:

- `ready=false`;
- `refused_before_cutoff=true`;
- `pair_attempted=false`;
- `economic_results_computed=false`.

Therefore the M021 execution machinery is accepted, but **M021 itself remains
open**. No prospective P/L, drawdown, symbol result, side result, period result,
or classification result has been inspected.

Current local-control-results evidence head after the refusal checks:

`63c885900bb63cf2a79f47cd731ff17d30c7facc`

The next authorized economic action is the frozen primary-window export only
after `2026-10-23T00:00:00Z`. If the predeclared count thresholds are not met,
the protocol's fixed seven-day extension schedule applies without looking at
economic outcomes to choose the extension.
