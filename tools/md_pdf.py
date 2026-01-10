#!/usr/bin/env python3
"""
md_pdf.py

Build an ad-hoc PDF from one or more Markdown files, using the same Pandoc
settings and Lua filters as the release build (wrapfig, headers, etc.).

Also supports an HTML/CSS backend (WeasyPrint) intended to make "text wraps
around image" behavior more predictable than LaTeX wrapfig for complex documents.

This is intended for rapid iteration on layout/art placement, without Fauceting
everything through a fixed "bundle" definition.

Examples:
  python tools/md_pdf.py rules/quickstart.md --out /tmp/quickstart.pdf --style bookish
  python tools/md_pdf.py rules/quickstart.md skins/clanfire.md --out /tmp/test.pdf --toc --style bookish
  python tools/md_pdf.py --files "rules/quickstart.md skins/clanfire.md" --out /tmp/test.pdf
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]

_MD_IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)\]\((\S+?)(\s+\"[^\"]*\")?\)")
_MD_IMAGE_LINK_ANGLE_RE = re.compile(r"!\[([^\]]*)\]\(<([^>]+)>(\s+\"[^\"]*\")?\)")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def tex_engine_available(engine: str) -> bool:
    return shutil.which(engine) is not None


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401

        return True
    except Exception:
        return False


def sanitize_for_pdflatex(text: str) -> str:
    # pdflatex is less forgiving of Unicode than lualatex/xelatex.
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


def normalize_css_font_size(raw: str) -> str:
    """
    Normalize a CLI font size argument to something CSS understands.

    Accepts values like:
      - "11pt" (passed through)
      - "10"   (interpreted as "10pt" for convenience)
      - "0.95em", "12px" (passed through)
    """
    s = raw.strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return f"{s}pt"
    return s


def rewrite_markdown_image_paths(*, text: str, source_path: Path) -> str:
    """
    Rewrite markdown image links so they resolve from repo root.

    Without this, concatenating multiple markdown files breaks relative images,
    because paths become relative to the *combined* temp file instead of each
    source file.
    """

    def rewrite_path(raw: str) -> str:
        if raw.startswith(("http://", "https://", "data:")):
            return raw
        if raw.startswith("#"):
            return raw

        path_part, sep, fragment = raw.partition("#")
        suffix = f"{sep}{fragment}" if sep else ""

        # Support GitHub-style root links like `/assets/...` by treating them as
        # repo-root relative.
        if path_part.startswith("/"):
            candidate = (ROOT / path_part.lstrip("/")).resolve()
        else:
            candidate = (source_path.parent / path_part).resolve()

        try:
            rel = candidate.relative_to(ROOT)
        except ValueError:
            # If the image resolves outside the repo, leave it unchanged.
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


def render_front_matter(title: str | None, subtitle: str | None) -> str:
    if not title and not subtitle:
        return ""
    lines: list[str] = ["---"]
    if title:
        lines.append(f'title: "{title}"')
    if subtitle:
        lines.append(f'subtitle: "{subtitle}"')
    lines += [
        'author: "Barry Brook"',
        f'date: "{datetime.now(timezone.utc).date().isoformat()}"',
        "---",
        "",
    ]
    return "\n".join(lines)


def concatenate_markdown(
    paths: list[Path],
    *,
    title: str | None,
    subtitle: str | None,
    pagebreak_marker: str,
) -> str:
    parts: list[str] = []
    front = render_front_matter(title, subtitle)
    if front:
        parts.append(front.rstrip())
        parts.append("")

    for idx, path in enumerate(paths):
        if idx != 0:
            parts.append(pagebreak_marker)
        text = load_text(path).strip()
        text = rewrite_markdown_image_paths(text=text, source_path=path)
        parts.append(text)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a PDF from one or more Markdown files (ad-hoc).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Markdown file paths (space-separated).",
    )
    parser.add_argument(
        "--files",
        default=None,
        help='Alternative: pass a single quoted string of paths (e.g. "rules/quickstart.md skins/clanfire.md").',
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output PDF path.",
    )
    parser.add_argument("--title", default=None, help="Optional PDF title (adds a title page).")
    parser.add_argument("--subtitle", default=None, help="Optional PDF subtitle.")
    parser.add_argument("--toc", action="store_true", help="Include a table of contents.")
    parser.add_argument("--toc-depth", type=int, default=2, help="TOC depth (default: 2).")
    parser.add_argument(
        "--backend",
        choices=["latex", "weasyprint"],
        default="latex",
        help="PDF backend (default: latex).",
    )
    parser.add_argument(
        "--style",
        choices=["default", "bookish"],
        default="bookish",
        help="Layout preset (default: bookish).",
    )
    parser.add_argument(
        "--pdf-engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default=None,
        help="Pandoc PDF engine (LaTeX backend only; default: depends on --style).",
    )
    parser.add_argument("--mainfont", default=None, help="PDF main font (xelatex/lualatex).")
    parser.add_argument("--sansfont", default=None, help="PDF sans font (xelatex/lualatex).")
    parser.add_argument("--monofont", default=None, help="PDF mono font (xelatex/lualatex).")
    parser.add_argument("--fontsize", default=None, help='PDF font size (e.g. "11pt").')
    parser.add_argument("--linestretch", type=float, default=None, help="PDF line stretch (e.g. 1.05).")
    parser.add_argument("--paper", choices=["letter", "a4"], default="letter", help="Paper size (default: letter).")
    parser.add_argument("--margin", default="1in", help='Page margin (geometry), e.g. "1in".')
    parser.add_argument("--documentclass", default="article", help='LaTeX document class (default: "article").')
    parser.add_argument("--no-wrapfig", action="store_true", help="Disable wrapfig Lua filter.")
    parser.add_argument("--no-headers", action="store_true", help="Disable header include files.")
    parser.add_argument(
        "--keep-md",
        action="store_true",
        help="Keep the combined markdown in release/dist/_intermediate/md_pdf/ for inspection.",
    )
    args = parser.parse_args()

    if not pandoc_available():
        print("error: pandoc not found in PATH", file=sys.stderr)
        return 1

    inputs: list[str] = list(args.inputs or [])
    if args.files:
        try:
            inputs.extend(shlex.split(args.files))
        except ValueError as e:
            print(f"error: could not parse --files: {e}", file=sys.stderr)
            return 1

    if not inputs:
        print("error: no input markdown files provided", file=sys.stderr)
        return 1

    input_paths: list[Path] = []
    for raw in inputs:
        p = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not p.exists():
            print(f"error: missing input file: {raw}", file=sys.stderr)
            return 1
        input_paths.append(p)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (ROOT / out_path).resolve()
    if out_path.suffix.lower() != ".pdf":
        out_path = out_path.with_suffix(".pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    intermediate_dir = ROOT / "release" / "dist" / "_intermediate" / "md_pdf"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    combined_md = intermediate_dir / "combined.md"

    pagebreak_marker = "\n\\newpage\n" if args.backend == "latex" else "\n<div class=\"pagebreak\"></div>\n"
    combined_text = concatenate_markdown(
        input_paths,
        title=args.title,
        subtitle=args.subtitle,
        pagebreak_marker=pagebreak_marker,
    )
    write_text(combined_md, combined_text)

    if args.backend == "latex":
        combined_md_for_pdf = intermediate_dir / "combined_latex.md"

        pdf_engine = args.pdf_engine
        mainfont = args.mainfont
        sansfont = args.sansfont
        monofont = args.monofont
        fontsize = args.fontsize
        linestretch = args.linestretch
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
        else:
            if pdf_engine is None:
                pdf_engine = "pdflatex"
            if fontsize is None:
                fontsize = "11pt"
            if linestretch is None:
                linestretch = None

        if pdf_engine and not tex_engine_available(pdf_engine):
            print(f"error: LaTeX engine '{pdf_engine}' not found in PATH", file=sys.stderr)
            return 1

        md_for_pdf = combined_md
        if pdf_engine == "pdflatex":
            write_text(combined_md_for_pdf, sanitize_for_pdflatex(combined_text))
            md_for_pdf = combined_md_for_pdf

        cmd: list[str] = [
            "pandoc",
            str(md_for_pdf),
            "-o",
            str(out_path),
            # Keep behavior consistent with repo release builds.
            "--from",
            "markdown-blank_before_blockquote",
            f"--resource-path={md_for_pdf.parent}:{ROOT}",
            f"--pdf-engine={pdf_engine}",
            "-V",
            f"documentclass={documentclass}",
            "-V",
            f"fontsize={fontsize}",
            "-V",
            f"geometry:{'letterpaper' if args.paper == 'letter' else 'a4paper'}",
            "-V",
            f"geometry:margin={args.margin}",
        ]

        if linestretch:
            cmd += ["-V", f"linestretch={linestretch}"]
        if mainfont:
            cmd += ["-V", f"mainfont={mainfont}"]
        if sansfont:
            cmd += ["-V", f"sansfont={sansfont}"]
        if monofont:
            cmd += ["-V", f"monofont={monofont}"]

        if not args.no_headers:
            header_images = ROOT / "templates" / "pandoc" / "header_images.tex"
            if header_images.exists():
                cmd += ["--include-in-header", str(header_images)]
            if args.toc:
                header_toc = ROOT / "templates" / "pandoc" / "header_toc_pagebreak.tex"
                if header_toc.exists():
                    cmd += ["--include-in-header", str(header_toc)]

        if not args.no_wrapfig:
            wrapfig_filter = ROOT / "templates" / "pandoc" / "wrapfig.lua"
            if wrapfig_filter.exists():
                cmd += ["--lua-filter", str(wrapfig_filter)]

        if args.toc:
            cmd += ["--toc", f"--toc-depth={args.toc_depth}"]

        subprocess.run(cmd, cwd=ROOT, check=True)

        if not args.keep_md:
            try:
                combined_md_for_pdf.unlink(missing_ok=True)
            except Exception:
                pass
    else:
        if not weasyprint_available():
            venv_python = ROOT / ".venv" / "bin" / "python"
            hint = ""
            if venv_python.exists() and str(venv_python) not in sys.executable:
                hint = (
                    "\nIt looks like you're running system Python, but WeasyPrint may be installed in the repo venv.\n"
                    f"Try:\n  {venv_python} tools/md_pdf.py ... --backend weasyprint\n"
                    "or:\n  uv run python tools/md_pdf.py ... --backend weasyprint\n"
                )
            print(
                "error: WeasyPrint not installed (required for --backend weasyprint).\n\n"
                "Install (suggested):\n"
                "  uv pip install weasyprint\n\n"
                "On Ubuntu you may need system deps (example):\n"
                "  sudo apt-get update\n"
                "  sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0\n",
                file=sys.stderr,
            )
            if hint:
                print(hint, file=sys.stderr)
            return 1

        html_out = intermediate_dir / "combined.html"
        cmd = [
            "pandoc",
            str(combined_md),
            "-o",
            str(html_out),
            "--from",
            "markdown-blank_before_blockquote",
            "--to",
            "html5",
            "--standalone",
            f"--resource-path={combined_md.parent}:{ROOT}",
            "--metadata",
            f"pagetitle={out_path.stem}",
            "--lua-filter",
            str(ROOT / "templates" / "pandoc" / "html_pagebreak.lua"),
        ]
        if args.toc:
            cmd += ["--toc", f"--toc-depth={args.toc_depth}"]

        subprocess.run(cmd, cwd=ROOT, check=True)

        from weasyprint import CSS, HTML

        css_dir = ROOT / "templates" / "html"
        css_path = css_dir / ("bookish.css" if args.style == "bookish" else "default.css")

        stylesheets: list[CSS] = []
        if css_path.exists():
            stylesheets.append(CSS(filename=str(css_path)))

        page_size: Literal["letter", "a4"] = args.paper
        font_overrides = ""
        if args.fontsize:
            font_size_css = normalize_css_font_size(args.fontsize)
            # Pandoc's default HTML template sets a `@media print { body { font-size: 12pt; } }`
            # rule, so we must override `body` (not just `html`) for WeasyPrint PDFs.
            font_overrides += f"body {{ font-size: {font_size_css} !important; }}\n"
        if args.linestretch:
            font_overrides += f"body {{ line-height: {args.linestretch} !important; }}\n"

        runtime_css = f"""
@page {{
  size: {page_size};
  margin: {args.margin};
}}

{font_overrides}

/* Ensure our concatenation marker always breaks pages and clears floats. */
div.pagebreak {{
  break-before: page;
  page-break-before: always;
  clear: both;
}}
"""
        stylesheets.append(CSS(string=runtime_css))

        HTML(filename=str(html_out), base_url=str(ROOT)).write_pdf(str(out_path), stylesheets=stylesheets)

        if not args.keep_md:
            try:
                html_out.unlink(missing_ok=True)
            except Exception:
                pass

    if not args.keep_md:
        try:
            combined_md.unlink(missing_ok=True)
        except Exception:
            pass

    print(f"ok: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
