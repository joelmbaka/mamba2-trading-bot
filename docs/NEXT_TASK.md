# Next Authorized Task

## M024 — implement fixed H-UJ historical-holdout replay

Branch:

`symbol-specialization-research`

Holdout checkpoint protocol freeze:

`b8f54de8f79f84c6f913515231e46453106a6cc7`

Accepted readiness result:

`098ecd3116daf9e26b2bf6b03d6d7a643fce66cb`

Accepted readiness artifact SHA-256:

`85852452d61db9447e8935ddc05e2f8e41889aa3ae168b3cc2a76ab26ceedb2e`

Frozen readiness hashes:

- 57-date list:
  `5d71d3ed67e5ae50f7e515f765e99a4887336e8a0d3659c62836d79dfe484af4`
- replay boundary:
  `945c9961af7ce58e3b54223f0b8c10eb216e3dbfdf687ac002ef27b18197fab7`
- partition spec:
  `2fac9ab123f1ed173a51aab2cccb42368937e9373b4937a94fd421a89a49cb70`
- H1:
  `35cd428dd20dc965aa6e1479a28c73ad66329a1e64d188c1a6e16df25f7b260d`
- H2:
  `eb2dfda09cf52320eeb83aac9175713fb45a8b32a330e5b29168f5cd1bc9ae19`
- H3:
  `c57086b4e23affa9125f3ff4b4b9eb0352cf7bd5b45b45d7efdf865d984f9359`

## Implement exactly one economic candidate

**H-UJ**

- USDJPY strategy only;
- all-five market/conversion data retained;
- exact accepted C-UJ P2-08 BUY-only/all-hours configuration;
- exact readiness partition/hashes above;
- deterministic A/B artifacts;
- exact H1/H2/H3 blocks;
- no alternate arm.

Implement the frozen mechanical assessment from the milestone protocol without
changing thresholds.

Add tests proving:

- only H-UJ is executable;
- readiness hashes are mandatory;
- alternate partition/candidate is rejected before economic computation;
- non-USDJPY strategy entries remain impossible;
- M021/M025 outcomes remain unused;
- no real-order API.

Then add only fixed holdout family + assessment local-control actions.

Do not tune anything after seeing the holdout.
Do not merge/deploy or enable real trading.
