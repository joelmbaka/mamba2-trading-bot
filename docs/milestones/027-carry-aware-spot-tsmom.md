# Milestone 027 — Carry-Aware Spot TSMOM Approximation

Status: **STAGE 0 DATA-COVERAGE PROTOCOL FROZEN — NO ECONOMICS AUTHORIZED**

Protocol date: 2026-09-30

Branch:

`carry-aware-spot-tsmom`

Base commit:

`885d9d898292d46cb6c65093cd2fc0d28908791f`

## Objective

Test one explicitly approximate, public/free FX trend strategy after M026 proved
that publication-faithful raw futures/forward history is not available under the
current no-purchase boundary.

M027 is not MOP publication-faithful futures TSMOM.

It is labelled:

**CARRY-AWARE SPOT TSMOM — PUBLIC-DATA APPROXIMATION**

The research question is:

> Does a transparent spot-plus-short-rate approximation of currency excess
> returns retain a positive time-series-momentum effect before invented costs
> or parameter tuning?

## Frozen market object

For each admitted foreign currency versus USD, normalize spot to:

**USD value of one foreign-currency unit**

The daily approximate excess log return is frozen as:

`rx_t = Δlog(S_t) + carry_t / 261`

where:

- `S_t` is normalized spot;
- `carry_t = r_foreign - r_usd`;
- rates are annualized decimal short-term rates;
- `261` is the fixed daily accrual divisor;
- the rate observation used on day `t` must have been fully observable before
  that day under the frozen lag rule below.

This is an approximation. It is not a directly observed futures or forward
return.

## Frozen rate source hierarchy

Primary rate source:

**OECD Short-Term Interest Rates**

The source describes these rates as short-term borrowing/government-paper
market rates and states that they are generally based on three-month
money-market rates where available.

If an admitted currency has no qualifying OECD short-term-rate history, it is
not silently substituted with a policy rate inside the same run.

BIS central-bank policy rates may be used only in a separately labelled
sensitivity analysis under a future milestone, not M027.

## Frozen spot source hierarchy

Primary spot source:

**BIS bilateral exchange rates versus USD**

Fallback only when BIS lacks a required historical segment:

**Federal Reserve H.10 bilateral FX rate**

Fallback use must be documented before economics and may not be chosen based on
returns.

No broker/MT5 history is used to define the M027 research universe.

## Frozen rate lag / no-lookahead rule

OECD short-term rates are monthly averages.

For every calendar day in month `M`, the carry input is the rate differential
from the **previous completed calendar month M-1**.

No current-month average may be used within its own month.

Missing prior-month rate data make that currency ineligible for the affected
month. No interpolation or forward-fill across missing monthly rate
observations is permitted.

## Frozen signal

Only one signal is admitted:

**12-month time-series momentum**

At each month-end decision point:

- sum the prior 12 completed calendar months of approximate excess log returns;
- long next month when the 12-month sum is positive;
- short next month when the 12-month sum is negative;
- zero is flat.

No skip-month, alternate lookback, sign inversion, threshold, ensemble, or
multi-horizon signal is authorized in M027.

## Frozen risk scaling

Per admitted instrument:

- ex-ante annualized volatility target: **40%**;
- daily estimator: centered exponentially weighted variance of lagged daily
  approximate excess returns;
- annualization scalar: **261**;
- EWMA decay: **60 / 61**;
- estimate at decision time `t` may use information only through `t-1`.

No volatility floor/cap or leverage cap is authorized unless it is frozen in a
separate future milestone before any economics.

## Frozen portfolio aggregation

At each monthly rebalance:

1. compute each eligible currency's signed, volatility-scaled return stream;
2. equal-weight across all eligible currencies for that month;
3. do not reweight based on historical performance;
4. do not select or drop currencies based on P/L.

The portfolio must report the eligible-currency count each month.

## Universe selection — metadata only

The M027 universe is not named in advance.

It is selected mechanically from the intersection of currencies with:

- BIS USD bilateral spot history;
- OECD short-term-rate history;
- at least **72 consecutive eligible months** after applying the lag rule;
- unambiguous currency identity and quote normalization.

The final admitted universe must be frozen and hashed before any M027 strategy
return is computed.

The USD funding leg must also satisfy the same rate-availability rule.

No currency may be added/removed based on return performance.

## Evaluation partition

Stage 0 and Stage 1 are metadata/ingestion only.

Before first economics, a later protocol must freeze:

- immutable source snapshot end date;
- warmup;
- development/evaluation window;
- any holdout if enough later data exist.

No window may be chosen after looking at strategy returns.

