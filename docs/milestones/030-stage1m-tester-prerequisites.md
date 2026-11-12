# M030 Stage 1M — standalone tester prerequisites (read-only)

Date: 2026-11-12
Status: **READ-ONLY INSPECTION ACCEPTED; ACCOUNT-FREE TESTER STARTUP NOT PROVEN**

## Repository and execution boundary

Codex verified clean synchronized `scalping-recovery` at `8b93eba40ddbb91ad0864317874c2567099a9dda`; ahead/behind 0/0. No Wine, MT5, MetaEditor or Strategy Tester process was launched; no files copied or changed.

## Local binary inventory

| Binary | Bytes | SHA-256 |
| --- | ---: | --- |
| `terminal64.exe` | 131,588,216 | `f7e4ad40b74b05a67a03c8c7b8abf6d6f2aea45fe4669c42b67c1b361e0cfc72` |
| `metatester64.exe` | 24,075,856 | `d3ecb15e12e8918f80a8c531984b5a4ee6f2606ddf03504d8ec2514e7f110a49` |
| `MetaEditor64.exe` | 70,111,920 | `f9de90562ff98540278f16eb0d803a0392fd3be7a8fb6ad918817345507f2fc3` |

Application root `/home/joel/.local/share/mamba2-mt5-wine1121/app`, with empty `Tester/` and `MQL5/Profiles/Tester/`. Existing `.set` files pertain to example Math 3D EA, not M030. `MQL5/Profiles/Agents/metatrader-default.md` is development policy, not official runtime documentation.

## Supported conclusions

- Terminal/tester are distinct x64 PE binaries. Both import Windows networking APIs `WS2_32.dll` and `IPHLPAPI.DLL`; terminal additionally imports security/certificate libraries. Imports do not prove network traffic.
- Mix of UTF-16 INI and opaque binary configuration. Existing `terminal.ini` includes tester-state keys `LastBuildTester`, `LastTicksMode`, `LastExpert`, `LastOptimization` and UI state, **not** a complete standalone tester configuration.
- No supported local instruction, offline provisioning mechanism or native history import manifest was identified for tester operation without terminal/account/server metadata.
- Stage 1L only demonstrated a **short-lived terminal launch** in a blank network-denied sandbox; startup log reported build 6316, community authorization failure, newer MetaEditor request and terminal shutdown. No supported causal explanation for shutdown was proven.
- Whether the agent requires live terminal orchestration or can start in isolation remains an untested hypothesis.
- The native EURUSD `.hc`, `.hcc`, `ticks.dat` remain opaque and embedded in the account/server-specific MetaQuotes-Demo base; no cache portability or source parity is established.

## Sensitive material excluded from any future copied test

No `accounts.dat`, `servers.dat`, certificates, `common.ini`, `terminal.ini`, `settings.ini`, `bases/MetaQuotes-Demo`, EURUSD history/ticks, profiles, logs, community state, trades/subscriptions/mail/news, original Wine prefix or broad host root/home mappings.

## Proposed Stage 1N — narrowly bounded account-free executable startup

With *explicit separate authorization*, prepare a new disposable network-denied bubblewrap sandbox (host home/repo/original app/prefix not mounted; scratch-only writable; initial network absence verified). Copy **only** the terminal and tester executables, without account/history/config metadata. Initialize fresh Wine 11.21 prefix. Then:
1. Start copied `terminal64.exe /portable` with a short bounded timeout. Inspect readiness and process stability without exposing host display sockets, connecting a broker, using an EA or initiating history sync. If requested updates/login/download require unsanctioned access, stop immediately; the sandbox network-denial must continue externally.
2. **Only if the terminal is demonstrably stable and the tester agent's startup can be attempted without any backtest**, test bare `metatester64.exe` startup with a separate bounded timeout, no configuration, market data or EA. Never assume a bare agent launch can function. If a default agent startup would launch a test, download, login or unexpected service, stop.
3. Capture exact process-exit codes, non-sensitive logs, bounded network/FS checks and cleanup. Confirm original terminal PID 71219 and host wineserver PID 35411 untouched.
4. Never interpret agent existence or brief startup as native market-history coverage, a valid broker clock offset or decision/trading parity.

Do not invoke Strategy Tester jobs, run a simulated or historical order, import/copy history, connect to any broker, install packages, use local-control, edit repo/source or change original app/prefix. If safe startup cannot be isolated, return a blocker instead of weakening controls.
