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

