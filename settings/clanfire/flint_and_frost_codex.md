**CLANFIRE — FLINT & FROST CODEX**
*A rules‑light engine for Neanderthal saga at the edge of extinction, c. 50 000 BP*

---

### Core Mechanic
One roll of a d20 decides uncertain acts with real peril. A result **≤ attribute** succeeds; higher fails.  
• **Natural 1**: legendary feat.  
• **Natural 20**: dire mishap.  
• **Advantage / Disadvantage**: roll 2d20, keep lower / higher.  
• **Opposed**: both roll; if one succeeds and the other fails, that side wins. If both succeed compare **margin** (attribute − roll).

### Attributes
Begin with **10** in each; shift points by lowering one **‑2** to raise another **+1**. Limits 6–16.

| Abbrev | Attribute | What it governs |
| --- | --- | --- |
| MGT | **Might** | brute strength, hauling, close blows, endurance |
| FLT | **Fleetness** | quick movement, balance, stealth, thrown weapons |
| CUN | **Cunning** | tool‑making, tracking, tactical wit, problem‑solving |
| SPR | **Spirit** | willpower, ritual chant, resisting fear and frost |
| INS | **Instinct** | gut fortune, sudden insight **and** expendable pool |

### Instinct Pool
INS score equals a pool of stones. After you see any roll you may drop stones to move the die **±1 per stone** (never alters 1 or 20). One peaceful night by the clan fire restores **1 INS**. Mythic visions, trance rites or story boons may restore more. Empty instincts leave hunters exposed to fate.

### Stamina & Harm
Stamina starts at **5**. A bruise or stumble costs **1 STM**. Stone axe, spear or wolf bite adds **+1**. Mammoth gore or glacial crevasse adds **+2**. Furs or leather soak **1** if called. At **0 STM** you drop: death, crippling or rescue per fiction. A short rest with fire and water restores **1**, deep shelter and herbs **2**. Grave wounds need shaman craft.

### Shadow Track
Interlopers from the south, dying game herds, omens in the sky—each breach of the old order risks **Shadow**. Certain acts (speaking with Sapiens, violating taboos, bending time‑old spirits) call for a **SPR or CUN** roll; failure adds **1 SHADOW**. At **5** Shadow, calamity strikes: spirits withdraw, illness spreads, or a blizzard entombs the valley. Only dangerous ritual, great hunt or self‑sacrifice can ease the gloom.

### Combat Flow
1. **Attacker** rolls under MGT (melee) or FLT (thrown).  
2. **Defender** rolls under FLT to evade or MGT to parry with haft.  
3. Resolve hit; damage = 1 STM + weapon edge (light clubs 0, stone axe / spear +1, atlatl dart +2).  
4. Armour subtracts soak.

### Burden & Craft
A hunter totes **six substantial items**: spears, stone blade kit, fire drill, hide water skin, carved idol. Smaller trinkets ride in pouches. Excess weight slows and gives Disadvantage on FLT.

### Milestones
After a successful megafauna hunt, forging alliance, or surviving sky‑fire, award a **Milestone**: **+1 Attribute** (max 16) *or* **+1 STM**, plus boon—rare amber core, mammoth‑bone mail, dream of distant summers.

### Automated Dice & Instinct (Python)
All rolls, random weather, prey tables and Shadow checks run unseen with `random.randint(1,20)`. Announce result, margin, and chance to burn INS. Natural 1 and 20 stand inviolable.

---
Hold these laws close; the Ice drinks fools. The clan that masters flint and fate endures another dawn.

