#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

import _delvekit
import _sslib


ROOT = Path(__file__).resolve().parent.parent


def _manifest_prompt_path() -> Path:
    manifest = _sslib.load_yaml(ROOT / "manifest.yaml")
    prompts = manifest.get("prompts", {})
    rel = prompts.get("candlelight_delvekit_pitch_polish", "prompts/chat/candlelight_delvekit_pitch_polish.md")
    return ROOT / rel


def _load_text(path: str | None, stdin_fallback: bool = False) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    if stdin_fallback and not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("error: expected --text-file/--json-file or piped stdin")


def _parse_polish_text(text: str) -> tuple[str, str]:
    stripped = text.strip()
    if not stripped:
        raise SystemExit("error: empty polish text")
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        title = str(payload.get("title", "")).strip()
        blurb = str(payload.get("blurb", "")).strip()
        if title and blurb:
            return title, blurb

    title_match = re.search(r"(?im)^\s*Title:\s*(.+?)\s*$", stripped)
    blurb_match = re.search(r"(?ims)^\s*Blurb:\s*(.+?)\s*$", stripped)
    if title_match and blurb_match:
        return title_match.group(1).strip(), blurb_match.group(1).strip()
    raise SystemExit("error: could not parse polished output; expected JSON {title, blurb} or lines beginning with Title: and Blurb:")


def cmd_prepare(args: argparse.Namespace) -> int:
    data = _delvekit.load_dungeon(args.file)
    prompt_text = _manifest_prompt_path().read_text(encoding="utf-8")
    bundle = _delvekit.render_pitch_polish_prompt(data, prompt_text)
    payload_json = json.dumps(_delvekit.pitch_polish_payload(data), indent=2, ensure_ascii=False) + "\n"

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(bundle, encoding="utf-8")
    else:
        sys.stdout.write(bundle)

    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload_json, encoding="utf-8")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    data = _delvekit.load_dungeon(args.file)
    if args.title and args.blurb:
        title, blurb = args.title.strip(), args.blurb.strip()
    else:
        text = _load_text(args.text_file or args.json_file, stdin_fallback=True)
        title, blurb = _parse_polish_text(text)
    _delvekit.apply_polished_pitch(data, title=title, blurb=blurb)
    target = Path(args.out or args.file)
    target.parent.mkdir(parents=True, exist_ok=True)
    _delvekit.save_dungeon(target, data)
    if args.echo:
        sys.stdout.write(f"Title: {title}\nBlurb: {blurb}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or apply a Codex polish pass for Candlelight Delvekit pitches.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="Render the polish prompt bundle for a dungeon YAML file.")
    prepare.add_argument("--file", required=True, help="Path to Delvekit YAML")
    prepare.add_argument("--out", help="Write the prompt bundle here instead of stdout")
    prepare.add_argument("--json-out", help="Write the raw pitch payload JSON here")
    prepare.set_defaults(func=cmd_prepare)

    apply = sub.add_parser("apply", help="Apply polished title/blurb text back into the dungeon YAML.")
    apply.add_argument("--file", required=True, help="Path to Delvekit YAML")
    apply.add_argument("--out", help="Write updated YAML here instead of replacing --file")
    apply.add_argument("--text-file", help="File containing `Title:` and `Blurb:` lines")
    apply.add_argument("--json-file", help="File containing JSON with `title` and `blurb` keys")
    apply.add_argument("--title", help="Apply this title directly")
    apply.add_argument("--blurb", help="Apply this blurb directly")
    apply.add_argument("--echo", action="store_true", help="Print the parsed title/blurb after applying")
    apply.set_defaults(func=cmd_apply)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
