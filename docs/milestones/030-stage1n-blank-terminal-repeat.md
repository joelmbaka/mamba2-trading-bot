# M030 Stage 1N — repeatable isolated empty-terminal shutdown

Date: 2026-11-12
Status: **SAFE EXERCISE COMPLETE; ACCOUNT-FREE TERMINAL SESSION NOT STABLE; TESTER NOT STARTED**

## Repository

Codex verified clean synchronized `scalping-recovery` at `f12f8b08819a93ddf6cc8b8ac5ca8a57f996c56d`, ahead/behind 0/0. No repo/source changes.

## Disposable executable and sandbox evidence

Disposable root `/tmp/mamba2-stage1n.7bYpSP`, later deleted.

- Copied `app/terminal64.exe` SHA-256 `f7e4ad40b74b05a67a03c8c7b8abf6d6f2aea45fe4669c42b67c1b361e0cfc72`.
- Copied `app/metatester64.exe` SHA-256 `d3ecb15e12e8918f80a8c531984b5a4ee6f2606ddf03504d8ec2514e7f110a49`, but **not launched**.
- Read-only sandbox mounts `/usr`, `/bin`, `/lib`, `/lib64`, `/etc` plus read-only existing Wine 11.21 runtime mounted at `/opt/wine-staging`.
- Disposable writable `/work`, new prefix `/work/prefix`, isolated proc/dev/tmp. Host home/repository/original MT5 app/prefix and host display sockets/environment unavailable.
- No route, loopback only; outbound `1.1.1.1:80` denied `ENETUNREACH` (corrected probe exit code 1, expected failure).
- `wine --version`: Wine 11.21 Staging, exit 0; `wineboot -u`: exit 0. Only known `XDG_RUNTIME_DIR` warnings.

## Bounded terminal-only execution

`timeout --foreground --kill-after=2s 20s wine /work/app/terminal64.exe /portable`: exit status **69**. Disposable terminal log:
- `MetaTrader 5 x64 build 6316 started`
- `Windows 10 build 19045 on Wine 11.21`
- `MCP started on 127.0.0.1:22346` (loopback-only)
- `Please update your MetaEditor to the latest version`
- `MQL5.community authorization failed`
- `Terminal exit with code 0`
- `Terminal stopped with 10053`; `Terminal shutdown with 10053`

The terminal did not remain stable, matching the Stage 1L pattern. Exit 69, terminal-internal 0 and shutdown 10053 are different reporting layers and should not be conflated. Exact shutdown cause **not proven**. No terminal/tester process remained; by gate, `metatester64.exe` startup was **skipped**.

Scratch and prefix deleted; no bwrap leftover; host terminal PID `71219` and host wineserver PID `35411` unchanged. No account/config/history/data copy, broker access, test jobs, EA, import/download, replay, simulation or order.

## What is supported and what isn't

Supported: a blank copied terminal reproducibly starts and terminates under the restricted headless sandbox; Wine and networking controls function. **Not supported**: whether headless display omission, missing standalone runtime assets, attempted community authorization or version mismatch *caused* exit; whether a standalone tester agent requires a persistent terminal; whether native account-free EURUSD history can be accessed; historical clock mapping or bar/tick/strategy parity.

## Next Stage 1O — read-only shutdown cause and architecture decision

Codex should compare the full existing non-sensitive Stage 1L/1N disposable logs (only if still available), previous successful MetaEditor compile setups and MQL5 no-order EA build metadata, and official/local usage documentation or binary metadata without running any process. Investigate headless/windowing requirements, MetaEditor mismatch and behavior of an empty install. Do not overinterpret 10053 without reliable documentation.

Produce a **decision matrix** for:
1. Account-free tester with stable copied terminal (if technically grounded).
2. Separate tester-agent startup if documented to be safe/no-job without terminal.
3. Alternative independently verifiable native raw-time/ohlc extraction if isolated MT5 can't run without account state (do not substitute canonical CSV for independent verification).

Prefer recommending a STOP/pivot if local evidence shows the same blocked launch is being repeated without new information. No new MT5/Wine runs, source changes or history copy in Stage 1O.

## Still forbidden

Do not launch Wine/MT5/MetaEditor/Tester, connect broker, copy account/history/profile/state, import/download data, change original running terminal/prefix, run Python historical economics, place simulated/live orders, install packages, force-push/reset/new branches, or use local-control.
