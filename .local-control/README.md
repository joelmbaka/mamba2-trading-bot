# Mamba2 Remote Local Control

This branch is a GitHub-mailbox control plane for the physical Mamba2 checkout.

## Branches

- commands: `local-control:.local-control/command.json`
- results: `local-control-results:.local-control/result.json`

## Safety model

- The workstation agent polls GitHub every five seconds.
- It may automatically fast-forward only the branch already checked out locally.
- Automatic sync refuses dirty trees, detached HEAD, missing remotes, and divergence.
- Branch switching is explicit only.
- Branch switching refuses dirty trees and any target branch with local-only commits.
- No stash, reset, force checkout, history rewrite, branch deletion, arbitrary shell execution, or application-branch push exists.
- Test actions are fixed allowlisted workflows.
- Test subprocesses remove the real-MT5 integration opt-in and MT5 login/password/server variables.
- The control plane never places, modifies, or closes MT5 orders.
- Runtime/test output is bounded before publication.
- `bot_cache.json` contents are never read by control actions.

## Initial actions

```text
status
sync
switch_branch
repo_checks
runtime_versions
test_core
test_full_native
test_full_wine
```

`switch_branch` requires:

```json
{"branch":"branch-name"}
```

## Bootstrap

From the physical Mamba2 checkout:

```bash
git fetch origin local-control local-control-results
bash <(git show origin/local-control:.local-control/bootstrap.sh)
```

Re-run the same bootstrap command to update the installed control agent.

Service:

```text
chatgpt-mamba2-local-agent.service
```

Installed files live under:

```text
~/.local/share/chatgpt-mamba2-local-agent/
```

The application checkout is never converted into a control worktree. Results use a separate isolated worktree.
