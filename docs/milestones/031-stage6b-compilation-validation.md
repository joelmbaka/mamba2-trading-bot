# M031 Stage 6B — pinned C# compile-only result, dependency warnings and gate

Date: 2026-11-12
Status: **COMPILE-ONLY PASSED; INDEPENDENT LEAN RUNTIME/STRATEGY EXECUTION NOT RUN**

## Provenance and authorization

Codex compiled in a user-owned scratch build environment with the operator's explicit **compile-only** approval. Repository stayed clean on `scalping-recovery` at `884b48652112da6742b882abfed66f0dbaeef214`; origin 0/0; source files unchanged. Linux x86_64 confirmed. No Docker privileges, broker, MT5/Wine, market data ingestion, historical backtest, or strategy execution.

## SDK and package supply-chain evidence

- User-local SDK: `/home/joel/.local/share/mamba2/toolchains/dotnet-10.0.404/`, exact `10.0.404`.
- SDK archive: `/home/joel/.local/share/mamba2/downloads/m031-stage6b/dotnet-sdk-10.0.404-linux-x64.tar.gz`.
- SDK archive SHA-512 verified: `577d0eb17fec33d029104c5c63a1ab0accc3e28776274abef2218dbac5af18d2109b5406d26b31d76f5c245215e3ba0926a94c20246c672c41847c9e1eb1dc50`.
- Archive path/link safety checked by Codex.
- NuGet source: `https://api.nuget.org/v3/index.json`.
- `QuantConnect.Algorithm` version exactly `2.5.18248`; 26 total resolved packages.
- Scratch lockfile: `/home/joel/.local/share/mamba2/build/m031-stage6b/src/packages.lock.json`, SHA-256 `c1b212cb8617f82a7dbe28a1bd93535c79fab2eecb5193c3494e5f6fe9d5859f`.
- The raw full lockfile package inventory has **not** been fetched by ChatGPT; do not invent exact transitive dependency parents or runtime use.

## Build result

Scratch compile-only command: `dotnet build M031.csproj -c Release --no-restore`.

- Exit code 0; **0 errors, 2 warnings**.
- Built binary `/home/joel/.local/share/mamba2/build/m031-stage6b/src/bin/Release/net10.0/M031.dll`.
- Size 42,496 bytes.
- SHA-256: `44018debe665eb1966aca44177f4ca7b59470ab629e372f204e3119705322b7f`.

This validates compilation against the selected NuGet API. It does **not** validate LEAN engine initialization, custom-data subscription, UTC source timing, indicator/candidate equality, full first-source prefix or Python-vs-LEAN trade execution.

## Supply-chain security warnings (do not silently suppress)

1. `DotNetZip` version `1.16.0`: high severity directory-traversal vulnerability `GHSA-xhg6-9j5j-w4vf` / CVE-2024-48510. Advisory lists affected `>=1.10.1 <=1.16.0`, **no patched version** for original `DotNetZip`. URL: `https://github.com/advisories/GHSA-xhg6-9j5j-w4vf`.
2. `System.Drawing.Common` version `4.7.0`: critical severity Linux/macOS graphics-file parsing remote-code-execution `GHSA-rxg9-xrhp-64gj` / CVE-2021-24112. Advisory lists patched `4.7.2` / `5.0.3`. URL: `https://github.com/advisories/GHSA-rxg9-xrhp-64gj`.

NuGet warning severities are not a claim of active exploitation or of these code paths being invoked in this experiment. Before running any LEAN engine, inspect dependency provenance (`packages.lock.json` / `obj/project.assets.json`), installed assembly inclusion, and the actual entry points in local data-only execution. Do not blindly override transitive versions: it can break pinned LEAN/QuantConnect compatibility. Never silence warning flags to claim remediation.

## Runtime options — not yet approved

LEAN's official GitHub README documents building the open-source `QuantConnect/Lean` engine with `.NET 10` and running `QuantConnect.Lean.Launcher.dll` directly on Linux. Source: `https://github.com/QuantConnect/Lean`. This **could avoid Docker socket permissions** but requires a separately pinned engine commit, dependency inventory, network package restore, isolated configuration, offline historical data wiring, and security review. It is not established that the existing M031 DLL is drop-in compatible with a different LEAN engine revision.

Official LEAN CLI local backtesting **uses Docker** and the docs note plan/tier prerequisites: `https://www.quantconnect.com/docs/v2/lean-cli/installation/installing-lean-cli`. Do not suggest simply invoking CLI backtest as a no-Docker alternative. Avoid uploading proprietary canonical CSVs to any cloud environment without explicit authorization.

## Stage 6C next gate — read-only dependency/runtime feasibility

Read-only inspect existing scratch `packages.lock.json`, `obj/project.assets.json`, compiler warning messages and built DLL /deps manifest (if present), with no additional restores/downloads. Map which upstream packages require `DotNetZip` and `System.Drawing.Common` and whether the compiled M031 direct C# assembly references these APIs. Determine whether safe isolated offline local LEAN `Launcher` execution is feasible, or if an operator-reviewed container/rootless setup is warranted. Recommend an exact pinned engine commit and minimal additional downloads only after checking official docs/repo metadata. **Do not run engine, mount data, use Docker, change package versions or rerun the Python baseline.**

## Beyond Stage 6C

Separately request explicit approval for *runtime provisioning* (not implicitly covered by compile-only approval), then separately approve **one observation-only** sealed M031 LEAN historical candidate/indicator comparison, with 1,440 UTC completed-M1 decisions and exact source-aligned BUY/SELL/NONE and indicator tolerance. Do not claim 16 actual trades, trailing stops or economic parity until an independent execution model is built and verified. Mass Python testing/tuning remains blocked.
