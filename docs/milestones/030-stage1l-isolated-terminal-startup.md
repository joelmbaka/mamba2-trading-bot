# M030 Stage 1L — isolated, empty MT5 terminal startup

Date: 2026-11-12
Status: **ISOLATED APP STARTUP VERIFIED; PERSISTENT TERMINAL / TESTER / HISTORY NOT VERIFIED**

## Repository

Codex confirmed clean synchronized `scalping-recovery` at `ca48dde609cad571b75a1717e7ee1dd11d8691f4`, 0 ahead/behind. No repo modifications or existing terminal changes during Stage 1L.

## Copied binary and sandbox

Original executable: `/home/joel/.local/share/mamba2-mt5-wine1121/app/terminal64.exe`. Disposable copy: `/tmp/mamba2-stage1l-terminal2.UXUnbg/app/terminal64.exe`. Both SHA-256 `f7e4ad40b74b05a67a03c8c7b8abf6d6f2aea45fe4669c42b67c1b361e0cfc72`.

Only the executable copied. No account, server, config, certificate, profile, bases, history, Tester or common files copied. Bubblewrap read-only system mounts `/usr /bin /lib /lib64 /etc`; Wine 11.21 mounted read-only at `/opt/wine-staging`; scratch writable at `/work`, fresh Wine prefix `/work/prefix`; isolated proc/dev/tmp; no original host home, repo, original app/prefix, display socket, DISPLAY or WAYLAND_DISPLAY.

Commands:
- `/opt/wine-staging/bin/wine --version`: `wine-11.21 (Staging)`, exit **0**.
- Bounded `wineboot -u`: exit **0**; known `XDG_RUNTIME_DIR` warnings.
- `timeout --foreground --kill-after=2s 20s /opt/wine-staging/bin/wine /work/app/terminal64.exe /portable`: wrapper exit **69**. Application began initialization and terminated within timeout.

## Application evidence and limits

Decoded **disposable-only** MT5 log:
- `MetaTrader 5 x64 build 6316 started`
- `Windows 10 build 19045 on Wine 11.21`
- `Z:\work\app` — Wine's virtual Windows path, not evidence of host-root access; sandbox root remained private.
- Local MCP listener at `127.0.0.1:22346` (loopback, not external connectivity).
- Requested newer MetaEditor.
- MQL5.community authorization failed under unavailable network; no proof of broker login.
- Internal terminal exit code **0**; shutdown code **10053**. Its cause unestablished. Wrapper exit **69**; do not conflate these statuses.
- No native EURUSD history access, broker synchronization, Strategy Tester or EA execution was demonstrated. Session did not remain running; **do not assert** missing account state caused termination without causal evidence.

Sandbox reported no routes and loopback only, denied outbound access, original files inaccessible. Scratches removed, no bwrap leftovers. Original terminal PID **71219** and original wineserver PID **35411** stayed unchanged.

## Next gate — Stage 1M read-only offline standalone tester prerequisites

Before another Wine/terminal run, perform **read-only** research of local binaries, non-sensitive standalone tester documentation/example configurations and existing app layout to determine whether an isolated account-free Strategy Tester could start and work without contacting MetaQuotes, updating MetaEditor or needing original profile/server credentials. Distinguish terminal binary startup, tester-agent activation and native historical-data availability.

Specific risks: terminal's attempted online community authorization and runtime update request must be prevented externally; blank tester profile and opaque server-account history caches. A loopback MCP listener does not imply external network connectivity, but its exposure/authorization should be scoped if later use occurs.

Return evidence-based prerequisites and a fail-closed minimal next compatibility experiment. **Do not launch** Wine/MetaEditor/terminal/tester in Stage 1M, provision history, copy account metadata, connect broker, download data, place orders, or run historical backtest. A subsequent isolated test requires separate authorization.

Native server UTC offset, exact historical M1/M5 OHLC equality, tick history and full EMA warmup remain completely unproven.
