# M031 — independent LEAN **candidate-signal** comparator

**Status: candidate-only C# source successfully compiled on .NET SDK 10.0.404 against QuantConnect.Algorithm 2.5.18248. The LEAN engine has NOT been provisioned or run; independent signals remain UNVERIFIED.**

This C# code is intentionally a *different implementation* of the frozen
Python M031 indicator and raw-entry-condition calculations. It does not import
the Python strategy, broker or indicators. The first independent verification
gate is **1,440 complete-bar indicator observations and raw candidate
BUY/SELL/NONE decisions**, not simulated trading. The sealed Python baseline
reported 59 raw BUY/SELL candidate observations, 397 blocked observations and
16 actual strategy SIGNAL/SUBMIT/FILL/EXIT events. Those are distinct concepts.

## Fixed comparison inputs

Original files, mounted read-only:

- `EURUSD_M1.csv` — canonical Bid M1 (Unix-second UTC *bar opens*)
- `EURUSD_M1_ask.csv` — tick-aggregated minute Ask, required as a separate
  canonical source even though candidate-indicator matching does not use Ask prices
- `EURUSD_M5.csv` — **direct** canonical M5; never resample M1 for the M5
  stochastic/ATR inputs

The algorithm validates hard-coded SHA-256 hashes for the **manifest and all three CSVs** **before** subscribing. It also checks the complete available warm-up count at the first comparison boundary: 389,448 M1 and Ask rows (including the first sample bar) and 77,868 completed M5 bars.
The custom-data reader consumes each sealed multi-month CSV as a continuous
LocalFile stream; it must **not** discard rows merely because the engine's
request date changes. The algorithm checks strict source monotonicity and
exact seeded counts. The original source is never modified.

Historical source data begins in August 2025; the **complete** original source
prefix is required, particularly because EMA7 is first-source seeded. The
first compared source M1 bar opens at `2026-09-10T00:00Z` and becomes eligible
at **`00:01Z`**. The last source bar opens `23:59Z` and becomes eligible
at `2026-09-11T00:00Z`. The comparator fails closed unless exactly
**1,440** M1 observations, **1,440** corresponding Ask minute rows and **288**
canonical M5 sample rows were received, in order.

On the full prefix, M1-derived M5 differs from canonical M5 (three OHLC
mismatches among comparable bars, 83 additional derived-only buckets and
151 incomplete/missing M1 groups). Volume and spread also differ. The
independent engine must not silently consolidate M5.

## What this code does

- Uses LEAN custom data callbacks as the independent clock, with UTC source
  bar-open time and explicit bar completion.
- Independently calculates incremental Stochastic 21/7/7 on canonical M1/M5,
  EMA7 first-source recurrence, ATR14 simple rolling prior-close TR and
  the **last-ten** M1 %K extreme condition without any fresh-crossover test.
- Emits observation-only `indicator_trace.jsonl` with
  `candidate_signal`, indicator values, reason code, UTC decision boundary,
  M1 source bar open and latest completed M5 source bar open.
- Emits `events.jsonl` containing **M1_CLOSE only**. No `SIGNAL` events
  are emitted since there is no independently verified order/position model.
  Python's blocked-candidate suppression and 16 actual SIGNAL events are
  **not yet comparable** to this phase's records.
- Refuses existing Object Store output keys under a required unique run prefix.
  `input_manifest.json` and `summary.json` state
  `independent_candidate_signal_parity_only` explicitly.

The code **does not call MarketOrder, StopMarketOrder, LimitOrder, or any
LEAN broker/portfolio trading API**. This avoids the previous incorrect
unregistered Forex symbol, 0.1-lots-versus-unit ambiguity and native-LEAN
intrabar fill-model mismatch. No genuine execution or P/L parity is claimed.

## Remaining validation and runtime risks

1. **C# source compiled successfully in Stage 6B** (exit 0; warnings 2).
   Compiled DLL SHA-256: `44018debe665eb1966aca44177f4ca7b59470ab629e372f204e3119705322b7f`.
   This proves *source compilation* only, not runtime custom-data behavior,
   indicator parity, market-hours timing or trading execution.
2. The same LocalFile source is supplied across dates. LEAN's behavior when
   the custom-data reader advances the data clock across a multi-month file
   must be verified at runtime. If a pinned version cannot retain a continuous
   stream, design deterministic scratch-file daily shards rather than silently
   date-filtering or dropping original history.
3. LEAN custom-data callbacks may have date-boundary, market-hours or
   time-zone behavior that needs measured verification. A source M5 bar must
   not enter the M1 candidate calculation before its EndTime. Fail-closed
   1,440/288/1,440 and timestamp checks must pass.
