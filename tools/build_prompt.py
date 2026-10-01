#!/usr/bin/env python3
"""Assemble a compact Custodian prompt and check it against its exact sources."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml

import _sslib
import resume_pack

ROOT = Path(__file__).resolve().parents[1]
METADATA_PREFIX = "<!-- SINEW_PROMPT_METADATA "
MD_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(\s*(?:<[^>]+>|[^)]+?)\s*(?:\s+"[^\"]*")?\)(?:\{[^}]*\})?[ \t]*')


def strip_art_markdown(text: str) -> str:
    text = MD_IMAGE_RE.sub("", text)
    text = re.sub(r"^[ \t]+$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_joined_text(paths: list[Path]) -> str:
    return "\n\n".join(load_text(path).strip() for path in paths)


def load_manifest() -> dict:
    return _sslib.load_manifest(ROOT)


def list_skins(manifest: dict) -> None:
    for slug, skin in sorted(manifest.get("skins", {}).items()):
        print(f"{slug}: {skin.get('name', slug)}")


def _reference(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _resolve(reference: str, root: Path) -> Path:
    path = Path(reference)
    return path if path.is_absolute() else root / path


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def campaign_sources(campaign_dir: Path) -> list[Path]:
    """Exactly the live state files represented in the resume, including new arrivals."""
    paths = [campaign_dir / "campaign.yaml", campaign_dir / "state/trackers/session.yaml"]
    paths += sorted([*(campaign_dir / "state/characters").glob("*.yaml"),
                     *(campaign_dir / "state/characters").glob("*.yml")])
    for directory, pattern, suffixes in [
        ("memory", resume_pack.SESSION_YAML_RE, ("yaml", "yml")),
        ("logs", resume_pack.SESSION_MD_RE, ("md",)),
    ]:
        path = resume_pack.latest_session_file(campaign_dir / "state" / directory, pattern, suffixes)
        if path:
            paths.append(path)
    paths += [campaign_dir / "state/memory/hidden_scenario.md", campaign_dir / "state/checkpoints/last.md"]
    return sorted({path for path in paths if path.exists()})


def rules_section(manifest: dict, selector: str, root: Path = ROOT) -> tuple[Path, str]:
    book, separator, section = selector.partition(":")
    aliases = {"manual": "adventurers_manual", "adventurers": "adventurers_manual",
               "almanac": "custodians_almanac", "custodians": "custodians_almanac"}
    key = aliases.get(book, book)
    if not separator or not section or key not in manifest["rules"]["core"]:
        raise ValueError("section must be manual:NUMBER or almanac:NUMBER (for example manual:6)")
    path = root / manifest["rules"]["core"][key]
    lines = load_text(path).splitlines(keepends=True)
    matches = []
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading and re.match(rf"^{re.escape(section)}(?:\.(?!\d)|\s|$)", heading[2]):
            matches.append((index, len(heading[1])))
    if len(matches) != 1:
        raise ValueError(f"section '{selector}' was not uniquely found")
    start, level = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        heading = re.match(r"^(#{1,6})\s+", lines[index])
        if heading and len(heading[1]) <= level:
            end = index
            break
    return path, "".join(lines[start:end]).strip()


def assemble_prompt(manifest: dict, skin_slug: str | None, *, root: Path = ROOT,
                    campaign_dir: Path | None = None, profile: str = "compact", mode: str = "agent",
                    sections: list[str] | None = None, template_path: Path | None = None,
                    hidden_path: Path | None = None, keep_art: bool = False) -> tuple[str, dict]:
    sections = sections or []
    paths = [root / "manifest.yaml", root / "tools/build_prompt.py", root / "tools/resume_pack.py"]
    if (root / "VERSION").exists():
        paths.append(root / "VERSION")
    section_texts = []
    for selector in sections:
        path, text = rules_section(manifest, selector, root)
        paths.append(path)
        section_texts.append(text)
    if skin_slug is None:
        if not sections:
            raise ValueError("provide --skin, --campaign, or --section")
        body = "\n\n".join(section_texts)
    else:
        skin = manifest.get("skins", {}).get(skin_slug)
        if skin is None:
            raise ValueError(f"unknown skin '{skin_slug}'")
        if profile not in {"compact", "full"}:
            raise ValueError("prompt profile must be compact or full")
        core = manifest["rules"]["core"]
        adv_path, cust_path = (root / core[key] for key in ("adventurers_manual", "custodians_almanac"))
        quickstart_path = root / manifest["rules"]["quickstart"]
        paths += [adv_path, cust_path, quickstart_path]
        skin_paths = [root / skin["file"], *[root / p for p in skin.get("addons", [])]]
        paths += skin_paths
        template_path = template_path or root / manifest["prompts"][f"{mode}_starter"]
        paths.append(template_path)
        if campaign_dir:
            paths += campaign_sources(campaign_dir)
            pack = resume_pack.collect_resume(campaign_dir, manifest)
            public_state = {key: pack[key] for key in ("campaign", "characters", "scene", "checkpoint")}
            private_state = {key: pack[key] for key in ("sheets", "tracker", "memory", "log")}
            if hidden_path is None and (campaign_dir / "state/memory/hidden_scenario.md").exists():
                hidden_path = campaign_dir / "state/memory/hidden_scenario.md"
        else:
            public_state, private_state = {}, {}
        hidden_text = "[No hidden scenario supplied.]"
        if hidden_path:
            paths.append(hidden_path)
            hidden_text = load_text(hidden_path)
        core_text = (load_joined_text([adv_path, cust_path]) if profile == "full" else load_text(quickstart_path))
        index = ("For detailed rulings load a numbered section with `tools/build_prompt.py --section manual:6` "
                 "(combat), `--section manual:8` (Pressure), or `--section almanac:4` (Custodian Pressure procedure). "
                 "Read the selected skin's exceptions first. Use `--full` for both complete core books.")
        replacements = {"{{CORE_RULES}}": core_text, "{{RULES_SECTIONS}}": "\n\n".join(section_texts) or index,
                        "{{SKIN_TEXT}}": load_joined_text(skin_paths), "{{SKIN_NAME}}": skin["name"],
                        "{{PUBLIC_STATE}}": yaml.safe_dump(public_state, sort_keys=False).strip(),
                        "{{PRIVATE_STATE}}": yaml.safe_dump(private_state, sort_keys=False).strip(),
                        "{{HIDDEN_SCENARIO}}": hidden_text,
                        # Existing custom templates remain usable, but full books are now opt-in.
                        "{{CORE_RULES_ADVENTURERS}}": core_text,
                        "{{CORE_RULES_CUSTODIANS}}": index}
        body = load_text(template_path)
        for key, value in replacements.items():
            if not keep_art and key in {"{{CORE_RULES}}", "{{RULES_SECTIONS}}", "{{SKIN_TEXT}}", "{{CORE_RULES_ADVENTURERS}}"}:
                value = strip_art_markdown(value)
            body = body.replace(key, value.strip())
    if not keep_art and skin_slug is None:
        body = strip_art_markdown(body)
    body = body.rstrip() + "\n"
    sources = {_reference(path, root): _hash(path) for path in sorted(set(paths))}
    metadata = {"schema_version": 1, "skin": skin_slug, "profile": profile, "mode": mode,
                "sections": sections, "keep_art": keep_art, "sources": sources,
                "campaign": _reference(campaign_dir, root) if campaign_dir else None,
                "campaign_sources": [_reference(p, root) for p in campaign_sources(campaign_dir)] if campaign_dir else [],
                "body_sha256": hashlib.sha256(body.encode()).hexdigest()}
    metadata["fingerprint"] = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    header = METADATA_PREFIX + json.dumps(metadata, sort_keys=True, separators=(",", ":")) + " -->\n"
    return header + body, metadata


def check_prompt(path: Path, root: Path = ROOT) -> list[str]:
    if not path.exists():
        return [f"prompt missing: {path.name}"]
    text = load_text(path)
    header, _, body = text.partition("\n")
    if not header.startswith(METADATA_PREFIX) or not header.endswith(" -->"):
        return ["prompt has no source fingerprint; rebuild it"]
    try:
        metadata = json.loads(header[len(METADATA_PREFIX):-4])
        if metadata.get("schema_version") != 1 or not isinstance(metadata.get("sources"), dict):
            return ["prompt source fingerprint is invalid; rebuild it"]
        errors = []
        fingerprint = metadata.pop("fingerprint", None)
        if fingerprint != hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest():
            errors.append("prompt source fingerprint changed after assembly")
        if metadata.get("body_sha256") != hashlib.sha256(body.encode()).hexdigest():
            errors.append("prompt body changed after assembly")
        for reference, expected in metadata["sources"].items():
            source = _resolve(reference, root)
            if not source.exists() or _hash(source) != expected:
                errors.append(f"stale prompt source: {reference}")
        if metadata.get("campaign"):
            cdir = _resolve(metadata["campaign"], root)
            actual = [_reference(p, root) for p in campaign_sources(cdir)]
            if actual != metadata.get("campaign_sources"):
                errors.append("stale prompt: campaign source files changed")
        return errors
    except (ValueError, TypeError, OSError) as exc:
        return [f"invalid prompt fingerprint: {exc}"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a compact prompt, fetch rules sections, or check source freshness.")
    parser.add_argument("--skin")
    parser.add_argument("--campaign")
    parser.add_argument("--mode", choices=["agent", "chat"], default="agent")
    parser.add_argument("--profile", choices=["compact", "full"], default=None)
    parser.add_argument("--full", action="store_true", help="Embed both complete core books")
    parser.add_argument("--section", action="append", default=[], help="Load a rules section, e.g. manual:6 or almanac:4")
    parser.add_argument("--template")
    parser.add_argument("--hidden")
    parser.add_argument("--out")
    parser.add_argument("--keep-art", action="store_true")
    parser.add_argument("--list-skins", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check existing --out or campaign prompt; never write")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        if args.list_skins:
            list_skins(manifest)
            return 0
        cdir = _sslib.campaign_dir(args.campaign, root=ROOT) if args.campaign else None
        campaign = _sslib.load_yaml(cdir / "campaign.yaml") if cdir else {}
        if args.skin and campaign.get("skin") and args.skin != campaign["skin"]:
            raise ValueError("--skin does not match campaign.yaml")
        out = _resolve(args.out, ROOT) if args.out else cdir / "prompt.md" if cdir else None
        if args.check:
            if out is None:
                raise ValueError("--check requires --out or --campaign")
            errors = check_prompt(out)
            payload = {"ok": not errors, "output_path": str(out), "errors": errors}
            print(json.dumps(payload, indent=2) if args.json else "fresh" if not errors else "\n".join(errors))
            return 1 if errors else 0
        output, metadata = assemble_prompt(manifest, args.skin or campaign.get("skin"), campaign_dir=cdir,
            profile="full" if args.full else args.profile or campaign.get("prompt_profile", "compact"), mode=args.mode,
            sections=args.section, template_path=_resolve(args.template, ROOT) if args.template else None,
            hidden_path=_resolve(args.hidden, ROOT) if args.hidden else None, keep_art=args.keep_art)
        payload = {"ok": True, "skin": metadata["skin"], "profile": metadata["profile"],
                   "output_path": str(out) if out else None, "bytes": len(output.encode()),
                   "fingerprint": metadata["fingerprint"], "sources": metadata["sources"], "dry_run": args.dry_run}
        if out and not args.dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(output, encoding="utf-8")
        if args.json:
            print(json.dumps(payload, indent=2))
        elif args.dry_run or out is None:
            print(output, end="")
        else:
            print(f"written {out}")
        return 0
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
