# **CANDLELIGHT DELVEKIT**
### Optional sidecar for Candlelight Dungeons

*A lean referee kit for graph-paper dungeon exploration: hidden maps, revealed routes, old-school backtracking, and procedural danger.*

_(Use atop `skins/candlelight_dungeons.md`. Anything not listed here follows Candlelight Dungeons and core Sinew & Steel as written.)_

Candlelight Delvekit is optional. Candlelight Dungeons already works without it.
Use this add-on when you want a stricter dungeon loop: turns, map reveal, keys, factions, trap rooms, and revisits that matter.

This is not a new combat engine. Keep fights fast, rulings clean, and danger sharp.

---

## WHEN TO USE DELVEKIT

Use Delvekit when the delve itself is the challenge:

- mapping matters
- routes matter
- light and delay matter
- keys, sigils, and loops matter
- monsters move and react

If the dungeon is mostly a backdrop for a few scenes, skip this file and run plain Candlelight Dungeons.

---

## DEFAULT TONE

Suggested creation tone by difficulty:

| Delvekit difficulty | Suggested build tone |
|---|---|
| **Soft** | **heroic** (**16** build points) |
| **Medium** | **standard** (**6** build points) |
| **Hard** | **grim** (**0** build points) |

You may mix these as desired, but the pairings above are the intended defaults.

---

## THE DELVE TURN

When time, noise, and navigation matter, play in **exploration turns**.

One turn is roughly one meaningful dungeon beat: crossing a chamber, checking a door, searching a shrine, listening at a junction, forcing a chest, or withdrawing carefully.

On each turn, ask what the delvers do. Common choices:

- **Move** to a known adjacent room or passage
- **Inspect** a feature closely
- **Search** for hidden exits, clues, traps, or loot
- **Force** a door, chest, grate, or obstacle
- **Listen** or watch for movement
- **Map** and get bearings
- **Rest briefly** or re-order gear
- **Parley** or interact with creatures, idols, machinery, or shrines

If nothing is uncertain or costly, resolve it without a roll. Otherwise use normal Candlelight tests.

At the end of a risky or time-eating turn, the Custodian may do one or more of the following:

- advance **Fatigue**
- mark off light, rations, or other local resources
- trigger a **faction reaction**
- introduce a sign of the roaming threat
- check whether a trap, puzzle, or lock changes state

Routine movement through already-secured space usually needs no roll, but it still spends time.

---

## MAPS: HIDDEN AND REVEALED

Use two maps:

- a **hidden GM map**
- a **revealed player map**

The hidden map is the truth. The player map is earned knowledge.

### Revealing the player map

Add a room to the player map when the delvers enter it or clearly observe it.

Add a connection to the player map when the delvers confirm it exists:

- open corridor
- visible door
- stair
- bridge
- known shaft

Do **not** add these until found:

- secret doors
- concealed passages
- one-way routes not yet understood
- fake doors or false leads

If the party maps sloppily, the player map may be incomplete or wrong. That is enough penalty; no separate mapping rule is needed.

### Map style

Use line-drawn ASCII boxes with room labels and connector notes.
Prefer this:

```text
┌────────────────────┐
│ 1. ENTRY           │
└──────────┬─────────┘
           │
      secret door
           │
      ┌────┴────┐
      │ 2. WELL │
      └─────────┘
```

Avoid `#` / `.` field-fill maps. This add-on aims for keyed graph-paper clarity.

---

## LOCKS, KEYS, SIGILS, AND BACKTRACKING

Delvekit wants revisits. An old dungeon should fold back on itself.

Use blockers that are concrete and local:

- iron key
- saint’s seal
- ember sigil
- counterweight
- spoken phrase
- drained water level
- faction-held token

### Good blocker principles

- show the blocker before the solution if possible
- place the solution elsewhere in reachable space
- make at least some blockers visible on the map
- let a solved blocker open useful loops, not only one dead-end chamber
- where sensible, permit noisy force, costly bypass, or faction bargaining

### Unlocking

If the delvers have the right key, sigil, phrase, or solved condition, the obstacle opens with no roll unless pressure makes failure interesting.

