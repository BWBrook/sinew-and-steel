"""The Quickstart's physical two-page spread is a release gate."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from _release_content import Bundle
import release_build


SOURCE = """# Pocket rules

## 1. Core engine
Roll a die.

## 2. Skins
Choose a skin.

## 3. For the Custodian
State the stakes.

## 4. Example character
Tag: Field naturalist
"""
FIRST = "Pocket rules\n1. Core engine\nRoll a die.\n1"
SECOND = "2. Skins\nChoose a skin.\n3. For the Custodian\nState the stakes.\n4. Example character\nTag: Field naturalist\n2"


class QuickstartReleaseContractTests(unittest.TestCase):
    def test_standalone_requires_two_pages_and_both_content_boundaries(self):
        self.assertEqual(release_build.check_quickstart_pages([FIRST, SECOND], SOURCE)["quickstart_pages"], [1, 2])
        failures = ([FIRST], [FIRST, SECOND, "overflow"], [FIRST, "empty"], [FIRST.replace("1. Core engine", ""), SECOND])
        for pages in failures:
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                release_build.check_quickstart_pages(pages, SOURCE)

    def test_full_book_requires_pages_six_and_seven_followed_by_next_chapter(self):
        pages = ["cover", "Contents\n2. Quickstart 6\n3. The Adventurer 8", "contents", "preface", "preface", FIRST.replace("Pocket rules", "2. Quickstart"), SECOND, "CORE RULES\n3. The Adventurer"]
        options = dict(chapter_title="2. Quickstart", next_chapter_title="3. The Adventurer")
        checked = release_build.check_quickstart_pages(pages, SOURCE, **options)
        self.assertEqual(checked["quickstart_pages"], [6, 7])
        for bad in (["extra cover"] + pages, pages[:7] + ["overflow"] + pages[7:], pages[:6] + [SECOND.replace("Tag: Field naturalist", "")] + pages[7:]):
            with self.subTest(pages=bad), self.assertRaises(ValueError):
                release_build.check_quickstart_pages(bad, SOURCE, **options)

    def test_heading_match_ignores_whitespace_and_pdf_ligatures(self):
        pages = [FIRST.replace("Core engine", "Core   engine"), SECOND.replace("Field", "ﬁeld")]
        self.assertTrue(release_build.check_quickstart_pages(pages, SOURCE)["ok"])

    def test_saved_pdf_is_read_and_trailing_form_feed_is_not_an_extra_page(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "quickstart.md"
            source.write_text(SOURCE, encoding="utf-8")
            pdf = root / "quickstart.pdf"
            bundle = Bundle("quickstart", "Pocket rules", "Two pages", [source], "quickstart")
            completed = subprocess.CompletedProcess([], 0, f"{FIRST}\f{SECOND}\f", "")
            with patch.object(release_build.shutil, "which", return_value="pdftotext"), patch.object(release_build.subprocess, "run", return_value=completed) as extractor:
                checked = release_build.check_quickstart_pdf(pdf, bundle=bundle, key="quickstart")
            self.assertEqual(checked["pdf_pages"], 2)
            self.assertEqual(extractor.call_args.args[0], ["pdftotext", "-layout", str(pdf), "-"])

    def test_gate_failure_prevents_a_successful_release_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "quickstart.md"
            source.write_text(SOURCE, encoding="utf-8")
            bundle = Bundle("quickstart", "Pocket rules", "Two pages", [source], "quickstart")
            rendered = []

            def render(**kwargs):
                kwargs["pdf_path"].write_bytes(b"built PDF fixture")
                rendered.append(kwargs["pdf_path"])

            def inspect(command, **kwargs):
                self.assertEqual(Path(command[2]), rendered[0])
                self.assertTrue(rendered[0].is_file())
                return subprocess.CompletedProcess(command, 0, f"{FIRST}\f{SECOND}\fOverflow\f", "")

            errors = io.StringIO()
            with patch.object(release_build, "run_pandoc_md_to_weasyprint_pdf", side_effect=render), patch.object(release_build.shutil, "which", return_value="pdftotext"), patch.object(release_build.subprocess, "run", side_effect=inspect), contextlib.redirect_stderr(errors):
                built = release_build.build_bundle(bundle, key="quickstart", version="test", out_dir=root, intermediate_dir=root / "intermediate", pdf_requested=True, style="bookish", paper="a4", margin="1in", fontsize="11pt", linestretch=1.12, toc_depth=2)
            self.assertIsNone(built)
            self.assertIn("must occupy exactly 2 pages; got 3", errors.getvalue())

    def test_missing_pdf_reader_fails_explicitly(self):
        with patch.object(release_build.shutil, "which", return_value=None), self.assertRaisesRegex(ValueError, "requires pdftotext"):
            release_build.check_quickstart_pdf(Path("unread.pdf"), bundle=None, key="quickstart")


if __name__ == "__main__":
    unittest.main()
