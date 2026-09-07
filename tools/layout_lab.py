#!/usr/bin/env python3
"""
layout_lab.py

Run a small "lab bench" for Markdown → PDF layout behavior.

This builds each fixture in `examples/layout_lab/fixtures/` with tools/md_pdf.py
(pandoc + WeasyPrint) and can render the PDFs to PNGs for visual inspection.

Example:
  uv run --extra pdf python tools/layout_lab.py --out release/test/layout_lab --render-png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)

def _fixture_paths() -> list[Path]:
    fixtures_dir = ROOT / "examples" / "layout_lab" / "fixtures"
    return sorted(p for p in fixtures_dir.glob("*.md") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build layout lab fixtures to PDFs (and optionally PNGs).")
    parser.add_argument(
        "--out",
        default="release/test/layout_lab",
        help="Output directory (default: release/test/layout_lab).",
    )
    parser.add_argument("--style", choices=["default", "bookish"], default="bookish", help="Style preset.")
    parser.add_argument("--paper", choices=["letter", "a4"], default="letter", help="Paper size.")
    parser.add_argument("--margin", default="1in", help='Page margin (e.g. "1in").')
    parser.add_argument("--render-png", action="store_true", help="Also render PDFs to PNGs via pdftoppm.")
    parser.add_argument("--ppi", type=int, default=160, help="PNG render resolution (default: 160).")
    args = parser.parse_args()

    fixtures = _fixture_paths()
    if not fixtures:
        print("error: no fixtures found under examples/layout_lab/fixtures", file=sys.stderr)
        return 1

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = (ROOT / out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    pdf_dir = out_root / "pdf"
    png_dir = out_root / "png"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    if args.render_png:
        png_dir.mkdir(parents=True, exist_ok=True)

    for fixture in fixtures:
        rel = fixture.relative_to(ROOT).as_posix()
        out_pdf = pdf_dir / f"{fixture.stem}.pdf"
        cmd = [
            sys.executable,
            "tools/md_pdf.py",
            rel,
            "--out",
            str(out_pdf),
            "--style",
            args.style,
            "--paper",
            args.paper,
            "--margin",
            args.margin,
        ]
        try:
            _run(cmd)
        except subprocess.CalledProcessError:
            failures.append(fixture.name)
            continue

        if args.render_png:
            prefix = (png_dir / fixture.stem).as_posix()
            try:
                _run(["pdftoppm", "-png", "-r", str(args.ppi), str(out_pdf), prefix])
            except subprocess.CalledProcessError:
                failures.append(f"{fixture.name}:pdftoppm")

    if failures:
        print("Some builds failed:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 2

    print(f"ok: wrote lab outputs under {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
