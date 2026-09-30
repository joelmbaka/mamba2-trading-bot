# Next Authorized Task

## M025 — validate frozen Stage-4 machinery

Branch:

`public-strategy-benchmarks`

Stage-4 protocol:

`6511131792e32e74b6c98ce9de1d11dded5522b7`

Locked parser dependency:

`07facca9a04cc5f8154b7c648208f186326c0f2e`

Stage-4 implementation:

`f74bd6606b91f38a4255d38af6d4770500004ec5`

Fixed focused-test control:

`7ab842c005e45d07c6790ba037a0bd9c1ce86599`

## Execute exactly

1. sync Dell to exact remote feature HEAD;
2. run `m025_stage4_tests`;
3. if focused tests fail, repair only implementation/test defects;
4. require focused PASS;
5. run `test_full_native`;
6. require full native PASS;
7. only then add a fixed immutable `m025_stage4_economics` A/B action;
8. execute that action exactly once;
9. inspect only the frozen summaries/comparison;
10. document and stop.

Do not change any source, universe, sign, scale, lookback, hold period,
volatility target, estimator, sheet, column, missing-data treatment, lag,
comparison window, or metric after economics.

Do not inspect M021 post-cutoff outcomes.
Do not use M023/M024 outcomes to tune M025.
Do not merge/deploy or enable real trading.
