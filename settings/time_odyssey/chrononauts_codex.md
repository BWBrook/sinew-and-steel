**TIME ODYSSEY — CHRONONAUT’S CODEX**
*A lean rules engine for H. G. Wells‑style excursions across the centuries*

---

### Core Mechanic
Roll a single d20 whenever the outcome is uncertain and the stakes matter. A result **equal to or lower** than the relevant attribute earns success; higher marks failure.  
• **Natural 1**: astounding success.  
• **Natural 20**: catastrophic mishap.  
• **Advantage / Disadvantage**: roll two dice and keep the better / worse respectively.  
• **Opposed checks**: both sides roll; if only one succeeds, that side wins. If both succeed compare **margin** (attribute − roll) to decide.

### Attributes
Each chrononaut begins with **five attributes**. Baseline is **10**; to raise one by **+1** a player must lower another by **‑2**. Scores range from **6** (frail) to **16** (peerless).

| Abbrev | Attribute | Purview |
| --- | --- | --- |
| PRW | **Prowess** | Muscle, grit, close combat, hard labour |
| REF | **Reflex** | Agility, balance, evasive footwork, sleight of hand |
| INT | **Intellect** | Scientific insight, engineering, deduction, linguistic puzzles |
| EMP | **Empathy** | Persuasion, morale, reading motives, nurturing allies |
| ING | **Ingenuity** | Lateral thinking, serendipity, sheer luck **and** expendable fortune pool |

### Ingenuity Pool
Your ING score is mirrored by a pool of tokens. After any roll is revealed you may burn Ingenuity to nudge the die **±1 per token** (never altering natural 1 or 20). A calm night’s rest restores **1 ING**. Esoteric rejuvenators or paradoxical boons may refill more. A barren pool leaves you naked to chance.

### Stamina & Injury
Stamina starts at **5**. A punch or short fall costs **1**. Blades, revolver rounds or hungry Morlock claws deal **+1**. Heavy ordnance or machinery add **+2**. Armour (rare in Wellsian wardrobes) soaks **1** if sturdy. At **0 STM** you collapse—death, maiming or desperate rescue depends on narrative plausibility. A short respite with water and bandage restores **1 STM**; a full clinical rest or advanced future medic restores **2**.

### Temporal Anomaly Track
Meddling with history courts paradox. Certain feats—altering major events, meeting one’s past self, operating the machine under duress—require an **INT or ING** roll. Failure adds **1 ANOMALY**. At **5** anomaly points reality lashes back: memory fractures, equipment sublimates, or a rip‑current flings the party to an unknown era. Only arduous atonement or temporal realignment can shed Anomaly.

### Combat Snapshot
1. **Attacker** rolls under PRW (melee) or REF (ranged).  
2. **Defender** rolls under REF if dodging, or PRW when bracing behind cover.  
3. If attacker succeeds / defender fails → hit. If both succeed compare margins.  
4. **Damage**: 1 STM base + weapon edge (light weapons 0, sabres & pistols +1, arc‑rifles +2).  
5. Armour subtracts its value.

### Equipment & Burden
A traveller may carry **six substantial items**. The brass‑and‑crystal **Time Machine** itself is too massive—secure it off‑scene. Currency morphs by era; keep abstruse coinage slim lest you invite thieves or customs scrutiny.

### Advancement Milestones
After surviving a paradox cascade, cataloguing a prehistoric beast or shaping an epochal alliance, award a **Milestone**. Choose **+1 Attribute** (max 16) *or* **+1 Stamina**, plus a narrative boon—future alloy blade, Victorian patent rights, sympathetic Sphinx guardian.

### Automated Dice & Ingenuity (Python)
All rolls, random era tables and Anomaly checks run hidden via `random.randint(1,20)`. Show only the number, margin and offer to burn ING when relevant. Natural 1 and 20 remain immutable.

---
Ink these strictures upon vellum or etch them on a pocket brass plate—chrononauts who ignore them soon vanish into contradictory echoes.

