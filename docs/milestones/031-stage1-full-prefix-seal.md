# M031 Stage 1 — frozen full-prefix input seal and next implementation gate

Date: 2026-11-12
Status: **READ-ONLY INPUT AUDIT ACCEPTED; SAMPLE PRICE OHLC SEALED; FULL PREFIX M1→M5 PARITY FAILED; BASELINE NOT RUN**

## Repository and audit scope

Codex verified clean `scalping-recovery` at `89d66a735a2f9975ab3ef025cef745477999f3b0`, synchronized with origin (0/0), fetched origin successfully. No tests, replay, MT5/Wine, Strategy Tester, brokers, packages, downloads/uploads or file edits.

## Canonical source identity (immutable)

Directory: `backtest_data/m022-history-inventory-tick-m1-v2/`.

| File | SHA-256 | Rows |
| --- | --- | ---: |
| `manifest.json` | `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b` | n/a |
| `EURUSD_M1.csv` | `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` | 405283 |
| `EURUSD_M1_ask.csv` | `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c` | 405283 |
| `EURUSD_M5.csv` | `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` | 81036 |

CSV `time` is integer Unix seconds interpreted as UTC **bar-open**. Earliest M1 2025-08-25T00:03Z; earliest M5 2025-08-25T00:00Z. Frozen comparison interval `[2026-09-10T00:00:00Z,2026-09-11T00:00:00Z)`. Prior completed warm-up: 389447 M1 and 77868 canonical M5 bars. In-window: 1440 M1 and 288 M5 bars, with complete M1 five-minute groups.

## Critical data-source finding

M1-derived M5 OHLC matches *all 288 frozen-day* source M5 OHLC bars exactly. **It does not match across the entire preceding source prefix**:

- Canonical M5 records: 81036.
- Complete five-M1-derived buckets: 80885.
- Incomplete/missing M1 groups: 151.
- M1-derived buckets with no corresponding canonical M5 row: 83.
- Exactly 3 OHLC mismatches among comparable bars:
  - 2025-10-23T20:05:00Z
  - 2026-02-26T00:25:00Z
  - 2026-06-01T14:00:00Z

The three explicit mismatch timestamps, the 83 extra buckets, and incomplete-group issue **must all** be represented, not collapsed to only three differences. These counts describe the full exported history; do not misinterpret all as confined to the specific indicator seed prefix if future line-level evidence narrows them.

Additionally, **288/288** frozen M5 tick-volume/spread fields differ between M1-aggregated and canonical M5. Full-history ancillary fields differ in 71632 comparable bars. Example `2026-09-10T00:00Z`: derived tick volume 193 vs canonical 166; derived spread 12 vs canonical 0. Separate M1 Ask CSV has its own hash and minute-aggregated Ask, **not tick-level Ask sequence**.

**Gate conclusion:** frozen-day M5 OHLC from M1 aggregation PASS; full-prefix aggregate equivalence FAIL. Both the Python baseline and independent engine **must load original canonical M5 directly** throughout their complete seeded history. Never make a parity claim from native source identity, historical MT5 server clock or tick provenance without independent evidence.

## Strategy and time contract

- M1 completed candle from source open T available at information boundary T+1 minute. M5 only after full T+5 minute interval.
- M1 and M5 Stochastic(21,7,7), recent ten **M1** %K extremes without requiring fresh final-bar crossover, current K/D directional relation, M5 K/D direction, EMA7 seeded from first available **full canonical M1 prefix**, M5 ATR14 on **canonical M5**.
- Preserve disabled optional trend/RSI/higher-TF filters, order 0.1 lots, initial SL/TP zero and later ATR protection by position manager, order/position guards and source-specific Bid/Ask execution policy.
- Comparator key: symbol, decision UTC boundary, completed M1 source-open UTC, completed M5 source-open UTC when available. Exact source time/OHLC; numeric indicator absolute tolerance initially 1e-9 subject to a documented floating-point review; exact per-boundary signals and reasons. Do not match by ordinal positions. Follow event schema `m030.events.v1`.
- Distinguish *signal parity* from *execution-model parity*. `REJECT` and `ACCOUNT` kinds remain schema-only; blocked candidates emit no SIGNAL; independent engine must not fabricate parity from absent records. Costs and P/L depend on matched tick/Ask, spread, rounding, slippage, commission, swap, conversion and intrabar exit assumptions.

## Candidate baseline contract — NOT YET IMPLEMENTED OR RUN

Proposed module: `mamba2.backtest.m031_single_day_baseline`, arguments: `--manifest`, `--m1`, `--m1-ask`, `--m5`, `--symbol EURUSD`, `--start 2026-09-10T00:00:00Z`, `--end 2026-09-11T00:00:00Z`, `--output-dir`, `--fail-on-input-mismatch`.

Expected outputs in a new, bounded scratch directory only: `input_manifest.json`, `indicator_trace.jsonl` (ALL eligible boundary snapshots, not only signals when no position exists), `events.jsonl` (existing runner emission semantics, including no blocked candidate SIGNAL), and `summary.json`. If collecting blocked-boundary independent indicators, keep clearly separated non-order observation from the existing runner's skipped strategy/observer calls; **do not silently modify frozen production lifecycle or fabricate candidate SIGNALs**. If this distinction requires additional instrumentation, design/validate before execution.

Manifest: repo commit, engine/source versions, pinned hashes, full source row counts, pre-sample warm-up, exact UTC interval, canonical M5 direct-use proof, derived M5 equivalence FAIL for full prefix, ancillary policies, Ask usage, indicator defaults, event schema, no-tuning assertion, `executed` state. Include programmatic fail-closed hash check *before* run; no overwrite of an existing run output.

## Independent engine feasibility

Native MT5 custom symbols are a documented platform feature, but Stage 1O isolated no-account MT5 launch remains unstable; do not repeat empty launches or start an undocumented metatester executable. QuantConnect LEAN provides independent custom data APIs. Local Docker exists but `lean`, `dotnet` and a cached LEAN image are absent. A LEAN adapter must implement logic independently (no imports from Mamba2's strategy/indicator modules), load canonical M1, **canonical M5**, and optional canonical M1 Ask, use UTC bar-open semantics and explicit Forex market hours / completed-bar behavior, and emit comparable per-boundary traces. Docker image pull, runtime installation, cloud account/data upload and LEAN run remain separate permissions; no cost or network action is implied here.

## Decision: next stage is source-only implementation preparation, not backtest execution

Proceed with **M031 Stage 2 implementation of a fail-closed one-day Python CLI plus synthetic CLI/integrity tests**, with no historical economic run. Once source reviewed and focused tests pass, authorize exactly **one** frozen September 10 baseline. Provisioning and running independent LEAN comes after separate privacy/runtime checks. Mass testing or tuning remains blocked until independent, same-input eligible-boundary signal parity, with trade/economics evaluated under a separately pinned execution model. M030 original MetaQuotes-Demo clock/data lineage remains unresolved.
