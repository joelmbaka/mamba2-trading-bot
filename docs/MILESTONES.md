# Milestone Ledger

Each accepted milestone records the exact implementation SHA. Future milestones
should append a dated record here or add a dedicated file under
`docs/milestones/`.

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
| 018 | Proven-defect review and correction | `fb03bc197d60d5d7b5b218a86288811f72ec4f60` | Wrong-side initial ATR TP defect proven and narrowly corrected |
| 019 | Broader-history validation | `94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb` | Jun 23–Sep 24 deterministic broader replay; M018 and whole-window semantic parity preserved |

## Current acceptance evidence

Milestone 019 closed with:

- implementation SHA:
  `94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`;
- full native: **179 passed, 2 skipped**;
- full Wine: **179 passed, 2 skipped**;
- accepted M018 baseline preserved exactly:
  `e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`;
- accepted M018 diagnostic preserved exactly:
  `1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`;
- final broader baseline pair byte-identical:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- final broader diagnostic pair byte-identical:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- final optimized broader hashes equal the earlier pre-optimization broader
  hashes;
- wrong-side initial TP violations: **0**;
- negative-P/L take-profit exits: **0**;
- no new strategy-reporting artifacts;
- accepted orders / closed trades: **4,922 / 4,922**;
- net realized P/L: **USD -1,716.607632002333**;
- ending realized balance/equity: **USD 8,283.392367997667**;
- maximum equity drawdown:
  **USD 1,929.6969567926317 / 19.214803229083717%**.

The broader evidence does not support carrying the Sep-only profitable-SELL
observation into M020 as a side filter. Both BUY and SELL are negative over the
broader interval.

The strongest persistent descriptive candidate is the 00:00–03:59 UTC entry
bucket, which is negative in both the short accepted window and the broader
sample and has unusually wide spread exposure. M020 may test that as one
controlled entry filter, but must not treat the M019 observation itself as
causal proof.

See `docs/milestones/019-broader-history-validation.md` for the complete
record.

## Closeout format for future milestones

Record:

- purpose;
- implementation SHA;
- changed paths;
- exact validation totals;
- semantic contract established;
- limitations intentionally left unresolved;
- next authorized milestone.
