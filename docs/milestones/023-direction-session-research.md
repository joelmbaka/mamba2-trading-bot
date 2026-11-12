# Milestone 023 — Direction and Session Research

Status: **CLOSED — ZERO STAGE-B SESSIONS SUPPORTED; HISTORICAL HOLDOUT SEALED**

Branch:

`direction-session-research`

Branch point / closed M022 HEAD:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

M022 is closed and must not be reopened.

## Objective

M022 produced a new research hypothesis without supporting any candidate for
historical holdout:

- P2-03 validation improvement was entirely SELL-side contribution;
- P2-08 had the strongest validation headline economics among the M022
  finalists: net P/L, maximum drawdown, and win rate all improved versus P2-R;
- P2-08 still failed M022 support because 93.19% of positive BUY/SELL
  contribution came from SELL.

M023 asks a new, prospectively controlled question:

1. is SELL dominance structurally persistent across already-seen development
   and validation evidence;
2. does BUY have any stable time-localized contribution worth retaining;
3. is performance concentrated in stable market-session/time structure;
4. only after direction/session are fixed, does a weekday effect remain.

This new question does not reinterpret or weaken the failed M022 support
decision.

## First gate — diagnostic only

The first M023 gate is read-only analysis of existing accepted M022
development + validation artifacts.

Do **not** run a new side/session-filtered replay yet.

Do **not** inspect or open the untouched historical holdout.

Do **not** use M021 prospective outcomes.

Primary diagnostic arms:

- P2-R;
- P2-03;
- P2-08.

P2-01 is excluded from the main directional comparison because its M022
validation evidence failed the TP-safety gate.

Existing deterministic artifacts must be reused. If a required field is absent,
add only the minimum deterministic read-only diagnostic over the same already
seen partitions.

## Allowed source partitions

Development:

`2025-08-25T00:00:00Z` → `2026-04-21T00:00:00Z`

Validation:

`2026-04-21T00:00:00Z` → `2026-07-08T00:00:00Z`

Descriptive combined period:

development + validation only.

Untouched historical holdout remains sealed:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

M021 remains isolated.

## Timezone contract

For every diagnostic trade entry, derive timestamps using the runtime timezone
database in:

- UTC;
- `Africa/Nairobi` — EAT;
- `Europe/London` — DST-aware on the actual trade date;
- `America/New_York` — DST-aware on the actual trade date.

Do not substitute fixed UTC offsets for London or New York.

The diagnostic artifact must record:

- Python runtime;
- timezone implementation/module;
- timezone database source/version where available.

## Fixed EAT diagnostic windows

These windows are frozen before diagnostic output is inspected.

| Label | EAT | UTC |
|---|---|---|
| EAT-MORNING | 08:00–11:59 | 05:00–08:59 |
| EAT-MIDDAY | 12:00–14:59 | 09:00–11:59 |
| EAT-AFTERNOON | 15:00–17:59 | 12:00–14:59 |
| EAT-EVENING | 18:00–20:59 | 15:00–17:59 |
| EAT-ACTIVE | 08:00–20:59 | 05:00–17:59 |
| EAT-OFF-HOURS | 21:00–07:59 | complement of EAT-ACTIVE |

These are descriptive hypotheses only. None is a strategy filter at this gate.

## DST-aware market-session diagnostics

Report:

- London local entry hour;
- New York local entry hour;
- London-open transition;
- London/New York overlap.

For deterministic diagnostic labeling only, use:

- **London open transition**:
  `07:00–08:59 Europe/London`;
- **London/New York overlap**:
  entries satisfying both
  `13:00–16:59 Europe/London` and
  `08:00–11:59 America/New_York`.

Because both local-zone conditions are evaluated on each actual trade date,
temporary UK/US DST-transition mismatches remain visible rather than being
hidden behind a fixed UTC approximation.

Do not optimize arbitrary session boundaries in this gate.

## Direction attribution

For each of P2-R, P2-03, P2-08, separately for:

- development;
- validation;
- development + validation descriptive aggregate;

report:

- BOTH directions;
- SELL only;
- BUY only.

This is attribution/slicing over already-generated all-hours artifacts.

Removing historical trades from an all-hours artifact is **not** equivalent to
a fresh filtered-strategy replay. Suppressing entries can change later
position occupancy, order eligibility, strategy state, trailing interactions,
and subsequent fills.

Therefore no sliced result in this gate may be described as filtered-strategy
economics or causal performance.

## Required diagnostic metrics

Where fields exist in deterministic trade evidence, report for every relevant
direction/time grouping:

- closed trades;
- wins;
- losses;
- flats;
- non-flat win rate;
- net realized P/L;
- mean trade P/L;
- median trade P/L;
- mean entry spread;
- median entry spread;
- TP exit count;
- SL exit count;
- other exit count;
- per-symbol counts and net P/L.

Also report weekday breakdown for:

- Monday;
- Tuesday;
- Wednesday;
- Thursday;
- Friday.

Weekday output is diagnostic only. No weekday filter is authorized.

## Chronological stability

Use the ordered distinct common trading dates across development + validation.

There are 225 accepted development+validation trading dates, so define exactly
five non-shuffled chronological folds of **45 trading dates each**, in source
date order.

The diagnostic must publish the exact first/last date and date-list SHA-256 for
each fold.

For BOTH, SELL, and BUY, and for each fixed descriptive window where data
permits, report:

- fold P/L;
- fold trade count;
- folds with positive P/L;
- folds outperforming the corresponding BOTH/all-hours descriptive reference;
- symbol breadth within each fold when sample size permits;
- largest fold share of summed positive P/L / improvement.

A single short historical cluster must not define M023.

## Anti-mining rules

Hourly EAT/London/New-York tables may be produced diagnostically, but do not:

- choose the single best hour;
- create arbitrary discontinuous sets of winning hours;
- search all possible start/end session combinations;
- run a 24-hour × 5-weekday Cartesian optimization.

M023 seeks stable contiguous market-time structure.

## Future direction screen — design only

Do **not** execute this in the diagnostic gate.

Primary directional hypotheses:

- **D-R** — BOTH BUY + SELL;
- **D-S** — SELL only;
- **D-B** — BUY only.

P2-08 is the primary research anchor because it had the strongest M022
validation headline economics, but it was **not M022-supported** and is not
production-approved.

P2-R and P2-03 remain reference evidence for determining whether any SELL
effect is specific to P2-08 or persists across parameterizations.

