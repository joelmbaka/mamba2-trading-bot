# Milestone 020 — Controlled Experiments

Status: **IN PROGRESS**

Date started: 2026-09-25

Accepted M019 closeout base:

`927d90c656b6846603d338987bf67e6928499966`

Accepted M019 implementation SHA:

`94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`

Branch:

`backtest-controlled-experiments`

## Purpose

Test one explicitly stated hypothesis at a time against the accepted M019
control without turning the broader historical dataset into an unconstrained
parameter search.

No strategy behavior may change until an experiment definition is documented.

## Immutable control

The control is the accepted M019 strategy and replay semantics unchanged.

Required control artifacts:

- baseline SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`
- diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`

The experiment harness must reproduce the accepted control before treatment
results are interpreted.

## M020-A — first authorized experiment

### Hypothesis

New entries during `00:00–03:59 UTC` are a persistently harmful exposure.

This hypothesis is justified for testing because:

- the fixed bucket was negative in the accepted Sep-only evidence;
- the broader M019 bucket contains 842 trades and
  **USD -839.9216322911675** net realized P/L;
- its mean entry spread is **19.899049881235154 points**, much wider than the
  other fixed UTC buckets;
- the relationship can still be confounded by spread tails, symbol mix, and
  market regime.

The observation is not yet an accepted strategy change.

### Control

Accepted M019 strategy unchanged.

### Treatment

Change exactly one behavior:

- suppress **new entries** when the entry decision/fill time is
  `00:00:00 <= UTC time < 04:00:00`.

Positions already open before or during the blocked interval continue through
the unchanged position-management path.

### Must remain constant

- immutable M019 dataset;
- five symbols;
- replay timing and execution semantics;
- tick-derived historical Ask;
- account-currency conversion;
- position size 0.1;
- stochastic 21 / 7 / 7;
- trend/RSI/higher-TF flags;
- EMA 7;
- ATR 14 M5;
- SL 1 × ATR;
- TP 2 × ATR;
- M018 wrong-side initial-TP guard;
- trailing semantics;
- end-of-data behavior;
- explicit cost assumptions.

Do not add a spread threshold, symbol filter, side filter, or second strategy
change to M020-A.

## Experiment framework design

The framework must produce deterministic paired control/treatment evidence.

For each experiment:

1. identify an immutable experiment ID and exact hypothesis;
2. run the accepted control without strategy mutation;
3. run one treatment;
4. repeat each arm and require deterministic artifacts;
5. verify the control matches the accepted M019 hashes;
6. record treatment artifact hashes;
7. compare aggregate result and maximum drawdown;
8. compare per-symbol result and trade count;
9. compare BUY/SELL behavior;
10. compare late-June, July, August, and Sep 1–24 behavior;
11. report win/loss payoff and exit reasons;
12. report spread exposure and any changed trade population;
13. record whether the observed treatment effect is concentrated in one symbol
    or one subperiod;
14. document the experiment even when it is rejected or inconclusive.

## Overfitting rule

No result is accepted merely because aggregate P/L improves.

The existing June–September dataset has already been inspected in M019, so its
calendar slices are stability checks rather than pristine holdouts. Do not tune
on one slice and call another already-inspected slice independent validation.

A later milestone must use genuinely later paper/forward evidence before an
experimental strategy change is promoted toward live risk.

## Safety

Historical MT5 access remains read-only.

Never:

- enable real MT5 trading;
- place a real order;
- modify a real order;
- close a real position;
- invent commission, slippage, or swap;
- change accepted replay semantics silently;
- stack multiple strategy treatments into one experiment.

## M020-A implementation and validation

Implementation HEAD:

`3958b607ab12bf232c741fe520328b72dd9a23f2`

Implementation components:

- deterministic control/treatment harness in `mamba2/backtest/experiments.py`;
- experiment-only `UtcEntrySessionFilterStrategy`;
- diagnostic strategy transform hook that leaves normal callers unchanged;
- exact unit coverage for the 00:00–03:59 UTC boundary and wrapper isolation;
- permanent local-control actions for the immutable control pair and M020-A
  treatment pair.

Pre-treatment validation:

