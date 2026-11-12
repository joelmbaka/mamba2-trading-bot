# M030 Stage 1E — Python validation accepted; Wine/MetaEditor timeout

Date: 2026-11-12
Branch: `scalping-recovery`
Validated HEAD: `13f8aa22446e4ce4fe6a6cf99affaf300db99812` (clean and synchronized, 0 ahead/behind).

## Accepted evidence

- Focused synthetic Python tests: **39 passed**.
- Relevant regression tests: **45 passed**.
- Python syntax checks: passed for M030, runner, broker and test modules.
- Static inspection: rolling M1/M5 windows bounded to 48 bars; full-history initial EMA7 seed, 21/7/7 stochastic and intended ATR14 rolling calculation; completed-bar and gap checks; no account, broker, trade/order/position execution calls.
- Original running MT5 terminal remained untouched; no Strategy Tester, data download, broker connection, Python historical replay, trade, installation or local-control operation.
- Repository files unchanged by Codex.

## Failed / blocked isolated compilation

Disposable prefix: `/tmp/mamba2-m030-stage1e.YZFkBB/wine-prefix`.
Copied MetaEditor: `/tmp/mamba2-m030-stage1e.YZFkBB/wine-prefix/drive_c/M030MetaEditorApp/MetaEditor64.exe`.
Wine runtime: `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine`.
MetaEditor build evidence: `5.0.0.6316`.

Source and copied source SHA-256: `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`.
MetaEditor binary SHA-256: `f9de90562ff98540278f16eb0d803a0392fd3be7a8fb6ad918817345507f2fc3`.

The command returned **status 124 (timeout)**. Compiler log empty; **no EX5 output**. No compiler warnings or errors were emitted before timeout; this does *not* mean 0 errors or successful compilation. MetaEditor appears to have stalled during startup in the disposable Wine prefix. No source-level compiler conclusion is possible.

## Next gate — M030 Stage 1E-I read-only environment diagnostics

Do **not** immediately rerun MetaEditor in the original prefix or change trading source. First inspect read-only whether the failed disposable process was completely terminated, what the timeout captured, available Wine/MetaEditor logs, process ancestry, installed runtime dependencies, DLL paths, wineboot readiness and potential GUI/display/locking issues. Compare against successfully compiled disposable setups from Stage 1B-II / 1D using available evidence. Check original MT5 terminal PID and app/prefix still untouched.

Return a bounded diagnosis with evidence and a suggested safe next compilation attempt. Do not install packages, initialize Wine or MetaEditor, alter any prefix, copy credentials, restart the original terminal, run Strategy Tester, connect a broker or use local-control during the diagnostic preflight.

An independently authorized second step may retry the compiler in a freshly isolated environment with narrowly adjusted startup flags/timeouts, but no test or historical replay until a new EX5 has been produced and reviewed.

## Other remaining gates

Historical server-to-UTC mapping, exact native M1/M5 identity, full-prefix CopyRates availability, tester-only indicator equality and decision lifecycle parity remain unproven. The successful Python tests are not profitability or MT5 parity evidence.
