# M025 Public FX Benchmark Source Inventory

Checked: **2026-09-29**

Milestone:

`M025 — Public FX Strategy Benchmarks`

This artifact applies the prospectively frozen Stage-2 source-inventory gate.
It records source metadata only. No candidate strategy P/L, Sharpe ratio,
drawdown, win rate, or period-by-period benchmark economics were inspected or
computed.

## Classification vocabulary

Exactly one classification is used per source:

- **RAW-ELIGIBLE-CANDIDATE**
- **DERIVED-REFERENCE-ONLY**
- **PROXY-ONLY**
- **INSUFFICIENT**
- **UNAVAILABLE/RESTRICTED**

## B1 — MOP TSMOM

### AQR — Time Series Momentum: Original Paper Data

Publisher: AQR Capital Management

Canonical page:

https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data

Access: public web dataset, subject to AQR dataset terms.

Nature: derived strategy/factor returns.

Documented content:

- monthly long/short TSMOM factors;
- January 1985 through December 2009;
- 12-month formation / 1-month holding;
- 58 underlying liquid futures/forward instruments across equities,
  currencies, commodities, and government bonds.

Classification:

**DERIVED-REFERENCE-ONLY**

Reason: the source provides paper strategy factors, not the instrument-level
daily futures/forward return histories required to reconstruct the frozen
signal and ex-ante volatility estimator.

### AQR — Time Series Momentum: Factors, Monthly

Publisher: AQR Capital Management

Canonical page:

https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Factors-Monthly

Access: public web dataset, subject to AQR dataset terms.

Nature: updated derived factor returns.

Documented content:

- monthly TSMOM factor excess returns;
- starts January 1985;
- updated monthly;
- factors based on the same 12-month/1-month benchmark family.

Classification:

**DERIVED-REFERENCE-ONLY**

Reason: useful as an external published-series reference, but not raw
instrument-level input.

### Original MOP raw source stack

Publisher/source stack documented by the paper:

- Datastream;
- Bloomberg;
- individual futures exchanges;
- currency forwards from Citigroup from 1989;
- earlier currency spot plus IBOR inputs from Datastream/Bloomberg.

Nature: raw/underlying research inputs.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: the exact paper input stack depends materially on commercial feeds.
No public/free instrument-level mirror with the frozen paper fields and
history was established in this inventory.

### CME DataMine historical futures

Publisher: CME Group

Canonical page:

https://www.cmegroup.com/datamine.html

Documented content:

- historical CME futures/options data;
- settlement datasets and deeper market datasets;
- FX futures are part of CME's futures/FX coverage.

Access: order/commercial DataMine product.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: potentially raw and suitable in principle for CME instruments, but it
does not satisfy the frozen public/free access boundary.

### Barchart futures history

Publisher: Barchart

Canonical help page:

https://help.barchart.com/support/solutions/articles/242748-how-can-i-download-historical-data-

Documented content:

- futures by individual contract or "Nearby" continuous history;
- Nearby contracts roll using total volume and open interest;
- free/site-member daily download history is limited to about two years;
- longer daily history and broader downloads require paid membership.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: the public/free window is shorter than the frozen 72-consecutive-month
gate; the longer history is a paid service.

### Databento CME futures

Publisher: Databento

Canonical page:

https://databento.com/futures

Documented content:

- CME/CBOT/NYMEX/COMEX futures and reference data;
- historical coverage advertised from 2010 for CME Globex MDP 3.0;
- historical access priced by data volume.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: raw historical futures are commercial, not public/free under M025's
inventory boundary.

### Dukascopy historical spot feed

Publisher: Dukascopy Bank

Canonical documentation:

https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/overview-historical-data/

Documented content:

- historical ticks, bars, and feed history;
- Bid/Ask tick access through JForex history APIs;
- historical feed data come from the live environment even in demo.

Classification:

**PROXY-ONLY**

Reason: this is spot FX market data. It does not contain the futures/forward
excess-return economics required for publication-faithful MOP TSMOM, but it can
support a separately labelled **TSMOM SPOT PROXY**.

### Federal Reserve H.10 / FRED spot FX

Publisher: Federal Reserve Board / Federal Reserve Bank of St. Louis

Canonical pages:

https://www.federalreserve.gov/datadownload/choose.aspx?rel=h10

https://fred.stlouisfed.org/categories/94?t=h10

Documented content:

- downloadable daily foreign-exchange spot rates;
- current H.10 package exposes 23 daily rate series;
- several major series extend back to 1971, with later currencies beginning at
  their relevant availability dates.

Classification:

**PROXY-ONLY**

Reason: authoritative, long, public spot history, but no one-month
forward/carry leg. It is a strong candidate source for a separately frozen
TSMOM spot proxy, not the paper-faithful benchmark.

### Alpha Vantage historical FX

Publisher: Alpha Vantage

Canonical documentation:

https://www.alphavantage.co/documentation/

Documented content:

- FX daily/weekly/monthly OHLC endpoints;
- free API key path is advertised.

Classification:

**PROXY-ONLY**

Reason: spot FX only; no frozen forward/excess-return leg.

### B1 inventory conclusion

Public/free publication-faithful raw candidate:

**NONE ESTABLISHED**

Available evidence paths:

- AQR factors — **DERIVED-REFERENCE-ONLY**
- Federal Reserve H.10 / Dukascopy / Alpha Vantage spot —
  **PROXY-ONLY**

## B2 — Menkhoff currency momentum

### Original BBI + Reuters / Datastream input

