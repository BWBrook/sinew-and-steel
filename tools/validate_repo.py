#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PLACEHOLDERS = [
    "{{CORE_RULES_ADVENTURERS}}",
    "{{CORE_RULES_CUSTODIANS}}",
    "{{SKIN_TEXT}}",
    "{{HIDDEN_SCENARIO}}",
]


def main() -> int:
    errors = []
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("missing manifest.yaml")
        return report(errors)

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    # Check rules
    rules = manifest.get("rules", {})
    core = rules.get("core", {})
    for key in ("adventurers_manual", "custodians_almanac"):
        rel = core.get(key)
        if not rel:
            errors.append(f"manifest missing rules.core.{key}")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"missing file: {rel}")

    quickstart = rules.get("quickstart")
    if quickstart and not (ROOT / quickstart).exists():
        errors.append(f"missing file: {quickstart}")

    # Check skins
    skin_dir = ROOT / "skins"
    skin_files = {p.stem for p in skin_dir.glob("*.md")}
    manifest_skins = set(manifest.get("skins", {}).keys())

    missing_in_manifest = skin_files - manifest_skins
    missing_on_disk = manifest_skins - skin_files

    for slug in sorted(missing_in_manifest):
        errors.append(f"skin not in manifest: {slug}")
    for slug in sorted(missing_on_disk):
        errors.append(f"skin missing on disk: {slug}")

    # Check prompt template placeholders
    starter_path = ROOT / manifest.get("prompts", {}).get("starter", "prompts/starter_prompt.md")
    if starter_path.exists():
        content = starter_path.read_text(encoding="utf-8")
        for placeholder in REQUIRED_PLACEHOLDERS:
            if placeholder not in content:
                errors.append(f"starter prompt missing placeholder: {placeholder}")
    else:
        errors.append(f"missing file: {starter_path}")

    # Check templates
    templates = manifest.get("templates", {})
    for key, rel in templates.items():
        if not (ROOT / rel).exists():
            errors.append(f"missing template ({key}): {rel}")

    return report(errors)


def report(errors):
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
