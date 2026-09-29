# Milestone 025 — Public FX Strategy Benchmarks

Status: **STAGE 2 INVENTORY ACCEPTED — NO PUBLIC/FREE RAW-ELIGIBLE SOURCE; NO ECONOMIC RESULTS AUTHORIZED**

Protocol date: 2026-09-29

Branch:

`public-strategy-benchmarks`

Base commit:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

M025 is intentionally independent of M023. It must not read, branch from, tune
against, or otherwise use M023 outcomes. M021 remains frozen and untouched.

## Objective

Implement public, literature-defined FX benchmark strategies beside Mamba2 so
future research can ask whether the existing strategy adds value relative to
simple documented anomalies.

M025 is not a search for a profitable parameter combination. Strategy
definitions are fixed from published research before any M025 economic result is
inspected.

## Frozen benchmark families

### B1 — MOP-TSMOM-12-1

Source definition: Moskowitz, Ooi, and Pedersen (2012), Time Series Momentum.

Frozen mechanics:

- formation horizon: **12 months**;
- holding/rebalance horizon: **1 month**;
- direction: long when the instrument's trailing 12-month excess return is
  positive, short when negative;
- per-instrument ex-ante annualized volatility target: **40%**;
- volatility estimator: exponentially weighted variance of lagged **daily** returns around the exponentially weighted lagged-return mean;
- annualization scalar: **261**;
- EWMA decay: `delta = 60 / 61`, matching a 60-day center of mass;
- the volatility estimate at time `t` may use information only through
  `t-1`.

Publication-faithful execution requires an excess-return/forward-compatible
currency return series. A spot-price-only implementation must be labelled
**TSMOM SPOT PROXY**, never silently presented as the paper's exact futures or
forward strategy.

No alternate lookback, holding period, target volatility, or volatility
estimator is authorized in M025.

### B2 — MSSS-CURRENCY-MOMENTUM

Source definition: Menkhoff, Sarno, Schmeling, and Schrimpf (2012), Currency
Momentum Strategies.

Frozen benchmark variants:

- **MOM(1,1)**;
- **MOM(6,1)**;
- **MOM(12,1)**.

Frozen mechanics:

- month-end formation;
- rank currencies by lagged currency **log excess return** over the fixed formation
  horizon; multi-month formation returns are additive sums of monthly log excess
  returns;
- split the available cross-section into **six** deterministic portfolios;
- long the highest-return portfolio;
- short the lowest-return portfolio;
- holding period: **1 month**;
- equal weight currencies inside each extreme portfolio;
- rebalance monthly.

No formation horizon other than 1, 6, or 12 months is authorized in M025.

Publication-faithful economics require monthly spot and one-month forward data
(or an equivalent directly observed excess-return series) and a sufficiently
broad currency cross-section. The existing five Mamba2 symbols are not a valid
six-portfolio currency universe and must fail the data gate.

### B3 — HML-FX-CARRY

Source definition: Lustig, Roussanov, and Verdelhan (2011), *Common Risk Factors in Currency Markets*. Sort currencies into six portfolios on the one-month forward discount (equivalently, under covered interest parity, the short-term interest-rate differential) and define HML-FX as portfolio 6 minus portfolio 1.

Frozen mechanics:

- month-end sort;
- **six** deterministic portfolios;
- short the lowest-carry portfolio;
- long the highest-carry portfolio;
- equal weight currencies inside each extreme portfolio;
- hold/rebalance monthly.

No price-only substitute for carry is permitted. Carry economics require
observed one-month forward discounts or corresponding short-term rate
differentials.

### B4 — MAMBA-M020D-SNAPSHOT

The internal comparator is frozen now, before M023 completes:

- stochastic: 21 / 7 / 7;
- boundaries: 20 / 80;
- EMA: 7;
- ATR: 14 on M5;
- ATR SL/TP: 1.0 / 2.0;
- decision-time spread rule: reject new submissions only when spread is
  **>10 points**;
- all hours;
- both BUY and SELL.

This comparator is the accepted M020-D research candidate, not a claim that it
is production-safe or profitable. M023 outcomes may later be reported
separately but may not replace this frozen M025 comparator.

## Data sufficiency gates

Before any benchmark economics:

### TSMOM

Require:

