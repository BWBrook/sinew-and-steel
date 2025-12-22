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
    parser.add_argument("--campaign", help="Campaign slug under campaigns/ (uses campaign.yaml)")
    parser.add_argument("--mode", choices=["agent", "chat"], default="agent", help="Prompt style (default: agent)")
    parser.add_argument("--template", help="Prompt template path", default=None)
    parser.add_argument("--hidden", help="Optional hidden scenario file", default=None)
    parser.add_argument("--out", help="Output file path (default: stdout)")
    parser.add_argument("--list-skins", action="store_true", help="List available skins")
    parser.add_argument("--dry-run", action="store_true", help="Compute output but do not write files")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")

    args = parser.parse_args()
    manifest = load_manifest()

    if args.list_skins:
        list_skins(manifest)
        return 0

    campaign_skin = None
    campaign_dir = None
    if args.campaign:
        campaign_dir = ROOT / "campaigns" / args.campaign
        campaign_file = campaign_dir / "campaign.yaml"
        if not campaign_file.exists():
            print(f"error: campaign not found: {campaign_file}", file=sys.stderr)
            return 1
        campaign_data = yaml.safe_load(campaign_file.read_text(encoding="utf-8")) or {}
        campaign_skin = campaign_data.get("skin")
        if not campaign_skin:
            print("error: campaign.yaml missing skin", file=sys.stderr)
            return 1

    if not args.skin and not campaign_skin:
        print("error: --skin is required (use --list-skins to see options)", file=sys.stderr)
        return 1

    if args.skin and campaign_skin and args.skin != campaign_skin:
        print("error: --skin does not match campaign.yaml", file=sys.stderr)
        return 1

    skin_slug = args.skin or campaign_skin

    skins = manifest.get("skins", {})
    if skin_slug not in skins:
        print(f"error: unknown skin '{skin_slug}'", file=sys.stderr)
        return 1

    rules = manifest.get("rules", {})
    core = rules.get("core", {})
    adv_path = ROOT / core.get("adventurers_manual", "")
    cust_path = ROOT / core.get("custodians_almanac", "")

    skin_entry = skins[skin_slug]
    skin_path = ROOT / skin_entry.get("file", "")

    prompts = manifest.get("prompts", {})
    if args.mode == "chat":
        default_template = ROOT / prompts.get("chat_starter", prompts.get("starter", "prompts/chat/starter_prompt.md"))
    else:
        default_template = ROOT / prompts.get("agent_starter", prompts.get("starter", "prompts/agent/starter_prompt.md"))
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

    out_path = None
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    elif campaign_dir:
        out_path = campaign_dir / "prompt.md"
    else:
        out_path = None

    payload = {
        "ok": True,
        "skin": skin_slug,
        "mode": args.mode,
        "campaign": args.campaign,
        "template": str(template_path),
        "output_path": str(out_path) if out_path else None,
        "bytes": len(output.encode("utf-8")),
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        if args.json:
            import json

            print(json.dumps(payload, indent=2))
        else:
            print(output)
        return 0

    if out_path:
        out_path.write_text(output, encoding="utf-8")
        if args.json:
            import json

            print(json.dumps(payload, indent=2))
    else:
        if args.json:
            import json

            print(json.dumps(payload, indent=2))
        else:
            print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
