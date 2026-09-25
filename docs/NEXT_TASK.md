# Next Authorized Task

## Phase A — repository operations foundation

Before the first long baseline:

1. establish the docs/agent handoff;
2. create Mamba2 `local-control` and `local-control-results` branches;
3. install the workstation local-control agent;
4. validate safe status/sync/branch-switch/test execution through the GitHub mailbox;
5. merge the docs foundation to `main`;
6. safely fast-forward `backtest-first-baseline` to the accepted main head.

Do **not** run the long baseline until Phase A is accepted.

## Phase B — first real five-symbol baseline

Then run the current strategy unchanged:

- From: `2026-09-01T00:00:00Z`
- To: `2026-09-25T00:00:00Z`
- Symbols: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY
- Timeframes: M1, M5, M15
- Ask: tick-derived M1 Ask
- Starting balance: 10,000
- Explicit commission assumption: 0
- Explicit slippage assumption: 0

Run twice and require byte-identical deterministic reports before interpreting performance.

No optimization or strategy parameter changes are authorized during this milestone.
