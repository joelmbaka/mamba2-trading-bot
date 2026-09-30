#!/usr/bin/env python3
import concurrent.futures
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
M022_PHASE1_REGRESSION_DIR = REPO / "backtest_data" / "m022-phase1-regression-v3"
M022_PHASE1_REG_CONTROL_BASELINE = M022_PHASE1_REGRESSION_DIR / "control-baseline.json"
M022_PHASE1_REG_CONTROL_DIAGNOSTIC = M022_PHASE1_REGRESSION_DIR / "control-diagnostic.json"
M022_PHASE1_REG_M020D_BASELINE = M022_PHASE1_REGRESSION_DIR / "m020d-baseline.json"
M022_PHASE1_REG_M020D_DIAGNOSTIC = M022_PHASE1_REGRESSION_DIR / "m020d-diagnostic.json"
M022_PHASE1_REG_M020D_EVIDENCE = M022_PHASE1_REGRESSION_DIR / "m020d-evidence.json"
M022_PHASE1_REFERENCE_DIR = REPO / "backtest_data" / "m022-phase1-development" / "reference-v3"
M022_PHASE1_STOCHASTIC_DIR = REPO / "backtest_data" / "m022-phase1-development" / "stochastic-v1"
M022_PHASE1_STOCH_EQUIV_DIR = REPO / "backtest_data" / "m022-phase1-development" / "stochastic-21-7-7-equivalence-v1"
M022_PHASE1_BOUNDARY_DIR = REPO / "backtest_data" / "m022-phase1-development" / "boundaries-v1"
M022_PHASE1_EMA_DIR = REPO / "backtest_data" / "m022-phase1-development" / "ema-v1"
M022_PHASE1_SPREAD_DIR = REPO / "backtest_data" / "m022-phase1-development" / "spread-v1"
M022_PHASE1_ATR_SL_DIR = REPO / "backtest_data" / "m022-phase1-development" / "atr-sl-v1"
M022_PHASE1_ATR_TP_DIR = REPO / "backtest_data" / "m022-phase1-development" / "atr-tp-v1"
M022_PHASE1_SESSION_DIR = REPO / "backtest_data" / "m022-phase1-development" / "session-v1"
M022_PHASE2_DEV_DIR = REPO / "backtest_data" / "m022-phase2-development-v1"
M022_PHASE2_VALIDATION_DIR = REPO / "backtest_data" / "m022-phase2-validation-v1"
M023_DIRECTION_SESSION_DIR = REPO / "backtest_data" / "m023-direction-session-diagnostics-v1"
M023_STAGE_A_DIRECTION_DIR = REPO / "backtest_data" / "m023-stage-a-direction-v1"
M023_STAGE_B_SESSION_DIR = REPO / "backtest_data" / "m023-stage-b-session-v1"
M024_SYMBOL_SPECIALIZATION_DIR = REPO / "backtest_data" / "m024-symbol-specialization-v1"
M024_STAGE2_SYMBOL_DIR = REPO / "backtest_data" / "m024-stage2-symbol-v1"
M024_HOLDOUT_READINESS_DIR = REPO / "backtest_data" / "m024-holdout-readiness-v1"
M024_HOLDOUT_DIR = REPO / "backtest_data" / "m024-holdout-h-uj-v1"
M025_STAGE3_INGESTION_DIR = REPO / "backtest_data" / "m025-stage3-ingestion-v1"
M025_STAGE4_ECONOMICS_DIR = REPO / "backtest_data" / "m025-stage4-economics-v1"


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



def _require_m023_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "direction-session-research":
        raise RuntimeError(
            "M023 action requires branch direction-session-research"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M023 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "direction-session-research:"
            "refs/remotes/origin/direction-session-research"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M023 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/direction-session-research",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M023 action requires local HEAD to match "
            "origin/direction-session-research"
        )
    return head["stdout"].strip()


def _require_m024_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "symbol-specialization-research":
        raise RuntimeError(
            "M024 action requires branch symbol-specialization-research"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M024 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "symbol-specialization-research:"
            "refs/remotes/origin/symbol-specialization-research"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M024 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/symbol-specialization-research",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M024 action requires local HEAD to match "
            "origin/symbol-specialization-research"
        )
    return head["stdout"].strip()


def _require_m025_branch():
    branch = _run(["git", "branch", "--show-current"])
    name = branch["stdout"].strip()
    if branch["exit_code"] != 0 or name != "public-strategy-benchmarks":
        raise RuntimeError(
            "M025 action requires branch public-strategy-benchmarks"
        )

    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        raise RuntimeError("M025 action refuses a dirty worktree")

    refresh = _run([
        "git",
        "fetch",
        "origin",
        (
            "public-strategy-benchmarks:"
            "refs/remotes/origin/public-strategy-benchmarks"
        ),
    ])
    if refresh["exit_code"] != 0:
        raise RuntimeError("M025 action could not refresh remote branch")

    head = _run(["git", "rev-parse", "HEAD"])
    remote = _run([
        "git",
        "rev-parse",
        "--verify",
        "refs/remotes/origin/public-strategy-benchmarks",
    ])
    if (
        head["exit_code"] != 0
        or remote["exit_code"] != 0
        or head["stdout"].strip() != remote["stdout"].strip()
    ):
        raise RuntimeError(
            "M025 action requires local HEAD to match "
            "origin/public-strategy-benchmarks"
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











def _m022_phase2_expected_parameters():
    """Return the exact pre-frozen Phase-2 development matrix."""

    def params(
        *,
        k=21,
        d=7,
        slowing=7,
        ema=7,
        spread=None,
        sl=1.0,
        tp=2.0,
    ):
        return {
            "stochastic_k_period": int(k),
            "stochastic_d_period": int(d),
            "stochastic_slowing": int(slowing),
            "oversold_level": 20.0,
            "overbought_level": 80.0,
            "ema_period": int(ema),
            "decision_spread_max_points": spread,
            "atr_sl_multiplier": float(sl),
            "atr_tp_multiplier": float(tp),
            "block_00_04_utc": False,
        }

    return {
        "P2-R": params(),
        "P2-01": params(k=28, ema=12),
        "P2-02": params(k=28, spread=12.0),
        "P2-03": params(k=28, sl=1.5),
        "P2-04": params(k=28, tp=3.0),
        "P2-05": params(ema=12, spread=12.0),
        "P2-06": params(spread=12.0, sl=1.5),
        "P2-07": params(spread=12.0, tp=3.0),
        "P2-08": params(sl=1.5, tp=3.0),
        "P2-09": params(k=28, ema=12, spread=12.0),
        "P2-10": params(k=28, spread=12.0, sl=1.5, tp=3.0),
        "P2-11": params(k=28, ema=12, spread=12.0, sl=1.5, tp=3.0),
        "P2-12": params(
            k=14,
            ema=9,
            spread=12.0,
            sl=1.5,
            tp=2.5,
        ),
    }


def m022_phase2_development_family():
    """Run only the 12 frozen non-reference Phase-2 development arms."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    expected = _m022_phase2_expected_parameters()
    labels = tuple(f"P2-{index:02d}" for index in range(1, 13))

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    if any(not path.is_file() for path in reference_files.values()):
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    if reference_summary.get("parameters") != expected["P2-R"]:
        return {
            "ok": False,
            "reason": "reference-v3 does not match frozen P2-R parameters",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE2_DEV_DIR)
    output_root.mkdir(parents=True, exist_ok=True)

    def artifact_paths(label):
        prefix = f"M022-{label}"
        arm_dir = output_root / label
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def existing_payload(label):
        arm_dir, paths = artifact_paths(label)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial Phase-2 arm directory {label}: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing Phase-2 arm {label}"
            )
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-{label}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": json.loads(
                paths["a_summary"].read_text(encoding="utf-8")
            ),
            "reused_complete_artifacts": True,
        }

    def execute_arm(label):
        payload = existing_payload(label)
        if payload is not None:
            return label, payload, None

        arm_dir, _paths = artifact_paths(label)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "phase2",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return label, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return label, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final Phase-2 JSON payload"
                ),
            }
        return label, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, label): label
                for label in labels
            }
            for future in concurrent.futures.as_completed(futures):
                label, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 Phase-2 arm {label} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "arm": label,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[label] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def validate_arm(label, payload):
        summary = payload.get("summary") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        tp_safety = summary.get("tp_safety") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and summary.get("experiment_id") == f"M022-{label}"
            and summary.get("family") == "phase2"
            and summary.get("value_label") == label
            and params == expected[label]
            and summary.get("cost_contract")
            == (
                "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
                "SWAP-UNMODELED"
            )
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(
                tp_safety.get("negative_pl_take_profit_exits", -1)
            ) == 0
            and int(tp_safety.get("wrong_side_initial_tp", -1)) == 0
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 Phase-2 arm {label} failed frozen invariants"
            )
        return {
            "label": label,
            "experiment_id": payload.get("experiment_id"),
            "parameters": params,
            "baseline_sha256": payload.get("baseline_sha256"),
            "diagnostic_sha256": payload.get("diagnostic_sha256"),
            "summary_sha256": payload.get("summary_sha256"),
            "aggregate": summary.get("aggregate"),
            "per_symbol": summary.get("per_symbol"),
            "by_side": summary.get("by_side"),
            "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
            "rejections": summary.get("rejections"),
            "tp_safety": tp_safety,
            "remaining_positions": summary.get("remaining_positions"),
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    try:
        arms = [validate_arm(label, executed[label]) for label in labels]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    reference = {
        "label": "P2-R",
        "experiment_id": "M022-P1-REFERENCE",
        "parameters": expected["P2-R"],
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "aggregate": reference_summary.get("aggregate"),
        "per_symbol": reference_summary.get("per_symbol"),
        "by_side": reference_summary.get("by_side"),
        "by_entry_utc_bucket": reference_summary.get("by_entry_utc_bucket"),
        "rejections": reference_summary.get("rejections"),
        "tp_safety": reference_summary.get("tp_safety"),
        "remaining_positions": reference_summary.get("remaining_positions"),
        "reused_reference_evidence": True,
    }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "phase2-development",
        "execution": {
            "reference_reused": True,
            "nonreference_arm_count": 12,
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "matrix_labels": ["P2-R", *labels],
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
        "reference": reference,
        "arms": arms,
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "development",
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }



def _m022_validation_entrants():
    return ("P2-R", "P2-01", "P2-03", "P2-08")



def m022_phase2_validation_invariant_diagnostic():
    """Read existing validation summaries and report exact invariant checks."""

    feature_sha = _require_m022_branch()
    expected = _m022_phase2_expected_parameters()
    entrants = _m022_validation_entrants()
    rows = []

    for label in entrants:
        arm_dir = M022_PHASE2_VALIDATION_DIR / label
        prefix = f"M022-{label}"
        paths = {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }
        exists = {name: path.is_file() for name, path in paths.items()}
        if not all(exists.values()):
            rows.append({
                "label": label,
                "complete_artifacts": False,
                "exists": exists,
            })
            continue

        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        tp_safety = summary.get("tp_safety") or {}

        checks = {
            "deterministic_baseline": (
                _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            ),
            "deterministic_diagnostic": (
                _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            ),
            "deterministic_summary": (
                _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
            ),
            "experiment_id": summary.get("experiment_id") == f"M022-{label}",
            "family": summary.get("family") == "phase2",
            "value_label": summary.get("value_label") == label,
            "parameters": params == expected[label],
            "cost_contract": summary.get("cost_contract")
            == (
                "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
                "SWAP-UNMODELED"
            ),
            "source_manifest": partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558",
            "partition_name": partition.get("partition") == "validation",
            "start_utc": partition.get("start_utc") == "2026-04-21T00:00:00Z",
            "end_exclusive_utc": (
                partition.get("end_exclusive_utc") == "2026-07-08T00:00:00Z"
            ),
            "strict_common_boundary_clock": (
                partition.get("strict_common_boundary_clock") is True
            ),
            "full_symbol_m1_preserved": (
                partition.get("full_symbol_m1_preserved") is True
            ),
            "replay_boundary_count": (
                int(partition.get("replay_boundary_count", 0)) > 0
            ),
            "replay_boundary_sha256": bool(
                partition.get("replay_boundary_sha256")
            ),
            "tp_negative_pl_zero": int(
                tp_safety.get("negative_pl_take_profit_exits", -1)
            ) == 0,
            "tp_wrong_side_zero": int(
                tp_safety.get("wrong_side_initial_tp", -1)
            ) == 0,
        }
        rows.append({
            "label": label,
            "complete_artifacts": True,
            "checks": checks,
            "failed_checks": [
                name for name, passed in checks.items() if not passed
            ],
            "observed": {
                "experiment_id": summary.get("experiment_id"),
                "family": summary.get("family"),
                "value_label": summary.get("value_label"),
                "parameters": params,
                "partition": partition,
                "tp_safety": tp_safety,
                "baseline_sha256": _sha256(paths["a_baseline"]),
                "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
                "summary_sha256": _sha256(paths["a_summary"]),
            },
        })

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "entrants": list(entrants),
        "rows": rows,
        "safety": {
            "economic_replay_run": False,
            "read_existing_validation_artifacts_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase2_validation_family():
    """Run exactly the frozen Phase-2 validation entrants."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    expected = _m022_phase2_expected_parameters()
    entrants = _m022_validation_entrants()
    output_root = _ensure_baseline_path(M022_PHASE2_VALIDATION_DIR)
    output_root.mkdir(parents=True, exist_ok=True)

    def artifact_paths(label):
        prefix = f"M022-{label}"
        arm_dir = output_root / label
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def existing_payload(label):
        arm_dir, paths = artifact_paths(label)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial Phase-2 validation directory {label}: "
                + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing Phase-2 validation arm {label}"
            )
        return {
            "ok": True,
            "deterministic": True,
            "partition": "validation",
            "experiment_id": f"M022-{label}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": json.loads(
                paths["a_summary"].read_text(encoding="utf-8")
            ),
            "reused_complete_artifacts": True,
        }

    def execute_arm(label):
        payload = existing_payload(label)
        if payload is not None:
            return label, payload, None

        arm_dir, _paths = artifact_paths(label)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "phase2-validation",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return label, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return label, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final validation JSON payload"
                ),
            }
        return label, payload, run

    executed = {}
    try:
        # Run P2-R first, then at most two independent non-reference entrants
        # concurrently as frozen.
        label, payload, run = execute_arm("P2-R")
        if payload is None:
            return {
                "ok": False,
                "reason": "M022 validation reference failed",
                "feature_branch": "strategy-parameter-research",
                "feature_sha": feature_sha,
                "failed_run": {
                    "arm": label,
                    "exit_code": (run or {}).get("exit_code"),
                    "stdout": _bounded((run or {}).get("stdout")),
                    "stderr": _bounded((run or {}).get("stderr")),
                },
            }
        executed[label] = payload

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, label): label
                for label in entrants
                if label != "P2-R"
            }
            for future in concurrent.futures.as_completed(futures):
                label, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 validation arm {label} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "arm": label,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[label] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def validate_arm(label, payload):
        summary = payload.get("summary") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        tp_safety = summary.get("tp_safety") or {}

        structural_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "validation"
            and summary.get("experiment_id") == f"M022-{label}"
            and summary.get("family") == "phase2"
            and summary.get("value_label") == label
            and params == expected[label]
            and summary.get("cost_contract")
            == (
                "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
                "SWAP-UNMODELED"
            )
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("partition") == "validation"
            and partition.get("start_utc") == "2026-04-21T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-07-08T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
        )
        if not structural_ok:
            raise RuntimeError(
                f"M022 validation arm {label} failed structural invariants"
            )

        tp_safety_ok = bool(
            int(tp_safety.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp_safety.get("wrong_side_initial_tp", -1)) == 0
        )
        if label == "P2-R" and not tp_safety_ok:
            raise RuntimeError(
                "M022 validation reference failed mandatory TP safety"
            )

        return {
            "label": label,
            "experiment_id": payload.get("experiment_id"),
            "parameters": params,
            "baseline_sha256": payload.get("baseline_sha256"),
            "diagnostic_sha256": payload.get("diagnostic_sha256"),
            "summary_sha256": payload.get("summary_sha256"),
            "aggregate": summary.get("aggregate"),
            "per_symbol": summary.get("per_symbol"),
            "by_side": summary.get("by_side"),
            "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
            "rejections": summary.get("rejections"),
            "tp_safety": tp_safety,
            "tp_safety_gate_passes": tp_safety_ok,
            "remaining_positions": summary.get("remaining_positions"),
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    try:
        rows = [validate_arm(label, executed[label]) for label in entrants]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "phase2-validation",
        "execution": {
            "entrants": list(entrants),
            "entrant_count": len(entrants),
            "maximum_concurrent_nonreference_arms": 2,
            "reference_ran_first": True,
            "independent_arm_processes": True,
        },
        "partition": {
            "name": "validation",
            "start_utc": "2026-04-21T00:00:00Z",
            "end_exclusive_utc": "2026-07-08T00:00:00Z",
            "trading_dates": 56,
        },
        "reference": rows[0],
        "arms": rows[1:],
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "validation",
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase2_validation_assessment():
    """Apply the frozen M022 validation support rules mechanically."""

    feature_sha = _require_m022_branch()
    expected = _m022_phase2_expected_parameters()
    entrants = _m022_validation_entrants()

    summaries = {}
    for label in entrants:
        path = (
            M022_PHASE2_VALIDATION_DIR
            / label
            / f"M022-{label}-a-summary.json"
        )
        if not path.is_file():
            return {
                "ok": False,
                "reason": f"validation summary missing for {label}",
                "feature_sha": feature_sha,
                "path": str(path.relative_to(REPO)),
            }
        summaries[label] = json.loads(path.read_text(encoding="utf-8"))

    reference = summaries["P2-R"]
    ref_agg = reference.get("aggregate") or {}
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    def closed(mapping):
        return int((mapping or {}).get("closed_trades", 0))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    def sample_gate(summary):
        agg = summary.get("aggregate") or {}
        symbols = summary.get("per_symbol") or {}
        sides = summary.get("by_side") or {}
        buckets = summary.get("by_entry_utc_bucket") or {}

        total_ratio = (
            closed(agg) / closed(ref_agg) if closed(ref_agg) else None
        )
        symbol_ratios = {
            name: (
                closed(symbols.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_symbols.items()
        }
        side_ratios = {
            name: (
                closed(sides.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_sides.items()
        }
        bucket_ratios = {
            name: (
                closed(buckets.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_buckets.items()
        }
        passes = bool(
            total_ratio is not None
            and total_ratio >= 0.50
            and all(
                value is not None and value >= 0.40
                for value in symbol_ratios.values()
            )
            and all(
                value is not None and value >= 0.40
                for value in side_ratios.values()
            )
            and len(bucket_ratios) == 6
            and all(
                value is not None and value >= 0.25
                for value in bucket_ratios.values()
            )
        )
        return {
            "passes": passes,
            "total_ratio": total_ratio,
            "symbol_ratios": symbol_ratios,
            "side_ratios": side_ratios,
            "bucket_ratios": bucket_ratios,
        }

    rows = []
    for label in entrants:
        summary = summaries[label]
        aggregate = summary.get("aggregate") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        tp = summary.get("tp_safety") or {}
        sample = sample_gate(summary)

        invariant_ok = bool(
            params == expected[label]
            and summary.get("cost_contract")
            == (
                "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
                "SWAP-UNMODELED"
            )
            and partition.get("partition") == "validation"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2026-04-21T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-07-08T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
        )
        mandatory_ok = bool(invariant_ok and sample["passes"])

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        dd = float(aggregate.get("maximum_equity_drawdown", 0.0))
        win_rate_raw = aggregate.get("win_rate_nonflat_pct")
        win_rate = None if win_rate_raw is None else float(win_rate_raw)

        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        ref_dd = float(ref_agg.get("maximum_equity_drawdown", 0.0))
        ref_wr_raw = ref_agg.get("win_rate_nonflat_pct")
        ref_wr = None if ref_wr_raw is None else float(ref_wr_raw)

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        support_checks = {
            "mandatory_gates": mandatory_ok,
            "net_pl_strictly_better": net_pl > ref_net,
            "max_dd_no_worse": dd <= ref_dd,
            "win_rate_within_one_percentage_point": bool(
                win_rate is not None
                and ref_wr is not None
                and win_rate >= ref_wr - 1.0
            ),
            "symbol_positive_delta_min_2": (
                symbol_delta["positive_count"] >= 2
            ),
            "utc_bucket_positive_delta_min_2": (
                bucket_delta["positive_count"] >= 2
            ),
            "symbol_concentration_max_70pct": bool(
                symbol_delta["max_positive_share"] is not None
                and symbol_delta["max_positive_share"] <= 0.70
            ),
            "side_concentration_max_80pct": bool(
                side_delta["max_positive_share"] is not None
                and side_delta["max_positive_share"] <= 0.80
            ),
        }
        supported = bool(
            label != "P2-R" and all(support_checks.values())
        )

        rows.append({
            "label": label,
            "is_reference": label == "P2-R",
            "mandatory_ok": mandatory_ok,
            "sample_gate": sample,
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": dd,
                "win_rate_nonflat_pct": win_rate,
            },
            "support_checks": support_checks,
            "supported": supported,
            "breadth": {
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
            "accepted_orders": int(aggregate.get("accepted_orders", 0)),
            "closed_trades": int(aggregate.get("closed_trades", 0)),
            "ending_realized_balance": aggregate.get(
                "ending_realized_balance"
            ),
            "ending_equity": aggregate.get("ending_equity"),
            "maximum_equity_drawdown_pct": aggregate.get(
                "maximum_equity_drawdown_pct"
            ),
            "decision_spread_rejections": int(
                (summary.get("rejections") or {}).get("decision_spread", 0)
            ),
            "remaining_open_positions": int(
                aggregate.get("remaining_open_positions", 0)
            ),
        })

    supported_rows = [row for row in rows if row["supported"]]

    ref_obj = next(
        row["objectives"] for row in rows if row["label"] == "P2-R"
    )

    def robustness(row):
        obj = row["objectives"]
        ref_pl = float(ref_obj["net_realized_pl"])
        ref_dd = float(ref_obj["maximum_equity_drawdown"])
        ref_wr = float(ref_obj["win_rate_nonflat_pct"])
        pl_gain = (
            (float(obj["net_realized_pl"]) - ref_pl) / abs(ref_pl)
            if ref_pl
            else 0.0
        )
        dd_gain = (
            (ref_dd - float(obj["maximum_equity_drawdown"])) / ref_dd
            if ref_dd
            else 0.0
        )
        wr_gain = (
            (float(obj["win_rate_nonflat_pct"]) - ref_wr) / ref_wr
            if ref_wr
            else 0.0
        )
        return {
            "pl_gain_fraction": pl_gain,
            "dd_improvement_fraction": dd_gain,
            "win_rate_gain_fraction": wr_gain,
            "maximin": min(pl_gain, dd_gain, wr_gain),
        }

    for row in supported_rows:
        row["robustness"] = robustness(row)

    if len(supported_rows) <= 2:
        holdout_entrants = [row["label"] for row in supported_rows]
    else:
        ranked = sorted(
            supported_rows,
            key=lambda row: (
                -float(row["robustness"]["maximin"]),
                -int(row["breadth"]["symbol"]["positive_count"]),
                -int(
                    row["breadth"]["entry_utc_bucket"]["positive_count"]
                ),
                -float(row["sample_gate"]["total_ratio"]),
                row["label"],
            ),
        )
        holdout_entrants = [row["label"] for row in ranked[:2]]

    for row in rows:
        if row["is_reference"]:
            row["validation_status"] = "REFERENCE"
        elif not row["mandatory_ok"]:
            row["validation_status"] = "INELIGIBLE"
        elif row["supported"]:
            row["validation_status"] = "SUPPORTED"
        else:
            row["validation_status"] = "NOT SUPPORTED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "phase2-validation",
        "rubric": {
            "sample_gate": {
                "total_fraction": 0.50,
                "per_symbol_fraction": 0.40,
                "per_side_fraction": 0.40,
                "per_utc_bucket_fraction": 0.25,
            },
            "support": {
                "net_pl": "strictly better than validation P2-R",
                "maximum_equity_drawdown": "no worse than validation P2-R",
                "win_rate_nonflat_pct": (
                    "no more than 1.0 percentage point below validation P2-R"
                ),
                "symbol_positive_delta_min_count": 2,
                "calendar_bucket_positive_delta_min_count": 2,
                "max_symbol_positive_delta_share": 0.70,
                "max_side_positive_delta_share": 0.80,
            },
            "holdout_nonreference_cap": 2,
        },
        "supported_candidates": [
            row["label"] for row in supported_rows
        ],
        "holdout_entrants": holdout_entrants,
        "arms": rows,
        "historical_holdout_execution_authorized": False,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_validation_results_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase2_development_assessment():
    """Apply the completely frozen Phase-2 development rubric mechanically."""

    feature_sha = _require_m022_branch()
    expected = _m022_phase2_expected_parameters()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted P2-R reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    labels = tuple(f"P2-{index:02d}" for index in range(1, 13))
    summaries = {}
    for label in labels:
        path = (
            M022_PHASE2_DEV_DIR
            / label
            / f"M022-{label}-a-summary.json"
        )
        if not path.is_file():
            return {
                "ok": False,
                "reason": f"Phase-2 summary missing for {label}",
                "feature_sha": feature_sha,
                "path": str(path.relative_to(REPO)),
            }
        summaries[label] = json.loads(path.read_text(encoding="utf-8"))

    ref_agg = reference.get("aggregate") or {}
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    def closed(mapping):
        return int((mapping or {}).get("closed_trades", 0))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    def sample_gate(summary):
        agg = summary.get("aggregate") or {}
        symbols = summary.get("per_symbol") or {}
        sides = summary.get("by_side") or {}
        buckets = summary.get("by_entry_utc_bucket") or {}

        total_ratio = (
            closed(agg) / closed(ref_agg) if closed(ref_agg) else None
        )
        symbol_ratios = {
            name: (
                closed(symbols.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_symbols.items()
        }
        side_ratios = {
            name: (
                closed(sides.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_sides.items()
        }
        bucket_ratios = {
            name: (
                closed(buckets.get(name)) / closed(ref_row)
                if closed(ref_row)
                else None
            )
            for name, ref_row in ref_buckets.items()
        }

        passes = bool(
            total_ratio is not None
            and total_ratio >= 0.50
            and all(
                value is not None and value >= 0.40
                for value in symbol_ratios.values()
            )
            and all(
                value is not None and value >= 0.40
                for value in side_ratios.values()
            )
            and len(bucket_ratios) == 6
            and all(
                value is not None and value >= 0.25
                for value in bucket_ratios.values()
            )
        )
        return {
            "passes": passes,
            "total_ratio": total_ratio,
            "symbol_ratios": symbol_ratios,
            "side_ratios": side_ratios,
            "bucket_ratios": bucket_ratios,
        }

    rows = []
    all_summaries = {"P2-R": reference, **summaries}
    for label, summary in all_summaries.items():
        aggregate = summary.get("aggregate") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        tp = summary.get("tp_safety") or {}
        sample = sample_gate(summary)

        invariant_ok = bool(
            params == expected[label]
            and summary.get("cost_contract")
            == (
                "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
                "SWAP-UNMODELED"
            )
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
        )
        mandatory_ok = bool(invariant_ok and sample["passes"])

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net
        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )
        breadth_ok = True
        if label != "P2-R" and improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        rows.append({
            "label": label,
            "is_reference": label == "P2-R",
            "mandatory_ok": mandatory_ok,
            "sample_gate": sample,
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
            "accepted_orders": int(aggregate.get("accepted_orders", 0)),
            "closed_trades": int(aggregate.get("closed_trades", 0)),
            "ending_realized_balance": aggregate.get(
                "ending_realized_balance"
            ),
            "ending_equity": aggregate.get("ending_equity"),
            "maximum_equity_drawdown_pct": aggregate.get(
                "maximum_equity_drawdown_pct"
            ),
            "decision_spread_rejections": int(
                (summary.get("rejections") or {}).get("decision_spread", 0)
            ),
            "remaining_open_positions": int(
                aggregate.get("remaining_open_positions", 0)
            ),
        })

    eligible = [row for row in rows if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)
    nondominated_labels = {row["label"] for row in nondominated}

    shortlist = []
    for row in rows:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row)
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    ref_obj = next(
        row["objectives"] for row in rows if row["label"] == "P2-R"
    )

    def robustness(row):
        obj = row["objectives"]
        ref_pl = float(ref_obj["net_realized_pl"])
        ref_dd = float(ref_obj["maximum_equity_drawdown"])
        ref_wr = float(ref_obj["win_rate_nonflat_pct"])
        pl_gain = (
            (float(obj["net_realized_pl"]) - ref_pl) / abs(ref_pl)
            if ref_pl
            else 0.0
        )
        dd_gain = (
            (ref_dd - float(obj["maximum_equity_drawdown"])) / ref_dd
            if ref_dd
            else 0.0
        )
        wr_gain = (
            (float(obj["win_rate_nonflat_pct"]) - ref_wr) / ref_wr
            if ref_wr
            else 0.0
        )
        return {
            "pl_gain_fraction": pl_gain,
            "dd_improvement_fraction": dd_gain,
            "win_rate_gain_fraction": wr_gain,
            "maximin": min(pl_gain, dd_gain, wr_gain),
        }

    for row in shortlist:
        row["robustness"] = robustness(row)

    if len(shortlist) <= 3:
        finalists = [row["label"] for row in shortlist]
    else:
        ranked = sorted(
            shortlist,
            key=lambda row: (
                -float(row["robustness"]["maximin"]),
                -int(row["breadth"]["symbol"]["positive_count"]),
                -int(
                    row["breadth"]["entry_utc_bucket"]["positive_count"]
                ),
                -float(row["sample_gate"]["total_ratio"]),
                row["label"],
            ),
        )
        finalists = [row["label"] for row in ranked[:3]]

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "phase2-development",
        "rubric": {
            "sample_gate": {
                "total_fraction": 0.50,
                "per_symbol_fraction": 0.40,
                "per_side_fraction": 0.40,
                "per_utc_bucket_fraction": 0.25,
            },
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "development_finalist_cap": 3,
            "reference_always_retained": True,
        },
        "shortlist": [row["label"] for row in shortlist],
        "development_finalists": finalists,
        "arms": rows,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_session_assessment():
    """Apply the frozen one-hypothesis session rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    blocked_path = (
        M022_PHASE1_SESSION_DIR
        / "block-00-04-utc"
        / "M022-P1-SESSION-BLOCK-00-04-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not blocked_path.is_file():
        return {
            "ok": False,
            "reason": "M022 blocked-session summary is unavailable",
            "feature_sha": feature_sha,
            "path": str(blocked_path.relative_to(REPO)),
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    blocked = json.loads(blocked_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    arms = []
    for label, summary, is_reference in (
        ("all-hours", reference, True),
        ("block-00-04-utc", blocked, False),
    ):
        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        rejections = summary.get("rejections") or {}
        blocked_count = int(rejections.get("session_evaluation_boundaries", 0))

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and float(params.get("oversold_level", -1.0)) == 20.0
            and float(params.get("overbought_level", -1.0)) == 80.0
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == 7
            and params.get("decision_spread_max_points") is None
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
            and bool(params.get("block_00_04_utc")) is (not is_reference)
            and (
                blocked_count == 0
                if is_reference
                else blocked_count > 0
            )
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "label": label,
            "is_reference": is_reference,
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "session_evaluation_boundaries": blocked_count,
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "session",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "authorized_nonreference_variant": "block-00-04-utc",
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_session_family():
    """Run the sole frozen session hypothesis; reuse all-hours reference."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen session Phase-1 reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_SESSION_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    label = "block-00-04-utc"
    arm_dir = output_root / label
    prefix = "M022-P1-SESSION-BLOCK-00-04"
    paths = {
        "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
        "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
        "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
        "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
        "a_summary": arm_dir / f"{prefix}-a-summary.json",
        "b_summary": arm_dir / f"{prefix}-b-summary.json",
    }

    def payload_from_complete_artifacts():
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                "partial session arm directory: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                "non-deterministic existing blocked-session arm"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": prefix,
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    try:
        payload = payload_from_complete_artifacts()
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    run = None
    if payload is None:
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "session",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M022 blocked-session arm failed",
                "feature_branch": "strategy-parameter-research",
                "feature_sha": feature_sha,
                "failed_run": {
                    "exit_code": run["exit_code"],
                    "stdout": run["stdout"],
                    "stderr": run["stderr"],
                },
            }
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return {
                "ok": False,
                "reason": "unable to parse blocked-session JSON payload",
                "feature_sha": feature_sha,
                "failed_run": run,
            }

    summary = payload.get("summary") or {}
    tp = summary.get("tp_safety") or {}
    partition = summary.get("partition") or {}
    params = summary.get("parameters") or {}
    rejections = summary.get("rejections") or {}
    blocked_count = int(rejections.get("session_evaluation_boundaries", 0))
    arm_ok = bool(
        payload.get("ok")
        and payload.get("deterministic")
        and payload.get("partition") == "development"
        and partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
        and partition.get("start_utc") == "2025-08-25T00:00:00Z"
        and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
        and partition.get("strict_common_boundary_clock") is True
        and partition.get("full_symbol_m1_preserved") is True
        and int(partition.get("replay_boundary_count", 0)) > 0
        and bool(partition.get("replay_boundary_sha256"))
        and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
        and int(tp.get("wrong_side_initial_tp", -1)) == 0
        and float(params.get("oversold_level", -1.0)) == 20.0
        and float(params.get("overbought_level", -1.0)) == 80.0
        and int(params.get("stochastic_k_period", -1)) == 21
        and int(params.get("stochastic_d_period", -1)) == 7
        and int(params.get("stochastic_slowing", -1)) == 7
        and int(params.get("ema_period", -1)) == 7
        and params.get("decision_spread_max_points") is None
        and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
        and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
        and bool(params.get("block_00_04_utc")) is True
        and blocked_count > 0
    )
    if not arm_ok:
        return {
            "ok": False,
            "reason": "M022 blocked-session arm failed invariants",
            "feature_sha": feature_sha,
        }

    reference_payload = {
        "label": "all-hours",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "aggregate": reference_summary.get("aggregate"),
        "per_symbol": reference_summary.get("per_symbol"),
        "by_side": reference_summary.get("by_side"),
        "by_entry_utc_bucket": reference_summary.get("by_entry_utc_bucket"),
        "protection": reference_summary.get("protection"),
        "rejections": reference_summary.get("rejections"),
        "tp_safety": reference_summary.get("tp_safety"),
        "remaining_positions": reference_summary.get("remaining_positions"),
        "reused_reference_evidence": True,
    }
    blocked_payload = {
        "label": label,
        "experiment_id": payload.get("experiment_id"),
        "baseline_sha256": payload.get("baseline_sha256"),
        "diagnostic_sha256": payload.get("diagnostic_sha256"),
        "summary_sha256": payload.get("summary_sha256"),
        "aggregate": summary.get("aggregate"),
        "per_symbol": summary.get("per_symbol"),
        "by_side": summary.get("by_side"),
        "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
        "protection": summary.get("protection"),
        "rejections": rejections,
        "session_evaluation_boundaries": blocked_count,
        "tp_safety": tp,
        "remaining_positions": summary.get("remaining_positions"),
        "reused_complete_artifacts": bool(
            payload.get("reused_complete_artifacts")
        ),
    }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "session",
        "execution": {
            "reference_all_hours_reused": True,
            "authorized_nonreference_variant": label,
            "blocked_utc_hours": [0, 1, 2, 3],
            "existing_position_management_continues": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
        "arms": [reference_payload, blocked_payload],
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "development",
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_atr_tp_assessment():
    """Apply the frozen ATR-TP shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_ATR_TP_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 ATR-TP family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    multipliers = (1.0, 1.5, 2.0, 2.5, 3.0)
    arms = []
    for multiplier in multipliers:
        label = f"{multiplier:g}"
        if multiplier == 2.0:
            summary = reference
            summary_path = reference_path
        else:
            summary_path = (
                M022_PHASE1_ATR_TP_DIR
                / label
                / f"M022-P1-ATR-TP-{label}-a-summary.json"
            )
            if not summary_path.is_file():
                return {
                    "ok": False,
                    "reason": f"ATR-TP summary missing for {label}",
                    "feature_sha": feature_sha,
                    "path": str(summary_path.relative_to(REPO)),
                }
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == multiplier
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "atr_tp_multiplier": multiplier,
            "label": label,
            "is_reference": multiplier == 2.0,
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "atr-tp",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "fixed_atr_sl_multiplier": 1.0,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_atr_tp_family():
    """Run frozen ATR-TP screen with SL fixed at 1.0x."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen ATR-TP Phase-1 reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_ATR_TP_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    multipliers = (1.0, 1.5, 2.5, 3.0)

    def label_for(multiplier):
        return f"{multiplier:g}"

    def artifact_paths(multiplier):
        label = label_for(multiplier)
        prefix = f"M022-P1-ATR-TP-{label}"
        arm_dir = output_root / label
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(multiplier):
        label = label_for(multiplier)
        arm_dir, paths = artifact_paths(multiplier)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial ATR-TP arm directory {label}: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing ATR-TP arm {label}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-ATR-TP-{label}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(multiplier):
        existing = payload_from_complete_artifacts(multiplier)
        if existing is not None:
            return multiplier, existing, None

        label = label_for(multiplier)
        arm_dir, _paths = artifact_paths(multiplier)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "atr-tp",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return multiplier, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return multiplier, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final ATR-TP JSON payload"
                ),
            }
        return multiplier, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, multiplier): multiplier
                for multiplier in multipliers
            }
            for future in concurrent.futures.as_completed(futures):
                multiplier, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 ATR-TP arm {multiplier:g} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "atr_tp_multiplier": multiplier,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[multiplier] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def arm_result(multiplier, payload, *, reused_reference=False):
        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and float(params.get("oversold_level", -1.0)) == 20.0
            and float(params.get("overbought_level", -1.0)) == 80.0
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == 7
            and params.get("decision_spread_max_points") is None
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == multiplier
            and not bool(params.get("block_00_04_utc"))
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 ATR-TP arm {multiplier:g} failed invariants"
            )
        return {
            "atr_tp_multiplier": multiplier,
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
            "remaining_positions": summary.get("remaining_positions"),
            "reused_reference_evidence": reused_reference,
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    reference_payload = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "summary": reference_summary,
    }

    try:
        results = [
            arm_result(1.0, executed[1.0]),
            arm_result(1.5, executed[1.5]),
            arm_result(2.0, reference_payload, reused_reference=True),
            arm_result(2.5, executed[2.5]),
            arm_result(3.0, executed[3.0]),
        ]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "atr-tp",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_atr_sl_1_tp_2_reused": True,
            "fixed_atr_sl_multiplier": 1.0,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
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


def m022_phase1_atr_sl_assessment():
    """Apply the frozen ATR-SL shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_ATR_SL_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 ATR-SL family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    multipliers = (0.75, 1.0, 1.25, 1.5)
    arms = []
    for multiplier in multipliers:
        label = f"{multiplier:g}"
        if multiplier == 1.0:
            summary = reference
            summary_path = reference_path
        else:
            summary_path = (
                M022_PHASE1_ATR_SL_DIR
                / label
                / f"M022-P1-ATR-SL-{label}-a-summary.json"
            )
            if not summary_path.is_file():
                return {
                    "ok": False,
                    "reason": f"ATR-SL summary missing for {label}",
                    "feature_sha": feature_sha,
                    "path": str(summary_path.relative_to(REPO)),
                }
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and float(params.get("atr_sl_multiplier", -1.0)) == multiplier
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "atr_sl_multiplier": multiplier,
            "label": label,
            "is_reference": multiplier == 1.0,
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "atr-sl",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "fixed_atr_tp_multiplier": 2.0,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_atr_sl_family():
    """Run frozen ATR-SL screen with TP fixed at 2.0x."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen ATR-SL Phase-1 reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_ATR_SL_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    multipliers = (0.75, 1.25, 1.5)

    def label_for(multiplier):
        return f"{multiplier:g}"

    def artifact_paths(multiplier):
        label = label_for(multiplier)
        prefix = f"M022-P1-ATR-SL-{label}"
        arm_dir = output_root / label
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(multiplier):
        label = label_for(multiplier)
        arm_dir, paths = artifact_paths(multiplier)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial ATR-SL arm directory {label}: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing ATR-SL arm {label}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-ATR-SL-{label}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(multiplier):
        existing = payload_from_complete_artifacts(multiplier)
        if existing is not None:
            return multiplier, existing, None

        label = label_for(multiplier)
        arm_dir, _paths = artifact_paths(multiplier)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "atr-sl",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return multiplier, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return multiplier, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final ATR-SL JSON payload"
                ),
            }
        return multiplier, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, multiplier): multiplier
                for multiplier in multipliers
            }
            for future in concurrent.futures.as_completed(futures):
                multiplier, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 ATR-SL arm {multiplier:g} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "atr_sl_multiplier": multiplier,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[multiplier] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def arm_result(multiplier, payload, *, reused_reference=False):
        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and float(params.get("oversold_level", -1.0)) == 20.0
            and float(params.get("overbought_level", -1.0)) == 80.0
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == 7
            and params.get("decision_spread_max_points") is None
            and float(params.get("atr_sl_multiplier", -1.0)) == multiplier
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
            and not bool(params.get("block_00_04_utc"))
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 ATR-SL arm {multiplier:g} failed invariants"
            )
        return {
            "atr_sl_multiplier": multiplier,
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
            "remaining_positions": summary.get("remaining_positions"),
            "reused_reference_evidence": reused_reference,
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    reference_payload = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "summary": reference_summary,
    }

    try:
        results = [
            arm_result(0.75, executed[0.75]),
            arm_result(1.0, reference_payload, reused_reference=True),
            arm_result(1.25, executed[1.25]),
            arm_result(1.5, executed[1.5]),
        ]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "atr-sl",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_atr_sl_1_tp_2_reused": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
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


