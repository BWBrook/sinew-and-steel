#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def default_bookish_fonts() -> tuple[str, str, str]:
    # Match `tools/md_pdf.py` so ad-hoc PDFs and official release builds behave
    # the same on macOS vs Linux.
    if platform.system() == "Darwin":
        return ("Palatino", "Helvetica", "Menlo")
    return ("Linux Libertine O", "Linux Biolinum O", "JetBrains Mono")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def report_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        raise SystemExit(1)
    return yaml.safe_load(load_text(manifest_path)) or {}


def load_version() -> str:
    version_path = ROOT / "VERSION"
    if not version_path.exists():
        print(f"error: missing VERSION file: {version_path}", file=sys.stderr)
        raise SystemExit(1)
    return load_text(version_path).strip()


def git_head() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


def ensure_versions_match(manifest: dict, version: str) -> None:
    manifest_version = str(manifest.get("version", "")).strip()
    if manifest_version and manifest_version != version:
        print(
            f"error: version mismatch (VERSION={version}, manifest.yaml version={manifest_version})",
            file=sys.stderr,
        )
        raise SystemExit(1)


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def tex_engine_available(engine: str) -> bool:
    return shutil.which(engine) is not None


def configure_macos_weasyprint_runtime() -> None:
    """
    On Apple Silicon Macs, Homebrew libraries live under /opt/homebrew/lib.
    WeasyPrint's CFFI loader doesn't always see that path by default, so expose
    it before importing the backend.
    """
    if platform.system() != "Darwin":
        return

    brew_lib = Path("/opt/homebrew/lib")
    if not brew_lib.exists():
        return

    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    paths = [p for p in current.split(":") if p]
    brew_lib_str = str(brew_lib)
    if brew_lib_str not in paths:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            f"{brew_lib_str}:{current}" if current else brew_lib_str
        )


def weasyprint_available() -> bool:
    configure_macos_weasyprint_runtime()
    try:
        import weasyprint  # noqa: F401

        return True
    except Exception:
        return False


def normalize_css_font_size(raw: str) -> str:
    s = raw.strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"{s}pt"
    return s


