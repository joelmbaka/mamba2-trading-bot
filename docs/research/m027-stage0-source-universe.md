# M027 Stage-0 Source and Universe Inventory

Checked: 2026-09-30

Protocol:

`docs/milestones/027-carry-aware-spot-tsmom.md`

Stage-0 feature SHA used by the metadata-only universe probe:

`b45bea061411b273e2f30130d2224e2f84293d8d`

Local-control result commit:

`f06a777e48a96572beebcce9b96e76ac072ee318`

No observation values, returns, momentum signals, P/L, Sharpe, drawdown, or
other strategy economics were used.

## Sources

Spot:

- BIS bilateral exchange-rate bulk dataset:
  `https://data.bis.org/static/bulk/WS_XRU_csv_flat.zip`

Rates:

- OECD STES Financial Markets dataset, monthly three-month
  interbank/money-market short-term interest rate:
  `OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/.M.IR3TIB.PA.....`

USD funding reference:

- OECD reference area `USA`.

The currency/country identity map was frozen in the milestone before the
intersection was computed.

## Mechanical gate

A currency is Stage-0 admitted only if metadata show a run of at least
**72 consecutive eligible months**, where month M requires:

1. at least one BIS daily spot observation in M;
2. the foreign OECD rate observation for M-1;
3. the USA OECD rate observation for M-1.

The coverage probe did not read or report observation values.

## Result

Candidate identities: **26**

Accepted: **25**

Rejected: **1**

Universe SHA-256:

`db9e1f4438fd582a0c2903f2459e290e30450bfc76365f2bbe91553d45b51c00`

### Frozen admitted universe

| Currency | OECD ref | BIS ref | Longest eligible run |
|---|---|---|---|
| AUD | AUS | AU | 1971-01 → 2020-04 (592 months) |
| CAD | CAN | CA | 1964-07 → 2020-04 (670 months) |
| CHF | CHE | CH | 1999-08 → 2020-04 (249 months) |
| CLP | CHL | CL | 1998-11 → 2008-08 (118 months) |
| CNY | CHN | CN | 2006-03 → 2020-04 (170 months) |
| COP | COL | CO | 1986-02 → 2020-04 (411 months) |
| CZK | CZE | CZ | 1993-02 → 2020-04 (327 months) |
| DKK | DNK | DK | 1987-02 → 2020-04 (399 months) |
| EUR | EA20 | XM | 1994-02 → 2020-04 (315 months) |
| GBP | GBR | GB | 1986-02 → 2020-04 (411 months) |
| HUF | HUN | HU | 1991-02 → 2004-04 (159 months) |
| IDR | IDN | ID | 1998-02 → 2020-04 (267 months) |
| INR | IND | IN | 2011-12 → 2020-04 (101 months) |
| ISK | ISL | IS | 1987-12 → 2020-04 (389 months) |
| ILS | ISR | IL | 1992-02 → 2020-04 (339 months) |
| JPY | JPN | JP | 2002-05 → 2020-04 (216 months) |
| KRW | KOR | KR | 1991-02 → 2020-04 (351 months) |
| MXN | MEX | MX | 1997-02 → 2020-04 (279 months) |
| NOK | NOR | NO | 1979-02 → 2020-04 (495 months) |
| NZD | NZL | NZ | 1974-01 → 2020-04 (556 months) |
| PLN | POL | PL | 1991-07 → 2020-04 (346 months) |
| RON | ROU | RO | 1995-09 → 2020-04 (296 months) |
| RUB | RUS | RU | 1997-02 → 2020-01 (276 months) |
| SEK | SWE | SE | 1982-02 → 2020-04 (459 months) |
| ZAR | ZAF | ZA | 1981-01 → 2020-04 (472 months) |

### Rejected

| Currency | OECD ref | BIS ref | Reason |
|---|---|---|---|
| CRC | CRI | CR | BIS daily spot metadata absent; no lag-aligned eligible run |

## Mechanical decision

Stage-0 minimum: at least 4 admitted non-USD currencies.

Observed: **25**.

**STAGE-0 GATE: PASS**

The exact 25-currency set above is now frozen for M027. No currency may be
added or removed based on later return performance.

Monthly portfolio eligibility may still vary mechanically because the frozen
strategy already requires the prior-month rate and current-month spot
availability.

## Next gate

Stage 1 may implement:

- deterministic BIS/OECD parsing;
- quote normalization to USD value per foreign-currency unit;
- previous-completed-month rate alignment;
- approximate daily excess-log-return construction;
- no-lookahead and missing-data tests;
- immutable source snapshot hashing.

Stage 1 may not compute the 12-month momentum strategy, portfolio P/L, Sharpe,
drawdown, or symbol contributions.

Stage 2 must prospectively freeze the exact evaluation partition and report
schema before any strategy economics.
