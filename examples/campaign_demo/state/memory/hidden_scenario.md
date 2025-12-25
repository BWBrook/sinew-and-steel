# Hidden Scenario (Example) — Clanfire: Emberfall

This file is an example of where a private scenario/module can live for a campaign.
It can be included in an agent prompt via:

```bash
python tools/build_prompt.py --campaign <slug> --mode agent --hidden campaigns/<slug>/state/memory/hidden_scenario.md
```

The contents below are copied from `rules/scenarios/clanfire_emberfall_hidden.md`.

---

# Hidden Scenario Module — Clanfire: Emberfall

This module is designed to be pasted into an AI Custodian prompt as **private scenario notes**.
It assumes the core rules + Clanfire skin are already loaded.

## Scenario in one line
The clan’s fire is dying, the hunt must succeed, and hungry things in the birch‑line are already claiming the edge of the light.

## Default PCs (optional)
- Grak (Hunter): MGT 12 · FLT 11 · CUN 10 · SPR 8 · INS 8/8 · STM 7/7
- Tarra (Shaman): MGT 6 · FLT 8 · CUN 12 · SPR 14 · INS 11/11 · STM 3/3

## Truth (pick one twist)
1) Rival hunters shadow the same quarry and will steal the kill if PCs hesitate.  
2) Spirits are restless: prey is “marked” and demands a taboo cost to take.  
3) Strangers watch from the ridge and leave unnaturally clean footprints (not wolves).

## Pressure guidance (Shadow)
- Tick +1 Shadow on: taboo breach, failed risky rite, bargaining with spirits, loud violence near the cave.
- Purge Shadow only via: sacrifice, dangerous ritual, great hunt, or story quest.

## Optional clocks (use only if useful)
- Hunger (0/6): tick on time passing or empty return. Full ⇒ forced migration now.
- Storm (0/6): tick on loud actions or long exposure. Full ⇒ whiteout; risky tests cost 1 INS bead or +1 Shadow.
- Pack Learns (0/4): tick when wolves spot PCs or smell blood. Full ⇒ pack surrounds cave at night.

## Threat: Cave Wolf (Soldier 10)
- Attack FLT 10 (edge +1 bite), Defend FLT 10, STM 4, soak 0.
- Hook: if wolf wins with margin ≥ 4, it drags target 2–3 m into darkness.

## Opening beat (start here)
Read-aloud vibe: embers low, frost at cave mouth, “teeth on bone” crunch beyond birches, slow hungry exhale.

Offer options (2–4):
1) Read tracks downwind (CUN)  
2) Stalk the sound (FLT)  
3) Feed fire + call spirits (SPR; fail = +1 Shadow)  
4) Wake the clan and bar the cave (no roll; tick a clock)

## Keep rolls balanced
- Do not roll by default. Use narrative outcomes often and reward innovative play.
- Roll when uncertainty + stakes. Use clocks/Shadow as costs instead of constant checks.

