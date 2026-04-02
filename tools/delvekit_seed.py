#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

import _delvekit
import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a seeded Candlelight Delvekit dungeon.")
    parser.add_argument("--seed", type=int, required=True, help="Deterministic random seed")
    parser.add_argument("--size", choices=["tiny", "medium", "large"], default="tiny")
    parser.add_argument("--difficulty", choices=["soft", "medium", "hard"], default="medium")
    parser.add_argument("--title", help="Optional dungeon title")
    parser.add_argument("--out", help="Write YAML dungeon state to this path")
    parser.add_argument("--markdown-out", help="Optional markdown dossier output path")
    parser.add_argument("--gm-map-out", help="Optional rendered hidden GM map output path")
    parser.add_argument("--player-map-out", help="Optional rendered initial player map output path")
    parser.add_argument("--pitch-prompt-out", help="Optional Codex polish prompt bundle output path")
    parser.add_argument("--pitch-json-out", help="Optional raw pitch payload JSON output path")
    parser.add_argument("--adventure-prompt-out", help="Optional Codex adventure polish prompt bundle output path")
    parser.add_argument("--adventure-json-out", help="Optional raw adventure payload JSON output path")

    args = parser.parse_args()

    payload = _delvekit.generate_dungeon(
        seed=args.seed,
        size=args.size,
        difficulty=args.difficulty,
        title=args.title,
    )
    yaml_text = yaml.safe_dump(payload, sort_keys=False)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml_text, encoding="utf-8")
    else:
        sys.stdout.write(yaml_text)

    if args.markdown_out:
        path = Path(args.markdown_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_delvekit.dungeon_to_markdown(payload), encoding="utf-8")

    if args.gm_map_out:
        path = Path(args.gm_map_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_delvekit.render_map(payload, mode="gm"), encoding="utf-8")

    if args.player_map_out:
        path = Path(args.player_map_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_delvekit.render_map(payload, mode="player", frontier=True), encoding="utf-8")

    if args.pitch_prompt_out:
        manifest = _delvekit._sslib.load_yaml(Path(__file__).resolve().parent.parent / "manifest.yaml")
        prompt_rel = manifest.get("prompts", {}).get("candlelight_delvekit_pitch_polish", "prompts/chat/candlelight_delvekit_pitch_polish.md")
        prompt_text = (Path(__file__).resolve().parent.parent / prompt_rel).read_text(encoding="utf-8")
        path = Path(args.pitch_prompt_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_delvekit.render_pitch_polish_prompt(payload, prompt_text), encoding="utf-8")

    if args.pitch_json_out:
        path = Path(args.pitch_json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_delvekit.pitch_polish_payload(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.adventure_prompt_out:
        manifest = _delvekit._sslib.load_yaml(Path(__file__).resolve().parent.parent / "manifest.yaml")
        prompt_rel = manifest.get("prompts", {}).get("candlelight_delvekit_adventure_polish", "prompts/chat/candlelight_delvekit_adventure_polish.md")
        prompt_text = (Path(__file__).resolve().parent.parent / prompt_rel).read_text(encoding="utf-8")
        path = Path(args.adventure_prompt_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_delvekit.render_adventure_polish_prompt(payload, prompt_text), encoding="utf-8")

    if args.adventure_json_out:
        path = Path(args.adventure_json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_delvekit.adventure_polish_payload(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
