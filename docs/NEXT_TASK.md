# Next Authorized Task

## M028 Stage 2 — freeze forward-paper implementation contract

Stage-1 accepted result:

`bf90b33409aa78d303d0928404e73f3d1a7da1bf`

Stage-1 classification:

**FORWARD_PAPER_ONLY**

Before any paper strategy outcome is observed, freeze the exact forward-paper
implementation contract.

The contract must preserve M027 rather than retune it:

- 12 completed calendar months for the time-series-momentum signal;
- monthly decision/rebalance cadence;
- 40% per-instrument ex-ante volatility target;
- EWMA decay 60/61 and annualization 261;
- equal weighting across mechanically eligible currencies;
- no side/session/weekday/lookback/threshold optimization;
- no performance-based currency pruning.

Execution universe may start only from the eight Stage-1 mechanically viable
currencies: AUD, CAD, CHF, EUR, GBP, JPY, NZD, SEK.

Stage 2 must prospectively define:

- how M027 public-data signals are translated into broker pair direction;
- exact monthly decision timestamp and first eligible forward-paper month;
- paper position sizing under observed 100:1 margin evidence;
- gross-leverage ceiling and handling of infeasible target weights;
- bid/ask paper-entry and paper-exit marking;
- prospective spread/slippage recording;
- treatment of broker swap versus M027 carry so carry is not double-counted;
- commission status and how unknown commission is reported;
- immutable paper ledger/report schema;
- minimum observation period before any performance conclusion.

Stage 2 is specification/implementation only until that contract is frozen.

Safety:

- paper/shadow accounting only;
- no live order placement or position modification;
- no retrospective net-cost economics;
- no M027 retuning or rerun;
- no M021 post-cutoff outcome use;
- no merge/deploy/live promotion.
