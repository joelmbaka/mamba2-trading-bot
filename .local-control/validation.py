#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
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
M017_DIAGNOSTIC_A = FIRST_BASELINE_DIR / "diagnostic-a.json"
M017_DIAGNOSTIC_B = FIRST_BASELINE_DIR / "diagnostic-b.json"
M017_BASELINE_A = FIRST_BASELINE_DIR / "diagnostic-baseline-a.json"
M017_BASELINE_B = FIRST_BASELINE_DIR / "diagnostic-baseline-b.json"
M018_DIAGNOSTIC_A = FIRST_BASELINE_DIR / "m018-diagnostic-a.json"
M018_DIAGNOSTIC_B = FIRST_BASELINE_DIR / "m018-diagnostic-b.json"
M018_BASELINE_A = FIRST_BASELINE_DIR / "m018-baseline-a.json"
M018_BASELINE_B = FIRST_BASELINE_DIR / "m018-baseline-b.json"

M019_FROM_UTC = "2026-06-01T00:00:00Z"
M019_TO_UTC = "2026-09-25T00:00:00Z"
M019_DIR = REPO / "backtest_data" / "broader-history-20260601-20260925"
M019_MANIFEST = M019_DIR / "manifest.json"
M019_DIAGNOSTIC_A = M019_DIR / "m019-diagnostic-a.json"
M019_DIAGNOSTIC_B = M019_DIR / "m019-diagnostic-b.json"
M019_BASELINE_A = M019_DIR / "m019-baseline-a.json"
M019_BASELINE_B = M019_DIR / "m019-baseline-b.json"
M019_SYMBOLS = list(FIRST_BASELINE_SYMBOLS)
M019_TICK_CHECKPOINTS = [
    "2026-06-01T12:00:00Z",
    "2026-06-15T12:00:00Z",
    "2026-07-15T12:00:00Z",
    "2026-08-17T12:00:00Z",
    "2026-09-01T12:00:00Z",
    "2026-09-24T12:00:00Z",
]


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
    return _run(
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
start = datetime.fromisoformat("2026-06-01T00:00:00+00:00")
end = datetime.fromisoformat("2026-09-25T00:00:00+00:00")
checkpoints = [
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    for value in [
        "2026-06-01T12:00:00Z",
        "2026-06-15T12:00:00Z",
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
            rates = mt5.copy_rates_range(symbol, timeframe, start, end)
            if rates is None or len(rates) == 0:
                bars[label] = {"rows": 0, "first": None, "last": None}
                continue
            bars[label] = {
                "rows": int(len(rates)),
                "first": datetime.fromtimestamp(
                    int(rates[0]["time"]), timezone.utc
                ).isoformat().replace("+00:00", "Z"),
                "last": datetime.fromtimestamp(
                    int(rates[-1]["time"]), timezone.utc
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
        "from_utc": "2026-06-01T00:00:00Z",
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
    bars_ok = all(
        symbol_data.get(symbol, {}).get("bars", {}).get(timeframe, {}).get(
            "rows", 0
        ) > 0
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

broader = load_mt5_dataset(Path("backtest_data/broader-history-20260601-20260925/manifest.json"))
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


def execute(action):
    handlers = {
        "repo_checks": repo_checks,
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
        "broader_history_run_pair": broader_history_run_pair,
    }
    try:
        return handlers[action]()
    except KeyError as exc:
        raise ValueError(f"unsupported validation action: {action!r}") from exc