Roll only when the method itself is risky:

- forcing a swollen stone door
- picking a lock under threat
- tracing a burning sigil incorrectly
- lifting a gate before it slams back down

Natural **20** remains catastrophic. On a bad forcing attempt, think broken picks, noise, pinched limbs, alarm, lost footing, or a triggered trap before inventing a new subsystem.

Backtracking is not wasted play. It should cost time, light, and exposure.

---

## PUZZLES

Use only one or two puzzle elements in a delve unless the whole site is built around them.

Good Candlelight puzzles are part of the dungeon itself:

- saint-statues that must face the true crypt
- a flooded cistern with sluice controls
- a furnace shrine that opens only under live flame
- a bell sequence learned from nearby murals
- a tomb seal keyed to names, offerings, or lunar marks

### Puzzle handling

Do not turn the game into a riddle contest.

The Custodian should:

- describe the mechanism plainly
- seed clues in nearby rooms, carvings, notes, habits, or faction lore
- allow testing, partial progress, and brute-force attempts where fiction permits
- let failure cost time, noise, Fatigue, or exposure

If players solve it through logic, observation, or careful experimentation, let it work.
If they attempt a risky shortcut, call for one normal test at most.

Puzzles should change access, safety, or leverage. They should not exist only to stall the session.

---

## FACTIONS

Most good delves hold more than one appetite.

Use at least two factions when you want the dungeon to feel alive:

- goblin scavengers and tomb-keepers
- shrine acolytes and grave-robbers
- fungal beasts and ember cultists
- desperate deserters and the dead they have awakened

For each faction, define five short truths:

- **Want:** what they seek right now
- **Hold:** which rooms or routes they control
- **Fear:** what they avoid
- **Trade:** what they will bargain for
- **Strike:** what makes them turn hostile

### Faction reactions

After loud violence, theft, opened seals, long delay, or visible magic, the Custodian may advance a faction reaction.

Typical reactions:

- scouts appear
- guards reinforce a route
- a rival faction moves on a weakened area
- a hostage, relic, or key is relocated
- a bargain becomes available
- a route is trapped, barred, or watched

Keep reactions concrete and map-facing. Move bodies, alarms, patrols, keys, and doors.
Do not build a new reputation economy.

---

## DEADLY TRAP ROOMS

Candlelight Dungeons already supports sharp danger. Delvekit concentrates that danger into a few memorable spaces.

Most traps should do one of these:

- cost **Stamina**
- cost time and attract danger
- split the party
- destroy gear
- force retreat
- mark **Fatigue**

At most one room per delve should be a true **Grimtooth-style lethal trap room**.

### Lethal trap room guidance

Make it:

- memorable
- clueable
- avoidable or circumventable
- deadly if handled badly

Signs that a room is wrong:

- old corpses in impossible positions
- too-clean flagstones
- scorch marks on the ceiling
- chains, channels, vents, or suspicious weights
- devotional warnings in old script
- missing dust where pressure plates should be

Let caution matter:

- pole-tapping
- probing seams
- sending a mirror ahead
- tracing vents and drains
- weighing the floor
- observing from the threshold

If the trap is sprung badly, let it maim or kill. Do not soften it with hidden mercy rolls.
Use core tools only: tests, Stamina loss, separation, crushing, burning, falling, drowning, or a direct drop to **0 Stamina** when clearly warranted.

Hard mode should include at least one place where "we leave and come back better prepared" is the wise answer.

---

## ROAMING HORROR AND MAJOR BOSS

Each substantial delve benefits from:

- one feared **solo monster**
- one major **boss**

### Solo monster

This is the thing people whisper about.

Use it to make routes feel unsafe:

- leave signs before appearance
- let it move across the map
- make direct battle a bad first plan
- give it a clear weakness, limit, or avoidance pattern

Examples: lamp-hating troll, bone knight, blind furnace drake, saint-eater, stitched ogre.

### Major boss

This is the destination threat.

Place it behind meaningful progress:

- keys
- sigils
- puzzle access
- faction leverage
- costly route control

