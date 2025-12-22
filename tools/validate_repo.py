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
    manifest_skins = set(manifest.get("skins", {}).keys())

    missing_in_manifest = skin_files - manifest_skins
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

    # Check tools we rely on
    for rel in (
        "tools/_sslib.py",
        "tools/_dice.py",
        "tools/build_prompt.py",
        "tools/roll.py",
        "tools/recap.py",
        "tools/session_log.py",
        "tools/apply_roll.py",
        "tools/beat.py",
        "tools/doctor.py",
        "tools/ss.py",
        "tools/checkpoint.py",
        "tools/resume_pack.py",
        "tools/summary.py",
        "tools/new_session.py",
        "tools/gen_character.py",
        "tools/char_builder.py",
        "tools/recalc_sheet.py",
        "tools/campaign_init.py",
        "tools/validate_sheet.py",
        "tools/validate_campaign.py",
    ):
        if not (ROOT / rel).exists():
            errors.append(f"missing file: {rel}")

    return errors


def main() -> int:
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
