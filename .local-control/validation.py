#!/usr/bin/env python3
import hashlib
import json
import os
import signal
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path(os.environ["LOCAL_PROJECT_DIR"]).resolve()
WINEPREFIX = Path.home() / ".mamba2-mt5"
WINE_PYTHON = r"C:\Python310\python.exe"

CORE_TESTS = [
    "tests/test_backtest_baseline_reporting.py",
    "tests/test_backtest_portfolio_runner.py",
    "tests/test_backtest_strategy_lifecycle.py",
    "tests/test_position_manager_trailing_semantics.py",
    "tests/test_cache_manager_security.py",
    "tests/test_triple_cross_condition_semantics.py",
]

MAX_OUTPUT_CHARS = 80_000

FIRST_BASELINE_DIR = REPO / "backtest_data" / "first-baseline-20260901-20260925"
FIRST_BASELINE_MANIFEST = FIRST_BASELINE_DIR / "manifest.json"
FIRST_BASELINE_REPORT_A = FIRST_BASELINE_DIR / "report-a.json"
FIRST_BASELINE_REPORT_B = FIRST_BASELINE_DIR / "report-b.json"
FIRST_BASELINE_SYMBOLS = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
ACCEPTED_M016_REPORT_SHA256 = (
    "d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a"
)
ACCEPTED_M018_BASELINE_SHA256 = (
    "e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca"
)
ACCEPTED_M018_DIAGNOSTIC_SHA256 = (
    "1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7"
)
ACCEPTED_M019_BASELINE_SHA256 = (
    "114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983"
)
ACCEPTED_M019_DIAGNOSTIC_SHA256 = (
    "84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8"
)
M017_DIAGNOSTIC_A = FIRST_BASELINE_DIR / "diagnostic-a.json"
M017_DIAGNOSTIC_B = FIRST_BASELINE_DIR / "diagnostic-b.json"
M017_BASELINE_A = FIRST_BASELINE_DIR / "diagnostic-baseline-a.json"
M017_BASELINE_B = FIRST_BASELINE_DIR / "diagnostic-baseline-b.json"
M018_DIAGNOSTIC_A = FIRST_BASELINE_DIR / "m018-diagnostic-a.json"
M018_DIAGNOSTIC_B = FIRST_BASELINE_DIR / "m018-diagnostic-b.json"
M018_BASELINE_A = FIRST_BASELINE_DIR / "m018-baseline-a.json"
M018_BASELINE_B = FIRST_BASELINE_DIR / "m018-baseline-b.json"

M019_FROM_UTC = "2026-06-23T00:00:00Z"
M019_TO_UTC = "2026-09-25T00:00:00Z"
M019_DIR = REPO / "backtest_data" / "broader-history-20260623-20260925"
M019_MANIFEST = M019_DIR / "manifest.json"
M019_DIAGNOSTIC_A = M019_DIR / "m019-diagnostic-a.json"
M019_DIAGNOSTIC_B = M019_DIR / "m019-diagnostic-b.json"
M019_BASELINE_A = M019_DIR / "m019-baseline-a.json"
M019_BASELINE_B = M019_DIR / "m019-baseline-b.json"
M019_REGRESSION_DIAGNOSTIC_A = FIRST_BASELINE_DIR / "m019-regression-diagnostic-a.json"
M019_REGRESSION_DIAGNOSTIC_B = FIRST_BASELINE_DIR / "m019-regression-diagnostic-b.json"
M019_REGRESSION_BASELINE_A = FIRST_BASELINE_DIR / "m019-regression-baseline-a.json"
M019_REGRESSION_BASELINE_B = FIRST_BASELINE_DIR / "m019-regression-baseline-b.json"
M019_SYMBOLS = list(FIRST_BASELINE_SYMBOLS)
M019_TICK_CHECKPOINTS = [
    "2026-06-23T12:00:00Z",
    "2026-07-15T12:00:00Z",
    "2026-08-17T12:00:00Z",
    "2026-09-01T12:00:00Z",
    "2026-09-24T12:00:00Z",
]

M020_CONTROL_BASELINE_A = M019_DIR / "m020-control-baseline-a.json"
M020_CONTROL_BASELINE_B = M019_DIR / "m020-control-baseline-b.json"
M020_CONTROL_DIAGNOSTIC_A = M019_DIR / "m020-control-diagnostic-a.json"
M020_CONTROL_DIAGNOSTIC_B = M019_DIR / "m020-control-diagnostic-b.json"
M020_TREATMENT_BASELINE_A = M019_DIR / "m020-a-treatment-baseline-a.json"
M020_TREATMENT_BASELINE_B = M019_DIR / "m020-a-treatment-baseline-b.json"
M020_TREATMENT_DIAGNOSTIC_A = M019_DIR / "m020-a-treatment-diagnostic-a.json"
M020_TREATMENT_DIAGNOSTIC_B = M019_DIR / "m020-a-treatment-diagnostic-b.json"
M020_B_DIAGNOSTIC_A = M019_DIR / "m020-b-spread-diagnostic-a.json"
M020_B_DIAGNOSTIC_B = M019_DIR / "m020-b-spread-diagnostic-b.json"
M020_C_BASELINE_A = M019_DIR / "m020-c-baseline-a.json"
M020_C_BASELINE_B = M019_DIR / "m020-c-baseline-b.json"
M020_C_DIAGNOSTIC_A = M019_DIR / "m020-c-diagnostic-a.json"
M020_C_DIAGNOSTIC_B = M019_DIR / "m020-c-diagnostic-b.json"
M020_C_DECISION_A = M019_DIR / "m020-c-decision-spread-a.json"
M020_C_DECISION_B = M019_DIR / "m020-c-decision-spread-b.json"
M020_D_BASELINE_A = M019_DIR / "m020-d-baseline-a.json"
M020_D_BASELINE_B = M019_DIR / "m020-d-baseline-b.json"
M020_D_DIAGNOSTIC_A = M019_DIR / "m020-d-diagnostic-a.json"
M020_D_DIAGNOSTIC_B = M019_DIR / "m020-d-diagnostic-b.json"
M020_D_EVIDENCE_A = M019_DIR / "m020-d-evidence-a.json"
M020_D_EVIDENCE_B = M019_DIR / "m020-d-evidence-b.json"

ACCEPTED_M020_D_BASELINE_SHA256 = (
    "94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766"
)
ACCEPTED_M020_D_DIAGNOSTIC_SHA256 = (
    "45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e"
)
ACCEPTED_M020_D_EVIDENCE_SHA256 = (
    "e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a"
)

M021_FROM_UTC = "2026-09-25T00:00:00Z"
M021_PRIMARY_TO_UTC = "2026-10-23T00:00:00Z"
M021_DIR = REPO / "backtest_data" / "m021-forward-20260925-20261023"
M021_MANIFEST = M021_DIR / "manifest.json"
M021_OUTPUT_DIR = M021_DIR / "results"
M021_REG_CONTROL_BASELINE = M019_DIR / "m021-regression-control-baseline.json"
M021_REG_CONTROL_DIAGNOSTIC = M019_DIR / "m021-regression-control-diagnostic.json"
M021_REG_CANDIDATE_BASELINE = M019_DIR / "m021-regression-candidate-baseline.json"
M021_REG_CANDIDATE_DIAGNOSTIC = M019_DIR / "m021-regression-candidate-diagnostic.json"
M021_REG_CANDIDATE_EVIDENCE = M019_DIR / "m021-regression-candidate-evidence.json"

M022_CUTOFF_UTC = "2026-09-25T00:00:00Z"
M022_PROBE_FLOOR_UTC = "2010-01-01T00:00:00Z"
M022_SYMBOLS = list(FIRST_BASELINE_SYMBOLS)
M022_INVENTORY_DIR = REPO / "backtest_data" / "m022-history-inventory-raw"
M022_INVENTORY_MANIFEST = M022_INVENTORY_DIR / "manifest.json"
M022_TICK_INVENTORY_DIR = REPO / "backtest_data" / "m022-history-inventory-tick-m1-v2"
M022_TICK_INVENTORY_MANIFEST = M022_TICK_INVENTORY_DIR / "manifest.json"
M022_NATIVE_INVENTORY_DIR = REPO / "backtest_data" / "m022-history-inventory-native-m1-v3"
M022_NATIVE_INVENTORY_MANIFEST = M022_NATIVE_INVENTORY_DIR / "manifest.json"
M022_PHASE1_REGRESSION_DIR = REPO / "backtest_data" / "m022-phase1-regression-v1"
M022_PHASE1_REG_CONTROL_BASELINE = M022_PHASE1_REGRESSION_DIR / "control-baseline.json"
M022_PHASE1_REG_CONTROL_DIAGNOSTIC = M022_PHASE1_REGRESSION_DIR / "control-diagnostic.json"
M022_PHASE1_REG_M020D_BASELINE = M022_PHASE1_REGRESSION_DIR / "m020d-baseline.json"
M022_PHASE1_REG_M020D_DIAGNOSTIC = M022_PHASE1_REGRESSION_DIR / "m020d-diagnostic.json"
M022_PHASE1_REG_M020D_EVIDENCE = M022_PHASE1_REGRESSION_DIR / "m020d-evidence.json"
M022_PHASE1_REFERENCE_DIR = REPO / "backtest_data" / "m022-phase1-development" / "reference-v1"
M022_PHASE1_STOCHASTIC_DIR = REPO / "backtest_data" / "m022-phase1-development" / "stochastic-v1"


def _safe_env(wine=False):
    env = os.environ.copy()
    for key in (
        "MAMBA_RUN_MT5_INTEGRATION",
        "MAMBA_MT5_LOGIN",
        "MAMBA_MT5_PASSWORD",
        "MAMBA_MT5_SERVER",
    ):
        env.pop(key, None)
    if wine:
        env["WINEPREFIX"] = str(WINEPREFIX)
        env.setdefault("WINEDEBUG", "-all")
    else:
        env["UV_PROJECT_ENVIRONMENT"] = str(REPO / ".venv-native-control")
    return env


def _bounded(value):
    value = value or ""
    if len(value) <= MAX_OUTPUT_CHARS:
        return value
    return "[truncated; final output follows]\n" + value[-MAX_OUTPUT_CHARS:]


def _run(cmd, *, env=None):
    proc = subprocess.run(
        cmd,
        cwd=str(REPO),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    return {
        "command": list(cmd),
        "exit_code": proc.returncode,
        "stdout": _bounded(proc.stdout),
        "stderr": _bounded(proc.stderr),
    }


def _run_process_group_bounded(cmd, *, env=None, timeout_seconds):
    """Run one external probe with a hard wall-clock bound.

    Wine Python works reliably with PIPE-backed standard streams. If the
    timeout fires, kill the complete probe process group and never perform an
    unbounded communicate() while Wine helper processes may still hold pipe
    descriptors open.
    """

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        start_new_session=True,
    )
    timed_out = False
    stdout = ""
    stderr = ""

    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

        # Reap only with finite waits. Do not call communicate() here: Wine
        # descendants may keep inherited pipe descriptors open after the
        # direct child has been killed.
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

        if proc.stdout is not None:
            proc.stdout.close()
        if proc.stderr is not None:
            proc.stderr.close()

        stderr = (stderr or "") + (
            f"\nlocal-control hard-killed process group after "
            f"{timeout_seconds}s\n"
        )

    return {
        "command": list(cmd),
        "exit_code": proc.returncode if proc.returncode is not None else -9,
        "timed_out": timed_out,
        "stdout": _bounded(stdout),
        "stderr": _bounded(stderr),
    }


def _uv():
    value = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    if not Path(value).is_file():
        raise RuntimeError("uv is not available")
    return value


def _native_command(*args):
    # Use the repository lock + .python-version rather than assuming a
    # workstation-specific virtualenv path exists.
    return [_uv(), "run", "--locked", "python", *args]


def _wine():
    value = shutil.which("wine")
    if not value:
        raise RuntimeError("wine is not available")
    return value


def repo_checks():
    commands = []
    for cmd in (
        ["git", "rev-parse", "HEAD"],
        ["git", "branch", "--show-current"],
        ["git", "status", "--porcelain", "--untracked-files=all"],
        ["git", "diff", "--check"],
    ):
        commands.append(_run(cmd))

    commands.append(_run([_uv(), "lock", "--check"]))

    bot_cache = _run(["git", "ls-files", "--error-unmatch", "bot_cache.json"])
    icon_tracked = _run(["git", "ls-files", "--error-unmatch", "icon.png"])
    icon_status = _run(["git", "status", "--short", "--", "icon.png"])
    commands.extend([bot_cache, icon_tracked, icon_status])

    clean = commands[2]["stdout"].strip() == ""
    branch = commands[1]["stdout"].strip()
    divergence = None
    if branch:
        refresh = _run([
            "git",
            "fetch",
            "origin",
            f"{branch}:refs/remotes/origin/{branch}",
        ])
        commands.append(refresh)
        if refresh["exit_code"] != 0:
            return {
                "ok": False,
                "clean": clean,
                "branch": branch,
                "divergence": None,
                "bot_cache_tracked": bot_cache["exit_code"] == 0,
                "icon_tracked": icon_tracked["exit_code"] == 0,
                "icon_changed": bool(icon_status["stdout"].strip()),
                "reason": "failed to refresh current remote branch",
                "commands": commands,
            }
        remote = _run(["git", "rev-parse", "--verify", f"refs/remotes/origin/{branch}"])
        commands.append(remote)
        if remote["exit_code"] == 0:
            divergence_cmd = _run(
                ["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"]
            )
            commands.append(divergence_cmd)
            divergence = divergence_cmd["stdout"].strip()

    ok = (
        all(item["exit_code"] == 0 for item in commands[:5])
        and clean
        and bot_cache["exit_code"] != 0
        and icon_tracked["exit_code"] == 0
        and icon_status["stdout"].strip() == ""
        and (divergence in (None, "0\t0", "0 0"))
    )
    return {
        "ok": ok,
        "clean": clean,
        "branch": branch,
        "divergence": divergence,
        "bot_cache_tracked": bot_cache["exit_code"] == 0,
        "icon_tracked": icon_tracked["exit_code"] == 0,
        "icon_changed": bool(icon_status["stdout"].strip()),
        "commands": commands,
    }


