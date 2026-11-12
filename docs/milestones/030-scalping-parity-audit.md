# M030 — M5/M1 scalping recovery: read-only audit and independent MT5 parity design

Status: **STAGE 0 AUDIT RECORDED — EXECUTION / STRATEGY IMPLEMENTATION NOT AUTHORIZED**
Date: 2026-11-12
Branch: `scalping-recovery`

## Scope, authority and operating contract

The operator restored intraday FX scalping (M5 direction, M1 entry) as the primary goal. Existing monthly M025–M029 work is retained as inactive historical research. GitHub review and source edits are performed by ChatGPT; **all workstation commands, tests, backtests, MT5/Wine interaction and screenshots are executed by Codex directly**, not through the `local-control` GitHub mailbox. The operating branches remain for now but MUST NOT receive new commands or be used for execution.

This document records a GitHub source audit, not runtime proof. No test, backtest, terminal initialization, broker connection, or real trade was performed during this audit.

## Source inventory / established original behavior

| Component | Code path | Observed implementation |
| --- | --- | --- |
| Defaults | `config.py` | Five pairs EURUSD/EURJPY/GBPUSD/GBPJPY/USDJPY; M5 trading/M1 entry, M15 disabled; stochastic 21/7/7; EMA7; ATR14/M5; 0.1 lot; SL1x/TP2x ATR |
| Signals | `mamba2/strategy/triple_cross.py` | M5 K>D for BUY (K<D for SELL); recent 10 M1 K values contain at least one oversold (<20) or overbought (>80); current M1 K>D or K<D; latest completed M1 candle green above EMA or red below EMA; optional trend/RSI/higher TF disabled |
| Indicator math | `mamba2/indicators/stochastic.py`, `moving_average.py`, `atr.py` | Production implementations with causal replay caches; compare numerical results against a matching MQL5 implementation, not just built-in indicator names |
| Signal order | `mamba2/strategy/triple_cross.py` | Buy uses Ask, sell uses Bid; orders initially have SL=TP=0; attempts requote retry; later position manager installs initial ATR protection |
| Replay schedule | `mamba2/backtest/runner.py`, `feed.py` | One boundary per completed M1 bar; each strategy evaluated sequentially, order eligible for same-boundary execution-bar open; ATR refresh and one position-management cycle per boundary |
| Offline broker | `mamba2/backtest/broker.py` | Fills at M1 execution bar open with Ask/Bid and optional deterministic adverse slippage; checks completed-bar highs/lows for exits; chooses SL first if both SL/TP touched; charges configured per-side commissions |
| Protection/trailing | `mamba2/crew/position_manager.py` | Install SL/TP from closing-side price and ATR after entry; protective monotonic trail only when near target; candidate TP can also move if SL improves |
| Historical data | `mamba2/backtest/mt5_dataset.py` | Manifest/checksum import, MT5 bars/tick-derived M1 Bid/Ask; raw tick sequence not persisted in normal backtest feed |
| Diagnostics | `mamba2/backtest/diagnostics.py`, `m020_decision_spread.py` | Spread snapshots and trade reports; baseline explicitly sets commission and adverse-slippage models to zero |
| Previous research | `docs/milestones/019-*.md` through `024-*.md` | Historical outcomes, including unprofitable holdout and previously attempted parameter variations; these must not be mistaken for fresh holdout evidence |

## Priority parity risks — investigate, do NOT silently fix

1. **Stochastic signal is not a fresh cross.** `(stoch_entry['k'] < 20).any()` over a lookback of 10 plus current K>D may fire repeatedly after earlier oversold; M5 checks current relation rather than crossover event. Preserve original expression for baseline parity. A true-cross redesign is a later, separately approved strategy hypothesis.
2. **Protection gap.** The entry request sends zero SL/TP, then installs protection in `PositionManager.update_once()`. Reconstruct fill, modification timestamp and rejected stop modifications. On real-tick testing an unprotected interval may matter; the offline broker accepts modifications without enforcing broker stops/freeze levels or latency.
3. **OHLC path ambiguity.** Completed M1 bar SL+TP collisions resolve SL first. M1 bar highs/lows do not prove which was hit first. Tick-level validation must explain, not mask, differences.
4. **Bar-open time convention.** A source 10:00 M1 candle is visible at 10:01; do not use the new candle's high/low/close for decisions at 10:01. Execution can use the 10:01 open; exact first-tick time may not equal 10:01:00.000.
5. **Trailing semantics.** Near-target triggers when remaining TP distance is less than one-third of SL-to-TP span; only more-protective SL accepted. TP may be adjusted on a successful trail. A visual tester must record each modification, not only final SL/TP.
6. **Spread/cost semantics.** Replayed bar OHLC is Bid; Ask M1 derived from ticks where available; fallback spread otherwise. Explicit commission/slippage default zero; swap unmodeled. Don't conflate broker points with pips. Capture contract size, digits, point, tick size, tick value, commission model, margin/stops rules and account currency.
7. **Live vs replay cadence.** Live configuration has a 30-second loop, replay evaluates once per completed M1 boundary. Compare exact intended decision schedule separately from identical signal mathematics.
8. **Trade/account accounting.** Quote-to-account currency conversion uses same-boundary historical pairs. Confirm MT5 test account balance/currency, netting/hedging, cost postings, open positions at test end and overnight charges.
9. **Lookback and warming.** A one-day trade sample requires pre-roll historical M1/M5 data sufficient to initialize K/D/EMA/ATR. Warm-up must not contaminate the report window.
10. **Stochastic/ATR formula parity.** Production ATR uses simple rolling 14-period True Range average, which may differ from MT5's built-in ATR smoothing; the MQL5 harness must reproduce Python arithmetic exactly. Stochastic prices, smoothing, initialization, and candle alignment must likewise be matched explicitly.
11. **Metadata and order rejection.** Offline `order_check` accepts all orders and `order_modify` accepts any SL/TP; Strategy Tester may reject volume, stop distances or freeze constraints. Report these as behavioral differences.

