# M026 TSMOM Source Inventory

Checked: 2026-09-30

Protocol:

`docs/milestones/026-tradeable-fx-tsmom-reconstruction.md`

This inventory was performed after the M026 Stage-0 source-fidelity protocol
was frozen and before any M026 strategy economics.

No candidate source was selected using P/L, Sharpe, drawdown, sign, or other
economic outcomes.

## Decision

**No public/free A, B, or surviving C source is established.**

The M026 Stage-0 stop rule therefore fires. No M026 TSMOM economics are
authorized under the current public/free boundary.

## Inventory

### 1. CME Group Continuous Price Series — FX

Publisher: CME Group

Canonical pages:

- https://www.cmegroup.com/market-data/cme-group-continuous-price-series.html
- https://www.cmegroup.com/datamine.html
- https://www.cmegroup.com/datamine/datamine-api.html

Observed metadata:

- official settlement-based continuous futures;
- Front Contract and Active Contract series;
- Standard file includes contract identifier, settlement price, and next roll
  date;
- official FX series shown for Canadian Dollar, Japanese Yen, Euro FX,
  British Pound, Mexican Peso, and Australian Dollar;
- listed start date for those FX continuous series: **2004-01-02**;
- historical files are distributed through CME DataMine;
- CME states historical data are purchased through DataMine;
- API access is authenticated and entitlement-based;
- continuous-series access requires licensing / an Information License
  Agreement.

Fidelity assessment:

This is the strongest identified raw-futures source and would satisfy the
economic-data shape needed for a publication-faithful futures reconstruction
subject to a later exact roll/return review.

Classification under the frozen M026 public/free boundary:

**F — UNAVAILABLE / RESTRICTED**

Reason: historical access is licensed/purchased rather than a reproducible
public/free data path.

### 2. CME delayed website settlement pages / End of Market files

Publisher: CME Group

Canonical pages:

- https://www.cmegroup.com/market-data/daily-settlements.html
- https://www.cmegroup.com/articles/faqs/access-to-cme-group-settlement-data-faq.html

Observed metadata:

- settlement values on product web pages become freely viewable after the
  stated delay;
- CME moved historical settlement-file distribution from its legacy FTP path
  to DataMine;
- DataMine End of Market access is fee/licence based;
- the free delayed page does not establish a reproducible 72+ month
  contract-level historical bulk path with deterministic roll metadata.

Classification:

**F — UNAVAILABLE / RESTRICTED / INSUFFICIENT**

Reason: current delayed observations are visible, but the required historical
bulk/contract/roll path is not established as public/free.

### 3. Nasdaq Data Link / former Quandl CHRIS Wiki Continuous Futures

Prior identifier:

`CHRIS`

Prior documentation URL:

https://data.nasdaq.com/data/CHRIS-wiki-continuous-futures/documentation

Observed current access state:

- the former canonical documentation URL returns **404** during this inventory;
- recent secondary technical reports describe CHRIS access as discontinued;
- older research confirms it historically exposed continuous futures,
  including currencies, but historical prior availability does not satisfy the
  current reproducibility gate.

Classification:

**F — UNAVAILABLE / RESTRICTED**

Reason: no dependable current public/free source endpoint was established.

### 4. Federal Reserve Board H.10 bilateral FX rates

Publisher: Federal Reserve Board

Canonical pages:

- https://www.federalreserve.gov/releases/h10/hist/
- https://www.federalreserve.gov/datadownload/choose.aspx?rel=h10

Observed metadata:

- daily bilateral FX rates;
- official description identifies the observations as noon buying rates in New
  York for cable transfers payable in foreign currencies;
- long public history and reproducible downloads exist;
- the package exposes 23 bilateral rate series.

Classification:

**E — SPOT PROXY ONLY**

Reason: no directly observed futures/forward excess-return or financing/carry
leg. This source already supported the explicitly labelled M025 H.10 spot
proxy and cannot be upgraded to publication-faithful M026 data.

### 5. Dukascopy historical FX ticks/bars

Publisher: Dukascopy

Canonical pages:

- https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/history-ticks/
- https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/history-bars/

Observed metadata:

- historical tick and bar access;
- bid/ask market observations are available through the JForex historical
  interfaces.

Classification:

**E — SPOT PROXY ONLY**

Reason: spot FX history does not directly supply the required futures/forward
excess-return series.

### 6. BIS bilateral exchange rates

Publisher: Bank for International Settlements

Canonical page:

https://data.bis.org/topics/XRU

Observed metadata:

- daily and monthly bilateral exchange-rate data;
- public long-history official dataset.

Classification:

**E — SPOT PROXY ONLY**

Reason: bilateral spot data alone do not provide futures/forward excess
returns.

### 7. BIS central-bank policy rates + public spot

Publisher: Bank for International Settlements

Canonical page:

https://data.bis.org/topics/CBPOL

Observed metadata:

- long daily/monthly histories for more than 40 economies;
- the series represent each central bank's selected policy instrument;
- the rate may be a target, repo, discount, or historically substituted
  monetary-policy indicator.

Stage-0 C-path review:

A policy rate is not the same object as a directly investable one-month funding
rate or observed one-month FX forward price. Splicing policy instruments also
introduces country/time heterogeneity not present in directly observed futures
returns.

Classification:

**F — INSUFFICIENT FOR RATE-BASED RECONSTRUCTION**

Reason: the exact one-month investable carry/forward mapping required for a
publication-faithful daily excess-return series cannot be frozen from these
policy-rate series without inventing an economic approximation.

### 8. OECD short-term interest rates + public spot

Publisher: OECD

Canonical page:

https://www.oecd.org/en/data/indicators/short-term-interest-rates.html

Observed metadata:

- standard short-term rates are generally based on **three-month** money-market
  or Treasury-bill rates where available;
- rates are generally averages of daily observations.

Classification:

**F — INSUFFICIENT FOR RATE-BASED RECONSTRUCTION**

Reason: tenor and timing do not match the required directly observed
futures/forward excess-return process; using them would create a new proxy
rather than reconstruct the frozen MOP futures strategy.

### 9. Direct one-month forward datasets used in academic FX research

The Menkhoff et al. source review already documented spot and one-month forward
data obtained from BBI/Reuters through Datastream.

Classification:

**F — UNAVAILABLE / RESTRICTED**

Reason: proprietary data access, not a public/free reproducible M026 source.

### 10. AQR TSMOM^FX

Publisher: AQR

Status inherited from M025:

**D — DERIVED REFERENCE ONLY**

Reason: useful for external reference, but it does not expose the raw
instrument-level futures/forward series required to independently reconstruct
the strategy.

## Mechanical source-selection result

Frozen source preference:

1. direct raw futures;
2. direct raw forward/excess returns;
3. rate-based reconstruction only if exact investable mapping is supportable.

Result:

- A: strongest candidate exists (CME), but fails the public/free access gate;
- B: no public/free direct forward/excess-return raw source established;
- C: official free rate datasets reviewed do not establish the required exact
  investable one-month/daily excess-return mapping.

Therefore:

**SELECTED SOURCE: NONE**

**M026 STAGE-0 RESULT: DATA GATE NOT PASSED**

## Consequence

Do not implement M026 strategy ingestion or run M026 economics under the
current public/free constraint.

The scientifically clean next choices are external to this milestone:

1. acquire/license a raw futures dataset and open a new prospectively frozen
   milestone around that immutable dataset; or
2. define a separately named proxy/reconstruction research milestone whose
   approximation is explicit from the start.

Do not weaken M026 after seeing the source inventory.
