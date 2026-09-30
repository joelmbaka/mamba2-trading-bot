# Milestone 026 — Tradeable FX TSMOM Reconstruction

Status: **STAGE 0 SOURCE-FIDELITY PROTOCOL FROZEN — NO ECONOMICS AUTHORIZED**

Protocol date: 2026-09-30

Branch:

`tradeable-fx-tsmom-reconstruction`

Base commit:

`63a64db5edc75639fdc85d4790231023aa3e9392`

## Why M026 exists

M024's USDJPY specialization failed its one-shot historical holdout and is
closed. Its consumed holdout must not be reused.

M025 established two materially different facts:

1. the locally reconstructed Federal Reserve H.10 price-only TSMOM proxy is not
   publication-faithful because it omits futures/forward excess-return and
   financing/carry mechanics;
2. the externally published AQR `TSMOM^FX` derived reference has positive
   long-run economics, but a derived factor file is not itself a raw,
   independently reconstructed tradeable strategy.

M026 therefore asks one narrow question:

> Can a public/free, reproducible raw-data path support a publication-faithful
> FX time-series-momentum reconstruction with explicit excess-return mechanics
> and a defensible execution/cost contract?

M026 is not a parameter search and is not an attempt to rescue M024 or retune
M025.

## Frozen strategy family

Only one family is admitted:

**Moskowitz, Ooi, Pedersen-style FX time-series momentum, 12-month formation /
1-month holding.**

The frozen signal/economic constants inherited from the pre-economic M025
fidelity review are:

- trailing excess-return formation horizon: **12 months**;
- rebalance/holding horizon: **1 month**;
- long when trailing 12-month instrument excess return is positive;
- short when negative;
- per-instrument ex-ante annualized volatility target: **40%**;
- volatility estimator: centered exponentially weighted variance of lagged
  daily excess returns;
- annualization scalar: **261**;
- EWMA decay: `60 / 61`;
- no information later than `t-1` may enter the volatility estimate at
  decision time `t`.

No alternate lookback, holding period, target volatility, decay, sign rule, or
volatility estimator may be introduced inside M026 after source inspection.

Exact portfolio aggregation, roll timing, and transaction-cost mechanics must
be frozen in a later pre-economic stage after a raw source is selected on
metadata/fidelity grounds only.

## Stage 0 — source-fidelity inventory only

Stage 0 may inspect source documentation, metadata, schemas, access terms,
coverage, calendars, and instrument conventions.

Stage 0 must not download or calculate a strategy return series except where a
small non-economic schema sample is strictly necessary to prove field meaning.
It must not calculate P/L, Sharpe, drawdown, win rate, or compare candidate
source economics.

### Source classes

Every candidate must receive exactly one classification.

**A — RAW FUTURES CANDIDATE**

Must expose enough contract-level information to reconstruct daily FX futures
excess returns without inventing carry:

- settlement/close field with documented meaning;
- contract identifier and expiry;
- deterministic roll inputs/convention;
- stable currency contract specification;
- daily calendar/timezone convention;
- at least 72 consecutive usable months for at least one meaningful FX
  instrument set;
- reproducible public/free access.

**B — RAW FORWARD CANDIDATE**

Must expose:

- spot and directly observed FX forward prices, or directly observed currency
  excess returns;
- forward tenor sufficient for the monthly strategy;
- quote/base convention;
- timestamps/calendars;
- at least 72 consecutive eligible months;
- reproducible public/free access.

**C — RATE-BASED RECONSTRUCTION CANDIDATE**

Official spot plus official short-rate data may enter only as a separately
labelled reconstruction candidate. It cannot be called publication-faithful
unless the exact covered-interest-parity timing/convention and investable
excess-return mapping can be frozen without inventing unavailable prices.

**D — DERIVED REFERENCE ONLY**

Published factor/portfolio returns, including AQR `TSMOM^FX`, may be retained
only for later external validation. They cannot supply the raw reconstructed
strategy.

**E — SPOT PROXY ONLY**

Spot-price-only datasets, including Federal Reserve H.10 and Dukascopy spot,
cannot qualify for publication-faithful M026 economics.

**F — UNAVAILABLE / RESTRICTED / INSUFFICIENT**

Use when history, fields, access, contract metadata, universe, or license/access
conditions fail the frozen requirements.

## Mechanical source selection

Source selection is based only on fidelity and reproducibility, in this order:

1. direct raw futures candidate;
2. direct raw forward/excess-return candidate;
3. rate-based reconstruction candidate, only if no A/B source survives.

Within a class, prefer:

1. primary exchange/publisher/official source;
2. explicit field and contract documentation;
3. longest complete history;
4. deterministic immutable downloadability;
5. broadest stable FX universe.

Economic returns may not break ties.

If no A/B/C candidate survives, M026 stops at the data gate.

## Minimum data gate

Before any future M026 strategy economics, the selected raw/reconstruction path
must mechanically demonstrate:

- >=72 consecutive usable calendar months per admitted instrument;
- >=12 months pre-signal history before the first evaluated month;
- no synthetic forward/backward filling;
- explicit quote direction;
- explicit timezone/calendar;
- immutable source snapshot hashes;
- deterministic missing-observation policy;
- no use of M024 consumed holdout or M021 prospective outcomes.

A 10+ year history is preferred but not required by the mechanical minimum.

## Execution/cost boundary

No strategy economics are authorized in Stage 0.

Before economics, a later protocol must freeze one truthful cost treatment:

- directly observed bid/ask or exchange fees/slippage inputs where available; or
- an explicitly labelled gross-before-cost result if real cost inputs are not
  publicly available.

Costs must never be invented or tuned to profitability.

## Independence / anti-overfit rules

M026 may use M025 only as prior evidence motivating the raw-fidelity question.
It may not retune M025 after seeing its economics.

M026 must not:

- reuse the consumed M024 holdout;
- inspect or use M021 post-cutoff economics before M021's own frozen gate;
- filter to USDJPY, JPY pairs, BUY-only, SELL-only, sessions, weekdays, or
  volatility regimes;
- search currency subsets;
- add M15/third-timeframe logic;
- change Mamba2 production defaults;
- merge to main or deploy;
- enable, place, modify, or close real MT5 orders.

## Stage 0 authorized sequence

1. freeze this protocol;
2. inspect current public source documentation/metadata only;
3. publish `docs/research/m026-tsmom-source-inventory.md`;
4. assign exactly one frozen classification to every inspected source;
5. select at most one source path using the mechanical fidelity order above;
6. independently review the selected source against the minimum data gate;
7. stop before strategy economics.

If a source survives, Stage 1 may only implement deterministic ingestion and
schema validation. Stage 2 must freeze exact roll/excess-return/portfolio/cost
semantics before any first economic run.

## Stop rule

Once the first M026 economic output is eventually inspected, M026 may not
change its source, universe, signal constants, roll rule, leverage/volatility
target, cost rule, sign, or calendar based on that result.

Any such change requires a separately named future milestone.
