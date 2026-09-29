# Next Authorized Task

## Milestone 024 — validate read-only symbol specialization diagnostic

Branch:

`symbol-specialization-research`

Protocol freeze:

`12c8b93af164f24a719fa6151efb54f838659619`

Implemented analyzer commit:

`2a605aebee379e50df7193f9562b84bbb2edb128`

Fixed local-control actions commit:

`b0acf22ff8271a96f926dd9250b85418034053c4`

Accepted M023 D-B source-summary SHA-256:

`7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c`

## Execute in this exact order

1. confirm the Dell is clean and on the exact current
   `symbol-specialization-research` remote HEAD;
2. run `m024_symbol_specialization_tests`;
3. require focused native tests PASS;
4. run `m024_symbol_specialization_diagnostic`;
5. require deterministic A/B artifact hash equality and all safety checks;
6. independently review the four frozen subset classifications;
7. run `test_full_native`;
8. durably record the accepted diagnostic result and exact SHAs;
9. only then decide mechanically whether M024 stops or a separate prospective
   causal symbol-filtered replay protocol may be frozen.

Frozen subsets remain exactly:

- SYM-R — all five;
- SYM-UJ — USDJPY;
- SYM-JPY — EURJPY + GBPJPY + USDJPY;
- SYM-NONJPY — EURUSD + GBPUSD.

Do not run fresh strategy economics.
Do not inspect historical holdout.
Do not inspect M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not add symbol subsets, sessions, weekdays, SELL/BOTH, or M15.
Do not modify production defaults.
Do not merge/deploy or enable real trading.
