# M030 Stage 1A — Independent scalping parity harness

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **IMPLEMENTATION SCOPE AUTHORIZED; RUNTIME EXECUTION NOT AUTHORIZED**

## Objective

Implement independent, traceable Python and MQL5 instrumentation to compare the original M5-direction/M1-entry scalping strategy before any tuning. Stage 1A must not change strategy decisions, signal mathematics, entry/exit scheduling, costs, stop/trailing behavior, production settings, broker connectivity, or actual trading.

Stage 0 preflight was reported by Codex as clean/synced at `c36296c3fe3c74d82e50d30164595f78e9351bee`. Wine 11.21, MT5 terminal, MetaEditor and metatester64.exe were located. The installed MT5 executable build, tick-cache coverage and Tester GUI readiness remain unverified. EURUSD 2026-09-10 UTC repository M1 (1,440) and M5 (288) bars plus at least 24h warm-up are reported available under `backtest_data/m022-history-inventory-tick-m1-v2/`; source equality with MT5 cached ticks is **not** established.

## Phase 1A deliverables

1. **Frozen protocol:** EURUSD, `[2026-09-10T00:00:00Z,2026-09-11T00:00:00Z)`; data pre-roll separate from score window; M5 direction, M1 entry; stochastic 21/7/7, EMA 7, ATR14 M5, SL 1× ATR, TP 2× ATR, 0.1 lot. The original recent-extreme signal (not a fresh cross) and zero-SL/TP submission then protective modification remain unchanged. Compare baseline without the optional M020-D spread filter.
2. **Python observation adapter:** causal, opt-in event collection around `mamba2/backtest/runner.py`, `broker.py`, `mamba2/strategy/triple_cross.py`, `mamba2/crew/position_manager.py` and indicators. Default-disabled so ordinary replay output and strategy economics are preserved. Record every boundary, no-signal reason, submission, fill, protection modification/rejection, exit and account entry.
3. **Independent MQL5 test-only EA:** source under `mql5/` or `mt5/`, visibly marked TESTER-ONLY, with explicit fail-closed checks for tester context; no production EA modifications. Compute stochastic, EMA and **simple rolling TR ATR** to match Python, rather than trusting MQL5 built-in indicator naming. Decisions must use completed M1/M5 bars only. Include optional decision-only mode that sends no orders; simulated order mode must remain disabled by default and is reserved for separately approved Stage 2.
4. **Canonical data/export schema:** shared versioned CSV/JSONL event schema with `run_id`, engine, strategy/source hashes, UTC boundary and bar-open IDs, event sequence, Bid/Ask, indicator values, signal/reason, order request/retcode, position/deal identifiers, SL/TP before/after, execution/fill times, volume, tick/point specs, cost components and account-currency P/L. Store historical/source and terminal metadata outside the event stream in a manifest. Preserve raw evidence; do not overwrite existing historical artifacts.
5. **Deterministic comparison utility:** align boundaries and independent decisions first, then order/fill, protection, exit and financial records. Produce a first-divergence report with both raw events and mismatch categories (missing/inconsistent ticks, data/timing, indicator arithmetic, signal, spread, fill, broker stop/freeze, position modification, intrabar ambiguity, conversion/cost).
6. **Synthetic tests and fixtures:** test bar-close causal alignment, independent stochastic/EMA/ATR vectors, repeated-extreme-vs-cross distinction, entry with SL/TP=0, protection/trailing monotonicity and rejected modifications, Bid/Ask and point-vs-pip conventions, no-trade boundaries, same-candle SL+TP stop-first, event serialization and comparator error classification. No lookahead; no live broker/session.
7. **Execution guide:** commands for Codex to verify installed MT5 build, MetaEditor compile capability, Strategy Tester mode and isolated terminal/account context **without launching a backtest during Stage 1A**; require a local preflight report before runtime authorization.

## Non-negotiable independence

The MQL5 EA must derive its own indicator values and decisions from MT5 price series. It must **not** import Python decisions or execute a predetermined Python order list. Matching a Python-exported dataset is not sufficient proof that the MT5 Strategy Tester used identical ticks; record actual data provenance and coverage before Stage 2.

## Parity gates

- Gate A: implementation static review, tests supplied and safety guards verified; normal Python backtest behavior unchanged.
- Gate B: Codex independently confirms isolated terminal build, MetaEditor compilation, clean working tree, synthetic test results, tester-mode isolation, time-zone alignment, frozen market-spec inputs and tick provenance. Running local unit tests and compiler is **not** authorized by this document; Codex must receive explicit execution scope.
- Gate C: separately authorized one-day Python historical replay and MT5 visual Strategy Tester execution with simulated orders only, followed by event-by-event reconciliation. No backtest run or tester order is authorized in Stage 1A.
- Gate D: expand additional dates/symbols only after precise divergence classifications and sign-off.
- Gate E: optimization, forward paper and live trading remain out of scope.

No hard-coded tick/P&L tolerance should be used to conceal unmatched execution sources. Exact signal/boundary/side/lot equality is required for matched inputs; indicator tolerance must be documented; entry price within one tick is admissible only if tick source and execution semantics truly match. Stop/TP activation time and modification rejection mismatches may not be waived.

## Ownership and safeguards

ChatGPT owns GitHub design and implementation on existing `scalping-recovery`. Codex alone runs local commands, compiler, tests, Wine, terminal GUI, screenshots and later historical replay after separate authorization. Never use `local-control` or `local-control-results` for execution. No broker initialization, external data downloads, terminal order sends outside Strategy Tester, software installation, parameter tuning, schedules, force pushes, or branch proliferation.

## Stage 1A completion

Source files plus synthetic tests and deterministic comparison protocol committed to `scalping-recovery`; reviewed for original semantics and no-order safe defaults. Report exact commit and hand off to a separately scoped Codex validation. Do not claim MT5 parity merely from successful compilation or Python unit tests.
