This document describes the editorial style for new skins or rule changes (“Mentzer-era TSR editor”, but adapted to Sinew & Steel’s modern, lean chassis).

## Editorial North Star

- Teach the game as if the reader has never played Sinew & Steel before (and may not have played an RPG at all), but is intelligent and impatient.
- Every rule must answer: what you do at the table, when you do it, and what changes in the fiction/state.
- Clarity beats vibe; vibe is welcome only when it teaches or motivates play.
- Keep “agent harness” operational guidance out of the rules unless it’s truly part of the game system (we’ll keep the player/GM rules clean).

## Process (How to edit a rules/skin document)

  - 1) Define the job of the document (1 paragraph).
      - Who is it for (players? Custodian? both)?
      - What should the reader be able to do immediately after reading it?
      - What should it not try to cover (and where does that live instead)?
  - 2) Structural pass (information architecture first).
      - Ensure sections appear in the order the reader needs them at the table:
          1. What the game is
          2. What you need to play
          3. What a character is (and the minimum sheet)
          4. What you do in play (conversation loop)
          5. When to roll / how to roll
          6. Consequences (damage, pressure, clocks, etc.)
          7. A tiny worked example
      - If a concept is used before defined, reorder or add a “pre-brief” box.
      - Prefer short sections with strong headings over long walls of prose.
  - 3) Mechanical clarity pass (rules precision).
      - Convert any “implied” rules into explicit statements (without bloating).
      - Standardize terminology (one name per thing; no synonyms).
      - Add “defaults” wherever a reader might hesitate:
          - default build points (standard 6)
          - default pressure clock range
          - default when to roll vs narrate
      - Add “edge-case guardrails” only where ambiguity would cause table fights or agent drift.
  - 4) Teaching pass (examples, vignettes, mini-scripts).
      - Add small BECMI-style teaching devices:
          - a micro-vignette (2–6 lines) showing the conversation loop
          - a worked roll example (numbers shown, success/failure + consequence)
          - a micro combat exchange if combat exists in the doc
          - a tiny character build example if creation is in scope
      - Keep examples short, labeled, and obviously optional — but table-useful.
  - 5) Line edit pass (sentence-level).
      - Shorten sentences; prefer verbs; kill ambiguity.
      - Replace “can/may/should” with clear imperatives where it’s a rule.
      - Remove redundant phrases; tighten adjectives; avoid “rulebook throat-clearing.”
  - 6) Layout + usability pass (TSR editor instincts).
      - Add quick-reference elements:
          - “In one sentence” summaries
          - bullet checklists
          - small tables (e.g., what stats mean)
          - “If you remember nothing else…” callouts
      - Enforce consistent Markdown conventions:
          - consistent heading depths
          - consistent naming of dice/rolls
          - consistent formatting for key terms (e.g., Pressure, Luck, Stamina, build points)
  - 7) Consistency + cross-doc pass (minimal, but important).
      - Confirm the quickstart doesn’t contradict core rules.
      - Ensure it matches current mechanics (notably: Stamina baseline 5 participates in build points; build-point budgets; nudge semantics; etc.).
      - If we reference another document, make the reference specific and minimal (“For X, see Y”).
  - 8) Final “table read” pass (does it run?).
      - Pretend I’m at a table with a new group and only this doc.
      - Ask: where would they pause? what would they argue about?
      - Fix those points, not everything.

## Agent editing practice  

If an agent is the primary editor, follow these guidelines:

  - The agent can change:
      - ordering, headings, and layout
      - unclear phrasing, inconsistent terms, missing defaults
      - examples (including updating the Clanfire example character so it is provably legal under the current creation rules)
  - The agent shouldn't change (without asking):
      - core design intent, tone, setting voice
      - any “dial” choices (unless the doc contradicts itself)
      - large stylistic rewrites that risk turning it into a different book

How to Collaborate with a Human Author Per Document

  - Agent should do one document at a time and deliver:
      - the edited file (patch)
      - a short “editor’s memo” of what changed and why (especially any rule clarifications)
      - a short list of “author decisions” (things I’m not sure about and want you to confirm)
  - The human editor should then a final pass and either:
      - approve as-is, or
      - tweak voice/wording, or
      - tell me to adjust specific parts.
  - Then move to the next document.

---

## Skin Editing Checklist (Mechanics-First, Drift-Resistant)

