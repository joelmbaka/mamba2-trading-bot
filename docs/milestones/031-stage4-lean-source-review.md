# M031 Stage 4 — Review of Codex-authored LEAN source and safer parity phase

Date: 2026-11-12
Status: **ASSISTANT-AUTHORED SOURCE CORRECTIONS ON GITHUB; C# STILL UNCOMPILED, LEAN UNEXECUTED**

## Inputs and Python reference (Codex reports)

Sealed single-day Python baseline on original source interval `[2026-09-10,2026-09-11)`, boundary times `00:01` through next-day `00:00`, 1,440 observations, 1,529 events, 16 accepted submissions/fills/exits, 9 BUY and 7 SELL; 59 raw BUY/SELL candidates, 397 blocked observations. 4 positive stop-loss exits are supported by preceding SLTP_MODIFY events and can be compatible with trailing stops. Reported net P/L -15.842857142849278 with zero modeled commission, swap and slippage; historical Bid/Ask remains relevant. These are reported historical Python outputs, **not cross-engine verification**.

Codex reported that all four original baseline artifacts were preserved byte-identically at `/tmp/mamba2-m031-baseline-authorized-evidence`. Their actual per-artifact hash values were not supplied to this chat and have not been independently re-verified from GitHub. Do not claim that we downloaded or checked those local /tmp files.

Codex authored and committed in `3f4cce3b0ade10b44b32f66540fbeb0a2cebe822`:
- `lean/M031/M031FrozenData.cs`
- `lean/M031/M031FrozenBaselineAlgorithm.cs`
- `lean/M031/README.md`
- `tests/test_m031_lean_source_contract.py`

The eight passing tests were **keyword/source-contract tests only**, not C# compilation or LEAN execution.

## Findings and changes made directly by ChatGPT using GitHub connector

**Corrected issues:**
1. Sample boundary incorrectly admitted `2026-09-10 00:00Z`; now the comparison excludes `<= SealedStart`, includes `<= SealedEnd` and fails unless there are exactly 1,440 consecutive completed-M1 decision boundaries.
2. Unregistered `EURUSD` Forex `MarketOrder`, `StopMarketOrder`, `LimitOrder` paths would not have demonstrated an independently controlled 0.1-lot execution model. They were removed. This LEAN phase is now an **observation-only independent indicator/candidate signal comparator**, explicitly **not** an execution backtest. It produces only M1_CLOSE events, **no fake actual SIGNAL/FILL/EXIT events**, and cannot be judged against Python's 16 actual trades until a separately reviewed independent execution model exists.
3. Replaced full-prefix stochastic recomputation per boundary with incremental C# rolling 21/7/7 stochastic state and M5 ATR14 state, and maintained EMA7 first-source recurrence. Preserves ten-M1-%K extreme rule without a fresh last-bar crossover.
4. Added pinned `manifest.json` SHA-256 alongside M1, Ask M1, canonical direct M5 file hashes; first comparison boundary requires 389,448 M1 rows, 389,448 Ask rows and 77,868 completed M5 prefix rows (the first sample M1/Ask row is included).
5. Added strict M1/Ask chronological progress, complete M5 timing, no future incomplete M5 before decision, sample coverage counts M1=1,440, Ask=1,440, M5=288; guarded against existing Object Store output keys and required unique `output_prefix`.
6. `M031CsvBar.GetSource` originally had incompatible `DateTime?` third argument; fixed to LEAN's documented `bool isLiveMode`. Live mode explicitly denied. `BaseData.Value` is now populated by source Close.
7. Corrected mistaken attempt to filter full-file CSV rows by each LEAN source request date. The original multi-month CSV must stream continuously; blindly filtering by `date` could discard warmup when the LocalFile enumerator remains open. LEAN's date-switch behavior must be **confirmed in a pinned runtime**, not assumed.
8. Replaced fragile keyword tests with static guards for source independence, no order methods, required input contracts, exact boundary count, warmup and no future M5; refreshed README with true observation-only scope and known runtime risks.

**What is NOT established:**
- No `lean`, `dotnet`, pinned container, C# compiler or actual LEAN engine run was available to this turn. Source-only review/edits cannot prove LEAN C# compilation/API compatibility, date/source-stream handling, custom symbols/hours, end-date handling or parity.
- Any LEAN-vs-Python candidate agreement, indicator tolerance, full first-source warmup, 59 candidate matching count, blocked-state parity, actual trade parity, original MetaQuotes-Demo clock proof, native fill/slippage or profitability.
- If first LEAN compile/runtime produces a genuine error, Codex may propose a precisely bounded correction (user allows it to edit only in response to **actual execution errors**); prefer source changes through ChatGPT/GitHub for strategic semantics.

## Next limited validation gate

1. Codex fetch/reconcile updated `scalping-recovery`, verify clean sync and original Python baseline evidence hashes without replaying the baseline.
2. Run only existing Python **source-contract / unit / regression / syntax** tests that do not invoke historical economic replay or external networks; return exact results and signatures.
3. Static inspect C# against a **pinned** available LEAN API, without installing/pulling a runtime. Flag any additional build blockers (especially custom-data `Reader/GetSource` and Object Store integration).
4. If pinned LEAN runtime is unavailable, STOP and report exact requirements for separately approved local Docker image download/build. Do not claim an independent run occurred.
5. Once runtime separately authorized, **compile first**; only afterwards consider one bounded, observation-only run of the identical 2026-09-10 UTC sealed source with read-only data mounts and a unique OutputStore prefix, then compare 1,440 source-aligned candidate and indicator snapshots to Python `indicator_trace.jsonl`, without filling trades.
6. After exact no-unexplained candidate parity, design independent execution model matching Python 0.1 lots, Bid/Ask minute sidecar, fill timing, trailing SLTP, stop-first exits and event keys. Independent native MT5 broker/tick parity still separately blocked.

Do not run mass historical testing, parameter tuning, paper/live orders, MT5/Wine/Strategy Tester, broker access, cloud uploads, Docker pulls or package installs without new approval.
