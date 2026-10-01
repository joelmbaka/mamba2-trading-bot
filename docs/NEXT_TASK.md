# Next Authorized Task

## M028 Stage 1 — execution evidence only

Stage-0 accepted result:

`3258372afbf11aa8178cddd54c61b810c5e514d6`

Stage-1 protocol freeze:

`13507ae2bb06af4daa24f4df70b97a11a8606fa9`

Run exactly one read-only Stage-1 evidence probe.

It must:

- start only from the frozen 22-symbol Stage-0 mapping;
- mechanically classify current quote viability using the frozen 300-second relative-freshness rule;
- query only the seven frozen one-hour tick-history checkpoints;
- report spread metadata only, never returns or P/L;
- calculate only read-only 1.00-lot BUY/SELL margin requirements;
- keep commission **UNPROVEN**;
- keep historical swap evidence **UNPROVEN** unless a true series exists;
- classify the path as `FORWARD_PAPER_NOT_READY`, `FORWARD_PAPER_ONLY`, or `RETROSPECTIVE_NET_EXECUTION_READY` under the frozen rules.

Safety:

- read-only market and margin metadata only;
- no order placement or order validation;
- no position changes;
- no trade-history reads;
- no strategy replay/economics;
- no M027 rerun;
- no M021 post-cutoff outcome use;
- no merge/deploy/live trading.
