"""Security contract for local runtime cache persistence."""

import json

import pytest

from mamba2.crew.cache_manager import CacheManager


FORBIDDEN_KEY = "last_account_info"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_stale_account_info_is_scrubbed_on_construction(tmp_path):
    cache_path = tmp_path / "bot_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                FORBIDDEN_KEY: {
                    "synthetic_sensitive_marker": "must-not-survive",
                },
                "last_broker_type": "real",
            }
        ),
        encoding="utf-8",
    )

    manager = CacheManager(str(cache_path))

    assert FORBIDDEN_KEY not in manager.cache
    assert manager.get(FORBIDDEN_KEY) is None
    assert manager.get("last_broker_type") == "real"

    persisted = read_json(cache_path)
    assert persisted == {"last_broker_type": "real"}
    assert "must-not-survive" not in cache_path.read_text(encoding="utf-8")


def test_constructor_rewrites_stale_file_before_any_later_save(tmp_path):
    cache_path = tmp_path / "bot_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                FORBIDDEN_KEY: {"synthetic": "remove-now"},
                "safe": 7,
            }
        ),
        encoding="utf-8",
    )

    CacheManager(str(cache_path))

    assert read_json(cache_path) == {"safe": 7}


def test_save_cache_scrubs_forbidden_key_if_memory_is_mutated(tmp_path):
    cache_path = tmp_path / "bot_cache.json"
    manager = CacheManager(str(cache_path))
    manager.cache["safe"] = {"nested": True}
    manager.cache[FORBIDDEN_KEY] = {
        "synthetic_sensitive_marker": "must-not-persist",
    }

    manager.save_cache()

    assert FORBIDDEN_KEY not in manager.cache
    assert read_json(cache_path) == {"safe": {"nested": True}}
    assert "must-not-persist" not in cache_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("save", [False, True])
def test_set_rejects_forbidden_account_info_key(tmp_path, save):
    cache_path = tmp_path / "bot_cache.json"
    manager = CacheManager(str(cache_path))
    manager.set("safe", "preserve", save=True)

    with pytest.raises(ValueError, match="forbidden key"):
        manager.set(
            FORBIDDEN_KEY,
            {"synthetic_sensitive_marker": "must-not-persist"},
            save=save,
        )

    assert FORBIDDEN_KEY not in manager.cache
    assert manager.get("safe") == "preserve"
    assert read_json(cache_path) == {"safe": "preserve"}
    assert "must-not-persist" not in cache_path.read_text(encoding="utf-8")


def test_benign_keys_survive_load_and_save(tmp_path):
    cache_path = tmp_path / "bot_cache.json"
    original = {
        "last_broker_type": "mock",
        "safe_nested": {"enabled": True, "count": 3},
        "safe_list": ["a", "b"],
    }
    cache_path.write_text(json.dumps(original), encoding="utf-8")

    manager = CacheManager(str(cache_path))
    manager.save_cache()

    assert manager.cache == original
    assert read_json(cache_path) == original


def test_missing_cache_file_behavior_is_unchanged(tmp_path):
    cache_path = tmp_path / "missing.json"

    manager = CacheManager(str(cache_path))

    assert manager.cache == {}
    assert not cache_path.exists()


def test_invalid_json_behavior_is_unchanged(tmp_path, capsys):
    cache_path = tmp_path / "invalid.json"
    cache_path.write_text("{not-json", encoding="utf-8")

    manager = CacheManager(str(cache_path))

    assert manager.cache == {}
    assert cache_path.read_text(encoding="utf-8") == "{not-json"
    assert "Warning: Failed to load cache" in capsys.readouterr().out


def test_forbidden_value_is_never_emitted_to_stdout(tmp_path, capsys):
    cache_path = tmp_path / "bot_cache.json"
    marker = "synthetic-do-not-print"
    cache_path.write_text(
        json.dumps({FORBIDDEN_KEY: {"marker": marker}}),
        encoding="utf-8",
    )

    CacheManager(str(cache_path))

    assert marker not in capsys.readouterr().out
