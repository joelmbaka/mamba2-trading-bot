# Next Authorized Task

## Milestone 023 — Stage A causal direction screen

Branch:

`direction-session-research`

Current required pre-Stage-A HEAD:

`810981eba1f82ce051d319784bab1ba3879eda89`

The complete Stage-A numeric protocol must be frozen in the milestone document
before any D-R/D-S/D-B economic replay. After that freeze, implement and
execute only Stage A.

### Frozen research partition

- start: `2025-08-25T00:00:00Z`
- end-exclusive: `2026-07-08T00:00:00Z`
- accepted trading dates: **225**
- ordered date-list SHA-256:
  `50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`

Historical holdout remains sealed from `2026-07-08T00:00:00Z` onward.

### Exact P2-08 anchor

- stochastic 21/7/7;
- boundary 20/80;
- EMA7;
- spread gate none;
- ATR SL1.5;
- ATR TP3.0;
- all hours;
- directional trailing unchanged;
- M15 disabled;
- position size 0.1;
- costs:
  SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED.

### Exact Stage-A matrix

- D-R — BOTH BUY + SELL;
- D-S — SELL entries only;
- D-B — BUY entries only.

Direction overrides alter new-entry eligibility only.

No session filtering. No weekday filtering. No parameter retuning.

### Implementation authorization

After the docs-only Stage-A protocol freeze commit:

1. implement narrow experiment-only direction overrides;
2. add exact Stage-A tests;
3. add only fixed Stage-A family and mechanical-assessment local-control
   actions;
4. run native Stage-A tests;
5. sync the Dell to exact feature SHA;
6. execute D-R first, then D-S/D-B with max two non-reference arms
   concurrently;
7. mechanically assess using the frozen gates;
8. fix exactly one Stage-B direction using the frozen rule;
9. durably document the result;
10. stop before Stage B.

The complete numeric gates, concentration rules, weekly rules, reporting
requirements, and deterministic reduction rule are authoritative in:

`docs/milestones/023-direction-session-research.md`

### Hard boundaries

Do not:

- alter M022 conclusions;
- add a fourth direction arm;
- test sessions during Stage A;
- test weekdays;
- inspect historical holdout;
- inspect M021 outcomes for tuning;
- add M15;
- change production defaults;
- merge to main;
- deploy;
- enable live trading;
- place/modify/close real MT5 orders;
- expose arbitrary shell.
