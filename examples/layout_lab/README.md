# Layout Lab (Markdown → PDF)

This folder is a **small testbed** for layout behavior (especially **inline, wrapped images**),
so we can validate formatting on a "lab bench" before editing full rules/skins documents.

## Goal

We want Markdown documents to render to PDF such that:

- Page margins are **sacrosanct** (no text or figures in the margins).
- Images can be aligned **left** or **right** *inside the text block*.
- Text should **wrap around** images (CSS-float style):
  - only the lines beside the image are shortened
  - after the bottom edge of the image, text returns to full width
- Wrapping must **not cascade** into later blocks (lists, tables, headings).

## How to run

The lab runner builds PDFs for each fixture and optionally renders them to PNGs.

```bash
.venv/bin/python tools/layout_lab.py --out release/test/layout_lab --render-png
```

If you have multiple PDF backends configured, the runner will build each fixture with each
backend so you can compare results quickly.
