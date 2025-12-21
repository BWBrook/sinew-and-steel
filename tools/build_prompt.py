#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: missing file: {path}", file=sys.stderr)
        sys.exit(1)


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.yaml"
    try:
        return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        sys.exit(1)


def list_skins(manifest: dict) -> None:
    skins = manifest.get("skins", {})
    for slug in sorted(skins.keys()):
        name = skins[slug].get("name", slug)
        print(f"{slug}: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a full starter prompt from rules + skin.")
    parser.add_argument("--skin", help="Skin slug from manifest.yaml")
    parser.add_argument("--template", help="Prompt template path", default=None)
    parser.add_argument("--hidden", help="Optional hidden scenario file", default=None)
    parser.add_argument("--out", help="Output file path (default: stdout)")
    parser.add_argument("--list-skins", action="store_true", help="List available skins")

    args = parser.parse_args()
    manifest = load_manifest()

    if args.list_skins:
        list_skins(manifest)
        return 0

    if not args.skin:
        print("error: --skin is required (use --list-skins to see options)", file=sys.stderr)
        return 1

    skins = manifest.get("skins", {})
    if args.skin not in skins:
        print(f"error: unknown skin '{args.skin}'", file=sys.stderr)
        return 1

    rules = manifest.get("rules", {})
    core = rules.get("core", {})
    adv_path = ROOT / core.get("adventurers_manual", "")
    cust_path = ROOT / core.get("custodians_almanac", "")

    skin_entry = skins[args.skin]
    skin_path = ROOT / skin_entry.get("file", "")

    prompts = manifest.get("prompts", {})
    default_template = ROOT / prompts.get("starter", "prompts/starter_prompt.md")
    template_path = Path(args.template) if args.template else default_template
    if not template_path.is_absolute():
        template_path = ROOT / template_path

    template = load_text(template_path)
    adv_text = load_text(adv_path)
    cust_text = load_text(cust_path)
    skin_text = load_text(skin_path)

    hidden_text = "[No hidden scenario provided.]"
    if args.hidden:
        hidden_path = Path(args.hidden)
        if not hidden_path.is_absolute():
            hidden_path = ROOT / hidden_path
        hidden_text = load_text(hidden_path)

    replacements = {
        "{{CORE_RULES_ADVENTURERS}}": adv_text.strip(),
        "{{CORE_RULES_CUSTODIANS}}": cust_text.strip(),
        "{{SKIN_TEXT}}": skin_text.strip(),
        "{{HIDDEN_SCENARIO}}": hidden_text.strip(),
        "{{SKIN_NAME}}": skin_entry.get("name", args.skin),
    }

    output = template
    for key, value in replacements.items():
        output = output.replace(key, value + "\n")

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
