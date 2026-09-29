# Next Authorized Task

## Milestone 024 — diagnostic symbol specialization

Branch:

`symbol-specialization-research`

Protocol:

`docs/milestones/024-symbol-specialization-research.md`

Protocol is frozen before M024 diagnostic output.

Implement only the deterministic read-only diagnostic analyzer and tests for
the exact frozen subsets:

- SYM-R — all five;
- SYM-UJ — USDJPY;
- SYM-JPY — EURJPY + GBPJPY + USDJPY;
- SYM-NONJPY — EURUSD + GBPUSD.

Use only accepted M023 Stage-A D-B / BUY-only all-hours evidence over the same
225 seen-research dates.

Do not run fresh strategy economics.
Do not inspect historical holdout.
Do not inspect M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not add symbol subsets, sessions, weekdays, SELL/BOTH, or M15.
Do not modify production defaults.
Do not merge/deploy or enable real trading.

The diagnostic artifact must be deterministic, source-hash anchored, and
clearly labelled DESCRIPTIVE SUBSET ATTRIBUTION rather than causal
symbol-filtered economics.
