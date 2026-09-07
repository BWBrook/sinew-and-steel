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

### PDF renderer

#### WeasyPrint

You’ll need the Python package plus a few system libraries.

```bash
uv sync --extra pdf
```

On macOS (Homebrew), install the image-loader library once:

```bash
brew install gdk-pixbuf
```

On Ubuntu you may need:

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libgdk-pixbuf-2.0-0 libpango-1.0-0 libpangoft2-1.0-0
```

#### Typeface

The WeasyPrint stylesheet `templates/html/bookish.css` uses Linux Libertine O where installed, otherwise Times New Roman (the current macOS release builds). Change the CSS to alter the typeface.

---

## Ad-hoc PDFs (`tools/md_pdf.py`)

### Build one file

```bash
uv run --extra pdf python tools/md_pdf.py rules/quickstart.md \
  \
  --style bookish \
  --paper a4 \
  --out release/test/quickstart.pdf
```

### Build multiple files into one PDF

```bash
uv run --extra pdf python tools/md_pdf.py --files "rules/quickstart.md skins/clanfire.md" \
  \
  --toc \
  --style bookish \
  --out release/test/layout_test.pdf
```

### Common layout knobs

- `--paper a4|letter` (default: `a4`)
- `--margin "0.6in 0.75in"`  
  CSS-style shorthand is supported:
  - `"<all>"` (e.g. `0.75in`)
  - `"<top/bottom> <left/right>"` (e.g. `"0.6in 0.8in"`)
  - `"<top> <right> <bottom> <left>"` (e.g. `"0.6in 0.85in 0.6in 0.85in"`)
- `--fontsize 9.5`
- `--linestretch 1.12`
- `--style bookish|default`
- `--toc --toc-depth 2`

### Pagination baseline (recommended)

If you want your local pagination to match the repo’s default expectations for PDF iteration, use:

```bash
--style bookish --paper a4 --margin "0.55in 0.75in" --fontsize 11.5 --linestretch 1.12
```

> Quickstart note: if you are keeping the quickstart to *exactly two pages*, tweak `--margin`, `--fontsize`, and `--linestretch` first before cutting text.

---

## Wrapped images (WeasyPrint backend)

The **WeasyPrint** backend supports reliable, non-cascading text wrap around images using CSS floats.

In Markdown, add a class and a size:

```md
![](assets/art/ss_core_mechanic.png){.wrap-right width=1.4in}
![](assets/art/ss_luck_pool.png){.wrap-left width=1.1in}
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

Make sure you installed the repo’s PDF extra and are running the repo’s venv Python:

```bash
uv sync --extra pdf
```

Then build with:

```bash
uv run --extra pdf python tools/md_pdf.py ...
```

### Render to PNG for fast visual diffing

Install `pdftoppm` (Ubuntu: `sudo apt-get install -y poppler-utils`), then:

```bash
pdftoppm -png -f 1 -singlefile release/test/quickstart.pdf /tmp/quickstart_page1
```

---

## Release bundles (`tools/release_build.py`)

This produces the “official” release outputs under `release/dist/`.

PDF release builds use WeasyPrint: pandoc renders the assembled Markdown to
HTML, and WeasyPrint lays it out with `templates/html/bookish.css`.

Run:

```bash
uv run python tools/release_build.py --help
```

Build the full guided book:

```bash
uv run --extra pdf python tools/release_build.py --bundle full_book --pdf --style bookish
```

If you’re iterating on one or two chapters of art/layout, prefer `tools/md_pdf.py`
until you’re happy, then roll changes into the release build.