- native suite: **184 passed, 2 skipped**;
- Wine suite: **184 passed, 2 skipped**;
- treatment-code control regression reproduced the accepted M019 baseline hash
  exactly:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- treatment-code control regression reproduced the accepted M019 diagnostic
  hash exactly:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`.

Real-data treatment command:

`mamba2-m020a-treatment-pair-20260926-0603`

Completed:

`2026-09-26T03:26:37.880631+00:00`

Treatment determinism:

- baseline A/B identical: **PASS**;
- treatment baseline SHA-256:
  `65e3fe214e8e923175144dc9749c3fef521da964a796286805ebed745df42658`;
- diagnostic A/B identical: **PASS**;
- treatment diagnostic SHA-256:
  `c18c9fdda3fa9cb69cfd90f507d217897875248e5f8d745aa49cafe73925157e`;
- blocked-entry count in 00:00–03:59 UTC: **0**;
- blocked evaluation boundaries A/B: **80,747 / 80,747**;
- wrong-side initial-TP violations: **0**;
- negative-P/L take-profit exits: **0**;
- new strategy artifacts: **0**;
- remaining open positions: **0**.

### M020-A control vs treatment

| Metric | Control | M020-A treatment | Delta |
|---|---:|---:|---:|
| Closed trades | 4,922 | 4,104 | -818 |
| Wins | 1,899 | 1,642 | -257 |
| Losses | 3,020 | 2,459 | -561 |
| Flats | 3 | 3 | 0 |
| Non-flat win rate | 38.6054% | 40.0390% | +1.4336 pp |
| Net realized P/L | USD -1,716.6076 | USD -933.4296 | **USD +783.1780** |
| Ending equity | USD 8,283.3924 | USD 9,066.5704 | **USD +783.1780** |
| Maximum equity drawdown | USD 1,929.6970 | USD 1,271.3308 | **USD -658.3661** |
| Maximum drawdown % | 19.2148% | 12.6592% | **-6.5556 pp** |

Relative to control, the treatment reduced the historical net loss by about
**45.62%**, reduced maximum equity drawdown by about **34.12%**, and reduced
trade count by about **16.62%**.

The treatment remains loss-making. This is not profitability evidence.

### Stability by calendar entry period

Every inspected calendar period improved relative to the immutable control:

| Entry period | Control P/L | Treatment P/L | Delta |
|---|---:|---:|---:|
| Jun 23–30 | USD -170.1225 | USD -31.1150 | **USD +139.0075** |
| July | USD -637.4844 | USD -243.2565 | **USD +394.2279** |
| August | USD -674.9506 | USD -541.1094 | **USD +133.8413** |
| Sep 1–24 | USD -234.0501 | USD -117.9487 | **USD +116.1014** |

These slices were already inspected in M019 and are stability checks, not
independent holdouts.

### Stability by symbol

Every symbol improved relative to control:

| Symbol | Control P/L | Treatment P/L | Delta |
|---|---:|---:|---:|
| EURJPY | USD +113.6933 | USD +262.5154 | **USD +148.8220** |
| EURUSD | USD -301.5929 | USD -223.4500 | **USD +78.1429** |
| GBPJPY | USD -930.0207 | USD -509.6719 | **USD +420.3487** |
| GBPUSD | USD -423.3857 | USD -292.1857 | **USD +131.2000** |
| USDJPY | USD -175.3017 | USD -170.6373 | **USD +4.6644** |

The effect is strongest in GBPJPY but is not exclusive to GBPJPY. USDJPY shows
only a small improvement and remains effectively weak evidence for a universal
symbol-independent effect.

### Stability by side

Both sides improved:

| Side | Control P/L | Treatment P/L | Delta |
|---|---:|---:|---:|
| BUY | USD -762.8501 | USD -351.9240 | **USD +410.9261** |
| SELL | USD -953.7575 | USD -581.5056 | **USD +372.2519** |

The treatment does not justify a BUY-only or SELL-only rule.

### Remaining weakness

The treatment still produced:

- net realized P/L: **USD -933.4296206208546**;
- maximum drawdown: **USD 1,271.330847985335 / 12.659175316162072%**;
- four negative symbols out of five;
- all four calendar entry periods still negative;
- August alone at **USD -541.1093680009491**.

M020-A therefore does not establish a profitable strategy.

### M020-A classification

**PROMISING, NOT PROMOTED**

The treatment effect is materially better than control and is directionally
consistent across all four inspected calendar periods, all five symbols, and
both BUY and SELL. That is stronger than an aggregate-only improvement.

However:

- the same June–September dataset was used to discover and test the hypothesis;
- the 00:00–03:59 UTC bucket also had unusually high spread exposure;
- removing the session sharply reduces the remaining spread tails;
- treatment remains materially loss-making.

M020-A is therefore a candidate for later genuinely forward/paper validation,
not a live strategy change.

## M020-B — authorized diagnostic before another treatment

### Question

Is M020-A's improvement primarily associated with the UTC session itself, or
with the unusually wide entry spreads concentrated inside that session?

### Scope

M020-B is **diagnostic only**. It must not change strategy behavior.

Using the immutable M019 control artifacts and the deterministic M020-A
treatment artifacts, report the harmful-session population in fixed,
predeclared descriptive views:

1. entry-spread distribution and quantiles for 00:00–03:59 UTC;
2. P/L, wins, losses, and trade count by spread quantile within that session;
3. the same breakdown by symbol, BUY/SELL, and calendar entry period;
4. compare blocked-session spread bands with the same spread bands outside the
   blocked session where sample size permits;
5. identify whether the observed loss is concentrated in extreme spread tails
   or persists at ordinary spread levels;
6. do not introduce a spread threshold or optimize a cutoff.

The diagnostic may motivate a later single-variable spread experiment, but any
such threshold must be documented before implementation and must not be stacked
with the M020-A session filter.

M020 remains **IN PROGRESS** until this confound diagnosis is recorded.


## M020-B result — spread confound diagnosis

Validation:

- native suite: **188 passed, 2 skipped**;
- Wine suite: **188 passed, 2 skipped**;
- Wine Python: **3.10.11 AMD64**;
- Wine NumPy: **2.2.1**;
- Wine MetaTrader5: **5.0.6180**;
- command:
  `mamba2-m020b-spread-diagnostic-20260926-0646`;
- source control diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- output A/B byte-identical: **PASS**;
- output SHA-256:
  `8b57c2e8bbb4313e3d4e4aef758290a81d140ddd1797759944ab573f9b893a67`;
- strategy behavior changed: **false**.

Blocked-session population:

- 842 trades;
- 260 wins / 582 losses;
- net P/L: **USD -839.9216322911675**;
- mean spread: **19.899049881235154 points**;
- median spread: **4 points**;
- p75: **13 points**;
- p90: **77 points**;
- p95: **111 points**;
- maximum: **300 points**.

Fixed predeclared spread bands inside 00:00–03:59 UTC:

| Entry spread | Trades | Net P/L |
|---|---:|---:|
| <=2 | 295 | **USD +68.8293** |
| >2–5 | 195 | **USD +73.0221** |
| >5–10 | 94 | USD -70.8953 |
| >10–20 | 120 | USD -157.1550 |
| >20–50 | 28 | USD -64.8227 |
| >50–100 | 56 | USD -262.9088 |
| >100 | 54 | USD -425.9911 |

Rollups:

- <=5 points: 490 trades, **USD +141.85132131550108**;
- <=10 points: 584 trades, **USD +70.95600171225706**;
- >10 points: 258 trades, **USD -910.8776340034257**;
- >50 points: 110 trades, **USD -688.899959351615**.

Both sides show the same qualitative split:

- BUY <=5: **USD +45.9464**;
- SELL <=5: **USD +95.9049**;
- BUY >10: **USD -447.5654**;
- SELL >10: **USD -463.3122**.

The >10-point population was negative in every calendar period:

- Jun 23–30: **USD -113.2399**;
- July: **USD -407.4745**;
- August: **USD -180.5966**;
- Sep 1–24: **USD -209.5667**.

It was also negative for all five symbols.

Outside 00:00–03:59 UTC, spreads were much smaller:

- 4,080 trades;
- mean spread: **2.9166666666666665 points**;
- p95: **10 points**;
- maximum: **70 points**.

The outside-session >10-point bands were also negative where observations
existed.

### M020-B interpretation

The evidence does **not** support treating 00:00–03:59 UTC itself as the main
harmful mechanism.

Within that session, the <=5-point population was profitable overall, while the
loss was dominated by wider spreads, especially >10 and >50 points. Therefore
M020-A's time filter discards a meaningful population of low-spread trades that
was not harmful in aggregate.

This makes spread exposure a stronger causal candidate than clock time.

However, M020-B measures **fill-time entry spread**. In the accepted replay an
order is submitted from currently visible data and fills on the next M1
execution bar. The next-bar fill spread is not available at the decision
instant and cannot be used directly as a causal live filter without look-ahead.

M020-B therefore does **not** authorize a spread threshold yet.

## M020-C — authorized decision-time spread observability audit

### Question

Does the spread observable when the strategy submits an order show the same
harmful relationship as the next-bar fill spread diagnosed in M020-B?

### Scope

M020-C is diagnostic only.

It must record, without changing execution:

- order-submission UTC timestamp;
- decision-time bid and ask available through the broker at that instant;
- decision-time spread points;
- eventual fill-time spread points;
- resulting trade outcome and net P/L.

Then report:

1. decision-time spread distribution and fixed predeclared bands;
2. correlation/transition between decision-time and fill-time spread bands;
3. P/L by decision-time spread band;
4. the same by symbol, side, and calendar period;
5. whether a fixed decision-time spread boundary has sufficiently stable
   evidence to justify one later single-variable treatment.

Do not filter or reject any order during M020-C.

The accepted M019 baseline and diagnostic hashes must remain exactly unchanged
on the ordinary control path.


## M020-C result — decision-time spread observability

Validation:

- native suite: **191 passed, 2 skipped**;
- Wine suite: **191 passed, 2 skipped**;
- command:
  `mamba2-m020c-decision-spread-pair-20260926-0702`;
- accepted M019 baseline SHA-256 reproduced A/B exactly:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- accepted M019 diagnostic SHA-256 reproduced A/B exactly:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- decision-spread A/B byte-identical: **PASS**;
- decision-spread SHA-256:
  `0bb6e878eacfce9982cba23b05e8c4c4e437731554fe8b5f913125429b8f6a4f`;
- decision-spread rows: **4,922 / 4,922**;
- missing decision-spread rows: **0**;
- strategy behavior changed: **false**.

Decision-time spread distribution:

- p50: **2 points**;
- p75: **5 points**;
- p90: **10 points**;
- p95: **14 points**;
- p99: **107 points**;
- maximum: **250 points**.

Decision-time vs next-bar fill spread Pearson correlation:

**0.9213069050932308**

This confirms that the causal spread available at order submission strongly
tracks the fill-time spread diagnosed in M020-B.

### Fixed predeclared decision-time spread bands

| Decision-time spread | Trades | Net P/L |
|---|---:|---:|
| <=2 | 2,918 | USD -170.7632 |
| >2–5 | 842 | USD -97.7619 |
| >5–10 | 718 | USD -328.7979 |
| >10–20 | 289 | USD -374.7804 |
| >20–50 | 47 | USD -110.2818 |
| >50–100 | 54 | USD -197.6425 |
| >100 | 54 | USD -436.5799 |

Predeclared rollups:

- <=10 points: 4,478 trades, **USD -597.3229788380668**;
- >10 points: 444 trades, **USD -1,119.284653164277**;
- >20 points: 155 trades, **USD -744.5042466887646**.

The >10-point population is only about **9.02%** of all trades but accounts for
about **65.20%** of the accepted M019 net loss.

### Stability of >10-point decision-time spread

Both sides were negative:

- BUY: 186 trades, **USD -499.3611242643912**;
- SELL: 258 trades, **USD -619.9235288998857**.

Every calendar period was negative:

- Jun 23–30: 46 trades, **USD -82.02126797324189**;
- July: 162 trades, **USD -489.6043331609044**;
- August: 131 trades, **USD -272.16769055194993**;
- Sep 1–24: 105 trades, **USD -275.4913614781807**.

Every symbol was negative:

- EURJPY: **USD -200.59649447962207**;
- EURUSD: **USD -41.42142857143316**;
- GBPJPY: **USD -613.7359073337911**;
- GBPUSD: **USD -103.88571428570528**;
- USDJPY: **USD -159.64510849372516**.

### M020-C interpretation

The harmful wide-spread relationship persists using **causal information
available at order submission time**. It is not an artifact of using the
next-bar fill spread.

The >10-point boundary is not selected by a parameter sweep:

- it was a fixed predeclared M020-B/M020-C reporting boundary;
- it is also the observed p90 of the decision-time spread distribution;
- its harmful relationship is negative across all four calendar periods, all
  five symbols, and both sides.

This is sufficient to authorize one controlled treatment.

## M020-D — authorized single-variable decision-time spread treatment

### Hypothesis

New entries submitted when the observable decision-time spread is **greater
than 10 points** are a persistently harmful exposure.

### Control

Accepted M019 strategy unchanged.

### Treatment

Change exactly one behavior:

- reject a new entry at order submission when the broker-observable bid/ask
  spread is **>10 points**;
- allow entries at **<=10 points**.

The treatment must use only spread observable at the submission instant. It
must not inspect the next-bar execution spread.

### Isolation

M020-D must be tested independently against the immutable M019 control.

Do **not** stack:

- the M020-A 00:00–03:59 UTC session filter;
- symbol filters;
- side filters;
- ATR/SL/TP/trailing changes;
- stochastic/EMA/RSI/trend changes;
- any second spread threshold.

### Acceptance evidence

Before interpretation:

1. run treatment twice and require byte-identical artifacts;
2. preserve the ordinary M019 control hashes exactly;
3. prove zero accepted treatment entries have decision-time spread >10 points;
4. compare aggregate P/L and drawdown;
5. compare symbol, side, and calendar-period effects;
6. verify the result is not dependent on one symbol or one month;
7. retain all existing TP-direction, negative-TP, and no-strategy-artifact
   safety gates.

Even if M020-D improves the historical result, it remains in-sample controlled
evidence. A genuinely later paper/forward milestone remains mandatory.
