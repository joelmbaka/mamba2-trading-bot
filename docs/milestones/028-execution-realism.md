# Milestone 028 — Retail FX Execution Realism

Status: **STAGE 0 BROKER-METADATA PROTOCOL FROZEN — NO ECONOMICS AUTHORIZED**

Protocol date: 2026-10-01

Branch:

`execution-realism`

Base M027 closeout:

`e5564a99e1a0d57c6b165fd96b1e3c94e677ac43`

## Objective

M027 is closed with the prospectively frozen classification:

**SUPPORTED AS A GROSS PUBLIC-DATA APPROXIMATION**

M028 asks a different question:

> Can the M027 market object be translated into an executable retail-FX
> implementation using broker-observed symbol, spread, swap, commission, and
> leverage constraints without inventing historical costs or selecting
> currencies from M027 performance?

M028 does not alter or reopen M027.

No M027 parameter, source, signal, lookback, rate lag, volatility target,
currency contribution, fold, or economic result may be retuned inside M028.

## Why Stage 0 is metadata-only

The repository already models historical Bid/Ask spread when tick-derived Ask
data exist, plus optional explicit commission and slippage. It also explicitly
documents that:

- actual commission is not yet proven;
- slippage is not proven;
- swap/overnight financing is not modeled;
- leverage/margin is not modeled.

Therefore M028 must establish broker evidence before any net-performance
calculation.

Current broker metadata must never be silently treated as historical
1980–2020 metadata.

## Frozen broker/account source

Stage 0 uses only the MetaTrader 5 terminal session currently authenticated on
the Dell research machine.

The probe is read-only.

Allowed MT5 calls:

- `initialize`
- `shutdown`
- `terminal_info`
- `version`
- `account_info`
- `symbols_get`
- `symbol_info`
- `symbol_info_tick`
- `symbol_select` only when required to expose metadata/quotes

Forbidden in Stage 0:

- `order_send`
- `order_check`
- order modification or cancellation
- position close
- any real order placement
- `history_deals_get`
- `history_orders_get`
- reading open-position P/L
- reading balance/equity
- strategy replay
- M027 economics
- M021 post-cutoff economics

The probe must not return the MT5 login/account number or password.

## Frozen M027 source universe

The broker-availability probe starts from the already frozen 25-currency M027
universe only:

`AUD, CAD, CHF, CLP, CNY, COP, CZK, DKK, EUR, GBP, HUF, IDR, INR, ISK, ILS, JPY, KRW, MXN, NOK, NZD, PLN, RON, RUB, SEK, ZAR`

Frozen M027 universe SHA-256:

`db9e1f4438fd582a0c2903f2459e290e30450bfc76365f2bbe91553d45b51c00`

No currency may be added because the broker happens to offer it.

No currency may be removed because it lost money in M027.

## Frozen broker-symbol mapping rule

For each frozen non-USD currency `C`, Stage 0 considers only MT5 symbols whose
publisher metadata says:

- `currency_base == C` and `currency_profit == USD`, or
- `currency_base == USD` and `currency_profit == C`.

The symbol name itself is not used to infer the currencies when those metadata
fields disagree.

A symbol is mechanically eligible for mapping only when:

- symbol metadata are available;
- contract size is finite and strictly positive;
- point/tick size is finite and strictly positive;
- minimum volume is finite and strictly positive;
- trade mode is not disabled.

If exactly one mechanically eligible direct-USD symbol exists for currency
`C`, the mapping is accepted.

If zero exist, `C` is marked **UNAVAILABLE**.

If more than one exists, `C` is marked **AMBIGUOUS** and no symbol is chosen
in Stage 0.

No ambiguity may be resolved using M027 returns.

The Stage-0 executable candidate universe is the set of unambiguous mappings
only. It must be listed and hashed before any M028 economics.

The accepted-universe hash serialization is frozen as the uppercase accepted
currency codes sorted lexicographically, joined by a single newline character
with no trailing newline, then SHA-256 encoded as UTF-8.

Minimum continuation gate:

**4 unambiguous direct-USD currencies**

Fewer than 4 closes M028 before economics.

Passing this gate does not authorize economics by itself.

## Frozen per-symbol metadata schema

For each accepted or candidate broker symbol, Stage 0 may report only
execution-relevant metadata:

