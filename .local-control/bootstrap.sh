#!/usr/bin/env bash
set -euo pipefail

REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

ORIGIN="$(git config --get remote.origin.url || true)"
if [[ "$ORIGIN" != *"joelmbaka/mamba2-trading-bot"* ]]; then
  echo "ERROR: run this from the local joelmbaka/mamba2-trading-bot checkout."
  exit 1
fi

BASE="$HOME/.local/share/chatgpt-mamba2-local-agent"
RESULTS="$BASE/results-worktree"
AGENT="$BASE/agent.py"
VALIDATION="$BASE/validation.py"
RUNNER="$BASE/run.sh"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT="$UNIT_DIR/chatgpt-mamba2-local-agent.service"
TIMER="$UNIT_DIR/chatgpt-mamba2-local-agent.timer"

mkdir -p "$BASE" "$UNIT_DIR" "$HOME/.local/state/chatgpt-mamba2-local-agent"

echo "Fetching Mamba2 control branches..."
git fetch origin   local-control:refs/remotes/origin/local-control   local-control-results:refs/remotes/origin/local-control-results

echo "Installing isolated Mamba2 local-control agent..."
git show origin/local-control:.local-control/agent.py > "$AGENT"
git show origin/local-control:.local-control/validation.py > "$VALIDATION"
chmod 700 "$AGENT" "$VALIDATION"

# agent.py intentionally dispatches fixed validation actions generically via
# validation.ACTION_HANDLERS. Verify the dispatcher contract in agent.py and
# verify representative historical actions in validation.py itself.
if ! grep -Fq 'VALIDATION_ACTIONS = frozenset(validation.ACTION_HANDLERS)' "$AGENT"; then
  echo "ERROR: installed agent.py does not expose validation.ACTION_HANDLERS."
  exit 1
fi
if ! grep -Fq '"defect_review_diagnostic_run_pair": defect_review_diagnostic_run_pair' "$VALIDATION"; then
  echo "ERROR: installed validation.py does not contain the M018 action."
  exit 1
fi
if ! grep -Fq '"broader_history_run_pair": broader_history_run_pair' "$VALIDATION"; then
  echo "ERROR: installed validation.py does not contain the M019 action."
  exit 1
fi
if ! grep -Fq '"m022_history_checkpoint_probe": m022_history_checkpoint_probe' "$VALIDATION"; then
  echo "ERROR: installed validation.py does not contain the M022 checkpoint action."
  exit 1
fi

echo "Installed control dispatcher and M018/M019/M022 actions verified."

if ! /usr/bin/python3 -m py_compile "$AGENT" "$VALIDATION"; then
  echo "ERROR: installed local-control Python files do not compile."
  exit 1
fi
echo "Installed control files compile successfully."

if [[ ! -d "$RESULTS/.git" && ! -f "$RESULTS/.git" ]]; then
  rm -rf "$RESULTS"
  git worktree add --detach "$RESULTS" origin/local-control-results
else
  git -C "$RESULTS" fetch origin local-control-results
  git -C "$RESULTS" reset --hard origin/local-control-results
fi

cat > "$RUNNER" <<EOF
#!/usr/bin/env bash
set -euo pipefail

REPO="$REPO"
AGENT="$AGENT"
VALIDATION="$VALIDATION"

git -C "\$REPO" fetch origin \\
  local-control:refs/remotes/origin/local-control

AGENT_TMP="\${AGENT}.tmp"
VALIDATION_TMP="\${VALIDATION}.tmp"
trap 'rm -f "\$AGENT_TMP" "\$VALIDATION_TMP"' EXIT

git -C "\$REPO" show origin/local-control:.local-control/agent.py > "\$AGENT_TMP"
git -C "\$REPO" show origin/local-control:.local-control/validation.py > "\$VALIDATION_TMP"
/usr/bin/python3 -m py_compile "\$AGENT_TMP" "\$VALIDATION_TMP"
chmod 700 "\$AGENT_TMP" "\$VALIDATION_TMP"
mv "\$AGENT_TMP" "\$AGENT"
mv "\$VALIDATION_TMP" "\$VALIDATION"
trap - EXIT

