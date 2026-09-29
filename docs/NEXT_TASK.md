# Next Authorized Task

## Milestone 025 — public FX strategy benchmark fidelity review

M024 is closed.

Terminal M024 assessment:

**HOLDOUT NOT SUPPORTED**

Do not retune or rerun H-UJ on the consumed M024 holdout.

The next independent research track is M025:

`public-strategy-benchmarks`

Current M025 work is not yet accepted.

Before any M025 historical benchmark economics, perform a science-fidelity
review of the benchmark definitions and data gates, especially:

1. verify the exact Moskowitz/Ooi/Pedersen TSMOM ex-ante volatility formula
   against the original source;
2. confirm whether the implementation must use EWMA of squared returns rather
   than weighted variance around a weighted mean;
3. verify exact sign/formation/holding conventions;
4. verify Menkhoff et al. currency-momentum portfolio construction;
5. verify HML-FX carry requirements and reject any price-only substitute;
6. confirm minimum cross-sectional-universe and evaluation-history data gates;
7. patch tests/docs before accepting Stage 1 machinery;
8. run no historical benchmark economics until those definitions are frozen.

Do not use M024 holdout outcomes to tune M025 benchmark definitions.
Do not merge/deploy or enable real trading.