def _wine_windows_path(host_path):
    winepath = shutil.which("winepath")
    if not winepath:
        return None
    proc = subprocess.run(
        [winepath, "-w", str(host_path)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        env=_safe_env(wine=True),
        check=False,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _wine_python_candidates():
    candidates = [("base", WINE_PYTHON)]

    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    if dedicated.is_file():
        windows_path = _wine_windows_path(dedicated)
        if windows_path:
            candidates.append((".venv-wine", windows_path))

    # Previous validation work may use a repo-local Wine virtualenv. Discover
    # only top-level venv/wine-named directories; do not scan arbitrary user
    # data or file contents.
    for child in sorted(REPO.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        name = child.name.lower()
        if child.name == ".venv-wine":
            continue
        if "venv" not in name and "wine" not in name:
            continue
        executable = child / "Scripts" / "python.exe"
        if not executable.is_file():
            continue
        windows_path = _wine_windows_path(executable)
        if windows_path:
            candidates.append((child.name, windows_path))

    seen = set()
    unique = []
    for label, path in candidates:
        if path in seen:
            continue
        seen.add(path)
        unique.append((label, path))
    return unique


def _probe_wine_python(path):
    # Runtime discovery is part of the M022 preflight and must be bounded too;
    # otherwise a stuck Wine interpreter can hang before the checkpoint probe
    # reaches its own timeout boundary.
    return _run_process_group_bounded(
        [
            _wine(),
            path,
            "-c",
            (
                "import json,platform,numpy,MetaTrader5 as mt5,pytest;"
                "print(json.dumps({'python':platform.python_version(),"
                "'machine':platform.machine(),'numpy':numpy.__version__,"
                "'metatrader5':mt5.__version__,'pytest':pytest.__version__}))"
            ),
        ],
        env=_safe_env(wine=True),
        timeout_seconds=15,
    )


def bootstrap_wine_test_env():
    """Create a dedicated pinned Wine test environment without touching live MT5."""

    wine = _wine()
    target_host = REPO / ".venv-wine"
    target_win = _wine_windows_path(target_host)
    constraints_win = _wine_windows_path(REPO / "constraints" / "wine-runtime.txt")
    if not target_win or not constraints_win:
        raise RuntimeError("unable to map Wine test-environment paths")

    commands = []

    base_probe = _run(
        [
            wine,
            WINE_PYTHON,
            "-c",
            "import platform; print(platform.python_version())",
        ],
        env=_safe_env(wine=True),
    )
    commands.append(base_probe)
    if base_probe["exit_code"] != 0 or base_probe["stdout"].strip() != "3.10.11":
        return {
            "ok": False,
            "reason": "base Wine Python 3.10.11 is unavailable",
            "commands": commands,
        }

    create = _run(
        [wine, WINE_PYTHON, "-m", "venv", "--clear", target_win],
        env=_safe_env(wine=True),
    )
    commands.append(create)
    if create["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "failed to create dedicated Wine test venv",
            "commands": commands,
        }

    target_python = target_win.rstrip("\\") + "\\Scripts\\python.exe"

    install = _run(
        [
            wine,
            target_python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-c",
            constraints_win,
            "-e",
            ".[dev]",
        ],
        env=_safe_env(wine=True),
    )
    commands.append(install)
    if install["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "failed to install pinned Wine test dependencies",
            "commands": commands,
        }

    verify = _run(
        [
            wine,
            target_python,
            "-c",
            (
                "import json,platform,numpy,MetaTrader5 as mt5,pytest;"
                "from importlib.metadata import version;"
                "print(json.dumps({'python':platform.python_version(),"
                "'machine':platform.machine(),'numpy':numpy.__version__,"
                "'metatrader5':mt5.__version__,'pywin32':version('pywin32'),"
                "'pytest':pytest.__version__}))"
            ),
        ],
        env=_safe_env(wine=True),
    )
    commands.append(verify)

    ok = (
        verify["exit_code"] == 0
        and '"python": "3.10.11"' in verify["stdout"]
        and '"numpy": "2.2.1"' in verify["stdout"]
        and '"metatrader5": "5.0.6180"' in verify["stdout"]
        and '"pywin32": "310"' in verify["stdout"]
    )
    return {
        "ok": ok,
        "wine_python": target_python,
        "commands": commands,
    }


def runtime_discovery():
    probes = []
    selected = None
    for label, path in _wine_python_candidates():
        probe = _probe_wine_python(path)
        probes.append({"label": label, "python": path, "probe": probe})
        if selected is None and probe["exit_code"] == 0:
            selected = path

    native = _run(
        _native_command(
            "-c",
            (
                "import json,platform,numpy,pytest;"
                "print(json.dumps({'python':platform.python_version(),"
                "'machine':platform.machine(),'numpy':numpy.__version__,"
                "'pytest':pytest.__version__}))"
            ),
        ),
        env=_safe_env(),
    )
    return {
        "ok": native["exit_code"] == 0 and selected is not None,
        "native": native,
        "wine_candidates": probes,
        "selected_wine_python": selected,
    }


def _select_wine_python():
    discovery = runtime_discovery()
    selected = discovery.get("selected_wine_python")
    if not selected:
        raise RuntimeError(
            "no discovered Wine Python has pytest + NumPy + MetaTrader5"
        )
    return selected, discovery


def runtime_versions():
    wine_python, discovery = _select_wine_python()
    wine = _wine()

    native = _run(
        _native_command(
            "-c",
            (
                "import json,platform,numpy;"
                "print(json.dumps({'python':platform.python_version(),"
                "'machine':platform.machine(),'numpy':numpy.__version__}))"
            ),
        ),
        env=_safe_env(),
    )

    wine_result = _run(
        [
            wine,
            wine_python,
            "-c",
            (
                "import json,platform,numpy,MetaTrader5 as mt5;"
                "print(json.dumps({'python':platform.python_version(),"
                "'machine':platform.machine(),'numpy':numpy.__version__,"
                "'metatrader5':mt5.__version__}))"
            ),
        ],
        env=_safe_env(wine=True),
    )

    return {
        "ok": native["exit_code"] == 0 and wine_result["exit_code"] == 0,
        "native": native,
        "wine": wine_result,
        "wine_python": wine_python,
        "discovery": discovery,
    }


def _pytest_native(paths=None):
    args = ["-m", "pytest"]
    if paths:
        args.extend(paths)
    return _run(_native_command(*args), env=_safe_env())


def _pytest_wine():
    wine_python, discovery = _select_wine_python()
    wine = _wine()
    result = _run(
        [wine, wine_python, "-m", "pytest"],
        env=_safe_env(wine=True),
    )
    result["wine_python"] = wine_python
    result["discovery"] = discovery
    return result


def test_core():
    result = _pytest_native(CORE_TESTS)
    return {"ok": result["exit_code"] == 0, "run": result}


def test_full_native():
    result = _pytest_native()
    return {"ok": result["exit_code"] == 0, "run": result}


def test_full_wine():
    result = _pytest_wine()
    return {"ok": result["exit_code"] == 0, "run": result}



def _require_first_baseline_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "backtest-first-baseline":
        raise RuntimeError(
            "first-baseline action requires branch backtest-first-baseline"
        )
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("first-baseline action refuses a dirty worktree")


def _require_m017_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "backtest-baseline-diagnosis":
        raise RuntimeError(
            "baseline-diagnostic action requires branch "
            "backtest-baseline-diagnosis"
        )
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError(
            "baseline-diagnostic action refuses a dirty worktree"
        )


def _require_m018_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "backtest-proven-defect-review":
        raise RuntimeError(
            "M018 diagnostic action requires branch "
            "backtest-proven-defect-review"
        )
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M018 diagnostic action refuses a dirty worktree")


def _require_m019_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "backtest-broader-history":
        raise RuntimeError(
            "M019 action requires branch backtest-broader-history"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M019 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        "backtest-broader-history:refs/remotes/origin/backtest-broader-history",
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M019 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/backtest-broader-history",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M019 action requires local HEAD to match origin/backtest-broader-history"
        )


def _require_m020_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "backtest-controlled-experiments":
        raise RuntimeError(
            "M020 action requires branch backtest-controlled-experiments"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M020 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "backtest-controlled-experiments:"
            "refs/remotes/origin/backtest-controlled-experiments"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M020 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/backtest-controlled-experiments",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M020 action requires local HEAD to match "
            "origin/backtest-controlled-experiments"
        )


def _require_m021_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "prospective-forward-validation":
        raise RuntimeError(
            "M021 action requires branch prospective-forward-validation"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M021 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "prospective-forward-validation:"
            "refs/remotes/origin/prospective-forward-validation"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M021 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/prospective-forward-validation",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M021 action requires local HEAD to match "
            "origin/prospective-forward-validation"
        )


def _require_m022_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "strategy-parameter-research":
        raise RuntimeError(
            "M022 action requires branch strategy-parameter-research"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M022 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "strategy-parameter-research:"
            "refs/remotes/origin/strategy-parameter-research"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M022 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/strategy-parameter-research",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M022 action requires local HEAD to match "
            "origin/strategy-parameter-research"
        )
    return head["stdout"].strip()


def _ensure_baseline_path(path):
    root = (REPO / "backtest_data").resolve()
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("refusing path outside backtest_data") from exc
    return resolved


def first_baseline_cleanup():
    _require_first_baseline_branch()
    target = _ensure_baseline_path(FIRST_BASELINE_DIR)
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {
        "ok": not target.exists(),
        "path": str(target.relative_to(REPO)),
        "existed": existed,
    }


def first_baseline_export():
    _require_first_baseline_branch()
    output_dir = _ensure_baseline_path(FIRST_BASELINE_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": (
                "baseline dataset directory already exists; "
                "run first_baseline_cleanup explicitly before re-export"
            ),
            "path": str(output_dir.relative_to(REPO)),
        }

    wine_python, discovery = _select_wine_python()
    wine = _wine()

    command = [
        wine,
        wine_python,
        "-m",
        "mamba2.backtest.mt5_dataset",
        "--symbols",
        *FIRST_BASELINE_SYMBOLS,
        "--timeframes",
        "M1",
        "M5",
        "M15",
        "--from-utc",
        "2026-09-01T00:00:00Z",
        "--to-utc",
        "2026-09-25T00:00:00Z",
        "--output-dir",
        str(FIRST_BASELINE_DIR.relative_to(REPO)),
        "--include-tick-ask",
        "--tick-chunk-minutes",
        "1440",
    ]
    export = _run(command, env=_safe_env(wine=True))
    if export["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "read-only MT5 historical export failed",
            "export": export,
            "discovery": discovery,
        }

    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "export completed without manifest.json",
            "export": export,
            "discovery": discovery,
        }

    inspect_code = (
        "import json;"
        "from pathlib import Path;"
        "from mamba2.backtest.mt5_dataset import load_mt5_dataset;"
        f"p=Path({str(FIRST_BASELINE_MANIFEST)!r});"
        "d=load_mt5_dataset(p);"
        "print(json.dumps({"
        "'account_currency':d.account_currency,"
        "'symbols':sorted(d.m1_bars),"
        "'m1_rows':{s:len(d.m1_bars[s]) for s in sorted(d.m1_bars)},"
        "'ask_rows':{s:len(d.ask_m1_bars[s]) for s in sorted(d.ask_m1_bars)},"
        "'native_rows':{s:{tf:len(df) for tf,df in sorted(d.native_timeframe_bars[s].items())} "
        "for s in sorted(d.native_timeframe_bars)},"
        "'requested_range':d.manifest.get('requested_range'),"
        "'schema_version':d.manifest.get('schema_version')"
        "},sort_keys=True))"
    )
    inspect = _run(
        _native_command("-c", inspect_code),
        env=_safe_env(),
    )
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "exported dataset failed native load/integrity check",
            "export": export,
            "inspect": inspect,
        }

    try:
        summary = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse dataset inspection summary") from exc

    expected = set(FIRST_BASELINE_SYMBOLS)
    symbols_ok = set(summary.get("symbols", [])) == expected
    ask_ok = all(
        summary.get("ask_rows", {}).get(symbol)
        == summary.get("m1_rows", {}).get(symbol)
        and summary.get("m1_rows", {}).get(symbol, 0) > 0
        for symbol in FIRST_BASELINE_SYMBOLS
    )
    native_ok = all(
        summary.get("native_rows", {}).get(symbol, {}).get("M5", 0) > 0
        and summary.get("native_rows", {}).get(symbol, {}).get("M15", 0) > 0
        for symbol in FIRST_BASELINE_SYMBOLS
    )

    return {
        "ok": bool(symbols_ok and ask_ok and native_ok),
        "manifest": str(FIRST_BASELINE_MANIFEST.relative_to(REPO)),
        "dataset": summary,
        "export": export,
        "inspect": inspect,
        "wine_python": wine_python,
    }


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_snapshot():
    root = REPO / "backtest"
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(REPO))
        for path in root.rglob("*")
        if path.is_file()
    )


def first_baseline_run_pair():
    _require_first_baseline_branch()
    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "first baseline manifest is missing; export dataset first",
        }

    for report in (FIRST_BASELINE_REPORT_A, FIRST_BASELINE_REPORT_B):
        if report.exists():
            report.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for output in (FIRST_BASELINE_REPORT_A, FIRST_BASELINE_REPORT_B):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.baseline",
                "--manifest",
                str(FIRST_BASELINE_MANIFEST.relative_to(REPO)),
                "--output",
                str(output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "baseline execution failed",
                "runs": runs,
            }

    if not FIRST_BASELINE_REPORT_A.is_file() or not FIRST_BASELINE_REPORT_B.is_file():
        return {
            "ok": False,
            "reason": "baseline report file missing after successful command",
            "runs": runs,
        }

    bytes_a = FIRST_BASELINE_REPORT_A.read_bytes()
    bytes_b = FIRST_BASELINE_REPORT_B.read_bytes()
    sha_a = _sha256(FIRST_BASELINE_REPORT_A)
    sha_b = _sha256(FIRST_BASELINE_REPORT_B)
    identical = bytes_a == bytes_b and sha_a == sha_b

    report = json.loads(bytes_a.decode("utf-8"))
    artifacts_after = _artifact_snapshot()
    no_new_artifacts = artifacts_after == artifacts_before

    aggregate = report.get("aggregate", {})
    return {
        "ok": bool(identical and no_new_artifacts),
        "reports_identical": identical,
        "sha256_a": sha_a,
        "sha256_b": sha_b,
        "report_a": str(FIRST_BASELINE_REPORT_A.relative_to(REPO)),
        "report_b": str(FIRST_BASELINE_REPORT_B.relative_to(REPO)),
        "dataset": report.get("dataset"),
        "configuration": report.get("configuration"),
        "cost_assumptions": report.get("cost_assumptions"),
        "aggregate": aggregate,
        "per_symbol": report.get("per_symbol"),
        "remaining_positions": report.get("remaining_positions"),
        "equity_curve_rows": len(report.get("equity_curve", [])),
        "no_new_strategy_artifacts": no_new_artifacts,
        "artifact_snapshot_before": artifacts_before,
        "artifact_snapshot_after": artifacts_after,
        "runs": runs,
    }


def baseline_diagnostic_run_pair():
    _require_m017_branch()
    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 dataset manifest is missing",
        }
    if not FIRST_BASELINE_REPORT_A.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 report-a.json is missing",
        }

    accepted_sha = _sha256(FIRST_BASELINE_REPORT_A)
    if accepted_sha != ACCEPTED_M016_REPORT_SHA256:
        return {
            "ok": False,
            "reason": "local M016 report does not match accepted SHA-256",
            "expected_sha256": ACCEPTED_M016_REPORT_SHA256,
            "actual_sha256": accepted_sha,
        }

    outputs = (
        M017_DIAGNOSTIC_A,
        M017_DIAGNOSTIC_B,
        M017_BASELINE_A,
        M017_BASELINE_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    pairs = (
        (M017_DIAGNOSTIC_A, M017_BASELINE_A),
        (M017_DIAGNOSTIC_B, M017_BASELINE_B),
    )
    parsed = []
    for diagnostic_output, baseline_output in pairs:
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.diagnostics",
                "--manifest",
                str(FIRST_BASELINE_MANIFEST.relative_to(REPO)),
                "--output",
                str(diagnostic_output.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--expected-baseline-report",
                str(FIRST_BASELINE_REPORT_A.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "baseline diagnostic execution failed",
                "runs": runs,
            }
        try:
            parsed.append(
                json.loads(result["stdout"].strip().splitlines()[-1])
            )
        except (json.JSONDecodeError, IndexError) as exc:
            raise RuntimeError(
                "unable to parse diagnostic summary"
            ) from exc

    required = outputs
    if any(not output.is_file() for output in required):
        return {
            "ok": False,
            "reason": "diagnostic output missing after successful command",
            "runs": runs,
        }

    diagnostic_sha_a = _sha256(M017_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M017_DIAGNOSTIC_B)
    diagnostic_identical = (
        M017_DIAGNOSTIC_A.read_bytes() == M017_DIAGNOSTIC_B.read_bytes()
        and diagnostic_sha_a == diagnostic_sha_b
    )
    baseline_sha_a = _sha256(M017_BASELINE_A)
    baseline_sha_b = _sha256(M017_BASELINE_B)
    baseline_preserved = (
        baseline_sha_a == ACCEPTED_M016_REPORT_SHA256
        and baseline_sha_b == ACCEPTED_M016_REPORT_SHA256
        and M017_BASELINE_A.read_bytes() == FIRST_BASELINE_REPORT_A.read_bytes()
        and M017_BASELINE_B.read_bytes() == FIRST_BASELINE_REPORT_A.read_bytes()
    )

    diagnostic = json.loads(M017_DIAGNOSTIC_A.read_text(encoding="utf-8"))
    reconciliation = diagnostic.get("reconciliation", {})
    totals_ok = (
        reconciliation.get("accepted_orders") == 1393
        and reconciliation.get("closed_trades") == 1393
        and reconciliation.get("remaining_open_positions") == 0
        and reconciliation.get("ending_realized_balance")
        == 9731.45700985454
        and reconciliation.get("diagnostic_trade_rows") == 1393
    )

    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_after == artifacts_before
    analysis = diagnostic.get("analysis", {})

    return {
        "ok": bool(
            diagnostic_identical
            and baseline_preserved
            and totals_ok
            and no_new_strategy_artifacts
        ),
        "baseline_preserved": baseline_preserved,
        "accepted_baseline_sha256": ACCEPTED_M016_REPORT_SHA256,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "diagnostic_a": str(M017_DIAGNOSTIC_A.relative_to(REPO)),
        "diagnostic_b": str(M017_DIAGNOSTIC_B.relative_to(REPO)),
        "reconciliation": reconciliation,
        "analysis": {
            "by_symbol": analysis.get("by_symbol"),
            "by_side": analysis.get("by_side"),
            "by_entry_utc_bucket": analysis.get("by_entry_utc_bucket"),
            "by_exit_reason": analysis.get("by_exit_reason"),
            "spread_by_outcome": analysis.get("spread_by_outcome"),
            "conversion_routes": analysis.get("conversion_routes"),
            "protection": analysis.get("protection"),
            "loss_clustering": {
                key: value
                for key, value in (
                    analysis.get("loss_clustering") or {}
                ).items()
                if key != "streaks"
            },
            "drawdown_episode_count": analysis.get(
                "drawdown_episode_count"
            ),
            "deepest_drawdown_episodes": analysis.get(
                "deepest_drawdown_episodes"
            ),
        },
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "runs": runs,
    }


def defect_review_diagnostic_run_pair():
    _require_m018_branch()
    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 dataset manifest is missing",
        }
    if not FIRST_BASELINE_REPORT_A.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 report-a.json is missing",
        }

    accepted_bytes = FIRST_BASELINE_REPORT_A.read_bytes()
    accepted_sha = _sha256(FIRST_BASELINE_REPORT_A)
    if accepted_sha != ACCEPTED_M016_REPORT_SHA256:
        return {
            "ok": False,
            "reason": "local M016 report does not match accepted SHA-256",
            "expected_sha256": ACCEPTED_M016_REPORT_SHA256,
            "actual_sha256": accepted_sha,
        }
    accepted_report = json.loads(accepted_bytes.decode("utf-8"))

    outputs = (
        M018_DIAGNOSTIC_A,
        M018_DIAGNOSTIC_B,
        M018_BASELINE_A,
        M018_BASELINE_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for diagnostic_output, baseline_output in (
        (M018_DIAGNOSTIC_A, M018_BASELINE_A),
        (M018_DIAGNOSTIC_B, M018_BASELINE_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.diagnostics",
                "--manifest",
                str(FIRST_BASELINE_MANIFEST.relative_to(REPO)),
                "--output",
                str(diagnostic_output.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M018 corrected diagnostic replay failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M018 corrected output missing after successful command",
            "runs": runs,
        }

    baseline_bytes_a = M018_BASELINE_A.read_bytes()
    baseline_bytes_b = M018_BASELINE_B.read_bytes()
    baseline_sha_a = _sha256(M018_BASELINE_A)
    baseline_sha_b = _sha256(M018_BASELINE_B)
    baseline_identical = (
        baseline_bytes_a == baseline_bytes_b
        and baseline_sha_a == baseline_sha_b
    )

    diagnostic_bytes_a = M018_DIAGNOSTIC_A.read_bytes()
    diagnostic_bytes_b = M018_DIAGNOSTIC_B.read_bytes()
    diagnostic_sha_a = _sha256(M018_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M018_DIAGNOSTIC_B)
    diagnostic_identical = (
        diagnostic_bytes_a == diagnostic_bytes_b
        and diagnostic_sha_a == diagnostic_sha_b
    )

    corrected_report = json.loads(baseline_bytes_a.decode("utf-8"))
    diagnostic = json.loads(diagnostic_bytes_a.decode("utf-8"))
    aggregate = corrected_report.get("aggregate", {})
    accepted_aggregate = accepted_report.get("aggregate", {})
    trades = diagnostic.get("trades", [])

    target_direction_violations = []
    negative_take_profit = []
    for trade in trades:
        protection = trade.get("initial_protection") or {}
        target = protection.get("applied_tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        if target is not None and entry is not None:
            crossed = (
                side == "BUY" and float(target) <= float(entry)
            ) or (
                side == "SELL" and float(target) >= float(entry)
            )
            if crossed:
                target_direction_violations.append(
                    int(trade["position_ticket"])
                )
        if (
            trade.get("exit_reason") == "take_profit"
            and float(trade.get("net_realized_pl", 0.0)) < 0
        ):
            negative_take_profit.append(
                {
                    "ticket": int(trade["position_ticket"]),
                    "symbol": trade["symbol"],
                    "side": side,
                    "net_realized_pl": float(trade["net_realized_pl"]),
                }
            )

    aggregate_deltas = {}
    for key in (
        "accepted_orders",
        "closed_trades",
        "remaining_open_positions",
        "ending_realized_balance",
        "ending_unrealized_pl",
        "ending_equity",
        "gross_realized_pl",
        "commission",
        "net_realized_pl",
        "wins",
        "losses",
        "flats",
        "non_flat_win_rate_pct",
        "largest_closed_gain",
        "largest_closed_loss",
        "max_equity_drawdown",
        "max_equity_drawdown_pct",
    ):
        old = accepted_aggregate.get(key)
        new = aggregate.get(key)
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            aggregate_deltas[key] = new - old
        else:
            aggregate_deltas[key] = None

    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_after == artifacts_before

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and not target_direction_violations
            and not negative_take_profit
            and no_new_strategy_artifacts
        ),
        "baseline_reports_identical": baseline_identical,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "accepted_m016_sha256": ACCEPTED_M016_REPORT_SHA256,
        "baseline_changed_from_m016": (
            baseline_sha_a != ACCEPTED_M016_REPORT_SHA256
        ),
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "aggregate": aggregate,
        "accepted_m016_aggregate": accepted_aggregate,
        "aggregate_deltas": aggregate_deltas,
        "per_symbol": corrected_report.get("per_symbol"),
        "analysis": diagnostic.get("analysis"),
        "target_direction_violation_count": len(
            target_direction_violations
        ),
        "target_direction_violation_tickets": target_direction_violations,
        "negative_take_profit_count": len(negative_take_profit),
        "negative_take_profit_trades": negative_take_profit,
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "runs": runs,
    }



def configure_local_control_runtime():
    """Persist a long timeout for allowlisted one-shot validation jobs."""

    unit_dir = Path.home() / ".config" / "systemd" / "user"
    dropin_dir = unit_dir / "chatgpt-mamba2-local-agent.service.d"
    dropin = dropin_dir / "10-long-running-jobs.conf"
    dropin_dir.mkdir(parents=True, exist_ok=True)
    dropin.write_text(
        "[Service]\nTimeoutStartSec=6h\n",
        encoding="utf-8",
    )

    reload_result = _run(["systemctl", "--user", "daemon-reload"])
    show_result = _run([
        "systemctl",
        "--user",
        "show",
        "chatgpt-mamba2-local-agent.service",
        "--property=TimeoutStartUSec",
        "--value",
    ])
    value = show_result["stdout"].strip()
    ok = (
        reload_result["exit_code"] == 0
        and show_result["exit_code"] == 0
        and value not in ("", "1min 30s", "90s", "90000000")
    )
    return {
        "ok": ok,
        "dropin": str(dropin),
        "timeout_start": value,
        "daemon_reload": reload_result,
        "show": show_result,
    }


def broader_history_coverage_probe():
    _require_m019_branch()

    wine_python, discovery = _select_wine_python()
    wine = _wine()
    code = r'''
import json
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
start = datetime.fromisoformat("2026-06-23T00:00:00+00:00")
end = datetime.fromisoformat("2026-09-25T00:00:00+00:00")
checkpoints = [
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    for value in [
        "2026-06-23T12:00:00Z",
        "2026-07-15T12:00:00Z",
        "2026-08-17T12:00:00Z",
        "2026-09-01T12:00:00Z",
        "2026-09-24T12:00:00Z",
    ]
]
timeframes = [
    ("M1", mt5.TIMEFRAME_M1, 60),
    ("M5", mt5.TIMEFRAME_M5, 300),
    ("M15", mt5.TIMEFRAME_M15, 900),
]

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed for read-only M019 coverage probe")

try:
    output = {}
    for symbol in symbols:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"MT5 could not select {symbol}")

        bars = {}
        for label, timeframe, seconds in timeframes:
            cursor = start
            rows = []
            while cursor < end:
                chunk_end = min(cursor + timedelta(days=7), end)
                rates = mt5.copy_rates_range(
                    symbol,
                    timeframe,
                    cursor,
                    chunk_end,
                )
                if rates is not None and len(rates) > 0:
                    rows.extend(rates)
                cursor = chunk_end

            if not rows:
                bars[label] = {"rows": 0, "first": None, "last": None}
                continue

            unique = {}
            for row in rows:
                unique[int(row["time"])] = row
            ordered = [unique[key] for key in sorted(unique)]
            bars[label] = {
                "rows": int(len(ordered)),
                "first": datetime.fromtimestamp(
                    int(ordered[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z"),
                "last": datetime.fromtimestamp(
                    int(ordered[-1]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z"),
            }

        ticks = {}
        for checkpoint in checkpoints:
            sample_end = checkpoint + timedelta(minutes=15)
            values = mt5.copy_ticks_range(
                symbol,
                checkpoint,
                sample_end,
                mt5.COPY_TICKS_ALL,
            )
            count = int(len(values)) if values is not None else 0
            ticks[checkpoint.isoformat().replace("+00:00", "Z")] = count

        output[symbol] = {"bars": bars, "tick_samples": ticks}

    print(json.dumps({
        "from_utc": "2026-06-23T00:00:00Z",
        "to_utc": "2026-09-25T00:00:00Z",
        "symbols": output,
    }, sort_keys=True))
finally:
    mt5.shutdown()
'''
    result = _run(
        [wine, wine_python, "-c", code],
        env=_safe_env(wine=True),
    )
    if result["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "read-only M019 coverage probe failed",
            "run": result,
            "wine_python": wine_python,
            "discovery": discovery,
        }

    try:
        payload = json.loads(result["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse M019 coverage probe") from exc

    symbol_data = payload.get("symbols", {})
    expected_first = M019_FROM_UTC
    minimum_last = {
        "M1": "2026-09-24T23:59:00Z",
        "M5": "2026-09-24T23:55:00Z",
        "M15": "2026-09-24T23:45:00Z",
    }
    bars_ok = all(
        symbol_data.get(symbol, {}).get("bars", {}).get(timeframe, {}).get(
            "rows", 0
        ) > 0
        and symbol_data.get(symbol, {}).get("bars", {}).get(
            timeframe, {}
        ).get("first") == expected_first
        and symbol_data.get(symbol, {}).get("bars", {}).get(
            timeframe, {}
        ).get("last", "") >= minimum_last[timeframe]
        for symbol in M019_SYMBOLS
        for timeframe in ("M1", "M5", "M15")
    )
    ticks_ok = all(
        symbol_data.get(symbol, {}).get("tick_samples", {}).get(checkpoint, 0)
        > 0
        for symbol in M019_SYMBOLS
        for checkpoint in M019_TICK_CHECKPOINTS
    )
    return {
        "ok": bool(bars_ok and ticks_ok),
        "from_utc": M019_FROM_UTC,
        "to_utc": M019_TO_UTC,
        "bars_available": bars_ok,
        "tick_samples_available": ticks_ok,
        "coverage": symbol_data,
        "wine_python": wine_python,
        "discovery": discovery,
        "run": result,
    }


def broader_history_cleanup():
    _require_m019_branch()
    target = _ensure_baseline_path(M019_DIR)
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {
        "ok": not target.exists(),
        "path": str(target.relative_to(REPO)),
        "existed": existed,
    }


def broader_history_export():
    _require_m019_branch()
    output_dir = _ensure_baseline_path(M019_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": (
                "M019 dataset directory already exists; "
                "run broader_history_cleanup explicitly before re-export"
            ),
            "path": str(output_dir.relative_to(REPO)),
        }

    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 dataset is required for overlap verification",
        }

    wine_python, discovery = _select_wine_python()
    wine = _wine()
    export = _run(
        [
            wine,
            wine_python,
            "-m",
            "mamba2.backtest.mt5_dataset",
            "--symbols",
            *M019_SYMBOLS,
            "--timeframes",
            "M1",
            "M5",
            "M15",
            "--from-utc",
            M019_FROM_UTC,
            "--to-utc",
            M019_TO_UTC,
            "--output-dir",
            str(M019_DIR.relative_to(REPO)),
            "--include-tick-ask",
            "--tick-chunk-minutes",
            "1440",
            "--rate-chunk-days",
            "7",
        ],
        env=_safe_env(wine=True),
    )
    if export["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "read-only M019 historical export failed",
            "export": export,
            "wine_python": wine_python,
            "discovery": discovery,
        }

    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M019 export completed without manifest.json",
            "export": export,
        }

    inspect_code = r'''
import json
from pathlib import Path
import pandas as pd

from mamba2.backtest.mt5_dataset import load_mt5_dataset

broader = load_mt5_dataset(Path("backtest_data/broader-history-20260623-20260925/manifest.json"))
accepted = load_mt5_dataset(Path("backtest_data/first-baseline-20260901-20260925/manifest.json"))
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
start = pd.Timestamp("2026-09-01T00:00:00Z")
end = pd.Timestamp("2026-09-25T00:00:00Z")

overlap = {}
for symbol in symbols:
    symbol_checks = {}
    frames = [
        ("M1", broader.m1_bars[symbol], accepted.m1_bars[symbol]),
        ("M5", broader.native_timeframe_bars[symbol]["M5"], accepted.native_timeframe_bars[symbol]["M5"]),
        ("M15", broader.native_timeframe_bars[symbol]["M15"], accepted.native_timeframe_bars[symbol]["M15"]),
        ("ASK_M1", broader.ask_m1_bars[symbol], accepted.ask_m1_bars[symbol]),
    ]
    for label, wide, old in frames:
        sliced = wide.loc[(wide.index >= start) & (wide.index < end)]
        symbol_checks[label] = bool(sliced.equals(old))
    overlap[symbol] = symbol_checks

summary = {
    "account_currency": broader.account_currency,
    "symbols": sorted(broader.m1_bars),
    "m1_rows": {s: len(broader.m1_bars[s]) for s in sorted(broader.m1_bars)},
    "ask_rows": {s: len(broader.ask_m1_bars[s]) for s in sorted(broader.ask_m1_bars)},
    "native_rows": {
        s: {tf: len(df) for tf, df in sorted(broader.native_timeframe_bars[s].items())}
        for s in sorted(broader.native_timeframe_bars)
    },
    "requested_range": broader.manifest.get("requested_range"),
    "schema_version": broader.manifest.get("schema_version"),
    "overlap_with_m016": overlap,
}
print(json.dumps(summary, sort_keys=True))
'''
    inspect = _run(
        _native_command("-c", inspect_code),
        env=_safe_env(),
    )
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M019 dataset failed integrity/overlap inspection",
            "export": export,
            "inspect": inspect,
        }

    try:
        summary = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse M019 dataset inspection") from exc

    expected = set(M019_SYMBOLS)
    symbols_ok = set(summary.get("symbols", [])) == expected
    range_ok = summary.get("requested_range") == {
        "from_utc": M019_FROM_UTC,
        "to_utc": M019_TO_UTC,
    }
    ask_ok = all(
        summary.get("m1_rows", {}).get(symbol, 0) > 0
        and summary.get("ask_rows", {}).get(symbol)
        == summary.get("m1_rows", {}).get(symbol)
        for symbol in M019_SYMBOLS
    )
    native_ok = all(
        summary.get("native_rows", {}).get(symbol, {}).get("M5", 0) > 0
        and summary.get("native_rows", {}).get(symbol, {}).get("M15", 0) > 0
        for symbol in M019_SYMBOLS
    )
    overlap_ok = all(
        summary.get("overlap_with_m016", {}).get(symbol, {}).get(label)
        is True
        for symbol in M019_SYMBOLS
        for label in ("M1", "M5", "M15", "ASK_M1")
    )

    return {
        "ok": bool(
            symbols_ok and range_ok and ask_ok and native_ok and overlap_ok
        ),
        "manifest": str(M019_MANIFEST.relative_to(REPO)),
        "dataset": summary,
        "overlap_with_m016_identical": overlap_ok,
        "export": export,
        "inspect": inspect,
        "wine_python": wine_python,
        "discovery": discovery,
    }


