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


## M025 independent public-benchmark research

M025 is **OPEN — PROTOCOL FROZEN; STAGE 1 IMPLEMENTATION ONLY** on
`public-strategy-benchmarks`, based from the closed M022 docs SHA
`7047d5ff3fd4c74163b62f2142742a124462bb7d`.

It is intentionally isolated from M023. M023 results may not be used to choose,
replace, or tune M025 benchmark definitions.

Frozen benchmark families are:

- MOP TSMOM 12/1;
- currency momentum MOM(1,1), MOM(6,1), MOM(12,1);
- HML-FX carry;
- M020-D as the frozen internal Mamba comparator.

Stage 1 authorizes signal/portfolio machinery, data sufficiency gates, and
synthetic tests only. No M025 historical economics are authorized yet.


## M025 fidelity review checkpoint

Branch:

`public-strategy-benchmarks`

M025 remains independent of M024/M023 outcome selection. No M025 historical
economics have been run.

Primary-source review found:

- MOP centered EWMA variance semantics are correct in principle and should be
  preserved;
- Menkhoff formation returns require additive aggregation of monthly **log
  currency excess returns**;
- HML-FX attribution is Lustig, Roussanov, and Verdelhan (2011);
- the five-year-plus-warmup sufficiency gate must be consecutive, not a count
  of scattered eligible months.

Stage 1 remains code/tests/data-gate only.


## M025 Stage-1 fidelity implementation checkpoint

Feature repair:

`35775c872ef83fa161732f7975ef3c0513e1b847`

Fixed local-control support:

`6c5342e804c24f9a4ca8ee2b46f7991192713839`

No M025 economics have run. The next gate is exact Dell branch switch, focused
public-benchmark tests, then full native regression.


## M025 Stage 1 accepted

Accepted feature SHA:

`d2a6b1b1c2e4e6894e4564c615475ee4df571d55`

Focused acceptance:

`a9d4ce84b5cc35e911407082c056c24668b79401`
— **23 passed**.

Full native acceptance:

`28a5c79dd49e10f1255a97bc24a05b0df721bb1b`
— **260 passed, 2 skipped**.

No M025 economics have run.

The Stage-2 data-source inventory protocol is frozen. The next work is public
source metadata/schema inventory only, with no benchmark P/L.


## M025 Stage 2 source inventory accepted

Inventory artifact:

`docs/research/m025-public-source-inventory.md`

Result:

- no public/free raw-eligible source established for publication-faithful B1,
  B2, or B3;
- AQR TSMOM and CurrencyPortfolios are retained as derived external references;
- H.10/Dukascopy spot are retained only as possible TSMOM spot-proxy sources.

No M025 economics have run. Raw publication-faithful reconstruction stops here
under the current free-data boundary.


## M025 Stage-3 reference/proxy protocol frozen

Stage-2 inventory acceptance:

`efbf59094ff226542201a32963a5e75a1fccd416`

Stage 3 prospectively selects:

- **Federal Reserve H.10** for the explicit
  `TSMOM SPOT PROXY — FED H.10` path;
- AQR monthly TSMOM as a derived reference, currency factor only if schema
  proves it exists;
- LRV `CurrencyPortfolios.xls` as a derived HML-FX reference;
- accepted M020-D artifacts as the internal reference.

The H.10 source universe is frozen at all 23 daily currency-rate series, with
USD-per-foreign normalization and no fill/interpolation.

Economic metrics and cross-series comparison formulas are frozen before any
Stage-3 economic download/calculation.

Next gate: deterministic schema/ingestion only.


## M025 Stage-3 ingestion implementation checkpoint

Protocol:

`6b6592237fe4f9e087745c914e916bda6521012d`

Snapshot-range addendum:

`a7fa66244e57c9f0e214526ab8dee9b96537f87c`

Ingestion implementation:

`184f0fbd0e58e0d451120232a2cb9295c729f7f2`

Fixed controls:

`cd985e2f29d6814b1aec54ffff1b57b2c9a1ab6a`

Runtime probe:

`315a03a0ba1967d30a884b0fc0d33c39543f6e70`

No Stage-3 source has been economically evaluated. Next: focused ingestion
tests, then the immutable non-economic source snapshot.


## M025 Stage-3 H.10 VES/VEB metadata repair

Non-economic ingestion v4 stopped before publication because the exact frozen
Fed series `RXI_N.B.VES` carries legacy SDMX metadata
`CURRENCY="VEB"`.

The parser now accepts only `VES`/legacy `VEB` for that exact series and
still rejects all other currency-code drift.

Repair:

`82c9665f9dd29f7985b71dd2fa0e70422efba9fc`

No Stage-3 economics have run.


## M025 Stage-3 LRV transport repair

Non-economic ingestion v5 reached the LRV workbook step but the prior
Wharton-hosted URL did not produce a loadable XLS.

The same frozen `CurrencyPortfolios.xls` reference will use the historical
MIT mirror:

