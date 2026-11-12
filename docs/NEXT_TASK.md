# Next Task — M031 Stage 1 frozen input seal and independent adapter design (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **M031 STAGE 0 ACCEPTED; SINGLE-DAY BASELINE AND INDEPENDENT RUN NOT YET EXECUTED**

## User objective

Prove same-data independent **MT5 or web-based backtesting engine** decision and trade parity for the *identical Python-tested EURUSD period* before mass Python historical tests or parameter tuning. Match source timestamps, source OHLC, full causal warmup, indicator outputs and every eligible BUY/SELL/NONE decision—not merely overall profit statistics. Trade/fill and economic parity are separate gates because feed spread/tick and engine fill assumptions differ.

Read `docs/milestones/031-independent-engine-parity-gate.md` and `docs/milestones/031-stage0-independent-tester-feasibility.md` for exact provenance and contract.

## Stage 0 accepted findings

- Frozen UTC period `[2026-09-10,2026-09-11)`: 1,440 EURUSD M1 bars, 288 M5 bars, all 288 M1 5-bar groups complete. **288/288 derived M5 OHLC bars matched native-source M5 OHLC on this day**.
- All 288 M5 tick-volume and spread fields **differ** between derived M5 and canonical M5 records. Do **not** claim full-record, native spread or execution equivalence.
- Pinned original canonical source `backtest_data/m022-history-inventory-tick-m1-v2/`: manifest SHA-256 `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`; M1 `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe`; M1 Ask `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c`; M5 `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9`. Existing exporter’s integer Unix-second UTC interpretation is **not independent MT5 server-clock verification**.
- MT5 custom-symbol import and Tester are supported platform features but currently existing isolated Wine/MT5 starter is not stable; no account-free safe tester workflow proven. Do not retry blank startup or undocumented tester agent.
- Local `lean`/`dotnet` missing; Docker available, no LEAN image, no local adapter. LEAN provisioning, image pull, cloud uploads and runtime execution require separate approval.

## Next bounded Codex task — Stage 1 read-only input sealing

1. Verify clean synchronized branch. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and both M031 milestones.
2. Read-only audit source manifests/hash provenance, M1/M5/Ask day records, **complete actual indicator warmup prefixes** and whether M1-derived M5 OHLC equals independently exported M5 OHLC for all needed earlier bars (not only 288 sample bars). Detect mismatches, missing minutes, spread/Ask assumptions, and source ambiguity. Do not execute any trading replay.
3. Determine exactly which bar series and time fields a LEAN independently implemented strategy must consume; avoid implicit LEAN M5 consolidation where input history mismatches. Pin full-prefix indicator seeding, trading-session boundary behavior, UTC timestamp/source-open event keys, no fresh crossover, deferred initial SLTP, blocked candidate observability and tester-mode tick/cost caveats.
4. Produce a *reproducible but unexecuted* single-day Python baseline command and output manifest contract for per-boundary indicators, signal reasons, order/SLTP/exit events, hashes, and no portfolio optimization. Identify any code instrumentation needed and propose reviewed source-only changes, without editing.
5. Produce a minimal LEAN Docker or cloud adapter plan with precise runtime dependencies, source-code independence from Python Mamba2 strategy, CSV mount/privacy, expected outputs and package/network requirements. Distinguish local Docker image pulls from cloud uploading and cost commitments; neither is approved by this read-only task.
6. Report pass/fail dataset seal, blockers and the smallest separately approved bounded Python baseline + independent-engine provisioning gate.

## Prohibited for this stage

No tests or historical economic replay, no Wine/MT5/MetaEditor/Strategy Tester starts, undocumented metatester invocations, broker sessions, market-data downloads, Docker pulls/installations, cloud uploads, live/paper/simulated orders, parameter optimization, repo edits, reset/force-push or local-control.

## Subsequent explicit gates

A single **frozen-day Python baseline** may be authorized once data seal passes; a LEAN custom data runtime or supported MT5 custom-symbol tester requires separately reviewed privacy/technical approval. **Mass Python tests/tuning only after cross-engine matching eligible-boundary decisions and execution assumptions**, with broker economics considered separately.

M030 remains: Python synthetic semantics validated; independent native MT5 market-data/clock and broker execution parity unverified.
