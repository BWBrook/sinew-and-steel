#!/usr/bin/env python3
"""Prepare a complete campaign before writing any of its files."""
import argparse
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import random
import re
import sys
import tempfile

import yaml

import _pressure
import _resources
import _sslib
import gen_character

ROOT = Path(__file__).resolve().parents[1]


def build_scaffold(manifest: dict, *, skin_slug: str, slug: str, title: str,
                   budget: int = 6, names: list[str] | None = None, seed: int | None = None,
                   tags: list[str] | None = None, free_tags: list[dict] | None = None,
                   existing_actors: list[str] | None = None) -> dict[str, dict]:
    skin = manifest["skins"][skin_slug]
    characters = {}
    old_random = random.getstate()
    try:
        if seed is not None:
            random.seed(seed)
        for name in names or []:
            actor = _sslib.slugify(name, fallback="character")
            if actor in characters:
                raise ValueError(f"character names resolve to the same filename: {actor}")
            kwargs = {"tags": tags or []}
            if free_tags:
                kwargs["free_tags"] = free_tags
            characters[actor] = gen_character.build_sheet(
                {**skin, "slug": skin_slug, "_gen": {**skin.get("_gen", {}), "build_points_budget": budget}},
                name, "", **kwargs,
            )
            if seed is not None:
                characters[actor].setdefault("meta", {}).setdefault("generated", {})["seed"] = seed
    finally:
        random.setstate(old_random)

    actors = sorted(set(existing_actors or []) | set(characters))
    campaign = {"schema_version": 2, "slug": slug, "title": title, "skin": skin_slug,
                "created": date.today().isoformat(), "build_points_budget": budget,
                "prompt_profile": "compact", "notes": ""}
    tracker = {"schema_version": 2, "name": "Session Tracker", "scene": 0, "session": 1,
               "beat": 0, "pending_action": None, "npcs": {}, "combat": {}, "session_closed": False,
               "pressure": _pressure.new_pressure(skin, actors),
               "resources": _resources.new_resources(skin, actors),
               "clocks": deepcopy(skin.get("clocks", {})), "notes": []}
    memory_path = ROOT / "state" / "memory" / "seed_memory.yaml"
    memory = _sslib.load_yaml(memory_path) if memory_path.exists() else {
        "schema_version": 1, "summary": [], "threads": [], "npcs": [], "secrets": []}
    files = {"campaign.yaml": campaign, "state/trackers/session.yaml": tracker,
             "state/memory/session_001.yaml": memory}
    files.update({f"state/characters/{actor}.yaml": sheet for actor, sheet in characters.items()})
    return files


def _write_private(path: Path, text: str) -> None:
    # Owner-only from the first write, like every later campaign transaction.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)


