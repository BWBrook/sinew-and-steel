#!/usr/bin/env python3
"""
suggest_trim.py

Suggest `trim="l b r t"` values for PNG spot art, so wrapped images waste less
space (and so `wrapfigure` needs fewer wrapped lines).

This is an *optional* layout helper intended for maintainers during PDF
iteration; it uses Pillow if installed, but the core harness does not require
Pillow.

Examples:
  # Suggest trim for all spot art.
  python tools/suggest_trim.py

  # Suggest trim for specific files.
  python tools/suggest_trim.py assets/art/ss_roll_under.png assets/art/ss_advantage_disadvantage.png

  # Suggest trim for a subset (glob patterns are repo-root relative).
  python tools/suggest_trim.py --glob "assets/art/ss_*.png" --glob "assets/covers/*.png"

  # Output JSON (machine readable).
  python tools/suggest_trim.py --json

Notes:
  - Units: output includes both pixel counts and TeX dimensions (bp / in).
  - LaTeX `trim` order is: left bottom right top.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


def require_pillow() -> tuple[object, object]:
    try:
        from PIL import Image, ImageChops  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        print(
            "error: Pillow (PIL) is not installed.\n"
            "Install it only if you need layout trim suggestions:\n"
            "  uv add --dev pillow\n"
            "  # or: python -m pip install pillow",
            file=sys.stderr,
        )
        raise
    return Image, ImageChops


def find_image_paths(paths: list[str], globs: list[str]) -> list[Path]:
    if paths:
        resolved: list[Path] = []
        for raw in paths:
            p = Path(raw)
            if not p.is_absolute():
                p = (ROOT / p).resolve()
            if not p.exists():
                raise FileNotFoundError(f"missing file: {raw}")
            resolved.append(p)
        return resolved

    patterns = globs or ["assets/art/*.png"]
    matches: list[Path] = []
    for pat in patterns:
        for p in ROOT.glob(pat):
            if p.is_file():
                matches.append(p.resolve())
    # Deduplicate while preserving sort order.
    uniq: dict[str, Path] = {}
    for p in sorted(matches):
        uniq[str(p)] = p
    return list(uniq.values())


def fmt_dim(value: float, unit: str) -> str:
    if unit not in {"bp", "in"}:
        raise ValueError(f"unsupported unit: {unit}")

    # Make copy/paste nicer: prefer ints when essentially integral.
    if abs(value - round(value)) < 0.05:
        return f"{int(round(value))}{unit}"
    return f"{value:.2f}{unit}"


def bbox_nonwhite(*, img_rgb, Image, ImageChops, white_threshold: int) -> tuple[int, int, int, int] | None:
    """
    Return bbox (left, top, right, bottom) in px, where right/bottom are exclusive.
    """
    w, h = img_rgb.size
    white = Image.new("RGB", (w, h), (255, 255, 255))
    diff = ImageChops.difference(img_rgb, white).convert("L")

    # diff is 0 for pure-white pixels, and higher for darker pixels.
    diff_threshold = max(0, 255 - white_threshold)
    lut = [0] * 256
    for i in range(diff_threshold + 1, 256):
        lut[i] = 255
    mask = diff.point(lut)
    return mask.getbbox()


def open_as_rgb(path: Path, Image) -> tuple[object, tuple[float, float]]:
    """
    Open `path` and return (rgb_image, (dpi_x, dpi_y)).

    If the image is transparent, composite onto white first.
    """
    img = Image.open(path)
    info = getattr(img, "info", {}) or {}

    dpi = info.get("dpi")
    dpi_x = dpi_y = 72.0
    if isinstance(dpi, tuple) and len(dpi) == 2:
        try:
            dpi_x = float(dpi[0]) if float(dpi[0]) > 0 else 72.0
            dpi_y = float(dpi[1]) if float(dpi[1]) > 0 else 72.0
        except Exception:
            dpi_x = dpi_y = 72.0

    # Detect alpha / transparency and composite to white.
    has_alpha = img.mode in {"RGBA", "LA"} or (img.mode == "P" and "transparency" in info)
    if has_alpha:
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rgb = Image.alpha_composite(bg, rgba).convert("RGB")
        return rgb, (dpi_x, dpi_y)

    return img.convert("RGB"), (dpi_x, dpi_y)


def suggest_trim_for_image(
    *,
    path: Path,
    Image,
    ImageChops,
    white_threshold: int,
    pad_px: int,
) -> dict:
    rgb, (dpi_x, dpi_y) = open_as_rgb(path, Image)
    w, h = rgb.size
    bbox = bbox_nonwhite(img_rgb=rgb, Image=Image, ImageChops=ImageChops, white_threshold=white_threshold)

    rel = path.relative_to(ROOT).as_posix()
    payload: dict = {
        "file": rel,
        "size_px": [w, h],
        "dpi": [dpi_x, dpi_y],
        "threshold": white_threshold,
        "pad_px": pad_px,
    }

    if bbox is None:
        payload["note"] = "no non-white pixels detected"
        payload["bbox_px"] = None
        payload["trim_px"] = None
        payload["trim_bp"] = None
        payload["trim_in"] = None
        return payload

    left, top, right, bottom = bbox
    # Convert bbox to trims (LaTeX expects l b r t).
    trim_left_px = left
    trim_top_px = top
    trim_right_px = w - right
    trim_bottom_px = h - bottom

    # Reduce trims by padding (keeps a small margin around the art).
    trim_left_px = max(0, trim_left_px - pad_px)
    trim_top_px = max(0, trim_top_px - pad_px)
    trim_right_px = max(0, trim_right_px - pad_px)
    trim_bottom_px = max(0, trim_bottom_px - pad_px)

    # Convert px -> TeX dimensions.
    #
    # In practice (XeLaTeX + xdvipdfmx), PNG "px" are often treated as if
    # they were at 72dpi when applying `trim=`. Using embedded DPI metadata
    # can produce incorrect crops. So we provide a *recommended* trim string
    # in bp by treating 1px == 1bp, and an equivalent inch value at 72dpi.
    #
    # Keep the raw `dpi` field for debugging, but do not rely on it for trim.
    left_bp = float(trim_left_px)
    right_bp = float(trim_right_px)
    top_bp = float(trim_top_px)
    bottom_bp = float(trim_bottom_px)

    left_in = trim_left_px / 72.0
    right_in = trim_right_px / 72.0
    top_in = trim_top_px / 72.0
    bottom_in = trim_bottom_px / 72.0

    payload["bbox_px"] = [left, top, right, bottom]  # right/bottom are exclusive
    payload["trim_px"] = {"left": trim_left_px, "bottom": trim_bottom_px, "right": trim_right_px, "top": trim_top_px}

    payload["trim_bp"] = f"{fmt_dim(left_bp, 'bp')} {fmt_dim(bottom_bp, 'bp')} {fmt_dim(right_bp, 'bp')} {fmt_dim(top_bp, 'bp')}"
    payload["trim_in"] = f"{fmt_dim(left_in, 'in')} {fmt_dim(bottom_in, 'in')} {fmt_dim(right_in, 'in')} {fmt_dim(top_in, 'in')}"

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest trim values for spot art images (optional maintainer helper).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="Image file paths (repo-relative or absolute).")
    parser.add_argument(
        "--glob",
        action="append",
        default=[],
        help='Glob pattern(s) (repo-root relative). Example: --glob "assets/art/*.png".',
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=250,
        help="White threshold (0-255). Pixels darker than this count as content. Default: 250.",
    )
    parser.add_argument(
        "--pad",
        type=int,
        default=12,
        help="Padding in pixels to keep around detected content (reduces trim). Default: 12.",
    )
    parser.add_argument("--out", default=None, help="Write output YAML/JSON to a file (default: stdout).")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of YAML.")
    args = parser.parse_args()

    if args.threshold < 0 or args.threshold > 255:
        print("error: --threshold must be 0..255", file=sys.stderr)
        return 2
    if args.pad < 0:
        print("error: --pad must be >= 0", file=sys.stderr)
        return 2

    try:
        Image, ImageChops = require_pillow()
    except ModuleNotFoundError:
        return 2

    try:
        image_paths = find_image_paths(args.paths, args.glob)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    suggestions = [
        suggest_trim_for_image(
            path=path,
            Image=Image,
            ImageChops=ImageChops,
            white_threshold=args.threshold,
            pad_px=args.pad,
        )
        for path in image_paths
    ]

    payload = {"schema_version": 1, "generated_from": "tools/suggest_trim.py", "suggestions": suggestions}

    text = ""
    if args.json:
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    else:
        text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = (ROOT / out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"ok: wrote {out_path}")
    else:
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
