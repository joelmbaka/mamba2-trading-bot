# Next Task — M031 Stage 6A preserve evidence; compile-only approval gate

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 5 DOCKER DIAGNOSIS ACCEPTED; PINNED C# BUILD PROJECT ADDED; NO COMPILATION YET**

## Responsibility and workflow

**ChatGPT writes and reviews repository source through GitHub; Codex executes and validates.** Codex may edit source only when a genuinely executed test/build produces a concrete error, and then only the smallest necessary correction with its diff reported. No proactive source redesign in Codex.

Read `docs/milestones/031-stage5-runtime-diagnostics.md`, `docs/milestones/031-stage4-validation.md`, `docs/BACKTEST_SEMANTICS.md` and `lean/M031/README.md`.

## Verified Stage 5 blocker

- Rootful Docker daemon active, normal socket `/var/run/docker.sock` owned `root:docker` with mode 660; local user not in `docker` group; Docker client permission denied. Rootless context not present.
- `lean`, `dotnet`, `csc`, `mcs` absent; no actual C# compilation happened.
- **Do not add user to `docker` group automatically**: official Docker docs state it grants root-level privileges. Operator-reviewed one-off Docker access or separately provisioned rootless daemon require approval.

## Reference evidence — must persist

`/tmp/mamba2-m031-baseline-authorized/` (byte-identical preserved copy `/tmp/mamba2-m031-baseline-authorized-evidence/`) is tmpfs with 10-day cleanup; not durable.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `input_manifest.json` | 1624 | `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92` |
| `indicator_trace.jsonl` | 666374 | `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58` |
| `events.jsonl` | 301499 | `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a` |
| `summary.json` | 646 | `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f` |

## Next bounded Codex task — Stage 6A evidence durability, no network

1. Verify clean synchronized branch; read `AGENTS.md`, this task and Stage 5 evidence doc.
2. Check existing local original/preserved artifact paths and hashes again. **Copy** exactly the four preserved reference files to a new user-owned durable local directory outside the Git working tree, proposed `/home/joel/.local/share/mamba2/evidence/m031-2026-09-10/`, but STOP and report if this destination already exists, is a symlink, is not user-controlled or would overwrite any file. Do not delete, alter or rename source `/tmp` files. Apply owner-only directory permissions if creating a new private destination.
3. Verify file sizes and SHA-256 against the table; show destination and disk/filesystem type and return exact matches. No market replay or strategy execution.
4. Review source-only `lean/M031/M031.csproj` and its pinned `QuantConnect.Algorithm` dependency v`2.5.18248`, target `net10.0`. Run only the lightweight synthetic/source contract tests and syntax checks if helpful; no attempts to compile without a runtime.
5. Return the precise *future approval request* for a one-off .NET 10 SDK container build: official image digest/architecture to be independently resolved, operator-controlled Docker access (or rootless), disk space, separate initial network-enabled SDK/NuGet download/restore with lockfile hashes, then no-network compile of scratch copies of the 2 C# files and project. No assumption that the full `quantconnect/lean` engine image is necessary for a compile-only step.
6. Stop. Do not execute Docker setup, image pull, NuGet restore, C# compilation, LEAN engine, backtest or native MT5. Operator approval remains outstanding for those.

## Later separately approved Stage 6B — actual C# compile-only

- Rootless Docker or one-off operator-reviewed Docker access; **no persistent docker group membership by default**.
- Resolve/pin official Microsoft .NET 10 SDK **immutable digest**, separate download approval. `QuantConnect.Algorithm` v`2.5.18248` pinned; NuGet dependency restore may require a controlled network-enabled phase before final `--network none` build. Record lockfile.
- Mount repository original sources read-only, mount only a fresh staging/output directory writable, no original Wine/MT5 profiles, no `/var/run/docker.sock` inside container, use unprivileged user, drop capabilities, limit CPU/memory.
- Compile project only; no LEAN engine run/orders. Compiler errors go back to ChatGPT (Codex only minimal fixes on real compilation errors).
- After successful build, separately authorize a single independent **observation-only** LEAN engine candidate comparison on canonical sealed M1/M1 Ask/direct M5 and full first-source warm-up. Mass Python backtesting and tuning blocked until independent per-boundary signal and execution-model parity.

## Prohibitions for 6A

No `sudo`/root actions, service starts, group/user changes, Docker pulls, package downloads/installation, C# build, LEAN execution, Python historical rerun, MT5/Wine/Strategy Tester, broker access/trading, data mutation, force-push/reset or local-control.
