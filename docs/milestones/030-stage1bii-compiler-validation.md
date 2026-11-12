# M030 Stage 1B-II — isolated MQL5 compiler evidence

Date: 2026-11-12
Status: **COMPILATION ACCEPTED FROM CODEX REPORT; NO TESTER EXECUTION**

## Source identity and repository

- Branch `scalping-recovery`; local HEAD and origin `4130dbc487c642f1042c8df9f200aabeb42d5b34`, 0/0, clean.
- Probe: `mql5/M030_DecisionProbe.mq5`.
- Original and copied source SHA-256: `16d5dd992d8183074d0c7795661e4891aca4ff52a103fa11ad8786929b886ba6`.
- Compiled EX5 SHA-256: `392a6cb6f71893a5cb24a2da0a730120da98d18baadfebbf44030fb74522308c`.

## Environment and isolation

Disposable root: `/tmp/mamba2-m030-stage1bii.4hCdMM`.

- Prefix: `wine-prefix/` inside that root.
- Copied application: `wine-prefix/drive_c/M030MetaEditorApp/`.
- Source: `MQL5/Experts/M030_DecisionProbe.mq5` below the copied application.
- EX5 and compiler log: same copied `MQL5/Experts/` directory.
- Wine executable (read-only shared runtime binary): `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine`.
- Disposable `Z:` drive mapping and user-folder links removed, C: restricted to disposable prefix; empty disposable common directory. No original terminal, tester, history, `bases`, `config`, profiles, account files or common files copied. Running original terminal PID `71219` unchanged.

## Compiler result and interpretation

MetaEditor embedded build: **5.0.0.6316**.

Compiler log: **0 errors, 0 warnings**; compilation time **531 ms**; EX5 output present, hash reported above.

The process returned **exit status 1**, despite the successful compiler log. Treat the artifact as *compiled*, but preserve the nonzero-status anomaly for independent future verification. Never claim MT5 tester compatibility, execution readiness, or actual terminal build identity from the embedded MetaEditor version alone.

Compilation command from Codex report:

```sh
env WINEPREFIX=/tmp/mamba2-m030-stage1bii.4hCdMM/wine-prefix \
WINEARCH=win64 WINEDEBUG=-all \
timeout --foreground --kill-after=5s 90s \
/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine \
/tmp/mamba2-m030-stage1bii.4hCdMM/wine-prefix/drive_c/M030MetaEditorApp/MetaEditor64.exe \
/portable \
/compile:'C:\M030MetaEditorApp\MQL5\Experts\M030_DecisionProbe.mq5' \
/log
```

## What was NOT established

No MT5 terminal or Strategy Tester launched, broker accessed, data downloaded, historical Python replay run, real/demo order placed, simulated order generated or local-control used. Exact MT5 tick history, server-to-UTC offset, M1/M5 bar identity, deterministic EMA warm-up, no-position-block decision equality and end-to-end Python/MT5 execution parity remain unverified.

## Next gate: Stage 1C — no-trade data provenance and clock alignment

Before running any EA, inspect and document exact historical data provenance, earliest warm-up rows and retained time spans. A read-only offline file inspection and hashes may be performed by Codex only with an explicitly scoped instruction. Decode existing caches if possible without launching MT5, copying sensitive files, network/broker access or modifying the original environment. Compare broker/server time evidence where safely present; do not guess the UTC offset. Report uncertainties as blockers. No backtest, tester GUI launch, order operation or parameter optimization is authorized at this gate.
