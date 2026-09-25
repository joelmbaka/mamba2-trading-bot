#!/usr/bin/env python3
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

    branch = commands[1]["stdout"].strip()
    divergence = None
    if branch:
        remote = _run(["git", "rev-parse", "--verify", f"refs/remotes/origin/{branch}"])
        commands.append(remote)
        if remote["exit_code"] == 0:
            divergence_cmd = _run(
                ["git", "rev-list", "--left-right", "--count", f"HEAD...origin/{branch}"]
            )
            commands.append(divergence_cmd)
            divergence = divergence_cmd["stdout"].strip()

    clean = commands[2]["stdout"].strip() == ""
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


def execute(action):
    handlers = {
        "repo_checks": repo_checks,
        "bootstrap_wine_test_env": bootstrap_wine_test_env,
        "runtime_discovery": runtime_discovery,
        "runtime_versions": runtime_versions,
        "test_core": test_core,
        "test_full_native": test_full_native,
        "test_full_wine": test_full_wine,
    }
    try:
        return handlers[action]()
    except KeyError as exc:
        raise ValueError(f"unsupported validation action: {action!r}") from exc
