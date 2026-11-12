# Next Authorized Task — M030 Stage 1O shutdown/standalone-tester architecture review (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1N TERMINAL STARTUP REPRODUCED BUT SHORT-LIVED; TESTER AGENT UNTESTED**

## Accepted Stage 1N evidence

Codex verified clean synchronized `scalping-recovery` at `f12f8b08819a93ddf6cc8b8ac5ca8a57f996c56d`. With only copied `terminal64.exe` and `metatester64.exe` binaries in a newly initialized, network-denied, host-home-inaccessible Wine sandbox, the copied terminal began startup (build 6316), logged a newer MetaEditor request and failed MQL5.community authorization, then shut down. Wrapper status `69`; internal exit `0`; shutdown `10053` (cause unknown). Blank session did not remain stable; the bare tester executable was *not* invoked, per the gate. Wine init exit 0, external networking denied, original MT5 terminal PID 71219 and wineserver PID 35411 untouched. See `docs/milestones/030-stage1n-blank-terminal-repeat.md`.

## Immediate next bounded Codex task — Stage 1O read-only

1. Verify clean/synchronized branch and read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and Stage 1L/1M/1N reports.
2. Review existing non-sensitive Stage 1L and 1N terminal logs if retained, compiler-version evidence, local documentation and binary metadata **read-only**. Distinguish the actual cause of short-lived startup from guesses about headless mode, missing assets, community authorization and MetaEditor updates.
3. Determine whether a stand-alone MT5 strategy tester-agent startup is documented/supported without terminal orchestration, and whether a bare agent invocation can guarantee no backtest/history download/account access. If unknown, report it as unknown; do not execute to find out in this stage.
4. Examine whether an independent raw MT5 server time + OHLC discovery path is possible without an account-bearing original prefix, network or opaque history decoder. Distinguish verified mechanisms from conjecture.
5. Recommend one sharply bounded next experiment or a justified STOP/pivot. Avoid retrying the same empty terminal startup without a new falsifiable hypothesis and a way to observe it.
6. Report evidence, risks, blockers and a clear gate for separately authorized follow-up.

## Prohibitions

No Wine, MT5, MetaEditor or Strategy Tester launch; no copying native history/account/profile/state files, broker sessions, downloads/imports, historical replay, orders simulated or live, package installation, repository/strategy edits, original terminal alteration, new branches/force-push or local-control.

## Subsequent decision

Preserve frozen EURUSD 2026-09-10 M1/M5 research sample and canonical exporter hashes. Historical broker UTC offset, independent native bar data, tick identity and strategy/position execution parity remain unproven. A compile/test pass does not justify trading or performance tuning.
