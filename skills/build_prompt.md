---
name: build-prompt
description: Assemble a complete GM prompt from rules, skin, and optional hidden notes.
---

# Build Prompt

## Goal
Create a single prompt file containing core rules, the chosen skin, and optional hidden scenario notes.

## Steps
1. List available skins: `python tools/build_prompt.py --list-skins`.
2. Build a prompt: `python tools/build_prompt.py --skin <slug> --out /tmp/ss_prompt.md`.
3. (Optional) Include a hidden scenario: `--hidden path/to/notes.md`.

## Notes
- The template is `prompts/starter_prompt.md` and uses placeholders.
- The manifest is the source of truth for file paths.
