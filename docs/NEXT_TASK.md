# Next Authorized Task

## M024 — execute metadata-only historical-holdout readiness

Branch:

`symbol-specialization-research`

Prospective holdout protocol freeze:

`b8f54de8f79f84c6f913515231e46453106a6cc7`

Readiness implementation:

`f7c0f432367bd7d0e667af08b55f041e13700730`

Fixed local-control support:

`276f2d6c414d2f0405be9d4ec45009f529f17931`

## Execute exactly

1. sync Dell to exact current remote feature HEAD and require clean 0/0;
2. run `m024_holdout_readiness_tests`;
3. require focused PASS;
4. run `m024_holdout_readiness`;
5. require deterministic A/B artifact equality;
6. require all readiness/safety checks;
7. durably freeze the published:
   - 57-date list SHA;
   - H1/H2/H3 19-date SHAs;
   - replay-boundary SHA;
   - partition-spec SHA;
   - readiness artifact SHA;
8. stop before holdout economics until those hashes are documented.

Still forbidden:

- holdout P/L/trades/win rate/drawdown;
- holdout block/week economics;
- alternate candidates;
- M021 post-cutoff outcomes;
- M025 outcomes;
- merge/deploy/live trading.