def m022_phase1_spread_assessment():
    """Apply the frozen decision-time-spread shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_SPREAD_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 spread family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    thresholds = (None, 5, 8, 10, 12, 15)
    arms = []
    for threshold in thresholds:
        label = "none" if threshold is None else str(threshold)
        if threshold is None:
            summary = reference
            summary_path = reference_path
        else:
            summary_path = (
                M022_PHASE1_SPREAD_DIR
                / label
                / f"M022-P1-SPREAD-{label}-a-summary.json"
            )
            if not summary_path.is_file():
                return {
                    "ok": False,
                    "reason": f"spread summary missing for {label}",
                    "feature_sha": feature_sha,
                    "path": str(summary_path.relative_to(REPO)),
                }
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        rejections = summary.get("rejections") or {}
        rejection_accounting_ok = (
            threshold is None
            or (
                "decision_spread" in rejections
                and int(rejections.get("decision_spread", -1)) >= 0
            )
        )

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and rejection_accounting_ok
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "threshold_points": threshold,
            "label": label,
            "is_reference": threshold is None,
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "decision_spread_rejections": int(
                rejections.get("decision_spread", 0)
            ),
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "spread",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
            "decision_time_bid_ask_only": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_spread_family():
    """Run frozen decision-time spread screening; reuse accepted reference."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen no-spread-gate reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_SPREAD_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    thresholds = (5, 8, 10, 12, 15)

    def artifact_paths(threshold):
        label = str(threshold)
        prefix = f"M022-P1-SPREAD-{label}"
        arm_dir = output_root / label
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(threshold):
        label = str(threshold)
        arm_dir, paths = artifact_paths(threshold)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial spread arm directory {label}: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing spread arm {label}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-SPREAD-{label}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(threshold):
        existing = payload_from_complete_artifacts(threshold)
        if existing is not None:
            return threshold, existing, None

        label = str(threshold)
        arm_dir, _paths = artifact_paths(threshold)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "spread",
                "--value",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return threshold, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return threshold, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final spread JSON payload"
                ),
            }
        return threshold, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, threshold): threshold
                for threshold in thresholds
            }
            for future in concurrent.futures.as_completed(futures):
                threshold, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 spread arm {threshold} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "threshold_points": threshold,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[threshold] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def arm_result(threshold, payload, *, reused_reference=False):
        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        rejections = summary.get("rejections") or {}
        expected_spread = None if threshold is None else float(threshold)
        actual_spread = params.get("decision_spread_max_points")
        spread_matches = (
            actual_spread is None
            if expected_spread is None
            else actual_spread is not None
            and float(actual_spread) == expected_spread
        )
        rejection_accounting_ok = (
            expected_spread is None
            or (
                "decision_spread" in rejections
                and int(rejections.get("decision_spread", -1)) >= 0
            )
        )
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and float(params.get("oversold_level", -1.0)) == 20.0
            and float(params.get("overbought_level", -1.0)) == 80.0
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == 7
            and spread_matches
            and rejection_accounting_ok
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
            and not bool(params.get("block_00_04_utc"))
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 spread arm {threshold} failed invariants"
            )
        return {
            "threshold_points": threshold,
            "experiment_id": payload.get("experiment_id"),
            "baseline_sha256": payload.get("baseline_sha256"),
            "diagnostic_sha256": payload.get("diagnostic_sha256"),
            "summary_sha256": payload.get("summary_sha256"),
            "aggregate": summary.get("aggregate"),
            "per_symbol": summary.get("per_symbol"),
            "by_side": summary.get("by_side"),
            "by_entry_utc_bucket": summary.get("by_entry_utc_bucket"),
            "protection": summary.get("protection"),
            "rejections": rejections,
            "tp_safety": tp,
            "remaining_positions": summary.get("remaining_positions"),
            "reused_reference_evidence": reused_reference,
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    reference_payload = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "summary": reference_summary,
    }

    try:
        results = [
            arm_result(None, reference_payload, reused_reference=True),
            arm_result(5, executed[5]),
            arm_result(8, executed[8]),
            arm_result(10, executed[10]),
            arm_result(12, executed[12]),
            arm_result(15, executed[15]),
        ]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "spread",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_no_spread_gate_reused": True,
            "decision_time_bid_ask_only": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
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


def m022_phase1_ema_assessment():
    """Apply the frozen EMA-family shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_EMA_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 EMA family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    periods = (5, 7, 9, 12)
    arms = []
    for period in periods:
        if period == 7:
            summary = reference
            summary_path = reference_path
        else:
            summary_path = (
                M022_PHASE1_EMA_DIR
                / str(period)
                / f"M022-P1-EMA-{period}-a-summary.json"
            )
            if not summary_path.is_file():
                return {
                    "ok": False,
                    "reason": f"EMA summary missing for {period}",
                    "feature_sha": feature_sha,
                    "path": str(summary_path.relative_to(REPO)),
                }
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "period": period,
            "label": str(period),
            "is_reference": period == 7,
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "ema",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_ema_family():
    """Run frozen EMA screening; reuse accepted EMA7 reference."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen EMA7 Phase-1 reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_EMA_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    periods = (5, 9, 12)

    def artifact_paths(period):
        prefix = f"M022-P1-EMA-{period}"
        arm_dir = output_root / str(period)
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(period):
        arm_dir, paths = artifact_paths(period)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial EMA arm directory {period}: " + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing EMA arm {period}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-EMA-{period}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(period):
        existing = payload_from_complete_artifacts(period)
        if existing is not None:
            return period, existing, None

        arm_dir, _paths = artifact_paths(period)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "ema",
                "--value",
                str(period),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return period, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return period, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final EMA JSON payload"
                ),
            }
        return period, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, period): period
                for period in periods
            }
            for future in concurrent.futures.as_completed(futures):
                period, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": f"M022 EMA arm {period} failed",
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "period": period,
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[period] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def arm_result(period, payload, *, reused_reference=False):
        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and float(params.get("oversold_level", -1.0)) == 20.0
            and float(params.get("overbought_level", -1.0)) == 80.0
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == int(period)
            and params.get("decision_spread_max_points") is None
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
            and not bool(params.get("block_00_04_utc"))
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 EMA arm {period} failed invariants"
            )
        return {
            "period": period,
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
            "remaining_positions": summary.get("remaining_positions"),
            "reused_reference_evidence": reused_reference,
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    reference_payload = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "summary": reference_summary,
    }

    try:
        results = [
            arm_result(5, executed[5]),
            arm_result(7, reference_payload, reused_reference=True),
            arm_result(9, executed[9]),
            arm_result(12, executed[12]),
        ]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "ema",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_ema7_reused": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
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