## Independent comparison design

**Two tracks, with the same frozen market inputs:**

A. *Causal signal parity.* Independent MQL5 Expert Advisor computes stochastic/EMA/ATR and M5/M1 signals from closed candles. It records every decision (including no-trade and filter reasons) at each expected M1 boundary. Match Python decisions before diagnosing execution.

B. *Execution parity.* MQL5 tester sends its own simulated orders and records deal/order transactions and SL/TP changes. Compare the Python model to MT5 simulated fills, costs and exits. Do not replay Python trade results as if they were independent trades.

**Common immutable identity:** repository commit SHA, strategy spec hash, dataset manifest/raw tick hash, broker server and symbol identity, symbol digits/point/tick size/contract size, time interval UTC, time-zone conventions, tester tick modeling mode (prefer real ticks), initial balance/account currency, volume, commission/spread assumptions, tester delay settings, warm-up cutoff, MT5 build and EA hash.

**Canonical event ledger fields:** `run_id`, `source_engine`, `symbol`, `event_kind` (M1_CLOSE / SIGNAL / SUBMIT / FILL / SLTP_MODIFY / EXIT / REJECT), `utc_time_ms`, `m1_source_open_utc`, `m5_source_open_utc`, `side`, `request_id`, `position_id`, `volume_lots`, `bid`, `ask`, `decision_spread_points`, `entry_or_exit_price`, `sl`, `tp`, `atr`, `ema`, `m1_k`, `m1_d`, `m5_k`, `m5_d`, `exit_reason`, `gross_pl`, `commission`, `swap`, `net_pl`, `account_currency`, `reason_or_error_code`.

**Reconciliation order:** (1) data/timeframe alignment and candle indicator values, (2) signal and submission decisions, (3) execution fill prices/times, (4) protection modifications, (5) exit timing/reason, (6) P/L and account equity. Stop at the first divergence and emit machine-readable diffs plus synchronized screenshots and MT5 tester Journal/History evidence.

**Acceptance:** exact equality for bar-boundary identifiers, decisions, side and volume under matched inputs; indicator numerical error bounded by declared floating-point tolerance; price difference no greater than one tick **only where identical tick source/execution semantics are established**; no arbitrary tolerance for different fill time or SL/TP activation; any real-tick vs OHLC divergence must be individually explained and classified, not quietly accepted. Repeated executions should produce deterministic comparable artifacts. Strict trade-by-trade and accounting parity are mandatory before performance parameter tuning. A handful of matching trades is initial evidence, not general validation.

**Caveat:** MT5 real-tick Strategy Tester may replace missing/inconsistent ticks with generated ticks. Thus record actual tick coverage and tester data quality; simply selecting real-tick mode is not proof all ticks were genuine.

## Predeclared first visual sample and expansion

Proposed first sample: **EURUSD, 2026-09-10 00:00–23:59 UTC**, with sufficient earlier data for indicator warm-up. This is a *candidate*, not a verified complete one-day dataset. Codex must first check broker tick availability, M1/M5 bar completeness and precise source provenance without inspecting P/L outcomes. If incomplete, stop and report rather than swapping dates based on profitability.

Then a frozen evaluation set including representative wide-spread time windows, an SL+TP same-M1-candle collision, trailing-modification events and rollover; classify availability in the historical data before picking exact timestamps. Expand to one week, additional pairs and one full month only after documented parity gates.

## MT5 feasibility

Official MetaTrader 5 supports Strategy Tester Visualization with EAs, order/chart history and real-tick testing; it also supports generated tick modes. A test EA must be implemented for controlled simulation and logging rather than depending on hand-timed mouse clicks.

Existing isolated Wine 11.21 terminal GUI launch is verified historically, but independent MQL5 compile/test, tick coverage and visual Strategy Tester operations are **not verified**. The prior Windows Python bridge gap is unrelated to whether a standalone MQL5 EA can be run in the terminal. Workstation GUI actions belong to Codex.

References:
- https://www.metatrader5.com/en/terminal/help/algotrading/visualization
- https://www.metatrader5.com/en/terminal/help/algotrading/testing
- https://www.mql5.com/en/docs/runtime/testing

## Future implementation map (not authorized yet)

- Instrument `mamba2/strategy/triple_cross.py`, `mamba2/backtest/runner.py`, `mamba2/backtest/broker.py`, `mamba2/crew/position_manager.py` without altering economics.
- Add a Python event ledger and diff tool under `mamba2/backtest/` and unit tests under `tests/`.
- Add an independently implemented MQL5 tester EA under a new explicit `mt5/` or `mql5/` directory and structured journal export.
- Review `mamba2/backtest/mt5_dataset.py` for immutable raw-tick persistence when exact cross-engine parity is needed; never rewrite old source evidence in place.
- Require explicit approval for production signal/exit/cost changes.

## Stage 0 closeout criteria

GitHub source audit and parity design are documented. Runtime tick completeness, tester feasibility, screenshots, and identical trades are **not yet proven** and must be assessed by Codex in subsequent explicitly authorized execution work. No strategy optimization or live order execution follows automatically.