- daily observations with deterministic calendar handling;
- at least **5 complete consecutive years** of usable history after cleaning;
- at least 12 months of pre-signal history before the first eligible trade;
- no forward filling across missing trading observations;
- explicit source, timezone/calendar, instrument convention, and hashes.

A 10+ year dataset is preferred, but M025 mechanically blocks only below five
complete years.

### Cross-sectional momentum and carry

Require:

- at least **12 distinct foreign currencies versus one common base currency**
  at every evaluated month;
- monthly spot observations;
- monthly one-month forward observations or directly observed excess returns;
- carry additionally requires observed forward discount / short-rate
  differential;
- at least **5 complete consecutive years** after the common-universe gate;
- deterministic treatment of missing currencies and ties;
- bid/ask or other transaction-cost inputs must be separately labelled; costs
  may not be invented.

The current five-symbol MT5 universe must be classified **INSUFFICIENT** for
B2/B3.

## Stage 1 authorization

Stage 1 may only:

1. implement deterministic pure benchmark-signal/portfolio machinery;
2. implement data-audit and sufficiency gates;
3. add synthetic/unit tests for no-lookahead, exact parameter constants,
   deterministic ranking, and data-gate refusal;
4. add a spot-proxy label/path for TSMOM without running economic research;
5. preserve all M019/M020/M021/M022 behavior and artifacts.

Stage 1 must not:

- run benchmark economics on historical market data;
- inspect M022 historical holdout for M025;
- inspect M021 post-cutoff data;
- read M023 results;
- source-select or parameter-select based on profitability;
- add local-control economic actions;
- merge to main;
- deploy;
- enable or place real MT5 orders.

## Stage 1 acceptance

Stage 1 closes only when:

- exact public benchmark constants are regression-tested;
- future-data mutation cannot change earlier TSMOM volatility/signals;
- six-portfolio momentum and carry ranking is deterministic;
- insufficient universe/history fails before economic calculation;
- current five-symbol universe is explicitly rejected for B2/B3;
- no existing production strategy defaults change;
- full native tests pass.

Only after Stage 1 acceptance may a separate, prospectively frozen data-source
inventory gate be authorized.


## Stage-1 fidelity review — 2026-09-29

No M025 historical economics had been run before this review.

Primary-source reconciliation:

- Moskowitz, Ooi, and Pedersen (2012), *Time Series Momentum*:
  the ex-ante variance is an exponentially weighted variance of lagged daily
  returns around the exponentially weighted mean, annualized by 261, with
  delta chosen so the center of mass is 60 days. Therefore the existing
  centered EWM-variance implementation is retained and is now regression-tested
  against the explicit weighted-mean/weighted-variance equation.
- Menkhoff, Sarno, Schmeling, and Schrimpf (2012), *Currency Momentum
  Strategies*:
  monthly currency excess returns are log returns derived from spot and
  one-month forward rates. Formation returns over f months must therefore be
  additive sums of monthly log excess returns. The prior Stage-1 implementation
  incorrectly compounded them as arithmetic returns; this is a fidelity bug,
  not a parameter change.
- Lustig, Roussanov, and Verdelhan (2011), *Common Risk Factors in Currency
  Markets*:
  HML-FX is the excess-return spread between the sixth (highest forward
  discount / highest interest-rate) and first (lowest) of six monthly
  forward-discount-sorted currency portfolios.

Data-gate clarification:

- "five complete years + 12-month warmup" means one consecutive eligible run,
  not a count of scattered eligible months;
- monthly cross-sectional inputs must have at most one observation per calendar
  month;
- no forward filling is introduced.

These corrections occur before any M025 economic replay and therefore preserve
the prospective benchmark-research boundary.


## Stage-1 fidelity implementation checkpoint — 2026-09-29

Primary-source fidelity repair commit:

`35775c872ef83fa161732f7975ef3c0513e1b847`

Fixed local-control Stage-1 support:

`6c5342e804c24f9a4ca8ee2b46f7991192713839`

Feature changes at the fidelity-repair commit:

- Menkhoff multi-month formation returns now sum monthly **log excess
  returns**;
- MOP ex-ante volatility remains a centered EWM variance and is now tested
  against an explicit finite-history implementation of the paper equation;
- cross-sectional sufficiency now requires a consecutive 72-month eligible run
  (12-month warmup + 60 evaluation months);