def m022_phase1_boundary_assessment():
    """Apply the frozen boundary-family shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_BOUNDARY_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 boundary family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    pairs = ((15, 85), (20, 80), (25, 75))
    arms = []
    for low, high in pairs:
        if (low, high) == (20, 80):
            summary = reference
            summary_path = reference_path
        else:
            summary_path = (
                M022_PHASE1_BOUNDARY_DIR
                / f"{low}-{high}"
                / f"M022-P1-BOUND-{low}-{high}-a-summary.json"
            )
            if not summary_path.is_file():
                return {
                    "ok": False,
                    "reason": f"boundary summary missing for {low}/{high}",
                    "feature_sha": feature_sha,
                    "path": str(summary_path.relative_to(REPO)),
                }
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "pair": [low, high],
            "label": f"{low}/{high}",
            "is_reference": [low, high] == [20, 80],
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "boundaries",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_boundary_family():
    """Run frozen M1 boundary screening; reuse accepted 20/80 reference."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_files = {
        "a_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-b-summary.json"
        ),
    }
    missing_reference = [
        name for name, path in reference_files.items()
        if not path.is_file()
    ]
    if missing_reference:
        return {
            "ok": False,
            "reason": "accepted reference-v3 evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_reference_files": missing_reference,
        }

    reference_deterministic = bool(
        _sha256(reference_files["a_baseline"])
        == _sha256(reference_files["b_baseline"])
        and _sha256(reference_files["a_diagnostic"])
        == _sha256(reference_files["b_diagnostic"])
        and _sha256(reference_files["a_summary"])
        == _sha256(reference_files["b_summary"])
    )
    if not reference_deterministic:
        return {
            "ok": False,
            "reason": "accepted reference-v3 A/B artifacts are not deterministic",
            "feature_sha": feature_sha,
        }

    reference_summary = json.loads(
        reference_files["a_summary"].read_text(encoding="utf-8")
    )
    reference_params = reference_summary.get("parameters") or {}
    if (
        float(reference_params.get("oversold_level", -1.0)) != 20.0
        or float(reference_params.get("overbought_level", -1.0)) != 80.0
        or int(reference_params.get("stochastic_k_period", -1)) != 21
        or int(reference_params.get("stochastic_d_period", -1)) != 7
        or int(reference_params.get("stochastic_slowing", -1)) != 7
        or int(reference_params.get("ema_period", -1)) != 7
        or reference_params.get("decision_spread_max_points") is not None
        or float(reference_params.get("atr_sl_multiplier", -1.0)) != 1.0
        or float(reference_params.get("atr_tp_multiplier", -1.0)) != 2.0
        or bool(reference_params.get("block_00_04_utc"))
    ):
        return {
            "ok": False,
            "reason": "reference-v3 is not the frozen 20/80 Phase-1 reference",
            "feature_sha": feature_sha,
        }

    output_root = _ensure_baseline_path(M022_PHASE1_BOUNDARY_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    pairs = ((15, 85), (25, 75))

    def artifact_paths(low, high):
        prefix = f"M022-P1-BOUND-{low}-{high}"
        arm_dir = output_root / f"{low}-{high}"
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(low, high):
        arm_dir, paths = artifact_paths(low, high)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial boundary arm directory {low}/{high}: "
                + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing boundary arm {low}/{high}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-BOUND-{low}-{high}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(item):
        low, high = item
        existing = payload_from_complete_artifacts(low, high)
        if existing is not None:
            return item, existing, None

        arm_dir, _paths = artifact_paths(low, high)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.parameter_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(arm_dir.relative_to(REPO)),
                "--family",
                "boundaries",
                "--value",
                f"{low}/{high}",
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return item, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return item, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final boundary JSON payload"
                ),
            }
        return item, payload, run

    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, item): item
                for item in pairs
            }
            for future in concurrent.futures.as_completed(futures):
                item, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": (
                            f"M022 boundary arm {item[0]}/{item[1]} failed"
                        ),
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "pair": list(item),
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[item] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    def arm_result(low, high, payload, *, reused_reference=False):
        summary = payload.get("summary") or {}
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}
        params = summary.get("parameters") or {}
        arm_ok = bool(
            payload.get("ok")
            and payload.get("deterministic")
            and payload.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("start_utc") == "2025-08-25T00:00:00Z"
            and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and float(params.get("oversold_level", -1.0)) == float(low)
            and float(params.get("overbought_level", -1.0)) == float(high)
            and int(params.get("stochastic_k_period", -1)) == 21
            and int(params.get("stochastic_d_period", -1)) == 7
            and int(params.get("stochastic_slowing", -1)) == 7
            and int(params.get("ema_period", -1)) == 7
            and params.get("decision_spread_max_points") is None
            and float(params.get("atr_sl_multiplier", -1.0)) == 1.0
            and float(params.get("atr_tp_multiplier", -1.0)) == 2.0
            and not bool(params.get("block_00_04_utc"))
        )
        if not arm_ok:
            raise RuntimeError(
                f"M022 boundary arm {low}/{high} failed invariants"
            )
        return {
            "pair": [low, high],
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
            "remaining_positions": summary.get("remaining_positions"),
            "reused_reference_evidence": reused_reference,
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        }

    reference_payload = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-REFERENCE",
        "baseline_sha256": _sha256(reference_files["a_baseline"]),
        "diagnostic_sha256": _sha256(reference_files["a_diagnostic"]),
        "summary_sha256": _sha256(reference_files["a_summary"]),
        "summary": reference_summary,
    }

    try:
        results = [
            arm_result(15, 85, executed[(15, 85)]),
            arm_result(20, 80, reference_payload, reused_reference=True),
            arm_result(25, 75, executed[(25, 75)]),
        ]
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "boundaries",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_20_80_reused": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
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



