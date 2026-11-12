# Next Authorized Task

## M029 Stage 3 — trusted read-only data bridge and prospectively scheduled paper decision

**Prerequisite evidence completed 2026-11-12**

- Branch: `prospective-paper-recovery` (keep `main` unchanged).
- Frozen M029 protocol: `b84456f256cd701738b20ff30dc5be37f4f36dfb`.
- Stage-1 pure window/journal implementation accepted with 345 native passes.
- Stage-2 synthetic supplied-BIS/OECD/broker draft assembly accepted,
  feature `bd73d29751b376523e8fd4d74b357e5925744cf1`.
- Latest accepted exact-head native result:
  `bcb873c4d1b812b290e1066fde12e943a7912e49`,
  **356 passed, 2 skipped, 13 existing warnings**.

### Immediate engineering scope (not yet accepted)

1. Freeze a separate M029 Stage-3 operational protocol **before** any real
   source-derived strategy signal is inspected.
2. Design and implement an allowlisted **metadata-only readiness** command:
   source publisher cutoffs/hashes and broker quote/margin viability, with
   read-only MT5 methods only. No signal signs, targets, prices of fills or P/L
   may be generated before the proper window.
3. Wire M029 Stage-2 assembly to source snapshots downloaded **inside the
   decision window**, with actual UTC retrieval timestamps and quote times.
4. Read the workstation UTC clock internally; reject early and late execution,
   including after **2026-12-07T12:10:00Z** for the December month.
5. Use exclusive immutable paper-decision creation and hash verification;
   on record collision never recompute or overwrite.
6. Require both fixed source cutoff and >=4 broker-eligible currencies or
   produce an on-time immutable flat/not-ready record with null P/L.
7. Synthetic-only pre-decision tests, full native regression, safety audit and
   explicit Stage-3 acceptance before authorizing a real-source paper signal.

### Prospective decision schedule

First eligible, if Stage 3 is approved and ready:

- Month: `2026-12`
- Opens: **2026-12-07T12:00:00Z** (15:00 East Africa Time)
- Closes: **2026-12-07T12:10:00Z** (15:10 East Africa Time)
- Do NOT create any record for October or November 2026.
- Do NOT reconstruct a missed December decision after its close.
- Do NOT assume the December execution is automated or scheduled yet.

### Safety and strategy invariants

Preserve M027 12-month signal and volatility, M028 8 currencies and broker
pair mapping, USD 10k reference equity, 4x gross cap, 25% margin cap and
minimum four viable positions. No net P/L with unproven financing/commission
or unobserved slippage. No actual MT5 orders, position changes, trade history,
account balance reads, strategy retuning, historical economics reruns,
production deploy or merge. No assessment before 12 completed prospective
paper holding periods. Tests may use synthetic fixtures only until the
separately frozen Stage-3 approval.
