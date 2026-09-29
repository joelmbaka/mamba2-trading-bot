# Current State

Last updated: 2026-09-26

## Latest accepted implementation milestone

**020 — Controlled experiments**

Accepted implementation SHA:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

Accepted prior milestone:

**019 — Broader-history validation**

Milestone 020 changed experiment/backtest infrastructure only. It did not
promote experimental behavior into the production/live strategy.

## M019 final validation

Current optimized implementation:

- full native suite: **179 passed, 2 skipped**
- full Wine suite: **179 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**

M018 byte-preservation gate:

- command: `mamba2-m019-m018-regression-current-head-20260925-2016`
- baseline A/B byte-identical: **PASS**
- baseline SHA-256:
  `e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`
- diagnostic A/B byte-identical: **PASS**
- diagnostic SHA-256:
  `1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`

The optimized replay therefore reproduces the accepted Sep 1–24 M018 artifacts
exactly.

Final broader pair:

- command: `mamba2-m019-final-broader-pair-20260925-2022`
- baseline A/B byte-identical: **PASS**
- baseline SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`
- diagnostic A/B byte-identical: **PASS**
- diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`
- wrong-side initial TP violations: **0**
- negative-P/L take-profit exits: **0**
- new strategy-reporting artifacts: **0**
- remaining open positions: **0**

The final optimized broader hashes also equal the earlier pre-optimization
broader pair hashes, providing whole-window evidence that the replay performance
work preserved results.

## Accepted broader dataset

Window:

`2026-06-23T00:00:00Z` through `2026-09-25T00:00:00Z`

Dataset:

`backtest_data/broader-history-20260623-20260925/manifest.json`

Account currency: **USD**

Rows:

| Symbol | M1 | Ask M1 | M5 | M15 |
|---|---:|---:|---:|---:|
| EURUSD | 97,914 | 97,914 | 19,584 | 6,528 |
| EURJPY | 97,914 | 97,914 | 19,584 | 6,528 |
| GBPUSD | 97,911 | 97,911 | 19,584 | 6,528 |
| GBPJPY | 97,911 | 97,911 | 19,584 | 6,528 |
| USDJPY | 97,910 | 97,910 | 19,584 | 6,528 |

The Sep 1–24 overlap is identical to the accepted M016/M018 market data for M1,
native M5, native M15, and tick-derived Ask M1.

## Accepted broader result

Cost label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

Actual commission, slippage, and swap remain unproven/unmodeled and must not be
invented.

Aggregate:

- accepted orders / closed trades: **4,922 / 4,922**
- wins / losses / flats: **1,899 / 3,020 / 3**
- non-flat win rate: **38.60540760317138%**
- net realized P/L: **USD -1,716.607632002333**
- ending realized balance/equity: **USD 8,283.392367997667**
- maximum equity drawdown:
  **USD 1,929.6969567926317 / 19.214803229083717%**

Per-symbol net P/L:

- EURJPY: **USD +113.69332714418455**
- EURUSD: **USD -301.59285714284704**
- GBPJPY: **USD -930.0206586449655**
- GBPUSD: **USD -423.3857142857603**
- USDJPY: **USD -175.301729072955**

All four calendar entry subperiods were negative:

- Jun 23–30: **USD -170.12248532167797**
- July: **USD -637.4843772180006**
- August: **USD -674.9506208103498**
- Sep 1–24: **USD -234.0501486523148**

## Stable and unstable descriptive observations

The Sep-only M018 side asymmetry did not persist. On the broader replay:

- BUY: 2,213 trades, **USD -762.8500941221877**
- SELL: 2,709 trades, **USD -953.7575378801578**

Therefore the earlier observation that SELL was profitable is not stable enough
to justify a side filter.

The strongest persistent time-bucket observation is 00:00–03:59 UTC:

- 842 trades
- **USD -839.9216322911675**
- mean entry spread: **19.899049881235154 points**
- median: **4 points**
- maximum: **300 points**

Other UTC buckets had much smaller mean spreads, roughly 2.58–3.62 points.
Losses overall entered at a wider mean spread than wins:

- losses: mean **7.070529801324503**, median **2**, max **300**
- wins: mean **3.843601895734597**, median **2**, max **211**

This is descriptive association, not proof that spread or session timing causes
the loss.

Protection/exit evidence:

- all **4,922** trades received initial protection
- **2,090** trades had trailing activity
- **3,531** total trailing modifications
- stop-loss exits: **4,715**, net **USD -3,530.797379799249**
- take-profit exits: **207**, all 207 winners, net **USD +1,814.1897477968992**

