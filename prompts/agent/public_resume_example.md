# Public Resume Example (Agent)

Use this when you need a player-safe resume in a fresh context.

## Steps
1. Run a public resume pack (redacts private memory/secrets):
   `uv run python tools/resume_pack.py --campaign <slug> --public`
   It holds the campaign, characters, character, scene and checkpoint fields only.
   Add `--character <character_slug>` only to restrict it to one sheet; omit it for a party.
2. Use the output to refresh **your internal context only**.
3. Share only player-facing content: the checkpoint text (exact last GM message).
   The public pack has no log entry.

## Player-facing output (example)
```
[Last GM output]
<checkpoint text>
```
