# Milestone 023 — Direction and Session Research

Status: **OPEN — DIAGNOSTIC-ONLY GATE FROZEN; NO FILTERED M023 REPLAY AUTHORIZED**

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
