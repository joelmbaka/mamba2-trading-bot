# M031 Stage 6A — durable evidence accepted; compile-only runtime path selected

Date: 2026-11-12
Status: **EVIDENCE PRESERVED ON PERSISTENT EXT4; NO SDK, NUGET, LEAN OR BACKTEST EXECUTED**

## Git and evidence verification

Codex reported clean, synchronized `scalping-recovery` at `96047cd944913b7af93adaf2a28b0ccbfa545a40`, 0/0 divergence.

The complete sealed Python run output was copied from the verified `/tmp` reference to the new persistent, user-owned `ext4` directory:

`/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/`

No destination symlink or overwritten files. Directory `0700`, files `0600`, owned `joel:joel`. Original `/tmp` artifacts unchanged.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `input_manifest.json` | 1624 | `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92` |
| `indicator_trace.jsonl` | 666374 | `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58` |
| `events.jsonl` | 301499 | `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a` |
| `summary.json` | 646 | `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f` |

These are generated Python output hashes, **not** the immutable source CSV hashes. Keep this private evidence directory outside the public Git repo. Its presence on disk does not prove a LEAN run.

## Local compile-only strategy — avoids Docker privileges

Rootful Docker is running but the user is not in the `docker` group. Since that group grants root-level access, **do not add membership or request sudo** just to compile the C# comparator. Official Microsoft .NET SDK tarballs allow a version-pinned installation to a user-owned directory without root.

New source-only build pin added to `lean/M031/global.json`: exact **.NET SDK 10.0.404**, no version roll-forward. Existing `M031.csproj` targets `net10.0`, pins `QuantConnect.Algorithm` version `2.5.18248`, and generates a dependency lockfile at first restore. A new static test protects the exact SDK selection.

Official Microsoft release 2026-11-10 (release 10.0.15) documents SDK 10.0.404:
- Metadata source: `https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json`.
- **Linux x64** SDK archive URL: `https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.404/dotnet-sdk-10.0.404-linux-x64.tar.gz`.
- Official SHA-512: `577d0eb17fec33d029104c5c63a1ab0accc3e28776274abef2218dbac5af18d2109b5406d26b31d76f5c245215e3ba0926a94c20246c672c41847c9e1eb1dc50`.
- Source: `https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json`, SDK `10.0.404`, `rid=linux-x64`.
- Dependency: `https://www.nuget.org/packages/QuantConnect.Algorithm/2.5.18248`, targets .NET 10.0.

The checksum must be validated *after* the explicitly approved download and *before* extracting. Check `uname -m` is `x86_64` first; STOP for any other arch and obtain the corresponding official metadata hash rather than using the x64 archive. Avoid downloading and executing an unpinned bootstrap installation script.

## Next proposed Stage 6B — requires user approval for downloads

This is a **source compilation gate**, not an independent LEAN engine run:
1. Obtain operator permission for a **user-scoped** .NET SDK 10.0.404 archive download and specific NuGet dependencies (network-enabled initial restore), storing under a new dedicated user-owned M031 toolchain/build directory outside the Git working tree; no sudo/Docker modifications.
2. Obtain/verify exact SDK archive and SHA-512, extract to a fresh private user-owned toolchain directory. Record `dotnet --version`, architecture, SDK SHA and original repository HEAD.
3. Copy exactly `lean/M031/M031.csproj`, `global.json` and the two reviewed `.cs` files into a **fresh** writable scratch build directory. Do not change original sources or any reference artifacts.
4. Invoke a separately permissioned `dotnet restore` against the pinned project and NuGet source, producing `packages.lock.json` and a full dependency inventory/hash. Restore is **network-enabled**, not an offline operation. Preserve the generated lock file for ChatGPT review.
5. Run `dotnet build --no-restore` in the scratch project, with SDK telemetry disabled. Report exact diagnostics, warnings, dependency versions, binary hashes and SDK version; no strategy execution or data loading.
6. If compile errors occur, Codex reports diagnostics for ChatGPT to edit the *GitHub* source. Codex may only make minimal necessary corrections after a genuine execution error, per operator's agreement.

Full LEAN engine runtime, Docker, cloud data transfers, no-order historical observation run, execution parity, MT5 native clock parity and economic testing remain **separately unauthorized**. Compilation alone is not signal parity.

## Constraints

No changes to original production Mamba2 strategy, sealed market files or verified Python output. No trading calls, broker connections, server-state copies, MT5/Wine execution, performance tuning or mass backtests.
