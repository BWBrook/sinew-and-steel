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
    atomic_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


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
        if candidate.is_absolute():
            if candidate.exists() and candidate.resolve().is_relative_to(characters_dir.resolve()):
                return candidate
            raise ValueError(f"character path must be inside {characters_dir}")
        if not candidate.is_absolute():
            # Allow passing "name.yaml" or "name".
            if candidate.suffix in (".yaml", ".yml"):
                matches = [characters_dir / candidate.name]
            else:
                matches = [characters_dir / f"{candidate.name}{suffix}" for suffix in (".yaml", ".yml")]
            matches = [path for path in matches if path.is_file()]
            if not matches and characters_dir.is_dir():
                # Case-insensitive on every filesystem, not only on macOS.
                stem = Path(candidate.name).stem.casefold()
                matches = [path for path in characters_dir.iterdir()
                           if path.suffix in (".yaml", ".yml") and path.stem.casefold() == stem]
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
