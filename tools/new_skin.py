#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def slug_to_name(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("-", " ").replace("_", " ").split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new skin from templates/skin_template.md")
    parser.add_argument("--slug", required=True, help="Skin slug (filename without .md)")
    parser.add_argument("--name", help="Display name (defaults from slug)")
    parser.add_argument("--register", action="store_true", help="Register in manifest.yaml", default=True)
    parser.add_argument("--no-register", action="store_false", dest="register")

    args = parser.parse_args()
    slug = args.slug.strip()
    name = args.name or slug_to_name(slug)

    template_path = ROOT / "templates/skin_template.md"
    if not template_path.exists():
        print(f"error: missing template: {template_path}", file=sys.stderr)
        return 1

    skin_path = ROOT / "skins" / f"{slug}.md"
    if skin_path.exists():
        print(f"error: skin already exists: {skin_path}", file=sys.stderr)
        return 1

    template = template_path.read_text(encoding="utf-8")
    content = template.replace("SKIN NAME", name)
    skin_path.write_text(content, encoding="utf-8")

    if args.register:
        manifest_path = ROOT / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        skins = manifest.setdefault("skins", {})
        if slug in skins:
            print(f"warning: manifest already contains skin '{slug}'", file=sys.stderr)
        else:
            skins[slug] = {
                "name": name,
                "file": f"skins/{slug}.md",
                "pressure_track": "Pressure",
            }
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"created {skin_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
