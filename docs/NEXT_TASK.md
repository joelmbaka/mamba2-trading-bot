# Next Authorized Task

## Milestone 024 — public FX benchmark machinery

Branch:

`public-strategy-benchmarks`

Protocol:

`docs/milestones/024-public-fx-strategy-benchmarks.md`

Base:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

M025 is intentionally independent of M023. Do not read or use M023 outcomes.
M021 remains frozen and must not be inspected early.

## Stage 1 only

Implement deterministic, research-only machinery for the exact frozen benchmark
definitions:

- MOP TSMOM 12-month formation / 1-month hold with 40% per-instrument target
  volatility and the fixed 60-day-center EWMA estimator;
- currency momentum MOM(1,1), MOM(6,1), MOM(12,1), six portfolios, long High /
  short Low;
- HML-FX carry, six portfolios, long highest carry / short lowest carry;
- frozen internal comparator metadata for M020-D.

Implement hard data sufficiency gates:

- TSMOM: minimum five complete usable years plus 12-month warmup;
- cross-sectional momentum/carry: minimum 12 distinct foreign currencies versus
  a common base, minimum five complete years, and required forward/excess-return
  inputs;
- carry additionally requires observed forward discount or rate differential;
- the existing five-symbol Mamba2 universe must fail B2/B3 before economics.

Add focused synthetic tests for:

- constants;
- no lookahead;
- deterministic ranking/ties;
- exact portfolio membership;
- insufficient-history refusal;
- insufficient-universe refusal;
- spot-proxy labelling.

## Prohibited

Do not run any M025 historical economics yet.
Do not add economic local-control actions.
Do not inspect M022 holdout.
Do not inspect M021 post-cutoff data.
Do not read M023 results.
Do not modify production strategy defaults.
Do not merge, deploy, or enable real trading.

After code/tests are committed, run the native focused/full suite only. Stage 1
acceptance must precede any data-source inventory or economic replay.