## Future bounded direction/session design

The next economic stage, if later authorized, must remain sequential and
bounded:

### Stage A — direction

On the frozen research anchor, compare only:

- D-R;
- D-S;
- D-B.

No side weighting and no additional direction variants.

### Stage B — session

Only after one direction hypothesis is prospectively fixed may session
screening occur.

The session family may use only a small contiguous set drawn from the already
frozen diagnostic concepts:

- all-hours reference;
- EAT-ACTIVE;
- EAT-MORNING;
- EAT-MIDDAY;
- EAT-AFTERNOON;
- EAT-EVENING;
- London-open transition;
- London/New-York overlap.

Before any Stage-B replay, the exact subset must be frozen from diagnostic
evidence with no more than **4 non-reference session variants** plus all-hours
reference.

Do not combine arbitrary hours.

### Weekday conditioning

No weekday filter in Stage A or Stage B.

Weekday conditioning may be considered only after direction + session are
fixed, and only through a later small predeclared family.

## Future M023 robustness rule design

M022's side-concentration <=80% rule is not appropriate for a hypothesis whose
question is explicitly directional specialization.

Before any filtered M023 replay is dispatched, freeze direction-appropriate
robustness gates covering at least:

- sufficient total activity;
- per-symbol representation;
- multiple-symbol P/L breadth;
- multiple chronological folds;
- multiple days/weeks;
- stable session behavior;
- maximum single-symbol contribution;
- maximum single-fold/short-period contribution;
- deterministic/safety invariants;
- unchanged cost and replay semantics.

Do not weaken any M022 conclusion.

## Cost / replay contract

