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
