# Next Authorized Task

## Milestone 023 — Direction and Session Research

Branch:

`direction-session-research`

Protocol:

`docs/milestones/023-direction-session-research.md`

Closed M022 branch point:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

M022 is closed. Do not reopen or reinterpret it.

M021 remains independently frozen on `prospective-forward-validation`; do not
inspect its outcomes for M023 tuning.

## Current gate

**DIAGNOSTIC ONLY.**

Use only already-seen M022 development + validation deterministic evidence for:

- P2-R;
- P2-03;
- P2-08.

Exclude P2-01 from the main directional comparison because its validation
evidence failed the TP-safety gate.

Do not run fresh filtered strategy economics.

Do not inspect historical holdout:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`.

## Required diagnostic output

For development, validation, and combined descriptive aggregate:

- BOTH;
- SELL only;
- BUY only.

Use DST-aware entry timestamps in:

- UTC;
- Africa/Nairobi;
- Europe/London;
- America/New_York.

Frozen EAT windows:

- EAT-MORNING 08:00–11:59 EAT;
- EAT-MIDDAY 12:00–14:59 EAT;
- EAT-AFTERNOON 15:00–17:59 EAT;
- EAT-EVENING 18:00–20:59 EAT;
- EAT-ACTIVE 08:00–20:59 EAT;
- EAT-OFF-HOURS 21:00–07:59 EAT.

DST-aware market labels:

- London open transition: 07:00–08:59 Europe/London;
- London/New York overlap: both 13:00–16:59 Europe/London and
  08:00–11:59 America/New_York.

Required metrics where present:

- counts, wins/losses/flats, non-flat win rate;
- net/mean/median trade P/L;
- average/median entry spread;
- TP/SL/other exit counts;
- per-symbol counts and P/L;
- weekday breakdown;
- 5 chronological folds of 45 accepted trading dates each.

The analysis must clearly state that slicing old all-hours trades is not
equivalent to replaying a strategy with entry suppression.

## Implementation rule

Prefer existing accepted diagnostic artifacts.

If trade-level fields needed for this gate are not present, add only a narrow,
deterministic, read-only diagnostic over the same already-seen artifacts.

Any Dell-only operation must use fixed allowlisted local-control actions.

No arbitrary shell and no real-order action.

## Deliverable

Publish:

1. diagnostic source references and hashes;
2. EAT/London/New-York direction/time tables;
3. weekday diagnostics;
4. 5-fold chronological stability;
5. a bounded next-stage direction/session matrix **design only**.

Do not execute the future D-R/D-S/D-B or session matrix in this gate.

## Hard boundaries

Do not:

- run new M022 economics;
- run a fresh M023 side/session-filtered strategy replay;
- inspect M022 historical holdout;
- inspect M021 outcomes;
- add M15 as a signal;
- alter production defaults;
- merge to main;
- deploy;
- enable live trading;
- place/modify/close real MT5 orders.