Give it positional advantage, strange terrain, bodyguards, or ritual support before reaching for extra mechanics.
Weapon edge, armour soak, Stamina, Fatigue, and good room design are enough.

---

## DIFFICULTY LEVELS

Difficulty should tune danger with a few explicit knobs, not a stack of sub-systems.

Choose one for the whole delve.

Use one simple zero-stamina ladder:

- **Soft:** the first two times a delver hits **0 Stamina** in a delve, they may survive with a hard cost if the fiction allows; the next time, they die
- **Medium:** the first time a delver hits **0 Stamina** in a delve, they may survive with a hard cost if the fiction allows; the next time, they die
- **Hard:** hitting **0 Stamina** means death unless an ally's immediate action prevents the blow before it lands

Hard costs should change the delve: lost gear, forced retreat, separation, maiming, or capture on softer modes.
Do not turn a second chance into a free reset.

### Soft

Closest to stock Candlelight Dungeons. Suggested build tone: **heroic (16)**.

- clearer clues before traps and locks
- more alternate routes and safer retreats
- fewer hostile patrol shifts
- roaming horror appears less often and hunts less aggressively
- puzzle failures cost time, position, or **Fatigue**, not instant disaster
- most traps injure, split, or scare rather than kill outright
- at **0 Stamina**, there is room for two hard survivals before death
- soft should punish recklessness, greed, and repeated poor judgment, not ordinary curiosity

Use soft when you want torchlit adventure with pressure but not a meat grinder.

### Medium

Classic dangerous dungeon crawl. Suggested build tone: **standard (6)**.

- meaningful attrition from delay, wrong turns, and noisy choices
- lock-and-key structure matters
- factions react briskly to intrusion
- the roaming horror can cut off routes
- serious traps can drop a delver fast if caution fails
- forced doors, rushed locks, and bad puzzle shortcuts often cost **Stamina**, gear, or position
- at **0 Stamina**, there is room for one hard survival before death
- medium should give a little breathing room after one bad decision, but not after a pattern of sloppy play

Use medium as the default Delvekit mode.

### Hard

Death is a real possibility. Suggested build tone: **grim (0)**.

- wasted turns should hurt
- fewer safe loops and fewer easy retreats
- weaker clue density before major hazards
- harsher faction response to noise and delay
- the roaming horror actively pressures rest and backtracking
- at least one trap room or route hazard can kill through bad judgment
- bosses punish frontal assault unless the party has prepared advantages
- at **0 Stamina**, the delver dies on hard
- hard should only tolerate a couple of bad decisions before a delver is dead, broken, or forced out
- hard should also allow bad luck to finish a delver when the risk was honestly lethal

Hard mode should reward scouting, baiting, splitting enemies, ambush, retreat, and bargaining.
If the delvers fight every room head-on, they should not expect to survive.
Do not soften hard mode with capture, prophecy, last-second bargains, or other prolonging devices unless the table asked for that tone before play began.

### Small explicit knobs

Use these to tune a delve without adding a new combat layer:

- **Lethality:** clearer warning signs in soft, fewer in hard
- **Trap severity:** maiming in soft, killing in hard
- **Faction pressure:** slower reinforcement in soft, active pursuit in medium, ruthless follow-through in hard
- **Resource pressure:** more safe pauses in soft, fewer in medium, almost none in hard
- **Zero-Stamina risk:** two hard survivals in soft, one in medium, and final in hard

---

## QUICK CUSTODIAN PROCEDURE

When the delve is in focus:

1. Describe the room or threshold clearly.
2. Ask what the delvers actually do.
3. Resolve with no roll unless risk and uncertainty matter.
4. On a risky turn, update time, Fatigue, factions, or map state.
5. Reveal only what has been earned.
6. Keep blockers concrete and revisits meaningful.
7. Let caution, retreat, and cunning beat brute force when they should.

That is the whole add-on.

---

## FINAL PRINCIPLES

- Keep the map readable.
- Keep the room keys short.
- Keep danger legible before it becomes lethal.
- Keep factions active.
- Keep backtracking costly, not tedious.
- Keep combat in the base game.

If Delvekit starts adding more machinery than fear, cut it back.
