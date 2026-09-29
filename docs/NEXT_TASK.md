# Next Authorized Task

## M025 — execute Stage-3 non-economic ingestion

Branch:

`public-strategy-benchmarks`

Protocol freeze:

`6b6592237fe4f9e087745c914e916bda6521012d`

H.10 snapshot-range freeze:

`a7fa66244e57c9f0e214526ab8dee9b96537f87c`

Ingestion implementation:

`184f0fbd0e58e0d451120232a2cb9295c729f7f2`

Fixed local-control support:

`cd985e2f29d6814b1aec54ffff1b57b2c9a1ab6a`

Runtime probe:

`315a03a0ba1967d30a884b0fc0d33c39543f6e70`

## Execute exactly

1. sync/fast-forward Dell to exact current M025 feature HEAD;
2. run `m025_stage3_ingestion_tests`;
3. require focused PASS;
4. run `m025_stage3_ingestion` once;
5. require non-economic safety flags;
6. freeze:
   - H.10 raw SHA;
   - H.10 normalized-panel SHA;
   - AQR raw SHA and schema classification;
   - LRV raw SHA and schema classification;
   - ingestion report SHA;
7. stop before returns/economics;
8. freeze a separate Stage-3 economic-execution checkpoint only after
   ingestion acceptance.

## Forbidden

Do not compute returns, P/L, Sharpe, drawdown, wealth, correlations, tracking
error, or rankings.

Do not modify benchmark/proxy definitions after source ingestion.
Do not inspect M021 post-cutoff outcomes.
Do not use M023/M024 outcomes to alter definitions.
Do not merge/deploy or enable real trading.
