# M031 independent LEAN source contract

`M031FrozenData.cs` and `M031FrozenBaselineAlgorithm.cs` are a separate C# implementation of the frozen EURUSD comparison path. They do not import Mamba2 Python strategy, indicator, broker, or replay code.

The adapters read three local CSV sources directly:

- `EURUSD_M1.csv`: Bid M1 bars, Unix seconds interpreted as UTC bar-open time;
- `EURUSD_M1_ask.csv`: minute Ask sidecar, matched by M1 bar-open time;
- `EURUSD_M5.csv`: direct canonical M5 bars, never consolidated from M1.

The algorithm receives `m1_path`, `m1_ask_path`, `m5_path`, `sample_start`, and `sample_end` as LEAN parameters. Its data adapters set `EndTime` to bar-open plus one or five minutes, so a decision is processed only after the completed M1 bar is available and only completed M5 bars are eligible.

The independent calculations implement:

- first-source EMA7 recurrence;
- stochastic 21/7/7 with the production slowing-window arithmetic;
- M1 last-ten `%K` threshold checks without requiring a fresh crossover;
- canonical M5 ATR14 with the insufficient-history sentinel;
- the original M5 direction, M1 K/D and EMA/candle entry rules;
- one-symbol position/pending-order blocking;
- fill-time deferred SL/TP attachment;
- per-boundary indicator observations and `m030.events.v1` lifecycle records.

The intended separately authorized local invocation is conceptually:

```text
lean backtest M031FrozenBaselineAlgorithm \
  --m1_path=/sealed/EURUSD_M1.csv \
  --m1_ask_path=/sealed/EURUSD_M1_ask.csv \
  --m5_path=/sealed/EURUSD_M5.csv \
  --sample_start=2026-09-10T00:00:00Z \
  --sample_end=2026-09-11T00:00:00Z
```

This command was not executed. LEAN is not installed or provisioned locally. A runtime must enforce read-only source mounts, preserve the four Python evidence artifacts, and write independent outputs to a new destination. Hashes and per-boundary keys must be compared before any economic interpretation.
