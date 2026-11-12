# M030 Stage 1S — final evidence matrix and native-parity pause

Date: 2026-11-12
Status: **PYTHON DETERMINISTIC SEMANTICS VALIDATED FOR TESTED SCOPE; NATIVE MT5 PARITY AND ECONOMIC PERFORMANCE UNRESOLVED**

## Read-only audit and git verification

Codex confirmed a clean synchronized `scalping-recovery` at `46c4cf1ae0b9e49889861f5e2e600a52c9bac898` with ahead/behind `0/0`. No Wine, MetaEditor, MT5, Strategy Tester, broker, historical replay, downloads, tests or local file changes.

## Stage 1S evidence matrix

| Dimension | Verified evidence | Outstanding gate |
| --- | --- | --- |
| Indicator arithmetic | `mamba2/indicators/stochastic.py:162-242` 21/7/7 with public 35-bar warmup; `moving_average.py:85-172` EMA7 first-source `ewm(adjust=False)`; `atr.py:89-142` ATR14 requiring 15 rows publicly. Stage 1Q focused tests 64 passed. | Native MT5 indicator values on independently matched source histories. |
| Production signal rules | `mamba2/strategy/triple_cross.py:69-153,213-310,343-454`; M5 K/D directional confirmation, M1 most recent ten K extremes with **no required fresh crossover**, EMA7/candle filter, initial SL=TP=0. Stage 1Q tests exercise the actual strategy and M030 observer. | No-order native decision trace for same exact bar-open timestamps and full warmup. |
| Causal Python feed | `mamba2/backtest/feed.py:148-248` reveals completed bars at bar close, `runner.py:128-150` controls event boundary sequencing. | Independent native time/source-bar validation; Python causality does not establish server clock truth. |
| Synthetic execution and event order | `mamba2/backtest/broker.py:136-145,219-367,388-503` and `mamba2/crew/position_manager.py`; Stage 1R 59 focused and 109 synthetic regression tests passed with 1 known legacy skip. `M1_CLOSE → SIGNAL → SUBMIT → FILL → SLTP_MODIFY`; prior completed-bar `EXIT` precedes next `M1_CLOSE`. | Native execution/fill/event timestamps and costs under a supported tester/broker environment. |
| Open/pending guards | `runner.py:99-121`; Stage 1R uses actual `StochasticTripleTFStrategy` with synthetic indicators and proves no duplicate submits while position or order pending. | Native account/position semantics. |
| MQL5 compilation | Earlier MetaEditor 5.0.0.6316 independently compiled the no-order decision probe and clock-bar probe. | Actual MQL5 runtime traces; compilation alone cannot establish parity. |
| Native UTC clock | `mamba2/backtest/m030_clock_discovery.py:45-49,153-231` compares independently provided raw native times and both M1/M5 OHLC with offset candidates. | No independent frozen-window native probe capture and verified server-to-UTC anchor. Existing exporter UTC interpretation is not independent proof. |
| Native M1/M5 bars | `mamba2/backtest/mt5_dataset.py:85-218` exports and hashes bar-open histories; existing September 10, 2026 canonical UTC sample and immutable source hashes retained. | Independently capture and compare the full M1/M5 window plus causal prefixes, with verified server/UTC mapping and provenance. |
| Native ticks/Ask | `mt5_dataset.py:221-280` defines tick aggregation by `time_msc` or `time`; no verified native sample tick/Ask identity. | Independent native tick sequence, Bid/Ask and bar reconstruction. |
| Tester execution | `M030_ClockBarProbe.mq5` is intentionally tester-only/no-order; Stage 1O found no documented safe account-free `metatester64.exe` launch contract. Repeated blank copied-terminal starts exited. | Documented, privacy-preserving, externally network-isolated native tester workflow with no-order output. |
| Economic performance | Synthetic broker supports deterministic spread, commission, adverse slippage, conversion, stop-first handling; `docs/BACKTEST_SEMANTICS.md`. | Broker-specific contracts, native fills/ticks, margins, swaps, actual costs and **separately authorized** economic evaluation. No profitability claim permitted. |

### Known trace omissions

`REJECT` and `ACCOUNT` kinds are schema-declared by `m030_parity.py` but not runtime emitted. Runner suppresses candidate observation when a position or order blocks evaluation, so there is intentionally no blocked `SIGNAL` record. Do not imply the log captures suppressed candidates.

## Availability of independent MT5 interface

Stage 1S found **no new supported account-free offline native source**. `MT5Broker.initialize()` requires a live MT5 terminal path (`mamba2/broker/mt5_broker.py:44-61`); `mt5_dataset.py` exporter needs functioning terminal/session; `m030_clock_discovery.py` only compares output supplied independently; `M030_ClockBarProbe.mq5` requires tester context. Opaque `.hc`, `.hcc`, tick and original MetaQuotes-Demo account/profile state cannot be assumed portable, independent or safe to copy.

## Decision — PAUSE native parity

**Formally pause M030 native MT5 verification at Stage 1S**, preserving Stage 1O's STOP on repeated blank-terminal and undocumented bare tester launch attempts. Python deterministic correctness submilestone is accepted for the exact synthetic test scope. Do not conflate those results with independent MT5 indicator/decision/clock/tick/fill parity, a production-ready trading bot, or trading profitability.

Reopen only on materially new evidence:
1. documented, account-free offline MT5 history and tester workflow, or
2. independently obtained raw native historical M1/M5/tick and UTC timestamp data with provenance and complete warmup, or
3. a separately approved privacy-preserving native tester environment producing reproducible no-order evidence.

Any future economic backtest, optimization, broker connection, order simulation or live/paper trading requires independent approval and its own safety/data gates. Do not invent historical clock offsets or infer native history coverage from opaque file presence.

## Recommended disposition

No follow-on synthetic testing just to create a stage number. Preserve code, tests and the frozen source sample, stop milestone expansion, and wait for an objectively new native-data/tester capability before resuming parity. When such evidence appears, audit it read-only before authorizing any experiment.
