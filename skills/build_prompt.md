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
- Default templates are `prompts/agent/starter_prompt.md` (agent mode) and `prompts/chat/starter_prompt.md` (chat mode).
- Use `--mode chat` for non-agent play or `--template` to override.
- By default, `tools/build_prompt.py` strips embedded artwork tags like `![](...){...}` from the rules and skins so the prompt is clean for LLM ingestion. Use `--keep-art` if you explicitly want to include them.
- The manifest is the source of truth for file paths.
- Use `--dry-run` to avoid writing files, or `--json` for a machine-readable summary.