- symbol name;
- base currency;
- profit/quote currency;
- margin currency;
- trade mode;
- digits;
- point;
- trade tick size;
- trade tick value;
- trade tick value profit/loss where available;
- trade contract size;
- volume min/max/step;
- margin initial/maintenance where available;
- swap mode;
- swap long;
- swap short;
- triple-swap rollover weekday;
- most recent quote timestamp;
- current/last Bid;
- current/last Ask;
- current spread in points derived as `(ask - bid) / point` when valid.

The spread observation is a **single current metadata snapshot**, not a
historical cost series.

It may not be applied to M027's 1980–2020 returns in Stage 0.

## Frozen account metadata schema

Stage 0 may report:

- broker/server identity;
- account currency;
- account leverage;
- margin mode;
- account trade mode/type if exposed.

Stage 0 must not report:

- login/account number;
- password;
- balance;
- equity;
- margin used;
- free margin;
- open profit/loss.

## Commission rule

MetaTrader symbol metadata do not reliably encode broker commission schedules.

Stage 0 must therefore report commission as:

**UNPROVEN**

unless the broker exposes an explicit commission field through the allowed
metadata calls.

Stage 0 must not infer commission from M027 returns, public guesses, or a
different broker.

A future M028 stage may establish commission through official broker
documentation or a separately frozen, privacy-preserving read-only evidence
probe.

## Swap / carry rule

M027's excess-return approximation already includes lagged short-rate
differential carry.

Retail MT5 swap is an implementation financing mechanism and must not simply be
added on top of M027 carry as if it were a separate independent return.

Stage 0 records current broker swap metadata only.

Before any M028 economics, a later protocol must explicitly freeze whether the
retail implementation:

1. replaces the M027 carry approximation with broker swap evidence; or
2. evaluates only a forward paper period where actual broker swap can be
   observed.

No historical 1980–2020 swap series may be fabricated from today's broker
settings.

## Leverage / margin rule

Stage 0 records current account leverage and symbol margin metadata only.

No leverage cap is introduced into M027 after seeing its positive result.

Before any M028 economics, a later protocol must prospectively freeze:

- the exact account leverage contract;
- gross/notional exposure calculation;
- symbol margin calculation;
- any portfolio gross-leverage ceiling;
- the handling of infeasible target weights.

No economic result may be inspected before those rules are frozen.

## Stage 0 output

The first Stage-0 report must contain:

- feature SHA;
- terminal build/version metadata;
- broker/server identity;
- non-sensitive account metadata;
- all 25 currency mapping outcomes;
- accepted symbol mapping table;
- unavailable currencies;
- ambiguous currencies;
- accepted-universe ordered list;
- accepted-universe SHA-256;
- current spread/swap/contract metadata for mapped symbols;
- continuation-gate status;
- explicit `commission_proven: false` unless directly exposed;
- safety flags.

No P/L, Sharpe, drawdown, terminal wealth, currency contribution, fold return,
or M027 reclassification may appear.

## Stage 0 continuation rule

If at least 4 unambiguous symbols exist, Stage 0 passes the broker-availability
gate.

The next stage may only investigate evidence quality for:

- historical/current spread;
- commission;
- swap/financing;
- leverage/margin.

It still may not run strategy economics until the exact executable cost and
leverage contract plus evaluation period are frozen.

If sufficiently faithful retrospective execution data cannot be established,
M028 must not retrofit today's costs onto 1980–2020 and call that a real
backtest.

The allowed fallback is a separately frozen forward-paper implementation.

## Anti-selection rule

M028 must not:

- inspect M027 per-currency contribution to decide broker symbols;
- drop currencies because they were negative in M027;
- privilege CNY, COP, JPY, or any other currency because of known M027/M024
  outcomes;
- search sides, sessions, weekdays, lookbacks, rate lags, volatility targets,
  or subperiods;
- alter M027's accepted result.

## Safety

No real trading is authorized by M028.

No MT5 order API may be called.

No merge to `main` is authorized.

No deployment is authorized.
## Stage-0 broker-availability result accepted — 2026-10-01

Accepted command:

`mamba2-m028-stage0-broker-metadata-v1`

Accepted result commit:

`3258372afbf11aa8178cddd54c61b810c5e514d6`

Feature SHA:

`de05a0207c6679e58f17fded969ab3e5401c2d68`

Result:

- frozen M027 currencies inspected: **25**
- unambiguous direct-USD mappings: **22**
- unavailable: **CNY, ISK, RON**
- ambiguous: **none**
- continuation gate minimum: **4**
- continuation gate: **PASS**
- accepted mapped-universe SHA-256:
  `5f1ae15c35b3b20e24b4f999c7628d3534b54e30eb535295a69e359f285dd996`