Conversion routes remained explicit:

- JPY->USD through direct USDJPY: **2,980 trades**
- USD->USD no conversion: **1,941 trades**
- one flat JPY trade had no conversion route and zero P/L

Maximum consecutive losses: **22**, from
`2026-08-11T00:01:00Z` through `2026-08-11T05:01:00Z`.

The deepest drawdown episode peaked at **USD 10,042.761998581507** on
2026-06-23 16:49 UTC, reached **USD 8,113.0650417888755** on
2026-09-04 16:43 UTC, and was not recovered by the dataset end.

See `docs/milestones/019-broader-history-validation.md` for the complete
acceptance record.

## M020 closeout — controlled experiments

Milestone 020 is **CLOSED**.

Accepted implementation SHA:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

M020-A:

**PROMISING, NOT PROMOTED**

M020-B:

**COMPLETE — fill-spread confound diagnosis**

M020-C:

**COMPLETE — decision-time spread observability**

M020-D:

**PROMISING**

The final accepted M020-D treatment rejects only a new order whose observable
decision-time spread is **>10 points**. It does not stack the M020-A session
filter and does not change production/live strategy behavior.

Final validation after correcting rejected-order reporting:

- native: **195 passed, 2 skipped**;
- Wine: **195 passed, 2 skipped**;
- immutable control command:
  `mamba2-m020d-reporting-fix-control-20260926-0843`;
- accepted M019 baseline preserved:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- accepted M019 diagnostic preserved:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- authoritative treatment command:
  `mamba2-m020d-authoritative-treatment-pair-20260926-1014`;
- treatment baseline SHA-256:
  `94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`;
- treatment diagnostic SHA-256:
  `45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`;
- treatment evidence SHA-256:
  `e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`;
- result branch SHA:
  `53e79d1da25994c87330faaaf805928de08c427e`;
- rejected attempts: **976**;
- accepted spread violations: **0**;
- maximum accepted decision spread: **10 points**;
- wrong-side initial TP violations: **0**;
- negative-P/L take-profit exits: **0**;
- new strategy-reporting artifacts: **0**;
- remaining open positions: **0**.

Control -> M020-D:

- accepted/closed: **4,922/4,922 -> 4,664/4,664**;
- wins/losses/flats:
  **1,899/3,020/3 -> 1,860/2,800/4**;
- non-flat win rate:
  **38.60540760317138% -> 39.91416309012876%**;
- net realized P/L:
  **USD -1,716.607632002333 -> USD -677.647148799515**;
- ending balance/equity:
  **USD 8,283.392367997667 -> USD 9,322.352851200485**;
- maximum equity drawdown:
  **USD 1,929.6969567926317 / 19.214803229083717% ->
  USD 1,067.1062318369404 / 10.629228567139583%**.

P/L improvement:

**USD +1,038.960483202818**

All four inspected calendar periods, all five symbols, and both sides improve
relative to control. GBPJPY contributes about **56.03%** of the improvement,
but all four other symbols also improve. The treatment remains loss-making:
three of four calendar periods, four of five symbols, and both sides remain
negative.

M020-D is therefore **PROMISING**, but remains in-sample experimental evidence.
It is not promoted to live risk.

The first M020-D treatment pair also revealed a replay-reporting bug where
intentional `retcode=1` rejections were counted under `accepted_orders`.
That accounting bug was fixed and regression-tested before the authoritative
pair. Rejected orders had never reached the pending execution queue, so the
economic treatment behavior did not change.

No M020-E is authorized. Further tuning of thresholds or stacking M020-A would
reuse an already-inspected dataset and is outside the closed milestone.

## Durable handoff

