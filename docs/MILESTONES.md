# Milestone Ledger

Each accepted milestone records the exact implementation SHA. Future milestones should append a dated record here or add a dedicated file under `docs/milestones/`.

| # | Milestone | Accepted implementation SHA | Core result |
|---|---|---|---|
| 001 | Deterministic OHLC replay | `f0fb7fb5a76bffe8212978e58e28f42d8c7b3e1b` | Deterministic historical replay foundation |
| 002 | Runner + strategy adapter | `25062790b06c9cd6ebf735f878cd30664ee29321` | Production strategy driven by replay |
| 003 | Execution lifecycle | `d0772fe3b51ce05c14cfa8b6372a683412797bda` | Orders, positions, ledger |
| 004 | MT5 bar-open semantics | `75bdde55f94234890b171dcd063314622d84927a` | No future candle leakage |
| 005 | Native runtime/history exporter | `f744fcece1045201a6e0c60065563f588d985873` | Read-only MT5 datasets; pinned Wine runtime |
| 006 | Production lifecycle replay | `ddfb639fd3036b08a69814c690791c5ec5929bd6` | ATR/PositionManager + duplicate-order guard |
| 007 | Spread-aware execution | `fb500cde9dcde5544e84200c60c9cfa1a7c3d551` | Bid/Ask + tick-derived Ask |
| 008 | Account-currency P/L | `fee486156fdbacbcc5459f34c058a7574b06753a` | Historical conversion routes |
| 009 | Execution costs | `8e05c13c0d08d87dbb4710b484c70bfe80dff03c` | Explicit commission/slippage model |
| 010 | Strategy-condition semantics | `52718e03bdf70cf986af93963bf5e16bdbb97332` | Trend/RSI/higher-TF flags honored |
| 011 | Portfolio replay | `e1fbf895d9d1eeeb04ebca0f6aa043de2406a578` | Shared five-symbol account |
| 012 | Baseline reporting | `f903e34aff17a8efe974482750aa9134c8f67af3` | Deterministic report + explicit stochastic 21/7/7 |
| 013 | Trailing semantics | `4cd40f4af9d2f4e6a6e7d1fc570171bf8a493e32` | Monotonic existing stops |
| 014 | Runtime cache sanitization | `40536d96c6ac2119fca3c2cfec92dad889e7c878` | Stale account metadata removed safely |
| 015 | First real five-symbol baseline | **PENDING** | Sep 1–24, 2026, current strategy unchanged |

## Current acceptance evidence

Milestone 014 closed with:

- native: 165 passed, 2 skipped;
- Wine: 165 passed, 2 skipped;
- Wine Python 3.10.11 x64;
- NumPy 2.2.1;
- MetaTrader5 5.0.6180;
- clean worktree;
- `bot_cache.json` untracked;
- `icon.png` unchanged.

## Closeout format for future milestones

Record:

- purpose;
- implementation SHA;
- changed paths;
- exact validation totals;
- semantic contract established;
- limitations intentionally left unresolved;
- next authorized milestone.