Mapped currencies:

`AUD, CAD, CHF, CLP, COP, CZK, DKK, EUR, GBP, HUF, IDR, ILS, INR, JPY, KRW, MXN, NOK, NZD, PLN, RUB, SEK, ZAR`

Observed terminal/account metadata:

- terminal: **MetaTrader 5 build 6215**
- server: **MetaQuotes-Demo**
- account currency: **USD**
- account leverage: **100:1**
- margin mode: **2**
- commission metadata fields exposed: **none**
- commission status: **UNPROVEN**

Safety:

- market-data read only: **true**
- order API called: **false**
- position change API called: **false**
- trade history read: **false**
- account login returned: **false**
- balance/equity returned: **false**
- historical economics run: **false**
- M027 economics rerun: **false**
- M021 post-cutoff outcomes used: **false**

### Quote-quality observation

The Stage-0 mapping gate is intentionally metadata-based and is not the same as a live-quote gate.

At the accepted snapshot:

- six mapped symbols had non-zero quotes dated 2026-10-01:
  **USDCHF, EURUSD, GBPUSD, USDJPY, NZDUSD, USDSEK**;
- AUDUSD and USDCAD had non-zero quotes but their latest quoted timestamps were
  **2026-09-25**;
- the remaining fourteen mapped symbols returned zero Bid/Ask with epoch-like
  `1970-01-01T00:00:00Z` quote timestamps.

Therefore the 22-currency mapping result proves broker symbol availability only.
It does **not** prove that all 22 are currently streamable/executable.

### Publisher incident

The first publication attempt encountered a control-plane JSON serialization
error because a subprocess timeout/error field could contain `bytes`. The
strategy probe itself remained read-only. The same command ID subsequently
published the accepted result above. No economics or order operation occurred.

The control publisher was repaired separately on `local-control` to decode
bytes deterministically before JSON serialization.

## Stage-0 stop/continuation decision

Stage 0 passes its pre-frozen broker-availability gate.

Economics remain **NOT AUTHORIZED**.

Before any executable-performance calculation, M028 must now establish:

1. which mapped symbols have mechanically valid current quote streams;
2. whether historical spread evidence is available for those symbols;
3. whether commission can be proven for the selected paper/broker environment;
4. how current broker swap relates to M027's already-included carry approximation;
5. the exact leverage/margin contract and infeasible-weight handling;
6. whether the valid path is retrospective execution research or forward paper only.

Today's MetaQuotes-Demo costs must not be retrofitted onto M027's 1980–2020
history and presented as historical executable costs.
## Stage-1 execution-evidence protocol freeze — 2026-10-01

Status: **FROZEN BEFORE ANY M028 STRATEGY ECONOMICS**

Stage 1 answers only:

> Does the currently authenticated MetaQuotes-Demo environment provide enough
> mechanically usable quote, tick-history, and margin evidence to support a
> forward paper implementation, and can retrospective execution costs be
> established without inventing commission or historical swap?

Stage 1 must not calculate strategy P/L, Sharpe, drawdown, wealth, contribution,
or any M027 reclassification.

### Frozen input universe

Start only from the 22 unambiguous Stage-0 mappings frozen at:

`5f1ae15c35b3b20e24b4f999c7628d3534b54e30eb535295a69e359f285dd996`

No Stage-0 unavailable currency may be substituted with a cross.

### Mechanical current-quote viability

For each mapped symbol, obtain one current `symbol_info_tick` snapshot.

Define the Stage-1 reference tick time as the maximum tick timestamp among
mapped symbols that have finite positive Bid and Ask.

A mapped symbol is **QUOTE_VIABLE** only when:

- Bid is finite and > 0;
- Ask is finite and > 0;
- Ask >= Bid;
- tick timestamp is valid and within **300 seconds** of the Stage-1 reference
  tick time.

This is an execution-availability rule only. It does not use M027 returns.

Minimum forward-paper quote gate:

**4 QUOTE_VIABLE currencies**

Fewer than 4 => Stage 1 stops with `FORWARD_PAPER_NOT_READY`.

### Frozen tick-history coverage checkpoints

For QUOTE_VIABLE symbols only, query read-only MT5 tick history at exactly
these UTC windows, each **12:00:00–12:59:59**:

- 2026-09-30
- 2026-09-01
- 2026-08-03
- 2026-07-01
- 2026-04-01
- 2026-01-05
- 2025-10-01

For each symbol/window report only:

- tick count;
- first tick timestamp;
- last tick timestamp;
- count with finite positive Bid/Ask;
- spread-points min/median/max over valid positive Bid/Ask ticks.

No price return, direction, signal, or P/L statistic may be computed.

Checkpoint presence is metadata evidence only; it does not authorize using
current broker costs as historical 1980–2020 costs.

### Frozen margin evidence

For each QUOTE_VIABLE symbol, Stage 1 may call read-only
`order_calc_margin` for exactly:

- **1.00 lot BUY** at the current Ask;
- **1.00 lot SELL** at the current Bid.

It may report only the calculated account-currency margin values.

`order_check` and `order_send` remain forbidden.

### Commission evidence

Stage 1 does not inspect trade history.

Because Stage 0 exposed no commission metadata fields, commission remains:

**UNPROVEN**

No zero-commission assumption is authorized.

### Swap evidence

Stage 1 may carry forward the current `swap_long`, `swap_short`, `swap_mode`,
and rollover-day metadata from Stage 0.

It must explicitly classify historical swap evidence as **UNPROVEN** unless an
actual time series is available from the allowed read-only broker data path.

Current swap settings must not be backfilled through historical M027 months.

### Stage-1 path classification

Stage 1 returns exactly one path classification:

**FORWARD_PAPER_NOT_READY**

when fewer than 4 currencies pass current quote viability or fewer than 4 have
valid current margin calculations.

Otherwise, when quote/margin gates pass but commission or historical swap is
unproven:

**FORWARD_PAPER_ONLY**

Retrospective net-execution economics are not authorized under that outcome.

`RETROSPECTIVE_NET_EXECUTION_READY` may be returned only if both commission
and historical swap evidence are independently proven without inference.

### Safety

Allowed MT5 calls:

- initialize/shutdown;
- symbol_info/symbol_info_tick/symbol_select;
- copy_ticks_range;
- order_calc_margin.

Forbidden:

- order_send;
- order_check;
- position modification/close;
- history_deals_get/history_orders_get;
- balance/equity/open-P&L return;
- strategy replay;
- M027 rerun;
- M021 post-cutoff outcome use.

No merge/deploy/live trading is authorized.
## Stage-1 v1 harness result — NO EVIDENCE ACCEPTED

Command:

`mamba2-m028-stage1-execution-evidence-v1`

Result commit:

`4b54cac700749c90655bf2ee8dd243fffbb8f2f0`

Outcome:

- process exit: **-9**
- hard timeout: **180 seconds**
- probe payload: **none**
- path classification: **not produced**

This is a control-harness timeout, not a failed strategy or broker-evidence gate.

No Stage-1 evidence from v1 is accepted.

Safety remained intact:

- read-only market-data path only;
- no order placement or validation;
- no position changes;
- no trade-history reads;
- no strategy replay;
- no M027 rerun;
- no M021 post-cutoff outcome use.

Implementation repair is permitted without changing the frozen Stage-1 protocol:
split current quote/margin inspection from historical tick checkpoints and bound
each historical-symbol probe independently so one slow MT5 history request cannot
block the complete evidence stage.
## Stage-1 v2 harness result — NO EVIDENCE ACCEPTED

Command:

`mamba2-m028-stage1-execution-evidence-v2`

Result commit:

`75f52146830ebbb16ae8e0e8e0e6802700c77694`

Outcome:

- snapshot process exit code: **0**
- helper timed out: **true** after 60 seconds
- probe payload: **none**
- path classification: **not produced**

The zero exit code plus timeout indicates the Wine/MT5 parent completed but
descendant processes retained PIPE-backed descriptors. This is a transport/
publication-harness problem, not a broker-evidence or strategy result.

No Stage-1 v2 evidence is accepted.

Implementation repair is permitted without changing the Stage-1 protocol:
use file-backed JSON output with non-PIPE standard streams so Wine descendants
cannot keep result transport open after the probe process completes.
## Stage-1 accepted result — FORWARD_PAPER_ONLY

Accepted command:

`mamba2-m028-stage1-execution-evidence-v3`

Accepted result commit:

`bf90b33409aa78d303d0928404e73f3d1a7da1bf`

Feature SHA:

`2dcbdb5e05c5f7e9a1a06fb711f0c9f85bfd7455`

Implementation:

`v3-file-backed-bounded`

### Frozen gate result

- current quote-viable currencies: **8**
- quote gate minimum: **4**
- quote gate: **PASS**
- valid current margin currencies: **8**
- margin gate minimum: **4**
- margin gate: **PASS**
- commission proven: **false**
- historical swap proven: **false**
- path classification: **FORWARD_PAPER_ONLY**

