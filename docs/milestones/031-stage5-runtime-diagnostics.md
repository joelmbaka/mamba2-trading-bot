# M031 Stage 5 — Docker blocker and compile-first approach

Date: 2026-11-12
Status: **READ-ONLY DIAGNOSTICS ACCEPTED; SEPARATE RUNTIME PROVISIONING APPROVAL REQUIRED**

## Git/repository check

Codex confirmed clean `scalping-recovery` at `a35609d7d3daf15c962a161b1f409a26f0ad8868`; `origin` synchronized 0/0, no repository modifications or service changes.

## Docker / LEAN diagnostics

- Docker client: `/usr/bin/docker`, context `default`, socket `unix:///var/run/docker.sock`.
- Docker daemon: **running**, PID 3510 at inspection time; socket mode `0660`, owner `root:docker`.
- User `joel` not in `docker` group; `docker info` and image inventory: permission denied.
- No user-rootless context or service; `dotnet`, `lean`, `csc`, `mcs` unavailable.
- Conclusion: socket permission issue, not missing/stopped daemon or a tested C# build failure. Absence of the image inventory does **not** establish whether any images exist.

Official Docker documentation warns that `docker` group membership grants root-level control over the host. Avoid granting permanent access solely for a one-off compilation; prefer separately configured rootless Docker, or an operator-reviewed **one-time privileged invocation with tightly scoped mounts and nonprivileged container settings**. Both need explicit operator approval. See https://docs.docker.com/engine/install/linux-postinstall and https://docs.docker.com/engine/security/rootless/ .

## Python reference preservation — checksum-pinned but transient

Codex compared original and preserved copies, all byte-identical. Original `/tmp/mamba2-m031-baseline-authorized`; preserved `/tmp/mamba2-m031-baseline-authorized-evidence`. Reported sizes and hashes:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `input_manifest.json` | 1624 | `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92` |
| `indicator_trace.jsonl` | 666374 | `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58` |
| `events.jsonl` | 301499 | `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a` |
| `summary.json` | 646 | `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f` |

`/tmp` is tmpfs with active daily cleanup timer and 10-day policy; two copies in `/tmp` are **not durable**. Priority is to copy to a chosen persistent user-owned data/evidence directory, validate SHA-256, and protect from overwrite; no historical rerun.

## Lower-footprint compilation path authored by ChatGPT

The official LEAN **engine** Docker image is large (Docker Hub shows latest amd64 compressed image size around 13.08 GB at inspection, and no local image was verified). It is unnecessary merely to check C# type/API compatibility.

Official `QuantConnect.Algorithm` NuGet package version `2.5.18248` targets `.NET 10.0` and is listed at https://www.nuget.org/packages/QuantConnect.Algorithm/2.5.18248 . The official QuantConnect/Lean main branch docs also recommend a .NET 10 SDK. These **web-published capabilities are not local build proof**.

ChatGPT added `lean/M031/M031.csproj` targeting `net10.0`, `OutputType=Library`, `EnableDefaultCompileItems=false`, deterministic build, and exact `PackageReference Include="QuantConnect.Algorithm" Version="2.5.18248"`. It includes only the two candidate-comparator C# source files. Static XML contract test added to `tests/test_m031_lean_source_contract.py`.

This project is for **compile-only** validation; it does not run LEAN, execute the algorithm, access prices or perform a backtest. It is not yet compiled, and its transitive dependency closure is not yet locked by an actual `packages.lock.json`. A supported SDK container image must be pinned to a specific manifest digest before use. The full LEAN engine/container remains a **later** gate after successful compilation.

## Next authorization and procedure — do not execute implicitly

1. **Preserve evidence** into a chosen persistent user-owned path, copying all four baseline files and independently validating the exact above size/hashes; do not change originals or commit outputs to the public repo.
2. **Operator-approved Docker access**, preferably rootless or a one-off carefully reviewed privileged operator command; do not change membership in `docker` group by default.
3. **Resolve and pin official Microsoft .NET 10 SDK container by immutable digest** with architecture, provenance, size and version. Pull requires separately approved network+disk. An SDK-only image can compile this project without pulling the full LEAN engine.
4. In a fresh writable staging folder outside the Git checkout, copy exactly `M031.csproj`, `M031FrozenData.cs`, `M031FrozenBaselineAlgorithm.cs`. Mount original repository read-only if needed; do not expose `/home/joel` wholesale, `/var/run/docker.sock` inside container, original Wine/MT5 prefix or credentials.
5. Initial `dotnet restore`/NuGet resolution requires a **separately approved dependency download**, unless packages are already cached. Record exact packages, hashes and generated lockfile. A later `dotnet build --no-restore` can run `--network none` in a bounded SDK container. Use a scratch build output location. Do **not** call a network-enabled restore a network-isolated compile.
6. Codex executes checks and reports exact compiler diagnostics; ChatGPT owns proactive source corrections. Codex may make only a minimal change in direct response to real build error, as previously agreed.
7. Even a successful C# compilation **does not establish LEAN engine runtime/data-subscription behavior or cross-engine signal parity**. Those require a separately authorized, sealed-data, observation-only LEAN engine run and per-boundary comparison.

Do not download/run LEAN engine or provision any privileged Docker action until the user approves. No MT5/Wine/broker, trading, mass backtests or tuning.