`https://web.mit.edu/adrienv/www/CurrencyPortfolios.xls`

and must pass an OLE-XLS magic-byte check before conversion.

No Stage-3 economics have run.


## M025 Stage-3 LRV conversion-path repair

Ingestion v6 proved the MIT payload is a real OLE XLS but LibreOffice failed on
relative temp paths.

Repair:

`26de5ae69742a7913ab56e0f5f73af2084e2c511`

Conversion now uses verified absolute paths. No economics have run.


## M025 Stage-3 LRV conversion-free schema repair

The validated MIT LRV workbook is a genuine OLE Excel file but LibreOffice
cannot convert it. Stage-3 now validates its schema directly from deterministic
OLE binary strings, requiring P1-P6 and HML labels while explicitly avoiding
numeric-cell parsing.

Feature repairs:

- `3302ab0fdaa698811ef549888bba5fbe1b541be6`
- `a267f626ad13281a0976e78c6f50fa3773efb042`

Control repair:

`2ab3bceb0f1506002490f6f2a18863e872045e1a`

No Stage-3 economics have run.


## M025 Stage 3 ingestion accepted

Accepted feature:

`554ab3a827163732f4dec335c716fec2f386bfe8`

Focused tests:

`2d3e36ca14c4a277666a74d4f300a982a19d88be` — **33 passed**.

Immutable ingestion:

`61bb9c5d591e8519f5bebc024d670204d9a71eab`

Report SHA:

`d5f05a7aed82d1cac275bcb222913ec61a38f00b2df74b3727e479d7a4324505`

H.10 raw SHA:

`38b941973dd7e6570e590291a34ebd27873ef98c7d09fcb0e3097ee76e793046`

H.10 normalized panel SHA:

`015e61cffd504f61853167bfab1511ecd92c51e87abd21c935ee70b064f43419`

All 23 frozen H.10 currencies pass the 72-month gate.

AQR exposes dedicated currency factor `TSMOM^FX`.

LRV exposes P1-P6 and HML schema.

No Stage-3 economics have run.

Next gate: freeze Stage-4 economic execution protocol.


## M025 Stage-4 implementation checkpoint

Protocol: `6511131792e32e74b6c98ce9de1d11dded5522b7`

Locked `xlrd==2.0.2` dependency:
`07facca9a04cc5f8154b7c648208f186326c0f2e`

Implementation:
`f74bd6606b91f38a4255d38af6d4770500004ec5`

Focused-test control:
`7ab842c005e45d07c6790ba037a0bd9c1ce86599`

No Stage-4 economics have run. Economic execution remains disabled pending
focused tests and full native regression.


## M025 Stage-4 validated; blocked on LRV unit metadata probe

Accepted focused Stage-4 tests:

`d95bf9911368d11c79e0e247247bc991c49a06dd`
— **42 passed**.

Accepted full native regression:

`f77ba7f1e424058a52d3c6f139b86347b1714852`
— **279 passed, 2 skipped**.

Stage-4 economics attempt `d1703515...` stopped at the frozen LRV unit gate
before a successful report; no unit was inferred from return magnitude.

Corrected metadata-only probe command
`mamba2-m025-stage4-lrv-unit-probe-v2` is queued on `local-control` at
`b61a2b6caeac49dd200d067678a28a2ec718ca72`, but the Dell local-agent has not
consumed it. Latest result remains the v1 environment failure.

No Stage-4 terminal economic result is accepted yet.

## M025 closed — Stage-4 terminal economics accepted

M025 is **CLOSED**.

Final repaired economic feature SHA:

`2aed0444c8f0e214d14f9dc90d4c2813388555db`

Post-repair validation:

- focused Stage-4: **43 passed / 0 failed**
  (`894ce65d5a1a83910fcacc3d3dfd5ccf551c1a8d`);
- full native: **280 passed / 2 skipped**
  (`d5f85857a3f4014f44b3f5970f16bca2090c87ca`).

Sole accepted Stage-4 economic execution:

`mamba2-m025-stage4-economics-after-unit-evidence-v1`

Result branch commit:

`c01ab5df81bdf31b3279b2c0d7e99843c7437ef7`

Deterministic A/B report SHA-256:

`633962e5896ac7e8edfe21626beaa09661b01afb286089c00e4c1349caf95ce9`

A/B byte identity: **PASS**.

Accepted headline references:

- H.10 TSMOM spot proxy annualized mean: **-1.6058975079063509**
- AQR TSMOM^FX annualized mean: **0.10093357261356833**
- LRV HML-FX annualized mean: **0.0003586837489041334**
- H.10 vs AQR zero-lag correlation: **-0.07400075645466087**

The LRV scale `0.01` was established through the prospectively frozen
Stage-4.1 evidence rule, not by return-magnitude inference.

Stop rule is active: no retuning, rescaling, lag/sign search, source
replacement, universe pruning, or production/live promotion is authorized
inside M025. Any further benchmark work requires a new prospectively frozen
milestone.