The consumed M024 holdout is unrelated and must not be reused.

## Cost contract

First M027 economics, if reached, will be labelled:

**GROSS SPOT-PLUS-CARRY APPROXIMATION / TRANSACTION COSTS UNMODELED**

unless a public, deterministic historical bid/ask/cost dataset is frozen before
economics.

Do not invent spreads, commissions, slippage, or swaps.

## Stage 0 authorized work

Stage 0 may only:

1. inspect BIS/OECD/Fed source metadata and access paths;
2. establish exact series identifiers and quote/rate conventions;
3. establish coverage dates;
4. derive the coverage-based candidate universe;
5. publish a deterministic source/universe inventory;
6. freeze the admitted universe before strategy-return calculation.

Stage 0 must not:

- compute approximate excess returns;
- compute momentum signals;
- compute P/L, Sharpe, drawdown, win rate, or symbol contributions;
- inspect M021 post-cutoff economics;
- reuse M024 holdout economics to alter M027;
- tune source, universe, lookback, side, session, weekday, volatility target,
  or rate lag;
- merge/deploy;
- enable real trading.

## Stage 0 stop rule

If the public spot/rate intersection cannot produce at least **4 non-USD
currencies** with 72 consecutive eligible months under one coherent source
contract, M027 stops before economics.

If the gate passes, Stage 1 may implement deterministic ingestion and
no-lookahead proxy-return construction only. Stage 2 must then freeze the exact
evaluation partition and report schema before the first economic run.

## Terminal anti-retuning rule

After the first M027 economic output is inspected, no source, universe,
lookback, signal sign, rate lag, volatility target, EWMA constant, aggregation
rule, or cost treatment may change inside M027.

Any such change requires a separately named milestone.

## Stage-0 currency-identity map — frozen before universe intersection

The BIS/OECD Stage-0 schema probes have inspected only identifiers and coverage
dates. No observation values, approximate returns, signals, or economics have
been inspected.

To prevent country-level rate series from being paired with an economically
different or duplicated currency, the admissible identity map is frozen now.

### USD funding leg

- OECD `USA` supplies the USD short-rate leg.
- USD is not a foreign-currency portfolio member.

### Euro

The euro enters exactly once:

- OECD rate area: `EA20`
- BIS reference area: `XM`
- BIS currency: `EUR`

Individual euro-area country rate series are not separate currencies and are
excluded from the portfolio identity map. This also avoids pairing a historical
national money-market rate with BIS's back-calculated EUR series.

### Non-euro candidate identities

| OECD ref | BIS ref | Currency |
|---|---|---|
| AUS | AU | AUD |
| CAN | CA | CAD |
| CHE | CH | CHF |
| CHL | CL | CLP |
| CHN | CN | CNY |
| COL | CO | COP |
| CRI | CR | CRC |
| CZE | CZ | CZK |
| DNK | DK | DKK |
| GBR | GB | GBP |
| HUN | HU | HUF |
| IDN | ID | IDR |
| IND | IN | INR |
| ISL | IS | ISK |
| ISR | IL | ILS |
| JPN | JP | JPY |
| KOR | KR | KRW |
| MEX | MX | MXN |
| NOR | NO | NOK |
| NZL | NZ | NZD |
| POL | PL | PLN |
| ROU | RO | RON |
| RUS | RU | RUB |
| SWE | SE | SEK |
| ZAF | ZA | ZAR |

No other country/currency identity may enter M027 without starting a new
milestone.

### Mechanical eligible-month rule

For a foreign-currency identity and calendar month `M`, Stage-0 coverage marks
the month eligible only when:

1. the BIS daily spot series has at least one observation date in month `M`;
2. the foreign OECD short-rate series has an observation for completed month
   `M-1`;
3. the USA OECD short-rate series has an observation for completed month
   `M-1`.

The candidate passes Stage 0 only if those metadata conditions contain a run of
at least **72 consecutive eligible months**.

This coverage check does not inspect or use `OBS_VALUE`.

## Stage-0 accepted universe — 2026-09-30

Pre-intersection identity-map freeze:

`b45bea061411b273e2f30130d2224e2f84293d8d`

Metadata-only universe result:

`f06a777e48a96572beebcce9b96e76ac072ee318`

Durable inventory:

`docs/research/m027-stage0-source-universe.md`

Inventory commit:

`cea651e699ae9ad02001f51fa2b5f51d0a311468`

Mechanical result:

- candidates: **26**
- admitted: **25**
- rejected: **1 (CRC)**
- minimum gate: **4**
- Stage-0 gate: **PASS**

