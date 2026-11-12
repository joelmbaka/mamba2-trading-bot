# M029 — Prospective paper-validation recovery

**Status: PROTOCOL FROZEN BEFORE ANY M029 SIGNAL OR ECONOMIC OBSERVATION**

Freeze date: 2026-11-12 UTC
Branch: `prospective-paper-recovery`
Base: `e4cabba73243651ef86b1ffe194bf64124ff8000` on `execution-realism`

## Reason for separate milestone

The M028 October 2026 paper decision was not run at its scheduled time.
The workstation audit on 2026-11-12 found neither the immutable October
decision record nor its containing directory. November's fifth weekday
(2026-11-06) has also passed.

No October/November signal, quote, holding period, equity curve or trading
decision may be fabricated or retrospectively backfilled. No missing month
counts towards the 12-completed-forward-period decision gate.

M027 remains **SUPPORTED ONLY AS A GROSS PUBLIC-DATA APPROXIMATION**, not a
broker-net-profit claim. M028 execution validation remains **FORWARD_PAPER_ONLY**.

## Invariants retained from M027 and M028

No alteration or optimization to:

- M027 12 *completed* calendar months of approximate log excess returns;
- lagged OECD short rates (one completed additional month), BIS XRU spot,
  no source substitutions or fills;
- lagged centered-EWMA volatility (decay 60/61; annualization 261);
- target annualized per-currency volatility 40%; equal-weight eligible currency
  aggregation;
- fixed eight currency identities:
  AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK;
- fixed direct-USD broker symbols and mechanical currency-to-BUY/SELL mapping;
- USD 10,000 *non-compounding* reference sizing;
- gross notional 4.0x cap, USD 2,500 (25%) projected margin cap;
- 4 executable nonzero currency minimum and broker lot rounding toward zero;
- BUY Ask / SELL Bid paper fills and inverse Bid/Ask paper exit marks;
- unproven commission, unobserved slippage, unproven financing/swap kept
  separately null — never misrepresented as zero/net P/L;
- no M021 prospective post-cutoff results, M027 economics reruns, live trading
  activation or performance-based selection.

## Fixed prospective calendar and time window

A monthly decision belongs to YYYY-MM at **12:00:00 UTC on the fifth Monday-Friday
weekday of that month**, exactly as M028. Do not introduce country holiday
calendars.

First M029 month: **2026-12**; scheduled time:
**2026-12-07T12:00:00Z**.

New, explicitly prospective operational processing allowance: only during the
half-open window **[scheduled time, scheduled time + 10 minutes)**. This is an
execution-latency window, not permission to reconstruct noon quotes; source
and quote observations must have actual timestamps in the live decision window,
and records must retain both scheduled and actual times.

- Before opening, refuse with `WINDOW_NOT_OPEN`; no signal or targets.
- In the open window, a pre-existing valid immutable record wins: reuse only
  that exact record, never recompute.
- After closing, a missing record is permanently `MISSED_WINDOW` for that
  month. Do not execute retroactively, even if sources are now complete.
- Any month earlier than December 2026 is `INELIGIBLE_HISTORICAL_MONTH`;
  **including October and November**.
- Do not create records for future months before their window opens.
- Calendar clock must be read from UTC inside the trusted workstation action;
  caller-provided timestamps are for synthetic tests only.
- No retry after the close; on failed readiness inside the window, an
  on-time immutable flat/not-ready decision may be recorded under the frozen
  M028 rules. Transport or crash failure without a record yields a missed
  month, not a late reconstruction.

## Readiness and immutable record

Before a signal evaluation, metadata-only readiness may check:

1. BIS and OECD source transport hashes (SHA-256), maximum actual source
   date/month, and completeness through the immediately preceding calendar
   month for BIS and preceding-minus-one for OECD.
2. Broker quote time and positive finite Bid/Ask with Ask >= Bid; quote freshness
   at decision time, valid contract/lot rules and read-only margin.
3. Exact fixed currency mapping and minimum 4 executable nonzero targets.
4. Clock window and absence/presence of immutable month record.

No formation sign, target, lots or P/L may be calculated in readiness.
The source availability, raw and normalized hashes, metadata timestamps,
broker quote timestamps, and safety flags must be written to the immutable
decision before it counts as an accepted forward decision. Never infer that
data available *today* were available on an earlier decision date.

On-time record path:
`~/.local/share/mamba2-forward-paper/YYYY-MM-decision.json`.

Create using exclusive `x` semantics; preserve the existing record on a
collision and validate its canonical SHA-256 rather than rewriting it.
Never overwrite, delete or silently repair a previous decision.
Records may contain signals and target positions only when created inside
the prospective window. Performance observation is a separate milestone.

## Stage 1 authorization (THIS IMPLEMENTATION)

- Implement pure, deterministic month-generic calendar/time-window gates.
- Implement read-only record presence, verification, safe exclusive write
  mechanism with canonical hash, strictly optional local-files-only fixture
  execution; no network/MT5 broker imports or calls.
- Strictly refuse historical and missed-window record creation.
- Add synthetic tests including UTC timezone, boundaries (just before,
  exact open, exact close), Dec/Jan rollover, existing-record collision,
  corrupt record, canonical hash, and null cost evidence.
- Execute focused and full *native* tests on the checked-out M029 branch.
- Do not calculate a live/source-derived 2026-12 strategy signal, broker
  positions, strategy returns, or send/read real orders.
- Do not merge/deploy this branch to `main`.