def _m019_monthly_trade_stats(trades):
    grouped = {}
    for trade in trades:
        month = str(trade.get("entry_time_utc", ""))[:7]
        if not month:
            month = "unknown"
        grouped.setdefault(month, []).append(trade)

    output = {}
    for month in sorted(grouped):
        rows = grouped[month]
        spreads = [
            float(row["entry_spread"]["spread_points"])
            for row in rows
            if row.get("entry_spread")
            and row["entry_spread"].get("spread_points") is not None
        ]
        spreads_sorted = sorted(spreads)
        count = len(spreads_sorted)
        if count == 0:
            spread_summary = {
                "count": 0,
                "mean": None,
                "median": None,
                "maximum": None,
            }
        else:
            middle = count // 2
            median = (
                spreads_sorted[middle]
                if count % 2
                else (
                    spreads_sorted[middle - 1]
                    + spreads_sorted[middle]
                ) / 2.0
            )
            spread_summary = {
                "count": count,
                "mean": sum(spreads_sorted) / count,
                "median": median,
                "maximum": max(spreads_sorted),
            }

        output[month] = {
            "closed_trades": len(rows),
            "wins": sum(row.get("outcome") == "win" for row in rows),
            "losses": sum(row.get("outcome") == "loss" for row in rows),
            "flats": sum(row.get("outcome") == "flat" for row in rows),
            "net_realized_pl": sum(
                float(row.get("net_realized_pl", 0.0)) for row in rows
            ),
            "entry_spread_points": spread_summary,
        }
    return output


def broader_history_m018_regression_pair():
    """Prove M019 replay infrastructure preserves accepted M018 bytes."""

    _require_m019_branch()
    if not FIRST_BASELINE_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M016 dataset manifest is missing",
        }

    outputs = (
        M019_REGRESSION_DIAGNOSTIC_A,
        M019_REGRESSION_DIAGNOSTIC_B,
        M019_REGRESSION_BASELINE_A,
        M019_REGRESSION_BASELINE_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    runs = []
    elapsed = []
    for diagnostic_output, baseline_output in (
        (M019_REGRESSION_DIAGNOSTIC_A, M019_REGRESSION_BASELINE_A),
        (M019_REGRESSION_DIAGNOSTIC_B, M019_REGRESSION_BASELINE_B),
    ):
        started = time.monotonic()
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.diagnostics",
                "--manifest",
                str(FIRST_BASELINE_MANIFEST.relative_to(REPO)),
                "--output",
                str(diagnostic_output.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        elapsed.append(time.monotonic() - started)
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M019 M018-regression replay failed",
                "elapsed_seconds": elapsed,
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M019 regression output missing",
            "elapsed_seconds": elapsed,
            "runs": runs,
        }

    baseline_sha_a = _sha256(M019_REGRESSION_BASELINE_A)
    baseline_sha_b = _sha256(M019_REGRESSION_BASELINE_B)
    diagnostic_sha_a = _sha256(M019_REGRESSION_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M019_REGRESSION_DIAGNOSTIC_B)

    baseline_identical = (
        M019_REGRESSION_BASELINE_A.read_bytes()
        == M019_REGRESSION_BASELINE_B.read_bytes()
    )
    diagnostic_identical = (
        M019_REGRESSION_DIAGNOSTIC_A.read_bytes()
        == M019_REGRESSION_DIAGNOSTIC_B.read_bytes()
    )
    baseline_preserved = (
        baseline_sha_a == ACCEPTED_M018_BASELINE_SHA256
        and baseline_sha_b == ACCEPTED_M018_BASELINE_SHA256
    )
    diagnostic_preserved = (
        diagnostic_sha_a == ACCEPTED_M018_DIAGNOSTIC_SHA256
        and diagnostic_sha_b == ACCEPTED_M018_DIAGNOSTIC_SHA256
    )

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and baseline_preserved
            and diagnostic_preserved
        ),
        "baseline_reports_identical": baseline_identical,
        "baseline_preserved": baseline_preserved,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "accepted_m018_baseline_sha256": ACCEPTED_M018_BASELINE_SHA256,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_preserved": diagnostic_preserved,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "accepted_m018_diagnostic_sha256": ACCEPTED_M018_DIAGNOSTIC_SHA256,
        "elapsed_seconds": elapsed,
        "total_elapsed_seconds": sum(elapsed),
        "runs": runs,
    }


