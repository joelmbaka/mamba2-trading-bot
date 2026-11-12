# M030 Stage 1K — Wine initialization inside network-denied sandbox

Date: 2026-11-12
Status: **WINE-ONLY SANDBOX STARTUP VERIFIED; MT5 APP AND TESTER NOT EXECUTED**

## Repository and isolation

Codex verified clean synchronized `scalping-recovery` at `7859e36f17fbe8c27d94e1255998ad92cc769cdf` (ahead/behind 0/0). Stage 1K used bubblewrap with isolated network, process and filesystem namespaces. Read-only system mounts: `/usr`, `/bin`, `/lib`, `/lib64`, `/etc`; existing Wine runtime from `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging` mounted read-only at `/opt/wine-staging`. Only disposable scratch writable at `/work` with fresh Wine prefix `/work/prefix`. Isolated `/proc`, `/dev`, `/tmp`. Host home, repository, original MT5 app and original Wine prefix not mounted.

## Execution evidence

- `/opt/wine-staging/bin/wine --version`: exit **0**, `wine-11.21 (Staging)`.
- `timeout --foreground 20s /opt/wine-staging/bin/wineboot -u`: exit **0** and new disposable `system.reg`, `user.reg`, `drive_c`, `dosdevices` generated. Two `XDG_RUNTIME_DIR is invalid or not set` warnings, not startup blockers.
- Network had **no routes**, loopback only. Outbound `1.1.1.1:80` and `8.8.8.8:53` failed `ENETUNREACH`.
- Host home/repo/original app/prefix/host process root were inaccessible from sandbox.
- Verification subprocess returned **0**. Scratch removed; no sandbox or bwrap leftovers. Existing host wineserver PID **35411** and terminal PID **71219** stayed unchanged.
- No MetaEditor, MT5 terminal, Tester, broker connection, history access/copy, order or installation. No repo changes by Codex.

## Scope of acceptance

**Only Wine startup and basic filesystem/network sandbox effectiveness are demonstrated.** This does not prove MetaTrader5 terminal application or Strategy Tester works under sandbox; nor native market-history portability, exact OHLC, clock offset, tick completeness or trading parity.

## Stage 1L — bounded no-account MT5 application startup

A separately approved Codex experiment should evaluate a *minimal copied standalone MT5 application*, in a **brand-new disposable sandbox** with the same external network-denial and host-home invisibility safeguards. **No broker account/profile/data/config/cache copied.** Inspect copied file inventory/realpaths and reject server/account files. Test only whether a copied MT5 terminal executable can start, display/init and exit cleanly offline; **no tester, EA load, replay, history synchronization or data provisioning**. Prefer headless/offscreen safe launch where feasible; do not expose original desktop socket or broad display access without a separately reviewed mount. Report if terminal cannot start without network/account state, rather than relaxing isolation.

Security controls: original PID 71219 and wineserver PID 35411 untouched; scoped process cleanup; no writes outside ephemeral scratch; no original app/prefix/repo mounts; check network deny during runtime and after; enforce explicit timeout/abort on any attempted login/download/update. No configuration/data carryover, no installation, no simulated/real orders.

A successfully started empty terminal still proves **nothing** about native history availability. Access to opaque EURUSD `.hc`/`.hcc`/`ticks.dat` market-data files remains a later *separately authorized* question.
