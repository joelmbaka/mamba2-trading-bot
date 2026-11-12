# Next Authorized Task — M030 Stage 1J sandbox feasibility test (no MT5)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1I READ-ONLY ACCEPTED; NETWORK/FILESYSTEM ISOLATION UNPROVEN**

## Prior evidence

Stage 1H-II: 49 focused tests, 59 relevant regressions and Python syntax checks passed. Original EURUSD M1/M5 canonical epoch-second CSV formats/hashes verified; independent no-order `M030_ClockBarProbe.mq5` built with 0 MetaEditor errors/warnings in isolated environment. Native terminal cache content, historical server offset and MT5 history portability remain unverified.

Stage 1I: clean synchronized branch `4e3e818434f80b0bbe64e7c25c7946e665edc69b`; original MT5 terminal PID 71219 remained untouched. Opaque EURUSD cache files exist under a MetaQuotes-Demo base co-located with sensitive server/account state; entire base must never be copied for the diagnostic. Existing user namespace and bwrap/unshare tools may permit offline isolation, but no network blocking has been proven. Full report: `docs/milestones/030-stage1i-history-feasibility.md`.

## Proposed next task after explicit Codex instruction

M030 Stage 1J: prove a **harmless, non-MT5** disposable process can run inside a least-privilege sandbox, with network namespace denying connectivity, host root/home/repo/original terminal inaccessible, and writable paths restricted to an isolated scratch directory. Use already installed tooling, bounded lifetime and clean teardown. No original app/prefix/history modifications or copies. Record exact command(s), exit codes, network/filesystem probe results, remaining processes and limitations; stop on inability to establish controls. No assumed security guarantee from presence of bwrap or unshare alone.

## Still prohibited

No Wine, MetaEditor, terminal/Strategy Tester launch, native history copies, account/profile files, market data downloads or imports, broker connection, Python historic economic replay, simulated/real orders, installs, production changes, force-push/reset/new branches or local-control. A proven toy-process sandbox does **not** automatically authorize a copied Wine/MT5 run.

## Following gate

Review Stage 1J evidence. Only then assess separate, staged native market-data-only provisioning feasibility under a network-denied disposable environment, with explicit authorization. If native history cannot be accessed without account state, remain blocked rather than fabricating offset/parity.
