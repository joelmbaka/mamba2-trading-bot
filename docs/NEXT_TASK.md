# Next Authorized Task

## Milestone 020-B — diagnose the M020-A spread confound

Milestone 020 remains **IN PROGRESS**.

Branch:

`backtest-controlled-experiments`

M020-A implementation HEAD before result documentation:

`3958b607ab12bf232c741fe520328b72dd9a23f2`

Accepted M019 immutable control:

- baseline SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`.

M020-A deterministic treatment artifacts:

- baseline SHA-256:
  `65e3fe214e8e923175144dc9749c3fef521da964a796286805ebed745df42658`;
- diagnostic SHA-256:
  `c18c9fdda3fa9cb69cfd90f507d217897875248e5f8d745aa49cafe73925157e`.

M020-A result:

- control P/L: **USD -1,716.607632002333**;
- treatment P/L: **USD -933.4296206208546**;
- delta: **USD +783.1780113814784**;
- control max DD: **USD 1,929.6969567926317 / 19.214803229083717%**;
- treatment max DD: **USD 1,271.330847985335 / 12.659175316162072%**;
- trades: **4,922 -> 4,104**;
- all four calendar periods improved;
- all five symbols improved;
- BUY and SELL both improved;
- treatment remains materially loss-making.

Classification:

**PROMISING, NOT PROMOTED**

## Objective

Before authorizing another strategy treatment, determine whether M020-A's
improvement is primarily associated with:

1. the 00:00–03:59 UTC session itself; or
2. the extreme spread exposure concentrated inside that session.

This is a **diagnostic task only**.

## Required diagnostic

Use deterministic historical artifacts from the immutable M019 control and
M020-A. Add reporting sufficient to produce:

1. entry-spread distribution and fixed quantiles for control trades entered
   during 00:00–03:59 UTC;
2. trade count, wins, losses, flats, and net P/L by those spread quantiles;
3. the same views by symbol;
4. the same views by BUY/SELL;
5. the same views for Jun 23–30, July, August, and Sep 1–24;
6. matched descriptive comparisons for the same spread bands outside
   00:00–03:59 UTC where sample size permits;
7. a clear statement of whether losses persist at ordinary spread levels or
   are dominated by extreme spread tails.

Use fixed descriptive quantiles/bands for diagnosis. Do **not** search for a
profitable cutoff.

## Must not change

Do not:

- change strategy behavior;
- add a spread filter;
- alter or stack the M020-A session filter;
- remove a symbol;
- change BUY/SELL eligibility;
- alter stochastic, EMA, ATR, SL, TP, trailing, position size, or execution
  semantics;
- alter historical data, conversion, or cost assumptions;
- enable real MT5 trading.

## Validation

Required before interpreting M020-B output:

- native tests pass;
- Wine tests pass;
- immutable M019 control hashes still reproduce exactly;
- M020-A treatment hashes remain reproducible if touched by reporting changes;
- diagnostic output is deterministic;
- no production strategy code path changes.

## Decision rule

M020-B may justify documenting a later **single-variable** spread hypothesis.
It does not itself authorize a spread cutoff.

If a later spread experiment is authorized, its threshold must be declared
before implementation and must be tested independently against the immutable
M019 control, not stacked with M020-A.

A genuinely later paper/forward milestone remains mandatory before any
experimental strategy behavior is promoted toward live risk.