Paper source:

Menkhoff, Sarno, Schmeling, and Schrimpf (2012),
*Currency Momentum Strategies*.

Documented raw input:

- end-of-month spot exchange rates;
- one-month forward exchange rates;
- January 1976 through January 2010;
- up to 48 currencies;
- Barclays Bank International and Reuters via Datastream.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: the publication-faithful raw spot/one-month-forward panel is based on
commercial data feeds.

### Journal of Financial Economics associated spreadsheet

Publisher: Journal of Financial Economics data/code archive

Canonical page:

https://journal-of-financial-economics.squarespace.com/data-and-code

Listed artifact:

`Menkoff_Sarno_Schmeling_Schrimpf.xlsx`

Access metadata:

- JFE identifies it as an Excel spreadsheet containing data associated with the
  paper;
- for papers in this older archive, the site states locally stored files are
  requested by email rather than exposed as normal direct links.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: it is not currently available through the public/free direct-access
path, and Stage 2 has not established that it contains the currency-level raw
spot/forward panel rather than derived paper data. It may be reconsidered only
through a separately authorized schema-access gate, without inspecting
economic outcomes.

### Federal Reserve H.10, Dukascopy, or Alpha Vantage spot panels

Classification:

**INSUFFICIENT**

Reason: B2 prospectively requires one-month forwards or directly observed
currency log excess returns. Spot-only history cannot satisfy that field gate.

### B2 inventory conclusion

Public/free publication-faithful raw candidate:

**NONE ESTABLISHED**

Do not replace the missing forward leg with spot momentum and call it
Menkhoff currency momentum.

## B3 — HML-FX carry

### Original Barclays + Reuters / Datastream panel

Paper source:

Lustig, Roussanov, and Verdelhan (2011),
*Common Risk Factors in Currency Markets*.

Documented raw input:

- daily U.S.-dollar spot and forward exchange-rate quotes;
- converted to end-of-month series;
- November 1983 through December 2009 in the published study;
- up to roughly 35 currencies in the main sample;
- Barclays and Reuters via Datastream;
- forward-discount sorting into six currency portfolios.

Classification:

**UNAVAILABLE/RESTRICTED**

Reason: publication-faithful currency-level spot and forward quotes rely on
commercial data.

### Author-published CurrencyPortfolios.xls

Publisher: Nikolai Roussanov / coauthors

Canonical author page:

https://finance.wharton.upenn.edu/~nroussan/

Listed artifact:

https://finance.wharton.upenn.edu/~nroussan/CurrencyPortfolios.xls

Access: public direct spreadsheet link.

Nature: published currency portfolio/factor data associated with the paper.

Classification:

**DERIVED-REFERENCE-ONLY**

Reason: this is valuable external HML-FX/portfolio reference evidence, but it
is not established as the underlying currency-level month-end spot and
one-month-forward formation panel.

### OECD short-term rates + Federal Reserve H.10 spot composite

Publishers:

- OECD Data Explorer;
- Federal Reserve H.10 / FRED.

Canonical pages:

https://data-explorer.oecd.org/

https://www.federalreserve.gov/datadownload/choose.aspx?rel=h10

Documented metadata:

- OECD exposes monthly short-term/immediate/interbank-rate statistics with a
  public SDMX API across many economies;
- Federal Reserve H.10 provides a broad, long-running public USD spot panel.

Classification:

**INSUFFICIENT**

Reason: Stage 2 has not established a uniform, directly corresponding
**one-month** funding-rate series across a >=12-currency common panel. Mixing
generic 3-month/immediate national money-market measures with spot rates would
silently change the frozen one-month-forward benchmark. No such substitution
is permitted.

### B3 inventory conclusion

Public/free publication-faithful raw candidate:

**NONE ESTABLISHED**

Available external evidence:

- author CurrencyPortfolios/HML-FX series —
  **DERIVED-REFERENCE-ONLY**

## B4 — fixed internal M020-D comparator

Source: accepted M020 controlled-experiment artifacts already in this
repository/local-control evidence.

Accepted implementation SHA:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

Published authoritative local-control result:

`53e79d1da25994c87330faaaf805928de08c427e`

Immutable M020-D treatment hashes:

- baseline:
  `94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`
- diagnostic:
  `45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`
- evidence:
  `e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`

Classification:

**DERIVED-REFERENCE-ONLY**

Reason: B4 is intentionally a frozen internal comparator snapshot. M025 may
reference its already accepted economics but may not rerun or tune it.

## Inventory decision

| Family | RAW-ELIGIBLE-CANDIDATE | Derived reference | Proxy path |
|---|---|---|---|
| B1 MOP TSMOM | **none established** | AQR TSMOM factors | H.10 / Dukascopy spot |
| B2 currency momentum | **none established** | none directly accessible/validated | none authorized |
| B3 HML-FX carry | **none established** | CurrencyPortfolios.xls | none authorized |
| B4 M020-D | n/a | accepted internal snapshot | n/a |

The Stage-2 stop rule therefore fires for publication-faithful B1/B2/B3
reconstruction under the current public/free boundary.

No benchmark definition is weakened.

No historical benchmark economics have been computed in M025.

## Permissible future directions

A later, separately frozen protocol may evaluate:

1. **published/reference series** exactly as published and explicitly label
   them as external reference returns rather than reconstructed raw benchmarks;
2. **TSMOM SPOT PROXY** using a prospectively fixed public spot source and
   universe.

Neither path may be described as publication-faithful raw reconstruction.