Quote- and margin-viable currencies:

`AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK`

### Observed 1.00-lot margin requirements in account currency

- AUDUSD: BUY **694.13**, SELL **694.12**
- USDCAD: BUY **1000.00**, SELL **1000.00**
- USDCHF: BUY **1000.00**, SELL **1000.00**
- EURUSD: BUY **1129.55**, SELL **1129.55**
- GBPUSD: BUY **1321.83**, SELL **1321.82**
- USDJPY: BUY **1000.00**, SELL **1000.00**
- NZDUSD: BUY **560.97**, SELL **560.96**
- USDSEK: BUY **1000.00**, SELL **1000.00**

These are current MetaQuotes-Demo margin calculations only. They are not
historical margin evidence and do not authorize live trading.

### Historical tick checkpoint evidence

The seven prospectively frozen one-hour checkpoints were successfully returned
for **AUD, CAD, EUR, GBP, JPY**. Every returned tick in those successful
windows had finite positive Bid/Ask values.

Historical retrieval timed out with no accepted payload for:

`CHF, NZD, SEK`

This partial tick-history result does not upgrade the path to retrospective
execution readiness. It is retained only as execution-data evidence.

Representative observed median spread-point evolution across the successful
checkpoint set:

- AUDUSD: roughly **4 points** in 2025-10/2026-01, falling to about **1 point**
  by the 2026-07 through 2026-09 checkpoints;
- USDCAD: roughly **4 points** in 2025-10 through 2026-04, then generally
  around **0–1 point** in later checkpoints;
- EURUSD and GBPUSD: several later checkpoint medians are **0 points** in the
  broker tick feed; this is recorded as observed data and must not be
  interpreted as proof of zero executable cost;
- USDJPY: checkpoint medians generally ranged from about **1–4 points**.

### Stage-1 conclusion

Stage 1 mechanically supports a forward-paper path for the eight viable
currencies above.

Stage 1 does **not** support a retrospective net-execution backtest because:

1. commission remains unproven;
2. historical swap/financing remains unproven;
3. three viable symbols did not complete the frozen historical tick probe;
4. today's broker settings must not be retrofitted onto M027's 1980–2020 history.

No M028 strategy economics have been run.

### Safety evidence

- market-data path read-only: **true**
- margin calculation only: **true**
- order validation: **not called**
- order placement: **not called**
- position changes: **not called**
- trade history read: **false**
- balance/equity returned: **false**
- strategy replay run: **false**
- M027 economics rerun: **false**
- M021 post-cutoff outcomes used: **false**

Stage-1 is now closed. Do not rerun or retune it to improve coverage or
execution-data appearance.
## Stage-2 forward-paper contract freeze — 2026-10-01

Status: **FROZEN BEFORE ANY FORWARD-PAPER STRATEGY OUTCOME**

Stage 1 mechanically classified M028 as:

**FORWARD_PAPER_ONLY**

Stage 2 therefore defines an implementation contract only. It may build and
validate deterministic shadow-position machinery, but it may not inspect
forward strategy P/L before this contract is committed.

### Fixed forward-paper currency set

Only the eight Stage-1 quote- and margin-viable currencies may participate:

`AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK`

Frozen broker mapping:

- AUD -> AUDUSD
- CAD -> USDCAD
- CHF -> USDCHF
- EUR -> EURUSD
- GBP -> GBPUSD
- JPY -> USDJPY
- NZD -> NZDUSD
- SEK -> USDSEK

No cross pair may substitute for a missing direct-USD symbol.

At each decision timestamp a currency is execution-eligible only when:

1. its M027-compatible signal and ex-ante volatility are available;
2. its current broker Bid and Ask are finite and positive with Ask >= Bid;
3. its quote is within 300 seconds of the freshest positive quote among the
   fixed eight currencies;
4. a positive read-only margin calculation is available for the required side;
5. the rounded target meets broker minimum-volume rules.

At least **4 non-zero execution-eligible currencies** are required to open or
rebalance the paper portfolio. Otherwise the decision is recorded as
`FORWARD_PAPER_NOT_READY` and the paper portfolio is flat for that holding
period.

### Signal and volatility contract — unchanged from M027

For every execution-eligible currency:

- market object remains USD value of one foreign-currency unit;
- approximate daily excess log return remains
  `dlog(spot) + (r_foreign - r_usd) / 261`;