## Stage 2 (NOT AUTHORIZED IN STAGE 1)

A separately authorized stage must bridge the pure gate to the frozen M028
source, broker-read-only quote/margin, and shadow target construction,
with an as-of timestamp/nonce check, on-time immutable record creation,
and safe source-not-ready flat records. This must be code-reviewed and
tested *before* 2026-12-07. No M029 real-source signal before that timestamp.

## Stage 3 forward assessment (FUTURE)

After 12 prospectively recorded and completed paper holding periods, a
separately frozen analysis may assess execution feasibility and cost-evidence
limitations. No claim of net executable profitability until actual commission,
slippage and financing evidence are supported. No past month backfill.

## Safety stop rules

Always refuse real orders, positions, order checks, MT5 trading history,
balance/equity retrieval, arbitrary shell, strategy optimization, historical
M028 decisions, and non-consented live deployment. A failed test stops
acceptance; no hidden fallback to historical evaluation.


## M029 Stage 1 accepted — 2026-11-12

- Protocol freeze: `b84456f256cd701738b20ff30dc5be37f4f36dfb`.
- Pure decision-window/readiness/immutable-file implementation:
  `03f0e0dfd918ad7c4827253c864a373a671abe8c`.
- Synthetic acceptance tests: `23234f97688d284476ccb4404cf1ce87407a60e1`.
- Exact tested branch HEAD: `eefcda398009a9d366bcbbb192d5a38b62df6191`.
- Local-agent full-native result commit:
  `2033f647e28d5d51ef52816c2c7115f4321853ce`.
- **345 passed, 2 skipped, 13 existing warnings**; M029 synthetic cases passed.
- No market data downloaded, broker initialized, signal computed or paper/live
  decision generated by this test action.
- Stage 1 is **CLOSED**. The implementation is limited to pure/local behavior.

## M029 Stage 2 protocol freeze — synthetic assembly only

**FROZEN BEFORE ANY M029 REAL-SOURCE SIGNAL OR PAPER DECISION**

The next implementation may build an importable, deterministic adapter from
*supplied* BIS raw bytes, OECD raw bytes, and supplied broker snapshot mappings
to an **unsealed draft paper record**. It must not fetch those bytes, initialize
MT5, or submit a paper/live order. The only Stage-2 execution is synthetic
fixtures in tests.

Order of operations:

1. Require the M029 UTC window to be `WINDOW_OPEN` *before* parsing input
   bytes, calculating formations, computing target lots, or writing a file.
   Missing months remain permanently refused.
2. Compute source hashes and source maximum date/month with the frozen BIS/OECD
   parsers. Apply the M028 month-specific source cutoff contract.
3. Validate the eight fixed direct-USD broker mappings and quote viability:
   finite positive Bid/Ask, Ask >= Bid, quote not in the future and no more
   than 300 seconds older than the supplied synthetic decision timestamp,
   valid positive margin for BUY and SELL.
4. Only with both source and at least 4 broker currencies ready may the
   existing M028 source/signal and shadow-position machinery run unchanged.
5. With valid source bytes but incomplete source month or broker readiness,
   assemble a not-ready **flat** draft; do not compute formation or target
   sides/lots. All four cost components remain null.
6. Stamp the draft with fixed scheduled UTC time, actual supplied test
   timestamp, raw/normalized source SHA-256, observed source/broker time,
   source cutoff evidence, broker quote timestamps and safety flags.
7. The existing M029 Stage-1 journal contract must validate and seal any
   later real decision; Stage 2 MUST NOT call it against workstation storage.
8. Do not consume M027 historical economics, M021 post-cutoff results,
   MT5 orders, trade history or balances. No real-data economics or results
   are authorized inside Stage 2.

The earlier frozen 10-minute processing window and original M027/M028
signals/sizing/cost rules are unchanged. Stage 3 (future) alone may connect
read-only real source/broker acquisition and the trusted UTC wall clock,
after a separate gate, code review and regression. Stage 3 must prohibit
source or quote snapshots acquired outside the actual processing window.

## M029 Stage 2 accepted — 2026-11-12

- Frozen Stage-2 protocol: `13bf3ff3931135fcf203921e6c6b4addf7257682`
  (recorded after Stage-1 accepted evidence).
- Synthetic supplied-source/broker assembly implementation:
  `c9e77aa3a95983684701fccff2223145596d3a44`.
- Safety repair to require explicit prior-ledger state for later months:
  `bd73d29751b376523e8fd4d74b357e5925744cf1`.
- Synthetic tests: `59b1a78ff5dcf3700af26dd7d27420c9a00f2795`
  and supplementary prior-state cases
  `05981c916e5a334200b3a42bbd55bfbebdcbd609`.
- Full native suite on exact tested Stage-2 HEAD
  `05981c916e5a334200b3a42bbd55bfbebdcbd609`:
  **356 passed, 2 skipped, 13 existing warnings**, 0 failures.
- Accepted result on `local-control-results`:
  `bcb873c4d1b812b290e1066fde12e943a7912e49`.
- No live source, broker initialization, signal-derived paper position,
  strategy performance or real orders were computed in acceptance.
- Source and broker inputs were supplied entirely as synthetic fixtures;
  the Stage-2 module has no network or MT5 imports and does not persist
  workstation records.

**Stage 2 CLOSED.** The remaining bridge to trusted UTC time, read-only
real-source/broker acquisition, and on-time immutable journal must be
implemented and independently accepted under the next, prospectively frozen
Stage-3 contract. No actual paper decision has been created.

