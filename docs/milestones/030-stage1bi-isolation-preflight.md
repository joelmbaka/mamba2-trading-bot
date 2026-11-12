# M030 Stage 1B-I — Isolated MetaEditor preflight accepted

Date: 2026-11-12
Source branch/head inspected: `scalping-recovery` / `914a628bfa92aee46bcb79838ff5b5ce6d3df1f6`
Status: **READ-ONLY INSPECTION COMPLETE; COMPILATION NOT PERFORMED**

## Codex workstation evidence

- Clean local worktree; local and remote HEAD identical; ahead/behind 0/0; fetch successful.
- Wine 11.21 Staging binary: `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine`.
- Existing Wine prefix: `/home/joel/.local/share/mamba2-mt5-wine1121/prefix`.
- Existing application: `/home/joel/.local/share/mamba2-mt5-wine1121/app`.
- MetaEditor: `app/MetaEditor64.exe`; terminal: `app/terminal64.exe`; tester component: `app/metatester64.exe`. All are x64 PE32+.
- Existing terminal PID **71219** started with `/portable` in the original `app` directory. This binds active terminal data/history/settings to the original app directory; do not modify or terminate it.
- Original prefix contains terminal/common MetaQuotes state, possibly account/profile information. It is **not safe to clone** the original prefix.
- Original prefix exposes root through Wine `Z:` and links standard user folders to the host. Disposable prefix must not retain broad host mappings.
- Tester EA source: `mql5/M030_DecisionProbe.mq5`; inspected SHA-256 `16d5dd992d8183074d0c7795661e4891aca4ff52a103fa11ad8786929b886ba6`. No `#include` directives; installed include library has 237 .mqh files but direct includes not required.
- No processes launched, no files changed, no compiler invoked, no historical data/broker access, no test/backtest/order or local-control use.

## Next stage: 1B-II — disposable no-order compilation only

Scope for Codex after explicit instruction:

1. Confirm clean `scalping-recovery` checkout, precise HEAD and sample source SHA-256; stop on divergence or unexplained source drift.
2. Allocate a **new, exclusively owned temporary root** outside the repo, running original Wine prefix and original MT5 app. Make a new independent Wine prefix; do not copy the old one.
3. Restrict or remove Wine `Z:` root mapping and user-folder symlinks **inside disposable prefix only**; prevent writes to host originals and fail closed if isolation cannot be established. Check all realpaths of source/target/prefix/output; no symlinks into original `app`/`prefix`, repo or host homes.
4. Copy only the minimum MetaEditor binary/support files needed to compile, plus an exact byte copy of the no-order MQL5 EA, into separate disposable app/source locations. No `bases`, `config`, `logs`, `Profiles`, `Files`, terminal/common MetaQuotes directories, account data, or credentials.
5. Confirm disposable path safety and no references to the running terminal's application/data directories **before** launching anything. Abort if the compiler requires those paths or interactive account state.
6. Launch **MetaEditor compiler only** from disposable app + Wine prefix, with the copied EA as source, output and logs entirely inside the disposable tree. No terminal/Strategy Tester launch. Do not install packages, allow broker access or perform market-data downloads.
7. Report compiler command, environment/prefix paths (omit secrets), source/output SHA-256, compiler/terminal build evidence if available, exit status, errors/warnings, produced .ex5 location, permission/symlink checks, and original running terminal process unchanged. Do not silently repair the EA locally: send errors to ChatGPT for GitHub source fixes.
8. If copy, prefix, mapping or compiler containment is unsafe or impossible without changes to original MT5, **stop before invoking MetaEditor**, state blocker and preserve existing state.

## Explicit exclusions

The no-order diagnostic EA may **only be compiled**, never run in Strategy Tester during 1B-II. No Python historical replay, MT5 test trades, real/demo orders, broker initialization or login, new historical data, strategy tuning, original-app/profile mutation, restart/kill of PID 71219, use of `local-control`/`local-control-results`, or edits to repository files.

This gate is compilation feasibility, not parity, profitability or trading approval.