Frozen universe SHA-256:

`db9e1f4438fd582a0c2903f2459e290e30450bfc76365f2bbe91553d45b51c00`

Frozen admitted currencies:

`AUD, CAD, CHF, CLP, CNY, COP, CZK, DKK, EUR, GBP, HUF, IDR, INR, ISK, ILS, JPY, KRW, MXN, NOK, NZD, PLN, RON, RUB, SEK, ZAR`

No observation values or economics were used to form this universe.

### Stage-1 source-value contract

Before any Stage-1 value ingestion:

- BIS XRU is interpreted according to the publisher definition as the nominal
  value of **one USD relative to the foreign currency**, i.e. foreign-currency
  units per USD;
- therefore every admitted foreign series is normalized mechanically as
  `USD per foreign unit = 1 / BIS observation`;
- OECD `IR3TIB` is measured in **percent per annum**;
- therefore raw OECD observations are converted to annual decimal rates by
  dividing by 100;
- month M daily carry uses only completed-month M-1 foreign and USA rates;
- missing spot or prior-month rates remain missing; no interpolation,
  forward-fill, or backward-fill is authorized.

Stage 1 may now implement and validate deterministic source parsing, immutable
snapshot hashing, quote/rate normalization, lag alignment, and approximate
daily excess-log-return construction.

Stage 1 remains non-strategy and non-economic: no 12-month signal, portfolio
return, P/L, Sharpe, drawdown, or contribution analysis is authorized.

## Stage-1 immutable ingestion checkpoint — 2026-09-30

Immutable ingestion feature SHA:

`30d4e845df0bed16915cd24f62447d22efc5388e`

Immutable local result:

`8744c7bd96f04129fd99cb2ab9f8ee1df1179331`

Report SHA-256:

`2c35506424bf8dae520f1dcf32fa5406a87f970faa7eebd9e44b1bf660a01308`

Frozen source hashes:

- BIS XRU raw:
  `cdf288e5a3bfe69cd8a797c4c15124b480a63a9099c1fb9853413f456f4ac890`
- OECD IR3TIB raw:
  `af54f1cf8677a0b2bd9c204210ad9b1f72d7bb669dce2e6e3c23f513be6cbed9`
- normalized BIS spot panel:
  `c01ac4cf5a1f85fbf0e3db9945bb80278546ff9e86a926f454bb838439d97ad0`
- normalized OECD rate panel:
  `fbfbe69b7aea4738be95668bebab2113416a62d534d4b8931dddf2e5920c1d2a`
- frozen approximate daily excess-log-return panel:
  `c0f166957d8879ba05cdfeb457ab8874657cd72900528856d81563d786b4848e`

Snapshot metadata:

- spot first / last date: **1945-01-01 / 2026-09-22**
- rate first / last month: **1956-01 / 2026-08**
- approximation rows: **28,024**
- frozen currencies: **25**
- strategy signal computed: **false**
- portfolio economics computed: **false**

Two parser-only commits after the first Stage-1 test pass repaired and pinned
the publisher's real BIS observation-value column capitalization. They did not
change source selection, universe, quote direction, rate units, carry timing,
signal parameters, or economics.

Stage-1 acceptance requires focused and full-native regression on the exact
ingestion SHA before Stage-2 economics may execute.

## Stage-2 economic protocol freeze — 2026-09-30

Status: **FROZEN BEFORE ANY M027 MOMENTUM SIGNAL OR PORTFOLIO ECONOMICS**

Stage 2 may proceed only after exact-SHA Stage-1 validation passes.

### Immutable input

Stage-2 uses only:

`backtest_data/m027-stage1-ingestion-v1/m027-approx-excess-log-returns.csv`

with required SHA-256:

`c0f166957d8879ba05cdfeb457ab8874657cd72900528856d81563d786b4848e`

No source refresh is allowed inside Stage 2.

### Monthly instrument return

For each currency and calendar month:

1. sum the available frozen daily approximate **log** excess returns in that
   month with no filling;
2. if the month has no valid daily approximate return, the monthly value is
   missing;
3. convert the realized monthly log excess return to arithmetic form for
   portfolio accounting as `exp(monthly_log_rx) - 1`.

No missing daily observation may be forward-filled, backward-filled, or
interpolated.

### Formation signal

At month-end `t`:

- require the prior **12 completed calendar months** of monthly approximate log
  excess returns for the currency;
- the formation statistic is their additive sum;
- positive => long;
- negative => short;
- exactly zero => flat.

The position formed at month-end `t` is applied only to month `t+1`.

### Volatility scaling

