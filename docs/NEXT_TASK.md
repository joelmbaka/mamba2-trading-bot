# Next Authorized Task

## Milestone 024 — validate and execute frozen Stage 2

Branch:

`symbol-specialization-research`

Frozen Stage-2 protocol:

`docs/milestones/024-symbol-specialization-research.md`

Causal runner implementation:

`d0dff1fc66e6bc1b60200a4aeaa27990bd1322fc`

Invariant-hardening repair:

`ea49b23f72b0e857538c77a6f469920248cfde6a`

Fixed local-control support:

`0226b4e807480ed7e754c362d72e0adf05d5f25d`

## Execute exactly

1. sync Dell to exact current remote feature HEAD and require clean 0/0;
2. run `m024_stage2_symbol_tests`;
3. require focused native PASS;
4. run `m024_stage2_symbol_family`;
5. require C-R exact accepted M023 D-B equivalence;
6. only then inspect C-UJ economics;
7. run `m024_stage2_symbol_assessment`;
8. mechanically accept its frozen classification;
9. run `test_full_native`;
10. durably document Stage-2 result;
11. stop before historical holdout.

Exact family remains:

- C-R — all-five strategies + all-five market data;
- C-UJ — USDJPY strategy only + all-five market data.

Do not add subsets, sessions, weekdays, SELL/BOTH, M15, spread filters, or
parameter changes.

Do not inspect/open historical holdout.
Do not inspect M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not modify production defaults.
Do not merge/deploy or enable real trading.