def write_scaffold(campaign_dir: Path, files: dict[str, dict]) -> list[str]:
    """New campaigns appear atomically; existing files are never overwritten."""
    directories = ("state/characters", "state/trackers", "state/memory", "state/logs", "state/checkpoints")
    campaign_dir.parent.mkdir(parents=True, exist_ok=True)
    if not campaign_dir.exists():
        with tempfile.TemporaryDirectory(prefix=f".{campaign_dir.name}_", dir=campaign_dir.parent) as temp:
            stage = Path(temp) / "campaign"
            for relative in directories:
                (stage / relative).mkdir(parents=True, exist_ok=True)
            for relative, data in files.items():
                _write_private(stage / relative, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
            # Readers share this lock with writers; it exists from the start.
            _write_private(stage / "state/.runtime.lock", "")
            os.rename(stage, campaign_dir)
        return list(files)
    written = []
    for relative in directories:
        (campaign_dir / relative).mkdir(parents=True, exist_ok=True)
    if not (campaign_dir / "state/.runtime.lock").exists():
        _write_private(campaign_dir / "state/.runtime.lock", "")
    for relative, data in files.items():
        path = campaign_dir / relative
        # Exclusive creation keeps preservation true even if another process writes first.
        try:
            _write_private(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        except FileExistsError:
            continue
        written.append(relative)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a campaign with structured Pressure and resource state.")
    parser.add_argument("--slug", help="Campaign folder name")
    parser.add_argument("--title", help="Campaign title; also derives a slug")
    parser.add_argument("--skin", required=True)
    parser.add_argument("--build-points", type=int)
    parser.add_argument("--tone", choices=["grim", "standard", "pulp", "heroic"])
    parser.add_argument("--base-dir", default="campaigns")
    parser.add_argument("--force", action="store_true", help="Fill missing scaffold files; preserve every existing file")
    parser.add_argument("--random-character", action="append", default=[], help="Generate a named character; repeat for a party")
    parser.add_argument("--seed", type=int, help="Reproducible character generation")
    parser.add_argument("--tag", action="append", default=[], help="Bought tag for each generated character")
    parser.add_argument("--free-tag", action="append", default=[], help="Skin grant as GRANT=NAME for each character")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        manifest = _sslib.load_manifest(ROOT)
        if args.skin not in manifest.get("skins", {}):
            raise ValueError(f"unknown skin '{args.skin}'")
        if not args.slug and not args.title:
            raise ValueError("provide --slug or --title")
        if args.tone and args.build_points is not None:
            raise ValueError("provide only one of --tone or --build-points")
        budget = {"grim": 0, "standard": 6, "pulp": 12, "heroic": 16}[args.tone] if args.tone else (
            6 if args.build_points is None else args.build_points)
        if budget < 0:
            raise ValueError("--build-points must be >= 0")
        slug = args.slug or _sslib.slugify(args.title, fallback="campaign")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", slug):
            raise ValueError("slug must contain only letters, digits, underscores, and hyphens")
        base = Path(args.base_dir)
        campaign_dir = (base if base.is_absolute() else ROOT / base) / slug
        if campaign_dir.exists() and not args.force:
            raise ValueError(f"campaign directory already exists: {campaign_dir}")
        cfile = campaign_dir / "campaign.yaml"
        if cfile.exists():
            saved = _sslib.load_yaml(cfile)
            if saved.get("skin") != args.skin or saved.get("build_points_budget", 6) != budget:
                raise ValueError("existing campaign skin/budget differs; --force only fills missing files")
        free_tags = []
        for raw in args.free_tag:
            grant, separator, name = raw.partition("=")
            if not separator or not grant.strip() or not name.strip():
                raise ValueError("--free-tag must be GRANT=NAME")
            free_tags.append({"grant": grant.strip(), "name": name.strip()})
        existing = sorted(p.stem for p in (campaign_dir / "state/characters").glob("*.y*ml"))
        if (campaign_dir / "state/trackers/session.yaml").exists():
            additions = {_sslib.slugify(name, fallback="character") for name in args.random_character} - set(existing)
            if additions:
                raise ValueError("add characters with gen_character.py --campaign so their roster bookkeeping updates; --force preserves existing state")
        files = build_scaffold(manifest, skin_slug=args.skin, slug=slug, title=args.title or slug,
                               budget=budget, names=args.random_character, seed=args.seed,
                               tags=args.tag, free_tags=free_tags, existing_actors=existing)
        preserved = sorted(relative for relative in files if (campaign_dir / relative).exists())
        writes = {relative: data for relative, data in files.items() if relative not in preserved}
        payload = {"ok": True, "campaign": {"slug": slug, "title": args.title or slug,
                    "skin": args.skin, "build_points_budget": budget, "dir": str(campaign_dir)},
                   "files": writes, "preserved": preserved, "seed": args.seed, "dry_run": args.dry_run}
        if not args.dry_run:
            payload["written"] = write_scaffold(campaign_dir, writes)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"{'dry-run: would initialize' if args.dry_run else 'initialized'} {campaign_dir}")
            if preserved:
                print(f"preserved {len(preserved)} existing files")
        return 0
    except (ValueError, RuntimeError, OSError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
