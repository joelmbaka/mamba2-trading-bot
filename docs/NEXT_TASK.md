# Next Authorized Task

## Milestone 023 — Direction and Session Research

Branch:

`direction-session-research`

Current diagnostic implementation/evidence SHA:

`f925ae8121fb9ce4ee04c1c980e58720c2a611f3`

Protocol freeze:

`099b947f630f26de07f65920c54e98c237dc45bd`

Deterministic diagnostic result:

`30712d1c55e1204fc4d849a38bfa96318155b54b`

Artifact SHA-256:

`0b306c2341befd7110ea2a6695ecd4fc473055fb2231849b5a3741a11251d9a2`

## Current gate

**M023 DIAGNOSTIC GATE IS COMPLETE.**

No filtered M023 strategy replay is currently authorized.

Diagnostic conclusions:

- SELL improvement concentration from M022 does not prove SELL-only is
  intrinsically stronger;
- BUY has the less-negative raw mean trade P/L in 5 of 6 P2-R/P2-03/P2-08
  development/validation comparisons;
- the strongest stable structure is time-of-day:
  EAT-ACTIVE 08:00–20:59 is materially less negative than EAT-OFF-HOURS
  across P2-R, P2-03, and P2-08;
- EAT-ACTIVE mean trade P/L improves versus each arm's all-hours descriptive
  fold in all 5 chronological folds;
- P2-08 SELL London-open transition is a credible secondary session
  hypothesis, but is not yet a strategy filter;
- no weekday filter is supported at this diagnostic gate.

## Proposed next-stage design

Stage A should remain exactly:

- D-R — BOTH;
- D-S — SELL only;
- D-B — BUY only;

on P2-08 as the primary causal research anchor.

**Do not execute Stage A yet.**

Before any Stage-A replay, durably freeze numeric directional robustness gates
appropriate to the new question.

Only after Stage A fixes a direction may Stage B freeze up to four
non-reference session variants plus all-hours reference from the existing
bounded pool.

EAT-ACTIVE has first diagnostic priority because it is the strongest
cross-arm/cross-fold time structure. London-open transition is a secondary
candidate, particularly if SELL survives Stage A.

## Hard stop

Do not:

- execute D-R/D-S/D-B yet;
- execute any session filter;
- execute weekday filtering;
- inspect the untouched historical holdout;
- inspect M021 outcomes for M023 tuning;
- reopen M022 economics;
- add M15;
- modify production defaults;
- merge to main;
- deploy;
- enable or touch real trading.

The next reviewer decision is whether to prospectively freeze the Stage-A
directional robustness protocol and authorize the three-arm causal direction
screen.
