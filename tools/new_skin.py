#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTRS = [
    ("MGT", "Might"),
    ("REF", "Reflex"),
    ("INT", "Intellect"),
    ("EMP", "Empathy"),
    ("LCK", "Luck"),
]


def slug_to_name(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("-", " ").replace("_", " ").split())


def parse_attr(item: str) -> tuple[str, str]:
    if "=" not in item:
        raise ValueError(f"Expected KEY=Label, got '{item}'")
    key, label = item.split("=", 1)
    key = key.strip()
    label = label.strip()
    if not key:
        raise ValueError(f"Invalid attribute key in '{item}'")
    if not label:
        label = key
    return key, label


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new skin from templates/skin_template.md")
    parser.add_argument("--slug", required=True, help="Skin slug (filename without .md)")
    parser.add_argument("--name", help="Display name (defaults from slug)")
    parser.add_argument("--register", action="store_true", help="Register in manifest.yaml", default=True)
    parser.add_argument("--no-register", action="store_false", dest="register")
    parser.add_argument(
        "--attr",
        action="append",
        default=[],
        help="Attribute mapping KEY=Label (repeat 5 times). Default: MGT/REF/INT/EMP/LCK.",
    )
    parser.add_argument("--luck-key", help="Luck attribute key (defaults to last attribute)")
    parser.add_argument("--luck-name", help="Luck pool display name (defaults from luck key label)")
    parser.add_argument("--pressure-track", help="Pressure track name (default: Pressure)")

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
            if args.attr:
                try:
                    attrs = [parse_attr(item) for item in args.attr]
                except ValueError as exc:
                    print(f"error: {exc}", file=sys.stderr)
                    return 1
                if len(attrs) != 5:
                    print("error: provide exactly 5 --attr entries", file=sys.stderr)
                    return 1
                keys = [key for key, _ in attrs]
                if len(set(keys)) != 5:
                    print("error: attribute keys must be unique", file=sys.stderr)
                    return 1
                attr_dict = {key: label for key, label in attrs}
            else:
                attr_dict = {key: label for key, label in DEFAULT_ATTRS}

            luck_key = args.luck_key or (list(attr_dict.keys())[-1] if attr_dict else "LCK")
            if luck_key not in attr_dict:
                print(f"error: luck key '{luck_key}' not found in attributes", file=sys.stderr)
                return 1
            luck_name = args.luck_name or attr_dict.get(luck_key, "Luck")
            pressure_track = args.pressure_track or "Pressure"
            skins[slug] = {
                "name": name,
                "file": f"skins/{slug}.md",
                "pressure_track": pressure_track,
                "attributes": attr_dict,
                "luck_key": luck_key,
                "luck_name": luck_name,
            }
            manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    print(f"created {skin_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
