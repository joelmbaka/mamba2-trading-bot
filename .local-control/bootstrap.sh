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

mkdir -p "$BASE" "$UNIT_DIR" "$HOME/.local/state/chatgpt-mamba2-local-agent"

echo "Fetching Mamba2 control branches..."
git fetch origin   local-control:refs/remotes/origin/local-control   local-control-results:refs/remotes/origin/local-control-results

echo "Installing isolated Mamba2 local-control agent..."
git show origin/local-control:.local-control/agent.py > "$AGENT"
git show origin/local-control:.local-control/validation.py > "$VALIDATION"
chmod 700 "$AGENT" "$VALIDATION"

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
export LOCAL_PROJECT_DIR="$REPO"
export LOCAL_RESULTS_DIR="$RESULTS"
export LOCAL_AGENT_POLL_SECONDS="5"
exec /usr/bin/python3 "$AGENT"
EOF
chmod 700 "$RUNNER"

cat > "$UNIT" <<EOF
[Unit]
Description=ChatGPT Mamba2 Local Development Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REPO
ExecStart=$RUNNER
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable chatgpt-mamba2-local-agent.service
systemctl --user restart chatgpt-mamba2-local-agent.service

sleep 2

echo
echo "=== MAMBA2 LOCAL AGENT ==="
systemctl --user --no-pager --full status chatgpt-mamba2-local-agent.service || true

echo
echo "=== RECENT LOGS ==="
journalctl --user -u chatgpt-mamba2-local-agent.service -n 30 --no-pager || true

echo
echo "Installed. Allowed actions:"
echo "  status, sync, switch_branch"
echo "  repo_checks, runtime_versions"
echo "  test_core, test_full_native, test_full_wine"
