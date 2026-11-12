# M031 — independent LEAN **candidate-signal** comparator

**Status: source corrections committed, not compiled or executed in LEAN.**

This C# code is intentionally a *different implementation* of the frozen
Python M031 indicator and raw-entry-condition calculations. It does not import
the Python strategy, broker or indicators. The first independent verification
gate is **1,440 complete-bar indicator observations and raw candidate
BUY/SELL/NONE decisions**, not simulated trading. The sealed Python baseline
reported 59 raw BUY/SELL candidate observations, 397 blocked observations and
16 actual strategy SIGNAL/SUBMIT/FILL/EXIT events. Those are distinct concepts.

## Fixed comparison inputs

Original files, mounted read-only:

- `EURUSD_M1.csv` — canonical Bid M1 (Unix-second UTC *bar opens*)
- `EURUSD_M1_ask.csv` — tick-aggregated minute Ask, required as a separate
  canonical source even though candidate-indicator matching does not use Ask prices
- `EURUSD_M5.csv` — **direct** canonical M5; never resample M1 for the M5
  stochastic/ATR inputs

The algorithm validates hard-coded SHA-256 hashes for the **manifest and all three CSVs** **before** subscribing. It also checks the complete available warm-up count at the first comparison boundary: 389,448 M1 and Ask rows (including the first sample bar) and 77,868 completed M5 bars.
The custom-data reader consumes each sealed multi-month CSV as a continuous
LocalFile stream; it must **not** discard rows merely because the engine's
request date changes. The algorithm checks strict source monotonicity and
exact seeded counts. The original source is never modified.

Historical source data begins in August 2025; the **complete** original source
prefix is required, particularly because EMA7 is first-source seeded. The
first compared source M1 bar opens at `2026-09-10T00:00Z` and becomes eligible
at **`00:01Z`**. The last source bar opens `23:59Z` and becomes eligible
at `2026-09-11T00:00Z`. The comparator fails closed unless exactly
**1,440** M1 observations, **1,440** corresponding Ask minute rows and **288**
canonical M5 sample rows were received, in order.

On the full prefix, M1-derived M5 differs from canonical M5 (three OHLC
mismatches among comparable bars, 83 additional derived-only buckets and
151 incomplete/missing M1 groups). Volume and spread also differ. The
independent engine must not silently consolidate M5.

## What this code does

- Uses LEAN custom data callbacks as the independent clock, with UTC source
  bar-open time and explicit bar completion.
- Independently calculates incremental Stochastic 21/7/7 on canonical M1/M5,
  EMA7 first-source recurrence, ATR14 simple rolling prior-close TR and
  the **last-ten** M1 %K extreme condition without any fresh-crossover test.
- Emits observation-only `indicator_trace.jsonl` with
  `candidate_signal`, indicator values, reason code, UTC decision boundary,
  M1 source bar open and latest completed M5 source bar open.
- Emits `events.jsonl` containing **M1_CLOSE only**. No `SIGNAL` events
  are emitted since there is no independently verified order/position model.
  Python's blocked-candidate suppression and 16 actual SIGNAL events are
  **not yet comparable** to this phase's records.
- Refuses existing Object Store output keys under a required unique run prefix.
  `input_manifest.json` and `summary.json` state
  `independent_candidate_signal_parity_only` explicitly.

The code **does not call MarketOrder, StopMarketOrder, LimitOrder, or any
LEAN broker/portfolio trading API**. This avoids the previous incorrect
unregistered Forex symbol, 0.1-lots-versus-unit ambiguity and native-LEAN
intrabar fill-model mismatch. No genuine execution or P/L parity is claimed.

## Remaining validation and runtime risks

1. **No C# compilation has been performed.** A pinned LEAN / .NET API check
   is required; keyword-only Python tests cannot replace compilation.
2. The same LocalFile source is supplied across dates. LEAN's behavior when
   the custom-data reader advances the data clock across a multi-month file
   must be verified at runtime. If a pinned version cannot retain a continuous
   stream, design deterministic scratch-file daily shards rather than silently
   date-filtering or dropping original history.
3. LEAN custom-data callbacks may have date-boundary, market-hours or
   time-zone behavior that needs measured verification. A source M5 bar must
   not enter the M1 candidate calculation before its EndTime. Fail-closed
   1,440/288/1,440 and timestamp checks must pass.
4. LEAN's `ObjectStore` namespace and CSV local-file paths must work in
   the pinned container. The source mounts must remain read-only.
5. Candidate agreement should be checked on **each eligible UTC boundary**
   by source-open keys, exact direction/reason, and indicator absolute
   tolerance initially 1e-9. Decimal arithmetic is not proof of double/
   NumPy bitwise identity. Investigate any mismatch, do not relabel it.
6. The next **trade** parity phase requires a separately reviewed
   independently implemented pending/fill, stop-first, bid/ask, ATR trailing
   and exit ledger with exact 0.1 **lot** semantics. Native LEAN order
   callbacks on a different security/feed do not automatically qualify.

## Required LEAN parameters

`manifest_path`, `m1_path`, `m1_ask_path`, `m5_path`,
`sample_start=2026-09-10T00:00:00Z`,
`sample_end=2026-09-11T00:00:00Z`, and a *unique*
`output_prefix=m031/<run-id>`.

**Do not use the previously suggested bare `lean backtest ... --m1_path`
example as an executable command.** LEAN CLI normally requires a correctly
provisioned project and configuration; the supported command syntax, engine
version and file mount settings must be established in a separate approved
runtime provisioning task.

## Next steps

Codex may execute the existing lightweight Python contract/unit/regression
tests, Python syntax and git integrity checks. **Source edits remain with
ChatGPT/GitHub**; Codex should report failures and may only edit in response
to an actual execution/compilation error, preserving evidence and never
changing production Mamba2 strategy logic.

After a separately approved pinned LEAN runtime provision, compile C# first,
then run exactly one observation-only frozen-day comparison. Do not execute
MT5/Wine, historical Python replay, mass backtests, tuning, broker
connections, Docker pulls or cloud uploads without their own approval.
