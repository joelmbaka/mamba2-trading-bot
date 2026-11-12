# Next Authorized Task

## M029 Stage 3A — implement the frozen operational safety boundary

Branch: `prospective-paper-recovery`. Do not touch `main`.

**Operational protocol frozen before implementation/real-data access:**
`c74ca08fe32bf9ac9954cee5b033f808f3932ddd`
(`docs/milestones/029-stage3-operational-protocol.md`).

Accepted Stage-1 / Stage-2 engine remains:
- Final pre-Stage-3 code/handoff HEAD: `917be98f784fe0842521b76a76ebf41a5654786c`.
- Local-agent final full native regression: **356 passed, 2 skipped,
  13 existing warnings**; result commit
  `bcb873c4d1b812b290e1066fde12e943a7912e49`.

### Operator-reported isolated MT5 compatibility evidence (2026-11-12)

- Wine **11.21 Staging**, Windows 11 compatibility, isolated copied
  MetaTrader 5 terminal showed `MetaTrader 5 - Netting`.
- No debugger warning appeared; no credentials, broker data, orders or
  existing MT5 installation files were used/changed.
- System Wine still **9.0**. Repository was clean at `917be98`.
- **Python/MetaTrader5 bridge unvalidated**. Do not equate GUI launch with
  broker API readiness.

### Authorized immediate work: code and synthetic tests ONLY

1. Implement trusted UTC-time window checks that run before source access,
   after blocking calls, and at the exact immutable journal write boundary.
2. Define real source acquisition metadata schema: actual UTC request/response
   timestamps, exact BIS/OECD publisher URLs/identities, source coverage
   date/month, raw/normalized hashes. Do not invent timestamps from a
   synthetic `now` argument when designing the live adapter.
3. Define a read-only broker transport interface with strict whitelist and
   separate isolated Wine 11.21/Windows 11 runtime discovery; do not connect
   to a broker yet, change Wine system defaults, copy credentials or mutate
   existing `~/.mt5` / `.venv-wine`.
4. Validate eight fixed symbol identities, quote timestamps inside the actual
   decision window and <=300 seconds old, Bid/Ask, lot rules, BUY/SELL margin;
   only metadata checks may occur before a decision.
5. Use synthetic/mock fixtures only to prove fail-closed no-backfill, crash
   handling, filesystem integrity, missing source/quote/margin, wrong symbols
   and UTC boundary/refusal semantics. Preserve M027/M028 strategy logic.
6. Run focused and full native regression, inspect exact feature SHA, and
   document Stage-3A acceptance evidence before approving any real-data test.

### STOP before Stage 3B real connectivity

Stage 3B (bounded read-only bridge/source readiness) requires a separate
explicit authorization **after** synthetic Stage-3A acceptance. No live HTTP
source downloads, real broker quote/margin calls, credentials, MT5
initialization or source-derived strategy signal are authorized by this
handoff.

Stage 3C (actual monthly on-time paper decision and optional scheduling)
requires its **own explicit acceptance/authorization** after Stage 3B.
Do not schedule it by default. No real MT5 order/position changes are permitted.

### Immutable prospective calendar

First possible month: `2026-12`; decision window is
**2026-12-07T12:00:00Z** through *strictly before*
**2026-12-07T12:10:00Z** (15:00–15:10 EAT).
October and November are irrecoverably missed. Never backfill. A missed
December window is also terminal.

Preserve source identities, eight-currency signal and sizing, unknown cost
fields, and minimum 12 completed prospective paper holding periods before
any strategy support analysis. See the frozen Stage-3 protocol for full rules.