4. LEAN's `ObjectStore` namespace and CSV local-file paths must work in
   the pinned container. The source mounts must remain read-only.
5. Candidate agreement should be checked on **each eligible UTC boundary**
   by source-open keys, exact direction/reason, and indicator absolute
   tolerance initially 1e-9. Decimal arithmetic is not proof of double/
   NumPy bitwise identity. Investigate any mismatch, do not relabel it.
6. The next **trade** parity phase requires a separately reviewed
   independently implemented pending/fill, stop-first, bid/ask, ATR trailing
   and exit ledger with exact 0.1 **lot** semantics. Native LEAN order
   callbacks on a different security/feed do not automatically qualify.

## Required LEAN parameters

`manifest_path`, `m1_path`, `m1_ask_path`, `m5_path`,
`sample_start=2026-09-10T00:00:00Z`,
`sample_end=2026-09-11T00:00:00Z`, and a *unique*
`output_prefix=m031/<run-id>`.

**Do not use the previously suggested bare `lean backtest ... --m1_path`
example as an executable command.** LEAN CLI normally requires a correctly
provisioned project and configuration; the supported command syntax, engine
version and file mount settings must be established in a separate approved
runtime provisioning task.

## Next steps

Codex may execute the existing lightweight Python contract/unit/regression
tests, Python syntax and git integrity checks. **Source edits remain with
ChatGPT/GitHub**; Codex should report failures and may only edit in response
to an actual execution/compilation error, preserving evidence and never
changing production Mamba2 strategy logic.

After a separately approved pinned LEAN runtime provision, compile C# first,
then run exactly one observation-only frozen-day comparison. Do not execute
MT5/Wine, historical Python replay, mass backtests, tuning, broker
connections, Docker pulls or cloud uploads without their own approval.

## Compile-only project (not a tester)

`M031.csproj` is a standalone C# library project targeting `net10.0` with
`QuantConnect.Algorithm` NuGet version `2.5.18248`. It includes only the two
M031 C# files. Its purpose is to surface real C# and LEAN API compilation
errors **without starting the engine or executing historical signals**.

Compilation has **not** yet happened. A .NET 10 SDK and exact transitive NuGet
dependencies must be provided under separate approval. The selected SDK
container needs an immutable digest; an initial network-enabled package
restore is separate from a later offline `dotnet build --no-restore`.
The original git source should be mounted read-only and copied into a fresh
writable staging directory for the build. Never expose the rootful Docker
socket inside the container or use the LEAN engine image solely for compilation.

See `docs/milestones/031-stage5-runtime-diagnostics.md`.

## Pinned compile-only environment (Stage 6B completed)

`global.json` pins .NET SDK **10.0.404** without roll-forward. Instead of
changing Docker socket permissions, this small C# project can be compiled
with the official Linux x64 SDK archive extracted into a **user-owned**
toolchain directory. The archive's official SHA-512 is recorded in
`docs/milestones/031-stage6a-durable-evidence-and-sdk-plan.md`. Always
verify the host architecture and downloaded archive hash before extraction.

Stage 6B restored 26 packages to a private scratch build directory; scratch
`packages.lock.json` SHA-256 is
`c1b212cb8617f82a7dbe28a1bd93535c79fab2eecb5193c3494e5f6fe9d5859f`.
Build result: 0 errors, 2 vulnerability warnings. Do not treat this as
independent signal parity or an engine execution test.

The persistent Python comparison reference is private at
`/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/`.

## Stage 6C pin for a possible local Launcher build

The `QuantConnect.Algorithm 2.5.18248` package metadata identifies the
matching official QuantConnect/Lean upstream commit
`a99fba023df877bd2301c14b4db37f40101d273c`. ChatGPT verified the
Launcher project at this commit targets `net10.0` and references the engine,
data-provider, brokerage, compression and other project assemblies.

Codex identified the transitive path `QuantConnect.Algorithm -> Common ->
Compression -> DotNetZip 1.16.0 -> System.Security.Permissions 4.7.0 ->
System.Windows.Extensions 4.7.0 -> System.Drawing.Common 4.7.0`.
M031 does not directly use zip extraction or image parsing, but the complete
engine may load a broader surface. No automatic package overrides or warning
suppressions are approved.

**The next stage requires separate operator approval to fetch/build the
pinned open-source Launcher in private scratch storage**. Do not execute
the Launcher, read market CSVs, use the upstream default config, expose
credentials, connect to a broker or run LEAN observations under that approval.
A minimal offline data-only configuration and no-network controls must be
reviewed before any later startup.

See `docs/milestones/031-stage6c-dependency-and-launcher-feasibility.md`.
