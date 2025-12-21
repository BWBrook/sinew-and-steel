from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sys
import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


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
                rel = characters_dir / candidate.name
            else:
                rel = characters_dir / f"{candidate.name}.yaml"
            if rel.exists():
                return rel

        raise FileNotFoundError(f"character not found: {character}")

    candidates = sorted(characters_dir.glob("*.yaml"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"no character sheets in {characters_dir}")

    names = ", ".join(p.name for p in candidates)
    raise FileNotFoundError(f"multiple character sheets in {characters_dir}: {names} (specify --character)")


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    def ok(self) -> bool:
        return not self.errors


def validate_double_debit(stats: dict[str, Any], baseline: int = 10) -> tuple[int, int, int, int]:
    increases = sum(max(0, int(v) - baseline) for v in stats.values())
    decreases = sum(max(0, baseline - int(v)) for v in stats.values())
    required_decreases = 2 * increases
    slack = decreases - required_decreases
    return increases, decreases, required_decreases, slack