def m022_phase1_stochastic_assessment():
    """Apply the predeclared stochastic shortlist rubric mechanically."""

    feature_sha = _require_m022_branch()
    reference_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference summary is unavailable",
            "feature_sha": feature_sha,
        }
    if not M022_PHASE1_STOCHASTIC_DIR.is_dir():
        return {
            "ok": False,
            "reason": "M022 stochastic family outputs are unavailable",
            "feature_sha": feature_sha,
        }

    reference = json.loads(reference_path.read_text(encoding="utf-8"))
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

    def numeric(mapping, key):
        value = (mapping or {}).get(key)
        return None if value is None else float(value)

    def delta_breakdown(candidate, baseline, key):
        names = sorted(set(candidate or {}) | set(baseline or {}))
        rows = {}
        positive = []
        for name in names:
            cand = numeric((candidate or {}).get(name), key)
            ref = numeric((baseline or {}).get(name), key)
            if cand is None or ref is None:
                continue
            delta = cand - ref
            rows[name] = delta
            if delta > 0:
                positive.append((name, delta))
        positive_sum = sum(value for _name, value in positive)
        max_share = (
            max(value for _name, value in positive) / positive_sum
            if positive_sum > 0
            else None
        )
        return {
            "deltas": rows,
            "positive_count": len(positive),
            "positive_sum": positive_sum,
            "max_positive_share": max_share,
        }

    ref_agg = reference.get("aggregate") or {}
    ref_closed = int(ref_agg.get("closed_trades", 0))
    activity_floor = ref_closed * 0.70
    ref_symbols = reference.get("per_symbol") or {}
    ref_sides = reference.get("by_side") or {}
    ref_buckets = reference.get("by_entry_utc_bucket") or {}

    arms = []
    for k, d, slowing in tuples:
        label = f"{k}-{d}-{slowing}"
        if (k, d, slowing) == (21, 7, 7):
            summary_path = (
                M022_PHASE1_STOCH_EQUIV_DIR
                / "M022-P1-STOCH-21-7-7-a-summary.json"
            )
        else:
            summary_path = (
                M022_PHASE1_STOCHASTIC_DIR
                / label
                / f"M022-P1-STOCH-{k}-{d}-{slowing}-a-summary.json"
            )
        if not summary_path.is_file():
            return {
                "ok": False,
                "reason": f"stochastic summary missing for {k}/{d}/{slowing}",
                "feature_sha": feature_sha,
                "path": str(summary_path.relative_to(REPO)),
            }
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        aggregate = summary.get("aggregate") or {}
        closed = int(aggregate.get("closed_trades", 0))
        tp = summary.get("tp_safety") or {}
        partition = summary.get("partition") or {}

        mandatory_ok = bool(
            closed >= activity_floor
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
            and partition.get("partition") == "development"
            and partition.get("source_manifest_sha256")
            == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
        and int(partition.get("replay_boundary_count", 0)) > 0
        and bool(partition.get("replay_boundary_sha256"))
        )

        net_pl = float(aggregate.get("net_realized_pl", 0.0))
        ref_net = float(ref_agg.get("net_realized_pl", 0.0))
        improves_net = net_pl > ref_net

        symbol_delta = delta_breakdown(
            summary.get("per_symbol") or {},
            ref_symbols,
            "net_realized_pl",
        )
        side_delta = delta_breakdown(
            summary.get("by_side") or {},
            ref_sides,
            "net_realized_pl",
        )
        bucket_delta = delta_breakdown(
            summary.get("by_entry_utc_bucket") or {},
            ref_buckets,
            "net_realized_pl",
        )

        breadth_ok = True
        if improves_net:
            breadth_ok = bool(
                symbol_delta["positive_count"] >= 2
                and bucket_delta["positive_count"] >= 2
                and (
                    symbol_delta["max_positive_share"] is not None
                    and symbol_delta["max_positive_share"] <= 0.70
                )
                and (
                    side_delta["max_positive_share"] is not None
                    and side_delta["max_positive_share"] <= 0.80
                )
            )

        arms.append({
            "tuple": [k, d, slowing],
            "label": f"{k}/{d}/{slowing}",
            "is_reference": [k, d, slowing] == [21, 7, 7],
            "mandatory_ok": mandatory_ok,
            "activity": {
                "closed_trades": closed,
                "reference_closed_trades": ref_closed,
                "minimum_closed_trades": activity_floor,
                "ratio_to_reference": (
                    closed / ref_closed if ref_closed else None
                ),
            },
            "objectives": {
                "net_realized_pl": net_pl,
                "maximum_equity_drawdown": float(
                    aggregate.get("maximum_equity_drawdown", 0.0)
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "net_pl_improves_reference": improves_net,
            "breadth": {
                "passes": breadth_ok,
                "symbol": symbol_delta,
                "side": side_delta,
                "entry_utc_bucket": bucket_delta,
            },
        })

    eligible = [row for row in arms if row["mandatory_ok"]]

    def dominates(left, right):
        l = left["objectives"]
        r = right["objectives"]
        l_win = l["win_rate_nonflat_pct"]
        r_win = r["win_rate_nonflat_pct"]
        if l_win is None or r_win is None:
            return False
        weak = (
            l["net_realized_pl"] >= r["net_realized_pl"]
            and l["maximum_equity_drawdown"]
            <= r["maximum_equity_drawdown"]
            and float(l_win) >= float(r_win)
        )
        strict = (
            l["net_realized_pl"] > r["net_realized_pl"]
            or l["maximum_equity_drawdown"]
            < r["maximum_equity_drawdown"]
            or float(l_win) > float(r_win)
        )
        return bool(weak and strict)

    nondominated = []
    for row in eligible:
        if not any(
            other is not row and dominates(other, row)
            for other in eligible
        ):
            nondominated.append(row)

    nondominated_labels = {row["label"] for row in nondominated}
    shortlist = []
    for row in arms:
        pareto = row["label"] in nondominated_labels
        row["pareto_nondominated"] = pareto
        if row["is_reference"]:
            row["screening_status"] = "REFERENCE"
            shortlist.append(row["label"])
        elif not row["mandatory_ok"]:
            row["screening_status"] = "INELIGIBLE"
        elif not pareto:
            row["screening_status"] = "DOMINATED"
        elif row["breadth"]["passes"]:
            row["screening_status"] = "SHORTLIST"
            shortlist.append(row["label"])
        else:
            row["screening_status"] = "FRAGILE / CONCENTRATED"

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "stochastic",
        "rubric": {
            "activity_floor_fraction": 0.70,
            "objectives": {
                "net_realized_pl": "maximize",
                "maximum_equity_drawdown": "minimize",
                "win_rate_nonflat_pct": "maximize",
            },
            "symbol_positive_delta_min_count": 2,
            "calendar_bucket_positive_delta_min_count": 2,
            "max_symbol_positive_delta_share": 0.70,
            "max_side_positive_delta_share": 0.80,
            "reference_always_retained": True,
        },
        "shortlist": shortlist,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_development_results_only": True,
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_stochastic_reference_equivalence():
    """Prove optimized stochastic 21/7/7 matches accepted reference-v3."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    reference_summary_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }
    if not reference_summary_path.is_file():
        return {
            "ok": False,
            "reason": "accepted reference-v3 summary is unavailable",
            "feature_sha": feature_sha,
        }

    output_dir = _ensure_baseline_path(M022_PHASE1_STOCH_EQUIV_DIR)
    if output_dir.exists():
        return {
            "ok": False,
            "reason": "M022 stochastic 21/7/7 equivalence directory already exists",
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
            "stochastic",
            "--value",
            "21/7/7",
            "--starting-balance",
            "10000",
        ),
        env=_safe_env(),
    )
    if run["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "optimized stochastic 21/7/7 equivalence run failed",
            "feature_sha": feature_sha,
            "run": run,
        }

    try:
        payload = json.loads(run["stdout"].strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {
            "ok": False,
            "reason": "unable to parse optimized stochastic 21/7/7 result",
            "feature_sha": feature_sha,
            "run": run,
        }

    reference = json.loads(
        reference_summary_path.read_text(encoding="utf-8")
    )
    candidate = payload.get("summary") or {}

    comparison_keys = (
        "partition",
        "cost_contract",
        "aggregate",
        "per_symbol",
        "by_side",
        "by_entry_utc_bucket",
        "protection",
        "rejections",
        "tp_safety",
        "remaining_positions",
    )
    comparisons = {
        key: candidate.get(key) == reference.get(key)
        for key in comparison_keys
    }
    economics_equal = all(comparisons.values())

    partition = candidate.get("partition") or {}
    tp = candidate.get("tp_safety") or {}
    invariants_ok = bool(
        payload.get("ok")
        and payload.get("deterministic")
        and payload.get("partition") == "development"
        and partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
        and partition.get("start_utc") == "2025-08-25T00:00:00Z"
        and partition.get("end_exclusive_utc") == "2026-04-21T00:00:00Z"
        and partition.get("strict_common_boundary_clock") is True
        and partition.get("full_symbol_m1_preserved") is True
        and int(partition.get("replay_boundary_count", 0)) > 0
        and bool(partition.get("replay_boundary_sha256"))
        and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
        and int(tp.get("wrong_side_initial_tp", -1)) == 0
    )

    return {
        "ok": bool(invariants_ok and economics_equal),
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "experiment_id": payload.get("experiment_id"),
        "deterministic": payload.get("deterministic"),
        "invariants_ok": invariants_ok,
        "reference_v3_economic_equivalence": economics_equal,
        "comparisons": comparisons,
        "candidate": {
            "baseline_sha256": payload.get("baseline_sha256"),
            "diagnostic_sha256": payload.get("diagnostic_sha256"),
            "summary_sha256": payload.get("summary_sha256"),
            "aggregate": candidate.get("aggregate"),
            "partition": partition,
            "tp_safety": tp,
        },
        "reference": {
            "aggregate": reference.get("aggregate"),
            "partition": reference.get("partition"),
            "tp_safety": reference.get("tp_safety"),
        },
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "development",
            "validation_economic_data_used": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m022_phase1_stochastic_family():
    """Run frozen stochastic screening with at most two arms concurrently."""

    feature_sha = _require_m022_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 native-M1 manifest is unavailable",
            "feature_sha": feature_sha,
        }

    reference_summary_path = (
        M022_PHASE1_REFERENCE_DIR / "M022-P1-REFERENCE-a-summary.json"
    )
    if not reference_summary_path.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 reference-v3 summary is missing",
            "feature_sha": feature_sha,
        }
    reference = json.loads(reference_summary_path.read_text(encoding="utf-8"))

    equivalence_files = {
        "a_baseline": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-a-baseline.json"
        ),
        "b_baseline": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-b-baseline.json"
        ),
        "a_diagnostic": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-a-diagnostic.json"
        ),
        "b_diagnostic": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-b-diagnostic.json"
        ),
        "a_summary": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-a-summary.json"
        ),
        "b_summary": (
            M022_PHASE1_STOCH_EQUIV_DIR
            / "M022-P1-STOCH-21-7-7-b-summary.json"
        ),
    }
    missing_equivalence = [
        name for name, path in equivalence_files.items()
        if not path.is_file()
    ]
    if missing_equivalence:
        return {
            "ok": False,
            "reason": "optimized 21/7/7 equivalence evidence is incomplete",
            "feature_sha": feature_sha,
            "missing_equivalence_files": missing_equivalence,
        }

    equivalence_deterministic = bool(
        _sha256(equivalence_files["a_baseline"])
        == _sha256(equivalence_files["b_baseline"])
        and _sha256(equivalence_files["a_diagnostic"])
        == _sha256(equivalence_files["b_diagnostic"])
        and _sha256(equivalence_files["a_summary"])
        == _sha256(equivalence_files["b_summary"])
    )
    equivalence_summary = json.loads(
        equivalence_files["a_summary"].read_text(encoding="utf-8")
    )
    equivalence_keys = (
        "partition",
        "cost_contract",
        "aggregate",
        "per_symbol",
        "by_side",
        "by_entry_utc_bucket",
        "protection",
        "rejections",
        "tp_safety",
        "remaining_positions",
    )
    equivalence_matches_reference = all(
        equivalence_summary.get(key) == reference.get(key)
        for key in equivalence_keys
    )
    if not equivalence_deterministic or not equivalence_matches_reference:
        return {
            "ok": False,
            "reason": (
                "optimized 21/7/7 equivalence is not accepted; refusing "
                "all other stochastic tuples"
            ),
            "feature_sha": feature_sha,
            "equivalence_deterministic": equivalence_deterministic,
            "reference_v3_economic_equivalence": (
                equivalence_matches_reference
            ),
        }

    output_root = _ensure_baseline_path(M022_PHASE1_STOCHASTIC_DIR)
    output_root.mkdir(parents=True, exist_ok=True)

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

    def artifact_paths(k, d, slowing):
        prefix = f"M022-P1-STOCH-{k}-{d}-{slowing}"
        arm_dir = output_root / f"{k}-{d}-{slowing}"
        return arm_dir, {
            "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
            "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
            "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
            "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
            "a_summary": arm_dir / f"{prefix}-a-summary.json",
            "b_summary": arm_dir / f"{prefix}-b-summary.json",
        }

    def payload_from_complete_artifacts(k, d, slowing):
        arm_dir, paths = artifact_paths(k, d, slowing)
        if not arm_dir.exists():
            return None
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            raise RuntimeError(
                f"partial stochastic arm directory {k}/{d}/{slowing}: "
                + ",".join(missing)
            )
        deterministic = bool(
            _sha256(paths["a_baseline"]) == _sha256(paths["b_baseline"])
            and _sha256(paths["a_diagnostic"]) == _sha256(paths["b_diagnostic"])
            and _sha256(paths["a_summary"]) == _sha256(paths["b_summary"])
        )
        if not deterministic:
            raise RuntimeError(
                f"non-deterministic existing stochastic arm {k}/{d}/{slowing}"
            )
        summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
        return {
            "ok": True,
            "deterministic": True,
            "partition": "development",
            "experiment_id": f"M022-P1-STOCH-{k}-{d}-{slowing}",
            "baseline_sha256": _sha256(paths["a_baseline"]),
            "diagnostic_sha256": _sha256(paths["a_diagnostic"]),
            "summary_sha256": _sha256(paths["a_summary"]),
            "summary": summary,
            "reused_complete_artifacts": True,
        }

    def execute_arm(item):
        k, d, slowing = item
        existing = payload_from_complete_artifacts(k, d, slowing)
        if existing is not None:
            return item, existing, None

        arm_dir, _paths = artifact_paths(k, d, slowing)
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
            return item, None, run
        try:
            payload = json.loads(run["stdout"].strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return item, None, {
                "exit_code": run["exit_code"],
                "stdout": run["stdout"],
                "stderr": (
                    run["stderr"]
                    + "\nunable to parse final stochastic JSON payload"
                ),
            }
        return item, payload, run

    run_items = [
        item for item in tuples
        if item != (21, 7, 7)
    ]
    executed = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(execute_arm, item): item
                for item in run_items
            }
            for future in concurrent.futures.as_completed(futures):
                item, payload, run = future.result()
                if payload is None:
                    return {
                        "ok": False,
                        "reason": (
                            f"M022 stochastic arm "
                            f"{item[0]}/{item[1]}/{item[2]} failed"
                        ),
                        "feature_branch": "strategy-parameter-research",
                        "feature_sha": feature_sha,
                        "failed_run": {
                            "tuple": list(item),
                            "exit_code": (run or {}).get("exit_code"),
                            "stdout": _bounded((run or {}).get("stdout")),
                            "stderr": _bounded((run or {}).get("stderr")),
                        },
                    }
                executed[item] = payload
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "completed_arm_artifacts_preserved": True,
                "partial_artifacts_not_overwritten": True,
            },
        }

    executed[(21, 7, 7)] = {
        "ok": True,
        "deterministic": True,
        "partition": "development",
        "experiment_id": "M022-P1-STOCH-21-7-7",
        "baseline_sha256": _sha256(equivalence_files["a_baseline"]),
        "diagnostic_sha256": _sha256(equivalence_files["a_diagnostic"]),
        "summary_sha256": _sha256(equivalence_files["a_summary"]),
        "summary": equivalence_summary,
        "reused_equivalence_evidence": True,
    }

    results = []
    for k, d, slowing in tuples:
        payload = executed[(k, d, slowing)]
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
            and partition.get("strict_common_boundary_clock") is True
            and partition.get("full_symbol_m1_preserved") is True
            and int(partition.get("replay_boundary_count", 0)) > 0
            and bool(partition.get("replay_boundary_sha256"))
            and int(tp.get("negative_pl_take_profit_exits", -1)) == 0
            and int(tp.get("wrong_side_initial_tp", -1)) == 0
        )
        if not arm_ok:
            return {
                "ok": False,
                "reason": (
                    f"M022 stochastic arm {k}/{d}/{slowing} "
                    "failed invariants"
                ),
                "feature_sha": feature_sha,
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
            "remaining_positions": summary.get("remaining_positions"),
            "reused_equivalence_evidence": bool(
                payload.get("reused_equivalence_evidence")
            ),
            "reused_complete_artifacts": bool(
                payload.get("reused_complete_artifacts")
            ),
        })

    return {
        "ok": True,
        "feature_branch": "strategy-parameter-research",
        "feature_sha": feature_sha,
        "family": "stochastic",
        "execution": {
            "maximum_concurrent_arms": 2,
            "independent_arm_processes": True,
            "reference_21_7_7_reused": True,
        },
        "partition": {
            "name": "development",
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-04-21T00:00:00Z",
            "trading_dates": 169,
        },
        "reference_21_7_7_economic_equivalence": True,
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
        and partition.get("strict_common_boundary_clock") is True
        and partition.get("full_symbol_m1_preserved") is True
        and int(partition.get("replay_boundary_count", 0)) > 0
        and bool(partition.get("replay_boundary_sha256"))
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






def _m023_stage_b_expected():
    return {
        "S-R": {
            "label": "ALL-HOURS",
            "start_hour": None,
            "end_hour": None,
            "duration_hours": 24,
        },
        "S-ACTIVE": {
            "label": "EAT-ACTIVE",
            "start_hour": 8,
            "end_hour": 20,
            "duration_hours": 13,
        },
        "S-MORNING": {
            "label": "EAT-MORNING",
            "start_hour": 8,
            "end_hour": 11,
            "duration_hours": 4,
        },
        "S-MIDDAY": {
            "label": "EAT-MIDDAY",
            "start_hour": 12,
            "end_hour": 14,
            "duration_hours": 3,
        },
        "S-AFTERNOON": {
            "label": "EAT-AFTERNOON",
            "start_hour": 15,
            "end_hour": 17,
            "duration_hours": 3,
        },
    }


def _m023_stage_b_paths(label):
    arm_dir = M023_STAGE_B_SESSION_DIR / label
    prefix = f"M023-B-{label}"
    return {
        "dir": arm_dir,
        "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
        "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
        "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
        "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
        "a_summary": arm_dir / f"{prefix}-a-summary.json",
        "b_summary": arm_dir / f"{prefix}-b-summary.json",
    }


def _m023_stage_b_validate_artifacts(label):
    expected = _m023_stage_b_expected()[label]
    paths = _m023_stage_b_paths(label)
    required = [
        paths["a_baseline"],
        paths["b_baseline"],
        paths["a_diagnostic"],
        paths["b_diagnostic"],
        paths["a_summary"],
        paths["b_summary"],
    ]
    exists = [path.is_file() for path in required]
    if any(exists) and not all(exists):
        raise RuntimeError(
            f"M023 Stage-B {label} has partial immutable artifacts"
        )
    if not all(exists):
        return None

    hashes = {
        "baseline_a": _sha256(paths["a_baseline"]),
        "baseline_b": _sha256(paths["b_baseline"]),
        "diagnostic_a": _sha256(paths["a_diagnostic"]),
        "diagnostic_b": _sha256(paths["b_diagnostic"]),
        "summary_a": _sha256(paths["a_summary"]),
        "summary_b": _sha256(paths["b_summary"]),
    }
    deterministic = (
        hashes["baseline_a"] == hashes["baseline_b"]
        and hashes["diagnostic_a"] == hashes["diagnostic_b"]
        and hashes["summary_a"] == hashes["summary_b"]
    )
    summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
    params = summary.get("parameters") or {}
    partition = summary.get("partition") or {}
    session = summary.get("session") or {}
    direction = summary.get("direction_invariants") or {}
    tp = summary.get("tp_safety") or {}
    safety = summary.get("safety") or {}
    expected_params = {
        "stochastic_k_period": 21,
        "stochastic_d_period": 7,
        "stochastic_slowing": 7,
        "oversold_level": 20.0,
        "overbought_level": 80.0,
        "ema_period": 7,
        "decision_spread_max_points": None,
        "atr_sl_multiplier": 1.5,
        "atr_tp_multiplier": 3.0,
        "block_00_04_utc": False,
    }
    checks = {
        "deterministic": deterministic,
        "milestone": summary.get("milestone") == "M023",
        "stage": summary.get("stage") == "B",
        "experiment_id": summary.get("experiment_id") == f"M023-B-{label}",
        "arm_id": summary.get("arm_id") == label,
        "direction_buy_only": summary.get("direction") == "BUY",
        "sell_accepted_zero": int(
            direction.get("sell_accepted_entries", -1)
        ) == 0,
        "parameters": params == expected_params,
        "session_label": session.get("label") == expected["label"],
        "session_timezone": session.get("timezone") == "Africa/Nairobi",
        "session_start": session.get("start_hour") == expected["start_hour"],
        "session_end": session.get("end_hour") == expected["end_hour"],
        "session_duration": int(
            session.get("duration_hours", -1)
        ) == expected["duration_hours"],
        "entry_only": session.get("new_entry_eligibility_only") is True,
        "cost_contract": summary.get("cost_contract")
        == (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "source_manifest": partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558",
        "start_utc": partition.get("start_utc")
        == "2025-08-25T00:00:00Z",
        "end_exclusive_utc": partition.get("end_exclusive_utc")
        == "2026-07-08T00:00:00Z",
        "trading_dates": int(partition.get("trading_dates", 0)) == 225,
        "date_list_sha256": partition.get("date_list_sha256")
        == "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0",
        "strict_common_boundary_clock": (
            partition.get("strict_common_boundary_clock") is True
        ),
        "full_symbol_m1_preserved": (
            partition.get("full_symbol_m1_preserved") is True
        ),
        "replay_boundary_count": int(
            partition.get("replay_boundary_count", 0)
        ) > 0,
        "replay_boundary_sha256": bool(
            partition.get("replay_boundary_sha256")
        ),
        "fold_count": len(partition.get("folds") or []) == 5,
        "tp_negative_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "tp_wrong_side_zero": int(
            tp.get("wrong_side_initial_tp", -1)
        ) == 0,
        "holdout_unused": (
            safety.get("historical_holdout_economic_data_used") is False
        ),
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
        "m15_disabled": safety.get("m15_signal_enabled") is False,
        "no_forced_session_close": (
            safety.get("forced_session_end_close") is False
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(
            f"M023 Stage-B {label} failed frozen invariants: {failed}"
        )
    return {
        "label": label,
        "hashes": hashes,
        "checks": checks,
        "summary": summary,
    }


def _m023_stage_b_mean_from_folds(summary):
    folds = summary["folds"]
    total_n = sum(int(row["closed_trades"]) for row in folds.values())
    total_pl = sum(float(row["net_realized_pl"]) for row in folds.values())
    return total_pl / total_n if total_n else None


def _m023_stage_b_reference_equivalence(stage_b_summary, stage_a_summary):
    fields = {}
    a_agg = stage_a_summary["aggregate"]
    b_agg = stage_b_summary["aggregate"]
    fields["closed_trades"] = (
        int(b_agg["closed_trades"]) == int(a_agg["closed_trades"])
    )
    fields["net_realized_pl"] = (
        float(b_agg["net_realized_pl"]) == float(a_agg["net_realized_pl"])
    )
    fields["mean_trade_pl"] = (
        float(_m023_stage_b_mean_from_folds(stage_b_summary))
        == float(_m023_stage_b_mean_from_folds(stage_a_summary))
    )
    fields["win_rate"] = (
        float(b_agg["win_rate_nonflat_pct"])
        == float(a_agg["win_rate_nonflat_pct"])
    )
    fields["max_dd"] = (
        float(b_agg["maximum_equity_drawdown"])
        == float(a_agg["maximum_equity_drawdown"])
    )

    def compact_symbols(summary):
        return {
            symbol: {
                "closed_trades": int(row["closed_trades"]),
                "net_realized_pl": float(row["net_realized_pl"]),
                "mean_trade_pl": (
                    None
                    if row.get("mean_trade_pl") is None
                    else float(row["mean_trade_pl"])
                ),
            }
            for symbol, row in summary["per_symbol"].items()
        }

    def compact_folds(summary):
        return {
            fold: {
                "closed_trades": int(row["closed_trades"]),
                "net_realized_pl": float(row["net_realized_pl"]),
                "mean_trade_pl": (
                    None
                    if row.get("mean_trade_pl") is None
                    else float(row["mean_trade_pl"])
                ),
            }
            for fold, row in summary["folds"].items()
        }

    def compact_eat(row):
        return {
            "closed_trades": int(row["closed_trades"]),
            "net_realized_pl": float(row["net_realized_pl"]),
            "mean_trade_pl": (
                None
                if row.get("mean_trade_pl") is None
                else float(row["mean_trade_pl"])
            ),
            "win_rate_nonflat_pct": float(row["win_rate_nonflat_pct"]),
            "fold_mean_trade_pl": row.get("fold_mean_trade_pl"),
        }

    fields["per_symbol"] = (
        compact_symbols(stage_b_summary)
        == compact_symbols(stage_a_summary)
    )
    fields["folds"] = (
        compact_folds(stage_b_summary)
        == compact_folds(stage_a_summary)
    )
    fields["eat_active"] = (
        compact_eat(stage_b_summary["eat_active"])
        == compact_eat(stage_a_summary["eat_active"])
    )
    fields["eat_off_hours"] = (
        compact_eat(stage_b_summary["eat_off_hours"])
        == compact_eat(stage_a_summary["eat_off_hours"])
    )
    fields["tp_safety"] = (
        stage_b_summary["tp_safety"] == stage_a_summary["tp_safety"]
    )
    return {
        "passes": all(fields.values()),
        "checks": fields,
    }


def m023_stage_b_session_family():
    """Run S-R, prove D-B parity, then the four frozen session arms."""

    feature_sha = _require_m023_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 source manifest is missing",
            "feature_sha": feature_sha,
        }
    if (
        _sha256(manifest)
        != "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
    ):
        return {
            "ok": False,
            "reason": "accepted M022 source manifest SHA changed",
            "feature_sha": feature_sha,
        }

    root = _ensure_baseline_path(M023_STAGE_B_SESSION_DIR)
    root.mkdir(parents=True, exist_ok=True)

    def run_arm(label):
        existing = _m023_stage_b_validate_artifacts(label)
        if existing is not None:
            return {
                "ok": True,
                "label": label,
                "reused_complete_artifacts": True,
                "run": None,
            }
        paths = _m023_stage_b_paths(label)
        paths["dir"].mkdir(parents=True, exist_ok=True)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m023_session_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(paths["dir"].relative_to(REPO)),
                "--arm",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        return {
            "ok": run["exit_code"] == 0,
            "label": label,
            "reused_complete_artifacts": False,
            "run": run,
        }

    reference_run = run_arm("S-R")
    if not reference_run["ok"]:
        return {
            "ok": False,
            "reason": "M023 Stage-B S-R execution failed",
            "feature_sha": feature_sha,
            "execution": {"S-R": reference_run},
        }
    try:
        stage_b_ref = _m023_stage_b_validate_artifacts("S-R")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    d_b_path = (
        M023_STAGE_A_DIRECTION_DIR
        / "D-B"
        / "M023-A-D-B-a-summary.json"
    )
    if not d_b_path.is_file():
        return {
            "ok": False,
            "reason": "accepted Stage-A D-B summary is missing",
            "feature_sha": feature_sha,
        }
    stage_a_d_b = json.loads(d_b_path.read_text(encoding="utf-8"))
    equivalence = _m023_stage_b_reference_equivalence(
        stage_b_ref["summary"],
        stage_a_d_b,
    )
    if not equivalence["passes"]:
        return {
            "ok": False,
            "reason": "S-R does not reproduce accepted D-B economics",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
            "nonreference_executed": False,
            "safety": {
                "historical_holdout_economic_data_used": False,
                "m021_post_cutoff_data_used": False,
                "real_order_api_called": False,
            },
        }

    executed = {"S-R": reference_run}
    labels = ("S-ACTIVE", "S-MORNING", "S-MIDDAY", "S-AFTERNOON")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            label: pool.submit(run_arm, label)
            for label in labels
        }
        for label in labels:
            executed[label] = futures[label].result()

    failed = [label for label in labels if not executed[label]["ok"]]
    if failed:
        return {
            "ok": False,
            "reason": f"M023 Stage-B session execution failed: {failed}",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
            "execution": executed,
        }

    validated = {}
    try:
        for label in ("S-R", *labels):
            validated[label] = _m023_stage_b_validate_artifacts(label)
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
        }

    def compact(item):
        summary = item["summary"]
        aggregate = summary["aggregate"]
        return {
            "label": item["label"],
            "hashes": item["hashes"],
            "checks": item["checks"],
            "session": summary["session"],
            "aggregate": aggregate,
            "overall": summary["overall"],
            "per_symbol": summary["per_symbol"],
            "folds": summary["folds"],
            "iso_weeks": summary["iso_weeks"],
            "direction_filter": summary["direction_filter"],
            "session_filter": summary["session_filter"],
            "tp_safety": summary["tp_safety"],
            "remaining_positions": summary["remaining_positions"],
            "source_date_replay_hashes": summary[
                "source_date_replay_hashes"
            ],
            "reference_windows": summary.get("reference_windows"),
        }

    return {
        "ok": True,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "family": "m023-stage-b-session",
        "reference_equivalence": equivalence,
        "execution": {
            "order": ["S-R", list(labels)],
            "maximum_concurrent_nonreference_arms": 2,
            "runs": {
                label: {
                    "reused_complete_artifacts": executed[label][
                        "reused_complete_artifacts"
                    ],
                    "exit_code": (
                        None
                        if executed[label]["run"] is None
                        else executed[label]["run"]["exit_code"]
                    ),
                }
                for label in ("S-R", *labels)
            },
        },
        "arms": {
            label: compact(validated[label])
            for label in ("S-R", *labels)
        },
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "seen-research-only",
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "weekday_filter_applied": False,
        },
    }


def m023_stage_b_session_assessment():
    """Mechanically apply frozen Stage-B session support/reduction rules."""

    feature_sha = _require_m023_branch()
    try:
        rows = {
            label: _m023_stage_b_validate_artifacts(label)
            for label in _m023_stage_b_expected()
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }
    if any(value is None for value in rows.values()):
        return {
            "ok": False,
            "reason": "M023 Stage-B artifacts are incomplete",
            "feature_sha": feature_sha,
        }

    ref = rows["S-R"]["summary"]
    d_b_path = (
        M023_STAGE_A_DIRECTION_DIR
        / "D-B"
        / "M023-A-D-B-a-summary.json"
    )
    if not d_b_path.is_file():
        return {
            "ok": False,
            "reason": "accepted Stage-A D-B summary is missing",
            "feature_sha": feature_sha,
        }
    d_b = json.loads(d_b_path.read_text(encoding="utf-8"))
    equivalence = _m023_stage_b_reference_equivalence(ref, d_b)
    if not equivalence["passes"]:
        return {
            "ok": False,
            "reason": "S-R/D-B reference equivalence failed",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
        }

    ref_agg = ref["aggregate"]
    ref_symbols = ref["per_symbol"]
    ref_folds = ref["folds"]
    ref_windows = ref["reference_windows"]

    def assess(label):
        row = rows[label]
        summary = row["summary"]
        aggregate = summary["aggregate"]
        overall = summary["overall"]
        symbols = summary["per_symbol"]
        folds = summary["folds"]
        weeks = summary["iso_weeks"]
        denominator = ref_windows[label]

        mandatory_ok = all(row["checks"].values())

        denom_total = int(denominator["overall"]["closed_trades"])
        total_ratio = (
            int(overall["closed_trades"]) / denom_total
            if denom_total else 0.0
        )
        symbol_ratios = {}
        for symbol in ref_symbols:
            denom = int(
                (
                    denominator["overall"].get("per_symbol") or {}
                ).get(symbol, {}).get("closed_trades", 0)
            )
            actual = int(symbols[symbol]["closed_trades"])
            symbol_ratios[symbol] = (
                actual / denom if denom else (1.0 if actual == 0 else 0.0)
            )
        fold_ratios = {}
        for fold in ref_folds:
            denom = int(
                denominator["folds"][fold]["closed_trades"]
            )
            actual = int(folds[fold]["closed_trades"])
            fold_ratios[fold] = (
                actual / denom if denom else (1.0 if actual == 0 else 0.0)
            )

        denom_trade_weeks = [
            week
            for week, value in denominator["iso_weeks"].items()
            if int(value["closed_trades"]) > 0
        ]
        represented_weeks = sum(
            int((weeks.get(week) or {}).get("closed_trades", 0)) > 0
            for week in denom_trade_weeks
        )
        week_presence = (
            represented_weeks / len(denom_trade_weeks)
            if denom_trade_weeks else 0.0
        )

        representation_checks = {
            "total_ge_60pct_same_window": total_ratio >= 0.60,
            "every_symbol_ge_40pct_same_window": all(
                value >= 0.40 for value in symbol_ratios.values()
            ),
            "every_fold_ge_40pct_same_window": all(
                value >= 0.40 for value in fold_ratios.values()
            ),
            "total_closed_ge_500": int(overall["closed_trades"]) >= 500,
            "every_fold_closed_ge_50": all(
                int(folds[fold]["closed_trades"]) >= 50
                for fold in folds
            ),
            "week_presence_ge_75pct": week_presence >= 0.75,
        }
        representation_ok = all(representation_checks.values())

        candidate_mean = float(overall["mean_trade_pl"])
        ref_mean = float(ref["overall"]["mean_trade_pl"])
        fold_mean_better = sum(
            folds[fold]["mean_trade_pl"] is not None
            and ref_folds[fold]["mean_trade_pl"] is not None
            and float(folds[fold]["mean_trade_pl"])
                > float(ref_folds[fold]["mean_trade_pl"])
            for fold in ref_folds
        )
        positive_folds = [
            fold
            for fold, value in folds.items()
            if float(value["net_realized_pl"]) > 0
        ]
        symbol_mean_better = sum(
            symbols[symbol]["mean_trade_pl"] is not None
            and ref_symbols[symbol]["mean_trade_pl"] is not None
            and float(symbols[symbol]["mean_trade_pl"])
                > float(ref_symbols[symbol]["mean_trade_pl"])
            for symbol in ref_symbols
        )
        positive_symbols = [
            symbol
            for symbol, value in symbols.items()
            if float(value["net_realized_pl"]) > 0
        ]

        eligible_weeks = []
        better_weeks = []
        for week, ref_window_row in denominator["iso_weeks"].items():
            cand = weeks.get(week)
            if (
                cand
                and int(cand["closed_trades"]) >= 5
                and int(ref_window_row["closed_trades"]) >= 5
            ):
                eligible_weeks.append(week)
                if (
                    cand["mean_trade_pl"] is not None
                    and ref_window_row["mean_trade_pl"] is not None
                    and float(cand["mean_trade_pl"])
                        > float(ref_window_row["mean_trade_pl"])
                ):
                    better_weeks.append(week)
        better_week_ratio = (
            len(better_weeks) / len(eligible_weeks)
            if eligible_weeks else 0.0
        )

        positive_symbol_pl = {
            symbol: float(symbols[symbol]["net_realized_pl"])
            for symbol in positive_symbols
        }
        positive_symbol_sum = sum(positive_symbol_pl.values())
        max_symbol_share = (
            max(positive_symbol_pl.values()) / positive_symbol_sum
            if positive_symbol_sum > 0 else None
        )
        positive_fold_pl = {
            fold: float(folds[fold]["net_realized_pl"])
            for fold in positive_folds
        }
        positive_fold_sum = sum(positive_fold_pl.values())
        max_fold_share = (
            max(positive_fold_pl.values()) / positive_fold_sum
            if positive_fold_sum > 0 else None
        )

        support_checks = {
            "net_pl_positive": float(aggregate["net_realized_pl"]) > 0,
            "mean_trade_pl_positive": candidate_mean > 0,
            "max_dd_strictly_lower_than_reference": (
                float(aggregate["maximum_equity_drawdown"])
                < float(ref_agg["maximum_equity_drawdown"])
            ),
            "win_rate_within_1pp": (
                float(aggregate["win_rate_nonflat_pct"])
                >= float(ref_agg["win_rate_nonflat_pct"]) - 1.0
            ),
            "fold_mean_better_ge_4": fold_mean_better >= 4,
            "positive_fold_pl_ge_3": len(positive_folds) >= 3,
            "symbol_mean_better_ge_3": symbol_mean_better >= 3,
            "positive_symbol_pl_ge_3": len(positive_symbols) >= 3,
            "weekly_mean_better_ge_60pct": better_week_ratio >= 0.60,
            "eligible_iso_weeks_ge_30": len(eligible_weeks) >= 30,
            "positive_symbol_concentration_le_60pct": (
                len(positive_symbols) >= 3
                and max_symbol_share is not None
                and max_symbol_share <= 0.60
            ),
            "positive_fold_concentration_le_60pct": (
                len(positive_folds) >= 3
                and max_fold_share is not None
                and max_fold_share <= 0.60
            ),
        }
        support_ok = all(support_checks.values())

        if not mandatory_ok or not representation_ok:
            classification = "INELIGIBLE"
        elif support_ok:
            classification = "SUPPORTED"
        else:
            classification = "NOT SUPPORTED"

        return {
            "label": label,
            "session": summary["session"],
            "classification": classification,
            "mandatory_ok": mandatory_ok,
            "representation": {
                **representation_checks,
                "ok": representation_ok,
                "total_ratio": total_ratio,
                "per_symbol_ratio": symbol_ratios,
                "per_fold_ratio": fold_ratios,
                "reference_window_trade_weeks": len(denom_trade_weeks),
                "represented_trade_weeks": represented_weeks,
                "week_presence_ratio": week_presence,
            },
            "support_checks": support_checks,
            "support_ok": support_ok,
            "economics": {
                "closed_trades": int(overall["closed_trades"]),
                "net_realized_pl": float(aggregate["net_realized_pl"]),
                "mean_trade_pl": candidate_mean,
                "maximum_equity_drawdown": float(
                    aggregate["maximum_equity_drawdown"]
                ),
                "maximum_equity_drawdown_pct": float(
                    aggregate["maximum_equity_drawdown_pct"]
                ),
                "win_rate_nonflat_pct": float(
                    aggregate["win_rate_nonflat_pct"]
                ),
            },
            "robustness": {
                "fold_mean_better": fold_mean_better,
                "positive_folds": positive_folds,
                "symbol_mean_better": symbol_mean_better,
                "positive_symbols": positive_symbols,
                "eligible_iso_weeks": len(eligible_weeks),
                "better_iso_weeks": len(better_weeks),
                "better_iso_week_ratio": better_week_ratio,
                "positive_symbol_pl": positive_symbol_pl,
                "max_positive_symbol_pl_share": max_symbol_share,
                "positive_fold_pl": positive_fold_pl,
                "max_positive_fold_pl_share": max_fold_share,
            },
        }

    labels = ("S-ACTIVE", "S-MORNING", "S-MIDDAY", "S-AFTERNOON")
    assessments = {label: assess(label) for label in labels}
    supported = [
        label
        for label in labels
        if assessments[label]["classification"] == "SUPPORTED"
    ]

    fixed = None
    selection_detail = {}
    if not supported:
        selection_reason = "zero Stage-B sessions are SUPPORTED"
    elif len(supported) == 1:
        fixed = supported[0]
        selection_reason = "exactly one Stage-B session is SUPPORTED"
    else:
        ref_mean = float(ref["overall"]["mean_trade_pl"])
        scores = {}
        for label in supported:
            item = assessments[label]
            econ = item["economics"]
            robust = item["robustness"]
            scores[label] = {
                "pl_gain_fraction": (
                    (econ["net_realized_pl"] - float(ref_agg["net_realized_pl"]))
                    / abs(float(ref_agg["net_realized_pl"]))
                ),
                "dd_improvement_fraction": (
                    (
                        float(ref_agg["maximum_equity_drawdown"])
                        - econ["maximum_equity_drawdown"]
                    )
                    / float(ref_agg["maximum_equity_drawdown"])
                ),
                "mean_trade_gain_fraction": (
                    (econ["mean_trade_pl"] - ref_mean) / abs(ref_mean)
                ),
                "win_rate_gain_fraction": (
                    (
                        econ["win_rate_nonflat_pct"]
                        - float(ref_agg["win_rate_nonflat_pct"])
                    )
                    / float(ref_agg["win_rate_nonflat_pct"])
                ),
                "positive_fold_fraction": (
                    len(robust["positive_folds"]) / 5.0
                ),
                "positive_symbol_fraction": (
                    len(robust["positive_symbols"]) / 5.0
                ),
            }
            scores[label]["robustness_maximin"] = min(
                scores[label].values()
            )

        def rank_key(label):
            item = assessments[label]
            session = item["session"]
            return (
                scores[label]["robustness_maximin"],
                len(item["robustness"]["positive_folds"]),
                len(item["robustness"]["positive_symbols"]),
                item["robustness"]["better_iso_week_ratio"],
                item["representation"]["total_ratio"],
                int(session["duration_hours"]),
            )

        best_key = max(rank_key(label) for label in supported)
        tied = [
            label for label in supported if rank_key(label) == best_key
        ]
        fixed = sorted(tied)[0]
        selection_reason = (
            "multiple Stage-B sessions SUPPORTED; frozen maximin/tie-break "
            "rule applied"
        )
        selection_detail = {"scores": scores}

    return {
        "ok": True,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "reference": {
            "label": "S-R",
            "classification": "REFERENCE",
            "economics": {
                "closed_trades": int(ref["overall"]["closed_trades"]),
                "net_realized_pl": float(ref_agg["net_realized_pl"]),
                "mean_trade_pl": float(ref["overall"]["mean_trade_pl"]),
                "maximum_equity_drawdown": float(
                    ref_agg["maximum_equity_drawdown"]
                ),
                "maximum_equity_drawdown_pct": float(
                    ref_agg["maximum_equity_drawdown_pct"]
                ),
                "win_rate_nonflat_pct": float(
                    ref_agg["win_rate_nonflat_pct"]
                ),
            },
            "reference_equivalence": equivalence,
            "hashes": rows["S-R"]["hashes"],
        },
        "assessments": assessments,
        "supported_sessions": supported,
        "fixed_session": fixed,
        "selection_reason": selection_reason,
        "selection_detail": selection_detail,
        "historical_holdout_execution_authorized": False,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_stage_b_artifacts_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "weekday_filter_run": False,
        },
    }


def _m023_stage_a_paths(label):
    arm_dir = M023_STAGE_A_DIRECTION_DIR / label
    prefix = f"M023-A-{label}"
    return {
        "dir": arm_dir,
        "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
        "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
        "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
        "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
        "a_summary": arm_dir / f"{prefix}-a-summary.json",
        "b_summary": arm_dir / f"{prefix}-b-summary.json",
    }


def _m023_stage_a_expected():
    return {
        "D-R": "BOTH",
        "D-S": "SELL",
        "D-B": "BUY",
    }


def _m023_stage_a_validate_artifacts(label):
    expected_direction = _m023_stage_a_expected()[label]
    paths = _m023_stage_a_paths(label)
    required = [
        paths["a_baseline"],
        paths["b_baseline"],
        paths["a_diagnostic"],
        paths["b_diagnostic"],
        paths["a_summary"],
        paths["b_summary"],
    ]
    exists = [path.is_file() for path in required]
    if any(exists) and not all(exists):
        raise RuntimeError(
            f"M023 Stage-A {label} has partial immutable artifacts"
        )
    if not all(exists):
        return None

    hashes = {
        "baseline_a": _sha256(paths["a_baseline"]),
        "baseline_b": _sha256(paths["b_baseline"]),
        "diagnostic_a": _sha256(paths["a_diagnostic"]),
        "diagnostic_b": _sha256(paths["b_diagnostic"]),
        "summary_a": _sha256(paths["a_summary"]),
        "summary_b": _sha256(paths["b_summary"]),
    }
    deterministic = (
        hashes["baseline_a"] == hashes["baseline_b"]
        and hashes["diagnostic_a"] == hashes["diagnostic_b"]
        and hashes["summary_a"] == hashes["summary_b"]
    )
    summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
    params = summary.get("parameters") or {}
    partition = summary.get("partition") or {}
    tp = summary.get("tp_safety") or {}
    invariants = summary.get("direction_invariants") or {}
    safety = summary.get("safety") or {}
    expected_params = {
        "stochastic_k_period": 21,
        "stochastic_d_period": 7,
        "stochastic_slowing": 7,
        "oversold_level": 20.0,
        "overbought_level": 80.0,
        "ema_period": 7,
        "decision_spread_max_points": None,
        "atr_sl_multiplier": 1.5,
        "atr_tp_multiplier": 3.0,
        "block_00_04_utc": False,
    }
    wrong_side_ok = (
        expected_direction == "BOTH"
        or (
            expected_direction == "SELL"
            and int(invariants.get("buy_accepted_entries", -1)) == 0
        )
        or (
            expected_direction == "BUY"
            and int(invariants.get("sell_accepted_entries", -1)) == 0
        )
    )
    checks = {
        "deterministic": deterministic,
        "milestone": summary.get("milestone") == "M023",
        "stage": summary.get("stage") == "A",
        "experiment_id": summary.get("experiment_id") == f"M023-A-{label}",
        "arm_id": summary.get("arm_id") == label,
        "direction": summary.get("direction") == expected_direction,
        "parameters": params == expected_params,
        "cost_contract": summary.get("cost_contract")
        == (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "source_manifest": partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558",
        "start_utc": partition.get("start_utc")
        == "2025-08-25T00:00:00Z",
        "end_exclusive_utc": partition.get("end_exclusive_utc")
        == "2026-07-08T00:00:00Z",
        "trading_dates": int(partition.get("trading_dates", 0)) == 225,
        "date_list_sha256": partition.get("date_list_sha256")
        == "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0",
        "strict_common_boundary_clock": (
            partition.get("strict_common_boundary_clock") is True
        ),
        "full_symbol_m1_preserved": (
            partition.get("full_symbol_m1_preserved") is True
        ),
        "replay_boundary_count": int(
            partition.get("replay_boundary_count", 0)
        ) > 0,
        "replay_boundary_sha256": bool(
            partition.get("replay_boundary_sha256")
        ),
        "fold_count": len(partition.get("folds") or []) == 5,
        "tp_negative_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "tp_wrong_side_zero": int(tp.get("wrong_side_initial_tp", -1)) == 0,
        "opposite_side_zero": wrong_side_ok,
        "holdout_unused": (
            safety.get("historical_holdout_economic_data_used") is False
        ),
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "session_filter_absent": safety.get("session_filter_applied") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(
            f"M023 Stage-A {label} failed frozen invariants: {failed}"
        )

    return {
        "label": label,
        "direction": expected_direction,
        "hashes": hashes,
        "summary": summary,
        "checks": checks,
    }


def m023_stage_a_direction_family():
    """Run exactly D-R, then D-S/D-B with max two non-reference processes."""

    feature_sha = _require_m023_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 source manifest is missing",
            "feature_sha": feature_sha,
        }
    manifest_sha = _sha256(manifest)
    if (
        manifest_sha
        != "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
    ):
        return {
            "ok": False,
            "reason": "accepted M022 source manifest SHA changed",
            "feature_sha": feature_sha,
            "manifest_sha256": manifest_sha,
        }

    root = _ensure_baseline_path(M023_STAGE_A_DIRECTION_DIR)
    root.mkdir(parents=True, exist_ok=True)

    def run_arm(label):
        existing = _m023_stage_a_validate_artifacts(label)
        if existing is not None:
            return {
                "ok": True,
                "label": label,
                "reused_complete_artifacts": True,
                "run": None,
            }
        paths = _m023_stage_a_paths(label)
        paths["dir"].mkdir(parents=True, exist_ok=True)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m023_direction_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(paths["dir"].relative_to(REPO)),
                "--arm",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        return {
            "ok": run["exit_code"] == 0,
            "label": label,
            "reused_complete_artifacts": False,
            "run": run,
        }

    reference_run = run_arm("D-R")
    if not reference_run["ok"]:
        return {
            "ok": False,
            "reason": "M023 Stage-A D-R execution failed",
            "feature_sha": feature_sha,
            "execution": [reference_run],
        }
    try:
        _m023_stage_a_validate_artifacts("D-R")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "execution": [reference_run],
        }

    executed = {"D-R": reference_run}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            label: pool.submit(run_arm, label)
            for label in ("D-S", "D-B")
        }
        for label in ("D-S", "D-B"):
            executed[label] = futures[label].result()

    failed_runs = [
        label for label in ("D-S", "D-B")
        if not executed[label]["ok"]
    ]
    if failed_runs:
        return {
            "ok": False,
            "reason": f"M023 Stage-A arm execution failed: {failed_runs}",
            "feature_sha": feature_sha,
            "execution": executed,
        }

    validated = {}
    try:
        for label in ("D-R", "D-S", "D-B"):
            validated[label] = _m023_stage_a_validate_artifacts(label)
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "execution": executed,
        }

    def compact(item):
        summary = item["summary"]
        aggregate = summary.get("aggregate") or {}
        return {
            "label": item["label"],
            "direction": item["direction"],
            "hashes": item["hashes"],
            "aggregate": aggregate,
            "per_symbol": summary.get("per_symbol"),
            "folds": summary.get("folds"),
            "iso_weeks": summary.get("iso_weeks"),
            "eat_active": summary.get("eat_active"),
            "eat_off_hours": summary.get("eat_off_hours"),
            "direction_filter": summary.get("direction_filter"),
            "direction_invariants": summary.get("direction_invariants"),
            "tp_safety": summary.get("tp_safety"),
            "remaining_positions": summary.get("remaining_positions"),
            "source_date_replay_hashes": summary.get(
                "source_date_replay_hashes"
            ),
            "checks": item["checks"],
        }

    return {
        "ok": True,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "family": "m023-stage-a-direction",
        "execution": {
            "order": ["D-R", ["D-S", "D-B"]],
            "maximum_concurrent_nonreference_arms": 2,
            "runs": {
                label: {
                    "reused_complete_artifacts": executed[label][
                        "reused_complete_artifacts"
                    ],
                    "exit_code": (
                        None
                        if executed[label]["run"] is None
                        else executed[label]["run"]["exit_code"]
                    ),
                }
                for label in ("D-R", "D-S", "D-B")
            },
        },
        "partition": {
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-07-08T00:00:00Z",
            "trading_dates": 225,
            "date_list_sha256":
                "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0",
        },
        "arms": {
            label: compact(validated[label])
            for label in ("D-R", "D-S", "D-B")
        },
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "seen-research-only",
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
        },
    }


def _m023_stage_a_fraction(numerator, denominator):
    denominator = float(denominator)
    if denominator == 0:
        raise RuntimeError("M023 Stage-A robustness denominator is zero")
    return float(numerator) / abs(denominator)


def m023_stage_a_direction_assessment():
    """Mechanically classify Stage-A arms and fix one Stage-B direction."""

    feature_sha = _require_m023_branch()
    try:
        rows = {
            label: _m023_stage_a_validate_artifacts(label)
            for label in ("D-R", "D-S", "D-B")
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
            "safety": {
                "economic_replay_run": False,
                "historical_holdout_economic_data_used": False,
                "m021_post_cutoff_data_used": False,
                "real_order_api_called": False,
            },
        }
    if any(value is None for value in rows.values()):
        return {
            "ok": False,
            "reason": "M023 Stage-A artifacts are incomplete",
            "feature_sha": feature_sha,
        }

    reference = rows["D-R"]["summary"]
    ref_agg = reference["aggregate"]
    ref_symbols = reference["per_symbol"]
    ref_folds = reference["folds"]
    ref_weeks = reference["iso_weeks"]
    ref_active = reference["eat_active"]

    def assess(label):
        candidate = rows[label]["summary"]
        agg = candidate["aggregate"]
        symbols = candidate["per_symbol"]
        folds = candidate["folds"]
        weeks = candidate["iso_weeks"]
        active = candidate["eat_active"]

        mandatory = dict(rows[label]["checks"])
        mandatory_ok = all(mandatory.values())

        total_activity_ratio = (
            float(agg["closed_trades"]) / float(ref_agg["closed_trades"])
            if int(ref_agg["closed_trades"]) > 0 else 0.0
        )
        symbol_activity = {
            symbol: (
                float(symbols[symbol]["closed_trades"])
                / float(ref_symbols[symbol]["closed_trades"])
                if int(ref_symbols[symbol]["closed_trades"]) > 0
                else 0.0
            )
            for symbol in sorted(ref_symbols)
        }
        fold_activity = {
            fold: (
                float(folds[fold]["closed_trades"])
                / float(ref_folds[fold]["closed_trades"])
                if int(ref_folds[fold]["closed_trades"]) > 0
                else 0.0
            )
            for fold in sorted(ref_folds)
        }
        ref_trade_weeks = [
            week
            for week, row in ref_weeks.items()
            if int(row["closed_trades"]) > 0
        ]
        represented_weeks = sum(
            int((weeks.get(week) or {}).get("closed_trades", 0)) > 0
            for week in ref_trade_weeks
        )
        week_presence_ratio = (
            represented_weeks / len(ref_trade_weeks)
            if ref_trade_weeks else 0.0
        )
        representation = {
            "total_closed_ge_35pct": total_activity_ratio >= 0.35,
            "every_symbol_ge_25pct": all(
                ratio >= 0.25 for ratio in symbol_activity.values()
            ),
            "every_fold_ge_25pct": all(
                ratio >= 0.25 for ratio in fold_activity.values()
            ),
            "weeks_ge_80pct": week_presence_ratio >= 0.80,
        }
        representation_ok = all(representation.values())

        candidate_mean = candidate["folds"]
        fold_better = sum(
            candidate_mean[fold]["mean_trade_pl"] is not None
            and ref_folds[fold]["mean_trade_pl"] is not None
            and float(candidate_mean[fold]["mean_trade_pl"])
                > float(ref_folds[fold]["mean_trade_pl"])
            for fold in ref_folds
        )
        symbol_better = sum(
            symbols[symbol]["mean_trade_pl"] is not None
            and ref_symbols[symbol]["mean_trade_pl"] is not None
            and float(symbols[symbol]["mean_trade_pl"])
                > float(ref_symbols[symbol]["mean_trade_pl"])
            for symbol in ref_symbols
        )

        eligible_weeks = []
        better_weeks = []
        for week in sorted(set(ref_weeks) | set(weeks)):
            ref_row = ref_weeks.get(week)
            cand_row = weeks.get(week)
            if (
                ref_row
                and cand_row
                and int(ref_row["closed_trades"]) >= 10
                and int(cand_row["closed_trades"]) >= 10
            ):
                eligible_weeks.append(week)
                if (
                    cand_row["mean_trade_pl"] is not None
                    and ref_row["mean_trade_pl"] is not None
                    and float(cand_row["mean_trade_pl"])
                        > float(ref_row["mean_trade_pl"])
                ):
                    better_weeks.append(week)
        weekly_ratio = (
            len(better_weeks) / len(eligible_weeks)
            if eligible_weeks else 0.0
        )
        weekly_ok = (
            len(eligible_weeks) >= 20
            and weekly_ratio >= 0.55
        )

        positive_symbol_deltas = {
            symbol: (
                float(symbols[symbol]["net_realized_pl"])
                - float(ref_symbols[symbol]["net_realized_pl"])
            )
            for symbol in ref_symbols
            if (
                float(symbols[symbol]["net_realized_pl"])
                - float(ref_symbols[symbol]["net_realized_pl"])
            ) > 0
        }
        symbol_positive_sum = sum(positive_symbol_deltas.values())
        max_symbol_share = (
            max(positive_symbol_deltas.values()) / symbol_positive_sum
            if symbol_positive_sum > 0 else None
        )

        positive_fold_deltas = {
            fold: (
                float(folds[fold]["net_realized_pl"])
                - float(ref_folds[fold]["net_realized_pl"])
            )
            for fold in ref_folds
            if (
                float(folds[fold]["net_realized_pl"])
                - float(ref_folds[fold]["net_realized_pl"])
            ) > 0
        }
        fold_positive_sum = sum(positive_fold_deltas.values())
        max_fold_share = (
            max(positive_fold_deltas.values()) / fold_positive_sum
            if fold_positive_sum > 0 else None
        )

        net_gain = (
            float(agg["net_realized_pl"])
            - float(ref_agg["net_realized_pl"])
        )
        concentration = {
            "positive_total_pl_improvement": net_gain > 0,
            "positive_symbol_deltas": positive_symbol_deltas,
            "max_positive_symbol_delta_share": max_symbol_share,
            "symbol_share_le_70pct": (
                max_symbol_share is not None and max_symbol_share <= 0.70
            ),
            "positive_fold_deltas": positive_fold_deltas,
            "max_positive_fold_delta_share": max_fold_share,
            "fold_share_le_60pct": (
                max_fold_share is not None and max_fold_share <= 0.60
            ),
        }
        concentration_ok = bool(
            concentration["positive_total_pl_improvement"]
            and concentration["symbol_share_le_70pct"]
            and concentration["fold_share_le_60pct"]
        )

        support_checks = {
            "net_pl_strictly_better": (
                float(agg["net_realized_pl"])
                > float(ref_agg["net_realized_pl"])
            ),
            "max_dd_usd_no_worse": (
                float(agg["maximum_equity_drawdown"])
                <= float(ref_agg["maximum_equity_drawdown"])
            ),
            "mean_trade_pl_strictly_better": (
                float(candidate["folds"]["F1"]["closed_trades"]) >= 0
                and float(candidate["eat_active"]["closed_trades"]) >= 0
                and float(
                    sum(
                        row["net_realized_pl"]
                        for row in candidate["folds"].values()
                    )
                    / sum(
                        row["closed_trades"]
                        for row in candidate["folds"].values()
                    )
                )
                > float(
                    sum(
                        row["net_realized_pl"]
                        for row in ref_folds.values()
                    )
                    / sum(
                        row["closed_trades"]
                        for row in ref_folds.values()
                    )
                )
            ),
            "win_rate_within_1pp": (
                float(agg["win_rate_nonflat_pct"])
                >= float(ref_agg["win_rate_nonflat_pct"]) - 1.0
            ),
            "fold_mean_better_ge_4": fold_better >= 4,
            "symbol_mean_better_ge_3": symbol_better >= 3,
            "eat_active_mean_better": (
                active["mean_trade_pl"] is not None
                and ref_active["mean_trade_pl"] is not None
                and float(active["mean_trade_pl"])
                    > float(ref_active["mean_trade_pl"])
            ),
            "weekly_mean_better_ge_55pct_with_ge20": weekly_ok,
            "symbol_concentration_le_70pct": concentration_ok
                and concentration["symbol_share_le_70pct"],
            "fold_concentration_le_60pct": concentration_ok
                and concentration["fold_share_le_60pct"],
        }
        support_ok = all(support_checks.values())

        if not mandatory_ok or not representation_ok:
            classification = "INELIGIBLE"
        elif support_ok:
            classification = "SUPPORTED"
        else:
            classification = "NOT SUPPORTED"

        overall_closed = sum(
            int(row["closed_trades"]) for row in folds.values()
        )
        overall_pl = sum(
            float(row["net_realized_pl"]) for row in folds.values()
        )
        mean_trade_pl = (
            overall_pl / overall_closed if overall_closed else None
        )

        return {
            "label": label,
            "direction": candidate["direction"],
            "classification": classification,
            "mandatory": mandatory,
            "mandatory_ok": mandatory_ok,
            "representation": {
                **representation,
                "ok": representation_ok,
                "total_activity_ratio": total_activity_ratio,
                "per_symbol_activity_ratio": symbol_activity,
                "per_fold_activity_ratio": fold_activity,
                "reference_trade_weeks": len(ref_trade_weeks),
                "represented_trade_weeks": represented_weeks,
                "week_presence_ratio": week_presence_ratio,
            },
            "support_checks": support_checks,
            "support_ok": support_ok,
            "economics": {
                "net_realized_pl": agg["net_realized_pl"],
                "maximum_equity_drawdown":
                    agg["maximum_equity_drawdown"],
                "maximum_equity_drawdown_pct":
                    agg["maximum_equity_drawdown_pct"],
                "mean_trade_pl": mean_trade_pl,
                "win_rate_nonflat_pct": agg["win_rate_nonflat_pct"],
                "eat_active_mean_trade_pl": active["mean_trade_pl"],
            },
            "robustness": {
                "folds_mean_better": fold_better,
                "symbols_mean_better": symbol_better,
                "eligible_iso_weeks": len(eligible_weeks),
                "better_iso_weeks": len(better_weeks),
                "better_iso_week_ratio": weekly_ratio,
                "concentration": concentration,
            },
            "activity_ratio": total_activity_ratio,
        }

    assessments = {
        label: assess(label)
        for label in ("D-S", "D-B")
    }
    supported = [
        label
        for label in ("D-S", "D-B")
        if assessments[label]["classification"] == "SUPPORTED"
    ]

    selection_detail = {}
    if not supported:
        fixed_arm = "D-R"
        fixed_direction = "BOTH"
        selection_reason = "neither single-direction arm is SUPPORTED"
    elif len(supported) == 1:
        fixed_arm = supported[0]
        fixed_direction = _m023_stage_a_expected()[fixed_arm]
        selection_reason = "exactly one single-direction arm is SUPPORTED"
    else:
        scores = {}
        for label in supported:
            row = assessments[label]
            econ = row["economics"]
            scores[label] = {
                "pl_gain_fraction": _m023_stage_a_fraction(
                    float(econ["net_realized_pl"])
                    - float(ref_agg["net_realized_pl"]),
                    ref_agg["net_realized_pl"],
                ),
                "dd_improvement_fraction": _m023_stage_a_fraction(
                    float(ref_agg["maximum_equity_drawdown"])
                    - float(econ["maximum_equity_drawdown"]),
                    ref_agg["maximum_equity_drawdown"],
                ),
                "mean_trade_gain_fraction": _m023_stage_a_fraction(
                    float(econ["mean_trade_pl"])
                    - (
                        sum(
                            float(x["net_realized_pl"])
                            for x in ref_folds.values()
                        )
                        / sum(
                            int(x["closed_trades"])
                            for x in ref_folds.values()
                        )
                    ),
                    (
                        sum(
                            float(x["net_realized_pl"])
                            for x in ref_folds.values()
                        )
                        / sum(
                            int(x["closed_trades"])
                            for x in ref_folds.values()
                        )
                    ),
                ),
                "win_rate_gain_fraction": _m023_stage_a_fraction(
                    float(econ["win_rate_nonflat_pct"])
                    - float(ref_agg["win_rate_nonflat_pct"]),
                    ref_agg["win_rate_nonflat_pct"],
                ),
                "active_mean_gain_fraction": _m023_stage_a_fraction(
                    float(econ["eat_active_mean_trade_pl"])
                    - float(ref_active["mean_trade_pl"]),
                    ref_active["mean_trade_pl"],
                ),
            }
            scores[label]["robustness_maximin"] = min(
                scores[label].values()
            )

        def rank_key(label):
            row = assessments[label]
            return (
                scores[label]["robustness_maximin"],
                row["robustness"]["folds_mean_better"],
                row["robustness"]["symbols_mean_better"],
                row["robustness"]["better_iso_week_ratio"],
                row["activity_ratio"],
                -ord(label[-1]),
            )

        fixed_arm = max(supported, key=rank_key)
        fixed_direction = _m023_stage_a_expected()[fixed_arm]
        selection_reason = (
            "both single-direction arms SUPPORTED; frozen maximin/tie-break "
            "rule applied"
        )
        selection_detail = {"scores": scores}

    return {
        "ok": True,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "reference": {
            "label": "D-R",
            "direction": "BOTH",
            "classification": "REFERENCE",
            "aggregate": ref_agg,
            "per_symbol": ref_symbols,
            "folds": ref_folds,
            "iso_weeks": ref_weeks,
            "eat_active": ref_active,
            "eat_off_hours": reference["eat_off_hours"],
            "hashes": rows["D-R"]["hashes"],
        },
        "assessments": assessments,
        "supported_nonreference": supported,
        "stage_b_fixed_arm": fixed_arm,
        "stage_b_fixed_direction": fixed_direction,
        "selection_reason": selection_reason,
        "selection_detail": selection_detail,
        "frozen_gates": {
            "total_activity_min_ratio": 0.35,
            "per_symbol_activity_min_ratio": 0.25,
            "per_fold_activity_min_ratio": 0.25,
            "week_presence_min_ratio": 0.80,
            "win_rate_max_deficit_pp": 1.0,
            "fold_mean_better_min": 4,
            "symbol_mean_better_min": 3,
            "weekly_better_min_ratio": 0.55,
            "eligible_week_min_count": 20,
            "positive_symbol_delta_max_share": 0.70,
            "positive_fold_delta_max_share": 0.60,
        },
        "safety": {
            "economic_replay_run": False,
            "existing_stage_a_artifacts_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "stage_b_session_replay_run": False,
        },
    }


def m023_direction_session_review():
    """Read the accepted M023 artifact and publish compact partition/hour tables."""

    feature_sha = _require_m023_branch()
    artifact = (
        M023_DIRECTION_SESSION_DIR
        / "m023-direction-session-diagnostics-a.json"
    )
    if not artifact.is_file():
        return {
            "ok": False,
            "reason": "accepted M023 diagnostic artifact is missing",
            "feature_sha": feature_sha,
        }
    observed = _sha256(artifact)
    expected = "0b306c2341befd7110ea2a6695ecd4fc473055fb2231849b5a3741a11251d9a2"
    if observed != expected:
        return {
            "ok": False,
            "reason": "M023 diagnostic artifact SHA mismatch",
            "feature_sha": feature_sha,
            "observed_sha256": observed,
            "expected_sha256": expected,
        }

    report = json.loads(artifact.read_text(encoding="utf-8"))
    arms = report["arms"]
    windows = (
        "ALL-HOURS",
        "EAT-MORNING",
        "EAT-MIDDAY",
        "EAT-AFTERNOON",
        "EAT-EVENING",
        "EAT-ACTIVE",
        "EAT-OFF-HOURS",
        "LONDON-OPEN-TRANSITION",
        "LONDON-NY-OVERLAP",
    )

    def slim(row):
        return {
            "closed_trades": row.get("closed_trades"),
            "net_realized_pl": row.get("net_realized_pl"),
            "mean_trade_pl": row.get("mean_trade_pl"),
            "median_trade_pl": row.get("median_trade_pl"),
            "win_rate_nonflat_pct": row.get("win_rate_nonflat_pct"),
            "positive_symbol_count": sum(
                float(value.get("net_realized_pl", 0.0)) > 0
                for value in (row.get("per_symbol") or {}).values()
            ),
        }

    partition_windows = {}
    for arm in ("P2-R", "P2-03", "P2-08"):
        partition_windows[arm] = {}
        for partition in ("development", "validation"):
            partition_windows[arm][partition] = {}
            for direction in ("BOTH", "SELL", "BUY"):
                partition_windows[arm][partition][direction] = {
                    window: slim(
                        arms[arm][partition][direction]["windows"][window]
                    )
                    for window in windows
                }

    hourly_p2_08 = {}
    for direction in ("BOTH", "SELL", "BUY"):
        hourly_p2_08[direction] = {}
        for zone, table in (
            arms["P2-08"]["combined"][direction]["hourly"].items()
        ):
            hourly_p2_08[direction][zone] = {
                hour: {
                    "closed_trades": row.get("closed_trades"),
                    "net_realized_pl": row.get("net_realized_pl"),
                    "mean_trade_pl": row.get("mean_trade_pl"),
                    "win_rate_nonflat_pct": row.get(
                        "win_rate_nonflat_pct"
                    ),
                }
                for hour, row in table.items()
            }

    return {
        "ok": True,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "artifact_sha256": observed,
        "partition_windows": partition_windows,
        "hourly_p2_08": hourly_p2_08,
        "safety": {
            "economic_replay_run": False,
            "existing_m023_artifact_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m023_direction_session_tests():
    """Run the narrow native gate for M023 read-only diagnostics."""

    feature_sha = _require_m023_branch()
    tests = [
        "tests/test_direction_session_diagnostics.py",
        "tests/test_m023_direction_research.py",
        "tests/test_m023_session_research.py",
        "tests/test_backtest_baseline_reporting.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "market_data_read_only": True,
            "existing_diagnostic_json_only": True,
            "economic_replay_run": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def m023_direction_session_diagnostic():
    """Build deterministic M023 diagnostics from accepted M022 JSON only."""

    feature_sha = _require_m023_branch()
    output_dir = _ensure_baseline_path(M023_DIRECTION_SESSION_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_a = output_dir / "m023-direction-session-diagnostics-a.json"
    output_b = output_dir / "m023-direction-session-diagnostics-b.json"

    def run_one(path):
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.direction_session_diagnostics",
                "--repo-root",
                ".",
                "--output",
                str(path.relative_to(REPO)),
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return False, run
        if not path.is_file():
            return False, {
                **run,
                "stderr": run["stderr"] + "\nM023 output artifact missing",
            }
        # The CLI stdout contains review convenience data and may be large.
        # Artifact JSON is the authoritative deterministic product.
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, {
                **run,
                "stderr": run["stderr"] + f"\ninvalid M023 artifact JSON: {exc}",
            }
        return True, run

    runs = []
    if not output_a.is_file():
        ok_a, run_a = run_one(output_a)
        runs.append(run_a)
        if not ok_a:
            return {
                "ok": False,
                "reason": "first M023 diagnostic build failed",
                "feature_branch": "direction-session-research",
                "feature_sha": feature_sha,
                "run": run_a,
            }
    if not output_b.is_file():
        ok_b, run_b = run_one(output_b)
        runs.append(run_b)
        if not ok_b:
            return {
                "ok": False,
                "reason": "second M023 diagnostic build failed",
                "feature_branch": "direction-session-research",
                "feature_sha": feature_sha,
                "run": run_b,
            }

    sha_a = _sha256(output_a)
    sha_b = _sha256(output_b)
    deterministic = sha_a == sha_b
    if not deterministic:
        return {
            "ok": False,
            "reason": "M023 diagnostic artifacts are non-deterministic",
            "feature_branch": "direction-session-research",
            "feature_sha": feature_sha,
            "artifact": {
                "a_path": str(output_a.relative_to(REPO)),
                "b_path": str(output_b.relative_to(REPO)),
                "a_sha256": sha_a,
                "b_sha256": sha_b,
            },
            "runs": runs,
        }

    report = json.loads(output_a.read_text(encoding="utf-8"))
    safety = report.get("safety") or {}
    safety_ok = bool(
        safety.get("economic_replay_run") is False
        and safety.get("existing_diagnostic_json_only") is True
        and safety.get("historical_holdout_economic_data_used") is False
        and safety.get("m021_post_cutoff_data_used") is False
        and safety.get("real_order_api_called") is False
    )

    def slim(summary):
        return {
            "closed_trades": summary.get("closed_trades"),
            "wins": summary.get("wins"),
            "losses": summary.get("losses"),
            "flats": summary.get("flats"),
            "win_rate_nonflat_pct": summary.get("win_rate_nonflat_pct"),
            "net_realized_pl": summary.get("net_realized_pl"),
            "mean_trade_pl": summary.get("mean_trade_pl"),
            "median_trade_pl": summary.get("median_trade_pl"),
            "entry_spread_points": summary.get("entry_spread_points"),
            "exit_counts": summary.get("exit_counts"),
            "per_symbol": summary.get("per_symbol"),
        }

    arms = report.get("arms") or {}
    overall = {}
    windows = {}
    weekdays = {}
    fold_stability = {}
    for arm in ("P2-R", "P2-03", "P2-08"):
        overall[arm] = {}
        for partition in ("development", "validation", "combined"):
            overall[arm][partition] = {
                direction: slim(
                    arms[arm][partition][direction]["overall"]
                )
                for direction in ("BOTH", "SELL", "BUY")
            }

        windows[arm] = {
            direction: {
                name: slim(summary)
                for name, summary in
                arms[arm]["combined"][direction]["windows"].items()
            }
            for direction in ("BOTH", "SELL", "BUY")
        }
        weekdays[arm] = {
            direction: {
                name: slim(summary)
                for name, summary in
                arms[arm]["combined"][direction]["weekdays"].items()
            }
            for direction in ("BOTH", "SELL", "BUY")
        }
        fold_stability[arm] = {}
        for direction in ("BOTH", "SELL", "BUY"):
            fold_stability[arm][direction] = {}
            for name, row in arms[arm]["fold_stability"][direction].items():
                fold_stability[arm][direction][name] = {
                    "folds_positive_net_pl": row.get(
                        "folds_positive_net_pl"
                    ),
                    "folds_net_pl_above_both_all_hours": row.get(
                        "folds_net_pl_above_both_all_hours"
                    ),
                    "folds_mean_trade_pl_above_both_all_hours": row.get(
                        "folds_mean_trade_pl_above_both_all_hours"
                    ),
                    "largest_fold_share_of_positive_net_pl": row.get(
                        "largest_fold_share_of_positive_net_pl"
                    ),
                    "largest_fold_share_of_positive_delta_vs_both_all_hours":
                        row.get(
                            "largest_fold_share_of_positive_delta_vs_both_all_hours"
                        ),
                    "folds": [
                        {
                            "fold": fold.get("fold"),
                            "closed_trades": fold.get("closed_trades"),
                            "net_realized_pl": fold.get("net_realized_pl"),
                            "mean_trade_pl": fold.get("mean_trade_pl"),
                            "positive_symbol_count": fold.get(
                                "positive_symbol_count"
                            ),
                        }
                        for fold in row.get("folds", [])
                    ],
                }

    # Hourly output is diagnostic only; return a compact P2-08 combined table
    # for reviewer visibility while the full artifact retains every arm.
    hourly_p2_08 = {
        direction: {
            zone: {
                hour: {
                    "closed_trades": summary.get("closed_trades"),
                    "net_realized_pl": summary.get("net_realized_pl"),
                    "mean_trade_pl": summary.get("mean_trade_pl"),
                    "win_rate_nonflat_pct": summary.get(
                        "win_rate_nonflat_pct"
                    ),
                }
                for hour, summary in table.items()
            }
            for zone, table in
            arms["P2-08"]["combined"][direction]["hourly"].items()
        }
        for direction in ("BOTH", "SELL", "BUY")
    }

    return {
        "ok": bool(deterministic and safety_ok),
        "feature_branch": "direction-session-research",
        "feature_sha": feature_sha,
        "artifact": {
            "a_path": str(output_a.relative_to(REPO)),
            "b_path": str(output_b.relative_to(REPO)),
            "a_sha256": sha_a,
            "b_sha256": sha_b,
            "deterministic": deterministic,
            "reused_first_artifact": len(runs) < 2,
        },
        "sources": report.get("sources"),
        "timezone_runtime": report.get("timezone_runtime"),
        "folds": report.get("folds"),
        "review_summary": {
            "overall": overall,
            "windows": windows,
            "weekdays": weekdays,
            "fold_stability": fold_stability,
            "hourly_p2_08": hourly_p2_08,
        },
        "runs": runs,
        "safety": safety,
    }



def m022_phase1_tests():
    """Run fixed native tests for M022 Phase-1 research machinery."""

    feature_sha = _require_m022_branch()
    tests = [
        "tests/test_parameter_research.py",
        "tests/test_replay_indicator_cache.py",
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


def m024_symbol_specialization_tests():
    """Run the narrow native gate for M024 read-only symbol diagnostics."""

    feature_sha = _require_m024_branch()
    tests = [
        "tests/test_m024_symbol_specialization.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "accepted_m023_d_b_summary_only": True,
            "economic_replay_run": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def m024_symbol_specialization_diagnostic():
    """Build deterministic M024 attribution from accepted M023 D-B only."""

    feature_sha = _require_m024_branch()

    try:
        source = _m023_stage_a_validate_artifacts("D-B")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
        }
    if source is None:
        return {
            "ok": False,
            "reason": "accepted M023 Stage-A D-B artifacts are missing",
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
        }

    expected_summary_sha = (
        "7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c"
    )
    source_hashes = source["hashes"]
    if (
        source_hashes.get("summary_a") != expected_summary_sha
        or source_hashes.get("summary_b") != expected_summary_sha
    ):
        return {
            "ok": False,
            "reason": "accepted M023 D-B summary hash changed",
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
            "observed_hashes": source_hashes,
        }

    output_dir = _ensure_baseline_path(M024_SYMBOL_SPECIALIZATION_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_a = output_dir / "m024-symbol-specialization-a.json"
    output_b = output_dir / "m024-symbol-specialization-b.json"

    exists = [output_a.is_file(), output_b.is_file()]
    if any(exists) and not all(exists):
        return {
            "ok": False,
            "reason": "partial immutable M024 diagnostic artifacts",
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
        }

    def run_one(path):
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m024_symbol_specialization",
                "--repo-root",
                ".",
                "--output",
                str(path.relative_to(REPO)),
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return False, run
        if not path.is_file():
            return False, {
                **run,
                "stderr": run["stderr"] + "\nM024 output artifact missing",
            }
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, {
                **run,
                "stderr": run["stderr"] + f"\ninvalid M024 artifact JSON: {exc}",
            }
        return True, run

    runs = []
    if not output_a.is_file():
        ok_a, run_a = run_one(output_a)
        runs.append(run_a)
        if not ok_a:
            return {
                "ok": False,
                "reason": "first M024 diagnostic build failed",
                "feature_branch": "symbol-specialization-research",
                "feature_sha": feature_sha,
                "run": run_a,
            }

        ok_b, run_b = run_one(output_b)
        runs.append(run_b)
        if not ok_b:
            return {
                "ok": False,
                "reason": "second M024 diagnostic build failed",
                "feature_branch": "symbol-specialization-research",
                "feature_sha": feature_sha,
                "run": run_b,
            }

    sha_a = _sha256(output_a)
    sha_b = _sha256(output_b)
    if sha_a != sha_b:
        return {
            "ok": False,
            "reason": "M024 diagnostic artifacts are non-deterministic",
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
            "artifact": {
                "a_sha256": sha_a,
                "b_sha256": sha_b,
            },
        }

    report = json.loads(output_a.read_text(encoding="utf-8"))
    safety = report.get("safety") or {}
    safety_ok = bool(
        report.get("milestone") == "M024"
        and report.get("analysis_kind") == "DESCRIPTIVE SUBSET ATTRIBUTION"
        and report.get("causal_symbol_filtered_replay") is False
        and safety.get("economic_replay_run") is False
        and safety.get("accepted_m023_d_b_summary_only") is True
        and safety.get("historical_holdout_economic_data_used") is False
        and safety.get("m021_post_cutoff_data_used") is False
        and safety.get("m025_outcomes_used") is False
        and safety.get("real_order_api_called") is False
    )
    if not safety_ok:
        return {
            "ok": False,
            "reason": "M024 diagnostic safety contract failed",
            "feature_branch": "symbol-specialization-research",
            "feature_sha": feature_sha,
            "artifact_sha256": sha_a,
        }

    subsets = {}
    for label in ("SYM-R", "SYM-UJ", "SYM-JPY", "SYM-NONJPY"):
        row = (report.get("subsets") or {}).get(label)
        if row is None:
            return {
                "ok": False,
                "reason": f"M024 diagnostic missing frozen subset {label}",
                "feature_branch": "symbol-specialization-research",
                "feature_sha": feature_sha,
            }
        subsets[label] = {
            "classification": row.get("classification"),
            "symbols": row.get("symbols"),
            "overall": row.get("overall"),
            "fold_stability": row.get("fold_stability"),
            "weekly_stability": row.get("weekly_stability"),
            "descriptive_screen_checks": row.get(
                "descriptive_screen_checks"
            ),
        }

    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "family": "m024-symbol-specialization-diagnostic",
        "source": {
            "m023_stage_a_d_b_summary_sha256": expected_summary_sha,
            "m023_stage_a_family_result":
                "04f8cb971ac56b06739aba594df1a2090745f396",
            "m023_stage_a_assessment":
                "ed01975c5ea7945d9890d807c58ff133e07a6aa1",
        },
        "artifact": {
            "a_path": str(output_a.relative_to(REPO)),
            "b_path": str(output_b.relative_to(REPO)),
            "a_sha256": sha_a,
            "b_sha256": sha_b,
            "deterministic": True,
        },
        "subsets": subsets,
        "descriptively_promising_subsets": report.get(
            "descriptively_promising_subsets"
        ),
        "next_stage_authorized": report.get("next_stage_authorized"),
        "next_stage_rule": report.get("next_stage_rule"),
        "runs": runs,
        "safety": safety,
    }


def _m024_stage2_expected():
    return {
        "C-R": ("EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"),
        "C-UJ": ("USDJPY",),
    }


def _m024_stage2_paths(label):
    arm_dir = M024_STAGE2_SYMBOL_DIR / label
    prefix = f"M024-S2-{label}"
    return {
        "dir": arm_dir,
        "a_baseline": arm_dir / f"{prefix}-a-baseline.json",
        "b_baseline": arm_dir / f"{prefix}-b-baseline.json",
        "a_diagnostic": arm_dir / f"{prefix}-a-diagnostic.json",
        "b_diagnostic": arm_dir / f"{prefix}-b-diagnostic.json",
        "a_summary": arm_dir / f"{prefix}-a-summary.json",
        "b_summary": arm_dir / f"{prefix}-b-summary.json",
    }


def _m024_stage2_validate_artifacts(label):
    expected_symbols = _m024_stage2_expected()[label]
    paths = _m024_stage2_paths(label)
    required = [
        paths["a_baseline"],
        paths["b_baseline"],
        paths["a_diagnostic"],
        paths["b_diagnostic"],
        paths["a_summary"],
        paths["b_summary"],
    ]
    exists = [path.is_file() for path in required]
    if any(exists) and not all(exists):
        raise RuntimeError(
            f"M024 Stage-2 {label} has partial immutable artifacts"
        )
    if not all(exists):
        return None

    hashes = {
        "baseline_a": _sha256(paths["a_baseline"]),
        "baseline_b": _sha256(paths["b_baseline"]),
        "diagnostic_a": _sha256(paths["a_diagnostic"]),
        "diagnostic_b": _sha256(paths["b_diagnostic"]),
        "summary_a": _sha256(paths["a_summary"]),
        "summary_b": _sha256(paths["b_summary"]),
    }
    deterministic = (
        hashes["baseline_a"] == hashes["baseline_b"]
        and hashes["diagnostic_a"] == hashes["diagnostic_b"]
        and hashes["summary_a"] == hashes["summary_b"]
    )
    summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
    partition = summary.get("partition") or {}
    safety = summary.get("safety") or {}
    tp = summary.get("tp_safety") or {}
    direction = summary.get("direction_invariants") or {}
    symbol_inv = summary.get("symbol_invariants") or {}
    expected_market = ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"]
    expected_params = {
        "stochastic_k_period": 21,
        "stochastic_d_period": 7,
        "stochastic_slowing": 7,
        "oversold_level": 20.0,
        "overbought_level": 80.0,
        "ema_period": 7,
        "decision_spread_max_points": None,
        "atr_sl_multiplier": 1.5,
        "atr_tp_multiplier": 3.0,
        "block_00_04_utc": False,
    }

    checks = {
        "deterministic": deterministic,
        "milestone": summary.get("milestone") == "M024",
        "stage": summary.get("stage") == "2",
        "experiment_id": summary.get("experiment_id") == f"M024-S2-{label}",
        "arm_id": summary.get("arm_id") == label,
        "direction_buy_only": summary.get("direction") == "BUY",
        "session_all_hours": summary.get("session") == "all-hours",
        "m15_disabled": summary.get("m15_signal_enabled") is False,
        "position_size": float(summary.get("position_size", 0.0)) == 0.1,
        "parameters": summary.get("parameters") == expected_params,
        "cost_contract": summary.get("cost_contract")
        == (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "strategy_symbols": tuple(summary.get("strategy_symbols") or ())
        == tuple(expected_symbols),
        "market_data_symbols": summary.get("market_data_symbols")
        == expected_market,
        "symbol_invariant_strategy": tuple(
            symbol_inv.get("strategy_symbols") or ()
        ) == tuple(expected_symbols),
        "symbol_invariant_market": symbol_inv.get("market_data_symbols")
        == expected_market,
        "excluded_symbol_trades_zero": int(
            symbol_inv.get("excluded_symbol_closed_trade_rows", -1)
        ) == 0,
        "sell_entries_zero": int(direction.get("sell_accepted_entries", -1)) == 0,
        "source_manifest": partition.get("source_manifest_sha256")
        == "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558",
        "start_utc": partition.get("start_utc")
        == "2025-08-25T00:00:00Z",
        "end_exclusive_utc": partition.get("end_exclusive_utc")
        == "2026-07-08T00:00:00Z",
        "trading_dates": int(partition.get("trading_dates", 0)) == 225,
        "date_list_sha256": partition.get("date_list_sha256")
        == "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0",
        "strict_common_boundary_clock": (
            partition.get("strict_common_boundary_clock") is True
        ),
        "full_symbol_m1_preserved": (
            partition.get("full_symbol_m1_preserved") is True
        ),
        "fold_count": len(partition.get("folds") or []) == 5,
        "tp_negative_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "tp_wrong_side_zero": int(tp.get("wrong_side_initial_tp", -1)) == 0,
        "holdout_unused": (
            safety.get("historical_holdout_economic_data_used") is False
        ),
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "m025_unused": safety.get("m025_outcomes_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "session_filter_absent": safety.get("session_filter_applied") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
        "market_data_not_reduced": (
            safety.get("market_data_universe_reduced") is False
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(
            f"M024 Stage-2 {label} failed frozen invariants: {failed}"
        )

    return {
        "label": label,
        "strategy_symbols": list(expected_symbols),
        "hashes": hashes,
        "summary": summary,
        "checks": checks,
    }


def _m024_stage2_reference_equivalence(stage2_ref, m023_d_b):
    current = stage2_ref["summary"]
    accepted = m023_d_b["summary"]
    checks = {
        "aggregate": current.get("aggregate") == accepted.get("aggregate"),
        "per_symbol": current.get("per_symbol") == accepted.get("per_symbol"),
        "folds": current.get("folds") == accepted.get("folds"),
        "iso_weeks": current.get("iso_weeks") == accepted.get("iso_weeks"),
        "tp_safety": current.get("tp_safety") == accepted.get("tp_safety"),
        "remaining_positions": current.get("remaining_positions")
        == accepted.get("remaining_positions"),
        "source_date_replay_hashes": current.get("source_date_replay_hashes")
        == accepted.get("source_date_replay_hashes"),
    }
    return {
        "passes": all(checks.values()),
        "checks": checks,
    }


def m024_stage2_symbol_tests():
    """Run focused native tests for M024 Stage-2 causal symbol research."""

    feature_sha = _require_m024_branch()
    tests = [
        "tests/test_m024_symbol_specialization.py",
        "tests/test_m024_symbol_causal_research.py",
        "tests/test_m023_direction_research.py",
        "tests/test_backtest_baseline_reporting.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "economic_replay_run": False,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def m024_stage2_symbol_family():
    """Run C-R, prove D-B parity, then run the sole C-UJ causal arm."""

    feature_sha = _require_m024_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 source manifest is missing",
            "feature_sha": feature_sha,
        }
    if _sha256(manifest) != (
        "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
    ):
        return {
            "ok": False,
            "reason": "accepted M022 source manifest SHA changed",
            "feature_sha": feature_sha,
        }

    root = _ensure_baseline_path(M024_STAGE2_SYMBOL_DIR)
    root.mkdir(parents=True, exist_ok=True)

    def run_arm(label):
        existing = _m024_stage2_validate_artifacts(label)
        if existing is not None:
            return {
                "ok": True,
                "label": label,
                "reused_complete_artifacts": True,
                "run": None,
            }
        paths = _m024_stage2_paths(label)
        paths["dir"].mkdir(parents=True, exist_ok=True)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m024_symbol_causal_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output-dir",
                str(paths["dir"].relative_to(REPO)),
                "--arm",
                label,
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        return {
            "ok": run["exit_code"] == 0,
            "label": label,
            "reused_complete_artifacts": False,
            "run": run,
        }

    reference_run = run_arm("C-R")
    if not reference_run["ok"]:
        return {
            "ok": False,
            "reason": "M024 Stage-2 C-R execution failed",
            "feature_sha": feature_sha,
            "execution": {"C-R": reference_run},
        }

    try:
        reference = _m024_stage2_validate_artifacts("C-R")
        accepted_d_b = _m023_stage_a_validate_artifacts("D-B")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }
    if accepted_d_b is None:
        return {
            "ok": False,
            "reason": "accepted M023 D-B artifacts are missing",
            "feature_sha": feature_sha,
        }

    equivalence = _m024_stage2_reference_equivalence(
        reference,
        accepted_d_b,
    )
    if not equivalence["passes"]:
        return {
            "ok": False,
            "reason": "M024 Stage-2 C-R failed accepted D-B equivalence",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
        }

    candidate_run = run_arm("C-UJ")
    if not candidate_run["ok"]:
        return {
            "ok": False,
            "reason": "M024 Stage-2 C-UJ execution failed",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
            "execution": {
                "C-R": reference_run,
                "C-UJ": candidate_run,
            },
        }

    try:
        candidate = _m024_stage2_validate_artifacts("C-UJ")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    def compact(item):
        summary = item["summary"]
        return {
            "label": item["label"],
            "strategy_symbols": item["strategy_symbols"],
            "hashes": item["hashes"],
            "aggregate": summary.get("aggregate"),
            "per_symbol": summary.get("per_symbol"),
            "folds": summary.get("folds"),
            "iso_weeks": summary.get("iso_weeks"),
            "direction_invariants": summary.get("direction_invariants"),
            "symbol_invariants": summary.get("symbol_invariants"),
            "tp_safety": summary.get("tp_safety"),
            "remaining_positions": summary.get("remaining_positions"),
            "source_date_replay_hashes": summary.get(
                "source_date_replay_hashes"
            ),
            "checks": item["checks"],
        }

    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "family": "m024-stage2-symbol",
        "reference_equivalence": equivalence,
        "arms": {
            "C-R": compact(reference),
            "C-UJ": compact(candidate),
        },
        "execution": {
            "order": ["C-R", "C-UJ"],
            "runs": {
                "C-R": {
                    "reused_complete_artifacts":
                        reference_run["reused_complete_artifacts"],
                    "exit_code": (
                        None if reference_run["run"] is None
                        else reference_run["run"]["exit_code"]
                    ),
                },
                "C-UJ": {
                    "reused_complete_artifacts":
                        candidate_run["reused_complete_artifacts"],
                    "exit_code": (
                        None if candidate_run["run"] is None
                        else candidate_run["run"]["exit_code"]
                    ),
                },
            },
        },
        "safety": {
            "economic_replay_run": True,
            "economic_partition": "seen-research-only",
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
        },
    }


def m024_stage2_symbol_assessment():
    """Mechanically apply frozen C-UJ representation/support rules."""

    feature_sha = _require_m024_branch()
    try:
        reference = _m024_stage2_validate_artifacts("C-R")
        candidate = _m024_stage2_validate_artifacts("C-UJ")
        accepted_d_b = _m023_stage_a_validate_artifacts("D-B")
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }
    if reference is None or candidate is None or accepted_d_b is None:
        return {
            "ok": False,
            "reason": "M024 Stage-2 artifacts are incomplete",
            "feature_sha": feature_sha,
        }

    equivalence = _m024_stage2_reference_equivalence(
        reference,
        accepted_d_b,
    )
    if not equivalence["passes"]:
        return {
            "ok": False,
            "reason": "M024 Stage-2 C-R reference equivalence failed",
            "feature_sha": feature_sha,
            "reference_equivalence": equivalence,
        }

    summary = candidate["summary"]
    descriptive = accepted_d_b["summary"]
    aggregate = summary.get("aggregate") or {}
    per_symbol = summary.get("per_symbol") or {}
    usd = per_symbol.get("USDJPY") or {}
    closed = int(aggregate.get("closed_trades", 0))
    net_pl = float(aggregate.get("net_realized_pl", 0.0))
    mean_pl = (
        float(usd.get("mean_trade_pl"))
        if usd.get("mean_trade_pl") is not None
        else None
    )

    descriptive_usd = (descriptive.get("per_symbol") or {}).get("USDJPY") or {}
    descriptive_closed = int(descriptive_usd.get("closed_trades", 0))
    total_ratio = (
        closed / descriptive_closed if descriptive_closed else 0.0
    )

    candidate_folds = summary.get("folds") or {}
    descriptive_folds = descriptive.get("folds") or {}
    per_fold_ratio = {}
    positive_folds = {}
    for label in ("F1", "F2", "F3", "F4", "F5"):
        current = candidate_folds.get(label) or {}
        source = (
            (descriptive_folds.get(label) or {}).get("per_symbol") or {}
        ).get("USDJPY") or {}
        current_count = int(current.get("closed_trades", 0))
        source_count = int(source.get("closed_trades", 0))
        per_fold_ratio[label] = (
            current_count / source_count if source_count else 0.0
        )
        fold_pl = float(current.get("net_realized_pl", 0.0))
        fold_mean = current.get("mean_trade_pl")
        positive_folds[label] = {
            "closed_trades": current_count,
            "net_realized_pl": fold_pl,
            "mean_trade_pl": fold_mean,
            "net_positive": fold_pl > 0,
            "mean_positive": (
                fold_mean is not None and float(fold_mean) > 0
            ),
        }

    positive_fold_rows = [
        row for row in positive_folds.values()
        if row["net_positive"]
    ]
    positive_fold_sum = sum(
        row["net_realized_pl"] for row in positive_fold_rows
    )
    max_positive_fold_share = (
        max(row["net_realized_pl"] for row in positive_fold_rows)
        / positive_fold_sum
        if positive_fold_sum > 0
        else None
    )

    candidate_weeks = summary.get("iso_weeks") or {}
    descriptive_weeks = descriptive.get("iso_weeks") or {}
    source_trade_weeks = [
        label for label, row in descriptive_weeks.items()
        if int(((row.get("per_symbol") or {}).get("USDJPY") or {}).get(
            "closed_trades", 0
        )) > 0
    ]
    represented_weeks = [
        label for label in source_trade_weeks
        if int((candidate_weeks.get(label) or {}).get("closed_trades", 0)) > 0
    ]
    week_presence_ratio = (
        len(represented_weeks) / len(source_trade_weeks)
        if source_trade_weeks else 0.0
    )

    eligible_weeks = [
        row for row in candidate_weeks.values()
        if int(row.get("closed_trades", 0)) >= 5
    ]
    positive_mean_weeks = [
        row for row in eligible_weeks
        if row.get("mean_trade_pl") is not None
        and float(row["mean_trade_pl"]) > 0
    ]
    positive_mean_week_ratio = (
        len(positive_mean_weeks) / len(eligible_weeks)
        if eligible_weeks else 0.0
    )

    representation = {
        "total_ge_80pct_descriptive": total_ratio >= 0.80,
        "every_fold_ge_70pct_descriptive": all(
            ratio >= 0.70 for ratio in per_fold_ratio.values()
        ),
        "week_presence_ge_80pct": week_presence_ratio >= 0.80,
        "ok": (
            total_ratio >= 0.80
            and all(ratio >= 0.70 for ratio in per_fold_ratio.values())
            and week_presence_ratio >= 0.80
        ),
        "total_ratio": total_ratio,
        "per_fold_ratio": per_fold_ratio,
        "source_trade_weeks": len(source_trade_weeks),
        "represented_trade_weeks": len(represented_weeks),
        "week_presence_ratio": week_presence_ratio,
    }

    support_checks = {
        "net_pl_positive": net_pl > 0,
        "mean_trade_pl_positive": mean_pl is not None and mean_pl > 0,
        "positive_net_pl_folds_ge_3": sum(
            row["net_positive"] for row in positive_folds.values()
        ) >= 3,
        "positive_mean_folds_ge_3": sum(
            row["mean_positive"] for row in positive_folds.values()
        ) >= 3,
        "positive_fold_concentration_le_60pct": (
            max_positive_fold_share is not None
            and max_positive_fold_share <= 0.60
        ),
        "eligible_iso_weeks_ge_30": len(eligible_weeks) >= 30,
        "positive_mean_iso_weeks_ge_50pct": (
            positive_mean_week_ratio >= 0.50
        ),
    }
    supported = representation["ok"] and all(support_checks.values())
    classification = (
        "SUPPORTED FOR HOLDOUT CHECKPOINT ONLY"
        if supported
        else "NOT SUPPORTED"
    )

    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "reference": {
            "label": "C-R",
            "classification": "REFERENCE",
            "reference_equivalence": equivalence,
        },
        "candidate": {
            "label": "C-UJ",
            "classification": classification,
            "strategy_symbols": ["USDJPY"],
            "economics": {
                "closed_trades": closed,
                "net_realized_pl": net_pl,
                "mean_trade_pl": mean_pl,
                "maximum_equity_drawdown": aggregate.get(
                    "maximum_equity_drawdown"
                ),
                "maximum_equity_drawdown_pct": aggregate.get(
                    "maximum_equity_drawdown_pct"
                ),
                "win_rate_nonflat_pct": aggregate.get(
                    "win_rate_nonflat_pct"
                ),
            },
            "representation": representation,
            "support_checks": support_checks,
            "folds": positive_folds,
            "weekly": {
                "eligible_iso_weeks": len(eligible_weeks),
                "positive_mean_iso_weeks": len(positive_mean_weeks),
                "positive_mean_iso_week_ratio": positive_mean_week_ratio,
            },
            "max_positive_fold_pl_share": max_positive_fold_share,
        },
        "supported": supported,
        "historical_holdout_execution_authorized": False,
        "next_step": (
            "freeze separate prospective historical-holdout checkpoint"
            if supported
            else "close M024 without historical holdout"
        ),
        "safety": {
            "economic_replay_run": False,
            "reads_existing_stage2_artifacts_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_run": False,
            "weekday_filter_run": False,
        },
    }


def m024_holdout_readiness_tests():
    """Run only the non-economic M024 holdout-readiness tests."""

    feature_sha = _require_m024_branch()
    tests = [
        "tests/test_m024_holdout_readiness.py",
        "tests/test_m024_symbol_causal_research.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "economic_replay_run": False,
            "holdout_economics_computed": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def m024_holdout_readiness():
    """Publish deterministic metadata-only readiness for the frozen holdout."""

    feature_sha = _require_m024_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    if not manifest.is_file():
        return {
            "ok": False,
            "reason": "accepted M022 source manifest is missing",
            "feature_sha": feature_sha,
        }

    expected_manifest_sha = (
        "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
    )
    if _sha256(manifest) != expected_manifest_sha:
        return {
            "ok": False,
            "reason": "accepted M022 source manifest SHA changed",
            "feature_sha": feature_sha,
        }

    root = _ensure_baseline_path(M024_HOLDOUT_READINESS_DIR)
    root.mkdir(parents=True, exist_ok=True)
    output_a = root / "m024-holdout-readiness-a.json"
    output_b = root / "m024-holdout-readiness-b.json"

    exists = [output_a.is_file(), output_b.is_file()]
    if any(exists) and not all(exists):
        return {
            "ok": False,
            "reason": "partial immutable M024 holdout-readiness artifacts",
            "feature_sha": feature_sha,
        }

    def run_one(path):
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m024_holdout_readiness",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--output",
                str(path.relative_to(REPO)),
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return False, run
        if not path.is_file():
            return False, {
                **run,
                "stderr": run["stderr"] + "\nreadiness artifact missing",
            }
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return False, {
                **run,
                "stderr": run["stderr"] + f"\ninvalid readiness JSON: {exc}",
            }
        return True, run

    runs = []
    if not output_a.is_file():
        for path in (output_a, output_b):
            ok, run = run_one(path)
            runs.append(run)
            if not ok:
                return {
                    "ok": False,
                    "reason": "M024 holdout readiness build failed",
                    "feature_sha": feature_sha,
                    "run": run,
                }

    sha_a = _sha256(output_a)
    sha_b = _sha256(output_b)
    if sha_a != sha_b:
        return {
            "ok": False,
            "reason": "M024 holdout readiness is non-deterministic",
            "feature_sha": feature_sha,
            "artifact": {
                "a_sha256": sha_a,
                "b_sha256": sha_b,
            },
        }

    report = json.loads(output_a.read_text(encoding="utf-8"))
    partition = report.get("partition") or {}
    safety = report.get("safety") or {}
    blocks = partition.get("blocks") or []

    checks = {
        "readiness_only": report.get("readiness_only") is True,
        "economics_computed_false": report.get("economics_computed") is False,
        "ready": report.get("ready") is True,
        "source_manifest_sha": partition.get("source_manifest_sha256")
        == expected_manifest_sha,
        "start_utc": partition.get("start_utc")
        == "2026-07-08T00:00:00Z",
        "end_exclusive_utc": partition.get("end_exclusive_utc")
        == "2026-09-25T00:00:00Z",
        "trading_dates": int(partition.get("trading_dates", 0)) == 57,
        "block_count": len(blocks) == 3,
        "blocks_19_dates": all(
            int(block.get("trading_dates", 0)) == 19 for block in blocks
        ),
        "block_labels": [block.get("label") for block in blocks]
        == ["H1", "H2", "H3"],
        "date_sha_present": bool(partition.get("date_list_sha256")),
        "replay_sha_present": bool(partition.get("replay_boundary_sha256")),
        "partition_sha_present": bool(report.get("partition_spec_sha256")),
        "broker_not_constructed": safety.get("broker_constructed") is False,
        "strategy_not_constructed": safety.get("strategy_constructed") is False,
        "orders_not_constructed": safety.get("orders_constructed") is False,
        "trades_not_computed": safety.get("trades_computed") is False,
        "pl_not_computed": safety.get("pl_computed") is False,
        "drawdown_not_computed": safety.get("drawdown_computed") is False,
        "win_rate_not_computed": safety.get("win_rate_computed") is False,
        "m021_unused": safety.get("m021_post_cutoff_outcomes_used") is False,
        "m025_unused": safety.get("m025_outcomes_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        return {
            "ok": False,
            "reason": "M024 holdout readiness contract failed",
            "feature_sha": feature_sha,
            "failed_checks": failed,
            "artifact_sha256": sha_a,
        }

    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "checkpoint": "m024-historical-holdout-readiness",
        "artifact": {
            "a_path": str(output_a.relative_to(REPO)),
            "b_path": str(output_b.relative_to(REPO)),
            "a_sha256": sha_a,
            "b_sha256": sha_b,
            "deterministic": True,
        },
        "partition": partition,
        "partition_spec_sha256": report.get("partition_spec_sha256"),
        "row_counts": report.get("row_counts"),
        "checks": checks,
        "runs": runs,
        "safety": safety,
    }


def _m024_holdout_paths():
    root = M024_HOLDOUT_DIR
    return {
        "dir": root,
        "a_baseline": root / "M024-H-UJ-a-baseline.json",
        "b_baseline": root / "M024-H-UJ-b-baseline.json",
        "a_diagnostic": root / "M024-H-UJ-a-diagnostic.json",
        "b_diagnostic": root / "M024-H-UJ-b-diagnostic.json",
        "a_summary": root / "M024-H-UJ-a-summary.json",
        "b_summary": root / "M024-H-UJ-b-summary.json",
        "assessment": root / "M024-H-UJ-assessment.json",
    }


def _m024_validate_holdout_artifacts():
    paths = _m024_holdout_paths()
    required = [
        paths["a_baseline"],
        paths["b_baseline"],
        paths["a_diagnostic"],
        paths["b_diagnostic"],
        paths["a_summary"],
        paths["b_summary"],
    ]
    exists = [path.is_file() for path in required]
    if any(exists) and not all(exists):
        raise RuntimeError("M024 H-UJ has partial immutable artifacts")
    if not all(exists):
        return None

    hashes = {
        "baseline_a": _sha256(paths["a_baseline"]),
        "baseline_b": _sha256(paths["b_baseline"]),
        "diagnostic_a": _sha256(paths["a_diagnostic"]),
        "diagnostic_b": _sha256(paths["b_diagnostic"]),
        "summary_a": _sha256(paths["a_summary"]),
        "summary_b": _sha256(paths["b_summary"]),
    }
    deterministic = (
        hashes["baseline_a"] == hashes["baseline_b"]
        and hashes["diagnostic_a"] == hashes["diagnostic_b"]
        and hashes["summary_a"] == hashes["summary_b"]
    )
    summary = json.loads(paths["a_summary"].read_text(encoding="utf-8"))
    readiness = summary.get("readiness") or {}
    partition = summary.get("partition") or {}
    direction = summary.get("direction_invariants") or {}
    symbols = summary.get("symbol_invariants") or {}
    safety = summary.get("safety") or {}
    tp = summary.get("tp_safety") or {}

    expected_blocks = {
        "H1": "35cd428dd20dc965aa6e1479a28c73ad66329a1e64d188c1a6e16df25f7b260d",
        "H2": "eb2dfda09cf52320eeb83aac9175713fb45a8b32a330e5b29168f5cd1bc9ae19",
        "H3": "c57086b4e23affa9125f3ff4b4b9eb0352cf7bd5b45b45d7efdf865d984f9359",
    }
    expected_parameters = {
        "stochastic_k_period": 21,
        "stochastic_d_period": 7,
        "stochastic_slowing": 7,
        "oversold_level": 20.0,
        "overbought_level": 80.0,
        "ema_period": 7,
        "decision_spread_max_points": None,
        "atr_sl_multiplier": 1.5,
        "atr_tp_multiplier": 3.0,
        "block_00_04_utc": False,
    }
    checks = {
        "deterministic": deterministic,
        "candidate": summary.get("candidate") == "H-UJ",
        "strategy_symbols": summary.get("strategy_symbols") == ["USDJPY"],
        "market_symbols": summary.get("market_data_symbols")
        == ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"],
        "buy_only": summary.get("direction") == "BUY",
        "session_all_hours": summary.get("session") == "all-hours",
        "m15_disabled": summary.get("m15_signal_enabled") is False,
        "position_size": float(summary.get("position_size", 0.0)) == 0.1,
        "parameters": summary.get("parameters") == expected_parameters,
        "cost_contract": summary.get("cost_contract")
        == (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "partition_start": partition.get("start_utc")
        == "2026-07-08T00:00:00Z",
        "partition_end": partition.get("end_exclusive_utc")
        == "2026-09-25T00:00:00Z",
        "readiness_artifact": readiness.get("artifact_sha256")
        == "85852452d61db9447e8935ddc05e2f8e41889aa3ae168b3cc2a76ab26ceedb2e",
        "partition_spec": readiness.get("partition_spec_sha256")
        == "2fac9ab123f1ed173a51aab2cccb42368937e9373b4937a94fd421a89a49cb70",
        "date_sha": readiness.get("date_list_sha256")
        == "5d71d3ed67e5ae50f7e515f765e99a4887336e8a0d3659c62836d79dfe484af4"
        and partition.get("date_list_sha256")
        == "5d71d3ed67e5ae50f7e515f765e99a4887336e8a0d3659c62836d79dfe484af4",
        "replay_sha": readiness.get("replay_boundary_sha256")
        == "945c9961af7ce58e3b54223f0b8c10eb216e3dbfdf687ac002ef27b18197fab7"
        and partition.get("replay_boundary_sha256")
        == "945c9961af7ce58e3b54223f0b8c10eb216e3dbfdf687ac002ef27b18197fab7",
        "block_hashes": readiness.get("block_sha256") == expected_blocks,
        "trading_dates": int(partition.get("trading_dates", 0)) == 57,
        "sell_zero": int(direction.get("sell_accepted_entries", -1)) == 0,
        "excluded_symbol_rows_zero": int(
            symbols.get("excluded_symbol_closed_trade_rows", -1)
        ) == 0,
        "tp_wrong_side_zero": int(tp.get("wrong_side_initial_tp", -1)) == 0,
        "tp_negative_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "holdout_used": (
            safety.get("historical_holdout_economic_data_used") is True
        ),
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "m025_unused": safety.get("m025_outcomes_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "session_filter_absent": safety.get("session_filter_applied") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
        "market_data_not_reduced": (
            safety.get("market_data_universe_reduced") is False
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(
            f"M024 H-UJ failed frozen holdout invariants: {failed}"
        )
    return {
        "hashes": hashes,
        "summary": summary,
        "checks": checks,
    }


def m024_holdout_tests():
    """Run focused tests for the frozen one-shot H-UJ holdout."""

    feature_sha = _require_m024_branch()
    tests = [
        "tests/test_m024_holdout_readiness.py",
        "tests/test_m024_holdout_research.py",
        "tests/test_m024_symbol_causal_research.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "economic_replay_run": False,
            "holdout_economics_computed": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def m024_holdout_h_uj_pair():
    """Run the sole frozen H-UJ deterministic historical-holdout pair."""

    feature_sha = _require_m024_branch()
    manifest = M022_NATIVE_INVENTORY_MANIFEST
    readiness_a = (
        M024_HOLDOUT_READINESS_DIR / "m024-holdout-readiness-a.json"
    )
    readiness_b = (
        M024_HOLDOUT_READINESS_DIR / "m024-holdout-readiness-b.json"
    )
    expected_readiness_sha = (
        "85852452d61db9447e8935ddc05e2f8e41889aa3ae168b3cc2a76ab26ceedb2e"
    )

    if not manifest.is_file():
        return {"ok": False, "reason": "accepted source manifest missing"}
    if _sha256(manifest) != (
        "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
    ):
        return {"ok": False, "reason": "accepted source manifest SHA changed"}
    if not readiness_a.is_file() or not readiness_b.is_file():
        return {"ok": False, "reason": "accepted readiness pair is missing"}
    if (
        _sha256(readiness_a) != expected_readiness_sha
        or _sha256(readiness_b) != expected_readiness_sha
    ):
        return {"ok": False, "reason": "accepted readiness SHA changed"}

    existing = _m024_validate_holdout_artifacts()
    run = None
    if existing is None:
        paths = _m024_holdout_paths()
        paths["dir"].mkdir(parents=True, exist_ok=True)
        run = _run(
            _native_command(
                "-m",
                "mamba2.backtest.m024_holdout_research",
                "--manifest",
                str(manifest.relative_to(REPO)),
                "--readiness",
                str(readiness_a.relative_to(REPO)),
                "--output-dir",
                str(paths["dir"].relative_to(REPO)),
                "--starting-balance",
                "10000",
            ),
            env=_safe_env(),
        )
        if run["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M024 H-UJ holdout replay failed",
                "feature_sha": feature_sha,
                "run": run,
            }

    try:
        evidence = _m024_validate_holdout_artifacts()
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }

    summary = evidence["summary"]
    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "candidate": "H-UJ",
        "hashes": evidence["hashes"],
        "checks": evidence["checks"],
        "aggregate": summary.get("aggregate"),
        "blocks": summary.get("blocks"),
        "iso_weeks": summary.get("iso_weeks"),
        "trading_date_counts": summary.get("trading_date_counts"),
        "direction_invariants": summary.get("direction_invariants"),
        "symbol_invariants": summary.get("symbol_invariants"),
        "tp_safety": summary.get("tp_safety"),
        "remaining_positions": summary.get("remaining_positions"),
        "execution": {
            "reused_complete_artifacts": run is None,
            "exit_code": None if run is None else run["exit_code"],
        },
        "safety": summary.get("safety"),
    }


def m024_holdout_assessment():
    """Apply frozen one-shot H-UJ holdout classification rules."""

    feature_sha = _require_m024_branch()
    try:
        evidence = _m024_validate_holdout_artifacts()
    except RuntimeError as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "feature_sha": feature_sha,
        }
    if evidence is None:
        return {
            "ok": False,
            "reason": "M024 H-UJ holdout artifacts are incomplete",
            "feature_sha": feature_sha,
        }

    paths = _m024_holdout_paths()
    run = _run(
        _native_command(
            "-m",
            "mamba2.backtest.m024_holdout_assessment",
            "--summary",
            str(paths["a_summary"].relative_to(REPO)),
            "--output",
            str(paths["assessment"].relative_to(REPO)),
        ),
        env=_safe_env(),
    )
    if run["exit_code"] != 0 or not paths["assessment"].is_file():
        return {
            "ok": False,
            "reason": "M024 H-UJ mechanical assessment failed",
            "feature_sha": feature_sha,
            "run": run,
        }

    assessment = json.loads(
        paths["assessment"].read_text(encoding="utf-8")
    )
    allowed = {
        "INELIGIBLE — DATA/READINESS",
        "INELIGIBLE — NONDETERMINISTIC",
        "INELIGIBLE — INVARIANT FAILURE",
        "HOLDOUT NOT SUPPORTED",
        "HOLDOUT SUPPORTED — RESEARCH VALIDATION ONLY",
    }
    if assessment.get("classification") not in allowed:
        return {
            "ok": False,
            "reason": "unexpected M024 holdout classification",
            "feature_sha": feature_sha,
            "classification": assessment.get("classification"),
        }

    return {
        "ok": True,
        "feature_branch": "symbol-specialization-research",
        "feature_sha": feature_sha,
        "assessment_sha256": _sha256(paths["assessment"]),
        "assessment": assessment,
        "historical_holdout_execution_authorized": False,
        "production_live_promotion_authorized": False,
        "safety": {
            "economic_replay_run": False,
            "reads_existing_holdout_artifacts_only": True,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def m025_switch_public_benchmarks():
    """Switch clean Dell checkout to the exact M025 feature branch safely."""

    target = "public-strategy-benchmarks"
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if status["exit_code"] != 0 or status["stdout"].strip():
        return {
            "ok": False,
            "reason": "M025 branch switch refuses a dirty worktree",
        }

    fetch = _run([
        "git",
        "fetch",
        "origin",
        f"{target}:refs/remotes/origin/{target}",
    ])
    if fetch["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "could not fetch M025 remote branch",
            "run": fetch,
        }

    local_ref = _run(["git", "show-ref", "--verify", f"refs/heads/{target}"])
    if local_ref["exit_code"] == 0:
        switch = _run(["git", "switch", target])
    else:
        switch = _run([
            "git",
            "switch",
            "--track",
            "-c",
            target,
            f"origin/{target}",
        ])
    if switch["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "could not switch to M025 branch",
            "run": switch,
        }

    divergence = _run([
        "git",
        "rev-list",
        "--left-right",
        "--count",
        f"HEAD...refs/remotes/origin/{target}",
    ])
    if divergence["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "could not measure M025 divergence",
            "run": divergence,
        }
    left, right = [
        int(value)
        for value in divergence["stdout"].strip().split()
    ]
    if left > 0:
        return {
            "ok": False,
            "reason": "local M025 branch has unpushed/divergent commits",
            "divergence": {"ahead": left, "behind": right},
        }
    ff = None
    if right > 0:
        ff = _run([
            "git",
            "merge",
            "--ff-only",
            f"refs/remotes/origin/{target}",
        ])
        if ff["exit_code"] != 0:
            return {
                "ok": False,
                "reason": "M025 fast-forward failed",
                "run": ff,
            }

    feature_sha = _require_m025_branch()
    return {
        "ok": True,
        "feature_branch": target,
        "feature_sha": feature_sha,
        "divergence": {"ahead": 0, "behind": 0},
        "switch": switch,
        "fast_forward": ff,
        "safety": {
            "dirty_worktree_refused": True,
            "force_reset_used": False,
            "economic_replay_run": False,
            "real_order_api_called": False,
        },
    }


def m025_public_benchmark_tests():
    """Run M025 Stage-1 benchmark machinery tests only."""

    feature_sha = _require_m025_branch()
    tests = [
        "tests/test_public_benchmarks.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "stage1_only": True,
            "historical_economics_run": False,
            "m021_post_cutoff_data_used": False,
            "m023_outcomes_used": False,
            "m024_holdout_outcomes_used_for_definition": False,
            "real_order_api_called": False,
        },
    }


def m025_stage3_runtime_probe():
    """Probe only the fixed parser/converter capabilities needed by Stage 3."""

    import importlib.util

    feature_sha = _require_m025_branch()
    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "executables": {
            "libreoffice": shutil.which("libreoffice"),
            "soffice": shutil.which("soffice"),
            "ssconvert": shutil.which("ssconvert"),
        },
        "python_modules": {
            "openpyxl": importlib.util.find_spec("openpyxl") is not None,
            "xlrd": importlib.util.find_spec("xlrd") is not None,
        },
        "safety": {
            "download_run": False,
            "file_conversion_run": False,
            "economic_computation_run": False,
            "real_order_api_called": False,
        },
    }


def m025_stage3_ingestion_tests():
    """Run only M025 Stage-3 ingestion + accepted Stage-1 benchmark tests."""

    feature_sha = _require_m025_branch()
    tests = [
        "tests/test_m025_stage3_ingestion.py",
        "tests/test_public_benchmarks.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "download_run": False,
            "economic_computation_run": False,
            "m021_post_cutoff_data_used": False,
            "m023_outcomes_used": False,
            "m024_outcomes_used_to_tune_definitions": False,
            "real_order_api_called": False,
        },
    }


def m025_stage3_ingestion():
    """Run the fixed non-economic source/schema ingestion exactly once."""

    feature_sha = _require_m025_branch()
    libreoffice = shutil.which("libreoffice")
    if not libreoffice:
        return {
            "ok": False,
            "reason": "LibreOffice is unavailable for fixed LRV schema conversion",
            "feature_sha": feature_sha,
        }

    final_dir = _ensure_baseline_path(M025_STAGE3_INGESTION_DIR)
    report_path = final_dir / "m025-stage3-ingestion.json"

    if final_dir.exists():
        required = [
            report_path,
            final_dir / "h10-all-data.zip",
            final_dir / "h10-normalized-usd-per-foreign.csv",
            final_dir / "Time-Series-Momentum-Factors-Monthly.xlsx",
            final_dir / "CurrencyPortfolios.xls",
        ]
        if not all(path.is_file() for path in required):
            return {
                "ok": False,
                "reason": "partial immutable M025 Stage-3 ingestion artifacts",
                "feature_sha": feature_sha,
            }
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {
            "ok": True,
            "feature_branch": "public-strategy-benchmarks",
            "feature_sha": feature_sha,
            "reused_immutable_artifacts": True,
            "report_sha256": _sha256(report_path),
            "report": report,
            "safety": report.get("safety"),
        }

    temp_dir = _ensure_baseline_path(
        Path(str(final_dir) + ".tmp")
    )
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=False)

    run = _run_process_group_bounded(
        _native_command(
            "-m",
            "mamba2.backtest.m025_stage3_ingestion",
            "--output-dir",
            str(temp_dir.relative_to(REPO)),
            "--libreoffice",
            libreoffice,
        ),
        env=_safe_env(),
        timeout_seconds=300,
    )
    if run["exit_code"] != 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "ok": False,
            "reason": "M025 Stage-3 ingestion failed",
            "feature_sha": feature_sha,
            "run": run,
        }

    temp_report = temp_dir / "m025-stage3-ingestion.json"
    if not temp_report.is_file():
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "ok": False,
            "reason": "M025 Stage-3 ingestion report missing",
            "feature_sha": feature_sha,
        }

    report = json.loads(temp_report.read_text(encoding="utf-8"))
    safety = report.get("safety") or {}
    forbidden_true = [
        "returns_computed",
        "pl_computed",
        "sharpe_computed",
        "drawdown_computed",
        "correlation_computed",
        "tracking_error_computed",
        "economic_ranking_computed",
        "m021_post_cutoff_outcomes_used",
        "m023_outcomes_used",
        "m024_outcomes_used_to_tune_definitions",
        "real_order_api_called",
    ]
    failed_safety = [
        key for key in forbidden_true
        if safety.get(key) is not False
    ]
    if (
        report.get("economic_computation_performed") is not False
        or failed_safety
    ):
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "ok": False,
            "reason": "M025 Stage-3 non-economic safety contract failed",
            "feature_sha": feature_sha,
            "failed_safety": failed_safety,
        }

    h10 = ((report.get("sources") or {}).get("h10") or {})
    if len(h10.get("source_ids") or []) != 23:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "ok": False,
            "reason": "M025 H.10 23-series source contract failed",
            "feature_sha": feature_sha,
        }

    temp_dir.rename(final_dir)
    report_path = final_dir / "m025-stage3-ingestion.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "reused_immutable_artifacts": False,
        "report_sha256": _sha256(report_path),
        "h10": {
            "raw_sha256": report["sources"]["h10"]["raw_sha256"],
            "normalized_panel_sha256": report["sources"]["h10"][
                "normalized_panel_sha256"
            ],
            "gate_72_consecutive_months_all_series": report["sources"][
                "h10"
            ]["gate_72_consecutive_months_all_series"],
            "first_source_date": report["sources"]["h10"][
                "first_source_date"
            ],
            "last_source_date": report["sources"]["h10"][
                "last_source_date"
            ],
        },
        "aqr": {
            "raw_sha256": report["sources"]["aqr_tsmom"]["raw_sha256"],
            "sheet_names": report["sources"]["aqr_tsmom"]["schema"][
                "sheet_names"
            ],
            "currency_specific_schema_present": report["sources"][
                "aqr_tsmom"
            ]["schema"]["currency_specific_schema_present"],
            "currency_or_fx_schema_tokens": report["sources"][
                "aqr_tsmom"
            ]["schema"]["currency_or_fx_schema_tokens"],
        },
        "lrv": {
            "raw_sha256": report["sources"][
                "lrv_currency_portfolios"
            ]["raw_sha256"],
            "schema_method": report["sources"][
                "lrv_currency_portfolios"
            ]["schema"]["schema_method"],
            "schema_strings": report["sources"][
                "lrv_currency_portfolios"
            ]["schema"]["sheet_or_schema_strings"],
            "p1_through_p6_schema_present": report["sources"][
                "lrv_currency_portfolios"
            ]["schema"]["p1_through_p6_schema_present"],
            "hml_schema_present": report["sources"][
                "lrv_currency_portfolios"
            ]["schema"]["hml_schema_present"],
        },
        "safety": report.get("safety"),
        "run": run,
    }


def m025_stage3_h10_transport_probe():
    """Probe the fixed official H.10 all-data ZIP transport, schema only."""

    import io
    import urllib.request
    import xml.etree.ElementTree as ET
    import zipfile

    feature_sha = _require_m025_branch()
    url = (
        "https://www.federalreserve.gov/datadownload/"
        "Output.aspx?filetype=zip&rel=h10"
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Mamba2-Research-Ingestion/1.0"
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type")
    except Exception as exc:
        return {
            "ok": False,
            "feature_sha": feature_sha,
            "reason": f"H.10 ZIP transport failed: {exc}",
            "safety": {
                "observation_values_reported": False,
                "economic_computation_run": False,
                "real_order_api_called": False,
            },
        }

    if not body:
        return {
            "ok": False,
            "feature_sha": feature_sha,
            "reason": "H.10 ZIP transport returned an empty body",
            "status": status,
            "content_type": content_type,
            "safety": {
                "observation_values_reported": False,
                "economic_computation_run": False,
                "real_order_api_called": False,
            },
        }

    try:
        archive = zipfile.ZipFile(io.BytesIO(body), "r")
    except zipfile.BadZipFile as exc:
        return {
            "ok": False,
            "feature_sha": feature_sha,
            "reason": f"H.10 all-data body is not a ZIP: {exc}",
            "status": status,
            "content_type": content_type,
            "body_bytes": len(body),
            "safety": {
                "observation_values_reported": False,
                "economic_computation_run": False,
                "real_order_api_called": False,
            },
        }

    members = archive.namelist()
    xml_members = [
        name for name in members
        if name.lower().endswith(".xml")
    ]

    schema_shapes = {}
    for name in xml_members[:12]:
        tags = set()
        attribute_names = set()
        try:
            with archive.open(name) as handle:
                count = 0
                for event, elem in ET.iterparse(handle, events=("start",)):
                    tags.add(elem.tag.split("}")[-1])
                    attribute_names.update(elem.attrib.keys())
                    count += 1
                    if count >= 2000:
                        break
        except ET.ParseError:
            continue
        schema_shapes[name] = {
            "tags": sorted(tags),
            "attribute_names": sorted(attribute_names),
        }

    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "url": url,
        "status": status,
        "content_type": content_type,
        "body_bytes": len(body),
        "archive_members": members,
        "xml_members": xml_members,
        "schema_shapes": schema_shapes,
        "safety": {
            "observation_values_reported": False,
            "economic_computation_run": False,
            "m021_post_cutoff_data_used": False,
            "m023_outcomes_used": False,
            "m024_outcomes_used_to_tune_definitions": False,
            "real_order_api_called": False,
        },
    }


def m025_stage3_lrv_binary_probe():
    """Probe only the fixed LRV workbook transport/schema container."""

    feature_sha = _require_m025_branch()
    url = "https://web.mit.edu/adrienv/www/CurrencyPortfolios.xls"
    root = _ensure_baseline_path(
        REPO / "backtest_data" / "m025-stage3-lrv-binary-probe-v1"
    )
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=False)
    source = root / "CurrencyPortfolios.xls"
    converted = root / "converted"
    converted.mkdir()

    downloader = (
        "from pathlib import Path;"
        "from urllib.request import Request,urlopen;"
        f"u={url!r};p=Path({str(source)!r});"
        "r=Request(u,headers={'User-Agent':'Mozilla/5.0 Mamba2-Research-Ingestion/1.0'});"
        "d=urlopen(r,timeout=120).read();"
        "p.write_bytes(d);"
        "print(len(d))"
    )
    download = _run_process_group_bounded(
        _native_command("-c", downloader),
        env=_safe_env(),
        timeout_seconds=180,
    )
    if download["exit_code"] != 0 or not source.is_file():
        shutil.rmtree(root, ignore_errors=True)
        return {
            "ok": False,
            "reason": "fixed LRV binary probe download failed",
            "feature_sha": feature_sha,
            "run": download,
        }

    magic = source.read_bytes()[:8].hex().upper()
    file_cmd = shutil.which("file")
    strings_cmd = shutil.which("strings")
    file_result = (
        _run([file_cmd, "-b", str(source)])
        if file_cmd
        else {"exit_code": -1, "stdout": "", "stderr": "file unavailable"}
    )

    string_runs = []
    selected_strings = []
    if strings_cmd:
        for args in (
            [strings_cmd, "-a", "-n", "4", str(source)],
            [strings_cmd, "-a", "-e", "l", "-n", "4", str(source)],
        ):
            run = _run(args)
            string_runs.append(run)
            if run["exit_code"] == 0:
                for line in run["stdout"].splitlines():
                    clean = line.strip()
                    if not clean:
                        continue
                    lower = clean.lower()
                    if any(
                        token in lower
                        for token in (
                            "portfolio",
                            "currency",
                            "currencies",
                            "hml",
                            "dollar",
                            "developed",
                            "all countries",
                            "all currencies",
                        )
                    ):
                        selected_strings.append(clean[:300])

    libreoffice = shutil.which("libreoffice")
    conversion = None
    conversion_output = converted / "CurrencyPortfolios.xlsx"
    if libreoffice:
        conversion = _run_process_group_bounded(
            [
                libreoffice,
                "--headless",
                "--convert-to",
                "xlsx",
                '--infilter=MS Excel 97',
                "--outdir",
                str(converted.resolve()),
                str(source.resolve()),
            ],
            env=_safe_env(),
            timeout_seconds=120,
        )

    result = {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "url": url,
        "size_bytes": source.stat().st_size,
        "sha256": _sha256(source),
        "first_8_bytes_hex": magic,
        "ole_magic_matches": magic == "D0CF11E0A1B11AE1",
        "file_description": file_result["stdout"].strip(),
        "selected_schema_strings": sorted(set(selected_strings))[:200],
        "libreoffice_infilter_conversion": {
            "attempted": conversion is not None,
            "exit_code": None if conversion is None else conversion["exit_code"],
            "stdout": "" if conversion is None else conversion["stdout"],
            "stderr": "" if conversion is None else conversion["stderr"],
            "xlsx_created": conversion_output.is_file(),
        },
        "safety": {
            "numeric_cells_parsed": False,
            "returns_computed": False,
            "economic_computation_run": False,
            "real_order_api_called": False,
        },
    }
    shutil.rmtree(root, ignore_errors=True)
    return result


def m025_stage4_runtime_probe():
    """Probe only fixed XLS parsing capabilities for M025 Stage 4."""

    import importlib.util

    feature_sha = _require_m025_branch()
    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "executables": {
            "xls2csv": shutil.which("xls2csv"),
            "in2csv": shutil.which("in2csv"),
            "ssconvert": shutil.which("ssconvert"),
            "libreoffice": shutil.which("libreoffice"),
            "soffice": shutil.which("soffice"),
        },
        "python_modules": {
            "xlrd": importlib.util.find_spec("xlrd") is not None,
            "olefile": importlib.util.find_spec("olefile") is not None,
            "python_calamine": importlib.util.find_spec("python_calamine") is not None,
            "openpyxl": importlib.util.find_spec("openpyxl") is not None,
        },
        "safety": {
            "numeric_cells_parsed": False,
            "economic_computation_run": False,
            "real_order_api_called": False,
        },
    }


def m025_stage4_add_xlrd_dependency():
    """Add the fixed xlrd parser dependency and push only lock metadata."""

    feature_sha = _require_m025_branch()
    uv = shutil.which("uv") or "/home/joel/.local/bin/uv"
    if not Path(uv).is_file():
        return {
            "ok": False,
            "reason": "uv executable unavailable",
            "feature_sha": feature_sha,
        }

    before = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if before["exit_code"] != 0 or before["stdout"].strip():
        return {
            "ok": False,
            "reason": "dependency action refuses dirty worktree",
            "feature_sha": feature_sha,
        }

    add = _run_process_group_bounded(
        [uv, "add", "xlrd==2.0.2"],
        env=_safe_env(),
        timeout_seconds=180,
    )
    if add["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "uv add xlrd failed",
            "feature_sha": feature_sha,
            "run": add,
        }

    diff = _run(["git", "diff", "--name-only"])
    changed = sorted(
        line.strip()
        for line in diff["stdout"].splitlines()
        if line.strip()
    )
    if changed != ["pyproject.toml", "uv.lock"]:
        return {
            "ok": False,
            "reason": "unexpected dependency-action file changes",
            "feature_sha": feature_sha,
            "changed_files": changed,
        }

    verify = _run_process_group_bounded(
        [
            uv,
            "run",
            "--locked",
            "python",
            "-c",
            (
                "import xlrd;"
                "assert xlrd.__version__ == '2.0.2';"
                "print(xlrd.__version__)"
            ),
        ],
        env=_safe_env(),
        timeout_seconds=120,
    )
    if verify["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "locked xlrd verification failed",
            "feature_sha": feature_sha,
            "verify": verify,
        }

    add_git = _run(["git", "add", "pyproject.toml", "uv.lock"])
    if add_git["exit_code"] != 0:
        return {"ok": False, "reason": "git add failed"}

    commit = _run([
        "git",
        "commit",
        "-m",
        "build: add xlrd for M025 Stage-4 workbook parsing",
    ])
    if commit["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "dependency commit failed",
            "commit": commit,
        }

    new_sha = _run(["git", "rev-parse", "HEAD"])["stdout"].strip()
    push = _run([
        "git",
        "push",
        "origin",
        "HEAD:public-strategy-benchmarks",
    ])
    if push["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "dependency push failed",
            "new_sha": new_sha,
            "push": push,
        }

    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "previous_feature_sha": feature_sha,
        "new_feature_sha": new_sha,
        "changed_files": changed,
        "xlrd_version": "2.0.2",
        "uv_add": add,
        "verify": verify,
        "safety": {
            "economic_computation_run": False,
            "market_values_parsed": False,
            "real_order_api_called": False,
        },
    }


def m025_stage4_tests():
    """Run frozen M025 Stage-4 machinery tests only; no economics."""

    feature_sha = _require_m025_branch()
    tests = [
        "tests/test_m025_stage4_economics.py",
        "tests/test_m025_stage3_ingestion.py",
        "tests/test_public_benchmarks.py",
    ]
    result = _pytest_native(tests)
    return {
        "ok": result["exit_code"] == 0,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "tests": tests,
        "run": result,
        "safety": {
            "economic_execution_run": False,
            "stage4_artifacts_written": False,
            "m021_post_cutoff_data_used": False,
            "m023_outcomes_used": False,
            "m024_outcomes_used_to_tune_m025": False,
            "real_order_api_called": False,
        },
    }


def m025_stage4_economics():
    """Run the sole frozen M025 Stage-4 deterministic A/B economics."""

    feature_sha = _require_m025_branch()
    input_dir = _ensure_baseline_path(M025_STAGE3_INGESTION_DIR)
    output_dir = _ensure_baseline_path(M025_STAGE4_ECONOMICS_DIR)
    a_path = output_dir / "m025-stage4-a.json"
    b_path = output_dir / "m025-stage4-b.json"

    required_inputs = [
        input_dir / "m025-stage3-ingestion.json",
        input_dir / "h10-all-data.zip",
        input_dir / "h10-normalized-usd-per-foreign.csv",
        input_dir / "Time-Series-Momentum-Factors-Monthly.xlsx",
        input_dir / "CurrencyPortfolios.xls",
    ]
    if not all(path.is_file() for path in required_inputs):
        return {
            "ok": False,
            "reason": "accepted Stage-3 immutable inputs are missing",
            "feature_sha": feature_sha,
        }

    if output_dir.exists():
        if not a_path.is_file() or not b_path.is_file():
            return {
                "ok": False,
                "reason": "partial immutable M025 Stage-4 artifacts",
                "feature_sha": feature_sha,
            }
    else:
        temp_dir = _ensure_baseline_path(
            Path(str(output_dir) + ".tmp")
        )
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=False)

        code = (
            "import json;"
            "from mamba2.backtest.m025_stage4_economics import run_stage4_pair;"
            f"r=run_stage4_pair(ingestion_dir={str(input_dir)!r},"
            f"output_dir={str(temp_dir)!r});"
            "print(json.dumps(r,sort_keys=True));"
            "raise SystemExit(0 if r.get('ok') else 1)"
        )
        run = _run_process_group_bounded(
            _native_command("-c", code),
            env=_safe_env(),
            timeout_seconds=300,
        )
        if run["exit_code"] != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "ok": False,
                "reason": "M025 Stage-4 deterministic pair failed",
                "feature_sha": feature_sha,
                "run": run,
            }

        temp_a = temp_dir / "m025-stage4-a.json"
        temp_b = temp_dir / "m025-stage4-b.json"
        if not temp_a.is_file() or not temp_b.is_file():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "ok": False,
                "reason": "M025 Stage-4 A/B artifacts missing",
                "feature_sha": feature_sha,
            }
        if _sha256(temp_a) != _sha256(temp_b):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "ok": False,
                "reason": "M025 Stage-4 A/B artifacts are nondeterministic",
                "feature_sha": feature_sha,
            }
        temp_dir.rename(output_dir)

    sha_a = _sha256(a_path)
    sha_b = _sha256(b_path)
    if sha_a != sha_b:
        return {
            "ok": False,
            "reason": "M025 Stage-4 immutable A/B hashes differ",
            "feature_sha": feature_sha,
            "a_sha256": sha_a,
            "b_sha256": sha_b,
        }

    report = json.loads(a_path.read_text(encoding="utf-8"))
    if report.get("stage") != "stage4-economics":
        return {
            "ok": False,
            "reason": "unexpected M025 Stage-4 report stage",
            "feature_sha": feature_sha,
        }
    safety = report.get("safety") or {}
    forbidden_true = [
        "definitions_tuned_after_economics",
        "source_replaced_after_economics",
        "lag_search_run",
        "sign_search_run",
        "subperiod_search_run",
        "currency_subset_search_run",
        "m021_post_cutoff_outcomes_used",
        "m023_outcomes_used",
        "m024_outcomes_used_to_tune_m025",
        "real_order_api_called",
    ]
    failed_safety = [
        key for key in forbidden_true
        if safety.get(key) is not False
    ]
    if failed_safety:
        return {
            "ok": False,
            "reason": "M025 Stage-4 safety contract failed",
            "failed_safety": failed_safety,
            "feature_sha": feature_sha,
        }

    series = report["series"]
    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "artifact": {
            "a_path": str(a_path.relative_to(REPO)),
            "b_path": str(b_path.relative_to(REPO)),
            "a_sha256": sha_a,
            "b_sha256": sha_b,
            "deterministic": True,
        },
        "h10_spot_proxy": {
            "label": series["h10_spot_proxy"]["label"],
            "cost_label": series["h10_spot_proxy"]["cost_label"],
            "summary": series["h10_spot_proxy"]["summary"],
            "first_valid_instrument_count": (
                series["h10_spot_proxy"]["valid_instrument_count"][0]
                if series["h10_spot_proxy"]["valid_instrument_count"]
                else None
            ),
            "last_valid_instrument_count": (
                series["h10_spot_proxy"]["valid_instrument_count"][-1]
                if series["h10_spot_proxy"]["valid_instrument_count"]
                else None
            ),
        },
        "aqr_tsmom_fx": {
            "label": series["aqr_tsmom_fx"]["label"],
            "summary": series["aqr_tsmom_fx"]["summary"],
        },
        "lrv_hml_fx": {
            "label": series["lrv_hml_fx"]["label"],
            "summary": series["lrv_hml_fx"]["summary"],
            "parser_metadata": series["lrv_hml_fx"]["parser_metadata"],
        },
        "comparison": report["comparisons"]["h10_vs_aqr_tsmom_fx"],
        "safety": safety,
    }


def m025_stage4_aqr_date_probe():
    """Inspect only AQR TSMOM Factors date-column structure; no returns."""

    import re
    import zipfile
    import xml.etree.ElementTree as ET
    from datetime import datetime, timedelta

    feature_sha = _require_m025_branch()
    workbook = (
        M025_STAGE3_INGESTION_DIR
        / "Time-Series-Momentum-Factors-Monthly.xlsx"
    )
    if not workbook.is_file():
        return {"ok": False, "reason": "AQR workbook missing"}

    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    doc_rel_ns = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    )
    pkg_rel_ns = (
        "http://schemas.openxmlformats.org/package/2006/relationships"
    )

    with zipfile.ZipFile(workbook, "r") as archive:
        wb = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in rels.findall(f"{{{pkg_rel_ns}}}Relationship")
        }
        target = None
        for sheet in wb.findall(f".//{{{main_ns}}}sheet"):
            if sheet.attrib.get("name") == "TSMOM Factors":
                rel_id = sheet.attrib[f"{{{doc_rel_ns}}}id"]
                target = rel_map[rel_id].lstrip("/")
                break
        if target is None:
            return {"ok": False, "reason": "TSMOM Factors sheet missing"}
        if not target.startswith("xl/"):
            target = "xl/" + target

        workbook_pr = wb.find(f"{{{main_ns}}}workbookPr")
        date1904 = (
            workbook_pr is not None
            and workbook_pr.attrib.get("date1904", "0")
            in {"1", "true", "True"}
        )
        root = ET.fromstring(archive.read(target))
        date_rows = []
        for cell in root.findall(f".//{{{main_ns}}}c"):
            ref = cell.attrib.get("r", "")
            match = re.fullmatch(r"A(\d+)", ref)
            if not match or int(match.group(1)) <= 18:
                continue
            value_node = cell.find(f"{{{main_ns}}}v")
            if value_node is None or value_node.text is None:
                continue
            try:
                serial = float(value_node.text)
            except ValueError:
                continue
            base = (
                datetime(1904, 1, 1)
                if date1904
                else datetime(1899, 12, 30)
            )
            converted = base + timedelta(days=serial)
            month = converted.strftime("%Y-%m")
            date_rows.append({
                "row": int(match.group(1)),
                "serial": serial,
                "converted_date": converted.date().isoformat(),
                "month": month,
                "cell_type": cell.attrib.get("t"),
                "style": cell.attrib.get("s"),
            })

    by_month = {}
    for row in date_rows:
        by_month.setdefault(row["month"], []).append(row)
    duplicates = {
        month: rows
        for month, rows in by_month.items()
        if len(rows) > 1
    }

    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        "date1904": date1904,
        "date_rows_count": len(date_rows),
        "first_rows": date_rows[:8],
        "last_rows": date_rows[-8:],
        "duplicate_months": duplicates,
        "safety": {
            "aqr_return_values_read": False,
            "economic_summary_computed": False,
            "real_order_api_called": False,
        },
    }


def m025_stage4_lrv_unit_probe():
    """Inspect only LRV sheet labels/styles needed to prove return units."""

    feature_sha = _require_m025_branch()
    workbook = M025_STAGE3_INGESTION_DIR / "CurrencyPortfolios.xls"
    if not workbook.is_file():
        return {"ok": False, "reason": "LRV workbook missing"}

    code = r"""
import json
import xlrd
from mamba2.backtest.m025_stage4_economics import locate_lrv_layout

workbook = r"__WORKBOOK__"
book = xlrd.open_workbook(workbook, formatting_info=True, on_demand=False)
layout = locate_lrv_layout(book)
sheet = book.sheet_by_name(layout.sheet_name)

text_rows = []
for row in range(min(sheet.nrows, 100)):
    texts = []
    for col in range(sheet.ncols):
        cell = sheet.cell(row, col)
        if cell.ctype == xlrd.XL_CELL_TEXT:
            clean = " ".join(str(cell.value).split())
            if clean:
                texts.append({"col": col, "text": clean[:300]})
    if texts:
        text_rows.append({"row": row, "texts": texts})

format_counts = {}
sampled_cells = []
for row in range(layout.header_row + 1, sheet.nrows):
    for portfolio_number, col in enumerate(layout.portfolio_cols, start=1):
        cell = sheet.cell(row, col)
        if cell.ctype != xlrd.XL_CELL_NUMBER:
            continue
        xf_index = getattr(cell, "xf_index", None)
        format_code = None
        format_key = None
        if xf_index is not None and xf_index < len(book.xf_list):
            format_key = book.xf_list[xf_index].format_key
            fmt = book.format_map.get(format_key)
            format_code = None if fmt is None else fmt.format_str
        key = str(format_code)
        format_counts[key] = format_counts.get(key, 0) + 1
        if len(sampled_cells) < 24:
            sampled_cells.append({
                "row": row,
                "portfolio": portfolio_number,
                "col": col,
                "cell_type": cell.ctype,
                "xf_index": xf_index,
                "format_key": format_key,
                "format_code": format_code,
            })

print(json.dumps({
    "sheet_name": layout.sheet_name,
    "header_row_zero_based": layout.header_row,
    "date_col_zero_based": layout.date_col,
    "portfolio_cols_zero_based": list(layout.portfolio_cols),
    "hml_col_zero_based": layout.hml_col,
    "text_rows_first_100": text_rows,
    "portfolio_numeric_format_counts": format_counts,
    "sampled_portfolio_cell_metadata": sampled_cells,
}, sort_keys=True))
"""
    code = code.replace("__WORKBOOK__", str(workbook))
    run = _run_process_group_bounded(
        _native_command("-c", code),
        env=_safe_env(),
        timeout_seconds=120,
    )
    if run["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "LRV unit metadata probe failed",
            "feature_sha": feature_sha,
            "run": run,
        }
    try:
        metadata = json.loads(run["stdout"].strip())
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "reason": f"LRV unit metadata probe emitted invalid JSON: {exc}",
            "feature_sha": feature_sha,
        }
    return {
        "ok": True,
        "feature_branch": "public-strategy-benchmarks",
        "feature_sha": feature_sha,
        **metadata,
        "safety": {
            "numeric_values_reported": False,
            "returns_computed": False,
            "economic_summary_computed": False,
            "real_order_api_called": False,
        },
    }




def recovery_remove_accidental_systemctl_file():
    """Remove only the known accidental root-level systemctl-name artifact."""

    relative = "ystemctl --user start chatgpt-mamba2-local-agent.service"
    target = REPO / relative

    status_before = _run([
        "git", "status", "--porcelain=v1", "--untracked-files=all",
    ])
    if status_before["exit_code"] != 0:
        return {
            "ok": False,
            "reason": "could not inspect worktree before recovery cleanup",
            "status_before": status_before,
        }

    dirty_lines = [
        line for line in status_before["stdout"].splitlines()
        if line.strip()
    ]
    allowed_lines = {
        f'?? "{relative}"',
        f"?? {relative}",
    }
    if len(dirty_lines) != 1 or dirty_lines[0] not in allowed_lines:
        return {
            "ok": False,
            "reason": "recovery cleanup refuses any worktree state except the single known untracked artifact",
            "changed_paths": dirty_lines,
        }

    if not target.exists() and not target.is_symlink():
        return {
            "ok": False,
            "reason": "expected accidental artifact is no longer present",
            "relative_path": relative,
        }
    if target.is_dir() and not target.is_symlink():
        return {
            "ok": False,
            "reason": "recovery cleanup refuses to remove a directory",
            "relative_path": relative,
        }

    target.unlink()

    status_after = _run([
        "git", "status", "--porcelain=v1", "--untracked-files=all",
    ])
    clean = (
        status_after["exit_code"] == 0
        and not status_after["stdout"].strip()
    )
    return {
        "ok": clean,
        "relative_path": relative,
        "removed": True,
        "clean_after": clean,
        "status_after": status_after,
    }



ACTION_HANDLERS = {
    "recovery_remove_accidental_systemctl_file": recovery_remove_accidental_systemctl_file,
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
    "m025_stage3_h10_transport_probe": m025_stage3_h10_transport_probe,
    "m025_stage3_lrv_binary_probe": m025_stage3_lrv_binary_probe,
    "m025_stage4_lrv_unit_probe": m025_stage4_lrv_unit_probe,
    "m025_stage4_aqr_date_probe": m025_stage4_aqr_date_probe,
    "m025_stage4_economics": m025_stage4_economics,
    "m025_stage4_tests": m025_stage4_tests,
    "m025_stage4_add_xlrd_dependency": m025_stage4_add_xlrd_dependency,
    "m025_stage4_runtime_probe": m025_stage4_runtime_probe,
    "m025_stage3_ingestion_tests": m025_stage3_ingestion_tests,
    "m025_stage3_ingestion": m025_stage3_ingestion,
    "m025_stage3_runtime_probe": m025_stage3_runtime_probe,
    "m025_switch_public_benchmarks": m025_switch_public_benchmarks,
    "m025_public_benchmark_tests": m025_public_benchmark_tests,
    "m024_holdout_tests": m024_holdout_tests,
    "m024_holdout_h_uj_pair": m024_holdout_h_uj_pair,
    "m024_holdout_assessment": m024_holdout_assessment,
    "m024_holdout_readiness_tests": m024_holdout_readiness_tests,
    "m024_holdout_readiness": m024_holdout_readiness,
    "m024_stage2_symbol_tests": m024_stage2_symbol_tests,
    "m024_stage2_symbol_family": m024_stage2_symbol_family,
    "m024_stage2_symbol_assessment": m024_stage2_symbol_assessment,
    "m024_symbol_specialization_tests": m024_symbol_specialization_tests,
    "m024_symbol_specialization_diagnostic": m024_symbol_specialization_diagnostic,
    "m023_stage_b_session_family": m023_stage_b_session_family,
    "m023_stage_b_session_assessment": m023_stage_b_session_assessment,
    "m023_stage_a_direction_family": m023_stage_a_direction_family,
    "m023_stage_a_direction_assessment": m023_stage_a_direction_assessment,
    "m023_direction_session_review": m023_direction_session_review,
    "m023_direction_session_tests": m023_direction_session_tests,
    "m023_direction_session_diagnostic": m023_direction_session_diagnostic,
    "m022_phase2_validation_invariant_diagnostic": m022_phase2_validation_invariant_diagnostic,
    "m022_phase2_validation_assessment": m022_phase2_validation_assessment,
    "m022_phase2_validation_family": m022_phase2_validation_family,
    "m022_phase2_development_assessment": m022_phase2_development_assessment,
    "m022_phase2_development_family": m022_phase2_development_family,
    "m022_phase1_session_assessment": m022_phase1_session_assessment,
    "m022_phase1_session_family": m022_phase1_session_family,
    "m022_phase1_atr_tp_assessment": m022_phase1_atr_tp_assessment,
    "m022_phase1_atr_tp_family": m022_phase1_atr_tp_family,
    "m022_phase1_atr_sl_assessment": m022_phase1_atr_sl_assessment,
    "m022_phase1_atr_sl_family": m022_phase1_atr_sl_family,
    "m022_phase1_spread_assessment": m022_phase1_spread_assessment,
    "m022_phase1_spread_family": m022_phase1_spread_family,
    "m022_phase1_ema_assessment": m022_phase1_ema_assessment,
    "m022_phase1_ema_family": m022_phase1_ema_family,
    "m022_phase1_boundary_assessment": m022_phase1_boundary_assessment,
    "m022_phase1_boundary_family": m022_phase1_boundary_family,
    "m022_phase1_stochastic_assessment": m022_phase1_stochastic_assessment,
    "m022_phase1_stochastic_reference_equivalence": m022_phase1_stochastic_reference_equivalence,
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
