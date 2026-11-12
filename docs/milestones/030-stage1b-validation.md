# M030 Stage 1B — Codex validation review

Date: 2026-11-12
Branch: `scalping-recovery`
Source HEAD validated: `07487976dd76cb03fd5022503810d2d85800a4f1`

## Outcome

**Python validation accepted; independent MQL5 compilation remains blocked. This is not MT5 parity acceptance.**

Codex reported:
- branch `scalping-recovery`, clean working tree, source HEAD equal to origin, 0 ahead/behind;
- direct `pytest` unavailable; existing `.venv` needed `PYTHONPATH=.`;
- `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py -q`: **10 passed**;
- related execution, portfolio, strategy lifecycle, spread, accounting and indicator cache tests: **45 passed**;
- Python `py_compile`: **passed**;
- static no-order EA inspection: no order/trade/account-initialization, broker-connect or position-modification calls found;
- opt-in instrumentation defaults off; no production strategy parameter or uninstrumented economics modified according to Codex static review.

Existing Wine executable: `/home/joel/.local/share/mamba2-mt5-wine1121/runtime/opt/wine-staging/bin/wine` (11.21 Staging).
Terminal: `/home/joel/.local/share/mamba2-mt5-wine1121/app/terminal64.exe`.
MetaEditor: `/home/joel/.local/share/mamba2-mt5-wine1121/app/MetaEditor64.exe`.
Tester component: `/home/joel/.local/share/mamba2-mt5-wine1121/app/metatester64.exe`.

Compilation was **not attempted**, since the terminal was already running from the same Wine environment and an isolated compilation context was not proven. Installed MT5 build and actual compiler diagnostics remain unknown. No tester execution, historical replay, broker connection, data download, package installation, order or local-control was performed.

## Next bounded task — Stage 1B-I isolated compile preparation

1. Codex first determines whether the existing terminal and Wine root can be left untouched while a *separate, disposable* compilation environment is prepared from existing binaries. Do not terminate or reuse the running terminal, edit its MQL5 tree, attach to its GUI, or copy credentials/account profiles.
2. A separate Wine prefix alone may not isolate writes if MetaEditor is pointed at the original app directory or common MQL5 files. Both the application/data directories and Wine prefix must be isolated and non-overlapping, and the compiled output must be inside that disposable location.
3. Inspect target environment identity and safety *without launching compilation yet*; report canonical executable/source/output paths, whether source copies could be made without preserving secrets, the source hash, and whether the terminal could be started accidentally. Reject unsafe relative paths, symbolic links and shared data roots.
4. Require separate authorization for making disposable copies, launching MetaEditor/compiling and any additional Wine processes. Stop and report if such operations require installs, account access or mutation of the original environment.
5. Only after compilation and a compiler report can a distinct tester-readiness gate be considered. Strategy Tester runs and historical economic comparisons remain prohibited.

## Unresolved protocol risks

- Same first source bar and EMA history seed across Python and MQL5, identical M1/M5 series and exact bar IDs.
- MT5 server offset not yet independently verified; terminal/tick history provenance unknown.
- Python open-position blocking and MQL5 candidate decision eligibility differ.
- MQL5 decision-only CSV and Python execution ledger are not a complete, independently matched trade lifecycle.
- Tests above do **not** prove full replay parity, cross-engine indicator equality, MT5 build identity or realistic net expectancy.

No strategy optimization, broker connection, live trade, simulated trade or historical Strategy Tester run is authorized.
