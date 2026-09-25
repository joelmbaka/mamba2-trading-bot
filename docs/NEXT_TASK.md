# Next Authorized Task

## Milestone 017 — Baseline diagnosis

Milestone 016 is accepted.

Accepted implementation SHA:

`4d8a15937f461c0e39d434be6639bfde83698d7f`

Accepted baseline report SHA-256:

`d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`

Branch:

`backtest-baseline-diagnosis`

## Objective

Explain the accepted M016 result using deterministic trade-level evidence before changing the strategy.

Do **not** optimize.

Do **not** change strategy parameters, signal conditions, ATR/trailing semantics, spread semantics, execution costs, conversion timing, position size, or end-of-data behavior.

## Source baseline

Reuse the verified M016 dataset:

- `2026-09-01T00:00:00Z` through `2026-09-25T00:00:00Z`
- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY
- M1
- native M5
- native M15
- tick-derived Ask M1

The accepted baseline totals must remain reproducible.

## First task — deterministic diagnostic evidence

Add a deterministic diagnostic artifact or reporting path that exposes enough evidence to explain every closed trade without changing replay decisions or fills.

At minimum capture, where applicable:

- stable order/position identity;
- symbol;
- side;
- entry UTC timestamp and price;
- exit UTC timestamp and price;
- exit reason;
- gross and net realized P/L;
- entry/exit historical Bid/Ask spread;
- ATR/protection state relevant to the trade;
- trailing-stop modifications relevant to the trade;
- account-currency conversion route used when conversion is required;
- UTC session bucket or sufficient timestamps to derive it.

Prefer deriving analysis fields after replay from immutable event/ledger data rather than injecting behavior into the strategy.

## Non-interference gate

Diagnostic instrumentation must not alter the accepted baseline.

Require:

1. the same verified dataset and strategy configuration;
2. aggregate totals reconcile exactly to M016;
3. accepted orders and closed trades remain 1,393 / 1,393;
4. ending realized balance remains `9731.45700985454`;
5. no remaining positions;
6. baseline report remains deterministic;
7. where the existing report format is unchanged, preserve its accepted SHA-256; if a deliberately separate diagnostic artifact is added, keep the accepted baseline report itself unchanged.

## Diagnosis required

After deterministic evidence exists, report descriptive findings for:

- symbol;
- BUY vs SELL;
- UTC session/time-of-day;
- exit reason;
- spread;
- ATR/protection/trailing behavior;
- account-currency conversion route;
- loss clustering and consecutive-loss behavior;
- drawdown episodes.

Do not rank symbols and do not change the strategy during M017.

The goal is to identify evidence-backed hypotheses for later defect review or controlled experiments, not to improve the backtest result yet.
