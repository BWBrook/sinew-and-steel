# Building PDFs (Markdown → PDF)

This repo’s rules and skins are written in Markdown and can be built into PDFs for printing / release.

There are two workflows:

- **Ad-hoc builds (recommended for layout/art iteration):** `tools/md_pdf.py`
- **Release bundles:** `tools/release_build.py` (uses the manifest-driven release pipeline)

> Tip: `release/` is gitignored (`release/*` in `.gitignore`), so it’s a safe place to put local PDF outputs.

---

## Prerequisites

### Always required

- `pandoc` on your PATH
- Python 3.11+ (repo uses a `uv`-managed venv by default)

Setup:

```bash
uv venv
uv sync
```

### Backend-specific

#### 1) WeasyPrint backend (recommended for **wrapped images**)

You’ll need the Python package plus a few system libraries.

```bash
uv pip install weasyprint
```

On Ubuntu you may need:

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libgdk-pixbuf-2.0-0 libpango-1.0-0 libpangoft2-1.0-0
```

#### 2) LaTeX backend (traditional Pandoc PDF)

You’ll need a TeX distribution and a PDF engine (this repo typically uses `xelatex` for the “bookish” style).

---

## Ad-hoc PDFs (`tools/md_pdf.py`)

### Build one file

```bash
.venv/bin/python tools/md_pdf.py rules/quickstart.md \
  --backend weasyprint \
  --style bookish \
  --paper letter \
  --out release/test/quickstart.pdf
```

### Build multiple files into one PDF

```bash
.venv/bin/python tools/md_pdf.py --files "rules/quickstart.md skins/clanfire.md" \
  --backend weasyprint \
  --toc \
  --style bookish \
  --out release/test/layout_test.pdf
```

### Common layout knobs

- `--paper letter|a4`
- `--margin "0.6in 0.75in"`  
  CSS-style shorthand is supported:
  - `"<all>"` (e.g. `0.75in`)
  - `"<top/bottom> <left/right>"` (e.g. `"0.6in 0.8in"`)
  - `"<top> <right> <bottom> <left>"` (e.g. `"0.6in 0.85in 0.6in 0.85in"`)
- `--fontsize 9.5` (WeasyPrint + LaTeX)
- `--linestretch 1.0` (WeasyPrint + LaTeX)
- `--style bookish|default`
- `--toc --toc-depth 2`

> Quickstart note: if you are keeping the quickstart to *exactly two pages*, tweak `--margin`, `--fontsize`, and `--linestretch` first before cutting text.

---

## Wrapped images (WeasyPrint backend)

The **WeasyPrint** backend supports reliable, non-cascading text wrap around images using CSS floats.

In Markdown, add a class and a size:

```md
![](assets/art/ss_core_mechanic.png){.wrap-right width=1.4in}
![](assets/art/ss_luck_tokens.png){.wrap-left width=1.1in}
```

Rules of thumb:

- Prefer `.wrap-left` / `.wrap-right`.
- Keep images **inside the text block** (no margin art). The CSS clears floats before lists/tables/quotes so wrapping doesn’t “leak” into later blocks.
- Use `width=<N>in` to keep things predictable across paper sizes.

---

## Page breaks

For manual breaks inside Markdown you can use raw markers like:

- `\newpage`
- `\pagebreak`

The PDF tooling maps these appropriately for both backends.

---

## Troubleshooting

### “WeasyPrint not installed”

Make sure you’re running the repo’s venv Python:

```bash
.venv/bin/python tools/md_pdf.py ... --backend weasyprint
```

Or:

```bash
uv run python tools/md_pdf.py ... --backend weasyprint
```

### Render to PNG for fast visual diffing

Install `pdftoppm` (Ubuntu: `sudo apt-get install -y poppler-utils`), then:

```bash
pdftoppm -png -f 1 -singlefile release/test/quickstart.pdf /tmp/quickstart_page1
```

---

## Release bundles (`tools/release_build.py`)

This produces the “official” release outputs under `release/dist/` (and can also build PDFs via Pandoc/LaTeX).

Run:

```bash
.venv/bin/python tools/release_build.py --help
```

If you’re iterating on art/layout, prefer `tools/md_pdf.py` until you’re happy, then roll changes into the release build.

