# Next Task — M031 Stage 6B pinned user-local C# compile (requires operator approval)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 6A DURABLE EVIDENCE ACCEPTED; SDK/DEPENDENCY DOWNLOADS AND COMPILATION NOT YET AUTHORIZED**

## Responsibilities

ChatGPT authors/reviews source and documentation via GitHub. Codex runs user-approved workstation checks. Codex only edits code if an actually executed test/build raises a concrete error and the smallest change is required; preserve output and report any changes/diffs. Never use `local-control`.

## Completed Stage 6A

- Python reference saved privately and persistently in `/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/` (ext4, `joel:joel`, directory `0700`, files `0600`), byte-identical to original `/tmp` artifacts.
- SHA-256: `input_manifest.json` `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92`; `indicator_trace.jsonl` `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58`; `events.jsonl` `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a`; `summary.json` `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f`.
- No SDK, NuGet, C# compilation, LEAN, Docker provisioning, backtest, MT5, broker or source mutation occurred.

See `docs/milestones/031-stage6a-durable-evidence-and-sdk-plan.md`, `lean/M031/README.md`, `docs/BACKTEST_SEMANTICS.md`.

## Chosen smaller compile-only path

User lacks Docker socket access because `/var/run/docker.sock` is owned by root:docker. Docker daemon is active; no need to start/reinstall it or grant persistent docker-group privileges. To validate C# types, a **user-scoped, non-admin SDK archive** is sufficient and avoids the Docker permission issue.

ChatGPT added `lean/M031/global.json` pinning exact .NET SDK **10.0.404** and a static contract test; `lean/M031/M031.csproj` already pins `QuantConnect.Algorithm` NuGet **2.5.18248**, `net10.0` and compile-only two source files.

Microsoft official SDK 10.0.404 Linux x64 artifact:
- URL: `https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.404/dotnet-sdk-10.0.404-linux-x64.tar.gz`
- SHA-512: `577d0eb17fec33d029104c5c63a1ab0accc3e28776274abef2218dbac5af18d2109b5406d26b31d76f5c245215e3ba0926a94c20246c672c41847c9e1eb1dc50`
- Official release metadata: `https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json`
- NuGet project dependency: `https://www.nuget.org/packages/QuantConnect.Algorithm/2.5.18248`

## Stage 6B — wait for explicit user authorization for these *specific* operations

Request approval for: (a) network download of that exact official SDK archive into a fresh user-owned toolchain directory, followed by SHA-512 check **before extraction**, (b) user-owned isolated NuGet cache and a **network-enabled** `dotnet restore` for the exact pinned project, and (c) local compile-only `dotnet build --no-restore` in a new scratch copy. **No sudo/Docker/socket/group changes**. No original repo/source or evidence mutation.

Once authorized, Codex should:

1. Verify branch sync, clean tree, `uname -s` = Linux, `uname -m` = x86_64, and source versions. Abort on other platform/arch; don't reuse this x64 hash.
2. Choose fresh private paths outside Git, e.g. `/home/joel/.local/share/mamba2/toolchains/dotnet-10.0.404/` for SDK, `/home/joel/.local/share/mamba2/build/m031-stage6b/` for scratch source/build, and a dedicated user-owned download folder. Abort if these paths exist, are symlinks, are unsafe, or risk overwriting anything.
3. Download **only** the official pinned SDK tarball over HTTPS; check SHA-512 against the complete checksum above, then extract as an unprivileged user. Verify `dotnet --version` = `10.0.404`. Do not pipe downloaded shell scripts to Bash.
4. Copy `lean/M031/global.json`, `M031.csproj`, `M031FrozenData.cs` and `M031FrozenBaselineAlgorithm.cs` to fresh scratch. Do not load trading CSV data: none is necessary for compilation. Disable .NET telemetry and first-time experience, use a dedicated private NuGet cache/home.
5. **Network-enabled phase, distinctly labeled:** `dotnet restore M031.csproj --source https://api.nuget.org/v3/index.json --use-lock-file`. Record complete resolved transitive dependency versions and `packages.lock.json` SHA-256. If restore fails or finds unexpected source/package issues, report exact error; do not expand network sources or privileges.
6. **No-restore compile phase:** `dotnet build M031.csproj -c Release --no-restore`. Do not claim OS network isolation unless actually enforced; `--no-restore` only forbids implicit restore. Record errors/warnings, generated assembly SHA-256, SDK and package metadata. No executable LEAN algorithm invocation is allowed.
7. If errors, report full compiler diagnostics to ChatGPT for source corrections; Codex may only implement a minimal direct fix after an actual compilation error, and must report exact diff and not alter trading semantics. Keep repo clean.
8. Stop after compilation. No independent historical LEAN run is authorized by this compile-only approval.

## Still blocked / separate authorization

An independently running LEAN engine needs a later runtime decision (rootless/user access or cloud). First stage is observation-only **candidate/indicator parity**, not trades: 1,440 UTC boundaries, 59 raw BUY/SELL candidates, direct canonical M1/M5, full warm-up, exact per-boundary signal/reason and numerical tolerance. Actual Python `SIGNAL`, fills, ATR SLTP/exit, economics and mass tuning remain blocked until separately modeled/tested. Original MT5 clock/tick parity remains unresolved.

## Prohibited

No Docker access escalation, group or service changes, `sudo`, LEAN engine runs, historical Python baseline rerun, Wine/MT5/Strategy Tester, broker access, order placement, optimization, mass testing, source dataset or preserved evidence edits, force-push/reset, local-control or unreviewed package download source.
