# M030 Stage 1E-II — successful isolated incremental EA compilation

Date: 2026-11-12
Status: **PYTHON VALIDATION AND MQL5 COMPILATION ACCEPTED; TESTER NOT YET AUTHORIZED**

## Repository and Python evidence

Codex inspected clean `scalping-recovery` at `d679139b8e7d4337997505a9ff446db538f6994a`, equal to origin (ahead/behind 0/0), with no source modifications. Prior Stage 1E Python validation: **39 focused tests passed**, **45 regressions passed**, Python syntax checks passed. Static review found only bounded 48-bar incremental signal computation and no broker/order/account/position calls.

## Independent compilation

Disposable root: `/tmp/mamba2-m030-stage1eii.g86cg7`
Prefix: `/tmp/mamba2-m030-stage1eii.g86cg7/wine-prefix`
Copied app: `wine-prefix/drive_c/M030MetaEditorApp`
Source and EX5: `MQL5/Experts/M030_DecisionProbe.mq5` / `MQL5/Experts/M030_DecisionProbe.ex5` under copied app.
Compiler log: `MQL5/Experts/M030_DecisionProbe.log` under copied app.

- Bounded initial `wineboot -u`: **exit 0**; completed prefix initialization before compiler launch.
- Prefix registry sizes: system.reg 3,687,852, user.reg 75,542, userdef.reg 4,026 bytes. No unfinished `wineboot`, `winedevice` or `rundll32` initialization before compilation.
- Independent prefix had host-root `Z:` mapping and broad user-folder symlinks removed; paths confined to disposable root. No original terminal app/prefix/repository references were found in disposable copied app.
- Wine: existing 11.21 Staging runtime; MetaEditor build `5.0.0.6316`.
- Compiler log: **0 errors, 0 warnings**; compile duration **771 ms**; produced EX5.
- MetaEditor CLI exit code **1**, same previously observed anomaly; evidence supports compiler success but anomaly remains documented.
- Original and copied source SHA-256: `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`.
- EX5 SHA-256: `ea46dcb09e4bbc77fdb6b764918ab38c2b269909ae4520459ea7261c131609b4`.
- MetaEditor SHA-256: `f9de90562ff98540278f16eb0d803a0392fd3be7a8fb6ad918817345507f2fc3`.
- Original running MT5 terminal PID `71219` remained unchanged. No terminal/tester, broker, replay, data download, package installation or order operation took place.

## Milestone acceptance and limits

**Stage 1E source validation and isolated compilation are accepted.** This is **not proof** that the EA can load all 2025-08 to 2026-09 historical bars, produce source-identical MT5 indicators, or match any Python decisions.

Remaining blockers:
1. The MQL5 probe requires independently verified historical server offset; Stage 1C could not establish that mapping. Do not invent an offset or rely on Kenya timezone.
2. MT5 terminal cache contents and first-bar M1/M5 origins are unverified; `CopyRates` might not supply the exact 389k M1 / 78k M5 prefix.
3. Native MT5 source OHLC, Ask/tick identity, signal eligibility and open-position blocking are unproven. No economic parity.
4. One-time full-prefix initialization and audit may be bounded algorithmically but have not been measured in tester runtime.
5. All tester input parameters must be explicit, immutable and matched to source identity. Under no circumstances infer an offset from an unrelated local clock.

## Next: Stage 1F read-only tester/data readiness plan

Before a first decision-only tester run, Codex may perform another **read-only** inspection of isolated sample history, tester configuration mechanics, EX5 compatibility and safe output destinations, and seek independent historical clock evidence. Report exact blockers and a proposed no-order, bounded tester setup; do not launch the tester or connect any broker. If the server offset or exact prefix remains unproven, retain a fail-closed gate and propose a provenance-preserving offline method instead of guessing.

A later isolated **decision-only** tester run must be separately authorized. Simulated orders and real/demo trading remain prohibited.
