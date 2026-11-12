# M030 Stage 1O — read-only startup architecture review and STOP decision

Date: 2026-11-12
Status: **ACCOUNT-FREE MT5 STARTUP PATH STOPPED — NO NEW EVIDENCE-SUPPORTED EXPERIMENT**

## Source and scope

Codex verified clean synchronized `scalping-recovery` at `a73126f100b5be268a4fcdcbd00fbb5ed5413f26`; ahead/behind 0/0. No Wine, terminal, MetaEditor, tester or broker operation; no files copied or modified.

## Reproducible outcomes — not proven causes

Stage 1L and Stage 1N both initialized isolated Wine 11.21, briefly started blank MT5 terminal build 6316, then observed failed MQL5.community authorization, request for newer MetaEditor, internal exit `0`, shutdown `10053` and outer Wine command result `69`. No accounts, profiles, source history or original terminal state supplied. A stable terminal session was **not** demonstrated.

The disposable run logs have been deleted. Remaining original-terminal config metadata report `LastBuild=6316`, `LastBuildTester=6316`, `LastBuildIDE=6316`, `ProgramBuild=6230`. Those values are mixed/stale, and do not identify the shutdown cause. Earlier independent compilation succeeded under MetaEditor `5.0.0.6316`.

- Original terminal binary SHA-256: `f7e4ad40b74b05a67a03c8c7b8abf6d6f2aea45fe4669c42b67c1b361e0cfc72`.
- Original tester binary SHA-256: `d3ecb15e12e8918f80a8c531984b5a4ee6f2606ddf03504d8ec2514e7f110a49`.

Exit code `69` is an outer process result, **not established as an MT5 error code**. Internal exit `0` only indicates entry into shutdown, not stable successful execution. `10053` numerically corresponds to WSAECONNABORTED in Windows networking, but no evidence identifies the affected socket or responsible component. Headless environment, missing resources, community failure, version disagreement and absent account state all remain **hypotheses**.

## Tester standalone and source-data constraints

No documented, supported contract was found guaranteeing safe standalone `metatester64.exe` startup without test jobs, broker/account access or history synchronization. Static strings (`tester_get_status`, `tester_prepare_config`, `tester_run_backtest`, `mqlogin`, `serverAuth`) demonstrate capabilities but not a safe standalone execution mode.

Opaque native EURUSD `.hc`, `.hcc` and tick files remain embedded in account/server-specific terminal state. Their offline portability, exact source histories, native candle timing and correspondence to immutable Python-exported CSVs are unproven. No independent historical MetaQuotes-Demo server-to-UTC mapping has been established. Repeating the blank startup cannot resolve these facts.

## Decision

**STOP Stage 1L/1N-style blank terminal retries and unauthorized bare tester-agent execution.** Do not infer an offset, copy full sensitive terminal state, expose credentials, enable broker access, provision alternate market history as though native, or claim Python/MT5 parity.

Two separate tracks remain:

**A. Python deterministic correctness (source-only):** Maintain frozen M5 direction/M1 entry strategy, original stochastic 21/7/7, EMA7, M5 ATR14, 1×ATR SL/2×ATR TP and stateful execution semantics. Prefer audited unit and synthetic causal regression fixtures, completed-candle timing, state/lifecycle invariants, deterministic event ordering and diff diagnostics. No historical economic replay, new strategy tuning or trading without separate authorization.

**B. Native MT5 parity (blocked):** Only reopen after materially new supported documentation, a validated account-free native history export/reader, or a separately approved, privacy-preserving MT5 environment with independently verified raw timestamps/OHLC and explicit clock mapping. Existing EX5 and Python test results do not confer tester, trading or backtesting readiness.

## Next bounded task

Stage 1P **read-only Python decision/execution parity gap assessment**: inventory existing source and synthetic tests without replay or changes, rank uncovered invariants and propose a narrow source-only test milestone. Make distinctions among indicator, signal decision, execution/position state and actual economics. This can advance independently of blocked MT5 native parity.

No repository changes were made by Codex during Stage 1O. The GitHub milestone/document changes that record this decision do not represent a validation of any tester run.