def sanitize_for_pdflatex(text: str) -> str:
    # pdflatex is less forgiving of Unicode than lualatex/xelatex.
    # We keep source markdown “pretty”, but sanitize the release build input so
    # the pipeline works on minimal TeX installs.
    replacements = {
        "\u00a0": " ",  # nbsp
        "\u2002": " ",  # en space
        "\u2003": " ",  # em space
        "\u2009": " ",  # thin space
        "\u202f": " ",  # narrow no-break space
        "≤": "<=",
        "≥": ">=",
        "→": "->",
        "⇒": "=>",
        "•": "-",
        "—": "--",
        "–": "-",
        "‑": "-",
        "−": "-",
        "≈": "~",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


_SKIN_CUSTODIAN_HEADING_RE = re.compile(r"^##\s+.*\bCustodian\b", re.IGNORECASE)
_SKIN_SAMPLE_HEADING_RE = re.compile(r"^##\s+.*\b(?:SAMPLE|EXAMPLE|ACTIVE|FIGURES)\b", re.IGNORECASE)
_MD_IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)\]\((\S+?)(\s+\"[^\"]*\")?\)")
_MD_IMAGE_LINK_ANGLE_RE = re.compile(r"!\[([^\]]*)\]\(<([^>]+)>(\s+\"[^\"]*\")?\)")


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


def cover_header_tex(*, cover_rel: Path) -> str:
    cover_posix = cover_rel.as_posix()
    # Override Pandoc's \maketitle with a full-page cover image.
    # This keeps the cover page before the TOC without custom templates.
    return "\n".join(
        [
            "% Auto-generated by tools/release_build.py",
            "\\usepackage{graphicx}",
            "\\usepackage{eso-pic}",
            "\\makeatletter",
            "\\renewcommand{\\maketitle}{%",
            "  \\thispagestyle{empty}%",
            # The outer parbox must be baseline-aligned to the *bottom* of the page.
            # If we use [c] here, TeX centers the box around the baseline and we end up
            # with a “half off-page” cover.
            "  \\AddToShipoutPictureBG*{\\AtPageLowerLeft{\\parbox[b][\\paperheight][c]{\\paperwidth}{\\centering%",
            f"    \\includegraphics[width=\\paperwidth,height=\\paperheight,keepaspectratio]{{{cover_posix}}}%",
            "  }}}%",
            "  \\null%",
            "}",
            "\\makeatother",
            "",
        ]
    )


def suppress_title_block_tex() -> str:
    # Keep PDF metadata (title/author/date) but suppress the rendered title
    # block. Useful for documents that already include their own headline,
    # such as the “Rules on Two Pages” quickstart.
    return "\n".join(
        [
            "% Auto-generated by tools/release_build.py",
            "\\makeatletter",
            "\\renewcommand{\\maketitle}{}",
            "\\makeatother",
            "",
        ]
    )


def rewrite_markdown_image_paths(*, text: str, source_path: Path) -> str:
    def rewrite_path(raw: str) -> str:
        if raw.startswith(("http://", "https://", "data:")):
            return raw
        if raw.startswith("#"):
            return raw

        path_part, sep, fragment = raw.partition("#")
        suffix = f"{sep}{fragment}" if sep else ""

        # Support GitHub-style root links like `/assets/...` by treating them as
        # repo-root relative for release builds.
        if path_part.startswith("/"):
            candidate = (ROOT / path_part.lstrip("/")).resolve()
        else:
            candidate = (source_path.parent / path_part).resolve()

        try:
            rel = candidate.relative_to(ROOT)
        except ValueError:
            return raw

        return rel.as_posix() + suffix

    def repl_paren(match: re.Match) -> str:
        alt = match.group(1)
        path = match.group(2)
        title = match.group(3) or ""
        return f"![{alt}]({rewrite_path(path)}{title})"

    def repl_angle(match: re.Match) -> str:
        alt = match.group(1)
        path = match.group(2)
        title = match.group(3) or ""
        return f"![{alt}](<{rewrite_path(path)}>{title})"

    text = _MD_IMAGE_LINK_ANGLE_RE.sub(repl_angle, text)
    text = _MD_IMAGE_LINK_RE.sub(repl_paren, text)
    return text


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


def run_pandoc_md_to_pdf(
    *,
    md_path: Path,
    pdf_path: Path,
    toc: bool,
    toc_depth: int,
    number_sections: bool,
    variant: str,
    pdf_engine: str,
    mainfont: str | None,
    sansfont: str | None,
    monofont: str | None,
    fontsize: str | None,
    linestretch: float | None,
    geometry: list[str],
    documentclass: str | None,
    extra_header_paths: list[Path] | None = None,
) -> None:
    cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(pdf_path),
        f"--resource-path={md_path.parent}:{ROOT}",
        # Pandoc enables `blank_before_blockquote` by default, which means a
        # line starting with `>` will NOT start a blockquote if it immediately
        # follows a paragraph. That’s a common authoring “papercut” (especially
        # for patterns like `**Micro‑vignette:**` followed by a quote).
        #
        # Disable it so `>` behaves like most people expect.
        "--from",
        "markdown-blank_before_blockquote",
        f"--pdf-engine={pdf_engine}",
    ]

    header_images = ROOT / "templates" / "pandoc" / "header_images.tex"
    if header_images.exists():
        cmd += ["--include-in-header", str(header_images)]

    wrapfig_filter = ROOT / "templates" / "pandoc" / "wrapfig.lua"
    if wrapfig_filter.exists():
        cmd += ["--lua-filter", str(wrapfig_filter)]

    if extra_header_paths:
        for header in extra_header_paths:
            if header.exists():
                cmd += ["--include-in-header", str(header)]

    if toc:
        header_path = ROOT / "templates" / "pandoc" / "header_toc_pagebreak.tex"
        if header_path.exists():
            cmd += ["--include-in-header", str(header_path)]
        cmd += ["--toc", f"--toc-depth={toc_depth}"]
    if number_sections:
        cmd += ["--number-sections"]

    if documentclass:
        cmd += ["-V", f"documentclass={documentclass}"]
    if fontsize:
        cmd += ["-V", f"fontsize={fontsize}"]
    if linestretch:
        cmd += ["-V", f"linestretch={linestretch}"]
    if mainfont:
        cmd += ["-V", f"mainfont={mainfont}"]
    if sansfont:
        cmd += ["-V", f"sansfont={sansfont}"]
    if monofont:
        cmd += ["-V", f"monofont={monofont}"]
    for opt in geometry:
        cmd += ["-V", f"geometry:{opt}"]

    # Keep variants simple for now; we can refine templates later.
    if variant == "screen":
        cmd += ["-V", "colorlinks=true", "-V", "linkcolor=blue", "-V", "urlcolor=blue"]
    elif variant == "print":
        cmd += ["-V", "colorlinks=false"]

    subprocess.run(cmd, cwd=ROOT, check=True)


