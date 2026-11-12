# Next Task — M031 Stage 5 LEAN runtime blocker diagnosis (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **M031 STAGE 4 SOURCE TESTS PASSED; C# UNCOMPILED; DOCKER DAEMON INACCESSIBLE**

## Working agreement — preserve this boundary

**ChatGPT authors and reviews source changes through GitHub. Codex executes bounded checks and reports evidence; it must not proactively write or redesign source.** Codex may apply a *minimal* correction only following an actual failed execution/build with a concrete error, and must clearly report the source diff and cause. No independent LEAN engine has yet compiled or run.

## Stage 4 accepted

At clean `8fd667a707a0ad5a0c44075fe35fe96f988e80a1`, synchronized `0/0`: 40 M031/M030 focused synthetic/regression tests passed in 0.50s; 0 failures/skips; Python syntax and `git diff --check` passed. Corrected `lean/M031` source emits **observation-only raw candidates**, not orders or execution parity.

See `docs/milestones/031-stage4-validation.md`, `docs/milestones/031-stage4-lean-source-review.md`, `lean/M031/README.md`, `docs/BACKTEST_SEMANTICS.md`.

Python reference artifacts from September 10, 2026: `/tmp/mamba2-m031-baseline-authorized/` (preserved byte-identical in `/tmp/mamba2-m031-baseline-authorized-evidence/`). SHA-256:
- `input_manifest.json`: `1c448f2bf4066f4a79f75823c429db8db63739d143abb30afd1d4ad815073b92`
- `indicator_trace.jsonl`: `cd810ce1bdf4fc4aacd74db522b699a24c8c7061a71f0f553951150fa785ad58`
- `events.jsonl`: `a1a6227badaf85b5302f1b3a2ab0fb319dda87d62534b85037493f9eee16d37a`
- `summary.json`: `fc07f1f4b0eb3cb51ddcf0c470bce50dadd0c1ad6fe6f746222a374b00b9140f`

The `/tmp` location is not durable storage. Do not rerun Python historical baseline automatically if it disappears; report first.

## Blocker

`lean`, `dotnet`, `csc`, `mcs` not installed. Docker client exists, but daemon inaccessible; no LEAN image present and no build attempted. Static tests are not C# compilation.

## Next bounded Codex job: environment diagnosis ONLY

1. Verify clean synchronized `scalping-recovery`. Read `AGENTS.md`, `docs/NEXT_TASK.md`, `docs/milestones/031-stage4-validation.md`, `lean/M031/README.md`.
2. **Read-only local diagnostics**: `docker context ls`, `docker info`, `docker image ls` (if daemon reachable), `id`, `id -nG`, `ls -l /var/run/docker.sock`, `systemctl status docker --no-pager`, `systemctl --user status docker --no-pager`, `command -v docker dotnet lean csc mcs`, `df -h`, `free -h`, and Docker rootless context details if existing. If any command requires elevation or changes state, **STOP** that command; capture diagnostics with no `sudo` or changes.
3. Report whether the daemon failure is socket absence, stopped service, permissions, missing rootless context, or unknown. Distinguish absence of local compiler from source compilation failure.
4. Recommend a pinned, separately approvable LEAN runtime and smallest safe *future* compile-only path. Include container image provenance, network/package requirements, approximate storage footprint if supported by evidence, CPU/memory constraints, CSV read-only mounting and separate write-only output destination. Avoid any promise that a LEAN CLI exists already or any unverified executable command.
5. Check only current existence, hashes, size and filesystem durability risk of preserved baseline evidence. Recommend a durable storage location outside transient `/tmp` without copying or mutating files.
6. Return a decision: safe environment path known / needs privilege approval / still blocked, exact evidence, and bounded proposed provisioning command for a separate approval. **Do not** execute the provisioning or LEAN code yet.

## Not authorized

No running/stopping/enabling Docker service, root/user group edits, `sudo`, Docker pulls, packages, .NET/LEAN installation, network access, cloud data uploads, C# execution/compile when a new runtime must first be provisioned, historical backtests, Python reruns, MT5/Wine/MetaEditor/Strategy Tester, trading/order calls, modifying source/CSV data, force-push/reset/branch creation or local-control.

## Subsequent separately approved gates

1. Repair/provision isolated pinned LEAN + .NET build environment without touching original MT5 or canonical data.
2. Compile C#; if failed, apply only a minimal error-grounded fix or return trace to ChatGPT for source correction.
3. Run exactly **one** observation-only independent comparison using sealed canonical M1, M1 Ask and **direct canonical M5**, full historical indicator prefix, 1,440 UTC boundaries, unique LEAN output prefix and read-only inputs.
4. Compare every raw candidate BUY/SELL/NONE and reason and numerical indicator values to the Python reference; investigate any difference before independent execution-model design.
5. Only after candidate and execution parity gates, consider authorized mass Python testing and tuning. No MT5 native broker clock/tick parity or profitability is asserted.
