# Next Task — M031 Stage 4 corrected LEAN source validation (execution-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **LEAN SOURCE REVIEW AND CORRECTIONS COMMITTED; C# NOT COMPILED; NO INDEPENDENT TESTER RUN**

## Project responsibility boundary

**ChatGPT writes and reviews source code through GitHub. Codex's primary role is to execute the requested bounded tests/builds and report evidence. Codex may edit only if a real executed check returns an error and the minimal fix is necessary; report exact changes/commits and do not change frozen strategy semantics.** Source-only/keyword tests never establish C# compilation or trading parity.

## Completed baseline / provenance

Python September 10, 2026 baseline completed successfully with sealed original EURUSD M1, M1 Ask and direct canonical M5. Reported 1,440 decision observations, 1,529 event records, 16 submissions/fills/exits and 25 SLTP_MODIFY, 59 raw BUY/SELL candidate observations, 397 blocked observations; P/L -15.842857142849278 under zero modeled commission/slippage/swap. All trades exited (including 4 profitable stop-loss exits with prior SLTP modifications). Evidence reportedly preserved at `/tmp/mamba2-m031-baseline-authorized-evidence` byte-for-byte; verify each file checksum read-only before any comparison. Native MetaQuotes-Demo data/time and broker fill parity remain unproven.

Codex's initial LEAN files `lean/M031/M031FrozenData.cs`, `M031FrozenBaselineAlgorithm.cs`, README and source contract tests were reviewed. **Original LEAN order paths were incorrect/incomparable** (unregistered Forex symbol, 0.1-lot unit mismatch, native stop/limit fills do not match Python semantics). They have been removed. See `docs/milestones/031-stage4-lean-source-review.md`.

## Corrected scope: first independent gate is raw **candidate/indicator** parity

The revised LEAN C# source implements no orders, pending state or blocked SIGNAL emission. It independently calculates M1/M5 stochastic 21/7/7, first-close EMA7, canonical M5 ATR14 and BUY/SELL/NONE raw candidate rule, using full original prefixes and UTC completed-bar boundaries. It emits 1,440 observation records and M1_CLOSE events **only**. Compare `candidate_signal`, `reason_or_error_code`, source M1/M5 open UTC, K/D, EMA and ATR from Python `indicator_trace.jsonl`; do **not** compare 16 actual Python trade SIGNALs with unimplemented LEAN orders. Candidate/raw signal matching is necessary before execution parity.

Input SHA-256 pinned for canonical manifest, M1, Ask M1 and direct M5. First sample boundary verifies full preceding M1/Ask/M5 prefix counts. Refuses reused Object Store keys. No pre-start trades, no date truncation, no future M5 exposure. Live mode prohibited. Reader/GetSource LEAN third argument corrected to `bool isLiveMode`.

## Next Codex action (bounded)

1. Verify clean synchronized `scalping-recovery`, read AGENTS.md, this document, `docs/BACKTEST_SEMANTICS.md`, `docs/milestones/031-stage4-lean-source-review.md`, and `lean/M031/README.md`.
2. Run the project’s **existing local Python synthetic tests** for `tests/test_m031_lean_source_contract.py`, `tests/test_m031_single_day_baseline.py`, and related non-economic M030 regression tests. Syntax-check only; do not execute M031 historical baseline.
3. Review latest C# source for obvious LEAN API compile blockers. Do not claim a build without a compiler. Return exact results, contract audit and needed pinned LEAN runtime/image version if not available.
4. Verify four preserved Python evidence files `input_manifest.json`, `indicator_trace.jsonl`, `events.jsonl`, `summary.json` byte-equal to original and report their SHA-256 hashes; do not rerun historical baseline.
5. If local LEAN/.NET remains unavailable, **STOP** before installations, Docker pulls, cloud uploads or historical independent run; ask for separately approved provisioning and source-mount plan.
6. Codex should **not author or redesign code proactively**. A minimal code edit is allowed only as a direct response to an actual execution/compilation error; report exactly what failed and changed. Do not change Mamba2 production strategy, original Python baseline or canonical source datasets.

## Following conditional gate (not yet authorized)

On separately approved pinned local LEAN runtime: compile C# and check API compatibility, then run **one observation-only same-input comparison** with read-only CSV mounts, explicit manifest and canonical M5 sources, a unique `output_prefix`, exact completed-bar times (first 00:01 through Sep11 00:00), and preserve independent outputs. Require 1,440 indicator observations and exact eligible per-boundary candidate directions/reasons, indicator values within predeclared 1e-9 tolerance (or justified numerical contract). Report any discrepancies. Only then implement and authorize independent trade/execution lifecycle, then consider mass Python economic testing/tuning after trade-level parity.

## Prohibitions

No additional historical Python rerun, no MT5/Wine/MetaEditor/Strategy Tester, broker access, trading/orders, optimization, unknown cloud/account uploads, Docker pull, package installation, data mutation, force-push/reset/new branch or local-control without separate approval. Native broker parity and economics remain unresolved.
