#!/usr/bin/env python3
"""
apply_trim_suggestions.py

Apply trim hints from `assets/trim_suggestions.yaml` to markdown image tags.

Why:
- Spot art often includes generous whitespace. When wrapped, that whitespace
  increases wrap height and causes ugly page breaks.
- Trimming keeps the images visually crisp without destructively cropping the
  source PNGs.

Scope:
- This is a maintainer workflow tool. It edits markdown files in-place.
- It does *not* require Pillow; it consumes the YAML output of
  `tools/suggest_trim.py`.

Examples:
  # Apply to the release-visible rules + skins.
  python tools/apply_trim_suggestions.py

  # Dry-run preview (no writes), print JSON summary:
  python tools/apply_trim_suggestions.py --dry-run --json

  # Apply to specific files:
  python tools/apply_trim_suggestions.py rules/quickstart.md skins/clanfire.md

  # Apply to a directory:
  python tools/apply_trim_suggestions.py --dir rules/core --dir skins
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


MD_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\("
    r"(?P<path><[^>]+>|[^)\s]+)"
    r"(?P<title>\s+\"[^\"]*\")?"
    r"\)"
    r"(?P<space>\s*)"
    r"(?P<attrs>\{[^}]*\})?"
)


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def iter_markdown_files(*, explicit: list[str], dirs: list[str]) -> list[Path]:
    results: list[Path] = []

    for raw in explicit:
        p = Path(raw)
        if not p.is_absolute():
            p = (ROOT / p).resolve()
        if not p.exists():
            raise FileNotFoundError(f"missing file: {raw}")
        results.append(p)

    for raw_dir in dirs:
        d = Path(raw_dir)
        if not d.is_absolute():
            d = (ROOT / d).resolve()
        if not d.exists() or not d.is_dir():
            raise FileNotFoundError(f"missing dir: {raw_dir}")
        results.extend(sorted(d.rglob("*.md")))

    # Default scope: rules quickstart + core + skins.
    if not results:
        results.extend([ROOT / "rules" / "quickstart.md"])
        results.extend(sorted((ROOT / "rules" / "core").rglob("*.md")))
        results.extend(sorted((ROOT / "skins").rglob("*.md")))

    # Deduplicate and keep stable ordering.
    uniq: dict[str, Path] = {}
    for p in results:
        uniq[str(p)] = p
    return list(uniq.values())


def resolve_image_path(*, md_path: Path, raw: str) -> Path | None:
    if raw.startswith(("http://", "https://", "data:")):
        return None
    if raw.startswith("#"):
        return None

    # Remove angle brackets if present.
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1]

    # Drop fragment.
    path_part = raw.split("#", 1)[0]

    # Support repo-root-style paths like `/assets/...`.
    if path_part.startswith("/"):
        candidate = (ROOT / path_part.lstrip("/")).resolve()
    else:
        candidate = (md_path.parent / path_part).resolve()

    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def upsert_trim(*, attrs: str | None, trim: str) -> str:
    trim_attr = f'trim="{trim}"'

    if not attrs:
        return "{" + trim_attr + "}"

    inner = attrs[1:-1]

    # Replace existing trim attr if present (quoted or bare).
    #
    # Note: this is intentionally *one* replacement, because chained substitutions
    # can partially match the new quoted value (e.g. `trim="1bp 2bp 3bp 4bp"`)
    # and leave trailing tokens behind.
    if re.search(r"\btrim\s*=", inner):
        inner = re.sub(
            r'\btrim\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s}]+)',
            trim_attr,
            inner,
            count=1,
        )

        # Cleanup: remove any stray unit tokens that may be left behind from a
        # previous buggy replacement, e.g.:
        #   trim="1bp 2bp 3bp 4bp" 2bp 3bp 4bp"
        inner = re.sub(
            r'(trim="[^"]*")(?:(?:\s+\d+(?:\.\d+)?(?:bp|in|pt|cm|mm)\"?)){1,6}',
            r"\1",
            inner,
        )

        return "{" + inner + "}"

    # Insert before close brace, with a spacer if needed.
    spacer = "" if inner.endswith((" ", "\n", "\t")) or inner == "" else " "
    return "{" + inner + spacer + trim_attr + "}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply trim suggestions to markdown image tags.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown file paths (repo-relative or absolute). If omitted, defaults to rules/quickstart.md + rules/core/*.md + skins/*.md.",
    )
    parser.add_argument(
        "--dir",
        action="append",
        default=[],
        help="Directory to scan for markdown files (can be repeated).",
    )
    parser.add_argument(
        "--suggestions",
        default="assets/trim_suggestions.yaml",
        help="Trim suggestions YAML (default: assets/trim_suggestions.yaml).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; only report what would change.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary (default: human text).")
    args = parser.parse_args()

    suggestions_path = Path(args.suggestions)
    if not suggestions_path.is_absolute():
        suggestions_path = (ROOT / suggestions_path).resolve()
    if not suggestions_path.exists():
        print(f"error: missing suggestions file: {suggestions_path}", file=sys.stderr)
        return 2

    suggestions_yaml = load_yaml(suggestions_path)
    suggestions_list = suggestions_yaml.get("suggestions", [])
    by_file: dict[str, str] = {}
    for entry in suggestions_list:
        if not isinstance(entry, dict):
            continue
        file_rel = entry.get("file")
        trim = entry.get("trim_bp")
        if isinstance(file_rel, str) and isinstance(trim, str):
            by_file[file_rel] = trim

    md_files = iter_markdown_files(explicit=args.paths, dirs=args.dir)

    changed_files: list[str] = []
    updated_images = 0
    skipped_images = 0

    per_file: dict[str, dict] = {}

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        original = text

        file_updates = 0

        def repl(match: re.Match) -> str:
            nonlocal updated_images, skipped_images, file_updates

            raw_path = match.group("path")
            resolved = resolve_image_path(md_path=md_path, raw=raw_path)
            if not resolved:
                skipped_images += 1
                return match.group(0)

            rel = resolved.relative_to(ROOT).as_posix()
            trim = by_file.get(rel)
            if not trim:
                skipped_images += 1
                return match.group(0)

            new_attrs = upsert_trim(attrs=match.group("attrs"), trim=trim)
            updated_images += 1
            file_updates += 1

            # Preserve any whitespace between ) and { ... }
            space = match.group("space") or ""
            title = match.group("title") or ""
            alt = match.group("alt") or ""

            return f"![{alt}]({raw_path}{title}){space}{new_attrs}"

        text = MD_IMAGE_RE.sub(repl, text)

        if text != original:
            per_file[md_path.relative_to(ROOT).as_posix()] = {"images_updated": file_updates}
            changed_files.append(md_path.relative_to(ROOT).as_posix())
            if not args.dry_run:
                md_path.write_text(text, encoding="utf-8")

    summary = {
        "suggestions_file": suggestions_path.relative_to(ROOT).as_posix(),
        "files_considered": len(md_files),
        "files_changed": len(changed_files),
        "images_updated": updated_images,
        "images_skipped": skipped_images,
        "changed_files": changed_files,
        "per_file": per_file,
    }

    if args.json:
        sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    else:
        print(f"ok: applied trim suggestions from {summary['suggestions_file']}")
        print(f"files changed: {summary['files_changed']} / {summary['files_considered']}")
        print(f"images updated: {summary['images_updated']} (skipped: {summary['images_skipped']})")
        if changed_files:
            print("changed files:")
            for f in changed_files:
                print(f"  - {f} ({per_file.get(f, {}).get('images_updated', 0)} images)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
