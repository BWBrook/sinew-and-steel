#!/usr/bin/env python3
"""
md_pdf.py

Build an ad-hoc PDF from one or more Markdown files with pandoc and WeasyPrint,
using the same stylesheet and page-break filter as the release build. Intended
for rapid iteration on layout and art placement without going through a bundle
definition.

Examples:
  uv run --extra pdf python tools/md_pdf.py rules/quickstart.md --out /tmp/quickstart.pdf
  uv run --extra pdf python tools/md_pdf.py rules/quickstart.md skins/clanfire.md --out /tmp/test.pdf --toc
  uv run --extra pdf python tools/md_pdf.py --files "rules/quickstart.md skins/clanfire.md" --out /tmp/test.pdf
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Literal

from _pdf_common import (
    configure_macos_weasyprint_runtime,
    load_text,
    normalize_css_font_size,
    pandoc_available,
    rewrite_markdown_image_paths,
    weasyprint_available,
    write_text,
)

ROOT = Path(__file__).resolve().parents[1]


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


def build_weasyprint_pdf(
    args,
    combined_md: Path,
    out_path: Path,
    intermediate_dir: Path,
) -> bool:
    configure_macos_weasyprint_runtime()

    if not weasyprint_available():
        venv_python = ROOT / ".venv" / "bin" / "python"
        hint = ""
        if venv_python.exists() and str(venv_python) not in sys.executable:
            hint = (
                "\nIt looks like you're running system Python, but WeasyPrint may be installed in the repo venv.\n"
                "Try:\n  uv run --extra pdf python tools/md_pdf.py ...\n"
            )
        print(
            "error: WeasyPrint not installed (uv sync --extra pdf).\n\n"
            "Install (suggested):\n"
            "  uv sync --extra pdf\n\n"
            "On Ubuntu you may need system deps (example):\n"
            "  sudo apt-get update\n"
            "  sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0\n",
            file=sys.stderr,
        )
        if hint:
            print(hint, file=sys.stderr)
        return False

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
    return True

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
        "--style",
        choices=["default", "bookish"],
        default="bookish",
        help="Layout preset (default: bookish).",
    )
    parser.add_argument("--fontsize", default=None, help='PDF font size (e.g. "11pt").')
    parser.add_argument("--linestretch", type=float, default=None, help="PDF line stretch (e.g. 1.05).")
    parser.add_argument("--paper", choices=["letter", "a4"], default="a4", help="Paper size (default: a4).")
    parser.add_argument("--margin", default="1in", help='Page margin, e.g. "1in" or "0.6in 0.8in".')
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

    pagebreak_marker = "\n<div class=\"pagebreak\"></div>\n"
    combined_text = concatenate_markdown(
        input_paths,
        title=args.title,
        subtitle=args.subtitle,
        pagebreak_marker=pagebreak_marker,
    )
    write_text(combined_md, combined_text)

    if not build_weasyprint_pdf(args, combined_md, out_path, intermediate_dir):
        return 1
    if not args.keep_md:
        try:
            combined_md.unlink(missing_ok=True)
        except Exception:
            pass

    print(f"ok: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
