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