def broader_history_run_pair():
    _require_m019_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M019 dataset manifest is missing; export first",
        }

    outputs = (
        M019_DIAGNOSTIC_A,
        M019_DIAGNOSTIC_B,
        M019_BASELINE_A,
        M019_BASELINE_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for diagnostic_output, baseline_output in (
        (M019_DIAGNOSTIC_A, M019_BASELINE_A),
        (M019_DIAGNOSTIC_B, M019_BASELINE_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.diagnostics",
                "--manifest",
                str(M019_MANIFEST.relative_to(REPO)),
                "--output",
                str(diagnostic_output.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M019 broader diagnostic replay failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M019 replay output missing after successful command",
            "runs": runs,
        }

    baseline_bytes_a = M019_BASELINE_A.read_bytes()
    baseline_bytes_b = M019_BASELINE_B.read_bytes()
    diagnostic_bytes_a = M019_DIAGNOSTIC_A.read_bytes()
    diagnostic_bytes_b = M019_DIAGNOSTIC_B.read_bytes()

    baseline_sha_a = _sha256(M019_BASELINE_A)
    baseline_sha_b = _sha256(M019_BASELINE_B)
    diagnostic_sha_a = _sha256(M019_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M019_DIAGNOSTIC_B)

    baseline_identical = (
        baseline_bytes_a == baseline_bytes_b
        and baseline_sha_a == baseline_sha_b
    )
    diagnostic_identical = (
        diagnostic_bytes_a == diagnostic_bytes_b
        and diagnostic_sha_a == diagnostic_sha_b
    )

    baseline = json.loads(baseline_bytes_a.decode("utf-8"))
    diagnostic = json.loads(diagnostic_bytes_a.decode("utf-8"))
    trades = diagnostic.get("trades", [])

    target_direction_violations = []
    negative_take_profit = []
    for trade in trades:
        protection = trade.get("initial_protection") or {}
        target = protection.get("applied_tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        if target is not None and entry is not None:
            crossed = (
                side == "BUY" and float(target) <= float(entry)
            ) or (
                side == "SELL" and float(target) >= float(entry)
            )
            if crossed:
                target_direction_violations.append(
                    int(trade["position_ticket"])
                )
        if (
            trade.get("exit_reason") == "take_profit"
            and float(trade.get("net_realized_pl", 0.0)) < 0
        ):
            negative_take_profit.append(
                {
                    "ticket": int(trade["position_ticket"]),
                    "symbol": trade["symbol"],
                    "side": side,
                    "net_realized_pl": float(trade["net_realized_pl"]),
                }
            )

    analysis = diagnostic.get("analysis", {})
    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_after == artifacts_before

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and not target_direction_violations
            and not negative_take_profit
            and no_new_strategy_artifacts
        ),
        "baseline_reports_identical": baseline_identical,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "aggregate": baseline.get("aggregate"),
        "per_symbol": baseline.get("per_symbol"),
        "by_entry_month": _m019_monthly_trade_stats(trades),
        "analysis": {
            "by_symbol": analysis.get("by_symbol"),
            "by_side": analysis.get("by_side"),
            "by_entry_utc_bucket": analysis.get("by_entry_utc_bucket"),
            "by_exit_reason": analysis.get("by_exit_reason"),
            "spread_by_outcome": analysis.get("spread_by_outcome"),
            "conversion_routes": analysis.get("conversion_routes"),
            "protection": analysis.get("protection"),
            "loss_clustering": {
                key: value
                for key, value in (
                    analysis.get("loss_clustering") or {}
                ).items()
                if key != "streaks"
            },
            "drawdown_episode_count": analysis.get(
                "drawdown_episode_count"
            ),
            "deepest_drawdown_episodes": analysis.get(
                "deepest_drawdown_episodes"
            ),
        },
        "target_direction_violation_count": len(
            target_direction_violations
        ),
        "target_direction_violation_tickets": target_direction_violations,
        "negative_take_profit_count": len(negative_take_profit),
        "negative_take_profit_trades": negative_take_profit,
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "runs": runs,
    }




def controlled_experiment_control_pair():
    """Prove the M020 harness reproduces accepted M019 control bytes."""

    _require_m020_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 dataset manifest is missing",
        }

    outputs = (
        M020_CONTROL_BASELINE_A,
        M020_CONTROL_BASELINE_B,
        M020_CONTROL_DIAGNOSTIC_A,
        M020_CONTROL_DIAGNOSTIC_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    runs = []
    for baseline_output, diagnostic_output in (
        (M020_CONTROL_BASELINE_A, M020_CONTROL_DIAGNOSTIC_A),
        (M020_CONTROL_BASELINE_B, M020_CONTROL_DIAGNOSTIC_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.experiments",
                "--manifest",
                str(M019_MANIFEST.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--diagnostic-output",
                str(diagnostic_output.relative_to(REPO)),
                "--expected-baseline-sha256",
                ACCEPTED_M019_BASELINE_SHA256,
                "--expected-diagnostic-sha256",
                ACCEPTED_M019_DIAGNOSTIC_SHA256,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M020 control harness failed accepted-M019 gate",
                "runs": runs,
            }

    baseline_sha_a = _sha256(M020_CONTROL_BASELINE_A)
    baseline_sha_b = _sha256(M020_CONTROL_BASELINE_B)
    diagnostic_sha_a = _sha256(M020_CONTROL_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M020_CONTROL_DIAGNOSTIC_B)

    baseline_identical = (
        M020_CONTROL_BASELINE_A.read_bytes()
        == M020_CONTROL_BASELINE_B.read_bytes()
    )
    diagnostic_identical = (
        M020_CONTROL_DIAGNOSTIC_A.read_bytes()
        == M020_CONTROL_DIAGNOSTIC_B.read_bytes()
    )
    baseline_preserved = (
        baseline_sha_a == ACCEPTED_M019_BASELINE_SHA256
        and baseline_sha_b == ACCEPTED_M019_BASELINE_SHA256
    )
    diagnostic_preserved = (
        diagnostic_sha_a == ACCEPTED_M019_DIAGNOSTIC_SHA256
        and diagnostic_sha_b == ACCEPTED_M019_DIAGNOSTIC_SHA256
    )

    first_payload = None
    try:
        first_payload = json.loads(
            runs[0]["stdout"].strip().splitlines()[-1]
        )
    except (json.JSONDecodeError, IndexError):
        first_payload = None

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and baseline_preserved
            and diagnostic_preserved
        ),
        "baseline_reports_identical": baseline_identical,
        "baseline_preserved": baseline_preserved,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "accepted_m019_baseline_sha256": ACCEPTED_M019_BASELINE_SHA256,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_preserved": diagnostic_preserved,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "accepted_m019_diagnostic_sha256": ACCEPTED_M019_DIAGNOSTIC_SHA256,
        "aggregate": (
            first_payload.get("aggregate")
            if isinstance(first_payload, dict)
            else None
        ),
        "runs": runs,
    }




def _m020_selected_delta(treatment, control, keys):
    return {
        key: (
            float(treatment.get(key, 0.0))
            - float(control.get(key, 0.0))
        )
        for key in keys
    }


def _m020_group_effect(treatment, control):
    names = sorted(set(control) | set(treatment))
    output = {}
    for name in names:
        control_row = control.get(name, {})
        treatment_row = treatment.get(name, {})
        output[name] = {
            "control": control_row,
            "treatment": treatment_row,
            "delta": _m020_selected_delta(
                treatment_row,
                control_row,
                (
                    "closed_trades",
                    "wins",
                    "losses",
                    "flats",
                    "net_realized_pl",
                ),
            ),
        }
    return output


def controlled_experiment_m020a_pair():
    """Run the single authorized M020-A treatment twice and compare control."""

    _require_m020_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 dataset manifest is missing",
        }

    control_outputs = (
        M020_CONTROL_BASELINE_A,
        M020_CONTROL_DIAGNOSTIC_A,
    )
    if any(not path.is_file() for path in control_outputs):
        return {
            "ok": False,
            "reason": "accepted M020 control artifacts are missing; run control pair",
        }
    if (
        _sha256(M020_CONTROL_BASELINE_A) != ACCEPTED_M019_BASELINE_SHA256
        or _sha256(M020_CONTROL_DIAGNOSTIC_A)
        != ACCEPTED_M019_DIAGNOSTIC_SHA256
    ):
        return {
            "ok": False,
            "reason": "local M020 control artifacts do not match accepted M019",
        }

    outputs = (
        M020_TREATMENT_BASELINE_A,
        M020_TREATMENT_BASELINE_B,
        M020_TREATMENT_DIAGNOSTIC_A,
        M020_TREATMENT_DIAGNOSTIC_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for baseline_output, diagnostic_output in (
        (M020_TREATMENT_BASELINE_A, M020_TREATMENT_DIAGNOSTIC_A),
        (M020_TREATMENT_BASELINE_B, M020_TREATMENT_DIAGNOSTIC_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.experiments",
                "--arm",
                "m020-a",
                "--manifest",
                str(M019_MANIFEST.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--diagnostic-output",
                str(diagnostic_output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M020-A treatment replay failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M020-A output missing after successful replay",
            "runs": runs,
        }

    baseline_identical = (
        M020_TREATMENT_BASELINE_A.read_bytes()
        == M020_TREATMENT_BASELINE_B.read_bytes()
    )
    diagnostic_identical = (
        M020_TREATMENT_DIAGNOSTIC_A.read_bytes()
        == M020_TREATMENT_DIAGNOSTIC_B.read_bytes()
    )
    baseline_sha_a = _sha256(M020_TREATMENT_BASELINE_A)
    baseline_sha_b = _sha256(M020_TREATMENT_BASELINE_B)
    diagnostic_sha_a = _sha256(M020_TREATMENT_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M020_TREATMENT_DIAGNOSTIC_B)

    control_baseline = json.loads(
        M020_CONTROL_BASELINE_A.read_text(encoding="utf-8")
    )
    control_diagnostic = json.loads(
        M020_CONTROL_DIAGNOSTIC_A.read_text(encoding="utf-8")
    )
    treatment_baseline = json.loads(
        M020_TREATMENT_BASELINE_A.read_text(encoding="utf-8")
    )
    treatment_diagnostic = json.loads(
        M020_TREATMENT_DIAGNOSTIC_A.read_text(encoding="utf-8")
    )

    treatment_trades = treatment_diagnostic.get("trades", [])
    blocked_entries = [
        {
            "ticket": int(trade["position_ticket"]),
            "symbol": trade["symbol"],
            "entry_time_utc": trade["entry_time_utc"],
        }
        for trade in treatment_trades
        if trade.get("entry_utc_bucket") == "00:00-03:59 UTC"
    ]

    target_direction_violations = []
    negative_take_profit = []
    for trade in treatment_trades:
        protection = trade.get("initial_protection") or {}
        target = protection.get("applied_tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        if target is not None and entry is not None:
            crossed = (
                side == "BUY" and float(target) <= float(entry)
            ) or (
                side == "SELL" and float(target) >= float(entry)
            )
            if crossed:
                target_direction_violations.append(
                    int(trade["position_ticket"])
                )
        if (
            trade.get("exit_reason") == "take_profit"
            and float(trade.get("net_realized_pl", 0.0)) < 0
        ):
            negative_take_profit.append(
                int(trade["position_ticket"])
            )

    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_before == artifacts_after

    control_aggregate = control_baseline.get("aggregate", {})
    treatment_aggregate = treatment_baseline.get("aggregate", {})
    control_analysis = control_diagnostic.get("analysis", {})
    treatment_analysis = treatment_diagnostic.get("analysis", {})
    control_months = _m019_monthly_trade_stats(
        control_diagnostic.get("trades", [])
    )
    treatment_months = _m019_monthly_trade_stats(treatment_trades)

    try:
        payload_a = json.loads(runs[0]["stdout"].strip().splitlines()[-1])
        payload_b = json.loads(runs[1]["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        payload_a = {}
        payload_b = {}

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and not blocked_entries
            and not target_direction_violations
            and not negative_take_profit
            and no_new_strategy_artifacts
        ),
        "experiment_id": "M020-A",
        "treatment": {
            "blocked_utc_start": "00:00:00",
            "blocked_utc_end_exclusive": "04:00:00",
            "behavior": "suppress new-entry strategy evaluation only",
        },
        "baseline_reports_identical": baseline_identical,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "blocked_entry_count": len(blocked_entries),
        "blocked_entries": blocked_entries,
        "blocked_evaluation_boundaries_a": payload_a.get(
            "blocked_evaluation_boundaries"
        ),
        "blocked_evaluation_boundaries_b": payload_b.get(
            "blocked_evaluation_boundaries"
        ),
        "target_direction_violation_count": len(
            target_direction_violations
        ),
        "negative_take_profit_count": len(negative_take_profit),
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "control": {
            "baseline_sha256": ACCEPTED_M019_BASELINE_SHA256,
            "diagnostic_sha256": ACCEPTED_M019_DIAGNOSTIC_SHA256,
            "aggregate": control_aggregate,
        },
        "treatment_result": {
            "aggregate": treatment_aggregate,
            "per_symbol": treatment_baseline.get("per_symbol"),
            "by_entry_month": treatment_months,
            "analysis": {
                "by_symbol": treatment_analysis.get("by_symbol"),
                "by_side": treatment_analysis.get("by_side"),
                "by_entry_utc_bucket": treatment_analysis.get(
                    "by_entry_utc_bucket"
                ),
                "by_exit_reason": treatment_analysis.get("by_exit_reason"),
                "spread_by_outcome": treatment_analysis.get(
                    "spread_by_outcome"
                ),
                "conversion_routes": treatment_analysis.get(
                    "conversion_routes"
                ),
                "protection": treatment_analysis.get("protection"),
                "loss_clustering": {
                    key: value
                    for key, value in (
                        treatment_analysis.get("loss_clustering") or {}
                    ).items()
                    if key != "streaks"
                },
                "drawdown_episode_count": treatment_analysis.get(
                    "drawdown_episode_count"
                ),
                "deepest_drawdown_episodes": treatment_analysis.get(
                    "deepest_drawdown_episodes"
                ),
            },
        },
        "effect": {
            "aggregate_delta": _m020_selected_delta(
                treatment_aggregate,
                control_aggregate,
                (
                    "accepted_orders",
                    "closed_trades",
                    "winning_closed_trades",
                    "losing_closed_trades",
                    "flat_closed_trades",
                    "net_realized_pl",
                    "ending_realized_balance",
                    "ending_equity",
                    "maximum_equity_drawdown",
                    "maximum_equity_drawdown_pct",
                ),
            ),
            "per_symbol": _m020_group_effect(
                treatment_baseline.get("per_symbol") or {},
                control_baseline.get("per_symbol") or {},
            ),
            "by_entry_month": _m020_group_effect(
                treatment_months,
                control_months,
            ),
            "by_side": _m020_group_effect(
                treatment_analysis.get("by_side") or {},
                control_analysis.get("by_side") or {},
            ),
        },
        "runs": runs,
    }


def controlled_experiment_m020b_diagnostic():
    """Run deterministic read-only M020-B spread-confound reporting."""

    _require_m020_branch()
    if not M020_CONTROL_DIAGNOSTIC_A.is_file():
        return {
            "ok": False,
            "reason": "accepted M020 control diagnostic is missing",
        }
    if _sha256(M020_CONTROL_DIAGNOSTIC_A) != ACCEPTED_M019_DIAGNOSTIC_SHA256:
        return {
            "ok": False,
            "reason": "M020 control diagnostic does not match accepted M019",
        }

    outputs = (M020_B_DIAGNOSTIC_A, M020_B_DIAGNOSTIC_B)
    for output in outputs:
        if output.exists():
            output.unlink()

    runs = []
    for output in outputs:
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m020_diagnostics",
                "--control-diagnostic",
                str(M020_CONTROL_DIAGNOSTIC_A.relative_to(REPO)),
                "--output",
                str(output.relative_to(REPO)),
                "--expected-control-diagnostic-sha256",
                ACCEPTED_M019_DIAGNOSTIC_SHA256,
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M020-B diagnostic command failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M020-B output missing after successful command",
            "runs": runs,
        }

    bytes_a = M020_B_DIAGNOSTIC_A.read_bytes()
    bytes_b = M020_B_DIAGNOSTIC_B.read_bytes()
    identical = bytes_a == bytes_b
    sha_a = _sha256(M020_B_DIAGNOSTIC_A)
    sha_b = _sha256(M020_B_DIAGNOSTIC_B)
    report = json.loads(bytes_a.decode("utf-8"))

    return {
        "ok": bool(
            identical
            and report.get("strategy_behavior_changed") is False
            and report.get("source_control_diagnostic_sha256")
            == ACCEPTED_M019_DIAGNOSTIC_SHA256
        ),
        "diagnostic_id": "M020-B",
        "strategy_behavior_changed": report.get("strategy_behavior_changed"),
        "source_control_diagnostic_sha256": report.get(
            "source_control_diagnostic_sha256"
        ),
        "outputs_identical": identical,
        "output_sha256_a": sha_a,
        "output_sha256_b": sha_b,
        "blocked_session": report.get("blocked_session"),
        "outside_blocked_session": report.get("outside_blocked_session"),
        "matched_spread_band_comparison": report.get(
            "matched_spread_band_comparison"
        ),
        "runs": runs,
    }


def controlled_experiment_m020c_pair():
    """Run deterministic causal decision-time spread diagnostics twice."""

    _require_m020_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 dataset manifest is missing",
        }

    outputs = (
        M020_C_BASELINE_A,
        M020_C_BASELINE_B,
        M020_C_DIAGNOSTIC_A,
        M020_C_DIAGNOSTIC_B,
        M020_C_DECISION_A,
        M020_C_DECISION_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for baseline_output, diagnostic_output, decision_output in (
        (M020_C_BASELINE_A, M020_C_DIAGNOSTIC_A, M020_C_DECISION_A),
        (M020_C_BASELINE_B, M020_C_DIAGNOSTIC_B, M020_C_DECISION_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m020_decision_spread",
                "--manifest",
                str(M019_MANIFEST.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--diagnostic-output",
                str(diagnostic_output.relative_to(REPO)),
                "--output",
                str(decision_output.relative_to(REPO)),
                "--expected-baseline-sha256",
                ACCEPTED_M019_BASELINE_SHA256,
                "--expected-diagnostic-sha256",
                ACCEPTED_M019_DIAGNOSTIC_SHA256,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M020-C decision-spread replay failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M020-C output missing after successful replay",
            "runs": runs,
        }

    baseline_sha_a = _sha256(M020_C_BASELINE_A)
    baseline_sha_b = _sha256(M020_C_BASELINE_B)
    diagnostic_sha_a = _sha256(M020_C_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M020_C_DIAGNOSTIC_B)
    decision_sha_a = _sha256(M020_C_DECISION_A)
    decision_sha_b = _sha256(M020_C_DECISION_B)

    baseline_identical = (
        M020_C_BASELINE_A.read_bytes() == M020_C_BASELINE_B.read_bytes()
    )
    diagnostic_identical = (
        M020_C_DIAGNOSTIC_A.read_bytes()
        == M020_C_DIAGNOSTIC_B.read_bytes()
    )
    decision_identical = (
        M020_C_DECISION_A.read_bytes() == M020_C_DECISION_B.read_bytes()
    )
    control_preserved = (
        baseline_sha_a == ACCEPTED_M019_BASELINE_SHA256
        and baseline_sha_b == ACCEPTED_M019_BASELINE_SHA256
        and diagnostic_sha_a == ACCEPTED_M019_DIAGNOSTIC_SHA256
        and diagnostic_sha_b == ACCEPTED_M019_DIAGNOSTIC_SHA256
    )

    report = json.loads(M020_C_DECISION_A.read_text(encoding="utf-8"))
    reconciliation = report.get("reconciliation") or {}
    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_before == artifacts_after

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and decision_identical
            and control_preserved
            and report.get("strategy_behavior_changed") is False
            and reconciliation.get("missing_decision_spread_rows") == 0
            and no_new_strategy_artifacts
        ),
        "diagnostic_id": "M020-C",
        "strategy_behavior_changed": report.get("strategy_behavior_changed"),
        "baseline_reports_identical": baseline_identical,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "control_hashes_preserved": control_preserved,
        "decision_reports_identical": decision_identical,
        "decision_sha256_a": decision_sha_a,
        "decision_sha256_b": decision_sha_b,
        "reconciliation": reconciliation,
        "decision_spread_percentiles": report.get(
            "decision_spread_percentiles"
        ),
        "fill_spread_percentiles": report.get("fill_spread_percentiles"),
        "decision_fill_pearson_correlation": report.get(
            "decision_fill_pearson_correlation"
        ),
        "by_decision_spread_band": report.get("by_decision_spread_band"),
        "decision_to_fill_band_transitions": report.get(
            "decision_to_fill_band_transitions"
        ),
        "by_symbol_and_decision_spread_band": report.get(
            "by_symbol_and_decision_spread_band"
        ),
        "by_side_and_decision_spread_band": report.get(
            "by_side_and_decision_spread_band"
        ),
        "by_entry_month_and_decision_spread_band": report.get(
            "by_entry_month_and_decision_spread_band"
        ),
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "runs": runs,
    }


def controlled_experiment_m020d_pair():
    """Run deterministic M020-D decision-time spread treatment twice."""

    _require_m020_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 dataset manifest is missing",
        }
    if (
        not M020_CONTROL_BASELINE_A.is_file()
        or not M020_CONTROL_DIAGNOSTIC_A.is_file()
    ):
        return {
            "ok": False,
            "reason": "M020 control artifacts are missing; run control pair",
        }
    if (
        _sha256(M020_CONTROL_BASELINE_A) != ACCEPTED_M019_BASELINE_SHA256
        or _sha256(M020_CONTROL_DIAGNOSTIC_A)
        != ACCEPTED_M019_DIAGNOSTIC_SHA256
    ):
        return {
            "ok": False,
            "reason": "M020 control artifacts do not match accepted M019",
        }

    outputs = (
        M020_D_BASELINE_A,
        M020_D_BASELINE_B,
        M020_D_DIAGNOSTIC_A,
        M020_D_DIAGNOSTIC_B,
        M020_D_EVIDENCE_A,
        M020_D_EVIDENCE_B,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    runs = []
    for baseline_output, diagnostic_output, evidence_output in (
        (M020_D_BASELINE_A, M020_D_DIAGNOSTIC_A, M020_D_EVIDENCE_A),
        (M020_D_BASELINE_B, M020_D_DIAGNOSTIC_B, M020_D_EVIDENCE_B),
    ):
        result = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m020_spread_treatment",
                "--manifest",
                str(M019_MANIFEST.relative_to(REPO)),
                "--baseline-output",
                str(baseline_output.relative_to(REPO)),
                "--diagnostic-output",
                str(diagnostic_output.relative_to(REPO)),
                "--evidence-output",
                str(evidence_output.relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        runs.append(result)
        if result["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M020-D treatment replay failed",
                "runs": runs,
            }

    if any(not output.is_file() for output in outputs):
        return {
            "ok": False,
            "reason": "M020-D output missing after successful replay",
            "runs": runs,
        }

    baseline_identical = (
        M020_D_BASELINE_A.read_bytes() == M020_D_BASELINE_B.read_bytes()
    )
    diagnostic_identical = (
        M020_D_DIAGNOSTIC_A.read_bytes() == M020_D_DIAGNOSTIC_B.read_bytes()
    )
    evidence_identical = (
        M020_D_EVIDENCE_A.read_bytes() == M020_D_EVIDENCE_B.read_bytes()
    )

    baseline_sha_a = _sha256(M020_D_BASELINE_A)
    baseline_sha_b = _sha256(M020_D_BASELINE_B)
    diagnostic_sha_a = _sha256(M020_D_DIAGNOSTIC_A)
    diagnostic_sha_b = _sha256(M020_D_DIAGNOSTIC_B)
    evidence_sha_a = _sha256(M020_D_EVIDENCE_A)
    evidence_sha_b = _sha256(M020_D_EVIDENCE_B)

    control_baseline = json.loads(
        M020_CONTROL_BASELINE_A.read_text(encoding="utf-8")
    )
    control_diagnostic = json.loads(
        M020_CONTROL_DIAGNOSTIC_A.read_text(encoding="utf-8")
    )
    treatment_baseline = json.loads(
        M020_D_BASELINE_A.read_text(encoding="utf-8")
    )
    treatment_diagnostic = json.loads(
        M020_D_DIAGNOSTIC_A.read_text(encoding="utf-8")
    )
    evidence = json.loads(M020_D_EVIDENCE_A.read_text(encoding="utf-8"))

    treatment_trades = treatment_diagnostic.get("trades", [])
    target_direction_violations = []
    negative_take_profit = []
    for trade in treatment_trades:
        protection = trade.get("initial_protection") or {}
        target = protection.get("applied_tp")
        entry = trade.get("entry_price")
        side = trade.get("side")
        if target is not None and entry is not None:
            crossed = (
                side == "BUY" and float(target) <= float(entry)
            ) or (
                side == "SELL" and float(target) >= float(entry)
            )
            if crossed:
                target_direction_violations.append(
                    int(trade["position_ticket"])
                )
        if (
            trade.get("exit_reason") == "take_profit"
            and float(trade.get("net_realized_pl", 0.0)) < 0
        ):
            negative_take_profit.append(int(trade["position_ticket"]))

    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_before == artifacts_after

    control_aggregate = control_baseline.get("aggregate", {})
    treatment_aggregate = treatment_baseline.get("aggregate", {})
    control_analysis = control_diagnostic.get("analysis", {})
    treatment_analysis = treatment_diagnostic.get("analysis", {})
    control_months = _m019_monthly_trade_stats(
        control_diagnostic.get("trades", [])
    )
    treatment_months = _m019_monthly_trade_stats(treatment_trades)

    return {
        "ok": bool(
            baseline_identical
            and diagnostic_identical
            and evidence_identical
            and evidence.get("accepted_spread_violation_count") == 0
            and not target_direction_violations
            and not negative_take_profit
            and no_new_strategy_artifacts
        ),
        "experiment_id": "M020-D",
        "treatment": evidence.get("treatment"),
        "baseline_reports_identical": baseline_identical,
        "baseline_sha256_a": baseline_sha_a,
        "baseline_sha256_b": baseline_sha_b,
        "diagnostics_identical": diagnostic_identical,
        "diagnostic_sha256_a": diagnostic_sha_a,
        "diagnostic_sha256_b": diagnostic_sha_b,
        "evidence_identical": evidence_identical,
        "evidence_sha256_a": evidence_sha_a,
        "evidence_sha256_b": evidence_sha_b,
        "rejected_order_count": evidence.get("rejected_order_count"),
        "accepted_spread_violation_count": evidence.get(
            "accepted_spread_violation_count"
        ),
        "maximum_accepted_decision_spread_points": evidence.get(
            "maximum_accepted_decision_spread_points"
        ),
        "target_direction_violation_count": len(
            target_direction_violations
        ),
        "negative_take_profit_count": len(negative_take_profit),
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "control": {
            "baseline_sha256": ACCEPTED_M019_BASELINE_SHA256,
            "diagnostic_sha256": ACCEPTED_M019_DIAGNOSTIC_SHA256,
            "aggregate": control_aggregate,
        },
        "treatment_result": {
            "aggregate": treatment_aggregate,
            "per_symbol": treatment_baseline.get("per_symbol"),
            "by_entry_month": treatment_months,
            "analysis": {
                "by_symbol": treatment_analysis.get("by_symbol"),
                "by_side": treatment_analysis.get("by_side"),
                "by_exit_reason": treatment_analysis.get("by_exit_reason"),
                "spread_by_outcome": treatment_analysis.get(
                    "spread_by_outcome"
                ),
            },
        },
        "effect": {
            "aggregate_delta": _m020_selected_delta(
                treatment_aggregate,
                control_aggregate,
                (
                    "accepted_orders",
                    "closed_trades",
                    "winning_closed_trades",
                    "losing_closed_trades",
                    "flat_closed_trades",
                    "net_realized_pl",
                    "ending_realized_balance",
                    "ending_equity",
                    "maximum_equity_drawdown",
                    "maximum_equity_drawdown_pct",
                ),
            ),
            "per_symbol": _m020_group_effect(
                treatment_baseline.get("per_symbol") or {},
                control_baseline.get("per_symbol") or {},
            ),
            "by_entry_month": _m020_group_effect(
                treatment_months,
                control_months,
            ),
            "by_side": _m020_group_effect(
                treatment_analysis.get("by_side") or {},
                control_analysis.get("by_side") or {},
            ),
        },
        "runs": runs,
    }


def _m021_readiness_payload():
    code = (
        "import json;"
        "from datetime import datetime,timezone;"
        "from mamba2.backtest.m021_forward_validation import readiness;"
        "print(json.dumps(readiness("
        "now_utc=datetime.now(timezone.utc),"
        f"cutoff_utc={M021_PRIMARY_TO_UTC!r}"
        "),sort_keys=True))"
    )
    run_result = _run(_native_command("-c", code), env=_safe_env())
    if run_result["exit_code"] != 0:
        return None, run_result
    try:
        payload = json.loads(run_result["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return None, run_result
    return payload, run_result


def m021_forward_readiness():
    _require_m021_branch()
    payload, run_result = _m021_readiness_payload()
    if payload is None:
        return {
            "ok": False,
            "reason": "unable to evaluate frozen M021 readiness",
            "run": run_result,
        }
    return {
        "ok": True,
        "protocol_gate": payload,
        "refused_before_cutoff": not bool(payload.get("ready")),
        "economic_results_computed": False,
        "run": run_result,
    }


def m021_historical_regression():
    _require_m021_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 dataset manifest is missing",
        }

    outputs = (
        M021_REG_CONTROL_BASELINE,
        M021_REG_CONTROL_DIAGNOSTIC,
        M021_REG_CANDIDATE_BASELINE,
        M021_REG_CANDIDATE_DIAGNOSTIC,
        M021_REG_CANDIDATE_EVIDENCE,
    )
    for output in outputs:
        if output.exists():
            output.unlink()

    artifacts_before = _artifact_snapshot()
    control = _run(
        _native_command(
            "-m",
            "mamba2.backtest.experiments",
            "--manifest",
            str(M019_MANIFEST.relative_to(REPO)),
            "--baseline-output",
            str(M021_REG_CONTROL_BASELINE.relative_to(REPO)),
            "--diagnostic-output",
            str(M021_REG_CONTROL_DIAGNOSTIC.relative_to(REPO)),
            "--arm",
            "control",
            "--expected-baseline-sha256",
            ACCEPTED_M019_BASELINE_SHA256,
            "--expected-diagnostic-sha256",
            ACCEPTED_M019_DIAGNOSTIC_SHA256,
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if control["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M021 historical control regression failed",
            "control": control,
        }

    candidate = _run(
        _native_command(
            "-m",
            "mamba2.backtest.m020_spread_treatment",
            "--manifest",
            str(M019_MANIFEST.relative_to(REPO)),
            "--baseline-output",
            str(M021_REG_CANDIDATE_BASELINE.relative_to(REPO)),
            "--diagnostic-output",
            str(M021_REG_CANDIDATE_DIAGNOSTIC.relative_to(REPO)),
            "--evidence-output",
            str(M021_REG_CANDIDATE_EVIDENCE.relative_to(REPO)),
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if candidate["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M021 historical M020-D regression failed",
            "control": control,
            "candidate": candidate,
        }

    observed = {
        "control_baseline": _sha256(M021_REG_CONTROL_BASELINE),
        "control_diagnostic": _sha256(M021_REG_CONTROL_DIAGNOSTIC),
        "candidate_baseline": _sha256(M021_REG_CANDIDATE_BASELINE),
        "candidate_diagnostic": _sha256(M021_REG_CANDIDATE_DIAGNOSTIC),
        "candidate_evidence": _sha256(M021_REG_CANDIDATE_EVIDENCE),
    }
    expected = {
        "control_baseline": ACCEPTED_M019_BASELINE_SHA256,
        "control_diagnostic": ACCEPTED_M019_DIAGNOSTIC_SHA256,
        "candidate_baseline": ACCEPTED_M020_D_BASELINE_SHA256,
        "candidate_diagnostic": ACCEPTED_M020_D_DIAGNOSTIC_SHA256,
        "candidate_evidence": ACCEPTED_M020_D_EVIDENCE_SHA256,
    }
    artifacts_after = _artifact_snapshot()
    no_new_strategy_artifacts = artifacts_before == artifacts_after
    hashes_preserved = observed == expected
    return {
        "ok": bool(hashes_preserved and no_new_strategy_artifacts),
        "hashes_preserved": hashes_preserved,
        "observed": observed,
        "expected": expected,
        "no_new_strategy_artifacts": no_new_strategy_artifacts,
        "control": control,
        "candidate": candidate,
    }


def m021_primary_export():
    _require_m021_branch()
    payload, readiness_run = _m021_readiness_payload()
    if payload is None:
        return {
            "ok": False,
            "reason": "unable to evaluate M021 readiness",
            "run": readiness_run,
        }
    if not payload.get("ready"):
        return {
            "ok": True,
            "ready": False,
            "refused_before_cutoff": True,
            "export_attempted": False,
            "economic_results_computed": False,
            "protocol_gate": payload,
            "run": readiness_run,
        }

    output_dir = _ensure_baseline_path(M021_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": "M021 primary dataset directory already exists",
            "path": str(output_dir.relative_to(REPO)),
        }

    wine_python, discovery = _select_wine_python()
    wine = _wine()
    command = [
        wine,
        wine_python,
        "-m",
        "mamba2.backtest.mt5_dataset",
        "--symbols",
        *M019_SYMBOLS,
        "--timeframes",
        "M1",
        "M5",
        "M15",
        "--from-utc",
        M021_FROM_UTC,
        "--to-utc",
        M021_PRIMARY_TO_UTC,
        "--output-dir",
        str(M021_DIR.relative_to(REPO)),
        "--include-tick-ask",
        "--tick-chunk-minutes",
        "1440",
        "--rate-chunk-days",
        "7",
    ]
    export = _run(command, env=_safe_env(wine=True))
    if export["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M021 read-only MT5 export failed",
            "export": export,
            "discovery": discovery,
        }
    if not M021_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M021 export completed without manifest",
            "export": export,
        }

    inspect_code = (
        "import json,hashlib;"
        "from pathlib import Path;"
        "from mamba2.backtest.mt5_dataset import load_mt5_dataset;"
        f"p=Path({str(M021_MANIFEST)!r});"
        "d=load_mt5_dataset(p);"
        "h=hashlib.sha256(p.read_bytes()).hexdigest();"
        "print(json.dumps({"
        "'manifest_sha256':h,"
        "'account_currency':d.account_currency,"
        "'symbols':sorted(d.m1_bars),"
        "'m1_rows':{s:len(d.m1_bars[s]) for s in sorted(d.m1_bars)},"
        "'ask_rows':{s:len(d.ask_m1_bars[s]) for s in sorted(d.ask_m1_bars)},"
        "'native_rows':{s:{tf:len(df) for tf,df in sorted(d.native_timeframe_bars[s].items()) "
        "for s in sorted(d.native_timeframe_bars)},"
        "'requested_range':d.manifest.get('requested_range')"
        "},sort_keys=True))"
    )
    inspect = _run(_native_command("-c", inspect_code), env=_safe_env())
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M021 exported dataset failed integrity inspection",
            "export": export,
            "inspect": inspect,
        }
    try:
        summary = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {
            "ok": False,
            "reason": "unable to parse M021 dataset inspection",
            "inspect": inspect,
        }

    range_ok = summary.get("requested_range") == {
        "from_utc": M021_FROM_UTC,
        "to_utc": M021_PRIMARY_TO_UTC,
    }
    symbols_ok = set(summary.get("symbols", [])) == set(M019_SYMBOLS)
    ask_ok = all(
        summary.get("m1_rows", {}).get(symbol, 0) > 0
        and summary.get("ask_rows", {}).get(symbol)
        == summary.get("m1_rows", {}).get(symbol)
        for symbol in M019_SYMBOLS
    )
    native_ok = all(
        summary.get("native_rows", {}).get(symbol, {}).get("M5", 0) > 0
        and summary.get("native_rows", {}).get(symbol, {}).get("M15", 0) > 0
        for symbol in M019_SYMBOLS
    )
    return {
        "ok": bool(range_ok and symbols_ok and ask_ok and native_ok),
        "ready": True,
        "manifest": str(M021_MANIFEST.relative_to(REPO)),
        "dataset": summary,
        "economic_results_computed": False,
        "export": export,
        "inspect": inspect,
        "wine_python": wine_python,
        "discovery": discovery,
    }


def m021_primary_pair():
    _require_m021_branch()
    payload, readiness_run = _m021_readiness_payload()
    if payload is None:
        return {
            "ok": False,
            "reason": "unable to evaluate M021 readiness",
            "run": readiness_run,
        }
    if not payload.get("ready"):
        return {
            "ok": True,
            "ready": False,
            "refused_before_cutoff": True,
            "pair_attempted": False,
            "economic_results_computed": False,
            "protocol_gate": payload,
            "run": readiness_run,
        }
    if not M021_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M021 primary manifest is missing; export first",
        }

    regression = m021_historical_regression()
    if not regression.get("ok"):
        return {
            "ok": False,
            "reason": "M021 historical regression gate failed",
            "regression": regression,
        }

    result = _run(
        _native_command(
            "-m",
            "mamba2.backtest.m021_forward_validation",
            "--manifest",
            str(M021_MANIFEST.relative_to(REPO)),
            "--output-dir",
            str(M021_OUTPUT_DIR.relative_to(REPO)),
            "--cutoff-utc",
            M021_PRIMARY_TO_UTC,
            "--now-utc",
            payload["now_utc"],
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if result["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M021 primary paired replay failed",
            "regression": regression,
            "run": result,
        }
    try:
        summary = json.loads(result["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {
            "ok": False,
            "reason": "unable to parse M021 paired replay result",
            "run": result,
        }
    return {
        "ok": bool(summary.get("ok")),
        "ready": True,
        "historical_regression": {
            "hashes_preserved": regression.get("hashes_preserved"),
            "observed": regression.get("observed"),
        },
        "pair": summary,
        "run": result,
    }




def m022_phase1_stochastic_family():
    """Run the frozen nine-arm stochastic family on development only."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_REFERENCE_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 reference pair must be accepted before stochastic family",
            "feature_sha": feature_sha,
        }

    reference_summary_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_summary_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is missing",
            "feature_sha": feature_sha,
        }
    reference = json.loads(reference_summary_path.read_text(encoding="utf-8"))

    output_root = _ensure_baseline_path(M022_PHASE1_STOCHASTIC_DIR)
    if output_root.exists():
        return {
            "ok": False,
            "reason": "M022 stochastic family output directory already exists",
            "feature_sha": feature_sha,
            "path": str(output_root.relative_to(REPO)),
        }
    output_root.mkdir(parents=True)

    tuples = (
        (9, 3, 3),
        (10, 4, 4),
        (10, 6, 6),
        (14, 3, 3),
        (14, 5, 5),
        (14, 7, 7),
        (21, 5, 5),
        (21, 7, 7),
        (28, 7, 7),
    )
    results = []
    for k, d, slowing in tuples:
        label = f"{k}-{d}-{slowing}"
        arm_dir = output_root / label
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "stochastic",
                "--value",
                f"{k}/{d}/{slowing}",
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return {
                "ok": False,
                "reason": f"M022 stochastic arm {k}/{d}/{slowing} failed",
                "feature_branch": "strategy-parameter-research",
                "feature_sha": feature_sha,
                "completed_arms": results,
                "failed_run": {
                    "tuple": [k, d, slowing],
                    "exit_code": run["exit_code"],
                    "stdout": _bounded(run["stdout"]),
                    "stderr": _bounded(run["stderr"]),
                },
            }
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return {
                "ok": False,
                "reason": f"unable to parse stochastic arm {k}/{d}/{slowing}",
                "feature_sha": feature_sha,
                "completed_arms": results,
            }

        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
        )
        if not arm_ok:
            return {
                "ok": False,
                "reason": f"M022 stochastic arm {k}/{d}/{slowing} failed invariants",
                "feature_sha": feature_sha,
                "completed_arms": results,
                "failed_payload": payload,
            }

        results.append({
            "tuple": [k, d, slowing],
            "experiment_id": payload.get("experiment_id"),
            "baseline_sha256": payload.get("baseline_sha256"),
            "diagnostic_sha256": payload.get("diagnostic_sha256"),
            "summary_sha256": payload.get("summary_sha256"),
            "aggregate": summary.get("aggregate"),
            "per_symbol": summary.get("per_symbol"),
            "by_side": summary.get("by_side"),
            "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
            "protection": summary.get("protection"),
            "rejections": summary.get("rejections"),
            "tp_safety": tp,
        })

    reference_fields = {
        "aggregate": reference.get("aggregate"),
        "per_symbol": reference.get("per_symbol"),
        "by_side": reference.get("by_side"),
        "by_entry_utc_bucket": reference.get("by_entry_utc_bucket"),
        "protection": reference.get("protection"),
        "rejections": reference.get("rejections"),
        "tp_safety": reference.get("tp_safety"),
    }
    current = next(row for row in results if row["tuple"] == [21, 7, 7])
    current_fields = {
        key: current.get(key)
        for key in reference_fields
    }
    reference_equivalent = current_fields == reference_fields

    return {
        "ok": bool(reference_equivalent),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "stochastic",
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
        "reference_21_7_7_economic_equivalence": reference_equivalent,
        "arms": results,
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "development",
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_reference_pair():
    """Run the frozen M022 reference on development only, twice."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    output_dir = _ensure_baseline_path(M022_PHASE1_REFERENCE_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": "M022 reference output directory already exists",
            "feature_sha": feature_sha,
            "path": str(output_dir.relative_to(REPO)),
        }

    run = _run(
        _native_command(
            "-m",
            "mamba2.backtest.parameter_research",
            "--manifest",
            str(manifest.relative_to(REPO)),
            "--output-dir",
            str(output_dir.relative_to(REPO)),
            "--family",
            "reference",
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if run["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 development reference pair failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "run": run,
        }

    try:
        payload = json.loads(run["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {
            "ok": False,
            "reason": "unable to parse M022 reference result",
            "feature_sha": feature_sha,
            "run": run,
        }

    summary = payload.get("summary") or {}
    partition = summary.get("partition") or {}
    tp_safety = summary.get("tp_safety") or {}
    aggregate = summary.get("aggregate") or {}

    partition_ok = (
        payload.get("partition") == "development"
        and partition.get("partition") == "development"
        and partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
        and partition.get("common_trading_dates_sha256")
        == "2efcd016d0d346036a33415e794903b5fea86ad610519fbda056ceb2c94feac5"
        and partition.get("start_utc") == "2025-08-25T00:00:00Z"
        and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
        and int(partition.get("common_trading_dates", 0)) == 169
    )
    safety_ok = (
        int(tp_safety.get("negative_pl_take_profit_exits", -1)) == 0
        and int(tp_safety.get("wrong_side_initial_tp", -1)) == 0
        and int(aggregate.get("remaining_open_positions", -1)) >= 0
    )
    deterministic = bool(payload.get("deterministic"))
    ok = bool(payload.get("ok") and deterministic and partition_ok and safety_ok)

    return {
        "ok": ok,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "experiment_id": payload.get("experiment_id"),
        "family": payload.get("family"),
        "value_label": payload.get("value_label"),
        "parameters": payload.get("parameters"),
        "partition": partition,
        "deterministic": deterministic,
        "baseline_sha256": payload.get("baseline_sha256"),
        "diagnostic_sha256": payload.get("diagnostic_sha256"),
        "summary_sha256": payload.get("summary_sha256"),
        "aggregate": aggregate,
        "per_symbol": summary.get("per_symbol"),
        "by_side": summary.get("by_side"),
        "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
        "protection": summary.get("protection"),
        "rejections": summary.get("rejections"),
        "tp_safety": tp_safety,
        "remaining_positions": summary.get("remaining_positions"),
        "partition_ok": partition_ok,
        "safety_ok": safety_ok,
        "cost_contract": summary.get("cost_contract"),
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "development",
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
        "run_exit_code": run["exit_code"],
    }


def m022_phase1_default_regression():
    """Hash-only regression of unchanged M019/M020-D executable semantics."""

    feature_sha = _require_m022_branch()
    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    output_dir = _ensure_baseline_path(M022_PHASE1_REGRESSION_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": "M022 Phase-1 regression directory already exists",
            "feature_sha": feature_sha,
            "path": str(output_dir.relative_to(REPO)),
        }
    output_dir.mkdir(parents=True)

    control = _run(
        _native_command(
            "-m",
            "mamba2.backtest.experiments",
            "--manifest",
            str(M019_MANIFEST.relative_to(REPO)),
            "--baseline-output",
            str(M022_PHASE1_REG_CONTROL_BASELINE.relative_to(REPO)),
            "--diagnostic-output",
            str(M022_PHASE1_REG_CONTROL_DIAGNOSTIC.relative_to(REPO)),
            "--arm",
            "control",
            "--expected-baseline-sha256",
            ACCEPTED_M019_BASELINE_SHA256,
            "--expected-diagnostic-sha256",
            ACCEPTED_M019_DIAGNOSTIC_SHA256,
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if control["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 default control no longer preserves accepted M019",
            "feature_sha": feature_sha,
            "control": control,
        }

    candidate = _run(
        _native_command(
            "-m",
            "mamba2.backtest.m020_spread_treatment",
            "--manifest",
            str(M019_MANIFEST.relative_to(REPO)),
            "--baseline-output",
            str(M022_PHASE1_REG_M020D_BASELINE.relative_to(REPO)),
            "--diagnostic-output",
            str(M022_PHASE1_REG_M020D_DIAGNOSTIC.relative_to(REPO)),
            "--evidence-output",
            str(M022_PHASE1_REG_M020D_EVIDENCE.relative_to(REPO)),
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if candidate["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 default path no longer preserves M020-D execution",
            "feature_sha": feature_sha,
            "control_exit_code": control["exit_code"],
            "candidate": candidate,
        }

    observed = {
        "m019_baseline": _sha256(M022_PHASE1_REG_CONTROL_BASELINE),
        "m019_diagnostic": _sha256(M022_PHASE1_REG_CONTROL_DIAGNOSTIC),
        "m020d_baseline": _sha256(M022_PHASE1_REG_M020D_BASELINE),
        "m020d_diagnostic": _sha256(M022_PHASE1_REG_M020D_DIAGNOSTIC),
        "m020d_evidence": _sha256(M022_PHASE1_REG_M020D_EVIDENCE),
    }
    expected = {
        "m019_baseline": ACCEPTED_M019_BASELINE_SHA256,
        "m019_diagnostic": ACCEPTED_M019_DIAGNOSTIC_SHA256,
        "m020d_baseline": ACCEPTED_M020_D_BASELINE_SHA256,
        "m020d_diagnostic": ACCEPTED_M020_D_DIAGNOSTIC_SHA256,
        "m020d_evidence": ACCEPTED_M020_D_EVIDENCE_SHA256,
    }
    preserved = observed == expected
    return {
        "ok": bool(preserved),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "hashes_preserved": preserved,
        "observed": observed,
        "expected": expected,
        "safety": {
            "economic_replay_run": True,
            "purpose": "accepted-artifact regression only",
            "parameter_result_inspected": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_tests():
    """Run fixed native tests for M022 Phase-1 research machinery."""

    feature_sha = _require_m022_branch()
    tests = [
        "tests/test_parameter_research.py",
        "tests/test_triple_cross_condition_semantics.py",
        "tests/test_backtest_baseline_reporting.py",
        "tests/test_position_manager_trailing_semantics.py",
        "tests/test_backtest_strategy_lifecycle.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
            "parameter_result_inspected": False,
        },
    }


def m022_inventory_tests():
    """Run the fixed native test gate for M022 history infrastructure."""

    feature_sha = _require_m022_branch()
    result = _pytest_native([
        "tests/test_mt5_dataset.py",
    ])
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "tests": ["tests/test_mt5_dataset.py"],
        "run": result,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_maxbars_recovery_probe():
    """Read MaxBars config state without initializing or restarting MT5."""

    feature_sha = _require_m022_branch()
    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    wine_python = _wine_windows_path(dedicated)
    if not wine_python:
        raise RuntimeError("cannot map established M022 Wine runtime")
    wine = _wine()

    probe_code = r'''
import hashlib
import json
from pathlib import Path

target = Path(r"C:\Program Files\MetaTrader 5\config\common.ini")
backup = target.with_name("common.ini.m022-maxbars-100000.backup")
if not target.is_file():
    raise RuntimeError(f"common.ini is missing: {target}")

raw = target.read_bytes()
values = []
for value in (100000, 500000):
    markers = [
        f"MaxBars={value}".encode("utf-8"),
        f"MaxBars={value}".encode("utf-16le"),
        f"MaxBars={value}".encode("utf-16be"),
    ]
    if any(marker in raw for marker in markers):
        values.append(value)

print(json.dumps({
    "target": str(target),
    "sha256": hashlib.sha256(raw).hexdigest(),
    "maxbars_markers": values,
    "backup_exists": backup.is_file(),
    "backup_sha256": (
        hashlib.sha256(backup.read_bytes()).hexdigest()
        if backup.is_file()
        else None
    ),
}, sort_keys=True), flush=True)
'''

    run = _run_process_group_bounded(
        [wine, wine_python, "-c", probe_code],
        env=_safe_env(wine=True),
        timeout_seconds=30,
    )
    payload = None
    if run["exit_code"] == 0 and run["stdout"].strip():
        payload = json.loads(run["stdout"].strip().splitlines()[-1])
    return {
        "ok": run["exit_code"] == 0 and payload is not None,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "probe": payload,
        "run": run,
        "safety": {
            "read_only": True,
            "terminal_initialized": False,
            "terminal_configuration_modified": False,
            "real_order_api_called": False,
            "economic_replay_run": False,
        },
    }


def m022_raise_mt5_maxbars():
    """Raise only MT5 MaxBars, with Wine-local backup and rollback."""

    feature_sha = _require_m022_branch()
    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    wine_python = _wine_windows_path(dedicated)
    if not wine_python:
        raise RuntimeError("cannot map established M022 Wine runtime")
    wine = _wine()

    prepare_code = r'''
import hashlib
import json
import os
from pathlib import Path

import MetaTrader5 as mt5

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed before MaxBars update")

try:
    terminal = mt5.terminal_info()
    account = mt5.account_info()
    if getattr(account, "server", None) != "MetaQuotes-Demo":
        raise RuntimeError("MaxBars update requires MetaQuotes-Demo account")

    target = Path(getattr(terminal, "path")) / "config" / "common.ini"
    backup = target.with_name("common.ini.m022-maxbars-100000.backup")
    if not target.is_file():
        raise RuntimeError(f"verified MT5 common.ini is missing: {target}")

    raw = target.read_bytes()
    patterns = [
        (b"MaxBars=100000", b"MaxBars=500000", "single-byte"),
        (
            "MaxBars=100000".encode("utf-16le"),
            "MaxBars=500000".encode("utf-16le"),
            "utf-16le",
        ),
        (
            "MaxBars=100000".encode("utf-16be"),
            "MaxBars=500000".encode("utf-16be"),
            "utf-16be",
        ),
    ]
    already = (
        b"MaxBars=500000" in raw
        or "MaxBars=500000".encode("utf-16le") in raw
        or "MaxBars=500000".encode("utf-16be") in raw
    )
    selected = None
    for old, new, encoding in patterns:
        if old in raw:
            selected = (old, new, encoding)
            break
    if selected is None and not already:
        raise RuntimeError(
            "fixed MaxBars=100000 marker not found; refusing edit"
        )

    before_sha = hashlib.sha256(raw).hexdigest()
    if not backup.exists():
        backup.write_bytes(raw)

    modified = False
    encoding = "already-500000"
    if selected is not None:
        old, new, encoding = selected
        updated = raw.replace(old, new, 1)
        temp = target.with_name("common.ini.m022.tmp")
        temp.write_bytes(updated)
        os.replace(temp, target)
        modified = True

    print(json.dumps({
        "target": str(target),
        "backup": str(backup),
        "before_sha256": before_sha,
        "encoding_match": encoding,
        "modified": modified,
        "server": getattr(account, "server", None),
        "old_maxbars_runtime": getattr(terminal, "maxbars", None),
    }, sort_keys=True), flush=True)
finally:
    mt5.shutdown()
'''

    prepare = _run_process_group_bounded(
        [wine, wine_python, "-c", prepare_code],
        env=_safe_env(wine=True),
        timeout_seconds=45,
    )
    if prepare["exit_code"] != 0 or not prepare["stdout"].strip():
        return {
            "ok": False,
            "reason": "Wine-local MaxBars preparation failed before restart",
            "feature_sha": feature_sha,
            "prepare": prepare,
        }
    prepared = json.loads(prepare["stdout"].strip().splitlines()[-1])

    kill_runs = []
    for image in ("terminal64.exe", "terminal.exe"):
        kill_runs.append(
            _run_process_group_bounded(
                [wine, "taskkill", "/F", "/IM", image],
                env=_safe_env(wine=True),
                timeout_seconds=15,
            )
        )
    time.sleep(2)

    verify_code = r'''
import json
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed after MaxBars update")

try:
    terminal = mt5.terminal_info()
    account = mt5.account_info()
    result = {
        "maxbars": getattr(terminal, "maxbars", None),
        "server": getattr(account, "server", None),
        "currency": getattr(account, "currency", None),
        "native_m1_aug_25": {},
        "runtime": list(mt5.version()) if hasattr(mt5, "version") else None,
    }
    for symbol in symbols:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"could not select {symbol}")
        rows = None
        for _attempt in range(8):
            rows = mt5.copy_rates_range(
                symbol,
                mt5.TIMEFRAME_M1,
                datetime(2025, 8, 25, tzinfo=timezone.utc),
                datetime(2025, 8, 26, tzinfo=timezone.utc),
            )
            if rows is not None and len(rows) >= 1000:
                break
            time.sleep(2)
        result["native_m1_aug_25"][symbol] = {
            "rows": 0 if rows is None else int(len(rows)),
            "first_bar_open_utc": (
                None
                if rows is None or len(rows) == 0
                else datetime.fromtimestamp(
                    int(rows[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "last_bar_open_utc": (
                None
                if rows is None or len(rows) == 0
                else datetime.fromtimestamp(
                    int(rows[-1]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "last_error": list(mt5.last_error()),
        }
    print(json.dumps(result, sort_keys=True), flush=True)
finally:
    mt5.shutdown()
'''

    verify = _run_process_group_bounded(
        [wine, wine_python, "-c", verify_code],
        env=_safe_env(wine=True),
        timeout_seconds=150,
    )
    payload = None
    if verify["exit_code"] == 0 and verify["stdout"].strip():
        payload = json.loads(verify["stdout"].strip().splitlines()[-1])

    verified = bool(
        payload
        and payload.get("maxbars") == 500000
        and payload.get("server") == "MetaQuotes-Demo"
    )

    rollback = None
    if not verified:
        for image in ("terminal64.exe", "terminal.exe"):
            _run_process_group_bounded(
                [wine, "taskkill", "/F", "/IM", image],
                env=_safe_env(wine=True),
                timeout_seconds=15,
            )
        rollback_code = r'''
import json
import os
from pathlib import Path

target = Path(r"C:\Program Files\MetaTrader 5\config\common.ini")
backup = target.with_name("common.ini.m022-maxbars-100000.backup")
if not backup.is_file():
    raise RuntimeError("M022 MaxBars rollback backup is missing")
temp = target.with_name("common.ini.m022.rollback.tmp")
temp.write_bytes(backup.read_bytes())
os.replace(temp, target)
print(json.dumps({"restored": True, "target": str(target)}), flush=True)
'''
        rollback_run = _run_process_group_bounded(
            [wine, wine_python, "-c", rollback_code],
            env=_safe_env(wine=True),
            timeout_seconds=30,
        )
        rollback = {
            "restored_backup": rollback_run["exit_code"] == 0,
            "run": rollback_run,
        }

    return {
        "ok": verified,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "prepared": prepared,
        "kill_runs": kill_runs,
        "verification": payload,
        "verify_run": verify,
        "rollback": rollback,
        "safety": {
            "account_required": "MetaQuotes-Demo",
            "configuration_change": "MaxBars only",
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_native_m1_file_probe():
    """Probe runtime MaxBars + Aug-2025 native M1 without Wine PIPE waits."""

    feature_sha = _require_m022_branch()
    dedicated = (REPO / ".venv-wine" / "Scripts" / "python.exe").resolve()
    if not dedicated.is_file():
        raise RuntimeError("established M022 Wine runtime is missing")
    wine_python = "Z:" + str(dedicated).replace("/", "\\")
    wine = _wine()
    wineserver = shutil.which("wineserver") or "/usr/bin/wineserver"

    result_path = Path("/tmp/mamba2-m022-native-m1-probe.json")
    try:
        result_path.unlink()
    except FileNotFoundError:
        pass
    windows_result = "Z:" + str(result_path.resolve()).replace("/", "\\")

    probe_code = r'''
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

out = Path(os.environ["M022_PROBE_RESULT"])
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed for M022 native-M1 probe")

try:
    terminal = mt5.terminal_info()
    account = mt5.account_info()
    payload = {
        "phase": "terminal",
        "maxbars": getattr(terminal, "maxbars", None),
        "server": getattr(account, "server", None),
        "currency": getattr(account, "currency", None),
        "runtime": list(mt5.version()) if hasattr(mt5, "version") else None,
        "native_m1_aug_25": {},
    }
    out.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    for symbol in symbols:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"could not select {symbol}")
        rows = mt5.copy_rates_range(
            symbol,
            mt5.TIMEFRAME_M1,
            datetime(2025, 8, 25, tzinfo=timezone.utc),
            datetime(2025, 8, 26, tzinfo=timezone.utc),
        )
        payload["native_m1_aug_25"][symbol] = {
            "rows": 0 if rows is None else int(len(rows)),
            "first_bar_open_utc": (
                None
                if rows is None or len(rows) == 0
                else datetime.fromtimestamp(
                    int(rows[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "last_bar_open_utc": (
                None
                if rows is None or len(rows) == 0
                else datetime.fromtimestamp(
                    int(rows[-1]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "last_error": list(mt5.last_error()),
        }
        out.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    payload["phase"] = "complete"
    out.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
finally:
    mt5.shutdown()
'''

    env = _safe_env(wine=True)
    env["M022_PROBE_RESULT"] = windows_result
    proc = subprocess.Popen(
        [wine, wine_python, "-c", probe_code],
        cwd=str(REPO),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )

    deadline = time.monotonic() + 40
    payload = None
    while time.monotonic() < deadline:
        if result_path.is_file():
            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = None
            if payload and payload.get("phase") == "complete":
                break
        time.sleep(0.5)

    # MT5 may intentionally remain open after Python disconnects. Terminate
    # the isolated Wine prefix explicitly so this probe cannot hold the
    # one-shot systemd worker open.
    stop_wine = _run_process_group_bounded(
        [wineserver, "-k"],
        env=env,
        timeout_seconds=10,
    )

    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass

    complete = bool(payload and payload.get("phase") == "complete")
    maxbars_ok = bool(payload and payload.get("maxbars") == 500000)
    history_ok = bool(
        complete
        and all(
            payload.get("native_m1_aug_25", {}).get(symbol, {}).get("rows", 0)
            >= 1000
            for symbol in M022_SYMBOLS
        )
    )
    return {
        "ok": maxbars_ok and history_ok,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "probe": payload,
        "complete": complete,
        "maxbars_verified": maxbars_ok,
        "native_aug_25_verified": history_ok,
        "wine_shutdown": stop_wine,
        "safety": {
            "market_data_read_only": True,
            "terminal_configuration_modified": False,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_terminal_history_capacity_probe():
    """Read-only probe of MT5 native-M1 capacity and max-bars configuration."""

    feature_sha = _require_m022_branch()
    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    if not dedicated.is_file():
        raise RuntimeError("established M022 Wine runtime is missing: .venv-wine")
    wine_python = _wine_windows_path(dedicated)
    if not wine_python:
        raise RuntimeError("cannot map established M022 Wine runtime")
    wine = _wine()

    probe_code = r'''
import json
from pathlib import Path
from datetime import datetime, timezone

import MetaTrader5 as mt5

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed for M022 capacity probe")

try:
    terminal = mt5.terminal_info()
    account = mt5.account_info()
    output = {
        "terminal": {
            "path": getattr(terminal, "path", None),
            "data_path": getattr(terminal, "data_path", None),
            "commondata_path": getattr(terminal, "commondata_path", None),
            "maxbars": getattr(terminal, "maxbars", None),
            "build": list(mt5.version()) if hasattr(mt5, "version") else None,
        },
        "account": {
            "server": getattr(account, "server", None),
            "currency": getattr(account, "currency", None),
        },
        "native_m1": {},
        "config_hits": [],
    }

    for symbol in symbols:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"could not select {symbol}")
        recent = mt5.copy_rates_from_pos(
            symbol,
            mt5.TIMEFRAME_M1,
            0,
            2000,
        )
        recent_rows = 0 if recent is None else int(len(recent))
        recent_first = None
        recent_last = None
        if recent_rows:
            recent_first = datetime.fromtimestamp(
                int(recent[0]["time"]), timezone.utc
            ).isoformat().replace("+00:00", "Z")
            recent_last = datetime.fromtimestamp(
                int(recent[-1]["time"]), timezone.utc
            ).isoformat().replace("+00:00", "Z")
        old_day = mt5.copy_rates_range(
            symbol,
            mt5.TIMEFRAME_M1,
            datetime(2025, 8, 25, tzinfo=timezone.utc),
            datetime(2025, 8, 26, tzinfo=timezone.utc),
        )
        output["native_m1"][symbol] = {
            "recent_rows_returned": recent_rows,
            "recent_first_bar_open_utc": recent_first,
            "recent_last_bar_open_utc": recent_last,
            "aug_25_2025_rows": 0 if old_day is None else int(len(old_day)),
            "aug_25_2025_first_bar_open_utc": (
                None
                if old_day is None or len(old_day) == 0
                else datetime.fromtimestamp(
                    int(old_day[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "aug_25_2025_last_bar_open_utc": (
                None
                if old_day is None or len(old_day) == 0
                else datetime.fromtimestamp(
                    int(old_day[-1]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            ),
            "last_error": list(mt5.last_error()),
        }

    roots = []
    for raw in (
        getattr(terminal, "path", None),
        getattr(terminal, "data_path", None),
    ):
        if raw:
            roots.append(Path(raw))

    seen = set()
    for root in roots:
        candidates = []
        for name in ("terminal.ini", "common.ini", "metaeditor.ini"):
            candidates.extend(root.glob(name))
            candidates.extend((root / "config").glob(name))
        candidates.extend((root / "config").glob("*.ini"))

        for path in candidates:
            key = str(path).lower()
            if key in seen or not path.is_file():
                continue
            seen.add(key)
            try:
                raw = path.read_bytes()
            except OSError:
                continue

            decoded = []
            for encoding in ("utf-8", "utf-16le", "utf-16be"):
                try:
                    decoded.append(raw.decode(encoding, errors="ignore"))
                except UnicodeError:
                    pass

            for text in decoded:
                for line in text.splitlines():
                    normalized = line.strip()
                    if "maxbars" in normalized.lower():
                        hit = {
                            "path": str(path),
                            "line": normalized[:200],
                        }
                        if hit not in output["config_hits"]:
                            output["config_hits"].append(hit)

    print(json.dumps(output, sort_keys=True), flush=True)
finally:
    mt5.shutdown()
'''

    run = _run_process_group_bounded(
        [wine, wine_python, "-c", probe_code],
        env=_safe_env(wine=True),
        timeout_seconds=45,
    )
    payload = None
    if run["exit_code"] == 0 and run["stdout"].strip():
        payload = json.loads(run["stdout"].strip().splitlines()[-1])
    return {
        "ok": run["exit_code"] == 0 and payload is not None,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "probe": payload,
        "run": run,
        "safety": {
            "market_data_read_only": True,
            "terminal_configuration_modified": False,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_history_checkpoint_probe():
    """Probe bounded historical checkpoints with a hard per-date kill limit."""

    feature_sha = _require_m022_branch()
    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    if not dedicated.is_file():
        raise RuntimeError("established M022 Wine runtime is missing: .venv-wine")
    wine_python = _wine_windows_path(dedicated)
    if not wine_python:
        raise RuntimeError("cannot map established M022 Wine runtime to a Windows path")
    discovery = {
        "selection": "established-dedicated-wine-runtime",
        "host_path": str(dedicated),
        "wine_python": wine_python,
    }
    wine = _wine()

    checkpoints = [
        "2026-06-01T00:00:00Z",
        "2026-05-18T00:00:00Z",
        "2026-05-04T00:00:00Z",
        "2026-04-20T00:00:00Z",
        "2026-04-06T00:00:00Z",
        "2026-03-23T00:00:00Z",
        "2026-03-09T00:00:00Z",
        "2026-02-23T00:00:00Z",
        "2026-02-09T00:00:00Z",
        "2026-01-26T00:00:00Z",
        "2026-01-12T00:00:00Z",
        "2025-12-15T00:00:00Z",
        "2025-11-17T00:00:00Z",
        "2025-10-20T00:00:00Z",
        "2025-09-22T00:00:00Z",
        "2025-08-25T00:00:00Z",
        "2025-07-28T00:00:00Z",
        "2025-06-30T00:00:00Z",
        "2025-06-02T00:00:00Z",
        "2025-05-05T00:00:00Z",
        "2025-04-07T00:00:00Z",
        "2025-03-10T00:00:00Z",
    ]

    probe_code = r'''
import json
import platform
import sys
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import numpy as np

from config import mt5 as mt5_config
from mamba2.backtest.mt5_dataset import _mt5_initialize_kwargs

symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
checkpoint = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
rates_end = checkpoint + timedelta(hours=12)
ticks_end = checkpoint + timedelta(minutes=10)

if not mt5.initialize(**_mt5_initialize_kwargs(mt5_config)):
    raise RuntimeError("MT5 initialize failed for M022 checkpoint probe")

try:
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    output = {}
    all_ok = True

    for symbol in symbols:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"MT5 could not select {symbol}")

        symbol_result = {}
        for label, timeframe in (
            ("M5", mt5.TIMEFRAME_M5),
            ("M15", mt5.TIMEFRAME_M15),
        ):
            rates = mt5.copy_rates_range(
                symbol, timeframe, checkpoint, rates_end
            )
            rows = 0 if rates is None else int(len(rates))
            first = None
            last = None
            if rows:
                first = datetime.fromtimestamp(
                    int(rates[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
                last = datetime.fromtimestamp(
                    int(rates[-1]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z")
            symbol_result[label] = {
                "rows": rows,
                "first_bar_open_utc": first,
                "last_bar_open_utc": last,
            }
            if rows == 0:
                all_ok = False

        ticks = mt5.copy_ticks_range(
            symbol, checkpoint, ticks_end, mt5.COPY_TICKS_ALL
        )
        valid = 0
        first_tick = None
        if ticks is not None:
            names = ticks.dtype.names or ()
            for row in ticks:
                bid = float(row["bid"])
                ask = float(row["ask"])
                if bid <= 0 or ask <= 0 or ask < bid:
                    continue
                raw_time = (
                    int(row["time_msc"]) / 1000.0
                    if "time_msc" in names
                    else float(row["time"])
                )
                ts = datetime.fromtimestamp(raw_time, timezone.utc)
                valid += 1
                if first_tick is None:
                    first_tick = ts
        symbol_result["ticks"] = {
            "valid_synchronized_bid_ask_rows": valid,
            "first_synchronized_bid_ask_tick_utc": (
                first_tick.isoformat().replace("+00:00", "Z")
                if first_tick is not None else None
            ),
        }
        if valid == 0:
            all_ok = False
        output[symbol] = symbol_result

    print(json.dumps({
        "checkpoint_utc": sys.argv[1],
        "all_symbols_pass": all_ok,
        "symbols": output,
        "broker_server": getattr(account, "server", None),
        "account_currency": getattr(account, "currency", None),
        "terminal_maxbars": getattr(terminal, "maxbars", None),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "metatrader5_package": getattr(mt5, "__version__", None),
            "terminal_version": (
                list(mt5.version()) if hasattr(mt5, "version") else None
            ),
        },
    }, sort_keys=True), flush=True)
finally:
    mt5.shutdown()
'''

    observations = []
    oldest_passing = None
    stop_reason = None

    for checkpoint in checkpoints:
        run = _run_process_group_bounded(
            [
                wine,
                wine_python,
                "-c",
                probe_code,
                checkpoint,
            ],
            env=_safe_env(wine=True),
            timeout_seconds=30,
        )
        observation = {
            "checkpoint_utc": checkpoint,
            "exit_code": run["exit_code"],
            "timed_out": run["timed_out"],
            "stderr": run["stderr"],
        }
        if run["stdout"].strip():
            try:
                payload = json.loads(run["stdout"].strip().splitlines()[-1])
                observation["probe"] = payload
            except json.JSONDecodeError:
                observation["stdout_tail"] = run["stdout"][-4000:]

        observations.append(observation)

        payload = observation.get("probe")
        if run["exit_code"] != 0:
            stop_reason = (
                f"checkpoint {checkpoint} did not complete within the fixed "
                "read-only process boundary or returned an error"
            )
            break
        if not payload or not payload.get("all_symbols_pass"):
            stop_reason = (
                f"checkpoint {checkpoint} lacks complete synchronized "
                "Bid/Ask tick plus M5/M15 coverage for all symbols"
            )
            break
        oldest_passing = checkpoint

    return {
        "ok": oldest_passing is not None,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "checkpoint_order": checkpoints,
        "oldest_passing_checkpoint_utc": oldest_passing,
        "stop_reason": stop_reason,
        "observations": observations,
        "wine_python": wine_python,
        "discovery": discovery,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_history_depth_probe():
    """Retired M022 probe; use the hard-bounded checkpoint action."""

    feature_sha = _require_m022_branch()
    return {
        "ok": False,
        "reason": (
            "m022_history_depth_probe is retired because MT5/Wine can ignore "
            "the soft timeout; use m022_history_checkpoint_probe"
        ),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


def m022_tick_inventory_cleanup():
    """Remove only the fixed tick-derived M022 inventory directory."""

    feature_sha = _require_m022_branch()
    target = _ensure_baseline_path(M022_TICK_INVENTORY_DIR)
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {
        "ok": not target.exists(),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "path": str(target.relative_to(REPO)),
        "existed": existed,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
        },
    }


def m022_native_inventory_existing_probe():
    """Read-only integrity/overlap probe for an existing native-M1 v3 artifact."""

    feature_sha = _require_m022_branch()
    root = M022_NATIVE_INVENTORY_DIR
    manifest = M022_NATIVE_INVENTORY_MANIFEST

    if not root.exists():
        return {
            "ok": False,
            "complete": False,
            "reason": "native-M1 v3 directory does not exist",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "path": str(root.relative_to(REPO)),
        }

    file_inventory = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root))
        file_inventory.append({
            "path": relative,
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
        })

    if not manifest.is_file():
        return {
            "ok": False,
            "complete": False,
            "reason": "existing native-M1 v3 directory has no manifest.json",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "path": str(root.relative_to(REPO)),
            "files": file_inventory,
            "safety": {
                "read_only": True,
                "economic_replay_run": False,
                "real_order_api_called": False,
                "m021_post_cutoff_data_used": False,
            },
        }

    inspect_code = r'''
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mamba2.backtest.mt5_dataset import load_mt5_dataset

candidate_path = Path(
    "backtest_data/m022-history-inventory-native-m1-v3/manifest.json"
)
accepted_path = Path(
    "backtest_data/broader-history-20260623-20260925/manifest.json"
)
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
price_columns = ["open", "high", "low", "close"]
overlap_start = pd.Timestamp("2026-06-23T00:00:00Z")
overlap_end = pd.Timestamp("2026-09-25T00:00:00Z")

def iso(value):
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")

def compare_prices(left, right, point):
    same_index = left.index.equals(right.index)
    if not same_index:
        return {
            "same_index": False,
            "left_rows": int(len(left)),
            "right_rows": int(len(right)),
            "max_abs_delta": None,
            "max_delta_points": None,
            "within_half_point": False,
            "identical_frame": False,
        }
    lv = left[price_columns].to_numpy(dtype=float)
    rv = right[price_columns].to_numpy(dtype=float)
    delta = np.abs(lv - rv)
    max_abs = float(delta.max()) if delta.size else 0.0
    max_points = max_abs / point if point > 0 else None
    return {
        "same_index": True,
        "left_rows": int(len(left)),
        "right_rows": int(len(right)),
        "max_abs_delta": max_abs,
        "max_delta_points": max_points,
        "within_half_point": bool(
            max_points is not None and max_points <= 0.5
        ),
        "identical_frame": bool(left.equals(right)),
    }

try:
    candidate = load_mt5_dataset(candidate_path)
    accepted = load_mt5_dataset(accepted_path)
except Exception as exc:
    print(json.dumps({
        "load_ok": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }, sort_keys=True))
    raise SystemExit(0)

per_symbol = {}
overlap_ok = True
common_dates = None

for symbol in symbols:
    point = float(candidate.symbol_metadata[symbol].point_size)
    m1 = candidate.m1_bars[symbol]
    ask = candidate.ask_m1_bars[symbol]
    native = candidate.native_timeframe_bars[symbol]
    missing_ask = m1.index.difference(ask.index)
    ask_extra = ask.index.difference(m1.index)

    cm1 = m1.loc[(m1.index >= overlap_start) & (m1.index < overlap_end)]
    am1 = accepted.m1_bars[symbol].loc[
        (accepted.m1_bars[symbol].index >= overlap_start)
        & (accepted.m1_bars[symbol].index < overlap_end)
    ]
    cask = ask.loc[(ask.index >= overlap_start) & (ask.index < overlap_end)]
    aask = accepted.ask_m1_bars[symbol].loc[
        (accepted.ask_m1_bars[symbol].index >= overlap_start)
        & (accepted.ask_m1_bars[symbol].index < overlap_end)
    ]

    bid_overlap = compare_prices(cm1, am1, point)
    ask_overlap = compare_prices(cask, aask, point)

    native_overlap = {}
    for timeframe in ("M5", "M15"):
        left = native[timeframe].loc[
            (native[timeframe].index >= overlap_start)
            & (native[timeframe].index < overlap_end)
        ]
        right_source = accepted.native_timeframe_bars[symbol][timeframe]
        right = right_source.loc[
            (right_source.index >= overlap_start)
            & (right_source.index < overlap_end)
        ]
        native_overlap[timeframe] = {
            "same_index": bool(left.index.equals(right.index)),
            "identical_frame": bool(left.equals(right)),
            "candidate_rows": int(len(left)),
            "accepted_rows": int(len(right)),
        }

    ask_meta = candidate.manifest["symbols"][symbol].get("ask_m1", {})
    symbol_ok = (
        len(missing_ask) == 0
        and len(ask_extra) == 0
        and m1.index.equals(ask.index)
        and bid_overlap["identical_frame"]
        and ask_overlap["within_half_point"]
        and ask_meta.get("source") == "copy_ticks_range"
        and all(
            native_overlap[tf]["identical_frame"]
            for tf in ("M5", "M15")
        )
    )
    overlap_ok = overlap_ok and symbol_ok

    dates = set(m1.index.normalize())
    dates &= set(ask.index.normalize())
    dates &= set(native["M5"].index.normalize())
    common_dates = dates if common_dates is None else common_dates & dates

    per_symbol[symbol] = {
        "m1_rows": int(len(m1)),
        "ask_m1_rows": int(len(ask)),
        "m5_rows": int(len(native["M5"])),
        "m15_rows": int(len(native["M15"])),
        "m1_first": iso(m1.index[0]),
        "m1_last": iso(m1.index[-1]),
        "ask_first": iso(ask.index[0]),
        "ask_last": iso(ask.index[-1]),
        "missing_ask_rows": int(len(missing_ask)),
        "extra_ask_rows": int(len(ask_extra)),
        "bid_overlap": bid_overlap,
        "ask_overlap": ask_overlap,
        "native_overlap": native_overlap,
        "accepted": bool(symbol_ok),
    }

ordered_dates = sorted(common_dates or [])
print(json.dumps({
    "load_ok": True,
    "overlap_ok": bool(overlap_ok),
    "manifest_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    "accepted_m019_manifest_sha256": hashlib.sha256(
        accepted_path.read_bytes()
    ).hexdigest(),
    "broker_server": candidate.manifest.get("broker_server"),
    "account_currency": candidate.manifest.get("account_currency"),
    "terminal_version": candidate.manifest.get("terminal_version"),
    "requested_range": candidate.manifest.get("requested_range"),
    "common_trading_date_count": int(len(ordered_dates)),
    "first_common_trading_date": (
        iso(ordered_dates[0]) if ordered_dates else None
    ),
    "last_common_trading_date": (
        iso(ordered_dates[-1]) if ordered_dates else None
    ),
    "per_symbol": per_symbol,
}, sort_keys=True))
'''

    inspect = _run(_native_command("-c", inspect_code), env=_safe_env())
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "complete": False,
            "reason": "existing v3 integrity probe process failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "files": file_inventory,
            "inspect": inspect,
        }

    try:
        payload = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse existing v3 probe") from exc

    complete = bool(payload.get("load_ok"))
    return {
        "ok": bool(complete and payload.get("overlap_ok")),
        "complete": complete,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "path": str(root.relative_to(REPO)),
        "files": file_inventory,
        "integrity": payload,
        "safety": {
            "read_only": True,
            "economic_replay_run": False,
            "real_order_api_called": False,
            "m021_post_cutoff_data_used": False,
        },
        "inspect": inspect,
    }


def m022_partition_freeze():
    """Materialize the frozen 60/20/20 M022 trading-date partition rule."""

    feature_sha = _require_m022_branch()
    if not M022_NATIVE_INVENTORY_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted native-M1 v3 manifest is unavailable",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "required_manifest": str(
                M022_NATIVE_INVENTORY_MANIFEST.relative_to(REPO)
            ),
        }

    code = r'''
import hashlib
import json
import math
from pathlib import Path

from mamba2.backtest.mt5_dataset import load_mt5_dataset

manifest_path = Path(
    "backtest_data/m022-history-inventory-native-m1-v3/manifest.json"
)
dataset = load_mt5_dataset(manifest_path)
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]

common_dates = None
for symbol in symbols:
    m1 = dataset.m1_bars[symbol]
    ask = dataset.ask_m1_bars[symbol]
    m5 = dataset.native_timeframe_bars[symbol]["M5"]

    dates = set(m1.index.normalize())
    dates &= set(ask.index.normalize())
    dates &= set(m5.index.normalize())
    common_dates = dates if common_dates is None else common_dates & dates

ordered = sorted(common_dates or [])
n = len(ordered)
dev_n = math.floor(n * 0.60)
val_n = math.floor(n * 0.20)
hold_n = n - dev_n - val_n

def day_iso(ts):
    return ts.isoformat().replace("+00:00", "Z")

def boundary_iso(ts):
    return ts.normalize().isoformat().replace("+00:00", "Z")

if n:
    development_start = ordered[0].normalize()
    validation_start = ordered[dev_n].normalize() if dev_n < n else None
    holdout_start = (
        ordered[dev_n + val_n].normalize()
        if (dev_n + val_n) < n
        else None
    )
else:
    development_start = validation_start = holdout_start = None

cutoff = "2026-09-25T00:00:00Z"
date_payload = "\n".join(day_iso(ts) for ts in ordered).encode("utf-8")
date_sha = hashlib.sha256(date_payload).hexdigest()
manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

partitions = {
    "development": {
        "trading_dates": dev_n,
        "start_utc": (
            boundary_iso(development_start)
            if development_start is not None else None
        ),
        "end_exclusive_utc": (
            boundary_iso(validation_start)
            if validation_start is not None else None
        ),
        "first_trading_date": (
            day_iso(ordered[0]) if dev_n else None
        ),
        "last_trading_date": (
            day_iso(ordered[dev_n - 1]) if dev_n else None
        ),
    },
    "validation": {
        "trading_dates": val_n,
        "start_utc": (
            boundary_iso(validation_start)
            if validation_start is not None else None
        ),
        "end_exclusive_utc": (
            boundary_iso(holdout_start)
            if holdout_start is not None else None
        ),
        "first_trading_date": (
            day_iso(ordered[dev_n]) if val_n else None
        ),
        "last_trading_date": (
            day_iso(ordered[dev_n + val_n - 1]) if val_n else None
        ),
    },
    "historical_holdout": {
        "trading_dates": hold_n,
        "start_utc": (
            boundary_iso(holdout_start)
            if holdout_start is not None else None
        ),
        "end_exclusive_utc": cutoff,
        "first_trading_date": (
            day_iso(ordered[dev_n + val_n]) if hold_n else None
        ),
        "last_trading_date": (
            day_iso(ordered[-1]) if hold_n else None
        ),
    },
}

minimum_ok = min(dev_n, val_n, hold_n) >= 20

print(json.dumps({
    "manifest_path": str(manifest_path),
    "manifest_sha256": manifest_sha,
    "common_trading_date_count": n,
    "common_trading_dates_sha256": date_sha,
    "first_common_trading_date": day_iso(ordered[0]) if ordered else None,
    "last_common_trading_date": day_iso(ordered[-1]) if ordered else None,
    "rule": {
        "development_fraction": 0.60,
        "validation_fraction": 0.20,
        "holdout_fraction": 0.20,
        "rounding": "floor first two; remainder to holdout",
        "whole_utc_trading_dates": True,
        "minimum_trading_dates_each": 20,
    },
    "partitions": partitions,
    "minimum_partition_size_ok": minimum_ok,
}, sort_keys=True))
'''

    run = _run(_native_command("-c", code), env=_safe_env())
    if run["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 partition computation failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "run": run,
        }

    try:
        payload = json.loads(run["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse M022 partition result") from exc

    return {
        "ok": bool(payload.get("minimum_partition_size_ok")),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "partition_freeze": payload,
        "safety": {
            "market_data_read_only": True,
            "economic_replay_run": False,
            "parameter_result_inspected": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
        "run": run,
    }


def m022_native_inventory():
    """Export native Bid M1 + tick Ask and prove accepted-M019 parity."""

    feature_sha = _require_m022_branch()
    candidate_start_utc = "2025-08-25T00:00:00Z"
    output_dir = _ensure_baseline_path(M022_NATIVE_INVENTORY_DIR)

    if output_dir.exists():
        return {
            "ok": False,
            "reason": (
                "M022 native inventory directory already exists; refusing "
                "overwrite of versioned evidence"
            ),
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "path": str(output_dir.relative_to(REPO)),
        }

    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 manifest is unavailable for overlap proof",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "required_manifest": str(M019_MANIFEST.relative_to(REPO)),
        }

    dedicated = (REPO / ".venv-wine" / "Scripts" / "python.exe").resolve()
    if not dedicated.is_file():
        raise RuntimeError("established M022 Wine runtime is missing: .venv-wine")
    wine_python = "Z:" + str(dedicated).replace("/", "\\")
    wine = _wine()

    export = _run(
        [
            shutil.which("timeout") or "/usr/bin/timeout",
            "--signal=KILL",
            "15m",
            wine,
            wine_python,
            "-m",
            "mamba2.backtest.mt5_dataset",
            "--symbols",
            *M022_SYMBOLS,
            "--timeframes",
            "M1",
            "M5",
            "M15",
            "--from-utc",
            candidate_start_utc,
            "--to-utc",
            M022_CUTOFF_UTC,
            "--output-dir",
            str(M022_NATIVE_INVENTORY_DIR.relative_to(REPO)),
            "--include-tick-ask",
            "--tick-chunk-minutes",
            "1440",
            "--rate-chunk-days",
            "7",
        ],
        env=_safe_env(wine=True),
    )
    if export["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 native-M1 historical inventory export failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "export": export,
            "wine_python": wine_python,
        }

    if not M022_NATIVE_INVENTORY_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M022 native inventory completed without manifest.json",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "export": export,
        }

    inspect_code = r'''
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mamba2.backtest.mt5_dataset import load_mt5_dataset

candidate_path = Path(
    "backtest_data/m022-history-inventory-native-m1-v3/manifest.json"
)
accepted_path = Path(
    "backtest_data/broader-history-20260623-20260925/manifest.json"
)
candidate = load_mt5_dataset(candidate_path)
accepted = load_mt5_dataset(accepted_path)
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
price_columns = ["open", "high", "low", "close"]
overlap_start = pd.Timestamp("2026-06-23T00:00:00Z")
overlap_end = pd.Timestamp("2026-09-25T00:00:00Z")

def iso(value):
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")

def compare_prices(left, right, point):
    same_index = left.index.equals(right.index)
    if not same_index:
        return {
            "same_index": False,
            "left_rows": int(len(left)),
            "right_rows": int(len(right)),
            "max_abs_delta": None,
            "max_delta_points": None,
            "within_half_point": False,
            "identical_frame": False,
        }
    lv = left[price_columns].to_numpy(dtype=float)
    rv = right[price_columns].to_numpy(dtype=float)
    delta = np.abs(lv - rv)
    max_abs = float(delta.max()) if delta.size else 0.0
    max_points = max_abs / point if point > 0 else None
    return {
        "same_index": True,
        "left_rows": int(len(left)),
        "right_rows": int(len(right)),
        "max_abs_delta": max_abs,
        "max_delta_points": max_points,
        "within_half_point": bool(
            max_points is not None and max_points <= 0.5
        ),
        "identical_frame": bool(left.equals(right)),
    }

def gap_summary(frame, minutes):
    diffs = frame.index.to_series().diff().dropna()
    expected = pd.Timedelta(minutes=minutes)
    gaps = diffs[diffs > expected]
    largest = gaps.max() if not gaps.empty else None
    return {
        "interval_gap_count": int(len(gaps)),
        "largest_interval_gap_minutes": (
            float(largest / pd.Timedelta(minutes=1))
            if largest is not None else None
        ),
    }

per_symbol = {}
overlap_ok = True
common_dates = None

for symbol in symbols:
    metadata = candidate.symbol_metadata[symbol]
    point = float(metadata.point_size)
    m1 = candidate.m1_bars[symbol]
    ask = candidate.ask_m1_bars[symbol]
    native = candidate.native_timeframe_bars[symbol]
    missing_ask = m1.index.difference(ask.index)
    ask_extra = ask.index.difference(m1.index)

    candidate_m1_overlap = m1.loc[
        (m1.index >= overlap_start) & (m1.index < overlap_end)
    ]
    accepted_m1_overlap = accepted.m1_bars[symbol].loc[
        (accepted.m1_bars[symbol].index >= overlap_start)
        & (accepted.m1_bars[symbol].index < overlap_end)
    ]
    candidate_ask_overlap = ask.loc[
        (ask.index >= overlap_start) & (ask.index < overlap_end)
    ]
    accepted_ask_overlap = accepted.ask_m1_bars[symbol].loc[
        (accepted.ask_m1_bars[symbol].index >= overlap_start)
        & (accepted.ask_m1_bars[symbol].index < overlap_end)
    ]

    bid_overlap = compare_prices(
        candidate_m1_overlap,
        accepted_m1_overlap,
        point,
    )
    ask_overlap = compare_prices(
        candidate_ask_overlap,
        accepted_ask_overlap,
        point,
    )

    native_overlap = {}
    for timeframe in ("M5", "M15"):
        left = native[timeframe].loc[
            (native[timeframe].index >= overlap_start)
            & (native[timeframe].index < overlap_end)
        ]
        right_source = accepted.native_timeframe_bars[symbol][timeframe]
        right = right_source.loc[
            (right_source.index >= overlap_start)
            & (right_source.index < overlap_end)
        ]
        native_overlap[timeframe] = {
            "same_index": bool(left.index.equals(right.index)),
            "identical_frame": bool(left.equals(right)),
            "candidate_rows": int(len(left)),
            "accepted_rows": int(len(right)),
        }

    ask_meta = candidate.manifest["symbols"][symbol].get("ask_m1", {})
    symbol_ok = (
        len(missing_ask) == 0
        and len(ask_extra) == 0
        and m1.index.equals(ask.index)
        and bid_overlap["identical_frame"]
        and ask_overlap["within_half_point"]
        and ask_meta.get("source") == "copy_ticks_range"
        and all(
            native_overlap[tf]["identical_frame"]
            for tf in ("M5", "M15")
        )
    )
    overlap_ok = overlap_ok and symbol_ok

    symbol_dates = set(m1.index.normalize())
    symbol_dates &= set(ask.index.normalize())
    symbol_dates &= set(native["M5"].index.normalize())
    common_dates = (
        symbol_dates
        if common_dates is None
        else common_dates & symbol_dates
    )

    files = candidate.manifest["symbols"][symbol]["files"]
    per_symbol[symbol] = {
        "point": point,
        "m1": {
            "rows": int(len(m1)),
            "first_bar_open_utc": iso(m1.index[0]),
            "last_bar_open_utc": iso(m1.index[-1]),
            "sha256": files["M1"]["sha256"],
            "source": "native_mt5_rates",
            **gap_summary(m1, 1),
        },
        "ask_m1": {
            "rows": int(len(ask)),
            "first_bar_open_utc": iso(ask.index[0]),
            "last_bar_open_utc": iso(ask.index[-1]),
            "sha256": ask_meta["sha256"],
            "source": ask_meta.get("source"),
            "missing_vs_bid_m1_rows": int(len(missing_ask)),
            "extra_vs_bid_m1_rows": int(len(ask_extra)),
            "valid_ticks": ask_meta.get("valid_ticks"),
            "spread_points_min": ask_meta.get("spread_points_min"),
            "spread_points_max": ask_meta.get("spread_points_max"),
            "zero_spread_ticks": ask_meta.get("zero_spread_ticks"),
        },
        "m5": {
            "rows": int(len(native["M5"])),
            "first_bar_open_utc": iso(native["M5"].index[0]),
            "last_bar_open_utc": iso(native["M5"].index[-1]),
            "sha256": files["M5"]["sha256"],
            **gap_summary(native["M5"], 5),
        },
        "m15": {
            "rows": int(len(native["M15"])),
            "first_bar_open_utc": iso(native["M15"].index[0]),
            "last_bar_open_utc": iso(native["M15"].index[-1]),
            "sha256": files["M15"]["sha256"],
            **gap_summary(native["M15"], 15),
        },
        "overlap": {
            "bid_m1": bid_overlap,
            "ask_m1": ask_overlap,
            "native": native_overlap,
            "accepted": bool(symbol_ok),
        },
    }

manifest_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
accepted_manifest_sha = hashlib.sha256(
    accepted_path.read_bytes()
).hexdigest()

starts = []
for symbol in symbols:
    starts.extend([
        candidate.m1_bars[symbol].index[0],
        candidate.ask_m1_bars[symbol].index[0],
        candidate.native_timeframe_bars[symbol]["M5"].index[0],
        candidate.native_timeframe_bars[symbol]["M15"].index[0],
    ])
strict_common_start = max(starts)
ordered_dates = sorted(common_dates or [])

print(json.dumps({
    "manifest_path": str(candidate_path),
    "manifest_sha256": manifest_sha,
    "accepted_m019_manifest_path": str(accepted_path),
    "accepted_m019_manifest_sha256": accepted_manifest_sha,
    "source": candidate.manifest.get("source"),
    "broker_server": candidate.manifest.get("broker_server"),
    "account_currency": candidate.manifest.get("account_currency"),
    "terminal_version": candidate.manifest.get("terminal_version"),
    "requested_range": candidate.manifest.get("requested_range"),
    "strict_common_start_utc": iso(strict_common_start),
    "strict_common_end_exclusive_utc": "2026-09-25T00:00:00Z",
    "accepted_overlap_start_utc": "2026-06-23T00:00:00Z",
    "accepted_overlap_end_exclusive_utc": "2026-09-25T00:00:00Z",
    "ask_price_overlap_tolerance_points": 0.5,
    "native_bid_overlap_requires_exact_frame": True,
    "overlap_ok": bool(overlap_ok),
    "common_trading_date_count": int(len(ordered_dates)),
    "first_common_trading_date": (
        iso(ordered_dates[0]) if ordered_dates else None
    ),
    "last_common_trading_date": (
        iso(ordered_dates[-1]) if ordered_dates else None
    ),
    "per_symbol": per_symbol,
}, sort_keys=True))
'''

    inspect = _run(
        _native_command("-c", inspect_code),
        env=_safe_env(),
    )
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 native inventory overlap inspection failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "export": export,
            "inspect": inspect,
        }

    try:
        summary = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(
            "unable to parse M022 native inventory inspection"
        ) from exc

    return {
        "ok": bool(summary.get("overlap_ok")),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "candidate_start_utc": candidate_start_utc,
        "cutoff_utc": M022_CUTOFF_UTC,
        "inventory": summary,
        "wine_python": wine_python,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
        "export": export,
        "inspect": inspect,
    }


def m022_tick_inventory():
    """Export a tick-derived M1 candidate and prove overlap with accepted M019."""

    feature_sha = _require_m022_branch()
    output_dir = _ensure_baseline_path(M022_TICK_INVENTORY_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": (
                "M022 tick inventory directory already exists; run "
                "m022_tick_inventory_cleanup explicitly before re-export"
            ),
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "path": str(output_dir.relative_to(REPO)),
        }

    if not M019_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "accepted M019 manifest is unavailable for overlap proof",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "required_manifest": str(M019_MANIFEST.relative_to(REPO)),
        }

    depth = m022_history_checkpoint_probe()
    if not depth.get("ok"):
        return {
            "ok": False,
            "reason": "bounded M022 depth probe did not establish a common start",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "depth": depth,
        }

    candidate_start_utc = depth.get("oldest_passing_checkpoint_utc")
    if not candidate_start_utc:
        return {
            "ok": False,
            "reason": "bounded M022 depth probe returned no candidate start",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "depth": depth,
        }

    dedicated = REPO / ".venv-wine" / "Scripts" / "python.exe"
    if not dedicated.is_file():
        raise RuntimeError("established M022 Wine runtime is missing: .venv-wine")
    wine_python = _wine_windows_path(dedicated)
    if not wine_python:
        raise RuntimeError("cannot map established M022 Wine runtime to a Windows path")
    discovery = {
        "selection": "established-dedicated-wine-runtime",
        "host_path": str(dedicated),
        "wine_python": wine_python,
    }
    wine = _wine()
    export = _run(
        [
            shutil.which("timeout") or "/usr/bin/timeout",
            "--signal=KILL",
            "15m",
            wine,
            wine_python,
            "-m",
            "mamba2.backtest.mt5_dataset",
            "--symbols",
            *M022_SYMBOLS,
            "--timeframes",
            "M1",
            "M5",
            "M15",
            "--from-utc",
            candidate_start_utc,
            "--to-utc",
            M022_CUTOFF_UTC,
            "--output-dir",
            str(M022_TICK_INVENTORY_DIR.relative_to(REPO)),
            "--include-tick-ask",
            "--derive-m1-from-ticks",
            "--tick-chunk-minutes",
            "1440",
            "--rate-chunk-days",
            "7",
        ],
        env=_safe_env(wine=True),
    )
    if export["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 tick-derived historical inventory export failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "depth": depth,
            "export": export,
            "wine_python": wine_python,
            "discovery": discovery,
        }

    if not M022_TICK_INVENTORY_MANIFEST.is_file():
        return {
            "ok": False,
            "reason": "M022 tick inventory completed without manifest.json",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "depth": depth,
            "export": export,
        }

    inspect_code = r'''
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mamba2.backtest.mt5_dataset import load_mt5_dataset

candidate_path = Path(
    "backtest_data/m022-history-inventory-tick-m1-v2/manifest.json"
)
accepted_path = Path(
    "backtest_data/broader-history-20260623-20260925/manifest.json"
)
candidate = load_mt5_dataset(candidate_path)
accepted = load_mt5_dataset(accepted_path)
symbols = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
price_columns = ["open", "high", "low", "close"]
overlap_start = pd.Timestamp("2026-06-23T00:00:00Z")
overlap_end = pd.Timestamp("2026-09-25T00:00:00Z")

def iso(value):
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")

def gap_summary(frame, minutes):
    diffs = frame.index.to_series().diff().dropna()
    expected = pd.Timedelta(minutes=minutes)
    gaps = diffs[diffs > expected]
    largest = gaps.max() if not gaps.empty else None
    return {
        "interval_gap_count": int(len(gaps)),
        "largest_interval_gap_minutes": (
            float(largest / pd.Timedelta(minutes=1))
            if largest is not None else None
        ),
    }

def compare_prices(left, right, point):
    same_index = left.index.equals(right.index)
    if not same_index:
        return {
            "same_index": False,
            "left_rows": int(len(left)),
            "right_rows": int(len(right)),
            "max_abs_delta": None,
            "max_delta_points": None,
            "within_half_point": False,
        }
    left_values = left[price_columns].to_numpy(dtype=float)
    right_values = right[price_columns].to_numpy(dtype=float)
    delta = np.abs(left_values - right_values)
    max_abs = float(delta.max()) if delta.size else 0.0
    max_points = max_abs / point if point > 0 else None
    return {
        "same_index": True,
        "left_rows": int(len(left)),
        "right_rows": int(len(right)),
        "max_abs_delta": max_abs,
        "max_delta_points": max_points,
        "within_half_point": bool(max_points is not None and max_points <= 0.5),
    }

per_symbol = {}
overlap_ok = True
for symbol in symbols:
    metadata = candidate.symbol_metadata[symbol]
    point = float(metadata.point_size)
    m1 = candidate.m1_bars[symbol]
    ask = candidate.ask_m1_bars[symbol]
    native = candidate.native_timeframe_bars[symbol]
    missing_ask = m1.index.difference(ask.index)
    ask_extra = ask.index.difference(m1.index)

    candidate_m1_overlap = m1.loc[
        (m1.index >= overlap_start) & (m1.index < overlap_end)
    ]
    accepted_m1_overlap = accepted.m1_bars[symbol].loc[
        (accepted.m1_bars[symbol].index >= overlap_start)
        & (accepted.m1_bars[symbol].index < overlap_end)
    ]
    candidate_ask_overlap = ask.loc[
        (ask.index >= overlap_start) & (ask.index < overlap_end)
    ]
    accepted_ask_overlap = accepted.ask_m1_bars[symbol].loc[
        (accepted.ask_m1_bars[symbol].index >= overlap_start)
        & (accepted.ask_m1_bars[symbol].index < overlap_end)
    ]

    bid_overlap = compare_prices(
        candidate_m1_overlap,
        accepted_m1_overlap,
        point,
    )
    ask_overlap = compare_prices(
        candidate_ask_overlap,
        accepted_ask_overlap,
        point,
    )

    native_overlap = {}
    for timeframe in ("M5", "M15"):
        left = native[timeframe].loc[
            (native[timeframe].index >= overlap_start)
            & (native[timeframe].index < overlap_end)
        ]
        right_source = accepted.native_timeframe_bars[symbol][timeframe]
        right = right_source.loc[
            (right_source.index >= overlap_start)
            & (right_source.index < overlap_end)
        ]
        native_overlap[timeframe] = {
            "same_index": bool(left.index.equals(right.index)),
            "identical_frame": bool(left.equals(right)),
            "candidate_rows": int(len(left)),
            "accepted_rows": int(len(right)),
        }

    source_entry = candidate.manifest["symbols"][symbol]["files"]["M1"]
    symbol_ok = (
        len(missing_ask) == 0
        and len(ask_extra) == 0
        and m1.index.equals(ask.index)
        and source_entry.get("source") == "copy_ticks_range_bid_aggregation"
        and bid_overlap["within_half_point"]
        and ask_overlap["within_half_point"]
        and all(
            native_overlap[tf]["identical_frame"]
            for tf in ("M5", "M15")
        )
    )
    overlap_ok = overlap_ok and symbol_ok

    files = candidate.manifest["symbols"][symbol]["files"]
    ask_meta = candidate.manifest["symbols"][symbol]["ask_m1"]
    per_symbol[symbol] = {
        "point": point,
        "m1": {
            "rows": int(len(m1)),
            "first_bar_open_utc": iso(m1.index[0]),
            "last_bar_open_utc": iso(m1.index[-1]),
            "sha256": files["M1"]["sha256"],
            "source": source_entry.get("source"),
            **gap_summary(m1, 1),
        },
        "ask_m1": {
            "rows": int(len(ask)),
            "first_bar_open_utc": iso(ask.index[0]),
            "last_bar_open_utc": iso(ask.index[-1]),
            "sha256": ask_meta["sha256"],
            "missing_vs_bid_m1_rows": int(len(missing_ask)),
            "extra_vs_bid_m1_rows": int(len(ask_extra)),
            "valid_ticks": ask_meta.get("valid_ticks"),
            "spread_points_min": ask_meta.get("spread_points_min"),
            "spread_points_max": ask_meta.get("spread_points_max"),
            "zero_spread_ticks": ask_meta.get("zero_spread_ticks"),
        },
        "m5": {
            "rows": int(len(native["M5"])),
            "first_bar_open_utc": iso(native["M5"].index[0]),
            "last_bar_open_utc": iso(native["M5"].index[-1]),
            "sha256": files["M5"]["sha256"],
            **gap_summary(native["M5"], 5),
        },
        "m15": {
            "rows": int(len(native["M15"])),
            "first_bar_open_utc": iso(native["M15"].index[0]),
            "last_bar_open_utc": iso(native["M15"].index[-1]),
            "sha256": files["M15"]["sha256"],
            **gap_summary(native["M15"], 15),
        },
        "overlap": {
            "bid_m1": bid_overlap,
            "ask_m1": ask_overlap,
            "native": native_overlap,
            "accepted": bool(symbol_ok),
        },
    }

manifest_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
accepted_manifest_sha = hashlib.sha256(accepted_path.read_bytes()).hexdigest()
starts = []
for symbol in symbols:
    starts.extend([
        candidate.m1_bars[symbol].index[0],
        candidate.ask_m1_bars[symbol].index[0],
        candidate.native_timeframe_bars[symbol]["M5"].index[0],
        candidate.native_timeframe_bars[symbol]["M15"].index[0],
    ])
strict_common_start = max(starts)

print(json.dumps({
    "manifest_path": str(candidate_path),
    "manifest_sha256": manifest_sha,
    "accepted_m019_manifest_path": str(accepted_path),
    "accepted_m019_manifest_sha256": accepted_manifest_sha,
    "source": candidate.manifest.get("source"),
    "broker_server": candidate.manifest.get("broker_server"),
    "account_currency": candidate.manifest.get("account_currency"),
    "terminal_version": candidate.manifest.get("terminal_version"),
    "requested_range": candidate.manifest.get("requested_range"),
    "strict_common_start_utc": iso(strict_common_start),
    "strict_common_end_exclusive_utc": "2026-09-25T00:00:00Z",
    "accepted_overlap_start_utc": "2026-06-23T00:00:00Z",
    "accepted_overlap_end_exclusive_utc": "2026-09-25T00:00:00Z",
    "price_overlap_tolerance_points": 0.5,
    "overlap_ok": bool(overlap_ok),
    "per_symbol": per_symbol,
}, sort_keys=True))
'''
    inspect = _run(
        _native_command("-c", inspect_code),
        env=_safe_env(),
    )
    if inspect["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "M022 tick inventory overlap inspection failed",
            "feature_branch": "strategy-parameter-research",
            "feature_sha": feature_sha,
            "candidate_start_utc": candidate_start_utc,
            "depth": depth,
            "export": export,
            "inspect": inspect,
            "wine_python": wine_python,
            "discovery": discovery,
        }

    try:
        summary = json.loads(inspect["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("unable to parse M022 tick inventory inspection") from exc

    overlap_ok = bool(summary.get("overlap_ok"))
    return {
        "ok": overlap_ok,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "candidate_start_utc": candidate_start_utc,
        "cutoff_utc": M022_CUTOFF_UTC,
        "depth": depth,
        "inventory": summary,
        "wine_python": wine_python,
        "discovery": discovery,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
        "export": export,
        "inspect": inspect,
    }

def m022_history_inventory_cleanup():
    """Remove only the fixed raw M022 history-inventory export directory."""

    feature_sha = _require_m022_branch()
    target = _ensure_baseline_path(M022_INVENTORY_DIR)
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {
        "ok": not target.exists(),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "path": str(target.relative_to(REPO)),
        "existed": existed,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
        },
    }


def m022_history_inventory():
    """Refuse the superseded unbounded discovery/export path.

    The first M022 invocation of this action used a 2010-origin tick discovery
    request and proved unsuitable as a bounded inventory mechanism. Keep the
    action name as an explicit refusal so old queued/manual commands cannot
    silently repeat it.
    """

    feature_sha = _require_m022_branch()
    return {
        "ok": False,
        "reason": (
            "m022_history_inventory is retired; use "
            "m022_history_depth_probe followed by m022_tick_inventory"
        ),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "safety": {
            "market_data_read_only": True,
            "real_order_api_called": False,
            "economic_replay_run": False,
            "m021_post_cutoff_data_used": False,
        },
    }


ACTION_HANDLERS = {
    "repo_checks": repo_checks,
    "configure_local_control_runtime": configure_local_control_runtime,
    "bootstrap_wine_test_env": bootstrap_wine_test_env,
    "runtime_discovery": runtime_discovery,
    "runtime_versions": runtime_versions,
    "test_core": test_core,
    "test_full_native": test_full_native,
    "test_full_wine": test_full_wine,
    "first_baseline_cleanup": first_baseline_cleanup,
    "first_baseline_export": first_baseline_export,
    "first_baseline_run_pair": first_baseline_run_pair,
    "baseline_diagnostic_run_pair": baseline_diagnostic_run_pair,
    "defect_review_diagnostic_run_pair": defect_review_diagnostic_run_pair,
    "broader_history_coverage_probe": broader_history_coverage_probe,
    "broader_history_cleanup": broader_history_cleanup,
    "broader_history_export": broader_history_export,
    "broader_history_m018_regression_pair": broader_history_m018_regression_pair,
    "broader_history_run_pair": broader_history_run_pair,
    "controlled_experiment_control_pair": controlled_experiment_control_pair,
    "controlled_experiment_m020a_pair": controlled_experiment_m020a_pair,
    "controlled_experiment_m020b_diagnostic": controlled_experiment_m020b_diagnostic,
    "controlled_experiment_m020c_pair": controlled_experiment_m020c_pair,
    "controlled_experiment_m020d_pair": controlled_experiment_m020d_pair,
    "m021_forward_readiness": m021_forward_readiness,
    "m021_historical_regression": m021_historical_regression,
    "m021_primary_export": m021_primary_export,
    "m021_primary_pair": m021_primary_pair,
    "m022_phase1_stochastic_family": m022_phase1_stochastic_family,
    "m022_phase1_reference_pair": m022_phase1_reference_pair,
    "m022_phase1_default_regression": m022_phase1_default_regression,
    "m022_phase1_tests": m022_phase1_tests,
    "m022_inventory_tests": m022_inventory_tests,
    "m022_maxbars_recovery_probe": m022_maxbars_recovery_probe,
    "m022_raise_mt5_maxbars": m022_raise_mt5_maxbars,
    "m022_native_m1_file_probe": m022_native_m1_file_probe,
    "m022_terminal_history_capacity_probe": m022_terminal_history_capacity_probe,
    "m022_history_checkpoint_probe": m022_history_checkpoint_probe,
    "m022_history_depth_probe": m022_history_depth_probe,
    "m022_tick_inventory_cleanup": m022_tick_inventory_cleanup,
    "m022_native_inventory_existing_probe": m022_native_inventory_existing_probe,
    "m022_partition_freeze": m022_partition_freeze,
    "m022_native_inventory": m022_native_inventory,
    "m022_tick_inventory": m022_tick_inventory,
    "m022_history_inventory_cleanup": m022_history_inventory_cleanup,
    "m022_history_inventory": m022_history_inventory,
}


def execute(action):
    try:
        handler = ACTION_HANDLERS[action]
    except KeyError as exc:
        raise ValueError(f"unsupported validation action: {action!r}") from exc
    return handler()
