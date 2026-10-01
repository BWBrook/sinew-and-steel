from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import sys
import yaml

from _rules import (TAG_COST, REFUND_CAP, tag_cost,
                    validate_double_debit_mixed, build_points_needed_mixed)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def save_yaml(path: Path, data: dict) -> None:
    from _runtime import atomic_text
    atomic_text(path, yaml.safe_dump(data, sort_keys=False))


def load_manifest(root: Path | None = None) -> dict:
    root = root or repo_root()
    manifest_path = root / "manifest.yaml"
    try:
        return load_yaml(manifest_path)
    except FileNotFoundError:
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        raise


def campaign_dir(slug: str, root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "campaigns" / slug


def campaign_file(slug: str, root: Path | None = None) -> Path:
    return campaign_dir(slug, root=root) / "campaign.yaml"


def campaign_state_dir(slug: str, root: Path | None = None) -> Path:
    return campaign_dir(slug, root=root) / "state"


def campaign_characters_dir(slug: str, root: Path | None = None) -> Path:
    return campaign_state_dir(slug, root=root) / "characters"


def campaign_trackers_dir(slug: str, root: Path | None = None) -> Path:
    return campaign_state_dir(slug, root=root) / "trackers"


def campaign_memory_dir(slug: str, root: Path | None = None) -> Path:
    return campaign_state_dir(slug, root=root) / "memory"


def campaign_logs_dir(slug: str, root: Path | None = None) -> Path:
    return campaign_state_dir(slug, root=root) / "logs"


def resolve_character_file(characters_dir: Path, character: str | None) -> Path:
    if character:
        candidate = Path(character)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        if not candidate.is_absolute():
            # Allow passing "name.yaml" or "name".
            if candidate.suffix in (".yaml", ".yml"):
                matches = [characters_dir / candidate.name]
            else:
                matches = [characters_dir / f"{candidate.name}{suffix}" for suffix in (".yaml", ".yml")]
            matches = [path for path in matches if path.is_file()]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise ValueError(f"duplicate character filename stem: {candidate.name}")

        raise FileNotFoundError(f"character not found: {character}")

    candidates = sorted(p for p in characters_dir.iterdir() if p.is_file() and p.suffix in {".yaml", ".yml"})
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"no character sheets in {characters_dir}")

    names = ", ".join(p.name for p in candidates)
    raise FileNotFoundError(f"multiple character sheets in {characters_dir}: {names} (specify --character)")


def repo_version(root: Path | None = None) -> str:
    root = root or repo_root()
    version_path = root / "VERSION"
    if not version_path.exists():
        return "unknown"
    return version_path.read_text(encoding="utf-8").strip() or "unknown"


def slugify(text: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text or "").strip("_").lower()
    return slug or fallback


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    def ok(self) -> bool:
        return not self.errors


ALLOWED_CLOCK_FIELDS = {"name", "current", "max", "notes"}


def _split_path(path: str) -> list[str]:
    if not path:
        raise KeyError("empty path")
    return path.split(".")


def _traverse_existing(data: dict, keys: list[str]) -> dict | None:
    cur = data
    for key in keys[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            return None
        cur = cur[key]
    return cur


def _ensure_parent(data: dict, keys: list[str]) -> tuple[dict, str]:
    cur = data
    for key in keys[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    return cur, keys[-1]


def _is_clock_path(keys: list[str]) -> bool:
    return len(keys) >= 2 and keys[0] == "clocks"


def _ensure_clock(data: dict, name: str) -> dict:
    clocks = data.get("clocks")
    if clocks is None:
        clocks = {}
        data["clocks"] = clocks
    if not isinstance(clocks, dict):
        raise TypeError("clocks is not a dict")
    clock = clocks.get(name)
    if not isinstance(clock, dict):
        clock = {}
        clocks[name] = clock
    clock.setdefault("name", name)
    clock.setdefault("current", 0)
    clock.setdefault("max", 5)
    return clock


def set_path(data: dict, path: str, value, *, allow_new: bool = False, allow_clock: bool = False) -> None:
    keys = _split_path(path)
    if allow_new:
        parent, key = _ensure_parent(data, keys)
        parent[key] = value
        return

    if allow_clock and _is_clock_path(keys):
        if len(keys) == 2:
            clocks = data.get("clocks")
            if clocks is None:
                clocks = {}
                data["clocks"] = clocks
            if not isinstance(clocks, dict):
                raise TypeError("clocks is not a dict")
            clocks[keys[1]] = value
            return

        clock = _ensure_clock(data, keys[1])
        parent = clock
        for key in keys[2:-1]:
            if key not in parent or not isinstance(parent[key], dict):
                raise KeyError(f"Missing key '{path}'")
            parent = parent[key]
        final = keys[-1]
        if final not in parent and final not in ALLOWED_CLOCK_FIELDS:
            raise KeyError(f"Missing key '{path}'")
        parent[final] = value
        return

    parent = _traverse_existing(data, keys)
    if parent is None or keys[-1] not in parent:
        raise KeyError(f"Missing key '{path}'")
    parent[keys[-1]] = value


def inc_path(data: dict, path: str, delta: int, *, allow_new: bool = False, allow_clock: bool = False) -> None:
    keys = _split_path(path)
    if allow_new:
        parent, key = _ensure_parent(data, keys)
    elif allow_clock and _is_clock_path(keys):
        if len(keys) == 2:
            raise KeyError(f"Missing key '{path}'")
        clock = _ensure_clock(data, keys[1])
        parent = clock
        for key in keys[2:-1]:
            if key not in parent or not isinstance(parent[key], dict):
                raise KeyError(f"Missing key '{path}'")
            parent = parent[key]
        key = keys[-1]
        if key not in parent and key not in ALLOWED_CLOCK_FIELDS:
            raise KeyError(f"Missing key '{path}'")
        if key not in parent:
            parent[key] = 0
    else:
        parent = _traverse_existing(data, keys)
        if parent is None or keys[-1] not in parent:
            raise KeyError(f"Missing key '{path}'")
        key = keys[-1]

    if key not in parent:
        raise KeyError(f"Missing key '{path}'")
    if not isinstance(parent[key], (int, float)):
        raise TypeError(f"Value at '{path}' is not numeric")
    parent[key] += delta


def _get_dict_at_path(data: dict, path: str) -> dict | None:
    keys = _split_path(path)
    cur = data
    for key in keys:
        if key not in cur or not isinstance(cur[key], dict):
            return None
        cur = cur[key]
    return cur


def clamp_currents(data: dict, paths: list[str]) -> None:
    for path in paths:
        if not path.endswith(".current"):
            continue
        parent_path = path.rsplit(".", 1)[0]
        parent = _get_dict_at_path(data, parent_path)
        if not isinstance(parent, dict):
            continue
        cur = parent.get("current")
        max_value = parent.get("max")
        if not isinstance(cur, int) or not isinstance(max_value, int):
            continue
        if cur < 0:
            parent["current"] = 0
        elif cur > max_value:
            parent["current"] = max_value
