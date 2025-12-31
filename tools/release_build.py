#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _preferred_logo_image() -> Path | None:
    # Prefer a dedicated logo if present, otherwise fall back to the icon.
    for rel in (
        Path("assets/covers/ss_logo.png"),
        Path("assets/covers/ss_icon.png"),
    ):
        candidate = ROOT / rel
        if candidate.exists():
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


def concatenate_markdown(paths: list[Path]) -> str:
    parts: list[str] = []
    for idx, path in enumerate(paths):
        if idx != 0:
            parts.append("\n\\newpage\n")
        text = load_text(path).strip()
        try:
            rel = path.resolve().relative_to(ROOT)
        except Exception:
            rel = None
        if rel and rel.parts and rel.parts[0] == "skins" and path.suffix.lower() == ".md":
            logo_rel = _preferred_logo_image()
            if logo_rel is not None:
                text = inject_skin_maker_mark(text, logo_rel=logo_rel).strip()
            text = inject_skin_section_pagebreaks(text).strip()
        text = rewrite_markdown_image_paths(text=text, source_path=path)
        parts.append(text)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


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
        choices=["all", "core_skins", "quickstart", "scenario_emberfall", "ai_appendix", "layout_test"],
        default="all",
        help="Which bundle(s) to build.",
    )
    parser.add_argument("--pdf", action="store_true", help="Also build PDFs (requires pandoc + LaTeX).")
    parser.add_argument(
        "--pdf-engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default=None,
        help="Pandoc PDF engine (default: depends on --style).",
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
        help="PDF paper size (default: letter).",
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

    pdf_engine = args.pdf_engine
    mainfont = args.mainfont
    sansfont = args.sansfont
    monofont = args.monofont
    fontsize = args.fontsize
    linestretch = args.linestretch
    paper = args.paper or "letter"
    margin = args.margin
    documentclass = args.documentclass

    if args.style == "bookish":
        if pdf_engine is None:
            pdf_engine = "xelatex"
        if mainfont is None:
            mainfont = "Linux Libertine O"
        if sansfont is None:
            sansfont = "Linux Biolinum O"
        if monofont is None:
            monofont = "JetBrains Mono"
        if fontsize is None:
            fontsize = "11pt"
        if linestretch is None:
            linestretch = 1.05
        if margin is None:
            margin = "1in"
        if documentclass is None:
            documentclass = "article"
    else:
        if pdf_engine is None:
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
        "out_dir": str(out_dir),
        "bundles": {},
        "pdf_requested": bool(args.pdf),
        "pdf_engine": pdf_engine if args.pdf else None,
        "pdf_style": args.style if args.pdf else None,
        "pdf_mainfont": mainfont if args.pdf else None,
        "pdf_sansfont": sansfont if args.pdf else None,
        "pdf_monofont": monofont if args.pdf else None,
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

    for key in targets:
        bundle = bundles[key]
        for p in bundle.input_paths:
            if not p.exists():
                print(f"error: missing input file for bundle '{key}': {p}", file=sys.stderr)
                return 1

        md_path = intermediate_dir / f"{bundle.output_base}.md"
        content = render_front_matter(bundle.title, bundle.subtitle, version) + concatenate_markdown(bundle.input_paths)
        write_text(md_path, content)

        bundle_result: dict = {"md": str(md_path), "pdf": []}

        if args.pdf:
            md_for_pdf = md_path
            if pdf_engine == "pdflatex":
                md_for_pdf = intermediate_dir / f"{bundle.output_base}_latex.md"
                write_text(md_for_pdf, sanitize_for_pdflatex(content))

            extra_headers: list[Path] = []
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

            if bundle.variants == ("pdf",):
                pdf_path = out_dir / f"{bundle.output_base}.pdf"
                run_pandoc_md_to_pdf(
                    md_path=md_for_pdf,
                    pdf_path=pdf_path,
                    toc=bundle.toc,
                    toc_depth=args.toc_depth,
                    number_sections=bundle.number_sections,
                    variant="screen",
                    pdf_engine=pdf_engine,
                    mainfont=mainfont,
                    sansfont=sansfont,
                    monofont=monofont,
                    fontsize=fontsize,
                    linestretch=linestretch,
                    geometry=geometry,
                    documentclass=documentclass,
                    extra_header_paths=extra_headers,
                )
                bundle_result["pdf"].append(str(pdf_path))
            else:
                for variant in bundle.variants:
                    pdf_path = out_dir / f"{bundle.output_base}_{variant}.pdf"
                    run_pandoc_md_to_pdf(
                        md_path=md_for_pdf,
                        pdf_path=pdf_path,
                        toc=bundle.toc,
                        toc_depth=args.toc_depth,
                        number_sections=bundle.number_sections,
                        variant=variant,
                        pdf_engine=pdf_engine,
                        mainfont=mainfont,
                        sansfont=sansfont,
                        monofont=monofont,
                        fontsize=fontsize,
                        linestretch=linestretch,
                        geometry=geometry,
                        documentclass=documentclass,
                        extra_header_paths=extra_headers,
                    )
                    bundle_result["pdf"].append(str(pdf_path))

        report["bundles"][key] = bundle_result

    (out_dir / "build_report.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")

    if args.json:
        import json

        print(json.dumps(report, indent=2))
    else:
        print(f"ok: built {len(targets)} bundle(s) in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
