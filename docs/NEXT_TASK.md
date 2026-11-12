# Next Authorized Task

## M029 Stage 1 — validate prospective safety machinery

Milestone branch: `prospective-paper-recovery`.

**Protocol frozen before implementation:**
`b84456f256cd701738b20ff30dc5be37f4f36dfb`
(`docs/milestones/029-prospective-paper-recovery.md`).

Stage-1 feature implementation:
`03f0e0dfd918ad7c4827253c864a373a671abe8c`
(`mamba2/backtest/m029_prospective.py`).

Synthetic tests:
`23234f97688d284476ccb4404cf1ce87407a60e1`
(`tests/test_m029_prospective.py`).

### Authorized immediate action

1. Verify the Dell checkout is clean and switch, without force, to the
   `prospective-paper-recovery` branch.
2. Run the full native test suite; inspect any failing tests and fix
   implementation/test defects without changing the frozen economic contract.
3. Record exact accepted feature SHA and test evidence.
4. Close only Stage 1 once tests pass and the result has been inspected.

### Permanently missed months

The October 2026 and November 2026 prospective windows passed without a
record. The 2026-11-12 workstation audit proved the configured October path
and directory absent. No historical paper decision may be backfilled.
The first eligible future window is:
**2026-12-07 12:00:00Z <= clock < 2026-12-07 12:10:00Z**.

### Not authorized in Stage 1

- No real-source signal or target-lot calculation.
- No real or paper position creation on broker.
- No live MT5 account read, order check, or order send.
- No M028 October first-decision action.
- No M027 retrospective economics rerun.
- No historical result retune or post-fact selection.
- No production merge/deploy.
- No M029 paper-decision record on the actual workstation.

The upcoming M029 Stage 2 must receive its own prospective implementation
authorization *after* Stage-1 regression is green. It will integrate
metadata-only readiness and broker/source adapters using the fixed Stage-1
calendar/journal invariants. The full M029 strategy remains unproven at
executable net-cost level.