Use this as a “lint list” whenever you add or revise anything in skins/*.md or in the corresponding manifest.yaml entry. The goal is: skins change flavour and emphasis, not the core math.

  1) Core Invariants (A Skin Must Not Break These)

  - Resolution stays d20 roll-under (and margin matters); no new dice systems or additive modifiers layered on top.
  - The game still runs on five attributes + Stamina + Luck tokens + Pressure (0–5); no extra stats, derived stats, or “sub-attributes.”
  - Pressure is universal 0–5 and when it hits 5 it triggers a crisis, then resets to 0 (skins can rename it: Shadow/Heat/Doom/etc.).
  - Stamina participates in the creation ledger with baseline 5, range 3–9 (attributes baseline 10, range 6–16).
  - Build points remain the same rules:
      - Default creation budget 6 (grim 0 / pulp 12 / heroic 16).
      - Spend rule: +1 costs 2 points above baseline, +1 costs 1 point below baseline (Stamina baseline 5; attributes baseline 10).
  - Luck remains dual-purpose:
      - Luck tokens are a pool you spend to nudge.
      - Luck tests roll ≤ current tokens (not max); spending now makes later Luck tests harder.

  2) “Skin Must Define” (The Minimum Mechanical Profile Every Skin Needs)
  These should be explicit in both the skin doc and manifest.yaml so humans and tools agree.

  - Skin identity + scope: one paragraph on what kinds of stories this skin supports (helps constrain rulings).
  - Attribute mapping:
      - Exactly 5 attributes, each with an all-caps short key (e.g., STR, NIM, …) and a name.
      - A sentence each on “what this covers” (broad strokes, not a skill list).
  - Luck key and name:
      - Which of the 5 attributes is Luck’s equivalent (luck_key) and what it’s called (luck_name).
      - A reminder that this stat is both a roll-under attribute and the token pool.
  - Pressure name + crisis tone:
      - Pressure track renamed (e.g., Shadow/Heat/Doom) and what a crisis looks like in this genre.
      - (Optional but strongly recommended) a 0–5 colour table with 1–2 “what changes” examples at 3–5.
  - Default “what stat for what” guidance (to prevent drift and over-rolling):
      - A quick mapping for common approaches: violence, evasion, investigation, persuasion, occult/tech, and “pure luck.”
      - Emphasize “pick the stat that matches the approach,” not “there is one correct stat per action.”
  - Genre recovery expectations:
      - How/when Luck tends to refresh in this skin’s fiction (rest, rites, shore leave, feast day, etc.)—this can be guidance-only, but it should exist.
  - If the skin introduces any named procedures (rituals, hacking, travel, corruption, sanity, etc.):
      - State the procedure in core terms (what to roll, what counts as Advantage/Disadvantage, what happens on success/failure, what resources tick).
      - Keep it short and auditable.

  3) Allowed Skin Customizations (Safe Ways to Add Texture Without Warping Core)

  - Renaming attributes/Luck/Pressure/Stamina to fit the genre (no math changes).
  - Declaring typical costs in-fiction (“spells usually cost +1 Pressure or 1 Luck”; “gunfights tend to spike Pressure fast”).
  - Providing recommended clocks (Heat, Threat, Patrol, Storm, Suspicion) with tick triggers—these are story-facing timers, not new mechanics.
  - Declaring canonical examples of Advantage/Disadvantage in this genre (cover, leverage, rituals prepared, home turf, etc.).
  - Adding equipment lists using existing tags (edge, soak, fatal, tools-as-advantage) rather than inventing new numeric layers.
  - Adding a small bestiary/NPC page using the tier-score method (tier + STM + edge/soak + 1 hook).

  4) Red Flags (Skin Drift Smells) — Fix These Immediately When You See Them

  - The skin implies or requires rolling constantly (“roll to do basic travel,” “roll every interaction”) instead of using stakes + uncertainty.
  - The skin introduces bonus stacking (“+2 for X, +3 for Y”) rather than Advantage/Disadvantage and fictional positioning.
  - The skin adds a skill list or an implicit skill list (“roll INT for tracking, REF for climbing, EMP for…”) that becomes prescriptive rather than illustrative.
  - The skin creates a second universal meta-track (“Fear is always tracked exactly like Pressure in every scene”) without explicitly calling it optional.
  - The skin changes the meaning of a “success” (e.g., “success still costs you most of the time”) without flagging it as a genre dial (and explaining why).
  - Any example character violates:
      - the Stamina-in-ledger rule,
      - the build points rules,
      - the attribute ranges (6–16) / STM range (3–9).

  5) Clarity for Humans + Agents (Formatting Discipline That Prevents Misreads)
  This is mechanical hygiene, not “prose polish”:

  - Put anything that is a true rule under a clearly labeled section like Mechanics (Strict).
  - Put vibes, advice, tables of examples, and evocative lists under Guidance (Soft).
  - If a sentence is guidance, don’t word it like a rule (“often,” “typically,” “a good default is…”).
  - If a skin introduces a term (Heat, Shadow, Sin, Anomaly), define it in one line the first time it appears, even if “obvious.”

  6) Tool / Manifest Alignment Checks (So the Harness Doesn’t Lie)
  When editing a skin, keep these in sync:

  - manifest.yaml entry matches the skin doc:
      - skins.<slug>.file is correct
      - pressure_track matches the name used in the doc
      - attributes keys/names match the doc
      - luck_key is one of those 5 keys
      - luck_name matches the doc’s Luck naming
  - Generator hints (skins.<slug>._gen) remain sane:
      - primary should be a real attribute key for the skin
      - min_steps/max_steps stay within your expected ranges

  7) Quick Mechanical Smoke Tests for Any Skin Edit (Recommended Practice)
  After editing a skin, run a tiny end-to-end loop to catch “I renamed something but forgot the manifest” errors:

  - python tools/validate_repo.py
  - Create a throwaway campaign with that skin and a random character, then validate:
      - python tools/campaign_init.py --name skin_smoke --skin <skin_slug> --random-character "Smoke"
      - python tools/validate_campaign.py --campaign skin_smoke
      - python tools/build_prompt.py --campaign skin_smoke

  If all of that passes, you’ve proven the skin works mechanically with the harness.
