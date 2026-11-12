# M030 Stage 1H — independent raw clock/OHLC discovery checkpoint

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **SOURCE COMMITTED; PYTHON TESTS AND MQL5 COMPILATION PENDING**

## New files

- `mql5/M030_ClockBarProbe.mq5`: completely independent, tester-only, EURUSD-only, **no-order** MQL5 EA. It does not load `M030_DecisionProbe.mq5` or the production strategy. It requires explicit `RunId`, unique `OutputName`, and explicit broad **server-local** `ServerEnvelopeStart`/`ServerEnvelopeEnd` parameters (default 0: refuse). No UTC offset required or guessed. Range limited to seven days, row cap at 20,000. Emits newest **completed** native M1 bar each M1 boundary, newest M5 only when changed, including raw server M1 boundary, actual server observed tick time, raw server source-open and unrounded _Digits OHLC. Stops on gaps, stale/unfinished bars, no-order unsafe context, exceeded cap and evidence output collision. All timestamp column names visibly identify server time; no UTC label. File output uses tester's isolated FILE_COMMON and must remain outside original prefix. This is a bar sample, **not entire 2025-2026 warm-up**.
- `mamba2/backtest/m030_clock_discovery.py`: pure-Python no-MT5/network offline comparator. Requires user-supplied **SHA-256 pins for probe, native M1 reference, native M5 reference**. Reads explicitly UTC-labeled reference CSV timestamp + OHLC, and strict server-local probe rows. Uses Decimal exact OHLC values (e.g. 1.10000 == 1.1), validates ordered unique native bars, completed-bar relationships and full canonical window expected counts. Tries explicit candidate integer-minute offsets (default -840 to +840 in 15-minute increments) over *both* M1 and M5; returns UNIQUE only for a **single exact full-coverage match**, otherwise AMBIGUOUS/NO_MATCH and first discrepancy by candidate. One constant offset applies only within the tested window; DST-changing historical data must be separately segmented. A match does **not** establish the entire warm-up or raw tick identity.
- `tests/test_m030_clock_discovery.py`: synthetic unique/ambiguous offsets, missing M5, mismatched M5 OHLC, file hash drift, duplicate native bars and incomplete canonical reference guard.

## Critical execution boundary

**No tester run, Wine process, broker session, historical trading backtest or order has occurred.** These are source-only commits. Before any tester operation:
1. Codex must validate synthetic tests and compile this **new, different** probe in a new disposable isolated Wine/MetaEditor environment. The compiled `M030_DecisionProbe.ex5` from Stage 1E is *not* this probe.
2. A separate runtime plan must prove the isolated tester can access native EURUSD history **offline** without account data/downloads. Stage 1G found no such proof. If unavailable, stop; do not copy full account profiles/history into an unsafe environment or connect to a broker.
3. Explicit separate authorization is required to launch a decision-free observation-only isolated tester. The MQL5 source cannot itself guarantee OS-level network blocking; isolation must enforce that externally and record checks.
4. The broad server envelope must cover the frozen `[2026-09-10T00:00Z, 2026-09-11T00:00Z)` UTC comparison under **all** candidate offsets; a candidate ±14 hour range means using e.g. server-local Sep 9 00:00 through Sep 12 00:00, subject to independent review and known dataset availability.
5. All source/probe hashes, input dates, output path, tester build, scenario time and completeness must be captured in an immutable manifest. If unknown native data source, no results may be treated as parity.

## Remaining design concerns for independent Codex review

- MetaEditor MQL5 compilation, API syntax, tester-only checks and `FILE_COMMON` output isolation have **not yet been validated** for this new probe.
- A tester may have no native history in the disposable prefix; source code cannot solve that.
- A market gap over the broad envelope causes fail-closed termination: document its impact on completeness rather than silently discarding missing bars. First-ever observed bar may precede selected envelope.
- Offline comparator requires a trusted source time column named `bar_open_utc`, `time`, `datetime` or `timestamp` in explicit ISO UTC form. Other reference CSV formats may need documented source-adapter work; never assume naive datetimes are UTC.
- Hardcoded full-day canonical window count of 1,440 M1 and 288 M5 is mandatory by default, but still requires OHLC identity to be independently observed; none is yet verified.
- A unique one-day constant offset cannot be asserted across a full year or through DST transitions.

## Next narrow gate

**Stage 1H-I Codex synthetic tests, static review, and disposable MetaEditor compilation only.** No Strategy Tester or broker. If defects occur, return exact compiler/test evidence to ChatGPT for GitHub-only source corrections.
