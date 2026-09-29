# Next Authorized Task

## Milestone 025 — public FX benchmark data-source inventory

Branch:

`public-strategy-benchmarks`

Accepted Stage-1 feature:

`d2a6b1b1c2e4e6894e4564c615475ee4df571d55`

Accepted focused tests:

`a9d4ce84b5cc35e911407082c056c24668b79401`
— **23 passed**.

Accepted full native regression:

`28a5c79dd49e10f1255a97bc24a05b0df721bb1b`
— **260 passed, 2 skipped**.

## Stage 2 only

Execute the frozen source-inventory protocol in:

`docs/milestones/025-public-fx-strategy-benchmarks.md`

Inventory public/free candidate data sources for:

- B1 MOP TSMOM;
- B2 Menkhoff currency momentum;
- B3 HML-FX carry;
- B4 accepted M020-D artifact references.

For each source, record publisher/access/raw-vs-derived/fields/frequency/history/
universe/convention/forward-or-rate availability/licensing metadata and apply
exactly one frozen inventory classification.

## Prohibited

Do not calculate benchmark P/L, Sharpe, drawdown, win rate, or economic ranking.
Do not choose a source based on returns.
Do not weaken raw-data requirements because a preferred source is unavailable.
Do not use M021 post-cutoff outcomes.
Do not use M023/M024 outcomes to alter benchmark definitions.
Do not merge/deploy or enable real trading.

After inventory review, stop before ingestion/economics and freeze a separate
protocol for any surviving RAW-ELIGIBLE-CANDIDATE.
