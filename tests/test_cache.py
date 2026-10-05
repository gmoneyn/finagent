import json
import time
from pathlib import Path

from finagent.cache import FileCache


def test_cache_set_and_get(tmp_path):
    cache = FileCache(cache_dir=tmp_path)
    cache.set("test_key", {"price": 150.0})
    result = cache.get("test_key")
    assert result == {"price": 150.0}


def test_cache_miss_returns_none(tmp_path):
    cache = FileCache(cache_dir=tmp_path)
    result = cache.get("nonexistent")
    assert result is None


def test_cache_expiry(tmp_path):
    cache = FileCache(cache_dir=tmp_path)
    cache.set("expiring", {"data": 1}, ttl_seconds=1)
    assert cache.get("expiring") == {"data": 1}
    time.sleep(1.1)
    assert cache.get("expiring") is None


def test_cache_no_expiry(tmp_path):
    cache = FileCache(cache_dir=tmp_path)
    cache.set("permanent", {"data": 1}, ttl_seconds=None)
    result = cache.get("permanent")
    assert result == {"data": 1}


def test_cache_files_are_readable_json(tmp_path):
    cache = FileCache(cache_dir=tmp_path)
    cache.set("readable", {"ticker": "AAPL", "price": 150.0})
    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) == 1
    with open(cache_files[0]) as f:
        data = json.load(f)
    assert data["value"]["ticker"] == "AAPL"
