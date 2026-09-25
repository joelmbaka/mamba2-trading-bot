#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(os.environ["LOCAL_PROJECT_DIR"]).resolve()
WINEPREFIX = Path.home() / ".mamba2-mt5"
NATIVE_PYTHON = REPO / ".venv-linux-backtest" / "bin" / "python"
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


def _require_native_python():
    if not NATIVE_PYTHON.is_file():
        raise RuntimeError(
            f"accepted native environment is missing: {NATIVE_PYTHON}"
        )


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

    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    if not Path(uv).is_file():
        raise RuntimeError("uv is not available")
    commands.append(_run([uv, "lock", "--check"]))

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


def runtime_versions():
    _require_native_python()
    wine = _wine()

    native = _run([
        str(NATIVE_PYTHON),
        "-c",
        (
            "import json,platform,numpy;"
            "print(json.dumps({'python':platform.python_version(),"
            "'machine':platform.machine(),'numpy':numpy.__version__}))"
        ),
    ], env=_safe_env())

    wine_result = _run([
        wine,
        WINE_PYTHON,
        "-c",
        (
            "import json,platform,numpy,MetaTrader5 as mt5;"
            "print(json.dumps({'python':platform.python_version(),"
            "'machine':platform.machine(),'numpy':numpy.__version__,"
            "'metatrader5':mt5.__version__}))"
        ),
    ], env=_safe_env(wine=True))

    return {
        "ok": native["exit_code"] == 0 and wine_result["exit_code"] == 0,
        "native": native,
        "wine": wine_result,
    }


def _pytest_native(paths=None):
    _require_native_python()
    cmd = [str(NATIVE_PYTHON), "-m", "pytest"]
    if paths:
        cmd.extend(paths)
    return _run(cmd, env=_safe_env())


def _pytest_wine():
    wine = _wine()
    return _run(
        [wine, WINE_PYTHON, "-m", "pytest"],
        env=_safe_env(wine=True),
    )


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
        "runtime_versions": runtime_versions,
        "test_core": test_core,
        "test_full_native": test_full_native,
        "test_full_wine": test_full_wine,
    }
    try:
        return handlers[action]()
    except KeyError as exc:
        raise ValueError(f"unsupported validation action: {action!r}") from exc
