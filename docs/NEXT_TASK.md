# Next Task — M031 Stage 6C dependency/security and engine readiness audit (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 6B C# COMPILATION PASSED; LEAN EXECUTION AND INDEPENDENT PARITY UNVERIFIED**

## Responsibility and safety contract

**ChatGPT authors/reviews source and documentation via GitHub. Codex executes bounded approved checks, and must not proactively rewrite or redesign source.** Codex may apply only a minimal necessary fix after a genuine test/compile failure, reporting exact error and diff. Operator approves provisioning, strategy changes, broker/data access and any historical engine run. Do not use `local-control`.

Read `AGENTS.md`, `docs/CURRENT_STATE.md`, this file, `docs/BACKTEST_SEMANTICS.md`, `docs/WORKFLOW.md`, `docs/milestones/031-stage6b-compilation-validation.md` and `lean/M031/README.md`.

## Evidence accepted

Codex completed Stage 6B in isolated user-owned scratch storage on synchronized clean `scalping-recovery` at `884b48652112da6742b882abfed66f0dbaeef214`.

- User-local Linux x64 SDK **10.0.404** with verified official SHA-512 `577d0eb17fec33d029104c5c63a1ab0accc3e28776274abef2218dbac5af18d2109b5406d26b31d76f5c245215e3ba0926a94c20246c672c41847c9e1eb1dc50`.
- NuGet `QuantConnect.Algorithm 2.5.18248` + 26 resolved packages, from official `https://api.nuget.org/v3/index.json`. Scratch `packages.lock.json` SHA-256 `c1b212cb8617f82a7dbe28a1bd93535c79fab2eecb5193c3494e5f6fe9d5859f`.
- `dotnet build M031.csproj -c Release --no-restore`: **exit 0, errors 0, warnings 2**.
- Generated `M031.dll` SHA-256 `44018debe665eb1966aca44177f4ca7b59470ab629e372f204e3119705322b7f` (42,496 bytes).
- Vulnerability warnings: `DotNetZip 1.16.0` (high, CVE-2024-48510, no original-package patched release), `System.Drawing.Common 4.7.0` (critical, CVE-2021-24112, patched releases include 4.7.2 and 5.0.3). **Warning investigation required before any engine run**. Do not downgrade security by suppressing NuGet audit warnings or silently overriding dependencies.
- Source and canonical data unchanged; Python reference preserved at `/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/` under owner-only permissions, hashes in Stage 6A document. No LEAN engine, backtest, MT5/Wine, broker or trading execution.

## Stage 6C — authorized task is read-only investigation ONLY

1. Verify synchronized clean repository and read the full listed contract files.
2. Verify existing scratch `packages.lock.json` SHA-256, SDK version, assembly hash, and output. Inspect transitive dependency references using `packages.lock.json`, `obj/project.assets.json`, compiler logs and DLL/assembly references **without restoring, downloading or executing LEAN**. Identify the direct/transitive package chain responsible for both `DotNetZip 1.16.0` and `System.Drawing.Common 4.7.0`. If a dependency path is not present, say so rather than guessing.
3. Report advisory scope, patched alternatives where available, whether M031 observation-only code directly references these vulnerable types, and whether a pinned future LEAN engine needs them. Distinguish *package present* from *vulnerable functionality exercised*. Recommend least disruptive mitigation/testing and restrictions; do not modify package pins, project files, DLLs or NuGet caches.
4. Assess the **official open-source LEAN Launcher** route that can run locally under .NET, potentially avoiding Docker. Official repo `https://github.com/QuantConnect/Lean` documents Linux `.NET 10` build and running `QuantConnect.Lean.Launcher.dll`. Identify a stable exact upstream commit compatible with compiled `QuantConnect.Algorithm 2.5.18248` where independently supportable, and assess launcher/config, custom-data file access, permissions, dependency/runtime requirements, limited data-only research execution and risks. Do not clone/download engine packages or access source state outside repository if not already present. If exact compatible revision is uncertain, report uncertainty, not an invented pin.
5. Compare approaches: (a) user-local pinned .NET + source-built open-source Launcher, (b) rootless/controlled Docker or official LEAN CLI. The standard LEAN CLI backtest uses Docker, so CLI is **not** a no-Docker workaround. Report licensing/plan and runtime constraints that require operator confirmation.
6. Recommend a minimal **separately approvable** engine-provisioning task, network/download scope, privacy isolation (no credentials, no MT5/Wine paths, no broker access, original CSVs read-only), resource costs and clear stop/rollback boundary.
7. Report exact environment evidence and finish with no edits. Do not run or rerun Python baseline or execute LEAN. Return whether runtime execution is safe/blocked, and smallest future approval decision.

## Explicitly prohibited in Stage 6C

No C# compilation/recompilation, NuGet restore, additional package/engine downloads, Docker membership/socket/service changes, `sudo`, LEAN engine launch/backtest, market-data upload, Python historical rerun, MT5/Wine/Strategy Tester, trading/broker access, optimization/mass Python tests, original source/data/evidence edits, branch switches/reset/force push, or local-control.

## Next future stages — each requires separate operator authorization

**6D runtime provisioning**: establish a pinned, isolated local LEAN Launcher or approved container, review transitive dependency risk and exact configs before fetching binaries.

**7 independent candidate observation**: one LEAN historical *observation-only* run on frozen canonical M1, M1 Ask, **direct** M5; full first-source indicator prefix; exactly 1,440 completed-M1 UTC boundaries, 59 Python raw candidate observations for side/count *and exact per-boundary values*, and 1e-9 starting indicator tolerance (investigate any mismatch). LEAN emits **no orders** in this phase.

**8 independent execution model**: separately implement and verify Bid/Ask execution, lot units, pending/fill order, deferred ATR stop/trailing, stop-first exit, trade/event/account parity under a controlled cost model before any mass Python research/tuning.

This build is compile-only evidence. Original native MT5 broker/tick/server-clock parity and profitability remain unproven.