Any future M023 replay must preserve the accepted replay semantics and:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`

Production defaults remain unchanged.

M15 remains disabled as a signal.

## Safety

Never:

- enable live trading;
- place, modify, or close real orders;
- expose arbitrary shell;
- modify production defaults;
- merge to main;
- deploy;
- reopen M022 economics;
- inspect the M022 historical holdout during this diagnostic gate;
- inspect M021 outcomes for M023 tuning;
- add M15 as a signal.

## Current authorization

Authorized now:

1. deterministic read-only diagnostic analysis of existing M022 development
   and validation evidence for P2-R, P2-03, P2-08;
2. source/artifact hash verification;
3. timezone-aware EAT/London/New-York descriptive tables;
4. weekday diagnostics;
5. 5-fold chronological stability diagnostics;
6. bounded next-stage direction/session design documentation.

Not authorized now:

- any fresh direction-filtered replay;
- any fresh session-filtered replay;
- weekday-filtered replay;
- historical-holdout inspection;
- M021 inspection;
- production/live changes.


## Accepted diagnostic evidence — 2026-09-28

The first M023 gate completed using existing M022 deterministic trade-level
diagnostics only. No strategy replay was run.

Protocol freeze commit:

`099b947f630f26de07f65920c54e98c237dc45bd`

Read-only analyzer implementation:

`f925ae8121fb9ce4ee04c1c980e58720c2a611f3`

Native diagnostic test command:

`mamba2-m023-direction-session-tests-v1`

Published test result:

`f84a30514645bcc454fc2666a2eca09e90d7f1fe`

Test result:

- **9 passed / 0 failed**;
- exact M023 feature SHA:
  `f925ae8121fb9ce4ee04c1c980e58720c2a611f3`;
- economic replay: **no**;
- historical holdout access: **no**;
- M021 outcome use: **no**;
- real-order API: **no**.

Deterministic diagnostic command:

`mamba2-m023-direction-session-diagnostic-v2`

Published diagnostic result:

`30712d1c55e1204fc4d849a38bfa96318155b54b`

Compact read-only review result:

`794151eb6608372b7d1c883f53cff3f8bf89ac6f`

Artifact pair:

- `backtest_data/m023-direction-session-diagnostics-v1/m023-direction-session-diagnostics-a.json`;
- `backtest_data/m023-direction-session-diagnostics-v1/m023-direction-session-diagnostics-b.json`.

Both artifact SHA-256:

`0b306c2341befd7110ea2a6695ecd4fc473055fb2231849b5a3741a11251d9a2`

Deterministic byte/hash equality: **PASS**.

The first artifact was preserved after a publisher-only stdout truncation
issue; the second artifact was generated later and matched it byte-for-byte.
No economic replay was repeated.

### Exact accepted M022 source references

| Arm | Partition | Closed trades | Diagnostic SHA-256 | Source baseline SHA-256 |
|---|---|---:|---|---|
| P2-R | development | 12,006 | `ae124fea75ead8f6d1e5e50cf090fb6db401ad5cdef6316f6851641f034205c7` | `55630b2ff48b8594f04ed2d7ebb2012ef7c39db5f7b3b50f2fb1212049418530` |
| P2-R | validation | 3,908 | `7a470bfebfa4434793f2f25bfcb416f4342187b5b08ca6f319237d9ea4856979` | `b0103541cc843109a41c7f6df34c01fa912ae74351324cb6233de3df2090c1c6` |
| P2-03 | development | 8,439 | `28cce843b8969a3058fdb2dd1e7677cc69292dadca8ff7683dbf0df5332ec76e` | `5d8a8e7470ba10e7398aee03e7df20668971f69985b3b6fea48a8c3b670ef794` |
| P2-03 | validation | 2,860 | `30b7718a0075278853a9224cd5939446ea4624bb73f2b566f333e1081ef8c0b8` | `44e8e0b0b66823a681ab100d52c71ee0b75de55bbd2f3fa1c336ba8404308fae` |
| P2-08 | development | 8,620 | `bc5ce5fae1717b42075f74860aee80b3c0f8155b860bae2096eefa6b9f7a800c` | `c4a893ff0896eda2a6726ac9c14415a0128817fdee58f17b670976eed5eed55f` |
| P2-08 | validation | 2,884 | `a8e81708d5f1128f8ad17497ee35f08cae8d9bc70e4b018aca1be5acd765f2ce` | `f333b76323459395d4d3f007a03fb842f210f86783bc114bd3eed57af21f3aae` |

### Timezone runtime

- Python: **3.10.19**
- implementation: **CPython**
- timezone conversion: stdlib `zoneinfo`
- tzdata package: **2025.2**
- zones:
  UTC, Africa/Nairobi, Europe/London, America/New_York.

London and New York labels were calculated from each trade's actual entry
date. No fixed-offset DST approximation was used.

### Exact chronological folds

Each fold contains 45 ordered accepted trading dates.

| Fold | First date | Last date | Date-list SHA-256 |
|---|---|---|---|
| F1 | 2025-08-25 | 2025-10-24 | `bccecd70357df71e85fbd7ce1d0f329fc6d866998c0fe3ad899290b6d0ed0f8e` |
| F2 | 2025-10-27 | 2025-12-29 | `4f6344e3ae75c51e48d176d0b85c743666cf34c4cfe7b05731d7d40a58d17a8b` |
| F3 | 2025-12-30 | 2026-03-03 | `6c51d75e0d585649821d3105e3e1d1b2c485fa34e70348041d1b137b26485d4f` |
| F4 | 2026-03-04 | 2026-05-05 | `f0e758dfdf722747aacc277fdd9c09b0ab9035415978369aaec97b6f1ed807ec` |
| F5 | 2026-05-06 | 2026-07-07 | `1df4395f28637370920957a3ae2af3eb5fc75b5d4255918e29d42fcd14073292` |

## Direction finding

The M022 validation observation that most **improvement versus P2-R** came
from SELL must not be confused with a finding that SELL-only had superior raw
economics.

Mean trade P/L by direction:

| Arm | Partition | SELL mean P/L | BUY mean P/L | Less-negative slice |
|---|---|---:|---:|---|
| P2-R | development | -1.4285 | -1.1285 | BUY |
| P2-R | validation | -0.8989 | -0.5872 | BUY |
| P2-03 | development | -1.5711 | -1.0340 | BUY |
| P2-03 | validation | -0.8821 | -1.1381 | SELL |
| P2-08 | development | -1.5461 | -1.3038 | BUY |
| P2-08 | validation | -1.1115 | -0.7612 | BUY |

Thus BUY had the less-negative mean trade P/L in **5 of 6** arm/partition
comparisons. SELL superiority is not a generic raw-slice property.

P2-08 combined descriptive totals:

| Direction | Closed trades | Net P/L | Mean P/L | Win rate |
|---|---:|---:|---:|---:|
| BOTH | 11,504 | -15,119.22 | -1.3143 | 34.79% |
| SELL | 6,263 | -9,007.31 | -1.4382 | 33.42% |
| BUY | 5,241 | -6,111.91 | -1.1662 | 36.43% |

These remain attribution slices, not causal filtered-strategy results.

## Strongest persistent time structure

The broad EAT-active/off-hours split is the clearest diagnostic structure.

Combined BOTH-direction mean trade P/L:

| Arm | EAT-ACTIVE 08:00–20:59 | EAT-OFF-HOURS 21:00–07:59 |
|---|---:|---:|
| P2-R | -0.6304 | -1.8529 |
| P2-03 | -0.7049 | -1.9439 |
| P2-08 | -0.6510 | -2.2050 |

For **all three arms**, EAT-ACTIVE mean trade P/L was better than the
corresponding BOTH/all-hours fold in **5 of 5 chronological folds**.
EAT-OFF-HOURS was better in **0 of 5**.

The same broad pattern also persists within P2-08 directions:

| P2-08 direction | EAT-ACTIVE mean P/L | EAT-OFF-HOURS mean P/L | ACTIVE better than all-hours mean in folds |
|---|---:|---:|---:|
| SELL | -0.8372 | -2.2250 | 5 / 5 |
| BUY | -0.4336 | -2.1803 | 5 / 5 |

This is a strong descriptive **time-of-day** hypothesis. It still does not
prove that suppressing off-hours entries will reproduce the sliced economics,
because entry suppression changes future strategy state and position
occupancy.

### Development versus validation — P2-08

| Direction/window | Development net P/L | Dev mean P/L | Validation net P/L | Val mean P/L |
|---|---:|---:|---:|---:|
| SELL EAT-MORNING | -682.13 | -0.9156 | +32.60 | +0.1288 |
| SELL EAT-MIDDAY | -867.07 | -1.2941 | -12.01 | -0.0501 |
| SELL EAT-AFTERNOON | -626.34 | -1.0634 | -65.59 | -0.3564 |
| SELL EAT-EVENING | -365.50 | -0.5632 | -386.97 | -1.7510 |
| SELL EAT-ACTIVE | -2,541.04 | -0.9578 | -431.98 | -0.4810 |
| SELL EAT-OFF-HOURS | -4,737.94 | -2.3056 | -1,296.35 | -1.9731 |
| SELL London-open transition | -459.34 | -1.0911 | +127.80 | +1.0224 |
| SELL London/NY overlap | -898.73 | -1.1178 | -272.76 | -1.0491 |
| BUY EAT-MORNING | -631.31 | -0.9653 | +69.82 | +0.3174 |
| BUY EAT-MIDDAY | -253.74 | -0.4375 | +118.51 | +0.6850 |
| BUY EAT-AFTERNOON | -62.90 | -0.1248 | -46.34 | -0.2971 |
| BUY EAT-EVENING | -479.01 | -0.8600 | -34.54 | -0.1736 |
| BUY EAT-ACTIVE | -1,426.96 | -0.6218 | +107.45 | +0.1436 |
| BUY EAT-OFF-HOURS | -3,673.37 | -2.2717 | -1,119.02 | -1.9260 |
| BUY London-open transition | -531.77 | -1.5064 | +33.54 | +0.3049 |
| BUY London/NY overlap | -253.31 | -0.3703 | -33.20 | -0.1581 |

Validation therefore contains positive time-localized BUY **and** SELL
slices. The broad ACTIVE/OFF-HOURS contrast is more persistent than any
single narrow positive window.

## Market-local timing observations

The full immutable artifact contains 24-hour local-clock tables for P2-08 in
all of:

- Africa/Nairobi;
- Europe/London;
- America/New_York;

for BOTH, SELL, and BUY separately.

Those tables are descriptive only and are intentionally not ranked by maximum
hourly P/L.

The predeclared broad market windows show:

- P2-08 SELL London-open transition:
  development mean -1.0911, validation mean **+1.0224**;
- P2-08 BUY London-open transition:
  development mean -1.5064, validation mean **+0.3049**;
- P2-08 London/New-York overlap remained negative in both partitions for both
  directions.

Fold stability for P2-08 SELL London-open transition is more interesting than
the overlap: its mean trade P/L is better than P2-08 BOTH/all-hours in **5/5
folds**, with positive net P/L in F4 and F5. It is therefore a legitimate
future session hypothesis, but not a validated filter.

## Narrow-window stability

The fixed subwindows show some localized structure, but less stability than
the broad ACTIVE/OFF-HOURS split.

For P2-08:

- SELL EAT-MORNING: positive net P/L in 1/5 folds;
- SELL EAT-MIDDAY: 1/5;
- SELL EAT-AFTERNOON: 1/5;
- SELL EAT-EVENING: 2/5;
- BUY EAT-MORNING: 1/5;
- BUY EAT-MIDDAY: 1/5;
- BUY EAT-AFTERNOON: **3/5**;
- BUY EAT-EVENING: 0/5.

P2-03 BUY EAT-EVENING is a notable descriptive exception: it is positive in
**4/5 folds**, but the effect is not reproduced by P2-08 BUY, so it may be
parameter-specific rather than general session structure.

This is why M023 must not select a window merely because it has the best
historical slice.

## Weekday diagnostic

No P2-08 combined weekday is profitable for BOTH, SELL, or BUY.

P2-08 BUY mean trade P/L by weekday:

| Day | Mean trade P/L | Net P/L |
|---|---:|---:|
| Monday | -0.4571 | -479.02 |
| Tuesday | -1.5065 | -1,690.27 |
| Wednesday | -1.1682 | -1,221.93 |
| Thursday | -1.4081 | -1,457.43 |
| Friday | -1.2760 | -1,263.26 |

The weekday table does not justify a weekday filter at this gate.

## Reviewer interpretation

The diagnostic evidence changes the working hypothesis in two important ways.

1. **Do not jump directly to SELL-only.**
   M022's SELL concentration described where P2-03/P2-08 improvements came
   from relative to P2-R. The raw M023 slices show BUY is less negative in
   most arm/partition comparisons, and BUY has clear positive validation
   pockets during active EAT hours.

2. **Time-of-day deserves causal replay before weekday mining.**
   The EAT-ACTIVE versus EAT-OFF-HOURS separation is large, appears across
   P2-R/P2-03/P2-08, and persists across all five folds in mean trade P/L.
   This is more credible than isolated hourly or weekday peaks.

## Proposed next-stage matrix design — not authorized to execute

### Stage A — causal direction screen

Primary anchor remains P2-08, with the exact M022 P2-08 parameters unchanged.

The bounded direction matrix should contain exactly:

| ID | Entry directions |
|---|---|
| D-R | BOTH BUY + SELL |
| D-S | SELL only |
| D-B | BUY only |

This is a **design**, not execution authorization.

The causal replay is required because slicing existing all-hours trades cannot
tell us how suppressing one direction changes later occupancy and state.

P2-R and P2-03 should remain read-only comparison evidence; do not create an
expanded cross-product of three parameter sets × three directions unless a
future prospective checkpoint explicitly requires it.

### Stage B — session family after direction is fixed

Do not freeze the exact Stage-B subset until Stage A has selected/fixed a
direction hypothesis.

The bounded candidate pool should remain:

- all-hours reference;
- EAT-ACTIVE;
- London-open transition;
- EAT-MORNING;
- EAT-MIDDAY;
- EAT-AFTERNOON;
- EAT-EVENING;
- London/New-York overlap.

At the later Stage-B freeze, choose **no more than four non-reference**
contiguous/session variants plus all-hours reference.

Diagnostic priority for that later freeze:

1. **EAT-ACTIVE** — strongest cross-arm/cross-fold structural effect;
2. **London-open transition** — especially relevant if Stage A fixes SELL;
3. narrow EAT windows only when their evidence matches the Stage-A direction;
4. London/New-York overlap is lower priority because it remained negative and
   less stable in these slices.

No arbitrary hourly sets are allowed.

### Future robustness design

Before Stage-A filtered replay, a separate prospective checkpoint must freeze
numeric gates appropriate to directional specialization. At minimum the gates
must cover:

- deterministic A/B;
- safety/TP invariants;
- minimum retained activity;
- per-symbol representation;
- multi-symbol P/L breadth;
- multiple chronological folds;
- multiple weeks/days;
- maximum single-symbol contribution;
- maximum single-fold/short-period contribution;
- unchanged cost/replay semantics.

M022's side-concentration <=80% rule must not be copied to a SELL-only or
BUY-only arm.

No numeric robustness threshold is being invented from the diagnostic
outcomes in this checkpoint.

## Diagnostic gate stop

This turn ends at diagnostic evidence + design.

No M023 direction-filtered replay has run.

No M023 session-filtered replay has run.

No weekday-filtered replay has run.

Historical holdout remains completely sealed.

M021 remains uninspected for M023 tuning.

Production defaults and main remain unchanged.


## Stage A protocol freeze — prospective causal direction screen

Status: **FROZEN BEFORE STAGE-A ECONOMICS**

This section supersedes the earlier "design only" Stage-A text for execution
control. It was committed before any D-R/D-S/D-B economic replay.

### Research anchor

Use exact P2-08 parameters:

- stochastic: **21 / 7 / 7**;
- boundary: **20 / 80**;
- EMA: **7**;
- decision-time spread gate: **none**;
- ATR SL: **1.5**;
- ATR TP: **3.0**;
- session: **ALL HOURS**;
- directional trailing: **unchanged**;
- M15: **disabled**;
- position size: **0.1**.

Cost contract remains:

\`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED\`

### Exact Stage-A matrix

Exactly three arms:

| ID | New-entry direction eligibility |
|---|---|
| D-R | BOTH BUY + SELL |
| D-S | SELL entries only; suppress new BUY entries |
| D-B | BUY entries only; suppress new SELL entries |

No weighting, no separate parameters by direction, no fourth arm, and no
parameter retuning.

The direction filter changes **new-entry eligibility only**. Do not change
stochastic semantics, M5/M1 logic, EMA confirmation, ATR, stop/TP
construction, trailing, exit handling, position management, spread behavior,
account-currency conversion, or replay timing.

Record direction-filter rejection counts explicitly.

All arms start under identical flat/research-partition semantics.

For D-S, accepted BUY entries must be **0**.

For D-B, accepted SELL entries must be **0**.

### Exact Stage-A seen-research partition

M022 development and validation have already been inspected, so Stage A uses
them as one continuous **seen research sample** only.

Start:

\`2025-08-25T00:00:00Z\`

End-exclusive:

\`2026-07-08T00:00:00Z\`

Accepted ordered trading dates:

**225**

First date:

\`2025-08-25\`

Last date:

\`2026-07-07\`

Ordered 225-date list SHA-256, using UTF-8 ISO dates joined by newline and a
final newline:

\`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0\`

Do not include \`2026-07-08T00:00:00Z\` onward.

Historical holdout remains sealed.

Existing folds remain exact and may not be redrawn:

| Fold | First date | Last date | Date-list SHA-256 |
|---|---|---|---|
| F1 | 2025-08-25 | 2025-10-24 | \`bccecd70357df71e85fbd7ce1d0f329fc6d866998c0fe3ad899290b6d0ed0f8e\` |
| F2 | 2025-10-27 | 2025-12-29 | \`4f6344e3ae75c51e48d176d0b85c743666cf34c4cfe7b05731d7d40a58d17a8b\` |
| F3 | 2025-12-30 | 2026-03-03 | \`6c51d75e0d585649821d3105e3e1d1b2c485fa34e70348041d1b137b26485d4f\` |
| F4 | 2026-03-04 | 2026-05-05 | \`f0e758dfdf722747aacc277fdd9c09b0ab9035415978369aaec97b6f1ed807ec\` |
| F5 | 2026-05-06 | 2026-07-07 | \`1df4395f28637370920957a3ae2af3eb5fc75b5d4255918e29d42fcd14073292\` |

Each fold contains exactly **45** accepted trading dates.

### Mandatory gates

Every arm must pass all of:

1. deterministic A/B baseline hash match;
2. deterministic A/B diagnostic hash match;
3. deterministic A/B summary hash match;
4. exact Stage-A parameter metadata;
5. exact 225-date research partition;
6. exact source-manifest evidence;
7. strict common replay-boundary clock;
8. full per-symbol M1 preservation;
9. unchanged cost contract;
10. negative-P/L TP exits = **0**;
11. wrong-side initial TP = **0**;
12. historical holdout untouched;
13. M021 unused;
14. real-order API not called.

Additional direction invariants:

- D-S: BUY accepted entries = **0**;
- D-B: SELL accepted entries = **0**.

### Activity and representation gates

Relative to D-R on the exact same 225-date research partition, D-S and D-B
must satisfy all of:

1. total closed trades >= **35%** of D-R total;
2. every one of the five symbols >= **25%** of that symbol's D-R closed
   trades;
3. every one of the five fixed chronological folds >= **25%** of D-R closed
   trades in that fold;
4. candidate has closed trades in >= **80%** of ISO calendar weeks in which
   D-R has at least one closed trade.

These thresholds are prospective and may not be lowered after economics.

### Stage-A support requirements

A non-reference direction arm is **SUPPORTED** only if all of the following
hold:

1. mandatory gates pass;
2. activity/representation gates pass;
3. net realized P/L is strictly better than D-R;
4. maximum equity drawdown USD is no worse than D-R;
5. mean closed-trade P/L is strictly better than D-R;
6. non-flat win rate is no more than **1.0 percentage point** below D-R;
7. mean closed-trade P/L is better than D-R in at least **4 of 5** fixed
   chronological folds;
8. mean closed-trade P/L is better than D-R in at least **3 of 5** symbols;
9. candidate mean closed-trade P/L is better than D-R during
   **EAT-ACTIVE 08:00–20:59 Africa/Nairobi**;
10. candidate mean closed-trade P/L is better than D-R in at least **55%** of
    eligible ISO weeks.

Weekly comparison rules:

- use ISO weeks;
- compare candidate versus D-R **mean closed-trade P/L**;
- a week is eligible only when both arms contain at least **10** closed trades;
- require at least **20** eligible weeks, otherwise weekly robustness fails;
- do not substitute total weekly P/L for the mean-trade comparison.

Net P/L alone is not sufficient.

### Concentration gates

For a single-direction arm with positive total P/L improvement versus D-R:

**Symbol concentration**

- compute positive symbol-level total-P/L deltas versus D-R;
- no one symbol may contribute more than **70%** of their summed positive
  deltas.

**Fold concentration**

- compute positive fold-level total-P/L deltas versus D-R;
- no one fold may contribute more than **60%** of their summed positive
  deltas.

There is deliberately **no BUY/SELL concentration gate**, because direction
specialization is the question under test.

### Stage-A session-stability reporting

Stage A remains **ALL HOURS**.

Do not filter sessions.

Each causal Stage-A arm must nevertheless report separately:

- EAT-ACTIVE: **08:00–20:59 Africa/Nairobi**;
- EAT-OFF-HOURS: **21:00–07:59 Africa/Nairobi**.

For each report include:

- closed trades;
- net P/L;
- mean trade P/L;
- win rate;
- per-symbol counts/P&L;
- fold-level mean P/L.

The Stage-A support gate requires only:

\`candidate EAT-ACTIVE mean trade P/L > D-R EAT-ACTIVE mean trade P/L\`

Do **not** require off-hours improvement. Off-hours are preserved for later
Stage-B causal session testing.

### Stage-A classifications

- D-R: **REFERENCE**.
- A non-reference arm failing a mandatory or representation gate:
  **INELIGIBLE**.
- An eligible non-reference arm failing one or more Stage-A support
  requirements: **NOT SUPPORTED**.
- A non-reference arm passing every Stage-A support requirement:
  **SUPPORTED**.

### Direction-fixing rule

D-R is always retained as the reference direction.

If neither D-S nor D-B is SUPPORTED:

**FIX D-R / BOTH** for Stage B.

If exactly one of D-S or D-B is SUPPORTED:

**fix that supported direction** for Stage B.

If both D-S and D-B are SUPPORTED, calculate for each:

\`pl_gain_fraction = (candidate_net_pl - reference_net_pl) / abs(reference_net_pl)\`

\`dd_improvement_fraction = (reference_dd - candidate_dd) / reference_dd\`

\`mean_trade_gain_fraction = (candidate_mean_trade_pl - reference_mean_trade_pl) / abs(reference_mean_trade_pl)\`

\`win_rate_gain_fraction = (candidate_win_rate - reference_win_rate) / reference_win_rate\`

\`active_mean_gain_fraction = (candidate_active_mean_trade_pl - reference_active_mean_trade_pl) / abs(reference_active_mean_trade_pl)\`

Then:

\`robustness_maximin = minimum of those five values\`

Choose the larger robustness_maximin.

Exact tie-break order:

1. more folds with better mean P/L than D-R;
2. more symbols with better mean P/L than D-R;
3. larger proportion of eligible weeks with better mean P/L;
4. higher closed-trade activity ratio;
5. lexicographically smaller arm ID.

No post-result alternative tie-breaker is permitted.

### Required reporting

For every arm report at minimum:

- exact direction;
- exact parameters;
- accepted orders;
- closed trades;
- wins/losses/flats;
- non-flat win rate;
- net realized P/L;
- mean trade P/L;
- median trade P/L;
- ending balance;
- ending equity;
- max DD USD/%;
- per-symbol counts/P&L/mean P&L;
- five-fold counts/P&L/mean P&L;
- ISO-week counts/P&L/mean P&L;
- EAT-ACTIVE counts/P&L/mean P&L;
- EAT-OFF-HOURS counts/P&L/mean P&L;
- direction-filter rejection count;
- entry-spread diagnostics;
- exit-type diagnostics;
- TP safety;
- remaining positions;
- deterministic artifact hashes;
- source/date/replay-boundary hashes;
- concentration diagnostics.

### Authorized implementation sequence

After this protocol-freeze commit exists:

1. implement experiment-only direction overrides;
2. leave production defaults unchanged;
3. add exact tests for D-R, D-S, D-B, opposite-side refusal, exact P2-08
   parameters, research-partition gating, holdout refusal, and deterministic
   reporting;
4. add only fixed local-control actions for:
   - M023 Stage-A direction family;
   - M023 Stage-A mechanical assessment;
5. do not add Stage-B session execution;
6. do not add historical-holdout execution;
7. run fixed native M023 Stage-A tests;
8. sync Dell to exact feature SHA;
9. require clean worktree, divergence 0/0, and exact feature SHA;
10. run D-R first;
11. then D-S and D-B may run concurrently, with maximum two non-reference
    arms concurrently;
12. review deterministic/safety evidence;
13. run frozen mechanical Stage-A assessment;
14. mechanically fix exactly one Stage-B direction according to the rule above;
15. durably record Stage-A results and the fixed direction;
16. stop.

### Stage B remains unauthorized

Do not execute a session-filtered replay in Stage A.

After Stage A mechanically fixes direction, stop. The next reviewer checkpoint
must freeze the exact Stage-B session matrix.

The future bounded candidate pool remains:

- all-hours reference;
- EAT-ACTIVE;
- London-open transition;
- EAT-MORNING;
- EAT-MIDDAY;
- EAT-AFTERNOON;
- EAT-EVENING;
- London/New-York overlap.

No more than **four non-reference** session variants may later be frozen.

Weekday conditioning remains deferred until direction + session are fixed.

Historical holdout remains sealed:

\`2026-07-08T00:00:00Z\` → \`2026-09-25T00:00:00Z\`

No M023 holdout action may exist yet.

M021 remains isolated and uninspected for M023 tuning.


## Stage A accepted result — direction fixed for Stage B

Stage-A family result:

\`04f8cb971ac56b06739aba594df1a2090745f396\`

Exact Stage-A economic feature SHA:

\`070ca2f01d887da4088698df40cd012a2596d048\`

Frozen mechanical assessment command:

\`mamba2-m023-stage-a-direction-assessment-v1\`

Assessment result:

\`ed01975c5ea7945d9890d807c58ff133e07a6aa1\`

Assessment status:

\`ok: true\`

### Mechanical classification

- **D-R / BOTH — REFERENCE**
- **D-S / SELL only — NOT SUPPORTED**
- **D-B / BUY only — SUPPORTED**

D-S passed mandatory and representation gates but failed the frozen support
requirements for:

- mean trade P/L improvement;
- win-rate tolerance;
- fold mean breadth;
- symbol mean breadth;
- EAT-active mean improvement;
- weekly robustness.

D-S robustness:

- total activity ratio: **0.6746611053**;
- folds with better mean: **2 / 5**;
- symbols with better mean: **2 / 5**;
- eligible ISO weeks: **46**;
- better ISO weeks: **19**;
- better-week ratio: **41.30%**.

D-B economics:

- closed trades: **6,630**;
- net realized P/L: **USD -7,453.8802448**;
- maximum equity drawdown: **USD 7,497.0102757**;
- mean trade P/L: **-1.124265497**;
- non-flat win rate: **36.6737%**;
- EAT-active mean trade P/L: **-0.4402526733**.

D-B robustness:

- total activity ratio: **0.5761209593**;
- every one of five symbols passed representation;
- every one of five chronological folds passed representation;
- represented reference trade weeks: **46 / 46**;
- folds with better mean: **4 / 5**;
- symbols with better mean: **3 / 5**;
- eligible ISO weeks: **46**;
- better ISO weeks: **30**;
- better-week ratio: **65.2174%**;
- max positive-symbol improvement share: **44.20%**;
- max positive-fold improvement share: **26.18%**.

Every frozen Stage-A support condition passed for D-B.

### Mechanically fixed Stage-B direction

The frozen Stage-A rule therefore fixes exactly:

**D-B / BUY ONLY**

for Stage B.

Do not reconsider SELL.

Do not carry BOTH as a competing Stage-B strategy direction.

D-R/BOTH may remain read-only/reference evidence where useful, but Stage-B
strategy direction is fixed to BUY only.

### Stage-A safety/isolation

Stage A completed with:

- historical holdout untouched;
- M021 unused;
- no session filtering;
- no weekday filtering;
- no real-order API;
- exact 225-date research sample preserved;
- deterministic A/B evidence for all three arms;
- TP-safety gates clean.

Stage B is still not authorized by this acceptance alone. A separate
prospective Stage-B protocol-freeze commit must exist before any
session-filtered economic replay.


## Stage B protocol freeze — BUY-only causal session screen

Status: **FROZEN BEFORE STAGE-B ECONOMICS**

This Stage-B protocol is prospectively fixed after Stage A mechanically selected
D-B / BUY only and before any session-filtered replay.

### Research anchor

Use exact P2-08 parameters:

- stochastic: **21 / 7 / 7**;
- boundary: **20 / 80**;
- EMA: **7**;
- decision-time spread gate: **none**;
- ATR SL: **1.5**;
- ATR TP: **3.0**;
- direction: **BUY ONLY**;
- directional trailing: **unchanged**;
- M15: **disabled**;
- position size: **0.1**.

Cost contract:

\`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED\`

### Exact Stage-B matrix

Exactly five arms:

| ID | Direction | New-entry session |
|---|---|---|
| S-R | BUY only | ALL HOURS |
| S-ACTIVE | BUY only | 08:00–20:59 Africa/Nairobi |
| S-MORNING | BUY only | 08:00–11:59 Africa/Nairobi |
| S-MIDDAY | BUY only | 12:00–14:59 Africa/Nairobi |
| S-AFTERNOON | BUY only | 15:00–17:59 Africa/Nairobi |

Do **not** add:

- EAT-EVENING;
- London-open transition;
- London/New-York overlap;
- arbitrary hours.

Frozen exclusion rationale from already accepted diagnostics:

- EAT-ACTIVE is the dominant stable structural hypothesis;
- P2-08 BUY EAT-AFTERNOON had the strongest narrow-window fold positivity:
  **3 / 5** folds;
- P2-08 BUY EAT-MIDDAY materially improved development mean and had positive
  validation economics;
- P2-08 BUY EAT-MORNING preserves the predeclared independent morning
  hypothesis and had positive validation evidence;
- P2-08 BUY EAT-EVENING was positive in **0 / 5** folds;
- London-open transition was materially negative during development for BUY
  and was previously more relevant under a possible SELL direction;
- London/New-York overlap remained negative and less stable.

No session candidate may be added after the first Stage-B economic result.

### Session-filter semantics

The session filter controls **new BUY entry eligibility only**.

Outside the selected session:

- suppress new BUY entries.

Do not:

- force-close existing positions at session end;
- disable stop loss;
- disable take profit;
- disable trailing;
- modify open-position management;
- alter account-currency conversion;
- alter replay timing;
- alter stochastic/EMA/ATR calculations.

An open position may continue to be managed and exit outside its entry
session.

Record session-filter rejection counts.

### Timezone contract

All Stage-B EAT windows use:

\`Africa/Nairobi\`

Use timezone-aware timestamps.

Africa/Nairobi has no DST transition, but use the named timezone rather than a
hardcoded offset or naive local-clock conversion.

Record timezone implementation/runtime metadata.

### Exact Stage-B seen-research sample

Use exactly:

\`2025-08-25T00:00:00Z\` → \`2026-07-08T00:00:00Z\`

Accepted trading dates:

**225**

Ordered date-list SHA-256:

\`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0\`

Reuse the exact existing five 45-date chronological folds. Do not redraw them.

Historical holdout remains sealed:

\`2026-07-08T00:00:00Z\` → \`2026-09-25T00:00:00Z\`

### Stage-B reference equivalence

S-R is the causal BUY-only all-hours strategy.

It must reproduce accepted Stage-A D-B exactly under identical feature code,
apart from Stage-B metadata.

Require exact economic parity with accepted D-B for:

- closed trades;
- net realized P/L;
- mean trade P/L;
- non-flat win rate;
- maximum equity drawdown;
- per-symbol economics;
- fold economics;
- EAT diagnostics;
- TP safety.

If S-R does not reproduce D-B, **STOP**.

Do not interpret any non-reference session economics until reference
equivalence passes.

### Mandatory gates

Every Stage-B arm must pass:

1. deterministic A/B baseline hash equality;
2. deterministic A/B diagnostic hash equality;
3. deterministic A/B summary hash equality;
4. exact P2-08 parameters;
5. BUY-only direction;
6. zero accepted SELL entries;
7. exact session metadata;
8. exact 225-date list;
9. exact source manifest;
10. strict common replay-boundary clock;
11. full per-symbol M1 preservation;
12. unchanged cost contract;
13. wrong-side initial TP = **0**;
14. negative-P/L TP exits = **0**;
15. historical holdout untouched;
16. M021 unused;
17. weekday filter absent;
18. M15 disabled;
19. no real-order API.

### Session representation gate

Do not compare a short session's raw trade count directly to all-hours.

For each candidate session W, derive from deterministic S-R / D-B all-hours
evidence the descriptive count of reference entries whose **entry time** falls
inside W.

That reference-window slice is used only as the representation denominator,
not as causal economic evidence.

For each non-reference session require all of:

1. candidate total closed trades >= **60%** of S-R's descriptive same-window
   closed-trade count;
2. for every symbol, candidate closed trades >= **40%** of S-R's descriptive
   same-window count for that symbol;
3. for every chronological fold, candidate closed trades >= **40%** of S-R's
   descriptive same-window count for that fold;
4. candidate has at least **500** closed trades total;
5. every fold has at least **50** closed trades;
6. candidate has trades in >= **75%** of ISO weeks in which the S-R
   descriptive same-window slice has at least one trade.

These gates may not be lowered after results.

### Primary Stage-B support rule

A non-reference session is **SUPPORTED** only if every condition holds:

1. mandatory gates pass;
2. representation gate passes;
3. net realized P/L is **strictly positive**;
4. mean closed-trade P/L is **strictly positive**;
5. maximum equity drawdown USD is strictly lower than S-R;
6. non-flat win rate is no more than **1.0 percentage point** below S-R;
7. mean trade P/L is better than S-R in at least **4 of 5** chronological
   folds;
8. candidate net P/L is positive in at least **3 of 5** chronological folds;
9. mean trade P/L is better than S-R in at least **3 of 5** symbols;
10. candidate net P/L is positive in at least **3 of 5** symbols;
11. candidate mean trade P/L is better than S-R in at least **60%** of
    eligible ISO weeks;
12. at least **30** ISO weeks are eligible.

Eligible weekly comparison:

- both candidate and S-R descriptive same-window evidence must contain at
  least **5** closed trades in that ISO week;
- compare **mean trade P/L**;
- do not substitute weekly total P/L.

### Concentration rules

For a candidate with positive net P/L:

**Positive symbol P/L concentration**

- at least **3** symbols must have positive net P/L;
- no one symbol may contribute more than **60%** of total positive symbol
  P/L.

**Positive fold P/L concentration**

- at least **3** folds must have positive net P/L;
- no one fold may contribute more than **60%** of total positive fold P/L.

These are mandatory Stage-B support rules.

### Stage-B classifications

- S-R: **REFERENCE**.
- Mandatory or representation failure: **INELIGIBLE**.
- Eligible but failing one or more support requirements:
  **NOT SUPPORTED**.
- Passing every support requirement: **SUPPORTED**.

### Session-fixing rule

If zero sessions are SUPPORTED:

- **STOP M023 before historical holdout**;
- do not open the holdout;
- do not invent another session.

If exactly one session is SUPPORTED:

- fix that session.

If more than one session is SUPPORTED, calculate relative to S-R:

\`pl_gain_fraction = (candidate_net_pl - reference_net_pl) / abs(reference_net_pl)\`

\`dd_improvement_fraction = (reference_dd - candidate_dd) / reference_dd\`

\`mean_trade_gain_fraction = (candidate_mean_trade_pl - reference_mean_trade_pl) / abs(reference_mean_trade_pl)\`

\`win_rate_gain_fraction = (candidate_win_rate - reference_win_rate) / reference_win_rate\`

\`positive_fold_fraction = positive_net_pl_folds / 5\`

\`positive_symbol_fraction = positive_net_pl_symbols / 5\`

Then:

\`robustness_maximin = minimum of all six values\`

Choose the largest robustness_maximin.

Exact tie-break order:

1. more positive folds;
2. more positive symbols;
3. larger proportion of eligible weeks with improved mean trade P/L;
4. higher representation/activity ratio;
5. broader session duration;
6. lexicographically smaller arm ID.

No alternative ranking is allowed after results.

### Profitability rule

Unlike Stage A, Stage B is not allowed to advance a merely less-negative
session.

The objective is a positive-expectancy session before consuming the untouched
historical holdout.

Therefore both are mandatory:

- \`net P/L > 0\`;
- \`mean trade P/L > 0\`.

If no session clears both plus all frozen robustness gates, do not open
historical holdout.

### Implementation sequence

After this docs-only Stage-B protocol-freeze commit exists:

1. implement experiment-only session entry eligibility;
2. leave production defaults unchanged;
3. add exact tests for:
   - S-R all-hours;
   - S-ACTIVE;
   - S-MORNING;
   - S-MIDDAY;
   - S-AFTERNOON;
   - exact BUY-only direction;
   - zero SELL entries;
   - exact time boundaries;
   - no forced session-end close;
   - continued open-position management outside entry windows;
   - exact research partition;
   - holdout refusal;
   - deterministic reporting;
4. add only fixed local-control actions for:
   - Stage-B reference-equivalence/family execution;
   - Stage-B mechanical assessment;
5. do not add historical-holdout execution;
6. do not add weekday execution;
7. run native Stage-B tests;
8. sync Dell to exact feature SHA;
9. confirm clean worktree, divergence 0/0, exact feature SHA;
10. run S-R first and require exact D-B equivalence;
11. only after reference equivalence PASS, run the four fixed non-reference
    sessions;
12. maximum concurrent non-reference arms: **2**;
13. review deterministic/safety evidence;
14. run frozen mechanical Stage-B assessment;
15. mechanically fix exactly one supported session or zero sessions and STOP;
16. durably document Stage-B result;
17. **STOP**.

### Holdout checkpoint

Even if Stage B produces a supported profitable session, do not immediately
execute historical holdout.

First durably record:

- exact supported session;
- exact parameters;
- exact direction;
- exact Stage-B economics;
- exact robustness evidence;
- exact prospective final holdout acceptance criteria.

Historical-holdout opening requires a separate reviewer checkpoint.

### Weekday filtering

Still unauthorized.

The accepted diagnostic did not support weekday filtering.

Do not use Stage-B outcomes to start weekday mining.

### Hard boundaries

Do not:

- reconsider SELL after the frozen Stage-A result;
- restore BOTH as a competing Stage-B direction;
- add another session;
- optimize arbitrary hours;
- test weekdays;
- inspect historical holdout;
- inspect M021 for tuning;
- add M15;
- change production defaults;
- merge to main;
- deploy;
- enable live trading;
- place, modify, or close real MT5 orders;
- expose arbitrary shell execution.


## Stage B accepted result — M023 closeout

Stage-B implementation feature SHA:

`f5cd1111d4626bd96e11dc9b630cdac364059a04`

Native Stage-B test result:

`8c9c245a4e114298e95a80e88a494c363ab9bfa9`

Preflight/sync result:

`806bb5a776d55c36aba71f2f42509f105398d248`

Stage-B deterministic family result:

`0c91e8fad993c9ab2f9075bf0d3b28dcda718249`

Frozen mechanical assessment command:

`mamba2-m023-stage-b-session-assessment-v1`

Assessment result:

`42630379450fa3b20d7fd24c5bc2decf83dddf46`

Assessment status:

`ok: true`

S-R reproduced the accepted D-B reference exactly across the frozen economic,
per-symbol, fold, EAT, drawdown, win-rate, and TP-safety checks.

### Exact Stage-B economics

| Arm | Closed trades | Net realized P/L | Mean trade P/L | Max DD USD | Win rate |
|---|---:|---:|---:|---:|---:|
| S-R | 6,630 | -$7,453.88 | -$1.12427 | $7,497.01 | 36.6737% |
| S-ACTIVE | 3,881 | -$1,687.54 | -$0.43482 | $2,095.95 | 38.8402% |
| S-MORNING | 1,256 | -$802.82 | -$0.63919 | $1,063.48 | 35.8566% |
| S-MIDDAY | 930 | -$53.41 | -$0.05743 | $453.56 | 42.2581% |
| S-AFTERNOON | 946 | -$281.73 | -$0.29781 | $508.04 | 39.7463% |

All four non-reference session arms passed mandatory and representation gates,
but every arm failed the prospectively frozen requirement that both:

- net realized P/L be strictly positive; and
- mean closed-trade P/L be strictly positive.

Mechanical classifications:

- **S-R — REFERENCE**
- **S-ACTIVE — NOT SUPPORTED**
- **S-MORNING — NOT SUPPORTED**
- **S-MIDDAY — NOT SUPPORTED**
- **S-AFTERNOON — NOT SUPPORTED**

Mechanical result:

- supported Stage-B sessions: **0**;
- fixed session: **none**;
- historical-holdout execution authorized: **false**.

S-MIDDAY was nearest to break-even, but the frozen protocol does not permit
advancing a merely less-negative session.

### M023 safety/isolation closeout

The assessment confirms:

- no new economic replay during assessment;
- existing Stage-B artifacts only;
- historical holdout economic data used: **no**;
- M021 post-cutoff data used: **no**;
- weekday filter run: **no**;
- real-order API called: **no**.

Therefore M023 is **CLOSED** before historical holdout. Do not add another
session, optimize hours, revive SELL/BOTH, test weekdays, or open the M022/M023
historical holdout under M023.

The next research milestone is **M024 — Symbol Specialization Research**.
