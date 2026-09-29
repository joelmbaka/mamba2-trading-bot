# Next Authorized Task

## M024 — implement metadata-only historical-holdout readiness

Branch:

`symbol-specialization-research`

Stage-2 acceptance documentation:

`ff9182cb835d8db022122dae3eed019c53faa924`

The historical-holdout checkpoint protocol is frozen in:

`docs/milestones/024-symbol-specialization-research.md`

## Exact authorized work

Implement a metadata-only readiness gate for the frozen M024 H-UJ holdout.

Holdout:

`2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`

Expected common trading dates:

**57**

Source manifest SHA-256:

`143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558`

Readiness must verify the exact source/coverage/partition/all-five-data/common
boundary semantics in the milestone protocol and deterministically publish:

- ordered 57-date list SHA-256;
- H1/H2/H3 19-date block SHA-256 values;
- replay-boundary SHA-256;
- source-manifest SHA-256;
- partition-spec SHA-256;
- required row-count metadata.

Add tests proving readiness performs no economic replay and that H-UJ economic
execution remains inaccessible until readiness is accepted.

A fixed local-control readiness action is allowed.

## Still forbidden

Do not compute or inspect holdout:

- P/L;
- trades;
- win rate;
- drawdown;
- fold/block economics;
- weekly economics;
- economic classification.

Do not use M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not add any candidate or filter.
Do not merge/deploy or enable real trading.