def cover_html_block(*, cover_rel: Path) -> str:
    cover_posix = cover_rel.as_posix()
    return "\n".join(
        [
            '<section class="ss-cover-page" aria-label="Cover">',
            f'  <img src="{cover_posix}" alt="Sinew & Steel cover" />',
            "</section>",
            "",
        ]
    )


def run_pandoc_md_to_weasyprint_pdf(
    *,
    md_path: Path,
    pdf_path: Path,
    toc: bool,
    toc_depth: int,
    number_sections: bool,
    variant: str,
    style: str,
    paper: str,
    margin: str,
    fontsize: str | None,
    linestretch: float | None,
    suppress_title_block: bool,
    include_before_body: Path | None = None,
) -> None:
    html_path = md_path.parent / f"{pdf_path.stem}.html"
    cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(html_path),
        "--from",
        "markdown-blank_before_blockquote",
        "--to",
        "html5",
        "--standalone",
        f"--resource-path={md_path.parent}:{ROOT}",
        "--metadata",
        f"pagetitle={pdf_path.stem}",
        "--lua-filter",
        str(ROOT / "templates" / "pandoc" / "html_pagebreak.lua"),
    ]

    if suppress_title_block:
        cmd += [
            "--metadata",
            "title=",
            "--metadata",
            "subtitle=",
            "--metadata",
            "author=",
            "--metadata",
            "date=",
        ]
    if include_before_body and include_before_body.exists():
        cmd += ["--include-before-body", str(include_before_body)]
    if toc:
        cmd += ["--toc", f"--toc-depth={toc_depth}"]
    if number_sections:
        cmd += ["--number-sections"]

    subprocess.run(cmd, cwd=ROOT, check=True)

    configure_macos_weasyprint_runtime()
    from weasyprint import CSS, HTML

    css_dir = ROOT / "templates" / "html"
    css_path = css_dir / ("bookish.css" if style == "bookish" else "default.css")

    stylesheets: list[CSS] = []
    if css_path.exists():
        stylesheets.append(CSS(filename=str(css_path)))

    font_overrides = ""
    if fontsize:
        font_size_css = normalize_css_font_size(fontsize)
        font_overrides += f"body {{ font-size: {font_size_css} !important; }}\n"
    if linestretch:
        font_overrides += f"body {{ line-height: {linestretch} !important; }}\n"

    link_css = ""
    if variant == "screen":
        link_css = "a { color: #2459a6; }\n"
    elif variant == "print":
        link_css = "a { color: inherit; text-decoration: none; }\n"

    runtime_css = f"""
@page {{
  size: {paper};
  margin: {margin};

  @top-center {{
    content: "";
    width: 100%;
    height: 0.18in;
    margin-bottom: 0.16in;
    border-bottom: 0.35pt solid #c7c7c7;
  }}

  @bottom-center {{
    content: counter(page);
    width: 100%;
    margin-top: 0.16in;
    padding-top: 0.045in;
    border-top: 0.35pt solid #c7c7c7;
    color: #555;
    font-size: 8.5pt;
    font-variant-numeric: tabular-nums;
  }}
}}

@page ss-cover {{
  size: {paper};
  margin: 0;

  @top-center {{
    content: none;
  }}

  @bottom-center {{
    content: none;
  }}
}}

@page ss-back-cover {{
  size: {paper};
  margin: {margin};

  @top-center {{
    content: none;
  }}

  @bottom-center {{
    content: none;
  }}
}}

{font_overrides}
{link_css}

section.ss-cover-page {{
  page: ss-cover;
  break-after: page;
  page-break-after: always;
  height: 100vh;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}}

section.ss-cover-page img {{
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}}

div.pagebreak {{
  break-before: page;
  page-break-before: always;
  clear: both;
}}

.ss-back-cover-blurb {{
  page: ss-back-cover;
}}
"""
    stylesheets.append(CSS(string=runtime_css))

    HTML(filename=str(html_path), base_url=str(ROOT)).write_pdf(
        str(pdf_path),
        stylesheets=stylesheets,
    )