- month M carry uses only completed-month M-1 rates;
- formation signal is the sum of the prior **12 completed calendar months**;
- positive formation = long foreign currency;
- negative formation = short foreign currency;
- zero formation = flat;
- annualized ex-ante volatility uses the M027 centered EWMA variance;
- EWMA decay remains **60/61**;
- annualization remains **261**;
- target volatility remains **40% per instrument**.

No signal threshold, alternate lookback, side filter, volatility floor,
session rule, weekday rule, or performance-based currency filter is allowed.

### Prospective source-refresh rule

M027 itself remains closed and its frozen economics are never rerun.

M028 may refresh only the same BIS XRU and OECD IR3TIB public source contracts
prospectively to construct new completed-month signals.

At every decision:

- the raw BIS and OECD payloads must be hashed;
- normalized inputs must be hashed;
- only observations published and available by the decision timestamp may be
  used;
- the immediately prior calendar month must be complete for required BIS spot;
- the rate month required by the frozen one-month carry lag must be present;
- no interpolation or source substitution is allowed;
- the exact source hashes and source maximum dates/months are written to the
  immutable paper decision record before target construction.

### Decision/rebalance timestamp

The paper decision occurs at **12:00:00 UTC on the fifth Monday-Friday business
day of each calendar month**.

Business-day counting here is mechanical Monday-Friday only; no country
holiday calendar is introduced.

The signal uses only completed calendar months before the decision month.

If the prospective source-completeness gate is not satisfied at that timestamp,
the month is skipped and remains flat. There is no late entry later in the
same month.

Earliest permitted M028 paper decision:

**2026-10-07T12:00:00Z**

No backfill of October or any earlier month is allowed after its decision time.

### Foreign-currency signal -> broker side mapping

For broker pairs with foreign currency as base and USD as quote:

`AUDUSD, EURUSD, GBPUSD, NZDUSD`

- long foreign -> BUY pair;
- short foreign -> SELL pair.

For broker pairs with USD as base and foreign currency as quote:

`USDCAD, USDCHF, USDJPY, USDSEK`

- long foreign -> SELL pair;
- short foreign -> BUY pair.

This orientation is mechanical and may not be changed after observing paper
results.

### Raw portfolio weights

Let `sigma_i` be the M027 ex-ante annualized volatility and `s_i` the frozen
formation sign.

Per-instrument raw M027 scaling:

`u_i = s_i * 0.40 / sigma_i`

For N execution-eligible non-flat currencies:

`w_i_raw = u_i / N`

This is exactly the M027 equal-weight aggregation translated into target
notional weights.

### Execution-only gross leverage cap

Forward paper uses a prospectively frozen gross notional leverage ceiling:

**4.0x reference equity**

Define:

`G = sum(abs(w_i_raw))`

`gross_scale = min(1, 4.0 / G)`

`w_i_gross = w_i_raw * gross_scale`

The scale is common across all currencies. No currency-specific clipping or
redistribution based on expected or historical performance is allowed.

Both uncapped and capped weights must be recorded so the effect of execution
realism remains auditable.

### Reference paper capital

Forward paper uses fixed reference capital:

**USD 10,000**

This is a sizing denominator, not a simulated account balance and not a claim
about deployable user capital.

Until complete cost accounting is proven, target sizing does not compound
paper P/L. Every monthly target is based on the same USD 10,000 reference
capital.

### Margin utilization gate

After gross-cap scaling and broker volume rounding, projected read-only margin
may use at most:

**25% of reference equity = USD 2,500**

If aggregate projected margin exceeds that amount, all non-zero target lots
are scaled down by one common factor and rounded toward zero again.

There is no performance-based reallocation after margin scaling.

If fewer than four non-zero positions remain after volume/margin constraints,
the entire monthly paper portfolio is flat and classified
`FORWARD_PAPER_NOT_READY`.

### Lot conversion and rounding

Target absolute USD notional is:

`abs(w_i_final) * 10,000`

For foreign-base/USD-quote pairs:

`lots = USD_notional / (contract_size * current_mid)`

For USD-base/foreign-quote pairs:

`lots = USD_notional / contract_size`

where:

`current_mid = (Bid + Ask) / 2`

Lots are rounded **toward zero** to the broker `volume_step`.

- below `volume_min` -> zero position;
- above `volume_max` -> capped at `volume_max` without redistribution;
- no rounding-up is permitted.

### Paper fill and mark convention

For a paper BUY:

- entry/increase price = current Ask;
- exit/decrease/mark price = current Bid.

For a paper SELL:

- entry/increase price = current Bid;
- exit/decrease/mark price = current Ask.

Bid/Ask spread is therefore represented directly by the shadow fills/marks.

No mid-price fill is permitted.

### Commission, slippage, and financing

Commission remains **UNPROVEN**.

Slippage remains **UNOBSERVED** because no real order is sent.

Historical broker swap remains **UNPROVEN**.

M027 carry may be used only to construct the signal/volatility input. It must
**not** be added as paper execution P/L.

The forward paper ledger must keep these fields separate:

- quote/spread-based spot P/L;
- commission: null / UNPROVEN;
- slippage: null / UNOBSERVED;
- broker financing/swap: null until prospectively verified;
- net P/L: null while any required cost component is unresolved.

Current swap metadata may be snapshotted for evidence, but it cannot be
silently converted into historical or realized net P/L.

### Immutable decision/ledger schema

Every monthly paper decision must record at least:

- decision timestamp and holding-period identifier;
- feature/code SHA;
- raw BIS/OECD SHA-256 hashes;
- normalized-input hashes and maximum source dates/months;
- fixed eight-currency universe;
- per-currency eligibility reason;
- 12-month formation value and sign;
- ex-ante volatility;
- raw M027 scaling and equal-weight target;
- gross-cap scale and resulting weight;
- broker symbol and side;
- Bid, Ask, midpoint and quote timestamp;
- contract size and volume min/max/step;
- unrounded and rounded target lots;
- read-only projected margin;
- any common margin scale;
- paper fill price;
- prior paper position and target paper position;
- cost-evidence status fields;
- all safety flags.

Decision files are append-only and content-hashed. A prior decision record may
not be overwritten after its decision timestamp.

### Observation and conclusion rule

Operational diagnostics may be reviewed immediately: source readiness, quote
freshness, sizing, margin, ledger integrity, and cost-evidence completeness.

No claim that the executable strategy is supported/not supported may be made
until at least:

**12 completed monthly forward-paper holding periods**

have been recorded prospectively under this frozen contract.

Before that threshold:

- no symbol pruning based on paper P/L;
- no parameter tuning;
- no side/session/weekday changes;
- no retrospective re-entry of skipped months;
- no annualized Sharpe or strategy-support classification used to change the
  contract.

Any future change to signal, execution universe, leverage cap, margin cap,
decision timestamp, cost treatment, or observation threshold requires a new
named milestone.

### Stage-2 implementation scope

Stage 2 may now implement and unit-test pure shadow-position machinery for:

- decision timestamps;
- broker-side orientation;
- raw M027 weight translation;
- common gross-cap scaling;
- lot conversion and toward-zero rounding;
- common margin scaling;
- bid/ask paper fill/mark conventions;
- immutable decision-record construction.

Stage 2 must not:

- send or validate a real broker order;
- modify a position;
- run retrospective M028 strategy economics;
- inspect M021 post-cutoff outcomes;
- rewrite M027 economics;
- create paper performance outcomes before the first real prospective decision
  timestamp.
## Stage-2 implementation accepted — 2026-10-01

Protocol freeze:

`3dd84c480d13adf598532489e6519f92683493f2`

Accepted implementation feature SHA:

`7ce4a54c9ac0e7d4083f1bbd58cc2284bffa1355`

Implementation files:

- `mamba2/backtest/m028_forward_paper.py`
- `tests/test_m028_forward_paper.py`

Focused validation result:

`88c0aa33ce2bc7fe89c233a3fb3b181b993e228a`

- focused tests: **17 passed**
- `py_compile`: **PASS**

Full native regression result:

`ec66dbc297572d59f0880a996600e459bbfc37b6`

- **314 passed**
- **2 skipped**
- **13 existing warnings**

Focused validation safety:

- broker initialized: **false**
- market data read: **false**
- real order API called: **false**
- position change API called: **false**
- trade history read: **false**
- historical strategy economics run: **false**
- forward strategy outcome computed: **false**
- M027 economics rerun: **false**
- M021 post-cutoff outcomes used: **false**

Stage 2 is closed. Its leverage, margin, timing, lot-rounding, cost-status,
and observation rules may not be changed inside M028 after prospective
forward outcomes begin.
## Stage-3 prospective readiness and first-decision protocol freeze — 2026-10-01

Status: **FROZEN BEFORE THE FIRST FORWARD-PAPER SIGNAL IS OBSERVED**

