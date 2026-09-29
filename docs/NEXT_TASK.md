# Next Authorized Task

## M024 — execute the one-shot H-UJ historical holdout

Branch:

`symbol-specialization-research`

Prospective holdout protocol:

`b8f54de8f79f84c6f913515231e46453106a6cc7`

Accepted readiness documentation:

`62f1bb0d0151e0cd8b2e29a824881107b0649e95`

H-UJ economic implementation:

`ee6bec3e93b507a9c7ac61a0c43fb485e2028357`

Assessment hardening:

`58e9a13b94598e4435c81637a476774abe096863`

Fixed local-control support:

`04ae5bbb0168c44d54b74bfc2bde37c6abc0a254`

Control invariant hardening:

`2acd2e73e78f27a2c50d837ba96cae36dd5efc08`

## Execute exactly

1. sync Dell to exact current remote feature HEAD;
2. run `m024_holdout_tests`;
3. require focused PASS;
4. run `m024_holdout_h_uj_pair` exactly once;
5. require deterministic A/B hashes and every frozen invariant;
6. run `m024_holdout_assessment` exactly once;
7. mechanically accept its terminal classification;
8. run `test_full_native`;
9. durably document M024 closeout;
10. stop.

No alternate candidate, partition, symbol set, direction, session, weekday,
spread filter, M15 setting, parameter, or position-size change is authorized.

Do not use M021 post-cutoff outcomes.
Do not use M025 outcomes.
Do not merge/deploy or enable real trading.