Use the already frozen M027 rule on the daily approximate excess-log-return
panel:

- centered exponentially weighted variance;
- decay `60 / 61`;
- annualization **261**;
- shift one daily observation so decision-time volatility uses information only
  through `t-1`;
- month-end volatility is the last available lagged daily estimate in the
  formation month;
- valid volatility must be finite and strictly positive;
- target annualized volatility: **40%**;
- no leverage cap, volatility floor, or volatility ceiling.

Per-currency formation weight:

`sign(12m_log_rx) * 0.40 / ex_ante_volatility`.

### Portfolio aggregation

For realized month `t+1`, a currency is mechanically eligible only when:

- its shifted formation weight is finite;
- its realized monthly arithmetic approximate excess return is finite.

Portfolio return is the equal-weight mean of eligible currency
weight × realized return contributions.

Minimum eligible currencies per reported portfolio month:

**4**

Months with fewer than 4 are not part of the evaluation sample.

No currency subset may be selected from performance.

### Availability-only evaluation window

Stage-2 readiness must compute only presence/eligibility metadata, never return
magnitudes or strategy economics.

Candidate realized months are capped at:

**2026-08-31**

This is the final complete rate month in the immutable Stage-1 snapshot and
precedes the partially observed September spot month.

The exact evaluation window is defined mechanically as:

1. identify every calendar month with at least 4 mechanically eligible
   currencies under the frozen formation/volatility/realization-presence rules;
2. find the **longest consecutive calendar-month block** of such months;
3. if multiple blocks tie, choose the **latest** tied block;
4. require at least **60 consecutive evaluation months** or stop M027 before
   economics;
5. freeze the resulting ordered month list and SHA-256 before the first
   economic execution.

This rule is based only on data availability and the already frozen strategy
mechanics. Return sign/magnitude may not influence the window.

### Frozen stability partitions

After readiness fixes the ordered evaluation-month list, split it into exactly
three consecutive blocks as evenly as possible using deterministic
`numpy.array_split` semantics:

- F1 — earliest third;
- F2 — middle third;
- F3 — latest third.

These folds may not be moved after economics.

### Frozen report metrics

The first and sole Stage-2 economic report must include:

Portfolio:

- first / last evaluation month;
- number of months;
- mean monthly return;
- annualized arithmetic mean = 12 × monthly mean;
- annualized volatility = sqrt(12) × sample monthly standard deviation;
- annualized Sharpe = annualized mean / annualized volatility, risk-free
  adjustment zero because the modeled series is already an approximate excess
  return;
- maximum cumulative-wealth drawdown;
- positive-month fraction;
- terminal cumulative wealth from 1.0;
- eligible-currency count min / median / max.

Stability:

- the same annualized mean for F1/F2/F3;
- positive-calendar-year count / eligible-year count;
- per-currency cumulative contribution over the fixed sample;
- largest positive-currency contribution share.

No lag search, sign search, subperiod search, or post-result currency removal
is authorized.

### Mechanical research classification

Classify **SUPPORTED AS A GROSS PUBLIC-DATA APPROXIMATION** only if all are true:

1. full-sample annualized arithmetic mean > 0;
2. full-sample annualized Sharpe > 0;
3. terminal cumulative wealth > 1.0;
4. at least **2 of 3** frozen chronological folds have positive annualized
   arithmetic mean;
5. at least **50%** of eligible calendar years have positive total return;
6. no single currency contributes more than **50%** of total positive currency
   contribution.

Otherwise classify:

**NOT SUPPORTED**

This classification does not authorize live trading because transaction costs,
direct forwards/futures, execution slippage, and real broker financing remain
unmodeled.

### Economic execution rule

After readiness freezes the exact month list:

1. focused Stage-2 tests must pass;
2. full native regression must pass;
3. execute the deterministic economic report twice from the same immutable
   inputs;
4. A/B report bytes must match exactly;
5. inspect the first accepted economic output once;
6. stop M027—no retuning.

No real MT5 order API may be called.

## Stage-2 readiness accepted — 2026-09-30

Focused Stage-2 validation:

- command: `mamba2-m027-stage2-tests-v1`
- result commit:
  `4efe732ba9e884ea091415b05f98a17eb9a7d794`
- result: **15 passed / 0 failed**
- feature SHA:
  `7a5cfcdb90fc0118397ac55edf5d19ca9bab8ea3`

Metadata-only readiness:

- command: `mamba2-m027-stage2-readiness-v1`
- feature SHA:
  `7a5cfcdb90fc0118397ac55edf5d19ca9bab8ea3`
