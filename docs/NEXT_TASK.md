# Next Authorized Task — M030 Stage 1B-II disposable MetaEditor compilation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **ISOLATION PREFLIGHT ACCEPTED; DISPOSABLE NO-ORDER COMPILE ONLY**

## Verified evidence

Stage 1B Python validation passed: 10 focused tests, 45 relevant regression tests, Python syntax compilation passed. Stage 1B-I read-only workstation inspection at source HEAD `914a628bfa92aee46bcb79838ff5b5ce6d3df1f6` established Wine 11.21 runtime, portable running terminal PID 71219, sensitive data in original prefix/app, and broad host mappings in Wine. Separate minimal disposable prefix and application copies are feasible but not yet created. Details: `docs/milestones/030-stage1bi-isolation-preflight.md`.

## Next task

Codex alone may, under an explicit scoped instruction, prepare a disposable, independently mapped Wine prefix and minimal MetaEditor application copy **outside the repository and original installation**, confirm isolation, and compile the copied no-order `mql5/M030_DecisionProbe.mq5` only. Do not copy original Wine prefix, profiles, `config`, `bases`, history, logs, common files, credentials, or account information. Remove host-root mappings and shared user-home symlinks inside disposable prefix; abort if any compiler dependency would touch the original environment. Preserve source checksum and return compiler evidence.

ChatGPT performs any necessary source fixes on GitHub after seeing Codex errors. No branch proliferation; no local-control.

## Still forbidden

Do not launch or interact with original terminal, Strategy Tester, historical Python replay, real/demo broker, any trading orders, data downloads, package installs or optimization. Compiling a no-order EA is **not** authority to run it. Leave the original portable MT5 and PID 71219 untouched.

## Next gate

Review MetaEditor compiler errors, exact build, isolated .ex5 hash and safety evidence. Separately decide decision-only historical test readiness before any tester session.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1a-parity-harness.md`
- `docs/milestones/030-stage1b-validation.md`
- `docs/milestones/030-stage1bi-isolation-preflight.md`
