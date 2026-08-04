"""PDF renderer used by the release build."""

from __future__ import annotations

from pathlib import Path
import subprocess

from _pdf_common import configure_macos_weasyprint_runtime, normalize_css_font_size

ROOT = Path(__file__).resolve().parents[1]

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
