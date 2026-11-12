# Next Authorized Task — M030 Stage 1B-I isolated compilation preflight

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **PYTHON VALIDATION PASSED; MQL5 COMPILATION BLOCKED; ISOLATION PREFLIGHT ONLY**

## Evidence

Codex validated source commit `07487976dd76cb03fd5022503810d2d85800a4f1` with a clean synchronized working tree. Focused M030 Python tests: **10 passed** using `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py -q`. Relevant regression tests: **45 passed**. Python `py_compile` passed. The standalone MQL5 decision probe was statically inspected and found to contain no trade/order/broker initialization calls. MetaEditor compilation was not attempted because the existing MT5 terminal was running from the same Wine environment. See `docs/milestones/030-stage1b-validation.md`.

## Current objective

Plan a **separately isolated MetaEditor compilation context**, without changing running MT5 state. Codex may inspect read-only paths, process/environment identity, symlinks, destination separation, and required compilation inputs, then report an exact safe isolation plan.

The executable tools are present at:
- `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine`
- `/home/joel/.local/share/mamba2-mt5-wine1121/app/MetaEditor64.exe`
- `/home/joel/.local/share/mamba2-mt5-wine1121/app/terminal64.exe`
- `/home/joel/.local/share/mamba2-mt5-wine1121/app/metatester64.exe`

An isolated Wine prefix **alone is not sufficient** if compiler/application/common-data paths still overlap the original MT5 installation. The design must isolate compiler input/output files, Wine prefix, platform data folders and terminal common files, and avoid copying private credentials/accounts. Do not launch MetaEditor or compile in the original environment.

## Allowed now

- ChatGPT: inspect GitHub source and documentation, document source-level defects, and prepare GitHub-only safe fixes without changing trading semantics.
- Codex upon explicit scope: **read-only** workstation isolation feasibility and exact-path inventory. No executable compilation, installation, file copying or terminal GUI interactions are authorized by this document.

## Gate following preflight

After an isolation plan is reviewed, a separately scoped Codex step can be authorized to prepare a disposable environment, compile the tester-only no-order EA and report build/error evidence. Only after that may data provenance, independent decision comparison and a later Strategy Tester execution be considered.

## Prohibited

No Python historical replay, MT5 Strategy Tester run, broker initialization/login, live or demo trading, simulated orders, market-data download, package installation, strategy optimization, resuming monthly paper schedules, use of `local-control` or `local-control-results`, force-push, reset/rebase/stash, or feature-branch proliferation.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/WORKFLOW.md`
- `docs/milestones/030-scalping-parity-audit.md`
- `docs/milestones/030-stage1a-parity-harness.md`
- `docs/milestones/030-stage1a-source-checkpoint.md`
- `docs/milestones/030-stage1b-validation.md`
