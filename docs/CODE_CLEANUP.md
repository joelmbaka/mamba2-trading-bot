# Code Cleanup Audit

Date: 2026-09-25

This audit was performed before the first long historical baseline so dead scaffolding and generated artifacts do not obscure the production/backtest surface.

## Removed now

### Generated artifacts accidentally tracked

- `backtest/market_metrics.csv`
- `logs/mamba2.log`

The root `backtest/` and `logs/` directories are runtime output, not source. They are now ignored.

### Empty placeholders

- `mamba2/indicators/detect_divergences.py`
- `mamba2/strategy/mq5_version.mq5`

Both were empty and unreferenced.

### Unused diagnostics/scaffolding

- `mamba2/crew/test_mt5_columns.py`
- `mamba2/indicators/MACD.py`
- `mamba2/indicators/support_resistance.py`
- `mamba2/trader/client.py`
- `tests/test_trader.py`
- entire `examples/` directory
- `mamba2/broker/README.md`

Evidence:

- `get_macd` had no caller outside its own module.
- `draw_support_resistance` had no caller outside its own module.
- `TraderClient` was used only by its own scaffold test and `examples/simple_strategy.py`.
- the MT5-column diagnostic had no repository caller.
- examples were not part of the production/backtest path; one required undeclared `yfinance`, and the MT5 demo printed account metadata contrary to the current security contract.
- the broker-local README duplicated the root documentation, referenced a nonexistent test path, and contained account-info-printing examples that conflict with the current security contract.

### Dead private code

Removed unused `StochasticTripleTFStrategy._registered_lower_lows`; it had no caller.

### Stale dependency

Removed direct SciPy dependency from `pyproject.toml` and `uv.lock`.

Production trend detection already uses NumPy OLS and contains no SciPy import.

## Intentionally kept

These are not currently production entry dependencies, but they are tested or support active runtime analytics, so they are not deleted in this cleanup:

- `mamba2/indicators/trend_line.py`
- `tests/test_trend_line.py`
- `mamba2/crew/plotter.py`
- `mamba2/crew/market_analyst.py`
- matplotlib / mplfinance dependencies

The live strategy still has an analytics/reporting path using plotter/market analyst, while trend-line remains a tested public indicator utility. Removing either would be a separate API/product decision.

## Follow-up candidates, not deleted yet

- `pydantic` appears to have no current source import.
- `pytest-asyncio` is installed as a base dependency rather than dev-only.
- `main.py` appears to schedule `update_pl_periodically` both in `main()` and again in `Bot.run()`; this is behavioral cleanup, not dead-code deletion, so it must be handled separately with tests.
- additional unused imports/comments can be cleaned only after static validation.

Do not mix these follow-ups into the first real baseline unless they are separately reviewed and accepted.
