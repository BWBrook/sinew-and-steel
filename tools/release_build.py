#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import yaml

from _pdf_common import (
    default_bookish_fonts,
    load_text,
    pandoc_available,
    sanitize_for_pdflatex,
    tex_engine_available,
    weasyprint_available,
    write_text,
)
from _pdf_render import run_pandoc_md_to_pdf, run_pandoc_md_to_weasyprint_pdf
from _release_content import (
    bundle_definitions,
    concatenate_book_parts,
    concatenate_end_matter,
    concatenate_markdown,
    cover_header_tex,
    render_front_matter,
    suppress_title_block_tex,
    wrap_markdown_div,
)

ROOT = Path(__file__).resolve().parents[1]


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


def build_bundle(
    bundle,
    *,
    key: str,
    version: str,
    out_dir: Path,
    intermediate_dir: Path,
    pdf_requested: bool,
    pdf_backend: str,
    pdf_engine: str | None,
    style: str,
    paper: str,
    margin: str | None,
    mainfont: str | None,
    sansfont: str | None,
    monofont: str | None,
    fontsize: str | None,
    linestretch: float | None,
    geometry: list[str],
    documentclass: str,
    toc_depth: int,
) -> dict | None:
    for p in bundle.input_paths:
        if not p.exists():
            print(f"error: missing input file for bundle '{key}': {p}", file=sys.stderr)
            return None

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

    effective_toc_depth = bundle.toc_depth if bundle.toc_depth is not None else toc_depth
    bundle_result: dict = {
        "md": report_path(md_path),
        "pdf": [],
        "toc_depth": effective_toc_depth if bundle.toc else None,
    }

    if pdf_requested:
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
                    style=style,
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
                        style=style,
                        paper=paper,
                        margin=margin or "1in",
                        fontsize=fontsize,
                        linestretch=linestretch,
                        suppress_title_block=bool(bundle.cover_image or bundle.suppress_title_block),
                        include_before_body=cover_include,
                    )
                bundle_result["pdf"].append(report_path(pdf_path))

    return bundle_result

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

    bundles = bundle_definitions(manifest, version)
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
        bundle_result = build_bundle(
            bundles[key],
            key=key,
            version=version,
            out_dir=out_dir,
            intermediate_dir=intermediate_dir,
            pdf_requested=bool(args.pdf),
            pdf_backend=pdf_backend,
            pdf_engine=pdf_engine,
            style=args.style,
            paper=paper,
            margin=margin,
            mainfont=mainfont,
            sansfont=sansfont,
            monofont=monofont,
            fontsize=fontsize,
            linestretch=linestretch,
            geometry=geometry,
            documentclass=documentclass,
            toc_depth=args.toc_depth,
        )
        if bundle_result is None:
            return 1
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
