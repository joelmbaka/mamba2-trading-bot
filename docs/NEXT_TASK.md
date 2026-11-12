# Next Authorized Task — M030 Stage 1K isolated Wine startup compatibility

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1J NON-MT5 NETWORK/FILESYSTEM SANDBOX VERIFIED; WINE/MT5 NOT YET VERIFIED**

## Accepted Stage 1J

Codex validated clean synchronized source `1e0fcc0825d2780a942db5165ccd850b7fb1784d`; disposable `bwrap --unshare-all --clearenv` harmless Python process had outbound IP attempts fail ENETUNREACH, zero routes, loopback only, inaccessible original home/repo/MT5/prefix, writable scratch only, and clean process/scratch teardown. Original MT5 PID 71219 untouched. See `docs/milestones/030-stage1j-sandbox-verification.md`.

This is **not** proof that Wine/MetaEditor/MT5/tester can run inside isolation or that native EURUSD history is portable. Historical server UTC offset and native OHLC remain unverified.

## Next bounded Codex task after explicit authorization

Stage 1K is an **isolated Wine startup diagnostic only**:
1. Confirm branch clean/synced and read AGENTS.md, docs/BACKTEST_SEMANTICS.md, NEXT_TASK.md and Stage 1J evidence.
2. Reuse the established *deny-network and home-inaccessible* bubblewrap pattern, with only necessary read-only system runtime mounts and a newly allocated disposable writable prefix/scratch.
3. Probe Wine 11.21 availability using `wine --version` inside the sandbox, and if safe, bounded `wineboot -u` in a **brand-new** disposable prefix. Allow only Wine initialization-related activity in that prefix. No MT5/MetaEditor binaries launched.
4. Verify network routes/interfaces and outbound denial **within this new sandbox**, plus no access to original app/prefix, accounts, repo or user home. Log exact isolation mounts and any Wine-specific dependencies that are required. Stop if Wine requires granting original environment access or network.
5. After exit, confirm scoped Wine/wineserver processes terminated, scratch removed, original terminal PID 71219 unchanged. Report command, init exit codes, registry presence, logs and unresolved blockers.

## Prohibitions

Do not launch MT5, MetaEditor, Strategy Tester or compile anything; do not copy original MT5 program or cached market history/account profiles/configuration, connect broker, download/import market data, place simulated/live orders, run Python historical backtest, install software, change source, modify original prefix, open new branch, force push or use local-control.

## Next decision

Only after successful Wine isolation may a **separately authorized** isolated tester application compatibility and market-data-only history feasibility experiment be scoped. Still no permission for strategy/clock-probe execution or broker activity.
