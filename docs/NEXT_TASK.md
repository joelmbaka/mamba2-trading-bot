# Next Authorized Task

## M025 — implement deterministic Stage-3 ingestion gate

Branch:

`public-strategy-benchmarks`

Stage-1 acceptance:

`d2a6b1b1c2e4e6894e4564c615475ee4df571d55`

Stage-2 inventory acceptance:

`efbf59094ff226542201a32963a5e75a1fccd416`

Stage-3 reference/proxy protocol is frozen in:

`docs/milestones/025-public-fx-strategy-benchmarks.md`

## Ingestion only

Implement deterministic, non-economic ingestion/schema validation for:

1. Federal Reserve H.10 exact frozen 23-series daily-rate package;
2. AQR monthly TSMOM reference artifact;
3. LRV `CurrencyPortfolios.xls`.

For H.10, publish before any return calculation:

- exact raw bytes SHA-256;
- exact 23 source IDs;
- source quote conventions;
- normalized USD-per-foreign panel SHA-256;
- first/last observations per series;
- missing counts;
- duplicate/date validity;
- positive finite price checks;
- 72-consecutive-month gate result;
- source and normalized schema metadata.

For AQR:

- raw artifact SHA-256;
- workbook/file schema;
- exact sheet/column names;
- whether a currency-specific monthly TSMOM factor exists;
- no return summary.

For LRV:

- raw artifact SHA-256;
- workbook schema;
- exact sheet/column names;
- whether six currency portfolios P1-P6 are identifiable;
- whether a published HML column exists;
- no return summary.

Add focused synthetic/parser tests and fixed non-economic local-control actions
only.

## Forbidden

Do not calculate:

- strategy/proxy/reference returns;
- P/L;
- Sharpe;
- drawdown;
- cumulative wealth;
- positive-month fraction;
- correlations;
- tracking error;
- economic ranking.

Do not replace H.10 after seeing outcomes.
Do not drop currencies based on outcomes.
Do not inspect M021 post-cutoff outcomes.
Do not alter definitions using M023/M024 outcomes.
Do not merge/deploy or enable real trading.