Stage 3 operationalizes the already frozen Stage-2 contract for the first
prospective paper decision.

First permitted decision timestamp:

**2026-10-07T12:00:00Z**

Decision identifier:

`2026-10`

### Stage-3A readiness probe — allowed before decision time

A pre-decision readiness probe may inspect only whether the frozen data and
broker prerequisites are becoming available.

It may:

- download the same BIS XRU and OECD IR3TIB source contracts;
- hash the raw source bytes;
- parse source metadata and report only source maximum date/month;
- test the frozen October source cutoffs:
  - BIS spot through **2026-09-30**;
  - OECD rates through **2026-08**;
- inspect current quote freshness for the fixed eight Stage-1 currencies;
- inspect current positive read-only margin availability;
- report counts/lists and safety metadata.

It must not report or compute:

- 12-month formation values or signs;
- ex-ante volatility values;
- target weights;
- broker BUY/SELL target sides;
- target lots;
- paper fills;
- strategy P/L or any performance statistic.

Readiness classification is mechanical:

- source cutoff fails -> `SOURCE_NOT_READY`;
- source cutoff passes but fewer than 4 quote+margin viable currencies ->
  `BROKER_NOT_READY`;
- both gates pass -> `READY_FOR_SCHEDULED_DECISION`.

A readiness pass does not permit an early paper decision.

### Stage-3B first-decision runtime — code may be built/tested now

The decision runtime must refuse to emit the October paper decision before
`2026-10-07T12:00:00Z`.

At or after that timestamp it may execute exactly one October decision under
the frozen Stage-2 rules.

At the actual decision:

1. fetch the same BIS/OECD source contracts once;
2. hash raw bytes and normalized panels;
3. require source completeness through Sep-2026 spot / Aug-2026 rates;
4. construct the M027-compatible approximate return history without changing
   source identity, quote direction, units, or carry lag;
5. compute formation through **2026-09-30** only;
6. compute the frozen lagged EWMA ex-ante volatility;
7. restrict to the fixed eight Stage-1 currencies;
8. take one broker quote/margin snapshot;
9. apply the Stage-2 execution-eligibility, equal-weight, 4.0x gross-cap,
   lot-rounding, and 25% margin-cap rules;
10. write one immutable `2026-10` decision record.

If any gate leaves fewer than four non-zero executable targets, the immutable
October decision is flat with `FORWARD_PAPER_NOT_READY`.

There is no later October retry or late entry after the decision timestamp.

### Append-only first-decision record

The runtime must refuse to overwrite an existing `2026-10` decision record.

Decision output is signal/position evidence only. It must not calculate a
holding-period return at decision creation.

Cost fields remain:

- commission: null / `UNPROVEN`;
- slippage: null / `UNOBSERVED`;
- financing: null until prospectively verified;
- net P/L: null.

### Test boundary before October 7

Before the first decision timestamp, tests may use synthetic formation,
volatility, quote, and margin fixtures only.

No live/source-derived October signal sign, weight, side, lot, or paper P/L may
be inspected early.

### Safety

- no real order placement;
- no order validation endpoint;
- no position modification;
- no trade-history read;
- no balance/equity return;
- no retrospective M028 net economics;
- no M027 rerun;
- no M021 post-cutoff outcomes;
- no live promotion.
## Stage-3A readiness result — SOURCE_NOT_READY

Readiness command:

`mamba2-m028-stage3-readiness-v1`

Result commit:

`8b715961e58c2e8a56069d26c780db52d46b194c`

Feature SHA observed by readiness probe:

`58649c4625872e8ae12f31103cfcc497cde3cdcd`

Mechanical source result:

- BIS spot maximum date: **2026-09-29**
- required BIS spot through: **2026-09-30**
- OECD rate maximum month: **2026-08**
- required OECD rate month: **2026-08**
- source gate: **FAIL**

Mechanical broker result:

- quote viable: **8 / 8**
- margin viable: **8 / 8**
- joint viable: **8 / 8**
- broker gate: **PASS**

Joint viable currencies:

`AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK`

Readiness classification:

**SOURCE_NOT_READY**

This is expected pre-decision readiness evidence only. The October signal was
not computed, no target side/lots were created, and no forward outcome was
observed.

Safety flags all remained false for signal reporting, target construction,
orders, position changes, trade-history reads, balance/equity return, M027
rerun, and M021 post-cutoff use.

The Stage-3 protocol remains unchanged. The source gate may be checked again
before or at the scheduled decision, but there is no early decision.
