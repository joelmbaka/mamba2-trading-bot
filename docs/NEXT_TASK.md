# Next Authorized Task — M030 Stage 1N blank terminal/tester executable startup (no data)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1M READ-ONLY AUDIT COMPLETE; ACCOUNT-FREE TESTER NOT DEMONSTRATED**

## Evidence

Stage 1M Codex verified clean synchronized `scalping-recovery` at `8b93eba40ddbb91ad0864317874c2567099a9dda`. MT5 terminal `terminal64.exe`, `metatester64.exe` and MetaEditor executables are available, but neither a standalone tester config nor any supported offline market-data-only provisioning mechanism was found. Original MetaQuotes-Demo data and account-linked configuration cannot safely be cloned. Read `docs/milestones/030-stage1m-tester-prerequisites.md`.

Stage 1L previously demonstrated only **short-lived MT5 terminal startup** with network denial, no credentials, profiles, history or display socket. Wine 11.21 initialization and sandbox network/FS isolation were separately verified in Stages 1J/1K. Native historical M1/M5 source parity and server-to-UTC offset remain unresolved.

## Next bounded Codex task — only after explicit instruction

**Stage 1N: bare executable startup compatibility under externally verified isolation, no data and no backtest.**

1. Verify clean/synchronized branch, read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and Stage 1M report.
2. Create new scratch and fresh Wine prefix; copy **only** `terminal64.exe` and `metatester64.exe`. Exclude all accounts, server config/certificates, common/settings/terminal INIs, bases/history/ticks, profiles, logs, original Wine prefix, community/trade state.
3. Reuse proven bubblewrap no-network/host-home-inaccessible sandbox; verify there are no network routes other than loopback and no access to original home/repository/MT5. No display socket or host desktop mounts; scratch-only writable.
4. Initialize Wine with bounded `wineboot -u`. Attempt **copied terminal startup** `/portable` with a bounded timeout, no EA, account or tester job. Record stability and runtime output, rather than assume that brief startup implies persistence.
5. **Only if safe and terminal remains stable**, attempt bare copied `metatester64.exe` process initialization with a bounded timeout **without scheduling a backtest**. If invocation is known to trigger a tester job, skip. Stop on unexpected update/login/download/service activity; do not weaken network isolation.
6. Report exact commands, original/copy SHA-256, prefix mount restrictions, exit codes, network verification, process cleanup and whether original terminal PID 71219 / original wineserver PID 35411 remained unchanged. Report blockers clearly.

## Prohibited

No Strategy Tester job, MQL5 EA/clock probe load, historical replay, real/simulated orders, broker login, data download/import/copies, original MT5 app/prefix modifications, software installs, repo source edits, new branches, force-push/reset or local-control.

## Following decision

Even successful bare tester-agent startup does not prove data availability, independent server clock mapping, or economic parity. A later data-only feasibility experiment would require a separate reviewed authorization and strict account-state exclusion.
