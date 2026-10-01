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
