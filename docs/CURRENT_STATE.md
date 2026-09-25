# Current State

Last updated: 2026-09-25

## Latest accepted implementation milestone

**016 — First real five-symbol baseline**

Accepted implementation SHA:

`4d8a15937f461c0e39d434be6639bfde83698d7f`

Validation:

- full native suite: **169 passed, 2 skipped**
- full Wine suite: **169 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- repository checks: PASS
- worktree: clean
- divergence: 0/0
- `bot_cache.json`: untracked
- `icon.png`: tracked and unchanged

Determinism gate:

- report A and report B: byte-for-byte identical
- SHA-256: `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`
- no new strategy-reporting artifacts

## Accepted first real baseline

Historical window:

`2026-09-01T00:00:00Z` through `2026-09-25T00:00:00Z`

Dataset:

- account currency: USD
- EURUSD M1/Ask rows: 25,916 / 25,916
- EURJPY M1/Ask rows: 25,916 / 25,916
- GBPUSD M1/Ask rows: 25,915 / 25,915
- GBPJPY M1/Ask rows: 25,914 / 25,914
- USDJPY M1/Ask rows: 25,913 / 25,913
- native M5 rows: 5,184 per symbol
- native M15 rows: 1,728 per symbol
- tick-derived Ask required and verified
- manifest/integrity load: PASS

Aggregate result:

- replay boundaries: 25,916
- accepted orders: 1,393
- closed trades: 1,393
- remaining positions: 0
- starting balance: USD 10,000.00
- ending realized balance: USD 9,731.45700985454
- ending unrealized P/L: USD 0.00
- ending equity: USD 9,731.45700985454
- gross realized P/L: USD -268.54299014544677
- commission: USD 0.00
- net realized P/L: USD -268.54299014546086
- wins / losses / flats: 579 / 813 / 1
- non-flat win rate: 41.5948275862069%
- largest closed gain: USD 35.041524659453856
- largest closed loss: USD -26.566478053355354
- maximum shared-account equity drawdown: USD 400.156643608565
- maximum shared-account equity drawdown: 3.9953123082355586%

Cost label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

These results are not described as fully net of actual broker costs because actual commission, slippage, and swap are not proven.

## M016 defects proven and corrected

The first real run exposed two replay defects that prevented the authorized baseline from completing.

### Replay scalability

Repeated full-history stochastic and ATR calculations made the real 24-day portfolio replay impractically slow.

The accepted correction:

- keeps production indicator arithmetic unchanged;
- activates causal full-history caching only through a ReplayFeed-specific static-history hook;
- slices cached values back to the currently visible causal prefix;
- uses prefix-efficient ReplayFeed history slicing;
- leaves production rate fetchers on the existing calculation path.

Exact parity tests prove cached replay outputs equal the legacy visible-only path.

### Sparse same-boundary FX conversion

The verified MT5 export has three EURJPY M1 timestamps on 2026-09-14 for which USDJPY has no same-minute M1 bar; GBPJPY overlaps one of those gaps.

The accepted correction does **not** carry forward an older quote or use a future/current/web rate. Direct same-boundary conversion remains preferred. When that direct conversion pair has no bar on the required replay phase, the broker may use a deterministic two-leg route made entirely from available same-boundary historical Bid/Ask prices, for example JPY→EUR→USD.

Tests cover execution-time fallback, completed-bar fallback, direct-route preference, and the existing no-future-price rule.

## Durable handoff

A fresh ChatGPT or Codex session must start with:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`
6. `docs/MILESTONES.md`

## Local control

Permanent branches:

- `local-control`
- `local-control-results`

Installed workstation service:

`chatgpt-mamba2-local-agent.service`

Validated capabilities include repository checks, runtime discovery, native/Wine tests, read-only baseline export, baseline cleanup, and paired deterministic baseline execution.

No arbitrary shell action is exposed.

## Current production/backtest settings

- Symbols: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY
- Position size: 0.1
- Stochastic: 21 / 7 / 7
- Trend filter: off
- RSI filter: off
- Higher-TF filter: off
- EMA: 7
- ATR: period 14, M5
- ATR SL multiplier: 1.0
- ATR TP multiplier: 2.0
- Existing BUY stops only move upward.
- Existing SELL stops only move downward.
- End-of-data does not force-liquidate.
- Historical spread uses tick-derived Ask where available.
- Unknown real commission/slippage must not be invented.

## Next milestone

**017 — Baseline diagnosis**

Branch:

`backtest-baseline-diagnosis`

Use the accepted M016 dataset and strategy unchanged. Build deterministic trade-level evidence and diagnose the result before any optimization.
