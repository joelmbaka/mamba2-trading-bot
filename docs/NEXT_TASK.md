# Next Authorized Task — M030 Stage 1G offline provenance feasibility (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1F ACCEPTED; HISTORICAL CLOCK AND NATIVE MT5 CACHE CONTENT NOT PROVEN**

## Prior acceptance

Stage 1E: 39 focused and 45 regression Python tests passed; observation-only incremental EA compiled independently, 0 errors/warnings. Stage 1F read-only preflight verified clean synced source `71a47bdcd84d940ce9a86375611e84aa70dee3f4`, and existing tester build record `LastBuildTester=6316`. Repo EURUSD research CSVs and local MetaQuotes-Demo MT5 caches exist but exact native history coverage, OHLC matching, real-tick identity and historical server-to-UTC offset cannot be established from their file metadata. See `docs/milestones/030-stage1f-readiness.md`.

## Next bounded Codex task

Under a separately scoped instruction, read-only and offline:

1. Verify clean synced `scalping-recovery`; read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/milestones/030-stage1f-readiness.md`.
2. Find/inspect existing **repo exporter source**, export scripts/manifests and timestamp conversion code that generated `m022-history-inventory-tick-m1-v2`. Distinguish the Python MetaTrader5 copy_rates/copy_ticks UTC claims from the historical MT5 terminal's actual server candle clock.
3. Inspect existing **non-sensitive** MT5 historical terminal logs/config or metadata *read-only* for any direct, date-specific MetaQuotes-Demo server-time / UTC pairing; no account secrets may be printed. Do not infer offset from Kenya, filename stamps or apparent active broker hours.
4. Determine whether locally present cache binary formats can be **safely and independently decoded** by already present tools without launching Wine/terminal, installing libraries, writing artifacts or touching original cached files. Do not claim decoded bar/tick coverage based only on size/hash.
5. Return exact file evidence, timestamp pairs and provenance confidence; clearly distinguish proven results, tentative clues and blockers.
6. If no conclusive offline evidence, design an isolated, no-order, separately authorized *clock/bar discovery* protocol that can inspect native MT5 historical timestamps safely **without requiring the unverified offset as an input**; it must not enable order execution or mutate original data.

## Do not do

Do not launch Wine, MetaEditor, MT5 or Strategy Tester; create/copy files, decode via scripts that write to disk, connect broker, download market data, run Python historical replay, submit simulated/live orders, change source/strategy, install packages or use local-control. Never guess the offset or silently replace history with alternate dataset.

## Following decision

ChatGPT evaluates evidence and separately approves only necessary source-level diagnostic changes on GitHub before any isolated no-order data-discovery execution. Full strategy parity and optimization remain blocked.