- TSMOM sufficiency requires a consecutive 72-month usable run for each
  instrument;
- duplicate calendar-month rows are rejected for monthly cross-sectional
  inputs;
- M025 numbering and HML-FX source attribution are corrected.

Fixed local-control actions:

- `m025_switch_public_benchmarks`;
- `m025_public_benchmark_tests`.

No M025 historical economics have run.

### Recovery sequence

1. switch Dell with `m025_switch_public_benchmarks`;
2. require exact remote feature HEAD and clean 0/0;
3. run `m025_public_benchmark_tests`;
4. if focused tests pass, run `test_full_native`;
5. review failures without weakening literature definitions or data gates;
6. durably accept Stage 1 only after focused + full native pass;
7. stop before any data-source inventory or benchmark economics.


## Stage-1 acceptance — 2026-09-29

Primary-source fidelity implementation:

`35775c872ef83fa161732f7975ef3c0513e1b847`

Test-fixture-only repair:

`d2a6b1b1c2e4e6894e4564c615475ee4df571d55`

Fixed local-control Stage-1 support:

`6c5342e804c24f9a4ca8ee2b46f7991192713839`

First focused run:

`446ebdaf8b100fda2ae7b6c1f925a48672847098`

It reached **22 passed / 1 failed**. The sole failure was a synthetic fixture
that duplicated the exact timestamp, causing the pre-existing unique-index
guard to fire before the newer duplicate-calendar-month guard. No scientific
or benchmark behavior failed.

Accepted focused run after fixture correction:

`a9d4ce84b5cc35e911407082c056c24668b79401`

Focused result:

**23 passed / 0 failed**

Final full native regression:

`28a5c79dd49e10f1255a97bc24a05b0df721bb1b`

Final full native result:

**260 passed / 2 skipped**

Exact accepted Stage-1 feature SHA:

`d2a6b1b1c2e4e6894e4564c615475ee4df571d55`

Stage-1 safety:

- M025 historical benchmark economics: **not run**;
- M021 post-cutoff outcomes: **unused**;
- M023 outcomes: **unused**;
- M024 holdout outcomes used to define/tune benchmarks: **no**;
- production defaults changed: **no**;
- real-order API: **unused**.

Stage 1 is accepted.


## Stage-2 data-source inventory protocol freeze — 2026-09-29

Status: **FROZEN BEFORE ANY M025 BENCHMARK ECONOMICS**

Stage 2 is a source/metadata gate only. It does not authorize strategy-return
calculation.

### Objective

Identify whether accessible historical data exist that can support the already
frozen B1/B2/B3 benchmark definitions without substituting economically
different inputs.

No source may be preferred because of its returns.

### Inventory classifications

Each candidate source/series must receive exactly one classification:

- **RAW-ELIGIBLE-CANDIDATE** — fields/frequency/history/universe can support
  the frozen publication-faithful calculation, subject to later deterministic
  ingestion validation;
- **DERIVED-REFERENCE-ONLY** — published portfolio/factor return series useful
  for external reference/equivalence checks but insufficient to reconstruct
  the frozen raw benchmark;
- **PROXY-ONLY** — can support an explicitly labelled proxy such as
  `TSMOM SPOT PROXY`, but not publication-faithful economics;
- **INSUFFICIENT** — missing required fields/history/universe;
- **UNAVAILABLE/RESTRICTED** — source exists but cannot be accessed under the
  current public/free research boundary.

No ranking among eligible sources based on economic performance is allowed.

### B1 — MOP TSMOM inventory requirements

A RAW-ELIGIBLE-CANDIDATE must provide:

1. daily returns or prices from a futures/forward-compatible currency
   instrument whose excess-return convention can be stated exactly;
2. enough raw information to construct daily excess returns without inventing
   financing/carry;
3. at least 72 consecutive usable calendar months per evaluated instrument
   (12-month warmup + 60 evaluation months);
4. stable instrument identifiers and roll/contract convention where futures
   are used;
5. source timezone/calendar documentation;
6. no synthetic forward filling across missing observations;
7. reproducible access metadata and source hashes once ingested.

Spot-only daily prices are **PROXY-ONLY**.

