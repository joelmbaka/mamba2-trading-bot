"""Security regression tests for MT5 runtime configuration."""

from config import MT5Config


def test_mt5_config_has_no_source_default_credentials(monkeypatch):
    for name in (
        "MAMBA_MT5_LOGIN",
        "MAMBA_MT5_PASSWORD",
        "MAMBA_MT5_SERVER",
        "MAMBA_MT5_PATH",
    ):
        monkeypatch.delenv(name, raising=False)

    cfg = MT5Config()

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

    cfg = MT5Config()

    assert cfg.login == 123456
    assert cfg.password == "placeholder-secret"
    assert cfg.server == "Example-Demo"
    assert cfg.path == r"C:\Example\terminal64.exe"
    assert cfg.timeout == 45000
    assert cfg.portable is True
