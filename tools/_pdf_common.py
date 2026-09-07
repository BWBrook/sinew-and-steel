"""Shared PDF-tooling primitives."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]

_MD_IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)\]\(([^<\s]\S*?)(\s+\"[^\"]*\")?\)")
_MD_IMAGE_LINK_ANGLE_RE = re.compile(r"!\[([^\]]*)\]\(<([^>]+)>(\s+\"[^\"]*\")?\)")



def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None



def configure_macos_weasyprint_runtime() -> None:
    """Expose Homebrew's library directory to WeasyPrint on macOS."""
    if platform.system() != "Darwin":
        return

    brew_lib = Path("/opt/homebrew/lib")
    if not brew_lib.exists():
        return

    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    paths = [path for path in current.split(":") if path]
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
    value = raw.strip()
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return f"{value}pt"
    return value



def rewrite_markdown_image_paths(*, text: str, source_path: Path) -> str:
    """Resolve image links relative to their source Markdown file."""

    def rewrite_path(raw: str) -> str:
        if raw.startswith(("http://", "https://", "data:")) or raw.startswith("#"):
            return raw

        path_part, separator, fragment = raw.partition("#")
        suffix = f"{separator}{fragment}" if separator else ""
        if path_part.startswith("/"):
            candidate = (ROOT / path_part.lstrip("/")).resolve()
        else:
            candidate = (source_path.parent / path_part).resolve()

        try:
            relative = candidate.relative_to(ROOT)
        except ValueError:
            return raw
        return relative.as_posix() + suffix

    def replace_parenthesized(match: re.Match) -> str:
        alt = match.group(1)
        path = match.group(2)
        title = match.group(3) or ""
        return f"![{alt}]({rewrite_path(path)}{title})"

    def replace_angled(match: re.Match) -> str:
        alt = match.group(1)
        path = match.group(2)
        title = match.group(3) or ""
        return f"![{alt}](<{rewrite_path(path)}>{title})"

    text = _MD_IMAGE_LINK_ANGLE_RE.sub(replace_angled, text)
    return _MD_IMAGE_LINK_RE.sub(replace_parenthesized, text)
