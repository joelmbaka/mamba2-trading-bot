# M029 Stage 3 — Frozen operational and live-readiness protocol

**Status: FROZEN BEFORE ANY STAGE-3 REAL-SOURCE SIGNAL, BROKER QUOTE READ, OR PAPER DECISION**

- Frozen on: 2026-11-12
- Branch: `prospective-paper-recovery`
- Parent accepted code and handoff HEAD: `917be98f784fe0842521b76a76ebf41a5654786c`
- Related frozen strategy/protocol: `docs/milestones/029-prospective-paper-recovery.md`
- This is an **operational/integration protocol**, not permission to trade, read broker accounts or run the future paper decision.

## 1. Accepted evidence and limits

The operator reported an **isolated compatibility smoke test** on 2026-11-12:

- Wine **11.21 Staging**, configured as Windows 11, successfully opened a copied MT5 terminal.
- Visible window: `MetaTrader 5 - Netting`, without the previously seen debugger-warning popup.
- The test did not use credentials, access broker data, place orders or modify the original MT5 installation.
- System Wine remains **9.0**; pre-existing `~/.mt5` and native/Wine Python test environments remain preserved.
- The application repository remained clean at `917be98` at the reported test.
- **Not yet proven:** MetaTrader5 Python package/API compatibility, terminal initialization from Python, symbol metadata, quote freshness, margin query support, read-only broker session viability, scheduler correctness or real-source as-of guarantees.

The above are operator-reported compatibility observations, not a test result independently produced by this repository. Launching the MT5 GUI does not imply the broker bridge works.

The Stage-2 accepted full native regression remains **356 passed / 2 skipped** with 13 existing warnings. No successful forward-paper decision, net executable edge or live-trading authorization exists.

## 2. Invariants that Stage 3 MUST NOT change

- Keep the M027 12-completed-month momentum formation and the **same** carry-aware BIS XRU / OECD IR3TIB public source identities, normalization, one-month carry lag and lagged EWMA volatility; never refresh M027 terminal economics.
- Keep the M028 fixed eight currencies (AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK), direct-USD broker pair orientations, equal weighting, 40% target per-currency ex-ante volatility, USD 10,000 noncompounding reference capital, 4.0x gross cap, 25% projected-margin cap and four nonzero-position minimum.
- Keep broker lot rounding toward zero and side-appropriate Ask/Bid paper fill/mark rules.
- Keep commission **UNPROVEN**, slippage **UNOBSERVED**, financing/swap **UNPROVEN** and net P/L **null** until supported by separately authorized evidence.
- M029 begins **2026-12**. October and November 2026 are irretrievably missed; do not recompute, backfill or invent their records or results.
- No strategy parameter search, universe selection by realized performance, M021 post-cutoff outcome use, retrospective M028 net economics, real orders, order checks, broker position changes or live deployment.

## 3. Stage 3 subdivisions and authorization boundaries

### Stage 3A — implementation and synthetic validation (authorized after this freeze)

Implement narrowly scoped, allowlisted actions and testable adapters for:

1. Inspecting **only** the isolated Wine 11.21 / Windows 11 setup, without changing system Wine 9.0, the source `~/.mt5` prefix, or existing pinned `.venv-wine` and `.venv-native-control` environments.
2. Locating/validating a separately isolated M029 bridge runtime. Do not assume the copied terminal includes a working Python/MT5 package; retain Python 3.10 / NumPy / MetaTrader5 accepted pins where applicable unless independently proven and separately approved.
3. Creating a metadata-only readiness schema; strict allowlisted terminal/symbol/quote/margin adapter with mock transport; actual, explicit UTC `fetch_started`, `fetch_finished`, `quote_observed`, `quote_tick` and `decision_created` timestamps.
4. Enforcing clock and source/quote evidence gates in the adapter and sealed ledger, rechecking the clock **after** potentially blocking network/broker operations and **immediately before** the exclusive journal write.
5. Providing tests with synthetic BIS/OECD bytes, synthetic broker API results, synthetic system clock and temporary filesystem only. Assert that the real source downloader, terminal initialization and order APIs were never called.

Stage 3A **does not authorize** live HTTP downloads, live MT5 initialization, real symbol/quote/margin reads, source-derived strategy signals, new paper records in the workstation journal, production deployments or scheduler activation.

### Stage 3B — separately accepted read-only connectivity/readiness

Only after Stage-3A code review, focused/native regression and a separate explicit go-ahead may the agent perform a bounded, manual, **read-only** smoke test against the *isolated* M029 runtime.

- Confirm actual Wine binary/path/prefix identity, terminal start/stop and MetaTrader5 Python import/API compatibility. Do not copy credentials or use a personal/live broker account as a shortcut.
- If a broker connection requires authentication or a demo account, stop and request an explicit suitable connection setup; do not retrieve, print, infer, or reuse user secrets.
- Permit broker `initialize` / `shutdown` only after approval; for a connected, non-live-risk demo session, permit read-only `symbol_info`, `symbol_info_tick` and `order_calc_margin` for **only the eight frozen symbols**. Use `terminal_info` if necessary without publishing account or machine identifiers. Do not modify Market Watch symbols as a hidden side effect.
- Explicitly forbid `order_send`, `order_check`, `positions_get`, `orders_get`, `history_*`, `account_info`, trade/account balances, real orders, and account metadata in logs or published control results.
- A separate allowlisted metadata-only BIS/OECD readiness check may verify the fixed publication URLs, raw SHA-256, normalized panel SHA-256, last available source date/month and publisher timestamps. It must not compute formation signs, volatility/targets, strategy returns, paper fills or P/L.
- Probe responses exposed through GitHub local control may contain only nonsecret readiness codes, counts, source dates/hashes, runtime versions and safe error classes. Never upload broker login, broker account identifiers, credentials or access tokens.
- Any Wine/terminal crash, unexpected debugger warning, stale tick, missing margin, incompatible API, untrusted timestamp or read-only policy violation => classify `BROKER_NOT_READY` or `ENVIRONMENT_NOT_READY` and stop; no source-derived signal.