def bundle_definitions(manifest: dict, version: str, out_dir: Path) -> dict[str, Bundle]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build release bundles (markdown + optional PDFs) into release/dist/.")
    parser.add_argument(
        "--out-dir",
        default="release/dist",
        help="Output directory (default: release/dist).",
    )
    parser.add_argument(
        "--bundle",
        choices=["all", "full_book", "core_skins", "quickstart", "scenario_emberfall", "ai_appendix", "layout_test"],
        default="all",
        help="Which bundle(s) to build.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also build PDFs (requires pandoc + selected backend).",
    )
    parser.add_argument(
        "--backend",
        choices=["weasyprint", "latex"],
        default="weasyprint",
        help="PDF backend for --pdf (default: weasyprint).",
    )
    parser.add_argument(
        "--pdf-engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default=None,
        help="Pandoc PDF engine for --backend latex (default: depends on --style).",
    )
    parser.add_argument(
        "--style",
        choices=["default", "bookish"],
        default="default",
        help="Layout preset (default: default).",
    )
    parser.add_argument("--mainfont", default=None, help="PDF main font (xelatex/lualatex).")
    parser.add_argument("--sansfont", default=None, help="PDF sans font (xelatex/lualatex).")
    parser.add_argument("--monofont", default=None, help="PDF mono font (xelatex/lualatex).")
    parser.add_argument(
        "--fontsize",
        default=None,
        help='PDF font size (e.g. "10pt", "11pt", "12pt").',
    )
    parser.add_argument(
        "--linestretch",
        type=float,
        default=None,
        help="PDF line stretch (e.g. 1.05).",
    )
    parser.add_argument(
        "--paper",
        choices=["letter", "a4"],
        default=None,
        help="PDF paper size (default: a4).",
    )
    parser.add_argument(
        "--margin",
        default=None,
        help='PDF margin (geometry), e.g. "1in" or "0.9in".',
    )
    parser.add_argument(
        "--documentclass",
        default=None,
        help='LaTeX document class (e.g. "article", "book").',
    )
    parser.add_argument(
        "--toc-depth",
        type=int,
        default=2,
        help="TOC depth when enabled (default: 2).",
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary.")
    args = parser.parse_args()

    pdf_backend = args.backend
    pdf_engine = args.pdf_engine
    mainfont = args.mainfont
    sansfont = args.sansfont
    monofont = args.monofont
    fontsize = args.fontsize
    linestretch = args.linestretch
    paper = args.paper or "a4"
    margin = args.margin
    documentclass = args.documentclass

    if args.style == "bookish":
        if pdf_backend == "latex" and pdf_engine is None:
            pdf_engine = "xelatex"
        default_mainfont, default_sansfont, default_monofont = default_bookish_fonts()
        if pdf_backend == "latex" and mainfont is None:
            mainfont = default_mainfont
        if pdf_backend == "latex" and sansfont is None:
            sansfont = default_sansfont
        if pdf_backend == "latex" and monofont is None:
            monofont = default_monofont
        if fontsize is None:
            fontsize = "11pt"
        if linestretch is None:
            linestretch = 1.12
        if margin is None:
            margin = "1in"
        if documentclass is None:
            documentclass = "article"
    else:
        if pdf_backend == "latex" and pdf_engine is None:
            pdf_engine = "pdflatex"
        if fontsize is None:
            fontsize = "11pt"
        if margin is None:
            margin = "1in"
        if documentclass is None:
            documentclass = "article"

    geometry: list[str] = ["letterpaper" if paper == "letter" else "a4paper"]
    if margin:
        geometry.append(f"margin={margin}")

    manifest = load_manifest()
    version = load_version()
    ensure_versions_match(manifest, version)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir = out_dir / "_intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    bundles = bundle_definitions(manifest, version, out_dir)
    targets = list(bundles.keys()) if args.bundle == "all" else [args.bundle]

    report: dict = {
        "ok": True,
        "version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "out_dir": report_path(out_dir),
        "bundles": {},
        "pdf_requested": bool(args.pdf),
        "pdf_backend": pdf_backend if args.pdf else None,
        "pdf_engine": pdf_engine if args.pdf and pdf_backend == "latex" else None,
        "pdf_style": args.style if args.pdf else None,
        "pdf_mainfont": mainfont if args.pdf and pdf_backend == "latex" else None,
        "pdf_sansfont": sansfont if args.pdf and pdf_backend == "latex" else None,
        "pdf_monofont": monofont if args.pdf and pdf_backend == "latex" else None,
        "pdf_fontsize": fontsize if args.pdf else None,
        "pdf_linestretch": linestretch if args.pdf else None,
        "pdf_paper": paper if args.pdf else None,
        "pdf_margin": margin if args.pdf else None,
        "pdf_documentclass": documentclass if args.pdf else None,
        "toc_depth": args.toc_depth,
    }

    if args.pdf and not pandoc_available():
        print("error: pandoc not found in PATH; install pandoc or omit --pdf", file=sys.stderr)
        return 1
    if args.pdf and pdf_backend == "weasyprint" and not weasyprint_available():
        print(
            "error: WeasyPrint not installed (required for --backend weasyprint).\n\n"
            "Install (suggested):\n"
            "  uv sync --extra pdf\n\n"
            "On macOS, also ensure the image loader is installed:\n"
            "  brew install gdk-pixbuf\n",
            file=sys.stderr,
        )
        return 1
    if args.pdf and pdf_backend == "latex" and pdf_engine and not tex_engine_available(pdf_engine):
        print(f"error: LaTeX engine '{pdf_engine}' not found in PATH", file=sys.stderr)
        return 1

    for key in targets:
        bundle = bundles[key]
        for p in bundle.input_paths:
            if not p.exists():
                print(f"error: missing input file for bundle '{key}': {p}", file=sys.stderr)
                return 1

        md_path = intermediate_dir / f"{bundle.output_base}.md"
        body = (
            concatenate_book_parts(bundle.book_parts)
            if bundle.book_parts
            else concatenate_markdown(bundle.input_paths)
        )
        if bundle.end_matter_paths:
            body = body.rstrip() + "\n" + concatenate_end_matter(bundle.end_matter_paths)
        body = wrap_markdown_div(body, bundle.content_class)
        content = render_front_matter(bundle.title, bundle.subtitle, version) + body
        write_text(md_path, content)

        effective_toc_depth = bundle.toc_depth if bundle.toc_depth is not None else args.toc_depth
        bundle_result: dict = {
            "md": report_path(md_path),
            "pdf": [],
            "toc_depth": effective_toc_depth if bundle.toc else None,
        }

        if args.pdf:
            md_for_pdf = md_path
            if pdf_backend == "latex" and pdf_engine == "pdflatex":
                md_for_pdf = intermediate_dir / f"{bundle.output_base}_latex.md"
                write_text(md_for_pdf, sanitize_for_pdflatex(content))

            extra_headers: list[Path] = []
            if pdf_backend == "latex":
                if bundle.cover_image:
                    cover_abs = ROOT / bundle.cover_image
                    if cover_abs.exists():
                        cover_header = intermediate_dir / f"{bundle.output_base}_cover.tex"
                        write_text(cover_header, cover_header_tex(cover_rel=bundle.cover_image))
                        extra_headers.append(cover_header)

                if bundle.suppress_title_block:
                    suppress_header = intermediate_dir / f"{bundle.output_base}_no_title.tex"
                    write_text(suppress_header, suppress_title_block_tex())
                    extra_headers.append(suppress_header)
            else:
                cover_include: Path | None = None
                if bundle.cover_image and (ROOT / bundle.cover_image).exists():
                    cover_include = intermediate_dir / f"{bundle.output_base}_cover.html"
                    write_text(cover_include, cover_html_block(cover_rel=bundle.cover_image))
                md_for_pdf = intermediate_dir / f"{bundle.output_base}_weasyprint.md"
                write_text(md_for_pdf, content)

            if bundle.variants == ("pdf",):
                pdf_path = out_dir / f"{bundle.output_base}.pdf"
                if pdf_backend == "latex":
                    run_pandoc_md_to_pdf(
                        md_path=md_for_pdf,
                        pdf_path=pdf_path,
                        toc=bundle.toc,
                        toc_depth=effective_toc_depth,
                        number_sections=bundle.number_sections,
                        variant="screen",
                        pdf_engine=pdf_engine or "pdflatex",
                        mainfont=mainfont,
                        sansfont=sansfont,
                        monofont=monofont,
                        fontsize=fontsize,
                        linestretch=linestretch,
                        geometry=geometry,
                        documentclass=documentclass,
                        extra_header_paths=extra_headers,
                    )
                else:
                    run_pandoc_md_to_weasyprint_pdf(
                        md_path=md_for_pdf,
                        pdf_path=pdf_path,
                        toc=bundle.toc,
                        toc_depth=effective_toc_depth,
                        number_sections=bundle.number_sections,
                        variant="screen",
                        style=args.style,
                        paper=paper,
                        margin=margin or "1in",
                        fontsize=fontsize,
                        linestretch=linestretch,
                        suppress_title_block=bool(bundle.cover_image or bundle.suppress_title_block),
                        include_before_body=cover_include,
                    )
                bundle_result["pdf"].append(report_path(pdf_path))
            else:
                for variant in bundle.variants:
                    pdf_path = out_dir / f"{bundle.output_base}_{variant}.pdf"
                    if pdf_backend == "latex":
                        run_pandoc_md_to_pdf(
                            md_path=md_for_pdf,
                            pdf_path=pdf_path,
                            toc=bundle.toc,
                            toc_depth=effective_toc_depth,
                            number_sections=bundle.number_sections,
                            variant=variant,
                            pdf_engine=pdf_engine or "pdflatex",
                            mainfont=mainfont,
                            sansfont=sansfont,
                            monofont=monofont,
                            fontsize=fontsize,
                            linestretch=linestretch,
                            geometry=geometry,
                            documentclass=documentclass,
                            extra_header_paths=extra_headers,
                        )
                    else:
                        run_pandoc_md_to_weasyprint_pdf(
                            md_path=md_for_pdf,
                            pdf_path=pdf_path,
                            toc=bundle.toc,
                            toc_depth=effective_toc_depth,
                            number_sections=bundle.number_sections,
                            variant=variant,
                            style=args.style,
                            paper=paper,
                            margin=margin or "1in",
                            fontsize=fontsize,
                            linestretch=linestretch,
                            suppress_title_block=bool(bundle.cover_image or bundle.suppress_title_block),
                            include_before_body=cover_include,
                        )
                    bundle_result["pdf"].append(report_path(pdf_path))

        report["bundles"][key] = bundle_result

    (out_dir / "build_report.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")

    if args.json:
        import json

        print(json.dumps(report, indent=2))
    else:
        print(f"ok: built {len(targets)} bundle(s) in {report_path(out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
