#!/usr/bin/env python3
import argparse
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


def check_prompt_template(path: Path, label: str, errors: list[str]) -> None:
    if path.exists():
        content = path.read_text(encoding="utf-8")
        for placeholder in REQUIRED_PLACEHOLDERS:
            if placeholder not in content:
                errors.append(f"{label} missing placeholder: {placeholder}")
    else:
        errors.append(f"missing file: {path}")


def collect_errors() -> list[str]:
    errors: list[str] = []
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("missing manifest.yaml")
        return errors

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
    skins_block = manifest.get("skins", {})
    manifest_skins = set(skins_block.keys())
    manifest_addon_slugs = set()
    for skin_entry in skins_block.values():
        for rel in skin_entry.get("addons", []) or []:
            manifest_addon_slugs.add(Path(rel).stem)

    missing_in_manifest = skin_files - manifest_skins - manifest_addon_slugs
    missing_on_disk = manifest_skins - skin_files

    for slug in sorted(missing_in_manifest):
        errors.append(f"skin not in manifest: {slug}")
    for slug in sorted(missing_on_disk):
        errors.append(f"skin missing on disk: {slug}")

    # Check prompt template placeholders
    prompts = manifest.get("prompts", {})
    agent_path = ROOT / prompts.get("agent_starter", prompts.get("starter", "prompts/agent/starter_prompt.md"))
    chat_path = ROOT / prompts.get("chat_starter", "prompts/chat/starter_prompt.md")
    check_prompt_template(agent_path, "agent starter prompt", errors)
    if prompts.get("chat_starter"):
        check_prompt_template(chat_path, "chat starter prompt", errors)

    # Check templates
    templates = manifest.get("templates", {})
    for key, rel in templates.items():
        if not (ROOT / rel).exists():
            errors.append(f"missing template ({key}): {rel}")

    # Check Python environment files
    for rel in ("pyproject.toml", "uv.lock"):
        if not (ROOT / rel).exists():
            errors.append(f"missing file: {rel}")

    # Check campaigns scaffold files
    campaigns_dir = ROOT / "campaigns"
    if not campaigns_dir.exists():
        errors.append("missing campaigns directory")
    else:
        for rel in ("campaigns/README.md", "campaigns/.gitignore"):
            if not (ROOT / rel).exists():
                errors.append(f"missing file: {rel}")

    # Every Python tool is part of the checked-in harness surface.
    tools_dir = ROOT / "tools"
    if not tools_dir.exists():
        errors.append("missing tools directory")
    else:
        for path in sorted(tools_dir.glob("*.py")):
            if not path.is_file():
                errors.append(f"missing file: {path.relative_to(ROOT)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sanity-check manifest.yaml, prompt templates, skins, templates and the tools/ layout."
    )
    parser.parse_args()
    errors = collect_errors()
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
