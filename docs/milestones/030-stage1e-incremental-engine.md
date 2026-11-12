# M030 Stage 1E — incremental diagnostic engine source checkpoint

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **SOURCE IMPLEMENTATION COMMITTED; COMPILATION AND TESTS NOT YET RUN**

## Implementation

`mql5/M030_DecisionProbe.mq5` now:

- Loads each *complete* M1/M5 source-history prefix once at the first frozen evaluation boundary through the existing strict `GetBars()` first-source and completed-bar checks. Missing starts or unsupported MT5 `CopyRates` coverage fail closed; they are not silently replaced by a shorter prefix.
- Initializes EMA7 from the earliest M1 source-close (same `ewm(span=7, adjust=False)` seed as the original Python implementation); afterward updates once per completed M1 with alpha `2/(7+1)=0.25`.
- Keeps the latest 48 completed M1 and 48 completed M5 bars. A 48-bar tail covers the full 21-period stochastic extrema, 7 slowing bars, 7 signal smoothing bars, and the most recent ten K values; it also covers the last fifteen M5 bars needed for ATR14 true-range rolling mean. The full prefix is not re-evaluated every minute.
- Reads only the latest completed M1 bar per subsequent boundary, and the latest completed M5 bar only when its completion boundary advances. Requires a contiguous M1 clock increment, fresh exact source-open timestamps, and exactly one new M5 bar when its expected completed timestamp changes. Missing data stops the no-order EA without guessing.
- Preserves the original candidate signal rule: M5 K>D or K<D, a recent extreme in ten M1 K values, same-direction M1 K/D and candle relative to EMA7. Does **not** replace the recent-extreme condition with a crossover.
- Retains optional full-prefix OHLC audit at initialization only; never logs historical bar data repeatedly.
- Keeps explicit independent first M1/M5 timestamps, externally verified server-to-UTC offset, frozen EURUSD sample, non-overwriting output paths and tester-only guard. No order/trading/account code added.

`tests/test_m030_incremental_contract.py` adds a purely synthetic offline mathematical regression contract:
- Full-prefix vs last-48 stochastic K/D and last-ten-K extreme flags over varied window lengths.
- Incremental seeded EMA7 vs Pandas `ewm(adjust=False)`.
- Full-prefix vs last-15 ATR14 simple rolling true range.
- Evidence that a previous K/D fresh crossover is not required.

## Complexity and limitations

Steady state is bounded per M1 boundary: one newest M1 rate, one newest M5 rate only when due, ~48-bar stochastic recomputation for each timeframe, and one EMA recurrence. Historical full-prefix load/EMA initialization and optional OHLC audit remain potentially expensive **once**. The large first-prefix copy is still dependent on real MT5 history availability and `CopyRates`/Max-bars limits; a syntactically valid EA does **not** prove sufficient MT5 history.

Do not claim numerical parity from these source and Python tests alone. Need independent MetaEditor compile, source OHLC equality, offset provenance, and a later separately authorized decision-only tester exercise. No tester operation, broker connection, historical replay, simulated order or trading is authorized now.

## Next Codex Stage 1E validation — isolated compile only

Upon explicit instruction:

1. Verify a clean and synchronized `scalping-recovery`, inspect `AGENTS.md`, `docs/NEXT_TASK.md`, `docs/BACKTEST_SEMANTICS.md` and this checkpoint.
2. Run focused synthetic tests `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py tests/test_m030_incremental_contract.py -q`, relevant regressions and Python syntax checks; report exact counts and any failures.
3. Independently compile **this revised** MQL5 EA from an exact copied source in a fresh disposable Wine prefix + copied MetaEditor app under the accepted isolation protocol. Avoid original terminal app/prefix, account profiles, history and common files; no tester launch. Return source/output hashes, errors, warnings, process exit status, compiler build, paths, and evidence existing terminal unchanged.
4. Static review: `CopyRates` range/full-history availability, bar timestamp alignment, MetaEditor diagnostics, any long-term floating-point discrepancy or MQL5 compilation issue. Report blockers without modifying repo source.

No historical tests/backtests, market-data downloads, account access, installation, order operations, or local-control.
