# Next Authorized Task — M030 Stage 1E synthetic and isolated compilation validation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **INCREMENTAL OBSERVATION ENGINE SOURCE COMMITTED; TESTS/RECOMPILE REQUIRED**

## Current progress

Stage 1D passed 13 focused and 45 regression tests. Its no-order MQL5 EA compiled with 0 MetaEditor errors/warnings; Wine CLI exit code 1 remains a known caveat. Codex diagnosed prohibitive repeated full-prefix computations (~19 billion estimated inner-loop iterations for a one-day tester sample).

ChatGPT has implemented Stage 1E GitHub source changes detailed in `docs/milestones/030-stage1e-incremental-engine.md`: full historical prefix read once for first-source EMA7 seeding, newest 48 M1/M5 bar windows for 21/7/7 stochastic and M5 ATR14, newest completed bar reads thereafter, explicit no-gap and completed-bar assertions, optional one-time audit, and synthetic Python vector tests in `tests/test_m030_incremental_contract.py`.

**The Stage 1E revised EA has not yet been independently compiled or run.**

## Next bounded task for Codex, after explicit instruction

- Confirm branch `scalping-recovery` is clean and synchronized with origin. Fetch/pull safely without reset, rebase, stash or force-push.
- Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and Stage 1E milestone.
- Run `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py tests/test_m030_incremental_contract.py -q`, relevant regression tests and `py_compile`.
- Static review: no-order EA safety, M1/M5 latest-bar progression, EMA seed, stochastic lookback, ATR14 and `CopyRates` constraints.
- Compile only the revised EA using a **new disposable Wine prefix and copied MetaEditor application**, protected from original MT5 app/prefix and host-user mappings. Report compiler errors, warnings, build, original/copied source SHA-256, EX5 SHA-256, paths, exit status, and original running terminal unchanged.
- Do not modify source locally; submit defects to ChatGPT for Github source edits.

## Still prohibited

Do not launch MT5 Strategy Tester or historical Python backtest, place simulated or real orders, connect a broker, download or modify market data, install packages, optimize settings, change the production strategy, launch the original terminal, use local-control or local-control-results, or create new branches.

## Subsequent gate

Review code/test/compile results and whether the full native M1/M5 prefix can actually be supplied by MT5. Independently verify historical server-to-UTC mapping and data identity before any separately approved isolated *decision-only* tester launch. Compilation is not parity evidence.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1c-data-provenance.md`
- `docs/milestones/030-stage1d-validation.md`
- `docs/milestones/030-stage1e-incremental-engine.md`