A published TSMOM factor return series is **DERIVED-REFERENCE-ONLY** unless it
contains the instrument-level raw data required by the frozen signal and
volatility calculation.

### B2 — currency momentum inventory requirements

A RAW-ELIGIBLE-CANDIDATE must provide, for a common base currency:

1. at least 12 distinct foreign currencies in every evaluated month;
2. end-of-month spot rates;
3. one-month forward rates or directly observed monthly currency **log excess
   returns**;
4. at least 72 consecutive eligible months;
5. quote convention sufficient to reproduce the U.S./base-investor return
   sign;
6. deterministic currency identifiers through redenominations/euro entry;
7. missing-data and availability metadata.

A spot-only cross-section is **INSUFFICIENT** for publication-faithful B2.

### B3 — HML-FX carry inventory requirements

A RAW-ELIGIBLE-CANDIDATE must satisfy the B2 cross-sectional requirements and
also provide either:

- observed one-month forward discounts; or
- corresponding directly observed short-term rate differentials with an
  explicit covered-interest-parity convention.

Price momentum, trailing spot returns, or an inferred carry score from price
history are not permitted substitutes.

A published HML-FX factor/portfolio series is
**DERIVED-REFERENCE-ONLY** unless currency-level formation data are also
available.

### B4 — internal M020-D comparator

The accepted M020-D snapshot remains the fixed internal comparator.

Stage 2 may inventory its already-accepted source/artifact references but may
not rerun or retune M020-D.

### Source evidence to record

For every candidate source record:

- source/publisher;
- public URL or canonical identifier;
- access status;
- license/reuse limitation where visible;
- raw versus derived;
- fields;
- frequency;
- first/last available dates where documented;
- currency/instrument universe where documented;
- base/quote convention;
- forward/interest-rate availability;
- transaction-cost fields if any;
- whether the 72-month gate is plausibly satisfiable;
- classification;
- exact reason for classification;
- date the source metadata were checked.

Do not record strategy P/L, Sharpe ratio, drawdown, winning periods, or other
candidate economic outcomes during this gate.

### Stop rule

If no public/free RAW-ELIGIBLE-CANDIDATE exists for a publication-faithful
benchmark family, record that fact and stop that family at the data gate.

Do not weaken the benchmark or silently substitute spot data.

A PROXY-ONLY TSMOM path may proceed later only under its explicit proxy label
and under a separately frozen execution protocol.

### Stage-2 authorized sequence

1. prospectively freeze this inventory protocol;
2. inspect public source documentation/metadata only;
3. publish a deterministic source-inventory document/artifact;
4. independently review classifications against the frozen field gates;
5. do not download/compute benchmark return panels yet unless needed solely to
   prove schema/access and explicitly authorized in a later ingestion gate;
6. freeze a separate ingestion/economic protocol only for
   RAW-ELIGIBLE-CANDIDATE sources that survive inventory;
7. stop before economics.


## Stage-2 source-inventory result — 2026-09-29

Deterministic inventory artifact:

`docs/research/m025-public-source-inventory.md`

Inventory decision:

- B1 MOP TSMOM: **no public/free RAW-ELIGIBLE-CANDIDATE established**;
- B2 Menkhoff momentum: **no public/free RAW-ELIGIBLE-CANDIDATE established**;
- B3 HML-FX carry: **no public/free RAW-ELIGIBLE-CANDIDATE established**;
- B4 M020-D: accepted frozen internal reference only.

Non-raw paths retained without weakening definitions:

- AQR TSMOM factor datasets — **DERIVED-REFERENCE-ONLY**;
- Roussanov/Lustig/Verdelhan CurrencyPortfolios.xls —
  **DERIVED-REFERENCE-ONLY**;
- Federal Reserve H.10 / Dukascopy spot —
  **PROXY-ONLY** for a separately labelled TSMOM spot proxy.

The frozen Stage-2 stop rule fires for publication-faithful B1/B2/B3 raw
reconstruction.

No M025 benchmark economics were run during source inventory.


## Stage-3 reference/proxy evidence protocol freeze — 2026-09-29

Status: **FROZEN BEFORE ANY STAGE-3 ECONOMIC DOWNLOAD/CALCULATION**

Stage-2 inventory acceptance:

`efbf59094ff226542201a32963a5e75a1fccd416`

Stage 3 keeps the two surviving evidence types scientifically separate:

