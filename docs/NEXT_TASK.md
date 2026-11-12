# Next Authorized Task — M030 Stage 1D synthetic and isolated compile validation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **SOURCE-ONLY ALIGNMENT UPDATE COMMITTED — VALIDATION PENDING**

## Changes awaiting independent Codex validation

See `docs/milestones/030-stage1d-alignment-contract.md`.

GitHub source now requires separate source-history starts for M1 (canonical 2025-08-25 00:03 UTC) and M5 (canonical 2025-08-25 00:00 UTC), a separately verified MT5 server-to-UTC offset (unknown), and strict completed-bar alignment. The independent tester-only MQL5 probe optionally exports timestamped native OHLC prefix records; Python has a strict per-timeframe audit comparator. Synthetic tests have been extended.

**This is not yet validated or compiled**. Prior EX5 from Stage 1B-II does not correspond to the revised source. MT5 historical cache coverage, time offset, tick provenance and large-history performance remain unresolved.

## Next bounded Codex task

Under explicit instruction: verify clean synced branch, run `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py -q` and relevant regressions, then **compile only** the revised no-order MQL5 probe in an independently disposable Wine prefix/application directory using the already accepted Stage 1B-II isolation safeguards. Report hashes, compiler errors/warnings, exact exit status, paths and original terminal unchanged. Read-only evaluate worst-case full-prefix performance/Memory cost without running a Strategy Tester or historical replay.

Do not install dependencies or modify repository source locally; source defects go back to ChatGPT for GitHub edits.

## Forbidden

No MT5 Strategy Tester launch, historical Python replay, simulated or live trade, broker connection/init, market data downloads, strategy optimization, local-control mailbox, modifying original Wine prefix/app, branch proliferation or rewriting Git history.

## Following gate

After compiler/test review: design bounded causal incremental indicator computation without altering full-source EMA seed, and independently verify server-to-UTC clock evidence before authorizing the first isolated decision-only tester session.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1a-parity-harness.md`
- `docs/milestones/030-stage1c-data-provenance.md`
- `docs/milestones/030-stage1d-alignment-contract.md`
