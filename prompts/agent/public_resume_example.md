# Public Resume Example (Agent)

Use this when you need a player-safe resume in a fresh context.

## Steps
1. Run a public resume pack (redacts private memory/secrets):
   `python tools/resume_pack.py --campaign <slug> --character <name> --public`
2. Use the output to refresh **your internal context only**.
3. Share only player-facing content:
   - the last public log entry (if any)
   - the checkpoint text (exact last GM message)

## Player-facing output (example)
```
[Public recap]
<last log entry, if it helps the player>

[Last GM output]
<checkpoint text>
```
