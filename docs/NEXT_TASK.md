# Next Authorized Task

## M025 — freeze Stage-4 economic execution protocol

Branch:

`public-strategy-benchmarks`

Accepted Stage-3 feature SHA:

`554ab3a827163732f4dec335c716fec2f386bfe8`

Accepted focused tests:

`2d3e36ca14c4a277666a74d4f300a982a19d88be`

Accepted immutable ingestion:

`61bb9c5d591e8519f5bebc024d670204d9a71eab`

Accepted ingestion report SHA:

`d5f05a7aed82d1cac275bcb222913ec61a38f00b2df74b3727e479d7a4324505`

Immutable source hashes:

- H.10 raw:
  `38b941973dd7e6570e590291a34ebd27873ef98c7d09fcb0e3097ee76e793046`
- H.10 normalized:
  `015e61cffd504f61853167bfab1511ecd92c51e87abd21c935ee70b064f43419`
- AQR workbook:
  `33470930e2269c0d97be4732ec2d9c27ddbc69ac8133b059a263e27400263eeb`
- LRV workbook:
  `e08676e399a3c80714e55bd980350892785e8091f483af0784197fd815612d74`

## Freeze before any economics

Write a separate Stage-4 protocol that fixes:

1. exact H.10 normalized-price parsing into
   `TSMOM SPOT PROXY — FED H.10`;
2. exact missing-observation treatment with no fill/interpolation;
3. exact 12/1 signal timing and accepted centered MOP volatility estimator;
4. exact 40% target-volatility scaling and equal-weight aggregation;
5. exact admitted H.10 universe — all 23 frozen currencies;
6. exact AQR `TSMOM^FX` sheet/column and unit convention;
7. exact LRV P1-P6/HML extraction and unit convention;
8. deterministic A/B economic artifact requirements;
9. exact summary/comparison metrics already frozen in the milestone;
10. stop/no-retuning rules after the first economic output.

Add parser/timing tests before execution.

## Still forbidden

Do not compute returns, P/L, Sharpe, drawdown, cumulative wealth, correlation,
tracking error, or economic rankings until the Stage-4 protocol is committed.

Do not change source, universe, sign, scale, lookback, holding period,
volatility target, estimator, or missing-data treatment after economics.

Do not inspect M021 post-cutoff outcomes.
Do not use M023/M024 outcomes to tune M025.
Do not merge/deploy or enable real trading.
