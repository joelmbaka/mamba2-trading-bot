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

if ! grep -Fq '"defect_review_diagnostic_run_pair"' "$AGENT"; then
  echo "ERROR: installed agent.py does not contain the M018 action."
  exit 1
fi
if ! grep -Fq '"defect_review_diagnostic_run_pair"' "$VALIDATION"; then
  echo "ERROR: installed validation.py does not contain the M018 action."
  exit 1
fi
if ! grep -Fq '"broader_history_run_pair"' "$AGENT"; then
  echo "ERROR: installed agent.py does not contain the M019 actions."
  exit 1
fi
if ! grep -Fq '"broader_history_run_pair"' "$VALIDATION"; then
  echo "ERROR: installed validation.py does not contain the M019 actions."
  exit 1
fi

echo "Installed control files verified for M018 and M019 actions."

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
export LOCAL_PROJECT_DIR="$REPO"
export LOCAL_RESULTS_DIR="$RESULTS"
export LOCAL_AGENT_POLL_SECONDS="5"
exec /usr/bin/python3 "$AGENT" "\$@"
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

echo
echo "=== PROCESS CURRENT QUEUED COMMAND ONCE ==="
systemctl --user stop chatgpt-mamba2-local-agent.service || true
CURRENT_COMMAND_ID="$(
  git show origin/local-control:.local-control/command.json |
    /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))'
)"
ONCE_LOG="$(mktemp)"
set +e
"$RUNNER" --once 2>&1 | tee "$ONCE_LOG"
ONCE_STATUS=${PIPESTATUS[0]}
set -e
echo "One-shot command exit status: $ONCE_STATUS"

git -C "$RESULTS" fetch origin local-control-results
git -C "$RESULTS" reset --hard origin/local-control-results
PUBLISHED_COMMAND_ID="$(
  /usr/bin/python3 -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); print(json.loads(p.read_text()).get("command_id","") if p.is_file() else "")'     "$RESULTS/.local-control/result.json"
)"

if [[ "$PUBLISHED_COMMAND_ID" != "$CURRENT_COMMAND_ID" ]]; then
  echo "WARNING: one-shot did not publish the current command; publishing bootstrap fallback."
  CURRENT_COMMAND_ID="$CURRENT_COMMAND_ID"   ONCE_STATUS="$ONCE_STATUS"   ONCE_LOG="$ONCE_LOG"   RESULT_PATH="$RESULTS/.local-control/result.json"   /usr/bin/python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

log_path = Path(os.environ["ONCE_LOG"])
log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
payload = {
    "version": 1,
    "command_id": os.environ["CURRENT_COMMAND_ID"],
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "ok": False,
    "action": "bootstrap_one_shot_fallback",
    "error": "one-shot command finished without publishing a matching result",
    "one_shot_exit_status": int(os.environ["ONCE_STATUS"]),
    "one_shot_log_tail": log[-12000:],
}
path = Path(os.environ["RESULT_PATH"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  git -C "$RESULTS" add .local-control/result.json
  git -C "$RESULTS" -c user.name="ChatGPT Mamba2 Bootstrap"     -c user.email="mamba2-bootstrap@localhost"     commit -m "local-agent: bootstrap fallback $CURRENT_COMMAND_ID"
  git -C "$RESULTS" push origin HEAD:local-control-results
else
  echo "One-shot result publication verification: PASS ($CURRENT_COMMAND_ID)"
fi
rm -f "$ONCE_LOG"

systemctl --user restart chatgpt-mamba2-local-agent.service

sleep 3

echo
echo "=== MAMBA2 LOCAL AGENT ==="
systemctl --user --no-pager --full status chatgpt-mamba2-local-agent.service || true

echo
echo "=== RECENT LOGS ==="
journalctl --user -u chatgpt-mamba2-local-agent.service -n 30 --no-pager || true

if ! systemctl --user is-active --quiet chatgpt-mamba2-local-agent.service; then
  echo "ERROR: chatgpt-mamba2-local-agent.service is not active after restart."
  exit 1
fi
echo "Service active verification: PASS"

echo
echo "Installed. Allowed actions:"
echo "  status, sync, switch_branch"
echo "  repo_checks, bootstrap_wine_test_env, runtime_discovery, runtime_versions"
echo "  test_core, test_full_native, test_full_wine"
echo "  first_baseline_cleanup, first_baseline_export, first_baseline_run_pair"
echo "  baseline_diagnostic_run_pair, defect_review_diagnostic_run_pair"
echo "  broader_history_coverage_probe, broader_history_cleanup"
echo "  broader_history_export, broader_history_run_pair"
