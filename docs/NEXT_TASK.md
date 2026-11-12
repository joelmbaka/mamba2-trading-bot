# Next Authorized Task — M030 Stage 1H-I source validation and isolated compiler

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **INDEPENDENT CLOCK DISCOVERY SOURCE COMMITTED; VALIDATION PENDING**

## Stage 1H source scope

New `mql5/M030_ClockBarProbe.mq5` provides separate **no-order**, tester-only EURUSD native M1/M5 candle export with raw server timestamps and an explicit offset-free server-date envelope, mandatory run identity and bounded collision-resistant CSV output. It is not the production strategy and does not change existing `M030_DecisionProbe.mq5`, trading parameters or market data.

New `mamba2/backtest/m030_clock_discovery.py` compares hash-verified probe + canonical source M1/M5 CSVs, rejecting duplicate, missing, stale or unequal bars and accepting historical offset **only after a unique complete M1+M5 match** within the frozen window. `tests/test_m030_clock_discovery.py` covers synthetic success/fail cases.

Full description and unverified constraints: `docs/milestones/030-stage1h-clock-probe.md`.

## Next bounded Codex task

Under explicit instruction:
1. Verify clean synchronized `scalping-recovery`; read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and the Stage 1H milestone.
2. Run `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_clock_discovery.py tests/test_m030_parity.py tests/test_m030_incremental_contract.py -q`, relevant regression tests, and Python syntax checks. Report exact failure details; do not repair code locally.
3. Static-review new MQL5 discovery probe: no orders/account/broker operations, required explicit raw server-date inputs, fresh completed M1/M5 semantics, bounds, no-output overwrite and missing-history response.
4. Independently compile **`mql5/M030_ClockBarProbe.mq5`**, not the old decision probe, using a newly initialized disposable Wine prefix + separate copied MetaEditor app. First finish bounded `wineboot -u`, check safety restrictions (Z: and user-folder links removed) and protect original terminal/account/config/history. Report source/EX5 hashes, compiler diagnostics and exit code.
5. Inspect offline reference CSV format from the local canonical dataset; check whether time column is explicitly UTC ISO-compatible and whether any adapter would be needed. Do not modify/export data.
6. Note that native M1/M5 historical coverage and server-to-UTC mapping remain **unproven**; a successful compiler is not tester readiness or parity proof.

## No authority to run

No MT5 Strategy Tester or terminal launch, no broker login/session, downloads, imports, simulated/real trades, Python historical replay, installs, changes to production strategy, original MT5 environment modifications, new branches, reset/force-push, or local-control. A decision-free isolated tester probe requires separate authorization **after** data availability, clock envelope and OS-level network isolation are reviewed.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1g-provenance.md`
- `docs/milestones/030-stage1h-clock-probe.md`
