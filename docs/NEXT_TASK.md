# Next Authorized Task

## Milestone 024 — Stage 2 causal USDJPY specialization

Branch:

`symbol-specialization-research`

The read-only diagnostic is accepted.

Accepted diagnostic feature SHA:

`f403124a31464f6b42768f6a1d985abe290cbc4c`

Accepted diagnostic result:

`0473b8f149a15516c6d7b4e2f1b0585482be7eef`

Accepted diagnostic artifact SHA-256:

`108752dfdb7430efb2c3b4b971d16d6affb1c43e2aacc1bc5ef8e276db2d6410`

Full native acceptance:

`1bed8eb23b6bca980d076dbf9173f6479f53239d`
— **283 passed, 2 skipped**.

Stage-2 protocol is frozen in:

`docs/milestones/024-symbol-specialization-research.md`

## Exact Stage-2 family

- C-R — all five strategy symbols; all-five market data.
- C-UJ — USDJPY strategy only; all-five market data retained.

Use exact accepted P2-08 BUY-only/all-hours settings and the same frozen
225-date seen-research partition.

## Implement now

1. implement experiment-only causal strategy-symbol selection;
2. add exact C-R/C-UJ tests;
3. ensure C-UJ retains all-five market/conversion data but instantiates only
   USDJPY strategy;
4. expose only fixed Stage-2 family + mechanical-assessment local-control
   actions;
5. do not expose historical holdout execution;
6. run focused native tests;
7. sync Dell to exact feature SHA;
8. run C-R first and require exact accepted D-B equivalence;
9. only then run C-UJ;
10. run frozen mechanical Stage-2 assessment;
11. run full native regression;
12. durably document the result;
13. stop before holdout.

Do not add symbol subsets, sessions, weekdays, SELL/BOTH, M15, M020-D spread
filtering, or parameter changes.

Do not inspect historical holdout or M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not modify production defaults.
Do not merge/deploy or enable real trading.
