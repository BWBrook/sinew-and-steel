"""Release-book Markdown assembly and bundle definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import sys

from _pdf_common import load_text, rewrite_markdown_image_paths

ROOT = Path(__file__).resolve().parents[1]

_SKIN_CUSTODIAN_HEADING_RE = re.compile(r"^##\s+.*\bCustodian\b", re.IGNORECASE)
_SKIN_SAMPLE_HEADING_RE = re.compile(r"^##\s+.*\b(?:SAMPLE|EXAMPLE|ACTIVE|FIGURES)\b", re.IGNORECASE)


def _strip_trailing_separator(lines: list[str]) -> None:
    while lines and lines[-1].strip() == "":
        lines.pop()
    if lines and lines[-1].strip() == "---":
        lines.pop()
    while lines and lines[-1].strip() == "":
        lines.pop()


def _inject_new_page(lines: list[str]) -> None:
    _strip_trailing_separator(lines)
    if lines and lines[-1].strip() in {"\\newpage", "\\clearpage", "\\pagebreak"}:
        lines.append("")
        return
    if lines and lines[-1].strip() != "":
        lines.append("")
    lines.append("\\newpage")
    lines.append("")


def inject_skin_section_pagebreaks(text: str) -> str:
    # For PDF release builds we want a stable “3-part skin layout”:
    # - Adventurer-facing rules first (can span multiple pages)
    # - Custodian section starts on a fresh page
    # - Sample characters start on a fresh page
    #
    # This also deliberately consumes the nearby `---` separators to avoid
    # leaving horizontal rules marooned in blank space.
    lines = text.splitlines()
    out: list[str] = []
    saw_custodian = False
    saw_samples = False
    for line in lines:
        if not saw_custodian and _SKIN_CUSTODIAN_HEADING_RE.match(line):
            _inject_new_page(out)
            saw_custodian = True
        elif not saw_samples and _SKIN_SAMPLE_HEADING_RE.match(line):
            _inject_new_page(out)
            saw_samples = True
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _preferred_logo_image_for_skin(skin_path: Path) -> Path | None:
    """
    Pick the best maker's-mark image for a given skin.

    Preference order:
      1) Per-skin logo in `assets/covers/ss_logo_<skin>.png`
      2) Compatibility aliases (e.g. remove `_of_the_`, `free_traders_*`)
      3) Generic S&S logo (`assets/covers/ss_logo.png`)
      4) Generic icon fallback (`assets/covers/ss_icon.png`) if present
    """

    stem = skin_path.stem
    candidates: list[Path] = [Path(f"assets/covers/ss_logo_{stem}.png")]

    if "_of_the_" in stem:
        candidates.append(Path(f"assets/covers/ss_logo_{stem.replace('_of_the_', '_')}.png"))

    if stem.startswith("free_traders_"):
        candidates.append(Path("assets/covers/ss_logo_free_traders.png"))

    candidates.extend(
        [
            Path("assets/covers/ss_logo.png"),
            Path("assets/covers/ss_icon.png"),
        ]
    )

    for rel in candidates:
        if (ROOT / rel).exists():
            return rel

    return None


def inject_skin_maker_mark(text: str, *, logo_rel: Path) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    insert_at = 1
    if len(lines) >= 2 and lines[1].lstrip().startswith("### "):
        insert_at = 2

    # Don't double-insert if the file already has it.
    needle = logo_rel.as_posix()
    if any(needle in line for line in lines[:12]):
        return text

    maker_mark = f"![](../{needle}){{.wrap-right width=0.45in}}"

    out: list[str] = []
    out.extend(lines[:insert_at])
    out.append("")
    out.append(maker_mark)
    out.append("")
    out.extend(lines[insert_at:])
    return "\n".join(out).rstrip() + "\n"


@dataclass(frozen=True)
class BookChapter:
    title: str
    path: Path
    strip_first_heading: bool = True
    content_class: str | None = None


@dataclass(frozen=True)
class BookPart:
    title: str
    chapters: tuple[BookChapter, ...]


@dataclass(frozen=True)
class Bundle:
    key: str
    title: str
    subtitle: str
    input_paths: list[Path]
    output_base: str
    toc: bool = False
    number_sections: bool = False
    variants: tuple[str, ...] = ("pdf",)
    cover_image: Path | None = None
    suppress_title_block: bool = False
    book_parts: tuple[BookPart, ...] = ()
    end_matter_paths: tuple[Path, ...] = ()
    toc_depth: int | None = None
    content_class: str | None = None


def render_front_matter(title: str, subtitle: str, version: str) -> str:
    today = date.today().isoformat()
    return "\n".join(
        [
            "---",
            f"title: \"{title}\"",
            f"subtitle: \"{subtitle}\"",
            "author: \"Barry Brook\"",
            f"version: \"{version}\"",
            f"date: \"{today}\"",
            "---",
            "",
        ]
    )


def prepare_release_markdown_source(path: Path) -> str:
    text = load_text(path).strip()
    try:
        rel = path.resolve().relative_to(ROOT)
    except Exception:
        rel = None
    if rel and rel.parts and rel.parts[0] == "skins" and path.suffix.lower() == ".md":
        logo_rel = _preferred_logo_image_for_skin(path)
        if logo_rel is not None:
            text = inject_skin_maker_mark(text, logo_rel=logo_rel).strip()
        text = inject_skin_section_pagebreaks(text).strip()
    return rewrite_markdown_image_paths(text=text, source_path=path).strip()


_MD_ATX_HEADING_RE = re.compile(r"^(?P<indent> {0,3})(?P<marks>#{1,6})(?P<space>[ \t]+)(?P<title>.*)$")
_MD_FENCE_RE = re.compile(r"^ {0,3}(```+|~~~+)")


def strip_first_markdown_heading(text: str) -> str:
    lines = text.splitlines()
    in_fence = False
    for idx, line in enumerate(lines):
        if _MD_FENCE_RE.match(line):
            in_fence = not in_fence
        if not in_fence and _MD_ATX_HEADING_RE.match(line):
            del lines[idx]
            while idx < len(lines) and lines[idx].strip() == "":
                del lines[idx]
            return "\n".join(lines).strip()
    return text.strip()


def normalize_book_body_headings(text: str) -> str:
    """
    The full book wraps standalone source files in the authored book hierarchy:
    parts are h2 and chapters are h3. Source-internal headings are therefore
    normalized to h4/h5 so they never leak into the top-level book TOC.
    """

    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    for line in lines:
        if _MD_FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        match = _MD_ATX_HEADING_RE.match(line)
        if not in_fence and match:
            old_level = len(match.group("marks"))
            new_level = 4 if old_level <= 2 else 5
            out.append(
                f'{match.group("indent")}{"#" * new_level}{match.group("space")}{match.group("title")}'
            )
        else:
            out.append(line)
    return "\n".join(out).strip()


def prepare_book_chapter_markdown(chapter: BookChapter) -> str:
    text = prepare_release_markdown_source(chapter.path)
    if chapter.strip_first_heading:
        text = strip_first_markdown_heading(text)
    return normalize_book_body_headings(text).strip()


def concatenate_markdown(paths: list[Path]) -> str:
    parts: list[str] = []
    for idx, path in enumerate(paths):
        if idx != 0:
            parts.append("\n\\newpage\n")
        parts.append(prepare_release_markdown_source(path))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def concatenate_book_parts(parts_spec: tuple[BookPart, ...]) -> str:
    parts: list[str] = ["# SINEW & STEEL", ""]
    for part_idx, part in enumerate(parts_spec):
        if part_idx != 0:
            parts.append("\n\\newpage\n")
        parts.append(f"## {part.title}")
        parts.append("")
        for chapter_idx, chapter in enumerate(part.chapters):
            if chapter_idx != 0:
                parts.append("\n\\newpage\n")
            if chapter.content_class:
                parts.append(f"::: {{.{chapter.content_class}}}")
                parts.append("")
            parts.append(f"### {chapter.title}")
            parts.append("")
            body = prepare_book_chapter_markdown(chapter)
            if body:
                parts.append(body)
                parts.append("")
            if chapter.content_class:
                parts.append(":::")
                parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def concatenate_end_matter(paths: tuple[Path, ...]) -> str:
    parts: list[str] = []
    for path in paths:
        text = strip_first_markdown_heading(prepare_release_markdown_source(path))
        if not text:
            continue
        # The named page style below forces the back-cover blurb onto its own
        # page in WeasyPrint; adding an explicit pagebreak as well creates a
        # spare blank page before the back cover.
        parts.append("")
        parts.append("::: {.ss-back-cover-blurb}")
        parts.append("")
        parts.append("## Back Cover Blurb {.unlisted}")
        parts.append("")
        parts.append(text)
        parts.append("")
        parts.append(":::")
        parts.append("")
    return "\n".join(parts).rstrip() + ("\n" if parts else "")


def wrap_markdown_div(content: str, class_name: str | None) -> str:
    if not class_name:
        return content
    return f"::: {{.{class_name}}}\n\n{content.rstrip()}\n\n:::\n"

def bundle_definitions(manifest: dict, version: str) -> dict[str, Bundle]:
    rules = manifest.get("rules", {})
    core = rules.get("core", {})
    adv_rel = core.get("adventurers_manual")
    cust_rel = core.get("custodians_almanac")
    quick_rel = rules.get("quickstart")

    if not adv_rel or not cust_rel:
        print("error: manifest missing core rules paths", file=sys.stderr)
        raise SystemExit(1)

    adv = ROOT / adv_rel
    cust = ROOT / cust_rel
    quick = ROOT / quick_rel if quick_rel else None

    skins = manifest.get("skins", {})
    skin_paths: list[Path] = []
    for slug, entry in skins.items():
        rel = entry.get("file")
        if not rel:
            print(f"error: manifest missing skins.{slug}.file", file=sys.stderr)
            raise SystemExit(1)
        skin_paths.append(ROOT / rel)

    bundles: dict[str, Bundle] = {}

    def skin_path(slug: str) -> Path:
        try:
            rel = skins[slug]["file"]
        except KeyError:
            print(f"error: manifest missing skin '{slug}'", file=sys.stderr)
            raise SystemExit(1)
        if not rel:
            print(f"error: manifest missing skins.{slug}.file", file=sys.stderr)
            raise SystemExit(1)
        return ROOT / rel

    if quick:
        full_book_parts = (
            BookPart(
                title="INTRODUCTION",
                chapters=(
                    BookChapter("1. Preface", ROOT / "rules" / "book" / "preface.md"),
                    BookChapter("2. Quickstart", quick, content_class="ss-quickstart-standalone"),
                ),
            ),
            BookPart(
                title="CORE RULES",
                chapters=(
                    BookChapter("3. The Adventurer", ROOT / "rules" / "book" / "the_adventurer.md"),
                    BookChapter("4. Adventurers Manual", adv),
                    BookChapter("5. The Custodian", ROOT / "rules" / "book" / "the_custodian.md"),
                    BookChapter("6. Custodian’s Almanac", cust),
                    BookChapter("7. Customisation", ROOT / "rules" / "book" / "customisation.md"),
                    BookChapter("8. Clanfire (exemplar skin)", skin_path("clanfire")),
                ),
            ),
            BookPart(
                title="STARTER SCENARIO",
                chapters=(
                    BookChapter("9. Clanfire: Emberfall", ROOT / "rules" / "scenarios" / "clanfire_emberfall.md"),
                    BookChapter(
                        "10. Clanfire Player Handout",
                        ROOT / "rules" / "scenarios" / "clanfire_emberfall_player_handout.md",
                    ),
                    BookChapter(
                        "11. Clanfire Custodian Notes",
                        ROOT / "rules" / "scenarios" / "clanfire_emberfall_custodian_notes.md",
                    ),
                ),
            ),
            BookPart(
                title="EXPANSION SKINS",
                chapters=(
                    BookChapter("12. Iron and Ruin", skin_path("iron_and_ruin")),
                    BookChapter("13. Time Odyssey", skin_path("time_odyssey")),
                    BookChapter("14. Briar and Benedictine", skin_path("briar_benedictine")),
                    BookChapter("15. Rust and Domes", skin_path("rust_and_domes")),
                    BookChapter("16. Candlelight Dungeons", skin_path("candlelight_dungeons")),
                    BookChapter("17. Service Duct Blues", skin_path("service_duct_blues")),
                    BookChapter("18. Whispers in the Fog", skin_path("whispers_in_the_fog")),
                    BookChapter(
                        "19. Free Traders of the Drift Marches",
                        skin_path("free_traders_of_the_drift_marches"),
                    ),
                    BookChapter("20. Twilight of the Northlands", skin_path("twilight_of_the_northlands")),
                ),
            ),
            BookPart(
                title="AI FOR SOLO PLAY",
                chapters=(
                    BookChapter("21. AI as Custodian", ROOT / "rules" / "book" / "ai_as_custodian.md"),
                    BookChapter("22. AI Play Notes", ROOT / "rules" / "appendices" / "ai_play.md"),
                ),
            ),
        )
        full_book_input_paths = [
            chapter.path for part in full_book_parts for chapter in part.chapters
        ]
        full_book_end_matter = (
            ROOT / "rules" / "book" / "back_cover_blurb.md",
        )

        bundles["full_book"] = Bundle(
            key="full_book",
            title="Sinew & Steel",
            subtitle="Core Rules, Skins & Starter Scenario",
            input_paths=[*full_book_input_paths, *full_book_end_matter],
            output_base=f"SinewAndSteel_FullBook_v{version}",
            toc=True,
            toc_depth=3,
            number_sections=False,
            variants=("screen", "print"),
            cover_image=Path("assets/covers/ss_cover_book_a4.png"),
            book_parts=full_book_parts,
            end_matter_paths=full_book_end_matter,
        )

    bundles["core_skins"] = Bundle(
        key="core_skins",
        title="Sinew & Steel",
        subtitle="Core Rules & Skins",
        input_paths=[adv, cust] + skin_paths,
        output_base=f"SinewAndSteel_CoreAndSkins_v{version}",
        toc=True,
        number_sections=False,
        variants=("screen", "print"),
        cover_image=Path("assets/covers/ss_cover.png"),
    )

    if quick:
        bundles["quickstart"] = Bundle(
            key="quickstart",
            title="Sinew & Steel",
            subtitle="Quickstart (Rules on Two Pages)",
            input_paths=[quick],
            output_base=f"SinewAndSteel_Quickstart_v{version}",
            toc=False,
            number_sections=False,
            variants=("pdf",),
            suppress_title_block=True,
            content_class="ss-quickstart-standalone",
        )

    bundles["scenario_emberfall"] = Bundle(
        key="scenario_emberfall",
        title="Sinew & Steel",
        subtitle="Clanfire: Emberfall (Starter Scenario)",
        input_paths=[ROOT / "rules" / "scenarios" / "clanfire_emberfall.md"],
        output_base=f"SinewAndSteel_Clanfire_Emberfall_v{version}",
        toc=False,
        number_sections=False,
        variants=("pdf",),
    )

    bundles["ai_appendix"] = Bundle(
        key="ai_appendix",
        title="Sinew & Steel",
        subtitle="Appendix: AI Custodian Play",
        input_paths=[ROOT / "rules" / "appendices" / "ai_play.md"],
        output_base=f"SinewAndSteel_AI_Play_Appendix_v{version}",
        toc=True,
        number_sections=False,
        variants=("pdf",),
    )

    if quick and "clanfire" in skins and "time_odyssey" in skins:
        clanfire_rel = skins["clanfire"].get("file")
        time_odyssey_rel = skins["time_odyssey"].get("file")
        if not clanfire_rel or not time_odyssey_rel:
            print("error: manifest missing skin file for clanfire/time_odyssey", file=sys.stderr)
            raise SystemExit(1)
        bundles["layout_test"] = Bundle(
            key="layout_test",
            title="Sinew & Steel",
            subtitle="Layout Test (Quickstart + Clanfire + Time Odyssey)",
            input_paths=[
                quick,
                ROOT / clanfire_rel,
                ROOT / time_odyssey_rel,
            ],
            output_base=f"SinewAndSteel_LayoutTest_v{version}",
            toc=True,
            number_sections=False,
            variants=("screen", "print"),
            cover_image=Path("assets/covers/ss_cover.png"),
        )

    return bundles
