# Next Authorized Task — M030 Stage 1L isolated empty MT5 startup feasibility

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1K SANDBOXED WINE INITIALIZATION PASSED; MT5/TESTER/HISTORY NOT YET VERIFIED**

## Accepted result

Stage 1K confirmed clean synchronized source `7859e36f17fbe8c27d94e1255998ad92cc769cdf`; disposable bubblewrap sandboxed Wine 11.21 initialized with `wineboot -u` exit 0 under working network-denial and limited mounts. Host home/repo/original MT5 installation and Wine prefix were inaccessible; original MT5 terminal PID 71219 and host wineserver PID 35411 unchanged. Read `docs/milestones/030-stage1k-sandboxed-wine.md`.

No MT5 app, MetaEditor, tester, native history, account or trade functionality was run. No native data portability or historical server offset is proven.

## Next bounded Codex task, after explicit authorization

Stage 1L — **start/exit compatibility of copied empty MT5 application only**, inside a new disposable `bwrap` network/mount namespace:
1. Verify clean synchronized branch and read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, Stage 1K report and this task. Inspect minimal application binaries and dependencies. Copy only non-sensitive program binaries/resources required for startup to the disposable app; exclude all original `config`, `bases`, `Tester` history, `MQL5/Profiles`, account credentials/servers/certificates, terminal and community state/logs.
2. Recreate previously verified no-network sandbox: no host home, original prefix/app, repository mount; read-only Wine runtime mounted separately; isolated scratch writable. No broad `Z:` root/user-host mapping. Verify no-network/routes and isolation *before* invoking copied terminal.
3. Initialize fresh disposable Wine prefix; run only copied `terminal64.exe` with `/portable` and a bounded timeout if startup isolation remains intact. Probe application process start/display readiness and safe termination; do not supply account login, server config or historical data.
4. No Strategy Tester, MetaEditor, EA, clock probe, history refresh/download, broker connection or market data provisioning. If terminal attempts to demand network/login/update, prevent it via OS network deny and stop; don't weaken restrictions.
5. Capture exact commands, dependencies, logs (redact sensitive information), file realpaths, runtime network denial, process exit/cleanup, original terminal PID 71219 and wineserver PID 35411 unchanged. If GUI/display requires sharing host desktop socket or expanding host access, **STOP** and report the needed access without mounting it.

## Prohibited

Do not launch Tester/MetaEditor or broker session; no original MT5 app/prefix/profile/account/history copies; no simulation/orders, downloads, history imports, Python historical trading replay, package installs, production strategy edits, branch changes, force-push or local-control.

## Following decision

Only after Stage 1L verified standalone application startup and an independently approved offline market-data-only provisioning plan may a later isolated no-order clock/bar tester diagnostic be considered. Empty terminal startup is not parity evidence.
