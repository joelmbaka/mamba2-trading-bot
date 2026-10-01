# Next Authorized Task

## M028 Stage 0 — read-only broker metadata probe

M028 protocol freeze:

`ed5effc7c3ac5df739fb80df7ed60b1a3409c8bd`

Run exactly one metadata-only probe against the currently authenticated MT5
terminal on the Dell research machine.

The probe must:

- use the frozen 25-currency M027 universe;
- map direct-USD symbols only from MT5 base/profit currency metadata;
- record current non-sensitive execution metadata;
- record account leverage/currency/margin mode without balance/equity/login;
- classify every currency as mapped, unavailable, or ambiguous;
- hash the accepted mapped universe;
- report commission as unproven unless directly exposed by allowed metadata;
- report no strategy economics.

Safety:

- no order APIs;
- no order/position changes;
- no trade-history inspection;
- no M027 economics;
- no M021 post-cutoff outcomes;
- no merge/deploy/live trading.

After the first accepted Stage-0 output, freeze the broker-availability result
before investigating commission, swap history/forward observation, historical
spread fidelity, or leverage implementation.
