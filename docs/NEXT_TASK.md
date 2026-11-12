# Next Authorized Task — M030 Stage 1I offline isolated history feasibility (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1H-II VERIFIED; ISOLATED NATIVE MT5 HISTORY ACCESS STILL BLOCKED**

## Accepted evidence

Codex validated source `c0a7d2259a5e10a3518603ee119d244577466f9b`, clean/synchronized (0/0). Focused M030 tests **49 passed**, relevant regression tests **59 passed**, syntax passed. Canonical EURUSD M1/M5 CSV files have integer epoch-second `time`, read successfully and explicitly as `unix_seconds_utc` without mutation. Known file hashes remain unchanged. Frozen Sep 10 2026 UTC: M1 1,440 rows and M5 288 rows. Complete results: `docs/milestones/030-stage1hii-validation.md`.

Standalone independent no-order `M030_ClockBarProbe.mq5` unchanged, SHA-256 `9b6b4782402c0eea268ccea8325ca81bf03b0e265054d58904c598137834a2fe`; prior isolated compile completed with 0 errors/warnings (EX5 SHA-256 `59cf2288212bc8d215b32f23a7bda89c9faf25dbcd486706999ad5251c5f2496`). No tester operation yet.

## Next bounded Codex task

After separately scoped instruction, perform **read-only offline** feasibility inventory:
1. Verify clean synced `scalping-recovery`, read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, Stage 1H-II and this file.
2. Inspect existing MT5 program/Tester directories and market-data-only history/tick caches (types, timestamps, relationships and path conventions), without copying or decoding undocumented formats as if reliable.
3. Identify whether a fresh offline isolated terminal/tester can consume *market-data-only* cache copies without account credentials, profiles, broker login, synchronization or downloading history. Seek documentation/source-grounded support; **do not assume this works**.
4. Check what an explicit independent offline network-isolation setup would require (e.g., sandbox/container namespace) and whether existing workstation permissions/tools allow it *without executing or creating anything*. Network blocking must be externally enforceable and verifiable; no new software installs.
5. Identify any private/sensitive files that must not be copied. Original app/prefix and PID 71219 remain untouched.
6. Report exact evidence, unknowns, verified-versus-hypothesized feasibility, disk/permission needs and a staged fail-closed proposal. Stop on any operation requiring terminal launch, data copy, original state modification or network connection.

## Still prohibited

No Wine/MetaEditor/MT5/Strategy Tester launch; no native cache or history copies/imports; no broker login/network; no data download; no Python historical economic backtest; no simulated/real orders; no installs, repo changes, original state changes, optimization, force-push/new branches or local-control.

## Subsequent decision

Only after feasibility evidence is reviewed may a **separately authorized** offline isolated no-order tester bar/clock discovery be considered. If tester cannot access native history with offline isolation and no account state, declare a blocker. No server offset or OHLC parity is established yet.
