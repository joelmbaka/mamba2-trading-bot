# M031 proposal — same-data, independent-engine parity before scale

Date: 2026-11-12
Status: **RESEARCH/PLAN ONLY — NO HISTORICAL REPLAY OR TESTER AUTHORIZED**

## User's required validation gate

User approved investigating historical performance but requires independent reproduction of **the exact same frozen EURUSD period** in MT5 or a suitable web-based backtester before any mass Python backtesting or tuning. Mass testing and parameter adjustment are **blocked until the independent comparison gate passes**.

This is a new independent-engine validation objective. It does **not** quietly close M030's unresolved original MetaQuotes-Demo **native market-data provenance/clock** problem.

## Proposed parity sequence

1. Freeze the canonical source bars and metadata: EURUSD `[2026-09-10 00:00Z, 2026-09-11 00:00Z)` with full existing indicator warm-up, original M1 and M5 CSV hashes, spread assumptions and exact bar-time semantics. Audit alignment of M5 prices and whether the M5 source equals resampling of M1; explicitly fail if not. MT5 custom symbols normally derive higher timeframes from imported M1, so M5 must not be assumed byte/row-equivalent.
2. Freeze untouched strategy contract: M5 stochastic 21/7/7, M1 last ten %K threshold check (no fresh cross), current M1 K/D relation, EMA7/candle filter, ATR14, initially zero SL/TP, subsequent position manager, runner guards and causal replay event order.
3. With separate explicit permission, produce **one bounded Python historical baseline** on frozen data, exporting observation-only per-boundary M1/M5 indicator values, candidate decisions, order lifecycle records and a manifest. Label Python modeled execution and costs; no broker/MT5.
4. Run the identical input through an **independently coded and executed implementation**. Preferred target is documented MT5 custom financial symbol bars/tick import + Strategy Tester under a newly reviewed privacy-preserving environment. This is **not currently runnable**: the isolated blank terminal shuts down and no account-free startup contract was proven. Alternative: QuantConnect LEAN web cloud custom data (separate algorithm implementation) subject to storage/licensing/account feasibility. TradingView provider chart data alone cannot be considered the same dataset.
5. Compare *per-boundary*, not only aggregate P/L: identical timezone/period/warm-up, M1 and M5 source OHLC, indicator K/D/EMA/ATR within stated numeric tolerance, candidate BUY/SELL/NONE, order submission, entry bar/time, volume, fill/stop/target, exit bar/time/reason; separate rule/strategy parity from tester-specific execution models and broker economics.
6. An independent **100% decision parity** gate (no unexplained mismatches, or each difference attributable and resolved) plus carefully matched execution assumptions is required before mass Python testing. Identical P/L cannot be demanded unless tick/Ask, spread, commissions, slippage, price rounding, tester fill/stop semantics and execution model also match. Aggregate profit factor or win rate alone is insufficient.
7. Only after a documented parity outcome: explicitly authorize out-of-sample/multi-period Python testing and eventually predeclared tuning with untouched holdout datasets. Never fit and judge on the same frozen verification sample.

## Verified platform facts and limits

- MetaTrader 5 official custom instrument help documents importing M1 OHLC and ticks, and strategy testing on custom symbols. M1 bars are stored and higher timeframes are synthesized. Custom-symbol testing is not proof of original broker's native raw history or independently anchored server time. It remains unsafe to retry the presently unstable sandbox without new reviewed evidence. Source: https://www.metatrader5.com/en/terminal/help/trading_advanced/custom_instruments
- MQL5 custom symbol API provides `CustomSymbolCreate`, `CustomRatesUpdate/Replace`, `CustomTicksAdd/Replace`: https://www.mql5.com/en/docs/customsymbols
- MT5 tick generation and Bid/Ask assumptions differ between real and generated ticks: https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation
- QuantConnect LEAN allows user-defined external datasets and cloud access: https://www.quantconnect.com/docs/v2/writing-algorithms/importing-data/key-concepts ; custom Object Store upload/storage restrictions: https://www.quantconnect.com/docs/v2/cloud-platform/object-store . Cloud data license/export restrictions need review before uploading or returning logs: https://www.quantconnect.com/docs/v2/cloud-platform/security-and-ip

## Immediate next authorized work: M031 Stage 0 read-only feasibility/evidence audit

A. Verify clean branch and inspect `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/milestones/030-stage1s-readiness-decision.md`, `mamba2/backtest/mt5_dataset.py`, `mamba2/backtest/m030_clock_discovery.py`, input manifests/CSV readers, strategy ports and existing MQL5 probes.

B. On *existing* immutable files, without executing a backtest, compare evidence for M1/M5 timestamps, source hashes, timescale alignment, warmup sufficiency, and whether derived M5 from M1 could equal the independent frozen M5 (source-only reasoning; no new replay).

C. Develop a feasibility matrix for MT5 custom symbols and QuantConnect with exact input/outputs, ability to host both timeframes and preserve UTC, version/runtime requirements, privacy restrictions, platform costs and limitations. Identify whether the documented custom-symbol interface offers a *new, falsifiable* hypothesis overcoming Stage 1O failure; official docs prove import/tester support, **not** standalone offline terminal stability.

D. Define canonical comparison schema, per-decision tolerances, strict pass/fail criteria and a staged order of authorization. Do not attempt tester launch, log in, import history, download, execute strategy, run Python historical economic replay or optimize.

E. Return read-only evidence and recommend one validated next step, or report that independent execution is still blocked. A paid cloud action, upload or broker action needs distinct approval.

## Hard safety boundaries

No operation against original live MT5/prefix or account. No undocumented bare metatester startup, network enabling, credential or server-state copying, real or simulated broker orders, package installations, force pushes, dataset alterations, unapproved historical economic backtesting, large-scale parameter search, or paper/live strategy deployment.

M030 remains **Python synthetic semantics validated; original MT5 native-data/time and economic parity unresolved** until independently established.
