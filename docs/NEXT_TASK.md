# Next Authorized Task

## Milestone 023 — Stage B causal session screen

Branch:

`direction-session-research`

Stage-A acceptance commit precedes this Stage-B freeze.

Fixed Stage-B direction:

**BUY ONLY**

Exact Stage-B matrix:

- S-R — BUY only, all hours;
- S-ACTIVE — BUY only, 08:00–20:59 Africa/Nairobi;
- S-MORNING — BUY only, 08:00–11:59 Africa/Nairobi;
- S-MIDDAY — BUY only, 12:00–14:59 Africa/Nairobi;
- S-AFTERNOON — BUY only, 15:00–17:59 Africa/Nairobi.

No other session may be added.

Use exact P2-08 parameters and the same 225-date seen-research sample:

`2025-08-25T00:00:00Z` → `2026-07-08T00:00:00Z`

Date-list SHA-256:

`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`

The complete frozen representation, profitability, fold/symbol/weekly,
concentration, reduction, and safety rules are authoritative in:

`docs/milestones/023-direction-session-research.md`

## Implementation authorization

1. implement narrow experiment-only session entry eligibility;
2. add exact Stage-B tests;
3. add only Stage-B family/reference-equivalence and mechanical-assessment
   local-control actions;
4. do not expose holdout or weekday execution;
5. run native Stage-B tests;
6. sync Dell to exact feature SHA;
7. run S-R and require exact accepted D-B economic equivalence;
8. only then run the four non-reference sessions with max concurrency 2;
9. run the frozen mechanical Stage-B assessment;
10. mechanically fix one supported session or zero sessions;
11. durably document the result;
12. stop.

Historical holdout remains sealed:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

No historical-holdout execution is authorized in this gate.
