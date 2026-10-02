#!/usr/bin/env python3
"""Check the creation ledgers printed in every skin's sample-character section.

The prose is the input: there is no parallel list of sample stats to go stale.
Explicit Tag/Knack/Expertise declarations are priced, after the manifest's
per-kind free grants. Equipment and future milestone wishes are not tags.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

import yaml

from _rules import ATTRIBUTE_MAX, ATTRIBUTE_MIN, STAMINA_MAX, STAMINA_MIN, creation_price


ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PER_SKIN = 2
_SAMPLE_SECTION = re.compile(r"^##\s+.*\b(?:sample|example|active|figures)\b.*$", re.I | re.M)
_SECTION = re.compile(r"^##\s+.+$", re.M)
_CHARACTER = re.compile(r"^###\s+(.+?)\s*$", re.M)
_CREATION_LINE = re.compile(r"^Creation:\s*(.*?)\s*$", re.I | re.M)
_CREATION = re.compile(r"\((\d+)\s+build points(?:;\s*used\s+(\d+))?\)", re.I)
_TAG_LABEL = re.compile(r"\b(Tag|Tags|Knack|Knacks|Expertise):\s*", re.I)


@dataclass(frozen=True)
class PublishedSample:
    skin: str
    name: str
    source: str
    line: int
    attributes: dict[str, int]
    stamina: int
    budget: int
    stated_used: int | None
    bought_tags: tuple[str, ...]
    free_tags: tuple[str, ...]

    @property
    def price(self) -> int:
        return creation_price(self.attributes, self.stamina, self.bought_tags)


@dataclass
class SampleValidation:
    samples: list[PublishedSample] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_statline(line: str, attribute_keys) -> tuple[dict[str, int], int]:
    """Read a printed creation statline, requiring all five scores and STM."""
    expected = set(attribute_keys) | {"STM"}
    scores: dict[str, int] = {}
    for raw_field in re.sub(r"<[^>]+>", "", line).split("|"):
        match = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9_]*)\s+(\d+)(?:/(\d+))?\s*", raw_field)
        if not match:
            raise ValueError(f"malformed stat field: {raw_field.strip()!r}")
        key, current, maximum = match.groups()
        if key in scores:
            raise ValueError(f"duplicate score: {key}")
        if key not in expected:
            # Personal Insanity and journey Fatigue are printed beside scores.
            if key not in {"Insanity", "Fatigue"} or (current, maximum) != ("0", "5"):
                raise ValueError(f"unexpected creation stat field: {key}")
            continue
        value = int(maximum if maximum is not None else current)
        if maximum is not None and int(current) != value:
            raise ValueError(f"creation pool {key} is not full")
        low, high = (STAMINA_MIN, STAMINA_MAX) if key == "STM" else (ATTRIBUTE_MIN, ATTRIBUTE_MAX)
        if not low <= value <= high:
            raise ValueError(f"{key} {value} is outside {low}-{high}")
        scores[key] = value
    missing = expected - scores.keys()
    if missing:
        raise ValueError(f"missing scores: {', '.join(sorted(missing))}")
    stamina = scores.pop("STM")
    return scores, stamina


def _sample_tags(block: str, free_grants: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    remaining = {kind: int(number) for kind, number in free_grants.items()}
    bought, free = [], []
    for line in block.splitlines():
        labels = list(_TAG_LABEL.finditer(line))
        for index, label in enumerate(labels):
            end = labels[index + 1].start() if index + 1 < len(labels) else len(line)
            declaration = re.sub(r"<[^>]+>", "", line[label.end():end]).strip()
            # A parenthesis describes the tag's scope; a sentence after it is
            # character prose. Semicolons separate multiple named tags.
            declaration = re.split(r"\.\s|\.$", declaration, maxsplit=1)[0]
            kind = label.group(1).lower().rstrip("s")
            names = re.split(r"\s*;\s*", declaration)
            if label.group(1).lower() in {"tags", "knacks"}:
                names = [part for name in names for part in re.split(r"\s*,\s*", name)]
            for name in names:
                name = re.sub(r"\s*\(.*", "", name).strip(" *_.")
                if not name:
                    raise ValueError(f"empty {kind} declaration")
                if remaining.get(kind, 0) > 0:
                    free.append(name)
                    remaining[kind] -= 1
                else:
                    bought.append(name)
    return tuple(bought), tuple(free)


def parse_skin_samples(text: str, slug: str, skin: dict, source: str = "<text>") -> SampleValidation:
    result = SampleValidation()
    blocks: list[tuple[str, int, str]] = []
    sections = list(_SECTION.finditer(text))
    for index, section in enumerate(sections):
        if not _SAMPLE_SECTION.fullmatch(section.group()):
            continue
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        sample_section = text[section.end():end]
        headings = list(_CHARACTER.finditer(sample_section))
        for number, heading in enumerate(headings):
            block_end = headings[number + 1].start() if number + 1 < len(headings) else len(sample_section)
            line = text.count("\n", 0, section.end() + heading.start()) + 1
            blocks.append((heading.group(1), line, sample_section[heading.end():block_end]))

    if len(blocks) != SAMPLES_PER_SKIN:
        result.errors.append(f"{source}: expected {SAMPLES_PER_SKIN} published sample characters; found {len(blocks)}")
    contained_creation_lines = sum(len(_CREATION_LINE.findall(block)) for _, _, block in blocks)
    if len(_CREATION_LINE.findall(text)) != contained_creation_lines:
        result.errors.append(f"{source}: Creation declaration outside a sample-character section")

    for name, line, block in blocks:
        label = f"{source}:{line} ({name})"
        try:
            creation_lines = _CREATION_LINE.findall(block)
            if len(creation_lines) != 1:
                raise ValueError(f"expected one Creation declaration; found {len(creation_lines)}")
            creation = _CREATION.search(creation_lines[0])
            if not creation:
                raise ValueError("cannot read Creation build-point budget and used amount")
            budget, used = creation.groups()
            statlines = [line for line in block.splitlines() if "|" in line and re.search(r"\bSTM\s+", line)]
            if len(statlines) != 1:
                raise ValueError(f"expected one complete statline; found {len(statlines)}")
            attributes, stamina = parse_statline(statlines[0], skin["attributes"])
            bought, free = _sample_tags(block, skin.get("creation_free_tags", {}))
            sample = PublishedSample(
                slug, name, source, line, attributes, stamina, int(budget),
                int(used) if used is not None else None, bought, free,
            )
            result.samples.append(sample)
            if sample.price > sample.budget:
                result.errors.append(f"{label}: creation price {sample.price} exceeds budget {sample.budget}")
            if sample.stated_used is not None and sample.price != sample.stated_used:
                result.errors.append(f"{label}: says used {sample.stated_used}, but creation price is {sample.price}")
        except (KeyError, ValueError, TypeError) as exc:
            result.errors.append(f"{label}: {exc}")
    return result


def validate_samples(manifest: dict, root: Path = ROOT) -> SampleValidation:
    result = SampleValidation()
    for slug, skin in manifest.get("skins", {}).items():
        source = skin.get("file")
        if not source or not (root / source).is_file():
            result.errors.append(f"{slug}: missing sample source: {source}")
            continue
        parsed = parse_skin_samples((root / source).read_text(encoding="utf-8"), slug, skin, source)
        result.samples.extend(parsed.samples)
        result.errors.extend(parsed.errors)
    if not result.samples:
        result.errors.append("no published skin samples parsed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    manifest = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    result = validate_samples(manifest)
    if result.errors:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"ok: {len(result.samples)} published sample characters across {len(manifest['skins'])} skins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
