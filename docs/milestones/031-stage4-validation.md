# M031 Stage 4 — corrected LEAN source validation acceptance

Date: 2026-11-12
Status: **SOURCE / PYTHON REGRESSIONS PASSED; NO C# BUILD; NO LEAN EXECUTION**

## Repository validation

Codex verified `scalping-recovery` at `8fd667a707a0ad5a0c44075fe35fe96f988e80a1`, synchronized with `origin/scalping-recovery` (0 ahead, 0 behind), clean working tree; `git diff --check` passed.

Prescribed M031 source-contract and baseline synthetic tests plus M030 parity/boundary/lifecycle regressions: **40 passed in 0.50 seconds**, 0 failures, 0 skips, no tracebacks. Python syntax checks passed. **These tests do not compile C# or prove QuantConnect LEAN API compatibility.**

The reviewed C# LEAN scope is explicitly **no-order observation-only**: canonical M1, canonical minute Ask and canonical *direct* M5 with source hashes, first-source indicator warmup, UTC completed-bar decisions, candidate observations and `M1_CLOSE` only. There are no claims of matching blocked order decisions, accepted Python `SIGNAL` events, fills, exits or trading P/L.

## Preserved original Python baseline evidence

Codex verified matching SHA-256 on each original `/tmp/mamba2-m031-baseline-authorized/` and byte-identical preserved `/tmp/mamba2-m031-baseline-authorized-evidence/` copy:

| Artifact | SHA-256 |
| --- | --- |
| `input_manifest.json` | `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92` |
| `indicator_trace.jsonl` | `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58` |
| `events.jsonl` | `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a` |
| `summary.json` | `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f` |

These SHA values are the **generated Python output artifacts**, not the canonical input source/manifest hashes. The copies are under `/tmp`; durability across cleanup/reboot is **not assured**. Any relocation/persistence of evidence to a durable path needs a distinct destination and preservation check. Never rerun the baseline just because an output copy disappears without separate approval.

Previously accepted reference output: source day 2026-09-10 UTC, 1440 M1 decision observations, 1529 emitted events, 59 raw BUY/SELL candidates, 397 blocked candidate observations, 16 actual Python SIGNAL/SUBMIT/FILL/EXIT events, 25 SLTP_MODIFY; 4 winning trades among 16 stop_loss exits with preceding trailing protection; modeled commission and slippage 0. This remains a **Python historical reference**, not independent verification.

## Runtime availability and blocker

- `lean`: unavailable.
- `dotnet`: unavailable.
- `csc`, `mcs`: unavailable.
- Docker CLI: available; **daemon inaccessible**.
- No LEAN runtime/image provisioned, C# compiler invoked, C# build attempted or independent run performed.
- There is currently no evidence of an actual C# API error. Treat static review as incomplete until compiler output exists.

## Gate / next action

**Stage 5 is a bounded read-only runtime diagnostic/plan, not another strategy-code phase.** Establish whether Docker daemon inaccessibility is caused by service stopped, user permissions, missing socket, rootless Docker context, or other environment issue, using read-only `docker info/context`, service/socket and uid/group checks. Inspect available disk/memory, cached image inventory and official/pinned LEAN runtime requirements if available, without installing or starting services. Return exact blocker, pinned runtime recommendation, source/output read-only mount plan, and authorization requirements.

Only with **separately explicit** approval: start or provision a safe isolated LEAN/.NET runtime, compile existing `lean/M031` C# without backtesting, then, on another authorization, perform one **observation-only** independent same-input candidate comparison with the preserved Python `indicator_trace.jsonl`. A C# compile error may justify the user's limited Codex fix exception, but code ownership and redesign remain with ChatGPT, not Codex.

M030's original native MT5 broker-clock/tick/execution parity remains paused. Mass Python economics and tuning remain blocked by the independent parity gate.
