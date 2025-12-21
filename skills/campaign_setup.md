---
name: campaign-setup
description: Create a per-campaign scaffold and bind it to a skin.
---

# Campaign Setup

## Goal
Create a campaign workspace with its own state and metadata, using a chosen skin.

## Steps
1. Initialize a campaign:
   `python tools/campaign_init.py --title "My Campaign" --skin <skin>`
2. (Optional) Generate a starting character:
   `python tools/campaign_init.py --title "My Campaign" --skin <skin> --random-character "Name"`
3. Build the full prompt directly from the campaign:
   `python tools/build_prompt.py --campaign <slug> --mode agent`

## Notes
- Campaigns live in campaigns/ and are ignored by git.
- Each campaign has its own state/ folder for characters, trackers, memory, and logs.
