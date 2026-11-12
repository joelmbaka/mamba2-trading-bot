# Next Task — M031 Stage 6D pinned LEAN Launcher source/build authorization gate

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 6C READ-ONLY AUDIT ACCEPTED; STAGE 6D DOWNLOAD/RESTORE/BUILD REQUIRES EXPLICIT OPERATOR APPROVAL**

## Standing development contract

ChatGPT authors and reviews code/documentation through GitHub. Codex executes locally and reports evidence; source edits only if an actual run or compiler error requires the smallest possible fix, with error and diff reported. Never use `local-control`. **No more Python baseline replays**, mass tests or optimization until independent parity gates pass.

Read `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/WORKFLOW.md`, `docs/milestones/031-stage6b-compilation-validation.md`, `docs/milestones/031-stage6c-dependency-and-launcher-feasibility.md`, and `lean/M031/README.md`.

## Accepted Stage 6C

Codex verified clean synchronized repo at `6d8eef5a37d77f01d00216cc7309504b0a6f386b`; `0/0` divergence. Existing M031.dll and NuGet lockfile SHA-256 independently match: DLL `44018debe665eb1966aca44177f4ca7b59470ab629e372f204e3119705322b7f` (42,496 bytes), lockfile `c1b212cb8617f82a7dbe28a1bd93535c79fab2eecb5193c3494e5f6fe9d5859f`. User-local SDK `10.0.404`. No runtime executed.

Transitive vulnerable dependencies in package assets:

```
QuantConnect.Algorithm 2.5.18248
└─ QuantConnect.Common 2.5.18248
   └─ QuantConnect.Compression 2.5.18248
      └─ DotNetZip 1.16.0                HIGH / CVE-2024-48510
         └─ System.Security.Permissions 4.7.0
            └─ System.Windows.Extensions 4.7.0
               └─ System.Drawing.Common 4.7.0 CRITICAL / CVE-2021-24112
```

The M031 comparator directly uses neither vulnerable API, but full Launcher dependency / code execution risk is still to be controlled. Do not suppress warnings or silently override pins.

The exact upstream commit recorded in the package nuspec is `a99fba023df877bd2301c14b4db37f40101d273c` from official `https://github.com/QuantConnect/Lean`. ChatGPT verified this commit and its `Launcher/QuantConnect.Lean.Launcher.csproj`, which targets `net10.0` and references many engine/data/brokerage projects. The official upstream `Launcher/config.json` includes *live and network provider settings*, so it must never be used unreviewed for M031 execution.

## Current benchmark to protect

Private durable Python reference:
`/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/`

Sealed reference day: `[2026-09-10T00:00:00Z,2026-09-11T00:00:00Z)`; 1440 decision boundaries `Sep10 00:01` through `Sep11 00:00`, 59 raw candidate signals and 16 actual trades. For independent first phase compare only raw candidate + indicator records, not 16 trades, because LEAN comparator intentionally emits no orders. Original canonical M1/Ask M1/**direct** M5 full warmup, never M1-derived M5. Reference file hashes in Stage 6A/6B documents.

## Stage 6D — separately approvable source + engine build ONLY

**Do not execute this stage until the operator expressly approves LEAN upstream source download and all required NuGet dependencies.** The earlier Stage 6B approval covered only M031 library compilation, not the Launcher engine download/build.

Proposed bounded Codex work once approved:

1. Verify clean synchronized `scalping-recovery`, full instructions, host Linux x86_64, user-local SDK `10.0.404`, private Python evidence intact and **adequate disk space** for a multi-project LEAN checkout/restore/build. Stop if inadequate.
2. Create a **fresh**, user-owned, owner-only upstream source and build area outside repository, suggested `/home/joel/.local/share/mamba2/lean-engine/a99fba023df877bd2301c14b4db37f40101d273c/`. Stop for existing paths/symlinks/overwrite; avoid writing anywhere inside `mamba2-trading-bot` and avoid touching original Python evidence or market CSVs.
3. Acquire only official `https://github.com/QuantConnect/Lean` at exact commit `a99fba023df877bd2301c14b4db37f40101d273c`, verify repository origin and exact `HEAD` (not moving `main`), check upstream `global.json` SDK pin and any submodule requirements before additional downloads. No arbitrary scripts, build binaries or credential access. Report any unexpected host or dependency.
4. Restore the pinned upstream Launcher project using the existing SDK, with only separately approved official NuGet sources. Record exact network hosts, resolved packages, new dependency-warning/audit inventory, lockfiles and checksums. If upstream requires other SDK versions, non-NuGet sources, hidden credentials, unreviewed setup or excessive disk/network, **STOP** rather than improvising.
5. Compile **only** `Launcher/QuantConnect.Lean.Launcher.csproj` in a user-owned scratch environment. Record errors/warnings, exact launcher/runtime DLL paths and SHA-256, complete build logs, upstream git commit. Do not run `dotnet Launcher.dll` or load M031.dll.
6. Codex may correct only an actual compiler error with the smallest documented fix; prefer reporting C# diagnostics to ChatGPT for review. No parameter or strategy changes or package overrides without approval.
7. Finish with clean original `scalping-recovery` tree, exact final upstream source commit, package inventory, build result and execution readiness/blockers.

### Prohibited during 6D

NO LEAN launcher *startup*, custom-data smoke test, historical data load, observer/algorithm execution, broker connections, simulated/paper/live orders, default upstream config use, source CSV copying or uploading, Python replay, MT5/Wine, Docker socket/sudo/group changes, production strategy edits, optimization or local-control. Build only; persistent config setup must be reviewed/approved later.

## Next future gates — NOT part of 6D

**6E offline configuration/safe no-order startup:** ChatGPT authors/reviews private minimal backtesting-only Launcher config with local custom CSV path, no credentials/API/remote providers; Codex then separately approved to perform a controlled startup and data-reader smoke test only, with output isolation and no trading.

**Stage 7 LEAN candidate comparison:** another explicit approval for one historical no-order run, 1440 decision boundaries with exact indicator values and all 59 raw candidate signals versus sealed Python trace. Report any missing or mismatched bar or candidate. Match original M5 full-prefix input directly.

**Stage 8 execution parity:** independently simulate same 16 fills, ATR SLTP modifications, stop-first and Bid/Ask exits, with lot and cost model matched. No mass tuning until parity. Original broker/tick data authenticity and profitability still unverified.
