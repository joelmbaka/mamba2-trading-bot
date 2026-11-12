# M030 Stage 1J — harmless-process sandbox evidence

Date: 2026-11-12
Status: **BASIC ISOLATION FEASIBILITY VERIFIED; WINE/MT5 ISOLATION UNTESTED**

## Git and operational scope

Codex verified clean synchronized `scalping-recovery` at `1e0fcc0825d2780a942db5165ccd850b7fb1784d` (ahead/behind 0/0). No source changes, cache copies, account accesses, broker connections, Wine/terminal/tester starts, imports, downloads or orders.

## Bounded non-MT5 probe

Bubblewrap using `--die-with-parent --new-session --unshare-all --clearenv`, read-only system mounts for `/usr`, `/bin`, `/lib`, `/lib64`, `/etc`, sandbox `/proc` and `/dev`, `--tmpfs /tmp`, one disposable scratch mount `--bind "$scratch" /work`, working directory/home `/work`, and restricted PATH; executes only the harmless `/usr/bin/python3` probe. The probe's executable/source location and exact invocation were recorded by Codex in its report; no executable MT5 code was run.

- `bwrap` exited **0**; process inside container PID **2**.
- Scratch read/write succeeded and scratch was removed after teardown.
- Host `/home/joel`, repository, original Wine prefix, original MT5 app and host `/proc/1/root/home/joel` were inaccessible inside sandbox.
- `/proc/net/route` empty; `/proc/net/dev` reported loopback only.
- Outbound connections to `1.1.1.1:80` and `8.8.8.8:53` failed with **ENETUNREACH**.
- No sandbox or bwrap process remained.
- Original terminal PID **71219** stayed running on host, untouched.

## Important boundaries

This establishes a usable **basic non-MT5 filesystem and network namespace isolation pattern only**. It does not establish Wine/MQL5/Strategy Tester compatibility, a security guarantee against kernel/privileged attacks, MT5 native EURUSD cache portability, or historical broker server-to-UTC alignment.

## Next gate — M030 Stage 1K

A separately authorized **sandboxed Wine runtime diagnostic** with a fresh disposable Wine prefix, copied bare Wine/MetaEditor files if essential, and a harmless `wine --version` / minimal `wineboot` experiment under the same externally enforced no-network and host-inaccessible policy. No terminal, MetaEditor compilation, Strategy Tester, original app/prefix/history copies or broker login. Account/profile/credentials remain excluded. Record exact necessary additional mounts, filesystem visibility, startup exit codes, scoped process teardown and whether network denial persists.

If Wine needs access to hidden host state, network, broader home mounts or original prefix to start, **stop** and report instead of weakening the sandbox without review. Do not re-run MT5 or trade.
