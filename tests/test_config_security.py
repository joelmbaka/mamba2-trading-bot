"""Security regression tests for the real MT5 runtime configuration.

The general test suite installs a mocked config module in tests/conftest.py.
These tests intentionally load the repository real config.py by file path so
the security contract is exercised rather than the suite-wide mock.
"""

import importlib.util
from pathlib import Path
import sys


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.py"


def load_real_config():
    module_name = "_mamba2_real_config_security"
    spec = importlib.util.spec_from_file_location(module_name, CONFIG_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load real config module from {CONFIG_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


def test_mt5_config_has_no_source_default_credentials(monkeypatch):
    # Empty values suppress any developer .env values while still exercising
    # the production environment parsing code.
    for name in (
        "MAMBA_MT5_LOGIN",
        "MAMBA_MT5_PASSWORD",
        "MAMBA_MT5_SERVER",
        "MAMBA_MT5_PATH",
    ):
        monkeypatch.setenv(name, "")

    config_module = load_real_config()
    cfg = config_module.MT5Config()

    assert cfg.login is None
    assert cfg.password == ""
    assert cfg.server == ""
    assert cfg.path == ""


def test_mt5_config_reads_explicit_environment(monkeypatch):
    monkeypatch.setenv("MAMBA_MT5_LOGIN", "123456")
    monkeypatch.setenv("MAMBA_MT5_PASSWORD", "placeholder-secret")
    monkeypatch.setenv("MAMBA_MT5_SERVER", "Example-Demo")
    monkeypatch.setenv("MAMBA_MT5_PATH", r"C:\\Example\\terminal64.exe")
    monkeypatch.setenv("MAMBA_MT5_TIMEOUT", "45000")
    monkeypatch.setenv("MAMBA_MT5_PORTABLE", "true")

    config_module = load_real_config()
    cfg = config_module.MT5Config()

    assert cfg.login == 123456
    assert cfg.password == "placeholder-secret"
    assert cfg.server == "Example-Demo"
    assert cfg.path == r"C:\\Example\\terminal64.exe"
    assert cfg.timeout == 45000
    assert cfg.portable is True
