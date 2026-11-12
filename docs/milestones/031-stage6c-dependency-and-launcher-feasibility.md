# M031 Stage 6C — vulnerability dependency chain and compatible LEAN Launcher audit

Date: 2026-11-12
Status: **READ-ONLY AUDIT ACCEPTED; SOURCE-ONLY COMPARATOR COMPILED; FULL LEAN ENGINE NOT PROVISIONED OR EXECUTED**

## Source state and verified build evidence

Codex verified clean synchronized `scalping-recovery` at `6d8eef5a37d77f01d00216cc7309504b0a6f386b`, zero divergence. No edits, new downloads, package restores or execution.

- `QuantConnect.Algorithm` `2.5.18248`, 26 NuGet packages.
- User-owned SDK `10.0.404` previously verified; `M031.dll` successfully compiled source-only.
- Lockfile `/home/joel/.local/share/mamba2/build/m031-stage6b/src/packages.lock.json`: SHA-256 `c1b212cb8617f82a7dbe28a1bd93535c79fab2eecb5193c3494e5f6fe9d5859f`.
- Compiled `M031.dll`: SHA-256 `44018debe665eb1966aca44177f4ca7b59470ab629e372f204e3119705322b7f`; original source unchanged.
- Preserved Python reference remains in `/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/` with checksums in Stage 6A milestone.

## Exact dependency chain from local restored package assets

```
QuantConnect.Algorithm 2.5.18248
└── QuantConnect.Common 2.5.18248
    └── QuantConnect.Compression 2.5.18248
        └── DotNetZip 1.16.0
            └── System.Security.Permissions 4.7.0
                └── System.Windows.Extensions 4.7.0
                    └── System.Drawing.Common 4.7.0
```

Also `System.Drawing.Common` -> `Microsoft.Win32.SystemEvents 4.7.0`, `Microsoft.NETCore.Platforms 3.1.0`. This chain is Codex's report after inspecting `packages.lock.json` and `project.assets.json`; do not infer any other direct parent.

- `DotNetZip 1.16.0` high vulnerability: directory traversal on unsafe extraction, no patched release of that original package.
- `System.Drawing.Common 4.7.0` critical vulnerability: image parsing on affected platforms; patched 4.7.2 and 5.0.3.
- M031 comparison C# has no direct zip extraction, image processing or direct references to either vulnerable type. **Presence != exploitation; lack of direct references != safe whole-engine use.** Never suppress warnings as a substitute for remediation or blindly override transitive versions in a pinned LEAN engine.

## Upstream LEAN revision proof

Pinned NuGet nuspec records `QuantConnect/Lean` upstream exact commit:

`a99fba023df877bd2301c14b4db37f40101d273c`

ChatGPT fetched the official [commit](https://github.com/QuantConnect/Lean/commit/a99fba023df877bd2301c14b4db37f40101d273c) and [Launcher project](https://raw.githubusercontent.com/QuantConnect/Lean/a99fba023df877bd2301c14b4db37f40101d273c/Launcher/QuantConnect.Lean.Launcher.csproj). The Launcher targets `net10.0` and directly references `Algorithm.CSharp`, `AlgorithmFactory`, `Algorithm`, `Api`, `Brokerages`, `Compression`, `Configuration`, `DownloaderDataProvider`, `Engine`, `Indicators`, `Common`, `Optimizer.Launcher`, `Research`, `Logging`, `Messaging`, `Queues`, and `ToolBox`. This is a **strong build-compatible pin**, not proof of a runnable offline data-only configuration.

ChatGPT also checked the upstream [Launcher/config.json](https://raw.githubusercontent.com/QuantConnect/Lean/a99fba023df877bd2301c14b4db37f40101d273c/Launcher/config.json). It includes a backtesting default environment, data folder, local object-store implementation *and* extensive broker/provider/HTTP endpoints and live-mode settings. **Do not run with the default configuration**, reuse credentials, access cloud provider endpoints or assume the engine cannot connect to a network.

The open-source Launcher is the preferred path for now because it can build under the existing user-owned .NET 10 SDK without Docker socket access. This is not the same as LEAN CLI (its default local backtest flow uses Docker). Future runtime must use a minimal reviewed offline configuration with blank credentials, restricted network and isolated data/log/output directories. Do not share market CSVs with third-party cloud services without explicit approval.

## M031 Stage 6D recommendation: controlled source acquisition and build ONLY

*Requires separate operator approval of new downloads and build.* No permission is implied by the earlier 6B compile-only authorization.

1. Confirm clean synced `scalping-recovery`, no local changes; preserved sealed evidence stable and untouched. Verify local available disk space, SDK version and user permissions.
2. Create a **fresh, private user-owned directory outside repo** for LEAN engine source/build, e.g. `/home/joel/.local/share/mamba2/lean-engine/a99fba023df877bd2301c14b4db37f40101d273c/`. Do not reuse or overwrite existing paths.
3. Download/checkout only the official `https://github.com/QuantConnect/Lean` source pinned to exactly `a99fba023df877bd2301c14b4db37f40101d273c`; verify `git rev-parse HEAD` and clean engine tree. Pin/validate submodules if relevant, do not fetch arbitrary branch HEAD. No new user repository branch required.
4. Use existing SDK `10.0.404`; restore only required engine Launcher project dependencies from approved NuGet (and any upstream documented project-specific required sources only after separate review); capture package graph, NuGet audit reports, lockfile snapshots/hashes and the exact list of new dependencies. **Do not presume that the existing M031 lockfile guarantees whole-Launcher dependency safety.**
5. Build `Launcher/QuantConnect.Lean.Launcher.csproj` source-only, no execution, in its own scratch user-owned staging location. Preserve build stdout/stderr, errors/warnings, DLL hashes, architecture and package inventory.
6. If unexpected dependency source, network target, access to credentials/market data, unreviewed install script, unexpected file modification or failure occurs: STOP and report; no workarounds, privilege elevation or out-of-scope downloads.
7. No run of Launcher, no custom-data smoke test, no M031 observation run, no broker access or simulated/live orders. These are distinct future explicit grants.

The full Launcher may restore many more dependencies, including vulnerable libraries. Before any executable startup, ChatGPT should prepare a minimal private offline config and explicit no-network/no-broker guards and independently audit the M031 data stream lifecycle.

## Independent parity gate still outstanding

Only after separately approved engine provisioning and startup can a **no-order** LEAN candidate-signal run be compared with exactly 1,440 UTC decision boundaries and 59 Python raw candidate BUY/SELL signals on canonical original M1, Ask, direct original M5, full prefix and first-source EMA. Trade execution (the 16 Python trades) is a *later* separate phase. Native original MT5 server clock/tick execution remains unverified. No mass Python optimization permitted.