- return values reported: **false**
- portfolio returns computed: **false**
- economic summary computed: **false**

Frozen evaluation window:

- first month: **1980-02-29**
- last month: **2020-04-30**
- months: **483**
- ordered month-list SHA-256:
  `c5cda6bb68904213dc46aa338887c19e7575e31cba8ab816e44469b81a3b4b40`

Frozen eligible-currency counts:

- minimum: **4**
- median: **22**
- maximum: **25**

Frozen chronological folds:

- F1: **1980-02-29 → 1993-06-30**, 161 months,
  SHA-256
  `015357895f4f4bae39566ed3467b67eb87c29876044a2b0a0e86010f451e55ee`
- F2: **1993-07-31 → 2006-11-30**, 161 months,
  SHA-256
  `d776c84d6088e2e21a9702e2d986381acbfd44e20426e8a2d4f9c050149232a3`
- F3: **2006-12-31 → 2020-04-30**, 161 months,
  SHA-256
  `145c93355905d15eb7946ab1c67ab52454c68ef23146f8b611053b2cd551ea6b`

The evaluation end is earlier than the 2026-08 cap because the frozen
availability rule selects the longest consecutive block with at least four
mechanically eligible currencies. No return sign or magnitude influenced this
choice.

This month list is now immutable for M027. No date, fold, or currency may be
changed after economics.
## Terminal M027 result — CLOSED

Final economic feature SHA:

`ebd650204cb8d03d4eb144d2b3bc431f8b838409`

Final pre-economic validation:

- focused Stage-2: **17 passed / 0 failed**
  (`c318aeeb5974f975d4fda76640326a61388fd1b0`);
- full native: **297 passed / 2 skipped**
  (`670ba6b651bf0223e01847ebbd5d380867d646bc`).

Sole accepted economic execution:

`mamba2-m027-stage2-economics-v1`

Result branch commit:

`5cebd54c14833dadd7e2de302213c059cd8b2116`

A/B report paths:

- `backtest_data/m027-stage2-economics-v1/m027-stage2-a.json`
- `backtest_data/m027-stage2-economics-v1/m027-stage2-b.json`

A/B SHA-256:

`08be7e8002410ad36e32caa98cb3cf6e66110bef2c24815b2c1582b96b957e00`

Byte identity:

**PASS**

### Frozen full-sample economics

Evaluation:

- **1980-02-29 → 2020-04-30**
- **483 months**
- eligible currencies per month: **4 / 22 median / 25 max**

Portfolio:

- annualized arithmetic mean: **0.3757941369870949**
- annualized volatility: **0.34603206871941145**
- annualized Sharpe: **1.0860095666214589**
- maximum drawdown: **-0.6214266894048992**
- positive-month fraction: **0.6666666666666666**
- terminal cumulative wealth from 1.0: **372687.6279800574**

Frozen chronological folds:

- F1 annualized mean: **0.46972723789656895**
- F2 annualized mean: **0.6066053534582256**
- F3 annualized mean: **0.05104981960649009**

All three folds are positive under the frozen metric.

Calendar-year stability:

- eligible calendar years: **41**
- positive calendar years: **30**
- positive-year fraction: **0.7317073170731707**

Concentration:

- largest positive currency contribution share: **0.3929912070958048**
- frozen gate maximum: **0.50**

### Mechanical classification

**SUPPORTED AS A GROSS PUBLIC-DATA APPROXIMATION**

Every prospectively frozen support gate passed.

This result is intentionally not called publication-faithful futures TSMOM and does not authorize live trading.

Important limitations remain unchanged:

- transaction costs are unmodeled;
- execution slippage is unmodeled;
- direct forwards/futures are not used;
- broker financing / swaps are not modeled from real executable history;
- the excess-return process is an explicit BIS spot + lagged OECD short-rate approximation;
- 40% per-instrument ex-ante volatility scaling can create material gross leverage and large drawdowns.

The very large long-run terminal wealth is therefore a property of the frozen gross approximation and must not be interpreted as an executable account equity forecast.

### Terminal stop rule

M027 is **CLOSED**.

Do not, inside M027:

- add transaction costs after seeing the result;
- add leverage/volatility caps or floors;
- remove losing currencies;
- retain only CNY/COP or other strong contributors;
- change the 12-month lookback;
- change carry lag or rate source;
- search signs, sessions, weekdays, symbols, subperiods, or alternate folds;
- change the 40% volatility target;
- refresh the source snapshot;
- rerun economics to seek a different result;
- merge/deploy or enable real trading.

Any executable-cost or broker-realism investigation must be a separately named prospectively frozen future milestone.
