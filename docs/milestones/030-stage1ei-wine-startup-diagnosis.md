# M030 Stage 1E-I — Wine prefix startup diagnosis

Date: 2026-11-12
Status: **READ-ONLY DIAGNOSIS ACCEPTED; FRESH ISOLATED COMPILE RETRY NEXT**

## Repository

Codex verified clean synced `scalping-recovery` at `d9b240dc4c247fb4ae6de5652a2b983537c39395` (ahead/behind 0/0).

## Observations

Failed Stage 1E disposable prefix: `/tmp/mamba2-m030-stage1e.YZFkBB/wine-prefix`.
Copied MetaEditor: `/tmp/mamba2-m030-stage1e.YZFkBB/wine-prefix/drive_c/M030MetaEditorApp/MetaEditor64.exe`.
Wine: 11.21 Staging; Wayland session `wayland-0`, `DISPLAY=:0`.

- `wineboot.log` only says: `wine: created the configuration directory '/tmp/mamba2-m030-stage1e.YZFkBB/wine-prefix'`.
- After the timeout, prefix-specific `wineserver`, `wineboot.exe --init`, two `winedevice.exe` and `rundll32.exe ... wine.inf` processes were still alive. Their environment matched the disposable prefix.
- No remaining MetaEditor, original/new terminal, or Strategy Tester process was observed; no prefix lock files or sockets found.
- Failed prefix `system.reg` 1,735,510 bytes / `user.reg` 61,633 bytes versus successful 1B-II: 2,119,661 / 79,635 bytes and 1D: 2,198,303 / 75,635 bytes.
- Both failed compile logs empty; no EX5.
- Earlier Stage 1B-II and 1D successful compiles used same Wine executable, MetaEditor 5.0.0.6316 and `/portable /compile /log` invocation pattern.
- Original running terminal PID `71219` remains in original app/prefix and unchanged.

## Diagnosis

Most strongly supported cause: the fresh disposable Wine prefix had **not finished initialization** before compilation was attempted. This is a probable environmental startup cause, not definitive proof of why Wine initialization stalled. Empty compiler log is **not** a compiler error report or evidence of source failure.

## Next narrowly authorized action — Stage 1E-II

Codex may, with an explicitly scoped instruction:
1. Verify clean synchronized repository and exact unmodified source hash `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`.
2. Create a **new** disposable root, brand-new Wine prefix and separate copied MetaEditor app/source; do not reuse the failed prefix or clone the original MT5 prefix.
3. Run a bounded `wineboot -u` initialization for that disposable prefix and **wait for successful completion**, using only the already-installed Wine 11.21 runtime. Verify startup/registry completion before compilation. Do not assume the absence of all Wine helper processes is required; check for unfinished `wineboot`/initialization processes and confirm a stable initialized prefix. Any timed-out process tree must be stopped only within that disposable prefix.
4. Remove/restrict `Z:` root mapping and any broad user-folder symlinks **inside the new prefix**. Realpath-check target app, copied source, EX5, log, and common directories; no paths into original app/prefix, repository or account data.
5. Copy minimal compiler support files and the exact source only; exclude `bases`, `config`, logs, profiles, history, original common directory and secrets.
6. Compile this copied no-order EA using MetaEditor from the disposable app with a bounded timeout. Record complete compiler log, exit status, build, source/EX5 SHA-256, and whether original terminal PID `71219` stayed unchanged. If prefix startup fails, **stop and report the blocker; do not invoke compiler**.
7. Do not edit the repository or attempt to repair source code locally; any compiler defects return to ChatGPT for GitHub edits.

## Prohibitions

No Strategy Tester launch, historical Python replay, broker connection/login, data download, package installation, real or simulated orders, original prefix/app/terminal mutation or restart, source changes, optimization or local-control. Compilation alone does not establish historical bar/tick data identity, signals, execution parity or strategy performance.