A fresh ChatGPT or Codex session must start with:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`
6. `docs/MILESTONES.md`
7. the current milestone file under `docs/milestones/`

## Local control

Permanent branches:

- `local-control`
- `local-control-results`

Installed workstation service:

`chatgpt-mamba2-local-agent.service`

The control plane exposes only fixed allowlisted actions. No arbitrary shell
action is exposed, and no real MT5 order action is permitted.

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

## Active milestone — M021 prospective paper/forward validation

M021 is **OPEN — PROTOCOL AND EXECUTION MACHINERY FROZEN**.

Branch:

`prospective-forward-validation`

Protocol-freeze commit:

`471892e247942ed91c0bbd9adae46e4a990c5db6`

Accepted machinery implementation SHA:

`f53d38b93434eb52b19f0f12a441e4439822e39e`

The protocol was frozen before later outcomes were inspected.

Primary prospective source-data window:

`[2026-09-25T00:00:00Z, 2026-10-23T00:00:00Z)`

The candidate remains exactly M020-D:

- reject new order submissions only when observable decision-time spread is
  **>10 points**;
- allow **<=10 points**;
- do not stack M020-A;
- do not tune the threshold.

M021 machinery validation on 2026-09-26:

- native: **206 passed, 2 skipped**;
- Wine: **206 passed, 2 skipped**;
- historical M019 control baseline/diagnostic hashes: **exactly preserved**;
- historical M020-D baseline/diagnostic/evidence hashes:
  **exactly preserved**;
- new strategy artifacts during regression: **0**;
- readiness before primary cutoff: **false**;
- early primary export: **refused before MT5 history access**;
- early paired replay: **refused before economic computation**.

No post-cutoff P/L, drawdown, symbol, side, period, or classification result has
been inspected.

M021 remains dormant until the primary cutoff
`2026-10-23T00:00:00Z`. At that point the fixed protocol controls whether the
window is classified or extended by a predeclared seven-day increment.

Real MT5 trading remains disabled. M020-D is not promoted to production/live
behavior.

## M022 closeout and M023 research state

M022 is **CLOSED** at docs closeout HEAD:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

Its accepted validation implementation SHA remains:

`a409a5703e709feb0b45cbe870f4d8639189b6ba`

The frozen M022 validation assessment supported zero non-reference candidates, so its historical holdout was not opened.

M023 — Direction and Session Research — is now **OPEN** on:

`direction-session-research`

The current M023 gate is diagnostic only. It may read existing M022 development + validation artifacts for P2-R, P2-03, and P2-08, derive timezone-aware direction/session/day/fold attribution, and publish deterministic diagnostic evidence. It may not run a fresh filtered strategy replay or inspect the untouched historical holdout.

## M023 diagnostic gate result

M023 diagnostic-only evidence completed deterministically on `direction-session-research` using existing accepted M022 JSON artifacts only.

Diagnostic implementation SHA:

`f925ae8121fb9ce4ee04c1c980e58720c2a611f3`

Diagnostic result commit:

`30712d1c55e1204fc4d849a38bfa96318155b54b`

Deterministic artifact SHA-256:

`0b306c2341befd7110ea2a6695ecd4fc473055fb2231849b5a3741a11251d9a2`

The main finding is a strong time-of-day effect: EAT-ACTIVE 08:00–20:59 is consistently less negative than EAT-OFF-HOURS across P2-R, P2-03, and P2-08 and across all five chronological folds in mean trade P/L. The raw direction slices do not support jumping directly to SELL-only; BUY is less negative in 5 of 6 arm/partition comparisons. No filtered replay has run. Historical holdout and M021 remain untouched.

## M023 Stage-A prospective freeze

The M023 diagnostic gate is complete. The exact Stage-A causal direction protocol is now prospectively frozen before Stage-A economics. Stage A uses P2-08 on the already-seen 225-date research sample, with exactly D-R/BOTH, D-S/SELL-only, and D-B/BUY-only. The ordered 225-date list SHA-256 is `50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`. Historical holdout and M021 remain sealed/uninspected. Stage B is not authorized.


## M023 closeout — direction/session research

M023 is **CLOSED** on `direction-session-research`.

Final economic feature SHA:

`f5cd1111d4626bd96e11dc9b630cdac364059a04`

Accepted Stage-B family result:

`0c91e8fad993c9ab2f9075bf0d3b28dcda718249`

Accepted Stage-B mechanical assessment:

`42630379450fa3b20d7fd24c5bc2decf83dddf46`

The frozen assessment classified S-ACTIVE, S-MORNING, S-MIDDAY, and
S-AFTERNOON **NOT SUPPORTED**. Supported sessions: **0**. Fixed session:
**none**. Historical-holdout execution remains **unauthorized**.

S-MIDDAY was closest to break-even at **-$53.4115** total and
**-$0.05743/trade**, but failed the mandatory positive-P/L and positive-mean
requirements.

The next milestone is **M024 — Symbol Specialization Research**. Its first gate
must remain diagnostic-only on already-seen research evidence. Historical
holdout and M021 remain sealed/uninspected for this research path.


## M024 open — Symbol Specialization Research

M024 is **OPEN — DIAGNOSTIC PROTOCOL FROZEN** on
`symbol-specialization-research`, branched from final M023 closeout
`ffd33e2ae0534d572c73840cccaa98104b3ad460`.

The first gate reads only accepted M023 D-B / BUY-only all-hours evidence and
tests exactly four predeclared descriptive symbol subsets: SYM-R, SYM-UJ,
SYM-JPY, and SYM-NONJPY. No fresh symbol-filtered economic replay is authorized.

The accepted D-B full-sample USDJPY slice was +$15.0437 across 1,335 closed
trades, but two of five chronological folds were negative. It is therefore a
hypothesis generator only.

Historical holdout and M021 remain sealed. M025 public benchmark research is
independent and may not be used to tune M024.


## M024 implementation checkpoint

M024 diagnostic machinery is implemented on
`symbol-specialization-research`.

Protocol freeze:

`12c8b93af164f24a719fa6151efb54f838659619`

Analyzer implementation:

`2a605aebee379e50df7193f9562b84bbb2edb128`

Fixed local-control support:

`b0acf22ff8271a96f926dd9250b85418034053c4`

The analyzer reads only the accepted M023 Stage-A D-B deterministic summary
pair, requires source SHA-256
`7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c`,
and cannot run strategy replay.

Focused native tests and the deterministic M024 diagnostic remain the next
acceptance gates. No M024 economic replay has run and historical holdout/M021
remain untouched.


## M024 diagnostic accepted / Stage 2 frozen

M024 diagnostic acceptance is complete at feature HEAD
`f403124a31464f6b42768f6a1d985abe290cbc4c`.

Focused tests:

- result commit:
  `7bed8ad0173916f61b488c2d1ffe3742f9051446`;
- **7 passed**.

Deterministic diagnostic:

- result commit:
  `0473b8f149a15516c6d7b4e2f1b0585482be7eef`;
- artifact SHA-256:
  `108752dfdb7430efb2c3b4b971d16d6affb1c43e2aacc1bc5ef8e276db2d6410`;
- only SYM-UJ / USDJPY classified **DESCRIPTIVELY PROMISING**.

Full native regression:

- result commit:
  `1bed8eb23b6bca980d076dbf9173f6479f53239d`;
- **283 passed, 2 skipped**.

USDJPY descriptive evidence:

- 1,335 trades;
- +$15.0437376424 total;
- +$0.0112687173/trade;
- 3/5 positive folds;
- 23/46 positive-mean eligible weeks = 50.0%;
- max positive-fold contribution share = 41.05198%.

This is not yet a causal/proven edge.

M024 Stage 2 is now prospectively frozen before economics with exactly C-R
(all-five reference) and C-UJ (USDJPY strategy only, all-five market data
retained). No historical holdout execution is authorized.


## M024 Stage-2 implementation checkpoint

The frozen C-R/C-UJ causal runner is implemented.

Feature implementation:

`d0dff1fc66e6bc1b60200a4aeaa27990bd1322fc`

Invariant hardening:

`ea49b23f72b0e857538c77a6f469920248cfde6a`

Fixed local-control actions:

`0226b4e807480ed7e754c362d72e0adf05d5f25d`

Stage-2 validation/economics have not yet been accepted at this checkpoint.
Historical holdout remains sealed and no holdout action exists.


## M024 Stage 2 accepted

M024 Stage 2 is fully accepted on `symbol-specialization-research`.

Feature SHA:

`fd9c0ec689c57c572a7318ddd54fecb8dc5e8666`

Family result:

`45cc718b908a28040a1907c08c8dc7382d800883`

Mechanical assessment:

`d99ca44882f9814d42ed5b71a86fd13150d41b8f`

Final full native regression:

`2a824763aab9e8b9be7eb5626cf657b857cae945`
— **288 passed, 2 skipped**.

C-R reproduced accepted M023 D-B exactly.

C-UJ / USDJPY-only strategy:

- 1,335 closed trades;
- +$15.0437376424 net;
- +$0.0112687173/trade;
- max DD $275.4694141888 / 2.7490114456%;
- 3/5 positive folds;
- 23/46 positive-mean eligible weeks = 50.0%;
- all frozen representation/support/safety gates passed.

Mechanical classification:

**SUPPORTED FOR HOLDOUT CHECKPOINT ONLY**

Historical holdout remains sealed and unauthorized. The next task is only to
freeze and review a separate prospective holdout-checkpoint protocol.


## M024 historical holdout checkpoint protocol frozen

Stage 2 is accepted and C-UJ is fixed as the sole holdout candidate.

A separate M024 historical-holdout checkpoint protocol is now frozen before
holdout economics.

Holdout window:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

Expected common trading dates:

**57**

Candidate:

**H-UJ — USDJPY strategy only, all-five market data retained**

The next gate is metadata-only readiness. No holdout P/L, trades, drawdown,
win rate, weekly economics, or classification may be computed before readiness
passes and publishes immutable date/replay hashes.
