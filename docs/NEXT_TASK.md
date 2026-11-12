# Next Authorized Task — M030 Stage 1M offline standalone-tester prerequisites (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1L COPIED TERMINAL STARTED IN ISOLATION; STANDALONE TESTER READINESS UNPROVEN**

## Prior evidence

Stage 1L Codex verified clean synced `scalping-recovery` at `ca48dde609cad571b75a1717e7ee1dd11d8691f4`; only copied bare MT5 terminal binary SHA-256 `f7e4ad40b74b05a67a03c8c7b8abf6d6f2aea45fe4669c42b67c1b361e0cfc72` was launched inside existing network-denied, host-inaccessible bubblewrap sandbox after successful `wineboot -u`. MT5 x64 build 6316 began starting, wrote only disposable local defaults/logs and exited; `timeout` wrapper status 69, internal terminal exit code 0, shutdown code 10053 (unknown cause). Logged attempted MQL5.community authorization (failed) and request for a newer MetaEditor; local loopback MCP. No tester/EA, broker or historical dataset operation. Original MT5 PID 71219 and wineserver PID 35411 unchanged. See `docs/milestones/030-stage1l-isolated-terminal-startup.md`.

## Immediate next task after explicit instruction (READ-ONLY)

Codex:
1. Verify clean branch and origin sync. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, Stage 1L report, and this file.
2. Inspect local **non-sensitive** MT5 terminal/tester program binaries and existing app directory layout, tester configuration documentation and any available non-secret usage/help/reference evidence. **No Wine or MT5 launch**.
3. Determine what is needed for account-free, network-disconnected tester launch: whether a stable terminal session is a prerequisite; relationship between `terminal64.exe`, `metatester64.exe`, tester settings, agent processes and compiled no-order EA; whether an update/authorization attempt may block startup. Distinguish evidence from assumptions.
4. Reconcile process exit evidence (wrapper status 69 vs internal exit 0 and shutdown 10053) only where the existing logs support a cause. Never claim failure due to missing account state without proof.
5. Inspect permissible offline use of a *blank* isolated configuration versus sensitive original accounts/servers/certs/profiles. Do not copy any of them. Determine if market-data-only provision is possible on present evidence; if unknown say so.
6. Report exact prerequisite matrix, missing evidence, risks and narrowly scoped next *separately authorized* safe compatibility experiment.

## No authority to do

No Wine/MT5/MetaEditor/Strategy Tester starts, account or native-history copies, imports/downloads, broker connection, Python historical economic backtest, simulation/orders, installs, repository edits, original state changes, force-push/new branch, or local-control.

## Following decision

Only if standalone-test prerequisites are evidence-supported can an isolated no-order diagnostic launch or data provisioning step be separately considered. Historical clock offset, native bar/tick identity and trading parity remain unproven.