export LOCAL_PROJECT_DIR="\$REPO"
export LOCAL_RESULTS_DIR="$RESULTS"
export LOCAL_AGENT_POLL_SECONDS="5"
exec /usr/bin/python3 "\$AGENT" "\$@"
EOF
chmod 700 "$RUNNER"

cat > "$UNIT" <<EOF
[Unit]
Description=ChatGPT Mamba2 Local Development Agent One-Shot Worker
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$RUNNER --once
# A Wine/MT5 descendant must never outlive the worker cgroup or make stop wait
# forever. The checkpoint action also kills its own process group at 30s.
KillMode=control-group
TimeoutStartSec=infinity
TimeoutStopSec=10s
SendSIGKILL=yes
FinalKillSignal=SIGKILL
EOF

cat > "$TIMER" <<EOF
[Unit]
Description=Poll ChatGPT Mamba2 GitHub mailbox

[Timer]
OnBootSec=10s
OnUnitInactiveSec=15s
AccuracySec=1s
Unit=chatgpt-mamba2-local-agent.service

[Install]
WantedBy=timers.target
EOF

# Load the hardened service definition before attempting to terminate any
# previously stuck worker. Otherwise systemd may still use the old unit with no
# finite stop timeout.
systemctl --user daemon-reload

# Kill the existing worker cgroup first so a stuck Wine/MT5 descendant cannot
# block bootstrap. Errors are harmless when the unit is already inactive.
systemctl --user kill --kill-whom=all --signal=SIGKILL \
  chatgpt-mamba2-local-agent.service >/dev/null 2>&1 || true

systemctl --user stop chatgpt-mamba2-local-agent.service || true
systemctl --user reset-failed chatgpt-mamba2-local-agent.service >/dev/null 2>&1 || true
systemctl --user disable chatgpt-mamba2-local-agent.service >/dev/null 2>&1 || true
systemctl --user stop chatgpt-mamba2-local-agent.timer >/dev/null 2>&1 || true

echo
echo "=== START CURRENT QUEUED COMMAND UNDER SYSTEMD ==="
CURRENT_COMMAND_ID="$(
  git show origin/local-control:.local-control/command.json |
    /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))'
)"

# Keep the permanent timer enabled, but do not execute the worker inline in
# this bootstrap shell. Starting under systemd gives the worker the hardened
# cgroup/stop semantics and lets bootstrap return even while MT5 work runs.
systemctl --user enable --now chatgpt-mamba2-local-agent.timer
systemctl --user start --no-block chatgpt-mamba2-local-agent.service || true

echo "Queued command started under systemd: $CURRENT_COMMAND_ID"
echo "Bootstrap is not waiting for command completion."

echo
echo "=== MAMBA2 LOCAL AGENT TIMER ==="
systemctl --user --no-pager --full status chatgpt-mamba2-local-agent.timer || true

echo
echo "=== RECENT WORKER LOGS ==="
journalctl --user -u chatgpt-mamba2-local-agent.service -n 30 --no-pager || true

if ! systemctl --user is-active --quiet chatgpt-mamba2-local-agent.timer; then
  echo "ERROR: chatgpt-mamba2-local-agent.timer is not active."
  exit 1
fi
echo "Timer active verification: PASS"

echo
echo "Installed. Allowed actions:"
echo "  status, sync, switch_branch"
echo "  repo_checks, bootstrap_wine_test_env, runtime_discovery, runtime_versions"
echo "  test_core, test_full_native, test_full_wine"
echo "  first_baseline_cleanup, first_baseline_export, first_baseline_run_pair"
echo "  baseline_diagnostic_run_pair, defect_review_diagnostic_run_pair"
echo "  broader_history_coverage_probe, broader_history_cleanup"
echo "  broader_history_export, broader_history_run_pair"
