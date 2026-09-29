# Next Authorized Task

## Milestone 024 — freeze historical-holdout checkpoint protocol

Branch:

`symbol-specialization-research`

Stage 2 is accepted.

Accepted Stage-2 feature SHA:

`fd9c0ec689c57c572a7318ddd54fecb8dc5e8666`

Accepted family result:

`45cc718b908a28040a1907c08c8dc7382d800883`

Accepted mechanical assessment:

`d99ca44882f9814d42ed5b71a86fd13150d41b8f`

Final full native acceptance:

`2a824763aab9e8b9be7eb5626cf657b857cae945`
— **288 passed, 2 skipped**.

Accepted candidate:

**C-UJ — USDJPY-only strategy, all-five market data retained**

Classification:

**SUPPORTED FOR HOLDOUT CHECKPOINT ONLY**

## Next step

Freeze a separate prospective historical-holdout checkpoint protocol **before
opening or computing any historical-holdout economics**.

The checkpoint protocol must predeclare at minimum:

1. exact fixed C-UJ strategy configuration;
2. exact historical holdout window:
   `2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`;
3. exact holdout data/date eligibility rules;
4. deterministic A/B replay requirements;
5. exact representation/readiness gates;
6. exact support/failure classification rules;
7. no post-result threshold changes;
8. stop rule after one holdout evaluation;
9. no M021 post-cutoff use;
10. no M025 outcome use;
11. no production/live promotion from the holdout without a separate gate.

Do not inspect/open the historical holdout before the protocol-freeze commit.

Do not tune symbols, sessions, weekdays, direction, parameters, M15, spread
filters, or position size.

Do not merge/deploy or enable real trading.