1. externally published **DERIVED REFERENCE SERIES**;
2. a locally reconstructed **TSMOM SPOT PROXY**.

Neither may be described as publication-faithful raw reconstruction.

### P1 — Federal Reserve H.10 TSMOM spot proxy

Prospectively selected source:

**Federal Reserve Board H.10 — Daily Foreign Exchange Rates**

The selection is based only on source authority, public access, long history,
stable documented identifiers, and explicit quote convention. No return
outcome was inspected to choose H.10.

Canonical H.10 daily-rate package contains exactly these 23 frozen source
series:

| Currency | H.10 series ID | Source quote |
|---|---|---|
| AUD | H10/H10/RXI$US_N.B.AL | USD per AUD |
| EUR | H10/H10/RXI$US_N.B.EU | USD per EUR |
| NZD | H10/H10/RXI$US_N.B.NZ | USD per NZD |
| GBP | H10/H10/RXI$US_N.B.UK | USD per GBP |
| BRL | H10/H10/RXI_N.B.BZ | BRL per USD |
| CAD | H10/H10/RXI_N.B.CA | CAD per USD |
| CNY | H10/H10/RXI_N.B.CH | CNY per USD |
| DKK | H10/H10/RXI_N.B.DN | DKK per USD |
| HKD | H10/H10/RXI_N.B.HK | HKD per USD |
| INR | H10/H10/RXI_N.B.IN | INR per USD |
| JPY | H10/H10/RXI_N.B.JA | JPY per USD |
| MYR | H10/H10/RXI_N.B.MA | MYR per USD |
| MXN | H10/H10/RXI_N.B.MX | MXN per USD |
| NOK | H10/H10/RXI_N.B.NO | NOK per USD |
| ZAR | H10/H10/RXI_N.B.SF | ZAR per USD |
| SGD | H10/H10/RXI_N.B.SI | SGD per USD |
| KRW | H10/H10/RXI_N.B.KO | KRW per USD |
| LKR | H10/H10/RXI_N.B.SL | LKR per USD |
| SEK | H10/H10/RXI_N.B.SD | SEK per USD |
| CHF | H10/H10/RXI_N.B.SZ | CHF per USD |
| TWD | H10/H10/RXI_N.B.TA | TWD per USD |
| THB | H10/H10/RXI_N.B.TH | THB per USD |
| VES | H10/H10/RXI_N.B.VES | VES per USD |

No H.10 dollar indexes enter the proxy.

#### Frozen normalization

Every source series is normalized to:

**USD value of one foreign-currency unit**

Therefore:

- AUD/EUR/NZD/GBP: keep source observation unchanged;
- all other frozen series: normalized price = `1 / source_rate`.

No sign or quote convention may be changed after economics.

#### Frozen data handling

- use only source observation dates;
- source `ND`/missing values become missing observations;
- do not forward-fill or backward-fill missing observations;
- do not interpolate;
- do not synthesize weekend/holiday observations;
- normalized prices must be finite and strictly positive;
- duplicate source dates are invalid;
- source rows are sorted chronologically;
- preserve source series identifiers and original quote convention in metadata.

The ingestion gate must freeze the downloaded bytes SHA-256 and a normalized
panel SHA-256 before any proxy return is calculated.

#### Frozen history / universe gate

The **source universe is exactly the 23 series above**.

Each instrument must have a consecutive source history sufficient for:

- 12 months pre-signal formation history; and
- at least 60 subsequent complete evaluation months.

The complete source panel must therefore demonstrate the Stage-1
72-consecutive-month gate before proxy economics.

An instrument may not be removed because of its later performance.

If an instrument fails the predeclared data gate, the ingestion result must
name it and classify P1 as **DATA GATE FAILED** unless a protocol-defined
source-level reason proves that the H.10 series itself is discontinued or
structurally unavailable. No economic subset search is allowed.

#### Frozen P1 strategy semantics

Label every artifact/result:

**TSMOM SPOT PROXY — FED H.10**

For each eligible normalized spot-price series:

1. compute simple spot returns with no fill;
2. use the already accepted MOP Stage-1 mechanics:
   - 12-month formation;
   - 1-month hold/rebalance;
   - centered ex-ante EWMA daily volatility;
   - `delta = 60/61`;
   - annualization = 261;
   - 40% per-instrument target volatility;
   - volatility information only through `t-1`;
