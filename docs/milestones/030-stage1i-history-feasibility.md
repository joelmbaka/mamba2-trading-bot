# M030 Stage 1I — offline tester/history feasibility audit

Date: 2026-11-12
Status: **READ-ONLY AUDIT ACCEPTED; NATIVE HISTORY PORTABILITY AND NETWORK ISOLATION UNPROVEN**

## Repository

Codex verified clean and synchronized `scalping-recovery` at `4e3e818434f80b0bbe64e7c25c7946e665edc69b`, ahead/behind 0/0. Remote refs fetched. No repository, MT5 or cache file was created or modified.

## Original MT5 environment

- Application: `/home/joel/.local/share/mamba2-mt5-wine1121/app`
- Wine prefix: `/home/joel/.local/share/mamba2-mt5-wine1121/prefix`
- Tester agent: `app/metatester64.exe`
- `app/Tester`: empty; `app/MQL5/Profiles/Tester`: empty
- Original terminal PID `71219` was still running and untouched; no MetaEditor/MetaTester process running.

### Existing opaque EURUSD cache

| Original path (under app/bases/MetaQuotes-Demo) | SHA-256 |
| --- | --- |
| `history/EURUSD/cache/M1.hc` | `ffa5b9ff285f176ac411d3fd97f70429b2ab001fb51b7cc87f43c2df0751afed` |
| `history/EURUSD/cache/M5.hc` | `5ee6fdd079e7458e24ca8531091900573cec865f269a6c7395e46090a1120250` |
| `history/EURUSD/2026.hcc` | `3f95e4e48cf4888a63535bb0531ad313f5e5fa4948b4312089b298998fa54331` |
| `ticks/EURUSD/ticks.dat` | `cc6ee0f1702233f8ae82048e472814b2ce26314e385aa0cd0b69741455cad19f` |

These binary files do not expose an independently verified UTC index or confirmed 2026-09-10 coverage. Their presence does not prove a fresh isolated tester can open them.

## Sensitive/account-linked dependencies

The original MetaQuotes-Demo base contains account-linked directories including `trades/115508635`, symbol and subscription state, and mail/news. Do **not** copy `app/config/accounts.dat`, `servers.dat`, certificates, terminal/common/settings configuration, `trades`, account-specific `symbols`, `subscriptions`, `mail`, `news`, profiles, Wine MetaQuotes/Terminal state, community information, logs, credentials, or the original Wine prefix. Do not copy the entire original MetaQuotes-Demo base to preserve data dependencies.

## Available isolation tools (presence only)

`/usr/bin/bwrap`, `/usr/bin/unshare`, `/usr/bin/nsenter`, `/usr/sbin/nft`, `/usr/sbin/iptables`, `/usr/bin/aa-exec`. User namespaces enabled. Nothing was executed; no network-denial or filesystem isolation is established yet.

## Conclusion

A fresh, offline, account-free MT5 tester with usable native EURUSD history is **not demonstrated**. There are independent obstacles: opaque cache format; uncertain cache portability without associated server/account metadata; absent tester profile/config; and unproven external network blocking. Clock-offset and native OHLC parity remain unknown.

## Proposed Stage 1J — disposable sandbox verification, not MT5 execution

With a *separate, explicit* authorization, validate a disposable, harmless process inside a dedicated user/mount/network namespace with **no network** and strictly limited filesystem mounts. No Wine/terminal/tester, original history copy, broker access or market-data replay. Define tests for:
- Unprivileged namespace/bootstrap feasibility; enforce deny-by-default network isolation and verify absence of routes/interfaces other than loopback, and failed outbound connection to an explicit public test IP, without attempting to contact brokerage endpoints.
- No visibility of original MT5 prefix/app, home directory, repo, secrets or original terminal process tree inside the sandbox. Only disposable inputs/outputs are writable; prohibit host-root `Z:` mapping.
- Failure-safe process teardown and no leaked sandbox processes/mounts; record exact exit codes and restrictions, not broad unsupported claims.
- Distinguish a sandbox network block verified for a trivial local process from future Wine/Tester isolation; the latter will still require verification in its own dedicated environment.

Stage 1J approval must NOT authorize copying the opaque EURUSD cache, starting MT5/tester, generating ticks, assuming historical UTC offsets or adjusting the strategy. Any tester/data-provisioning experiment remains a further separate decision.

No historical replay, downloads, installs, trades, source changes or local-control took place in Stage 1I.
