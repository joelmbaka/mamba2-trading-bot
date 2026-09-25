# Mamba2

Mamba2 is the production strategy and deterministic historical replay project for the current five-symbol forex system.

## Start here

Agents and developers should read:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`

Those files are the authoritative project handoff.

## Current production symbols

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

## Runtime model

Native Linux is used for deterministic backtest/replay work.

Validated Windows/Wine bridge:

- Python 3.10.11 x64
- NumPy 2.2.1
- MetaTrader5 5.0.6180

See `constraints/wine-runtime.txt`.

## Historical backtesting

Core replay lives under `mamba2/backtest/`.

Generated datasets belong under ignored `backtest_data/`.

Generated strategy analytics/plots belong under ignored root `backtest/`.

Do not add generated results to source control.

## MT5 safety

Credentials are supplied only through ignored/local environment configuration.

Backtest and historical-export work must not place, modify, or close real orders.

Do not print or persist MT5 account identifiers or holder metadata.

## Tests

Default tests exclude explicit MT5 integration:

```bash
python -m pytest
```

The real MT5 integration marker must never be enabled casually.

## Project plan

See `docs/PROJECT_PLAN.md` and `docs/MILESTONES.md`.
