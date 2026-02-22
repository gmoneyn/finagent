"""File-based JSON cache. Human-readable, debuggable."""

import hashlib
import json
import time
from pathlib import Path


class FileCache:
    """Simple file-based cache storing JSON files.

    Cache files are human-readable for easy debugging.
    Each entry stores: value, created_at, ttl_seconds.
    """

    def __init__(self, cache_dir: Path | str | None = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".finagent" / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        safe_name = hashlib.sha256(key.encode()).hexdigest()[:16]
        readable = key.replace("/", "_").replace(":", "_")[:40]
        return self.cache_dir / f"{readable}_{safe_name}.json"

    def get(self, key: str) -> dict | list | None:
        path = self._key_to_path(key)
        if not path.exists():
            return None

        with open(path) as f:
            entry = json.load(f)

        ttl = entry.get("ttl_seconds")
        if ttl is not None:
            elapsed = time.time() - entry["created_at"]
            if elapsed > ttl:
                path.unlink(missing_ok=True)
                return None

        return entry["value"]

    def set(self, key: str, value: dict | list, ttl_seconds: int | None = 3600) -> None:
        entry = {
            "key": key,
            "value": value,
            "created_at": time.time(),
            "ttl_seconds": ttl_seconds,
        }
        path = self._key_to_path(key)
        with open(path, "w") as f:
            json.dump(entry, f, indent=2, default=str)
