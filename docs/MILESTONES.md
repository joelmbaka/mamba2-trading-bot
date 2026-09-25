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
| 015 | Repository operations foundation | `32da1d846960cbc2b196da1c2f8c8a8561a5c322` | Durable docs/local-control + dead/generated repository cleanup |
| 016 | First real five-symbol baseline | `4d8a15937f461c0e39d434be6639bfde83698d7f` | Deterministic Sep 1–24 baseline; real-data replay blockers corrected |
| 017 | Baseline diagnosis | `e653ba87df2ff1e8afbad5704f9a8d81428d7b27` | Deterministic trade evidence; M016 report preserved byte-for-byte |

## Current acceptance evidence

Milestone 017 closed with:

- implementation SHA: `e653ba87df2ff1e8afbad5704f9a8d81428d7b27`;
- full native: **173 passed, 2 skipped**;
- full Wine: **173 passed, 2 skipped**;
- Wine Python 3.10.11 AMD64;
- Wine NumPy 2.2.1;
- Wine MetaTrader5 5.0.6180;
- Wine pytest 9.1.1;
- diagnostic pair byte-identical;
- diagnostic SHA-256:
  `edf01f4a1f936d386e618faa65fb9a7afb65fff6ae7ae9b4373c35692ced987a`;
- ordinary baseline report preserved byte-for-byte at accepted M016 SHA-256:
  `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`;
- 1,393 accepted orders / 1,393 closed trades / 1,393 diagnostic rows;
- 0 remaining positions;
- ending realized balance/equity USD 9,731.45700985454;
- net realized P/L USD -268.54299014546086;
- no new strategy-reporting artifacts.

Key descriptive evidence:

- BUY: USD -330.9923055212326; SELL: USD +62.44931537578547,
  despite almost identical non-flat win rates;
- 1,339 stop-loss exits, including 528 profitable stop exits after protection
  movement;
- 54 take-profit exits, including 3 negative-P/L exits requiring M018 review;
- losing trades had mean entry spread 7.174661746617466 points versus
  3.538860103626943 points for winners, with equal median 2-point spread;
- all 1,393 trades received initial ATR protection;
- 619 trades had successful trailing modifications;
- realized JPY exits used direct same-boundary USDJPY conversion, not the
  sparse two-leg fallback;
- maximum consecutive losses: 17;
- deepest drawdown: USD 400.156643608565 / 3.9953123082355586%, recovered;
- later USD 312.44186473816626 / 3.112078553673229% drawdown remained
  unrecovered at end of data.

See `docs/milestones/017-baseline-diagnosis.md` for the complete record.

## Closeout format for future milestones

Record:

- purpose;
- implementation SHA;
- changed paths;
- exact validation totals;
- semantic contract established;
- limitations intentionally left unresolved;
- next authorized milestone.