3. long when the trailing 12-month spot return is positive;
4. short when negative;
5. a zero signal receives zero directional exposure;
6. a non-finite/non-positive volatility observation is ineligible for that
   formation month; no volatility floor or leverage cap may be invented;
7. apply the month-end formation weight only to the following month;
8. form the proxy portfolio as the equal-weight mean of valid
   volatility-scaled instrument returns for the month.

No currency is weighted or excluded based on realized performance.

#### Costs and financing

H.10 supplies reference spot rates, not executable bid/ask/forward funding.

Therefore P1 is reported:

**GROSS SPOT-PRICE PROXY / TRANSACTION COSTS UNMODELED / CARRY AND FINANCING UNMODELED**

Do not invent spreads, commissions, swaps, or financing.

This limitation must accompany every economic result.

### R1 — AQR TSMOM derived reference

Canonical reference:

**AQR — Time Series Momentum: Factors, Monthly**

Use the published **currency TSMOM factor** only if ingestion/schema inspection
can identify a currency-specific monthly factor unambiguously.

If the downloadable artifact contains only a combined all-asset factor, classify
the currency-reference comparison as **SCHEMA INELIGIBLE** rather than silently
using the combined factor.

Do not reconstruct AQR's underlying positions.

### R2 — LRV currency-portfolio derived reference

Canonical reference:

**Lustig / Roussanov / Verdelhan — CurrencyPortfolios.xls**

Use the published six currency portfolio return series only after a
schema-only ingestion gate identifies P1 through P6 (or an unambiguous
equivalent).

Reference HML-FX is frozen as:

**P6 − P1**

If the sheet already publishes HML-FX, verify its identity against P6 − P1
before using it.

Do not treat these portfolio returns as raw spot/forward formation data.

### R3 — M020-D internal reference

Use only the already accepted M020-D snapshot/artifact hashes.

Do not rerun M020-D in Stage 3.

### Frozen economic summary metrics

For every monthly derived-reference or proxy return series admitted by a later
execution gate, report exactly:

- first/last included month;
- observation count;
- arithmetic mean monthly return;
- annualized arithmetic mean = `12 * monthly_mean`;
- annualized volatility = `sqrt(12) * sample_std(ddof=1)`;
- annualized Sharpe = annualized mean / annualized volatility;
- cumulative wealth from 1.0 by `cumprod(1 + r)`;
- maximum drawdown of that cumulative-wealth series;
- positive-month fraction.

No metric may be used to retune benchmark definitions.

### Frozen cross-series comparisons

Only when two series overlap in calendar months, report:

- exact common-window start/end/count;
- zero-lag Pearson correlation of monthly returns;
- annualized mean-return difference:
  `12 * mean(proxy - reference)`;
- annualized tracking error:
  `sqrt(12) * std(proxy - reference, ddof=1)`.

Do not optimize lags, scaling, signs, subperiods, or currency subsets to improve
correlation.

P1 may be compared with R1 only if R1 is a currency-specific TSMOM factor.

R2 HML-FX remains a standalone derived reference because no B3 raw/proxy
reconstruction is authorized.

R3 M020-D remains an internal accepted snapshot and is not forced into a
monthly return correlation comparison unless an already-accepted monthly
artifact exists.

### Stage-3 deterministic artifacts

Before economics, a separate ingestion gate must publish deterministic:

- source download URL/identifier;
- retrieval timestamp;
- raw source SHA-256;
- parsed/schema metadata;
- normalized panel SHA-256 where applicable;
- exact included source IDs/columns;
- first/last raw observation metadata;
- missing-value counts;
- 72-month gate result;
- no-economic-computation safety assertion.

Economic execution is unauthorized until those ingestion artifacts are
accepted.

### Stop / contamination rules

- no source replacement after seeing returns;
- no H.10 currency removal based on performance;
- no lookback/hold/vol-target/estimator change;
- no leverage cap/volatility floor invented after outcomes;
- no transaction-cost estimate invented after outcomes;
- no B2/B3 spot-only substitute;
- no M021 post-cutoff use;
- no M023/M024 outcome use to alter benchmark definitions;
- no production/live promotion.

Any later economic result is research evidence only.
