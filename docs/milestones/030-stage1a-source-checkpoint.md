# M030 Stage 1A — source checkpoint and validation handoff

Date: 2026-11-12. Active branch: `scalping-recovery`.

## Implemented (not yet executed or compiled)

- `mamba2/backtest/m030_parity.py`: versioned JSONL schema, opt-in in-memory `EventSink`, exclusive file save, offline read-only first-divergence comparison CLI. Run ID and market metadata are to be included in caller-managed run manifest before cross-engine comparison.
- `mamba2/backtest/runner.py`: opt-in `event_sink=` (default `None`) for single-symbol and portfolio runners; emits causal `M1_CLOSE` events. The default code path does not emit records.
- `mql5/M030_DecisionProbe.mq5`: test-context-only, EURUSD-only, M1 bar-boundary indicator/decision CSV probe; no `OrderSend`, `CTrade`, SL/TP modification or order execution code. Independent stochastic 21/7/7, EMA7 and simple 14-bar M5 TR mean.
- `tests/test_m030_parity.py`: synthetic timestamp, diff, price, event-schema and immutable-output checks.

**These are initial Stage 1A foundations, not completion or parity evidence.**
The Python M1 boundary event stream and MT5 indicator/decision CSV are **not the same schema yet**. Neither is an end-to-end comparable decision+execution ledger; execution parity remains unimplemented. Do not run MT5 Strategy Tester yet.

## Important correctness risks to resolve in the next source iteration

1. **EMA warm-up**: MQL5 obtains up to 512 completed bars and seeds EMA from the first of them; Python `ewm(adjust=False)` seeds from the first available source bar, potentially thousands of earlier candles. Freeze and align exact warm-up source start for both engines; never invent an arbitrary tolerance.
2. **MQL5 CopyRates alignment**: verify bar ordering, 1-shift completed-bar semantics, and equality to Python UTC open identifiers; actual first tick can occur after wall-clock minute start. MetaTrader timestamps are server-local, not proven UTC; record a verified offset before comparison.
3. **No signal while a position is open**: initial MQL5 decision-only EA does not model the Python runner's blocked-symbol gate, so its candidate signals must not be mistaken for accepted submissions. Add explicit state/reason mapping before reconciliation.
4. **Output conversion**: Python event JSONL and MQL5 CSV fields must be normalized with distinct data provenance, manifest IDs and source hashes. Do not pair rows by index if an engine has extra/missing events; align on exact completed-bar IDs before execution comparisons.
5. **Strategy details**: optional trend/RSI/M15 filters must be confirmed disabled. BUY and SELL branches of original strategy should be compared with actual Python evaluation, including branch-specific early returns.
6. **Price provenance**: repository M1/M5 bar completeness does not prove MT5 tick coverage. Cached terminal data may use other server history. The MetaQuotes-Demo source does not prove source-level parity.
7. **MQL5 indicator arithmetic**: the probe duplicates arithmetic independently but has not been compiled. Its output must be inspected against causal Python prefix vectors with identical initialization and bars before relying on any signal claim.
8. **Data output**: MQL5 FileOpen with FILE_COMMON writes outside repo to common terminal files. Ensure no existing diagnostic file is overwritten; unique names per run and hashes required before a tester launch.
9. **Scope**: no Python order/fill/protection/exit tracing, live MT5 integrations, accounting reconciliation or test-order EA exists yet; these remain Stage 1A deliverables requiring further implementation and review.

## Next bounded Codex task — source-only validation (requires explicit authorization)

After ChatGPT completes remaining source implementation, Codex may be instructed to:
1. Read `AGENTS.md`, `docs/NEXT_TASK.md`, `docs/BACKTEST_SEMANTICS.md`, this file and the active Stage 1A scope.
2. Check active branch, clean worktree and exact origin sync. Fetch changes without reset/rebase/stash.
3. Run focused synthetic `pytest tests/test_m030_parity.py -q` and repository regression tests only after explicitly authorized.
4. Confirm MetaEditor compilation is available **without connecting to any account**. Compile the observation-only EA when separately authorized, record compiler build and warnings.
5. Verify Strategy Tester can run in a fully isolated context without broker login or any EA order calls, and report blockers **without launching tests or downloading data** until a later authorization.

No historical Python backtest, simulated EA order, broker access, GUI Strategy Tester session, installs, strategy optimization or live trading is authorized by this handoff.

## First sample, frozen

EURUSD, `[2026-09-10T00:00:00Z,2026-09-11T00:00:00Z)`, with earlier data warm-up. Repository preflight reported M1 1,440, M5 288 and at least 24h historical warm-up. MT5 historical tick coverage still unknown. Stage 2 execution must not start without sample provenance and separate authorization.


## 2026-11-12 additional source work (unexecuted)

Additional opt-in source implementation:
- `mamba2/backtest/broker.py` now accepts `event_sink` and records SUBMIT/FILL/SLTP_MODIFY/EXIT at causal replay boundaries; it does not change uninstrumented defaults. Those are Python offline-broker observations, not MT5 tick-accurate events.
- Replay runner binds an explicitly supplied single sink to the broker and emits candidate SIGNAL events before calling the unblocked strategy.
- `mamba2/backtest/m030_signal_observer.py` reproduces baseline candidate decisions using the original Python indicator functions. It fails closed if optional trend/RSI/higher-TF filters are switched on. A candidate decision is not an accepted order and should only be reconciled with similarly *unblocked* MT5 decisions.
- `mamba2/backtest/m030_mt5_import.py` converts independent MQL5 decision CSV into the common SIGNAL event schema using a separately verified server-to-UTC offset. No assumed timezone or data provenance. Synthetic conversion tests have been added.
- `mql5/M030_DecisionProbe.mq5` now requires an explicit first-source-history timestamp for EMA seeding, rejects pre-existing output files and limits emitted decisions to the frozen sample. The precise Python and MT5 initial bar history, source timestamps and correct tester GUI behavior are still unverified.
- Comparator now includes both M1 and M5 source-open IDs and a frozen-UTC-window selection helper.

### Critical gates still unresolved

**Do not interpret these commits as Stage 1A completion.** Nothing has been compiled, tested or run. Two independent engines still need comparison against exact identical bar arrays (including the first bar used for EMA), verified conversion of server timestamps, handling of open-position blocking in MQL5, and explicit no-trade/warm-up alignment. MT5 currently emits decision candidates only: there is no test-order transaction implementation, so full fill/protection/exits/accounting parity cannot yet be asserted. Python emitted order IDs are offline-only and may never equal MT5 tickets. Record correspondences rather than comparing their numeric identities.

The opt-in signal observer currently emits no signal for blocked symbols (whereas standalone MT5 probe still evaluates every eligible boundary); compare **matching eligible boundaries only** until a matched position-state filter is implemented. The MQL5 output is server-time CSV and is not a directly comparable full-event ledger until imported and filtered. Output collision checks are not an atomic file lock; use unique RunId and OutputName, isolated tester context, and an immutable evidence manifest.

**Next decision gate**: Codex may run synthetic Python unit tests and compile the standalone tester-only EA only after a separately scoped local execution instruction. Do not launch any historical tester/backtest or connect to broker automatically. Fix all discovered compiler/tests defects on GitHub before considering an instrumented MT5 simulated-order EA.
