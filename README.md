# **Sinew & Steel**

*A razor-lean, setting-agnostic role-playing engine—designed to sing at the table and purr in the prompt window of any reasoning AI.*

---

## Why another ruleset?

Because most RPG rulebooks ask you to memorise a phone-book of subsystems before you can bleed on the page.  
Sinew & Steel works the other way round:

* **One d20, five numbers, two tracks**: simple enough to fit on a beer-soaked coaster.  
* **Friction where it matters:** burning Luck, shaving armour with margin, riding peril tracks.  
* **Skin-agnostic.**  Swap the coat of paint and you’re in Bronze-Age Atlantis, a Martian dust storm, or the heat-death horizon.  
* **AI-ready.**  The rules are easy for a language model to keep in short-term memory, so the “GM” can focus on story beats instead of chart-flipping.

> *Summarise the unwritten novel, said Borges.  We did.*

---

## Core concept (60 seconds)

| Pillar | One-line summary |
|---|---|
| **Roll-under d20** | ≤ attribute = succeed.  Natural 1 legendary, 20 catastrophic. |
| **Five attributes** | Baseline 10.  +1 costs –2 elsewhere.  Range 6-16. |
| **Luck = tokens** | Spend to nudge dice; pool size *is* the score. |
| **Stamina** | Starts at 5.  Hits deal 1 + weapon edge.  0 = collapse. |
| **Pressure track** | 0-5 fuse.  Colour changes by skin (Heat, Doom, Shadow, Anomaly). |
| **Dynamic armour** | Soak 1-3; attacker margin erodes soak 1 per 4 points. |

That’s the chassis.  Everything else is flavour‐text.

---

## Example skins

| Scenario | Pitch |
|---|---|
| **Clanfire** | Neanderthal Ice-Age survival.  Totem spirits, Beast bonds, Shadow track. |
| **Age Undreamed Of** | Howard-esque sword-and-sorcery.  Doom, Heroic acts, foul Sorcery. |
| **Time Odyssey** | H. G. Wells chrononautics.  Ingenuity pool, Anomaly crises, epoch graphing. |
| **Briar & Benedictine** | Medieval sleuthing.  Divine providence, Sin and pennance, murder mystery. |
| **Mars Saga** | Noir-tinged colonised Mars.  Heat track, psionics, red-dust grime. |

Swap a few words and build your own skin in an afternoon.

---

## Quick start

1. **Read `/core/Sinew&Steel_rules_on_a_page.pdf`.**  
2. Pick or clone a skin from `/skins/`.  
3. Hand the rules page to players; keep the skin doc behind your screen.  
4. (Optional) paste the **Starter Prompt** `/ai_play/` into ChatGPT or another LLM and hit enter.  
5. Roll dice, burn Luck, tell messy stories.

---

## For AI game-masters

The repo’s `/ai_play/` folder contains:

* A **starter prompt template** that loads the engine + chosen skin in one go. Add ruleset as required. 
* Tool call examples for dice rolls, Luck offers, and pressure escalations.

No plugins needed for reasoning engines with tool use—`random.randint(1,20)` and short, punchy prose carry the night.

---

## Contributing

Issues, forks, pull requests, new skins, typo fixes—all welcome.  Keep additions:

* **Lean.**  One new rule should replace three lines of “crunch.”  
* **Setting-agnostic** in core; setting-specific rules live in `skins/`.  
* **Plain Markdown** first; we’ll prettify later.

---

## Licence

* Sinew & Steel core rules © 2025 Barry Brook
* **Text & tables:** Creative Commons **CC-BY 4.0**  
* **Helper code snippets:** MIT

Credit the project, hack it, sell adventures, translate it into Akkadian—just link back here.

---

> “Steel is honest; spells are treacherous.  Dice are the coin we pay for either.”  
> — *Design notes, margin scrawl*

Happy carving.
