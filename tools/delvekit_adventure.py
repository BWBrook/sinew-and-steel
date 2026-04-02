#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import _delvekit
import _sslib


ROOT = Path(__file__).resolve().parent.parent


def _manifest_prompt_path() -> Path:
    manifest = _sslib.load_yaml(ROOT / "manifest.yaml")
    prompts = manifest.get("prompts", {})
    rel = prompts.get("candlelight_delvekit_adventure_polish", "prompts/chat/candlelight_delvekit_adventure_polish.md")
    return ROOT / rel


def _load_text(path: str | None, stdin_fallback: bool = False) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    if stdin_fallback and not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("error: expected --markdown-file or piped stdin")


def cmd_prepare(args: argparse.Namespace) -> int:
    data = _delvekit.load_dungeon(args.file)
    prompt_text = _manifest_prompt_path().read_text(encoding="utf-8")
    bundle = _delvekit.render_adventure_polish_prompt(data, prompt_text)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(bundle, encoding="utf-8")
    else:
        sys.stdout.write(bundle)
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_delvekit.adventure_polish_payload(data), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    text = _load_text(args.markdown_file, stdin_fallback=True)
    if not text.strip():
        raise SystemExit("error: empty adventure markdown")
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    if args.echo:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or apply a Codex polish pass for Candlelight Delvekit adventure markdown.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="Render the adventure polish prompt bundle for a dungeon YAML file.")
    prepare.add_argument("--file", required=True, help="Path to Delvekit YAML")
    prepare.add_argument("--out", help="Write the prompt bundle here instead of stdout")
    prepare.add_argument("--json-out", help="Write the raw adventure payload JSON here")
    prepare.set_defaults(func=cmd_prepare)

    apply = sub.add_parser("apply", help="Write polished module markdown to a file.")
    apply.add_argument("--out", required=True, help="Output markdown file")
    apply.add_argument("--markdown-file", help="Markdown file to write")
    apply.add_argument("--echo", action="store_true", help="Print the markdown after writing")
    apply.set_defaults(func=cmd_apply)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
