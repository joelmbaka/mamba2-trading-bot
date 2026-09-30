# Next Authorized Task

## M025 — recover Dell local-agent and finish LRV unit gate

Do **not** overwrite the active command:

`mamba2-m025-stage4-lrv-unit-probe-v2`

Active local-control command commit:

`b61a2b6caeac49dd200d067678a28a2ec718ca72`

The corrected probe action itself was repaired at:

`6aa1f79bb67274e9b6dafd6971df397fa809ff83`

Current feature branch:

`public-strategy-benchmarks`

Current accepted Stage-4 feature SHA:

`636478bf0ac6c55e138df418686b48492ee47486`

Already accepted:

- focused Stage-4 tests: **42 passed**
  (`d95bf9911368d11c79e0e247247bc991c49a06dd`);
- full native: **279 passed / 2 skipped**
  (`f77ba7f1e424058a52d3c6f139b86347b1714852`).

Latest economic attempt:

`d1703515dd09c7eff147aecac45772769f8d85a6`

stopped at:

`UNIT SCHEMA INELIGIBLE: LRV return unit is not explicit`

## Execute exactly

1. restore/restart the existing Dell
   `chatgpt-mamba2-local-agent.timer` /
   `chatgpt-mamba2-local-agent.service` if required;
2. let the already-queued v2 probe run;
3. inspect only LRV sheet labels/style/format metadata — no return values;
4. preserve the frozen Stage-4 unit rule;
5. if a parser-only repair is required, make it narrowly;
6. rerun `m025_stage4_tests`;
7. rerun `test_full_native`;
8. rerun deterministic `m025_stage4_economics` A/B exactly once;
9. durably document results and stop.

Do not infer LRV units from observed return magnitudes.
Do not change source, sheet, universe, scaling rule, sign, lag, lookback,
holding period, volatility target, estimator, or metrics.
Do not use M021/M023/M024 outcomes to tune M025.
Do not merge/deploy or enable real trading.