No Stage-3B readiness pass by itself authorizes a paper decision.

### Stage 3C — future time-limited paper decision (not yet authorized)

A **separate explicit acceptance and authorization** of Stage 3C, plus verified source/broker readiness and a scheduler dry run, are required before one prospective decision can run. The first potentially eligible window remains:

- Month `2026-12`
- Scheduled: **2026-12-07T12:00:00Z** (15:00 East Africa Time)
- Open only in **[2026-12-07T12:00:00Z, 2026-12-07T12:10:00Z)**.
- Window must be checked before network/broker access, after each potentially blocking operation, and at the final exclusive journal write. The trusted UTC clock is read inside the workstation action, not accepted from a remote caller.
- Do not backdate observations, force a clock value or run a missed decision after the window.

No automatic recurring task has been created under this document. A tested scheduler and explicit enablement are separate steps.

## 4. Prospectively frozen source and quote evidence

Before any source-derived signal or target construction, a Stage-3C action must establish:

1. **Real-time fetch provenance:** BIS XRU and OECD IR3TIB are fetched from the exact M027 URLs by the approved read-only downloader. Record request start, response completion, source identifier, last publication/observation date or month, raw SHA-256 and normalized SHA-256. Both fetches must start and end inside the active decision window. Do not label local cache files or later source revisions as on-time downloads.
2. **Source completeness:** for December 2026, BIS spot must cover **2026-11-30** and OECD rates through **2026-10**. This is a mechanical last-available-date/month gate, not a claim that future publication is guaranteed. Reject changed source identifiers, malformed content, missing rates, interpolations and unsupported source substitutions.
3. **No look-ahead:** compute formation using only the 12 completed calendar months through the preceding month under the frozen M027 rules, and lagged volatility using only information observable by the decision. Prove with synthetic future-mutation tests that observations later than the decision cutoff cannot affect earlier signals.
4. **Broker snapshot:** obtain only the fixed eight symbol metadata, Bid/Ask tick and BUY/SELL projected margin through approved read-only API calls. Record actual query start/end, the exchange/broker tick's UTC timestamp, contract/volume rules, and quote viability. Reject missing/ambiguous symbol, future tick, pre-window tick, nonpositive/inverted quote, unsupported contract data and margin errors. The tick must be **inside the open decision window**, not more than **300 seconds old** at use time, and no later than the trusted decision timestamp.
5. **No misleading timestamps:** Stage-2 `m029_assembly.py` currently stamps `source.observed_at_utc` and `broker.observed_at_utc` with supplied `now`. That synthetic shortcut is **not accepted** as real provenance. Before real activation, replace/extend the live adapter and record validator to validate actual acquisition timestamps rather than relabeling a delayed fetch as contemporaneous. Do not alter the frozen signal/sizing economics to solve this.
6. **Cross-gating:** if inputs are well-formed but source completeness fails or fewer than four symbols are read-only viable, permit only an **on-time, immutable flat/not-ready record** with truthful hashes/timestamps, no signal, no target lots and unknown costs still null. If transport/bridge cannot produce trustworthy evidence, fail without manufacturing an on-time record; after the close mark the month missed.
7. **Serialization and integrity:** use canonical record hashing, one file per month at `~/.local/share/mamba2-forward-paper/YYYY-MM-decision.json`, exclusive creation and durable flush. Validate existing record's month/timestamps/hash and return it unchanged on retry. Reject corrupt/symlink/partial records; no overwrite, repair, force retry or alternative record naming. Verify source and broker observation timestamps fall in the decision window and no later than creation.
8. **Safety and privacy:** do not record terminal credentials, account IDs, account balances, live positions, or personal profile information; no broker order endpoint call. The paper decision is a shadow ledger only. The 12 *completed* forward-paper holding-period minimum remains in force before any strategy-support conclusion.

## 5. Acceptance tests and stop conditions

Stage-3A acceptance must demonstrate, on the exact feature SHA:

- Synthetic-only focused and full native regression; no change to M027/M028 semantics.
- Fail-closed before open, at exact close, after close, on wrong timezone, missing source, unknown publish date, source hash mismatch, stale/future/pre-window quote, altered symbol, invalid volume/margin, symlink/corrupt/colliding journal and crash/retry cases.
- A repeatable isolated Python/MT5 bridge **mock** test; an actual read-only bridge smoke test belongs to Stage 3B and cannot be declared passed based on the GUI launch.
- Evidence that no real MT5 account connection, market quote, broker order, live/source-derived signal, paper decision or performance claim occurred during Stage-3A.
- A manual scheduler dry run must simulate early/on-time/missed UTC windows without activating production or reading real data.

If an operational gate fails, STOP. Never loosen data requirements, retrospective timing or strategy constraints to obtain a result. Every change to these frozen rules requires a new named protocol amendment **before** new forward outcomes are observed.

## 6. Immediate next task

Implement Stage 3A only, starting with the timestamp provenance defect and fail-closed time gate. Do not initiate Stage 3B or Stage 3C as a consequence of this freeze.