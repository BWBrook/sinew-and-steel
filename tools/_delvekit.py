from __future__ import annotations

import csv
from collections import Counter, deque
from pathlib import Path
from random import Random
from typing import Any

import _sslib


DELVEKIT_FRAGMENT_CSV = Path(__file__).resolve().parent.parent / "data" / "delvekit_fragments.csv"
_FRAGMENT_CACHE: dict[tuple[str, str], list[str]] | None = None


SCHEMA_VERSION = 1

SIZE_CONFIG = {
    "tiny": {"rooms": (6, 7), "loops": (0, 1), "secrets": (0, 1), "treasures": (1, 2)},
    "medium": {"rooms": (9, 11), "loops": (1, 2), "secrets": (1, 2), "treasures": (2, 3)},
    "large": {"rooms": (12, 15), "loops": (2, 4), "secrets": (1, 3), "treasures": (3, 4)},
}

DIFFICULTY_KNOBS = {
    "soft": {
        "suggested_tone": "heroic",
        "trap_room_prob": 0.25,
        "solo_prob": 0.25,
        "boss_prob": 0.45,
        "faction_prob": 0.50,
        "weird_npc_prob": 0.35,
        "keyed_prob": 0.55,
        "resource_pressure": "light",
        "faction_pressure": "measured",
        "zero_stamina": "the first two times a delver hits 0 Stamina in a delve, let them survive with a hard cost if the fiction allows; the next time, they die",
        "trap_severity": "mostly alarms, maiming setbacks, separation, or lost position",
    },
    "medium": {
        "suggested_tone": "standard",
        "trap_room_prob": 0.60,
        "solo_prob": 0.60,
        "boss_prob": 0.70,
        "faction_prob": 0.75,
        "weird_npc_prob": 0.35,
        "keyed_prob": 0.75,
        "resource_pressure": "meaningful",
        "faction_pressure": "active",
        "zero_stamina": "the first time a delver hits 0 Stamina in a delve, let them survive with a hard cost if the fiction allows; the next time, they die",
        "trap_severity": "serious harm, forced retreat, and real death risk if mishandled",
    },
    "hard": {
        "suggested_tone": "grim",
        "trap_room_prob": 0.85,
        "solo_prob": 0.80,
        "boss_prob": 0.90,
        "faction_prob": 0.90,
        "weird_npc_prob": 0.25,
        "keyed_prob": 0.90,
        "resource_pressure": "relentless",
        "faction_pressure": "ruthless",
        "zero_stamina": "0 Stamina is death on hard unless an ally's immediate action prevents the blow before it lands",
        "trap_severity": "lethal rooms, direct kill setups, and ruthless follow-through",
    },
}

COMMON_PUZZLES = ["saint_mask_puzzle", "bell_sequence", "sluice_puzzle", "furnace_vow", "weight_rite", "mirror_angles"]

STYLE_PACKS = {
    "reliquary": {
        "label": "candlelit reliquary",
        "pitch": "a shrine-complex of ash, bells, relic metal, and bad devotion",
        "site_names_first": ["Ashen", "Lantern", "Bone", "Cinder", "Veiled", "Sable"],
        "site_names_second": ["Reliquary", "Priory", "Chapel", "Crypt", "Vault", "Cistern"],
        "room_name_parts": {
            "start": ["Entry Stairs", "Gate Vestibule", "Cold Steps", "Pilgrim Descent"],
            "hub": ["Ash Court", "Processional Crossing", "Saints' Junction", "Forked Hall"],
            "boss": ["Throne of Ash", "Reliquary Heart", "Cinder Throne", "The Last Shrine"],
            "puzzle": ["Well of Saints", "Mask Chapel", "Bell Cistern", "Liturgy Wheel"],
            "approach": ["Reliquary Walk", "Iron Gallery", "Bell Passage", "Upper Grate"],
            "treasure": ["Silver Locker", "Abbot's Chest", "Pilgrim Hoard", "Reliquary Nook"],
            "generic": ["Collapsed Scriptorium", "Furnace Landing", "Broken Ossuary", "Lamp Store", "Dust Crypt", "Choir Stalls"],
        },
        "trap_rooms": [
            ("Censer Lift", "grimtooth_lethal_room", "A brass lift over a hidden drop, built to punish hurry and pride."),
            ("Murder Choir", "grimtooth_lethal_room", "Hanging bells and counterweights conceal darts, falls, and swinging blades."),
            ("Ash Sluice", "grimtooth_lethal_room", "A furnace drain can drown the room in hot ash if handled badly."),
            ("Saint's Pendulum", "grimtooth_lethal_room", "The chamber rewards stillness; panic wakes the scything weight."),
        ],
        "keys": [
            ("ember_sigil", "sigil_gate", "sigil gate"),
            ("bronze_key", "keyed_door", "bronze lock"),
            ("saint_phrase", "spoken_seal", "spoken seal"),
            ("counterweight_pin", "counterweight_gate", "counterweight gate"),
        ],
        "solo_monsters": [
            ("Bell-Hound", "Blind iron hunter that follows vibration and ringing metal."),
            ("Lamp-Eater", "A soot-black giant lizard that lunges at open flame."),
            ("Veil Widow", "A silk-pale corpse spider that waits above thresholds."),
            ("Wax Knight", "A silent armored revenant that never leaves the upper walk."),
        ],
        "bosses": ["Abbot of Cinders", "Bone Regent", "Lamp Tyrant", "Ash Widow", "Saint of Embers", "Choirmaster Hollow", "The Reliquary Steward", "Mother of Ash Lamps"],
        "factions": [
            ("Gutter Goblins", "lamp oil, food, and an escape route"),
            ("Ash Pilgrims", "the rekindling of a furnace or saint-fire"),
            ("Mould Monks", "spores, stillness, and intruders' lungs"),
            ("Grave Diggers", "bones, silver, and anything not nailed down"),
            ("Ratling Choir", "bells, scraps, and secrets whispered in drains"),
        ],
        "atmospheres": [
            "wet limestone and candle ash",
            "old incense cut with copper",
            "lamp grease and mouldy paper",
            "dry furnace heat and bitter dust",
            "bells trembling somewhere out of sight",
            "grave rosemary over stale blood",
        ],
        "contents": [
            "broken pews and ash bowls",
            "collapsed shelves and scroll tubes",
            "shrine fragments and cracked icons",
            "rusted censers and devotional masks",
            "bone heaps and robbed niches",
            "sermon frescoes and soot marks",
        ],
        "treasures": ["silver censer", "saint-bone charm", "ruby prayer-chain", "gold leaf reliquary scrap", "warm ember gem", "ivory seal-ring"],
        "weird_npcs": ["blind bell-ringer who refuses to leave", "wounded relic-thief hiding under a saint bier"],
    },
    "caverns": {
        "label": "flooded natural caverns",
        "pitch": "a wet cave site of sinkholes, pale fungus, slick ledges, and black water",
        "site_names_first": ["Drowned", "Moss", "Blackwater", "Moonless", "Hollow", "Pale"],
        "site_names_second": ["Caverns", "Sink", "Grotto", "Deep", "Pools", "Warrens"],
        "room_name_parts": {
            "start": ["Drip Mouth", "Collapsed Sink", "Cold Crawl", "Root Cleft"],
            "hub": ["Echo Pool", "Split Ledge", "Flood Junction", "Stone Throat"],
            "boss": ["Sunless Pool", "Maw Hollow", "Blackwater Nest", "The Drowned Heart"],
            "puzzle": ["Tide Wheel", "Blind Spring", "Stone Organ", "Fungus Gate"],
            "approach": ["Slick Traverse", "Bat Gallery", "Underpool Walk", "Narrow Ledge"],
            "treasure": ["Smuggler Cache", "Pearl Shelf", "Sunken Locker", "Dry Niche"],
            "generic": ["Fungus Shelf", "Drip Chamber", "Fishbone Den", "Broken Ferry", "Bat Roost", "Salt Pocket"],
        },
        "trap_rooms": [
            ("Flood Teeth", "grimtooth_lethal_room", "A narrow basin that becomes a drowning torrent when the wrong spill-gate is touched."),
            ("Slipshaft", "grimtooth_lethal_room", "A harmless-looking ledge gives way to a polished drop lined with spears of stone."),
            ("The Drowned Bell", "grimtooth_lethal_room", "A hanging clapper awakens a crushing surge from concealed cisterns."),
            ("Silt Lung", "grimtooth_lethal_room", "A tight chamber collapses into choking silt and black water when hurried."),
        ],
        "keys": [
            ("tide_mark", "floodgate", "floodgate"),
            ("pearl_key", "shell_lock", "shell lock"),
            ("ferryman_charm", "current_seal", "current seal"),
            ("sluice_pin", "sluice_gate", "sluice gate"),
        ],
        "solo_monsters": [
            ("Cave Hydra", "A pale multi-necked reptile that hunts by ripples and retreats into deep water."),
            ("Hook-Tooth Eel", "A rope-thick eel that lunges from flooded cracks and drags prey sideways."),
            ("The Blind Salamander", "A white giant salamander that owns the warmest pools."),
            ("Shellback Maw", "An armored cave horror that wedges itself into chokepoints and waits."),
        ],
        "bosses": ["Mother of Froth", "The Pearl Tyrant", "King Below the Drips", "The Drowned Matron", "Old Red Gill", "The Underpool Shepherd", "Hookjaw Patriarch", "Mist Below the Shelf"],
        "factions": [
            ("Fungus Shepherds", "spore beds, damp shelter, and captives to feed the rot"),
            ("Tidecutters", "dry ropeways, hidden caches, and control of the upper ledges"),
            ("Mud Eaters", "warm pools, eggs, and anything soft enough to drown"),
            ("Drip Kin", "mushrooms, scavenged copper, and safe sleeping shelves"),
        ],
        "atmospheres": [
            "wet stone and cold mineral water",
            "rotting reeds and cave musk",
            "echoes over unseen pools",
            "slick limestone and old guano",
            "fungus spores drifting in torchlight",
            "brine, damp rope, and stale fish",
        ],
        "contents": [
            "slick ledges and hanging roots",
            "fungus mats and gnawed shells",
            "rope anchors and water-worn crates",
            "dripping stalactites and old climbing spikes",
            "black pools and dead lanterns",
            "flood marks cut high into stone",
        ],
        "treasures": ["black pearl string", "waterproof smugglers' ledger", "pouch of river silver", "glowcap resin", "bronze diving mask", "sealed trade cask"],
        "weird_npcs": ["half-drowned ferryman who swears the cave remembers names", "cave child with a pocket full of pearls and no pupils"],
    },
    "dwarven": {
        "label": "dwarven underworks",
        "pitch": "a worked stone complex of foundries, locks, pressure doors, and bitter grudges",
        "site_names_first": ["Iron", "Granite", "Ember", "Rune", "Deep", "Hammer"],
        "site_names_second": ["Works", "Hall", "Vault", "Foundry", "Delve", "Archive"],
        "room_name_parts": {
            "start": ["Broken Lift", "Outer Sluice", "Collapsed Ramp", "Watch Entry"],
            "hub": ["Gear Court", "Cross-Hall", "Ore Junction", "Anvil Crossing"],
            "boss": ["King's Lock", "Anvil Throne", "Deep Engine", "The Final Forge"],
            "puzzle": ["Counterweight Hall", "Rune Lock", "Valve Choir", "Weight Bridge"],
            "approach": ["Chain Walk", "Upper Conduit", "Smiths' Gallery", "Engine Spine"],
            "treasure": ["Pay Chest", "Tool Vault", "Mint Niche", "Survey Locker"],
            "generic": ["Collapsed Workshop", "Ore Store", "Boiler Room", "Masons' Rest", "Bolt Gallery", "Dust Forge"],
        },
        "trap_rooms": [
            ("Stamp Mill", "grimtooth_lethal_room", "A dead mill line still wakes to pound anything standing on the wrong plates."),
            ("Counterweight Well", "grimtooth_lethal_room", "A false service shaft yanks the careless into moving stone and iron teeth."),
            ("Anvil Drop", "grimtooth_lethal_room", "The chamber rewards greed with a descending block the size of a wagon."),
            ("Boiler Maw", "grimtooth_lethal_room", "A split steam line can cook a whole room if the wrong valve is touched."),
        ],
        "keys": [
            ("rune_keyblock", "rune_lock", "rune lock"),
            ("foreman_seal", "gear_gate", "gear gate"),
            ("counterweight_pin", "counterweight_gate", "counterweight gate"),
            ("master_chain", "chain_lock", "chain lock"),
        ],
        "solo_monsters": [
            ("Chain Ogre", "A forge-bred brute that drags linked hooks through narrow halls."),
            ("Clockwork Warden", "A damaged bronze sentinel that still follows its last kill-order."),
            ("Coal Wyrm", "A soot-scaled burrower nesting in the warm slag runs."),
            ("Grudge Revenant", "An armored dwarf dead of betrayal and not yet willing to stop."),
        ],
        "bosses": ["The Last Overseer", "Runelord in Rust", "The Slag King", "Master of the Dead Forge", "Keeper Brass-Eye", "The Chain Chancellor", "Granite Widow", "Foreman Without Sleep"],
        "factions": [
            ("Hammer Gnawers", "scrap iron, fungus beer, and somewhere defensible to squat"),
            ("Cinder Dwarves", "ancestral locks, furnace cores, and proof the halls are still theirs"),
            ("Rope Guild Breakers", "pay chests, maps, and control of the lifts"),
            ("Tunnel Skinners", "ore carts, bones, and sharp salvage"),
        ],
        "atmospheres": [
            "old soot caught in worked stone",
            "iron dust and stale steam",
            "machine oil over cold granite",
            "metallic echoes through precise halls",
            "slag grit under every bootstep",
            "sealed air and ancient forge smoke",
        ],
        "contents": [
            "fallen braces and stonecut marks",
            "locked tool chests and chain runs",
            "cracked runestones and slag heaps",
            "ore carts and jammed gears",
            "boiler valves and hanging hooks",
            "survey markers hammered into the floor",
        ],
        "treasures": ["engraved dwarf gold", "rune key-block", "masterwork chisel set", "ledger of ore claims", "temper-steel blade blank", "sealed pay coffer"],
        "weird_npcs": ["old surveyor ghost still taking measurements", "trap-smith sealed inside a maintenance niche"],
    },
    "demonic": {
        "label": "demonic catacombs",
        "pitch": "a blasphemous undercrypt of blood altars, sacrificial passages, and doors that should stay closed",
        "site_names_first": ["Crimson", "Blasphemous", "Horned", "Infernal", "Bleak", "Hex"],
        "site_names_second": ["Catacombs", "Pits", "Shrine", "Crypt", "Sepulchre", "Vault"],
        "room_name_parts": {
            "start": ["Broken Ossuary", "Blood Steps", "Coffin Mouth", "Mourning Descent"],
            "hub": ["Red Junction", "Torment Court", "The Forked Nave", "Skull Crossing"],
            "boss": ["Infernal Choir", "Throne of Horns", "The Black Pit", "Last Sacrament"],
            "puzzle": ["Chain Chapel", "Mirror of Sin", "Bone Dial", "Vow Gate"],
            "approach": ["Flensing Walk", "Brass Catwalk", "Whisper Gallery", "Rib Passage"],
            "treasure": ["Votive Cache", "Heretic Strongbox", "Bone Treasury", "Hex Locker"],
            "generic": ["Bone Gallery", "Ash Mortuary", "Skin Archive", "Black Chapel", "Coffin Hall", "Soot Sepulchre"],
        },
        "trap_rooms": [
            ("Choir of Knives", "grimtooth_lethal_room", "A false litany wakes descending blades from every arch."),
            ("Blood Tithe Bridge", "grimtooth_lethal_room", "The bridge demands weight, then takes far more than offered."),
            ("Coffin Press", "grimtooth_lethal_room", "Stone biers slide inward and pulp anyone who trusts the center aisle."),
            ("The Red Swing", "grimtooth_lethal_room", "A pendulum idol punishes hesitation and panic alike."),
        ],
        "keys": [
            ("blood_signet", "blood_seal", "blood seal"),
            ("bone_tally", "ossuary_lock", "ossuary lock"),
            ("vow_chain", "vow_gate", "vow gate"),
            ("red_oil_key", "heretic_lock", "heretic lock"),
        ],
        "solo_monsters": [
            ("Maw Saint", "A flayed saint-thing that speaks softly before it tears."),
            ("Chain Devil", "A horned gaoler dragging live chains that hate escape."),
            ("Candle Ghoul", "A thin corpse predator that steals light before flesh."),
            ("The Skin Bishop", "A ritual butcher wrapped in stitched parchments and old faces."),
        ],
        "bosses": ["Bishop of Horns", "The Red Bride", "Arch-Penitent Malvek", "Mother Sepulchre", "The Eater Below the Altar", "The Candle Prelate", "Rector of Hooks", "The Coffin Choir"],
        "factions": [
            ("Red Novices", "fresh victims, lit altars, and approval from below"),
            ("Bone Collectors", "skulls, marrow, and quiet burial chambers"),
            ("Tallow Thieves", "candles, rendered fat, and exits no priest knows"),
            ("Grave Apostates", "forbidden books, surviving kin, and revenge"),
        ],
        "atmospheres": [
            "clotted incense and cold iron",
            "old blood rubbed into stone",
            "wax smoke and grave dust",
            "murmured prayers from rooms that should be empty",
            "brass heat around black altars",
            "sweet rot behind sealed doors",
        ],
        "contents": [
            "bone altars and votive gutters",
            "broken coffins and wax drippings",
            "chains, censers, and butcher hooks",
            "shuttered confessionals and cracked icons",
            "skull piles and soot-black walls",
            "ritual knives laid out too neatly",
        ],
        "treasures": ["obsidian idol", "blood ruby rosary", "forbidden prayer roll", "golden funeral mask", "tallow cask stamped with sigils", "grave-coin satchel"],
        "weird_npcs": ["escaped novice hiding beneath a bier", "mourner who insists the dead are still listening"],
    },
    "rooted": {
        "label": "root-choked warrens",
        "pitch": "an overgrown under-site where roots, old masonry, vermin, and half-buried shrines have fused together",
        "site_names_first": ["Root", "Thorn", "Green", "Moss", "Briar", "Verdigris"],
        "site_names_second": ["Warrens", "Burrows", "Halls", "Vault", "Sanctum", "Underchapel"],
        "room_name_parts": {
            "start": ["Root Cleft", "Buried Door", "Moss Steps", "Fallen Porch"],
            "hub": ["Tangle Court", "Root Crossing", "Collapsed Grove", "Forked Burrow"],
            "boss": ["Heart Root", "The Deep Grove", "Thorn Throne", "Rot Chapel"],
            "puzzle": ["Seed Wheel", "Hollow Idol", "Moon Well", "Root Lattice"],
            "approach": ["Burrow Walk", "Briar Gallery", "Spore Bridge", "Old Drain"],
            "treasure": ["Buried Shrine", "Smugglers' Niche", "Dry Root Vault", "Forgotten Cache"],
            "generic": ["Moss Hall", "Rat Nest", "Overgrown Cellar", "Rot Store", "Thorn Den", "Spore Cell"],
        },
        "trap_rooms": [
            ("Root Snare Pit", "grimtooth_lethal_room", "A quiet floor of loam hides tightening roots and a sharpened drop."),
            ("Spore Lung", "grimtooth_lethal_room", "A closed chamber floods with burning yellow spores if the wrong pod is cut."),
            ("The Green Drop", "grimtooth_lethal_room", "A rotten bridge over a nursery pit only looks strong at first glance."),
            ("Briar Press", "grimtooth_lethal_room", "Thorn walls fold inward when fresh blood touches the stones."),
        ],
        "keys": [
            ("seed_idol", "root_seal", "root seal"),
            ("thorn_token", "briar_gate", "briar gate"),
            ("moonwater_vial", "moon_lock", "moon lock"),
            ("burrow_bone", "burrow_gate", "burrow gate"),
        ],
        "solo_monsters": [
            ("Root Stag", "A blind antlered horror that charges by scent and vibration."),
            ("Moss Bear", "A cave bear overgrown with fungus and nesting biting things."),
            ("The Thorn Mother", "A swollen vine-witch that can move through walls of root."),
            ("Spore Hound", "A rangy tracker that leaves coughing fits where it passes."),
        ],
        "bosses": ["The Green Abbess", "Old Horn in the Deep", "The Rot King", "Mother Briar", "The Buried Gardener", "The Spore Canon", "Root-Crowned Harrower", "The Worm Orchard"],
        "factions": [
            ("Root Cultists", "seeds, blood, and a new season of growth"),
            ("Burrow Goblins", "dry bedding, stolen food, and worm tunnels"),
            ("Mushroom Keepers", "spore chambers, damp peace, and bodies for mulch"),
            ("Thorn Hunters", "skins, antlers, and safe routes through the green dark"),
        ],
        "atmospheres": [
            "wet roots and old brick dust",
            "spore rot under cold earth",
            "green damp and bruised leaves",
            "animal musk in cramped tunnels",
            "soil falling softly from the ceiling",
            "stale shrine air under living growth",
        ],
        "contents": [
            "root curtains and cracked masonry",
            "fungus shelves and burrow spoil",
            "collapsed statuary wrapped in vine",
            "rat bones and gnawed relics",
            "old drains now choked with roots",
            "shrines swallowed by damp earth",
        ],
        "treasures": ["amber seed necklace", "sealed herb chest", "silver pruning knife", "moss-hidden tax box", "jade idol eye", "bag of rare glow spores"],
        "weird_npcs": ["garden hermit who speaks to roots as if they answer", "grave-robber trapped waist-deep in a living wall"],
    },
    "frost": {
        "label": "frozen tomb-complex",
        "pitch": "a dead cold site of sealed crypts, hoarfrost traps, burial goods, and things kept too long in the ice",
        "site_names_first": ["Frost", "Winter", "Pale", "Icebound", "Rime", "White"],
        "site_names_second": ["Tomb", "Vault", "Crypt", "Barrow", "Sepulchre", "Hold"],
        "room_name_parts": {
            "start": ["Snow Stairs", "Frost Gate", "Rimed Descent", "Outer Crypt"],
            "hub": ["White Court", "Cold Crossing", "Hoarfrost Hall", "Forked Tomb"],
            "boss": ["King's Tomb", "Rime Heart", "The Last Barrow", "Ice Throne"],
            "puzzle": ["Mirror Vault", "Frost Dial", "Lantern of Rime", "Funerary Lock"],
            "approach": ["Ice Gallery", "Frozen Walk", "Burial Run", "Wind Bridge"],
            "treasure": ["Grave Goods Niche", "Ice Chest", "Kingsilver Locker", "Barrow Cache"],
            "generic": ["Rimed Ossuary", "Frost Chapel", "Cold Store", "Shield Hall", "Snow Cellar", "Mourners' Gallery"],
        },
        "trap_rooms": [
            ("Rime Drop", "grimtooth_lethal_room", "A glazed floor pitches the unwary into a frozen spear trench."),
            ("The Cold Bell", "grimtooth_lethal_room", "Ringing the wrong chain unleashes a slab of murderous ice."),
            ("White Breath", "grimtooth_lethal_room", "A sealed chamber flash-freezes lungs and fingers within moments."),
            ("King's Slide", "grimtooth_lethal_room", "The burial ramp becomes a lethal chute if weight falls wrong."),
        ],
        "keys": [
            ("kingsilver_seal", "funerary_lock", "funerary lock"),
            ("rime_lantern", "ice_seal", "ice seal"),
            ("grave_oath", "oath_gate", "oath gate"),
            ("antler_key", "barrow_lock", "barrow lock"),
        ],
        "solo_monsters": [
            ("Ice Wight", "A silent dead noble that hunts warmth and open breath."),
            ("Rime Wolf", "A gaunt white predator that circles until someone slips."),
            ("Snow Blind Ogre", "A huge pale brute that smashes by sound in the dark."),
            ("The Pale Bride", "A frost-dead revenant still searching for her wedding hall."),
        ],
        "bosses": ["The White King", "Rime Widow", "Barrow Marshal", "Frost Mother", "The Sealed Prince", "The Hoarfrost Chamberlain", "Queen in the Ice Chapel", "The Last Mourner"],
        "factions": [
            ("Tomb Robbers", "burial goods, dry fire, and a way back out"),
            ("Rime Acolytes", "preserved dead, cold silence, and the old rites"),
            ("Fur-Clad Exiles", "warm rooms, food, and iron worth melting"),
            ("Ghoul Kin", "frozen flesh, marrow, and the lower crypts"),
        ],
        "atmospheres": [
            "dead cold biting through gloves",
            "hoarfrost on worked stone",
            "old cedar smoke trapped in ice",
            "thin air and ringing quiet",
            "funerary spices under freezing dust",
            "snowmelt dripping into dark crypt cracks",
        ],
        "contents": [
            "frozen bier frames and cracked shields",
            "ice-rimmed sarcophagi",
            "burial cloth and snapped spear shafts",
            "frosted murals and old braziers",
            "drifts packed against sealed doors",
            "grave shelves thick with rime",
        ],
        "treasures": ["kingsilver torque", "sealed amber urn", "fur-lined burial cloak", "ice-clear gem", "runed antler bow", "grave ring set with garnets"],
        "weird_npcs": ["snow-blind graverobber wrapped in grave linen", "preserved mourner who wakes only when spoken to"],
    },
}

STYLE_SUBTHEMES = {
    "reliquary": [
        "a saint-house stripped by generations of grave-thieves",
        "a bell-foundry turned secret pilgrimage route",
        "a plague shrine quietly reused by rival sects",
        "a reliquary archive with sealed confession chambers",
        "a martyr crypt whose processional ways were trapped later",
        "a furnace chapel built around an unquiet burial vault",
    ],
    "caverns": [
        "a smugglers' cave system flooded after an old cave-in",
        "a fungus grotto fed by warm mineral vents",
        "a drowned ferry route beneath a sinkhole",
        "a cave shrine swallowed by black water over generations",
        "a pearl cavern contested by scavengers and cave folk",
        "a ropeway network above deep predator pools",
    ],
    "dwarven": [
        "a dead mint and payroll vault beneath the old works",
        "a foundry district shut during a mutiny",
        "a survey complex guarding unfinished deep tunnels",
        "a lift-and-sluice network built to feed a royal forge",
        "a machine hall where the last overseers sealed themselves in",
        "a ruin of chain lifts, ore stores, and grudge shrines",
    ],
    "demonic": [
        "a penitential crypt converted into a sacrificial maze",
        "a funeral underchurch where heretics hid their rites",
        "a chained ossuary built to hold something worse below",
        "a plague catacomb rededicated to infernal vows",
        "a burial shrine twisted into a tallow-smoke cult site",
        "a sepulchre whose lower chambers were carved for offerings, not burials",
    ],
    "rooted": [
        "an old underchapel half-swallowed by living roots",
        "a collapsed cellar network turned into a green cult den",
        "a burrowed shrine-complex full of spore gardens and rat runs",
        "a forgotten tax vault broken open by roots and vermin",
        "an underground herb store rotted into a fungal nursery",
        "a drowned crypt now fused with briar tunnels and sink pits",
    ],
    "frost": [
        "a royal barrow line sealed after a bad winter rite",
        "a glacier-cut crypt full of burial goods and old feuds",
        "a tomb-complex where mourners froze in place around the dead",
        "a snowbound hold used for both burial and last defense",
        "a kingsilver vault trapped beneath ice-choked passages",
        "a funerary shrine where the dead were meant to sleep through the thaw",
    ],
}

STYLE_PUBLIC = {
    "reliquary": {
        "motifs": ["ash", "bells", "saints", "cinders", "relics", "choirs"],
        "places": ["the underchapel", "the reliquary halls", "the bell crypt", "the processional vault"],
        "artifacts": ["a stolen relic", "a saintly object", "a sealed devotional treasure", "a black-market reliquary prize"],
        "rescues": ["a missing novice", "a trapped torchbearer", "a lost cantor", "someone taken for the rites"],
        "bosses": ["a hidden cult leader", "a shrine tyrant", "an unquiet abbot", "a power in the inner shrine"],
        "solos": ["a roaming hunter", "something that stalks by sound", "a patient ambush predator", "an old guardian no one wants to wake"],
        "factions": ["rival claimants", "feuding shrine-dwellers", "desperate scavengers and zealots", "two camps already at knives' edge"],
    },
    "caverns": {
        "motifs": ["blackwater", "sinkstone", "pearls", "ropes", "echoes", "fungus"],
        "places": ["the flooded underways", "the drowned caves", "the blackwater shelves", "the sink tunnels"],
        "artifacts": ["a contraband prize", "a lost chart", "a drowned idol", "something valuable from the deep shelves"],
        "rescues": ["a stranded guide", "a missing diver", "a trapped ferryman", "someone lost beyond the floodgate"],
        "bosses": ["a thing ruling the deep water", "a tyrant of the lower pools", "a predator-lord in the dark water", "something old in the drowned chambers"],
        "solos": ["a lurking water-hunter", "something pale that follows ripples", "a tunnel predator", "a deep thing that owns the warm pools"],
        "factions": ["rival cave crews", "smugglers and locals", "two camps contesting the shelves", "claimants fighting over the dry routes"],
    },
    "dwarven": {
        "motifs": ["iron", "granite", "chains", "gears", "runes", "slag"],
        "places": ["the dead works", "the chain halls", "the old foundry", "the underforge"],
        "artifacts": ["a master key", "a payoff worth hauling out", "a lost tool of office", "something valuable from the sealed works"],
        "rescues": ["a trapped surveyor", "a missing lift-hand", "a wounded prospector", "someone sealed beyond the mechanism halls"],
        "bosses": ["a bitter overseer", "a ruler of the dead forge", "an ancient claimant of the works", "a machine-bound tyrant"],
        "solos": ["a relentless guardian", "a heavy thing that hunts the corridors", "a chained brute", "an old warden still on its rounds"],
        "factions": ["rival salvage crews", "claim-jumpers and holdouts", "two work gangs on the verge of war", "competing scavengers of the old halls"],
    },
    "demonic": {
        "motifs": ["horns", "blood", "chains", "coffins", "wax", "altars"],
        "places": ["the red crypt", "the chained underchurch", "the black catacombs", "the lower shrine"],
        "artifacts": ["a forbidden object", "a ritual prize", "evidence of heresy", "something valuable from a place best left sealed"],
        "rescues": ["a condemned captive", "a chained mourner", "a missing novice", "someone marked for the next rite"],
        "bosses": ["a thing leading the rites", "a power under the altar", "a hidden bishop of the lower dark", "a tyrant of the sacrificial halls"],
        "solos": ["a butcher in the dark", "a light-hungry predator", "something chained that still roams", "a solitary horror stalking the nave"],
        "factions": ["rival cult cells", "survivors and zealots", "two blasphemous camps at odds", "knife-edged alliances in the catacombs"],
    },
    "rooted": {
        "motifs": ["roots", "thorns", "spores", "burrows", "green dark", "moss"],
        "places": ["the root halls", "the buried grove", "the undergrowth below", "the briar vaults"],
        "artifacts": ["a living prize", "a hidden cache worth the risk", "something buried and still wanted", "a green relic from below"],
        "rescues": ["a missing gatherer", "someone trapped in living growth", "a lost hunter", "a taken child or guide"],
        "bosses": ["a power in the roots", "a tyrant of the green dark", "something old feeding on the burrows", "a ruler of the overgrown shrine"],
        "solos": ["a blind charger", "a spoor-tracking beast", "a hunter moving through the walls", "something feral in the growth"],
        "factions": ["rival burrow clans", "hunters and cultists", "two camps fighting through the green dark", "locals contesting the old shrine"],
    },
    "frost": {
        "motifs": ["rime", "ice", "barrows", "kingsilver", "white breath", "grave snow"],
        "places": ["the frozen crypts", "the white barrows", "the ice halls", "the cold sepulchres"],
        "artifacts": ["a burial treasure", "a cold heirloom", "a sealed prize from the dead", "something worth stealing before the thaw"],
        "rescues": ["a missing scout", "a sealed mourner", "a trapped robber", "someone still alive in the cold halls"],
        "bosses": ["a ruler of the frozen dead", "a cold court hidden below", "a power in the barrows", "something old that should have stayed buried"],
        "solos": ["a white hunter", "a cold-stalking revenant", "a thing that circles in the dark", "a predator of breath and warmth"],
        "factions": ["rival grave crews", "survivors and acolytes", "two camps fighting for the warm rooms", "claimants at war in the barrows"],
    },
}

PUBLIC_ADJECTIVES = [
    "black", "buried", "broken", "cold", "cursed", "dark", "forgotten", "hidden", "hollow", "iron",
    "last", "lost", "mortal", "sealed", "silent", "sunless", "shuttered", "unquiet", "veiled", "old",
]

PUBLIC_NOUNS = [
    "altar", "archive", "barrow", "bell", "bridge", "catacomb", "choir", "crypt", "door", "forge",
    "gate", "hall", "idol", "lock", "maze", "path", "passage", "pool", "prize", "road", "route",
    "secret", "shrine", "stone", "throne", "vault", "way", "well", "wound",
]

PATRON_NAMES_FIRST = [
    "Aldren", "Bera", "Calix", "Dessa", "Edda", "Fen", "Garrick", "Hester", "Ivo", "Joren",
    "Ketha", "Lysa", "Mara", "Noll", "Orsik", "Pella", "Quill", "Rusk", "Sera", "Tamn",
]
PATRON_NAMES_LAST = [
    "Vale", "Morrow", "Thorn", "Rill", "Ashdown", "Fenmark", "Crowle", "Hollis", "Vane", "Brindle",
    "Marrow", "Keel", "Dusk", "Rowan", "Sable", "Grint", "Mire", "Tallow", "Rook", "Hearth",
]

STYLE_PATRONS = {
    "reliquary": ["bell-keeper", "grave-tender", "disgraced prior", "relic broker", "chapel widow", "shrine factor"],
    "caverns": ["river factor", "smuggler widow", "rope-master", "ferryman", "pearl buyer", "dock priest"],
    "dwarven": ["paymaster's clerk", "claim-jumper", "forge widow", "charter-holder", "surveyor", "ore broker"],
    "demonic": ["mourner", "ink-stained confessor", "grave broker", "escaped novice", "funeral agent", "heretic hunter"],
    "rooted": ["hedge-witch", "rat-catcher", "herb factor", "field widow", "moss-cutter", "garden sexton"],
    "frost": ["fur factor", "grave claimant", "thaw priest", "barrow widow", "snow guide", "cold-market broker"],
}

STYLE_REWARDS = {
    "reliquary": ["good silver and church silence", "a relic's worth in hard coin", "absolution and a purse besides", "enough silver to forget the smell of incense"],
    "caverns": ["river silver and a dry bed", "contraband coin with no questions asked", "a pearl-cut share of the take", "more money than honest ferry work pays in a season"],
    "dwarven": ["mint silver and first claim on salvage", "a ledger-backed payout", "tool steel, coin, and a written share", "enough stamped coin to finance the next descent"],
    "demonic": ["quiet coin and a sealed confession", "grave silver and no further questions", "enough pay to make blasphemy feel practical", "a purse heavy enough to outweigh good judgment"],
    "rooted": ["herb silver and safe shelter", "a cut of the resale and fresh bandages", "coin, poultices, and a place by the stove", "enough money to make the spores worth breathing"],
    "frost": ["kingsilver and a warm roof", "grave coin and a winter's meat", "enough pay to see out the cold months", "silver, furs, and a fire already lit"],
}


def _load_fragment_cache() -> dict[tuple[str, str], list[str]]:
    global _FRAGMENT_CACHE
    if _FRAGMENT_CACHE is not None:
        return _FRAGMENT_CACHE
    cache: dict[tuple[str, str], list[str]] = {}
    if DELVEKIT_FRAGMENT_CSV.exists():
        with DELVEKIT_FRAGMENT_CSV.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                style = (row.get("style") or "").strip()
                category = (row.get("category") or "").strip()
                values = (row.get("values") or "").strip()
                if not style or not category or not values:
                    continue
                parts = [item.strip() for item in values.split("|") if item.strip()]
                if parts:
                    cache.setdefault((style, category), []).extend(parts)
    _FRAGMENT_CACHE = cache
    return cache


def _fragment_pool(style_key: str, category: str, fallback: list[str] | None = None) -> list[str]:
    cache = _load_fragment_cache()
    specific = cache.get((style_key, category), [])
    shared = [] if style_key == "*" else cache.get(("*", category), [])
    pool = [*specific, *shared]
    return pool or list(fallback or [])


def _one_of(rng: Random, style_key: str, category: str, fallback: list[str]) -> str:
    pool = _fragment_pool(style_key, category, fallback)
    return rng.choice(pool)


def _build_phrase(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip()).strip()


def _compose_site_name(style_key: str, rng: Random, fallback_style: dict[str, Any]) -> str:
    first = _one_of(rng, style_key, "site_first", _style_pool(fallback_style, "site_names_first"))
    second = _one_of(rng, style_key, "site_second", _style_pool(fallback_style, "site_names_second"))
    return _build_phrase(first, second)


def _compose_faction(style_key: str, rng: Random) -> tuple[str, str]:
    prefix = _one_of(rng, style_key, "faction_prefix", ["Hidden"])
    suffix = _one_of(rng, style_key, "faction_suffix", ["Knives"])
    want = _one_of(rng, style_key, "faction_want", ["safer rooms and something worth keeping"])
    return _build_phrase(prefix, suffix), want


def _compose_faction_profile(style_key: str, rng: Random) -> dict[str, str]:
    name, want = _compose_faction(style_key, rng)
    culture = _one_of(rng, style_key, "faction_culture", ["hard-eyed squatters with old grudges"])
    loadout = _one_of(rng, style_key, "faction_loadout", ["patched armor and ugly knives"])
    tactic = _one_of(rng, style_key, "faction_tactic", ["prefer ambushes and quick retreats"])
    return {
        "name": name,
        "want": want,
        "culture": culture,
        "loadout": loadout,
        "tactic": tactic,
    }


def _compose_boss(style_key: str, rng: Random) -> str:
    title = _one_of(rng, style_key, "boss_title", ["Warden"])
    noun = _title_focus_text(_one_of(rng, style_key, "public_motif", ["Ash"]))
    place = _title_focus_text(_without_leading_article(_one_of(rng, style_key, "public_place", ["the undercrypt"])))
    pattern = rng.choice(
        [
            f"The {title} of the {place}",
            f"The {noun} {title}",
            f"{title} of {place}",
            f"The {title} Beneath the {place}",
        ]
    )
    return pattern


def _compose_solo(style_key: str, rng: Random) -> tuple[str, str]:
    adjective = _one_of(rng, style_key, "solo_adj", ["Blind"])
    noun = _one_of(rng, style_key, "solo_noun", ["Hunter"])
    hunt = _one_of(rng, style_key, "solo_hunt", ["returns to the same dark route again and again"])
    name = f"{adjective} {noun}"
    return name, f"A {name.lower()} that {hunt}."


def _compose_treasure(style_key: str, rng: Random) -> str:
    adjective = _one_of(rng, style_key, "treasure_adj", ["sealed"])
    noun = _one_of(rng, style_key, "treasure_noun", ["coffer"])
    return _build_phrase(adjective, noun)


def _compose_weird_npc(style_key: str, rng: Random) -> str:
    trait = _one_of(rng, style_key, "npc_trait", ["wounded"])
    role = _one_of(rng, style_key, "npc_role", ["guide"])
    condition = _one_of(rng, style_key, "npc_condition", ["hiding behind a fallen screen"])
    return _build_phrase(trait, role, condition)


def _compose_rescue_target(style_key: str, rng: Random) -> str:
    return _one_of(rng, style_key, "rescue_target", ["someone missing below"])


def _compose_recruit_target(style_key: str, rng: Random) -> str:
    return _one_of(rng, style_key, "recruit_target", ["someone below with reasons to deal"])


def _compose_treasure_objective(style_key: str, rng: Random) -> str:
    return _one_of(rng, style_key, "treasure_objective", ["leave with enough treasure to matter"])


def _compose_monster_group(style_key: str, rng: Random) -> dict[str, str]:
    family = _one_of(rng, style_key, "monster_family", ["vermin pack"])
    role = _one_of(rng, style_key, "monster_role", ["lurkers"])
    trait = _one_of(rng, style_key, "monster_trait", ["drawn to blood and noise"])
    sign = _one_of(rng, style_key, "monster_sign", ["old droppings and gnawed scraps"])
    return {
        "name": _build_phrase(family, role),
        "trait": trait,
        "sign": sign,
    }


def load_dungeon(path: str | Path) -> dict[str, Any]:
    payload = _sslib.load_yaml(Path(path))
    validate_dungeon(payload)
    return payload


def save_dungeon(path: str | Path, data: dict[str, Any]) -> None:
    validate_dungeon(data)
    _sslib.save_yaml(Path(path), data)


def validate_dungeon(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the current Delvekit schema without rewriting old inputs."""
    if not isinstance(data, dict):
        raise ValueError("dungeon data must be a mapping")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported dungeon schema_version: {data.get('schema_version')!r}")

    dungeon = data.get("dungeon")
    required_dungeon = {
        "id", "name", "style", "style_label", "subtheme", "skin", "addon",
        "size", "difficulty", "start_room", "hook_type", "hook_summary",
        "hook_target", "pitch_skeleton", "title_draft", "player_blurb_draft",
        "player_blurb", "character_motivation",
    }
    if not isinstance(dungeon, dict):
        raise ValueError("dungeon section is missing or invalid")
    missing_dungeon = sorted(required_dungeon - set(dungeon))
    if missing_dungeon:
        raise ValueError(f"dungeon section missing keys: {', '.join(missing_dungeon)}")
    if dungeon["style"] not in STYLE_PACKS:
        raise ValueError(f"unknown Delvekit style: {dungeon['style']}")

    rooms = data.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        raise ValueError("dungeon rooms must be a non-empty list")
    required_room = {
        "id", "name", "x", "y", "description", "atmosphere", "contents", "exits",
        "secret_exits", "locks", "trap_tags", "puzzle_tags", "faction_tags",
        "solo_monster_tags", "boss_tags", "treasure_tags", "role_tags", "discovered",
    }
    for room in rooms:
        if not isinstance(room, dict):
            raise ValueError("each dungeon room must be a mapping")
        missing_room = sorted(required_room - set(room))
        if missing_room:
            raise ValueError(f"room {room.get('id', '?')} missing keys: {', '.join(missing_room)}")
        discovered = room["discovered"]
        if not isinstance(discovered, dict) or not {"room", "visible_exits", "secret_exits", "notes"} <= set(discovered):
            raise ValueError(f"room {room.get('id', '?')} has invalid discovered state")

    required_top_level = {"keys", "factions", "monster_groups", "solo_monsters", "bosses", "weird_npcs", "player_map"}
    missing_top_level = sorted(required_top_level - set(data))
    if missing_top_level:
        raise ValueError(f"dungeon data missing keys: {', '.join(missing_top_level)}")
    player_map = data["player_map"]
    if not isinstance(player_map, dict):
        raise ValueError("player_map must be a mapping")
    missing_map = sorted({"discovered_rooms", "discovered_connections", "discovered_secret_connections", "current_room"} - set(player_map))
    if missing_map:
        raise ValueError(f"player_map missing keys: {', '.join(missing_map)}")
    return data


def room_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(room["id"]): room for room in data.get("rooms", [])}


def edge_key(a: str, b: str) -> str:
    left, right = sorted((str(a), str(b)))
    return f"{left}|{right}"


def neighbors(data: dict[str, Any], include_secret: bool = False) -> dict[str, set[str]]:
    idx = room_index(data)
    out = {rid: set() for rid in idx}
    for room in idx.values():
        rid = str(room["id"])
        for item in room.get("exits", []):
            target = str(item["to"])
            if target in idx:
                out[rid].add(target)
        if include_secret:
            for item in room.get("secret_exits", []):
                target = str(item["to"])
                if target in idx:
                    out[rid].add(target)
    return out


def shortest_paths(data: dict[str, Any], start: str) -> tuple[dict[str, int], dict[str, str | None]]:
    graph = neighbors(data)
    dist = {str(start): 0}
    parent: dict[str, str | None] = {str(start): None}
    queue = deque([str(start)])
    while queue:
        current = queue.popleft()
        for nxt in sorted(graph.get(current, [])):
            if nxt in dist:
                continue
            dist[nxt] = dist[current] + 1
            parent[nxt] = current
            queue.append(nxt)
    return dist, parent


def subtree_sizes(parent: dict[str, str | None]) -> dict[str, int]:
    sizes = Counter({rid: 1 for rid in parent})
    ordered = sorted(parent.items(), key=lambda item: 0 if item[1] is None else 1, reverse=True)
    for rid, p in ordered:
        if p is None:
            continue
        sizes[p] += sizes[rid]
    return dict(sizes)


def all_edge_meta(data: dict[str, Any]) -> list[dict[str, Any]]:
    idx = room_index(data)
    seen: set[tuple[str, str, str]] = set()
    meta: list[dict[str, Any]] = []
    for room in idx.values():
        rid = str(room["id"])
        for kind in ("exits", "secret_exits"):
            for item in room.get(kind, []):
                target = str(item["to"])
                if target not in idx:
                    continue
                pair = tuple(sorted((rid, target)) + [kind])
                if pair in seen:
                    continue
                seen.add(pair)
                label = item.get("map_label") or item.get("label")
                locks = []
                if kind == "exits":
                    for side in (idx[rid], idx[target]):
                        for lock in side.get("locks", []):
                            if str(lock.get("blocks_exit_to")) == (target if side is idx[rid] else rid):
                                locks.append(lock)
                meta.append(
                    {
                        "a": pair[0],
                        "b": pair[1],
                        "kind": "secret" if kind == "secret_exits" else "regular",
                        "label": label,
                        "locks": locks,
                    }
                )
    return meta


def _choose_count(rng: Random, low_high: tuple[int, int]) -> int:
    low, high = low_high
    return rng.randint(low, high)


def _pick_style(rng: Random) -> tuple[str, dict[str, Any]]:
    style_key = rng.choice(sorted(STYLE_PACKS))
    return style_key, STYLE_PACKS[style_key]


def _style_pool(style: dict[str, Any], key: str, fallback: list[Any] | None = None) -> list[Any]:
    return list(style.get(key, fallback or []))


def _pick_subtheme(rng: Random, style_key: str) -> str:
    pool = _fragment_pool(style_key, "subtheme", STYLE_SUBTHEMES.get(style_key, []))
    if not pool:
        return "an old underplace with too many secrets left intact"
    return rng.choice(pool)


def _with_article(noun_phrase: str) -> str:
    lowered = noun_phrase.lower()
    if lowered.startswith(("the ", "a ", "an ")):
        return noun_phrase
    return f"the {noun_phrase}"


def _without_leading_article(noun_phrase: str) -> str:
    lowered = noun_phrase.lower()
    for prefix in ("the ", "a ", "an "):
        if lowered.startswith(prefix):
            return noun_phrase[len(prefix):]
    return noun_phrase


def _title_focus_text(text: str) -> str:
    text = _without_leading_article(text).strip()
    if not text:
        return "Delve"
    if any(char.isupper() for char in text[1:]):
        return text
    return text.title()




def _choose_title_variant(rng: Random, variants: list[str]) -> str:
    cleaned = [item for item in variants if item]
    if not cleaned:
        return "Delve"
    return rng.choice(cleaned)


def _public_pool(style_key: str, key: str, fallback: list[str]) -> list[str]:
    category_map = {
        "motifs": "public_motif",
        "places": "public_place",
    }
    category = category_map.get(key)
    if category:
        pool = _fragment_pool(style_key, category, [])
        if pool:
            return pool
    return list(STYLE_PUBLIC.get(style_key, {}).get(key, fallback))


def _with_indefinite_article(phrase: str) -> str:
    stripped = phrase.strip()
    if not stripped:
        return phrase
    lowered = stripped.lower()
    if lowered.startswith(("the ", "a ", "an ")):
        return stripped
    article = "an" if stripped[0].lower() in "aeiou" else "a"
    return f"{article} {stripped}"


def _english_join(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _format_title_template(template: str, teaser: dict[str, str]) -> str:
    return template.format(
        adjective=_title_focus_text(teaser["adjective"]),
        noun=_title_focus_text(teaser["noun"]),
        place=teaser["place_focus"],
        motif=_title_focus_text(teaser["motif"]),
        motif_2=_title_focus_text(teaser["motif_2"]),
    )


def _public_teaser(style_key: str, rng: Random) -> dict[str, str]:
    motifs = _public_pool(style_key, "motifs", ["shadow", "stone", "dust"])
    places = _public_pool(style_key, "places", ["the underways", "the vaults"])
    motif = rng.choice(motifs)
    other_motifs = [item for item in motifs if item != motif]
    motif_2 = rng.choice(other_motifs or motifs)
    place = rng.choice(places)
    adjective = rng.choice(PUBLIC_ADJECTIVES)
    noun = rng.choice(PUBLIC_NOUNS)
    return {
        "motif": motif,
        "motif_2": motif_2,
        "place": place,
        "adjective": adjective,
        "noun": noun,
        "title_focus": _title_focus_text(f"{adjective} {noun}"),
        "place_focus": _title_focus_text(place),
    }


def _public_patron(style_key: str, rng: Random) -> dict[str, str]:
    first = _one_of(rng, style_key, "patron_first", PATRON_NAMES_FIRST)
    last = _one_of(rng, style_key, "patron_last", PATRON_NAMES_LAST)
    role = _one_of(rng, style_key, "patron_role", STYLE_PATRONS.get(style_key, ["fixer", "widow", "factor"]))
    reward = _one_of(rng, style_key, "reward", STYLE_REWARDS.get(style_key, ["good silver and no questions"]))
    return {
        "name": f"{first} {last}",
        "role": role,
        "full": f"{first} {last}, {_with_indefinite_article(role)}",
        "reward": reward,
    }








def generate_dungeon(*, seed: int, size: str, difficulty: str, title: str | None = None) -> dict[str, Any]:
    from _delvekit_prose import build_module_blurb

    if size not in SIZE_CONFIG:
        raise ValueError(f"unknown size '{size}'")
    if difficulty not in DIFFICULTY_KNOBS:
        raise ValueError(f"unknown difficulty '{difficulty}'")

    rng = Random(seed)
    style_key, style = _pick_style(rng)
    subtheme = _pick_subtheme(rng, style_key)
    rooms_target = _choose_count(rng, SIZE_CONFIG[size]["rooms"])
    coords, regular_pairs = _generate_layout(rng, rooms_target)
    extra_pairs = _add_regular_loops(rng, coords, regular_pairs, SIZE_CONFIG[size]["loops"])
    secret_pairs = _add_secret_links(rng, coords, regular_pairs | extra_pairs, SIZE_CONFIG[size]["secrets"])

    rooms = []
    id_by_coord = {}
    for index, coord in enumerate(coords, start=1):
        rid = str(index)
        id_by_coord[coord] = rid
        rooms.append(
            {
                "id": rid,
                "name": f"Room {rid}",
                "x": coord[0],
                "y": coord[1],
                "description": "",
                "atmosphere": "",
                "contents": [],
                "exits": [],
                "secret_exits": [],
                "locks": [],
                "trap_tags": [],
                "puzzle_tags": [],
                "faction_tags": [],
                "solo_monster_tags": [],
                "boss_tags": [],
                "treasure_tags": [],
                "role_tags": [],
                "discovered": {"room": rid == "1", "visible_exits": [], "secret_exits": [], "notes": []},
            }
        )
    by_id = {room["id"]: room for room in rooms}

    for left, right in sorted(regular_pairs | extra_pairs):
        a = id_by_coord[left]
        b = id_by_coord[right]
        _connect_regular(by_id[a], by_id[b], left, right)
        _connect_regular(by_id[b], by_id[a], right, left)

    for left, right in sorted(secret_pairs):
        a = id_by_coord[left]
        b = id_by_coord[right]
        _connect_secret(by_id[a], by_id[b], left, right)
        _connect_secret(by_id[b], by_id[a], right, left)

    generated_name = title or _generated_site_name(rng, style)
    data = {
        "schema_version": SCHEMA_VERSION,
        "dungeon": {
            "id": _sslib.slugify(generated_name, fallback="delvekit_site"),
            "name": generated_name,
            "style": style_key,
            "style_label": style["label"],
            "style_pitch": style["pitch"],
            "subtheme": subtheme,
            "skin": "candlelight_dungeons",
            "addon": "candlelight_delvekit",
            "size": size,
            "difficulty": difficulty,
            "seed": seed,
            "start_room": "1",
            "difficulty_knobs": DIFFICULTY_KNOBS[difficulty],
        },
        "rooms": rooms,
        "keys": [],
        "factions": [],
        "monster_groups": [],
        "solo_monsters": [],
        "bosses": [],
        "weird_npcs": [],
        "player_map": {
            "discovered_rooms": ["1"],
            "discovered_connections": [],
            "discovered_secret_connections": [],
            "current_room": "1",
        },
    }

    dist, parent = shortest_paths(data, "1")
    sizes_map = subtree_sizes(parent)
    hub_id = _pick_hub(data)
    farthest = max(dist, key=lambda rid: (dist[rid], rid))
    branch_key = _maybe_add_keyed_progression(data, rng, dist, parent, sizes_map, difficulty, style)

    feature_rolls = DIFFICULTY_KNOBS[difficulty]
    trap_room_id = _maybe_add_trap_room(data, rng, feature_rolls["trap_room_prob"], style)
    puzzle_rooms = _add_puzzles(data, rng, size, style, forbidden={trap_room_id} if trap_room_id else set())
    _add_treasures(data, rng, size, style)
    _add_weird_npc(data, rng, feature_rolls["weird_npc_prob"], style)
    _add_factions(data, rng, feature_rolls["faction_prob"], style)
    _add_monster_ecology(data, rng, size)
    boss_id = _maybe_add_boss(data, rng, feature_rolls["boss_prob"], farthest, style)
    solo_candidates = []
    if boss_id and parent.get(boss_id):
        solo_candidates.append(parent[boss_id])
    solo_candidates.append(farthest)
    solo_id = _maybe_add_solo_monster(
        data,
        rng,
        feature_rolls["solo_prob"],
        solo_candidates,
        style,
        forbidden={boss_id} if boss_id else set(),
    )
    _ensure_tiny_feature_budget(data, rng, difficulty, style, dist, parent, sizes_map, farthest, hub_id)
    _ensure_soft_challenge(data, rng, style, dist, parent, sizes_map, farthest)

    for room in data["rooms"]:
        rid = room["id"]
        if rid == "1":
            room["role_tags"].append("start")
        if rid == hub_id:
            room["role_tags"].append("hub")
        if rid == farthest:
            room["role_tags"].append("deep")
        if branch_key and rid == branch_key["key_room"]:
            room["role_tags"].append("key_room")
        if trap_room_id and rid == trap_room_id:
            room["role_tags"].append("trap_room")
        if boss_id and rid == boss_id:
            room["role_tags"].append("boss_room")
        if solo_id and rid == solo_id:
            room["role_tags"].append("approach")
        if rid in puzzle_rooms:
            room["role_tags"].append("puzzle_room")
        room["role_tags"] = sorted(set(room.get("role_tags", [])))

    _name_and_describe_rooms(data, rng, style)
    hook_seed = f"{seed}:{size}:{difficulty}:{style_key}:hook"
    _add_player_hook(data, Random(hook_seed))
    if not title:
        title_rng = Random(f"{hook_seed}:title")
        generated_name, polished_blurb = build_module_blurb(data, title_rng)
        data["dungeon"]["title_draft"] = generated_name
        data["dungeon"]["player_blurb_draft"] = polished_blurb
        data["dungeon"]["name"] = generated_name
        data["dungeon"]["id"] = _sslib.slugify(generated_name, fallback="delvekit_site")
        data["dungeon"]["player_blurb"] = polished_blurb
    else:
        _, polished_blurb = build_module_blurb(data, Random(f"{hook_seed}:title"))
        data["dungeon"]["title_draft"] = title
        data["dungeon"]["player_blurb_draft"] = polished_blurb
        data["dungeon"]["player_blurb"] = polished_blurb
    validate_dungeon(data)
    return data


def _generate_layout(rng: Random, rooms_target: int) -> tuple[list[tuple[int, int]], set[tuple[tuple[int, int], tuple[int, int]]]]:
    coords = [(0, 0)]
    taken = {(0, 0)}
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    while len(coords) < rooms_target:
        base = rng.choice(coords)
        rng.shuffle(directions)
        placed = False
        for dx, dy in directions:
            nxt = (base[0] + dx, base[1] + dy)
            if nxt in taken:
                continue
            taken.add(nxt)
            coords.append(nxt)
            edges.add(tuple(sorted((base, nxt))))
            placed = True
            break
        if not placed:
            continue
    return coords, edges


def _adjacent_pairs(coords: list[tuple[int, int]]) -> set[tuple[tuple[int, int], tuple[int, int]]]:
    coord_set = set(coords)
    out = set()
    for x, y in coords:
        for dx, dy in ((1, 0), (0, 1)):
            nxt = (x + dx, y + dy)
            if nxt in coord_set:
                out.add(tuple(sorted(((x, y), nxt))))
    return out


def _add_regular_loops(
    rng: Random,
    coords: list[tuple[int, int]],
    edges: set[tuple[tuple[int, int], tuple[int, int]]],
    count_range: tuple[int, int],
) -> set[tuple[tuple[int, int], tuple[int, int]]]:
    candidates = list(_adjacent_pairs(coords) - edges)
    rng.shuffle(candidates)
    want = min(len(candidates), _choose_count(rng, count_range))
    return set(candidates[:want])


def _add_secret_links(
    rng: Random,
    coords: list[tuple[int, int]],
    occupied: set[tuple[tuple[int, int], tuple[int, int]]],
    count_range: tuple[int, int],
) -> set[tuple[tuple[int, int], tuple[int, int]]]:
    candidates = list(_adjacent_pairs(coords) - occupied)
    rng.shuffle(candidates)
    want = min(len(candidates), _choose_count(rng, count_range))
    return set(candidates[:want])


def _direction_label(src: tuple[int, int], dst: tuple[int, int]) -> str:
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    if dx == 1:
        return "east passage"
    if dx == -1:
        return "west passage"
    if dy == 1:
        return "south passage"
    if dy == -1:
        return "north passage"
    return "passage"


def _connect_regular(room: dict[str, Any], other: dict[str, Any], src: tuple[int, int], dst: tuple[int, int]) -> None:
    room["exits"].append({"to": other["id"], "label": _direction_label(src, dst)})


def _connect_secret(room: dict[str, Any], other: dict[str, Any], src: tuple[int, int], dst: tuple[int, int]) -> None:
    room["secret_exits"].append({"to": other["id"], "label": _direction_label(src, dst), "map_label": "secret door"})


def _feature_flags(data: dict[str, Any]) -> dict[str, bool]:
    rooms = data.get("rooms", [])
    return {
        "keyed": bool(data.get("keys")),
        "secret_route": any(room.get("secret_exits") for room in rooms),
        "trap": any(room.get("trap_tags") for room in rooms),
        "puzzle": any(room.get("puzzle_tags") for room in rooms),
        "solo": bool(data.get("solo_monsters")),
        "weird_npc": bool(data.get("weird_npcs")),
    }


def _has_route_complexity(data: dict[str, Any]) -> bool:
    rooms = data.get("rooms", [])
    puzzle_count = sum(1 for room in rooms if room.get("puzzle_tags"))
    return bool(data.get("keys")) or any(room.get("secret_exits") for room in rooms) or puzzle_count > 1


def _maybe_add_forced_secret_route(data: dict[str, Any], rng: Random) -> bool:
    if any(room.get("secret_exits") for room in data.get("rooms", [])):
        return False
    coords = [(room["x"], room["y"]) for room in data["rooms"]]
    id_by_coord = {(room["x"], room["y"]): room["id"] for room in data["rooms"]}
    occupied: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for room in data["rooms"]:
        src = (room["x"], room["y"])
        for exit_info in room.get("exits", []):
            other = room_index(data).get(str(exit_info["to"]))
            if other:
                occupied.add(tuple(sorted((src, (other["x"], other["y"])))))
        for exit_info in room.get("secret_exits", []):
            other = room_index(data).get(str(exit_info["to"]))
            if other:
                occupied.add(tuple(sorted((src, (other["x"], other["y"])))))
    candidates = list(_adjacent_pairs(coords) - occupied)
    if not candidates:
        return False
    left, right = rng.choice(candidates)
    a = room_index(data)[id_by_coord[left]]
    b = room_index(data)[id_by_coord[right]]
    _connect_secret(a, b, left, right)
    _connect_secret(b, a, right, left)
    return True


def _pick_hub(data: dict[str, Any]) -> str:
    graph = neighbors(data)
    depth, _ = shortest_paths(data, "1")
    return max(graph, key=lambda rid: (len(graph[rid]), -depth.get(rid, 99), -int(rid)))


def _maybe_add_keyed_progression(
    data: dict[str, Any],
    rng: Random,
    depth: dict[str, int],
    parent: dict[str, str | None],
    sizes: dict[str, int],
    difficulty: str,
    style: dict[str, Any],
    *,
    force: bool = False,
) -> dict[str, str] | None:
    if not force and rng.random() > DIFFICULTY_KNOBS[difficulty]["keyed_prob"]:
        return None

    rooms = room_index(data)
    candidates = []
    for child, par in parent.items():
        if par is None:
            continue
        if depth.get(child, 0) < 2:
            continue
        if sizes.get(child, 0) < 2:
            continue
        candidates.append((depth[child], sizes[child], par, child))
    if not candidates:
        return None

    _, _, lock_from, lock_to = max(candidates)
    subtree = {lock_to}
    queue = deque([lock_to])
    tree_children: dict[str, list[str]] = {}
    for child, par in parent.items():
        if par is None:
            continue
        tree_children.setdefault(par, []).append(child)
    while queue:
        current = queue.popleft()
        for child in tree_children.get(current, []):
            subtree.add(child)
            queue.append(child)

    reachable_keys = [rid for rid in rooms if rid not in subtree and rid != "1"]
    if not reachable_keys:
        return None

    key_room = max(reachable_keys, key=lambda rid: (depth.get(rid, 0), int(rid)))
    lock_kind = rng.choice(_style_pool(style, "keys"))
    key_id, lock_type, map_label = lock_kind
    rooms[lock_from]["locks"].append(
        {
            "id": f"{lock_from}_to_{lock_to}_{lock_type}",
            "type": lock_type,
            "blocks_exit_to": lock_to,
            "requires": key_id,
            "map_label": map_label,
        }
    )
    for item in rooms[lock_from]["exits"]:
        if str(item["to"]) == lock_to:
            item["map_label"] = map_label
    for item in rooms[lock_to]["exits"]:
        if str(item["to"]) == lock_from:
            item["map_label"] = map_label
    data["keys"].append(
        {
            "id": key_id,
            "name": _pretty_key_name(key_id),
            "found_in": key_room,
            "unlocks": [f"{lock_from}_to_{lock_to}_{lock_type}"],
        }
    )
    rooms[key_room]["treasure_tags"].append(key_id)
    rooms[key_room]["contents"].append(_pretty_key_name(key_id))
    return {"lock_from": lock_from, "lock_to": lock_to, "key_room": key_room}


def _ensure_one_puzzle(data: dict[str, Any], rng: Random, style: dict[str, Any], forbidden: set[str] | None = None) -> list[str]:
    if any(room.get("puzzle_tags") for room in data.get("rooms", [])):
        return []
    forbidden = set(forbidden or set())
    forbidden.add("1")
    candidates = _eligible_room_ids(data, forbidden)
    if not candidates:
        return []
    rid = rng.choice(candidates)
    style_key = data["dungeon"].get("style", "reliquary")
    room = room_index(data)[rid]
    puzzle_names = _fragment_pool(style_key, "puzzle_tag", _style_pool(style, "puzzles", COMMON_PUZZLES))
    puzzle_devices = _fragment_pool(style_key, "puzzle_device", [])
    puzzle_inputs = _fragment_pool(style_key, "puzzle_input", [])
    puzzle_logics = _fragment_pool(style_key, "puzzle_logic", [])
    puzzle_results = _fragment_pool(style_key, "puzzle_result", [])
    room["puzzle_tags"].append(rng.choice(puzzle_names))
    if puzzle_devices and puzzle_inputs and puzzle_logics:
        device = rng.choice(puzzle_devices)
        inputs = rng.choice(puzzle_inputs)
        logic = rng.choice(puzzle_logics)
        result = rng.choice(puzzle_results or ["It clearly controls the way forward."])
        room["contents"].append(f"{device} that accepts {inputs}")
        room["contents"].append(f"its rule seems to involve {logic}")
        room["contents"].append(result)
    else:
        room["contents"].append("worked mechanism with an obvious rule")
    room["role_tags"].append("puzzle_room")
    return [rid]


def _ensure_tiny_feature_budget(
    data: dict[str, Any],
    rng: Random,
    difficulty: str,
    style: dict[str, Any],
    depth: dict[str, int],
    parent: dict[str, str | None],
    sizes: dict[str, int],
    farthest: str,
    hub_id: str,
) -> None:
    if data["dungeon"].get("size") != "tiny":
        return
    target = 3 if difficulty == "soft" else 4
    preferred_solo = []
    if data.get("bosses") and parent.get(data["bosses"][0]["lair"]):
        preferred_solo.append(parent[data["bosses"][0]["lair"]])
    preferred_solo.append(farthest)
    while sum(1 for present in _feature_flags(data).values() if present) < target:
        flags = _feature_flags(data)
        missing = [name for name, present in flags.items() if not present]
        if not missing:
            break
        rng.shuffle(missing)
        progress = False
        for feature in missing:
            if feature == "keyed":
                if _maybe_add_keyed_progression(data, rng, depth, parent, sizes, difficulty, style, force=True):
                    progress = True
                    break
            elif feature == "secret_route":
                if _maybe_add_forced_secret_route(data, rng):
                    progress = True
                    break
            elif feature == "puzzle":
                if _ensure_one_puzzle(data, rng, style):
                    progress = True
                    break
            elif feature == "weird_npc":
                before = len(data.get("weird_npcs", []))
                _add_weird_npc(data, rng, 1.0, style)
                if len(data.get("weird_npcs", [])) > before:
                    progress = True
                    break
            elif feature == "solo":
                if _maybe_add_solo_monster(
                    data,
                    rng,
                    1.0,
                    preferred_solo,
                    style,
                    forbidden={data["bosses"][0]["lair"]} if data.get("bosses") else set(),
                ):
                    progress = True
                    break
            elif feature == "trap":
                if _maybe_add_trap_room(data, rng, 1.0, style):
                    progress = True
                    break
        if not progress:
            break


def _ensure_soft_challenge(
    data: dict[str, Any],
    rng: Random,
    style: dict[str, Any],
    depth: dict[str, int],
    parent: dict[str, str | None],
    sizes: dict[str, int],
    farthest: str,
) -> None:
    if data["dungeon"].get("difficulty") != "soft":
        return
    has_challenge = any(
        [
            bool(data.get("keys")),
            bool(data.get("factions")),
            bool(data.get("solo_monsters")),
            bool(data.get("bosses")),
            any(room.get("trap_tags") for room in data.get("rooms", [])),
            any(room.get("puzzle_tags") for room in data.get("rooms", [])),
        ]
    )
    if has_challenge:
        return
    if _ensure_one_puzzle(data, rng, style):
        return
    if _maybe_add_keyed_progression(data, rng, depth, parent, sizes, "soft", style, force=True):
        return
    _maybe_add_solo_monster(data, rng, 1.0, [farthest], style)


def _pretty_key_name(key_id: str) -> str:
    return key_id.replace("_", " ").title()


def _eligible_room_ids(data: dict[str, Any], forbidden: set[str] | None = None) -> list[str]:
    forbidden = forbidden or set()
    return [room["id"] for room in data["rooms"] if room["id"] not in forbidden]


def _maybe_add_trap_room(data: dict[str, Any], rng: Random, probability: float, style: dict[str, Any]) -> str | None:
    if rng.random() > probability:
        return None
    candidates = _eligible_room_ids(data, {"1", _pick_hub(data)})
    if not candidates:
        return None
    rid = rng.choice(candidates)
    style_key = data["dungeon"].get("style", "reliquary")
    trap_names = _fragment_pool(style_key, "trap_name", [])
    trap_descs = _fragment_pool(style_key, "trap_desc", [])
    trap_telegraphs = _fragment_pool(style_key, "trap_telegraph", [])
    trap_triggers = _fragment_pool(style_key, "trap_trigger", [])
    trap_payloads = _fragment_pool(style_key, "trap_payload", [])
    trap_aftermaths = _fragment_pool(style_key, "trap_aftermath", [])
    if trap_names and trap_telegraphs and trap_triggers and trap_payloads:
        name = rng.choice(trap_names)
        tag = "grimtooth_lethal_room"
        telegraph = rng.choice(trap_telegraphs)
        trigger = rng.choice(trap_triggers)
        payload = rng.choice(trap_payloads)
        aftermath = rng.choice(trap_aftermaths or ["Survivors are left split, trapped, or easy prey."])
        desc = f"{telegraph} {trigger} {payload} {aftermath}"
    elif trap_names and trap_descs:
        name = rng.choice(trap_names)
        tag = "grimtooth_lethal_room"
        desc = rng.choice(trap_descs)
    else:
        name, tag, desc = rng.choice(_style_pool(style, "trap_rooms"))
    room = room_index(data)[rid]
    room["trap_tags"].append(tag)
    room["description"] = desc
    room["contents"].append("warning plaques")
    room["contents"].append("old bones in a bad place")
    room["role_tags"].append("trap_room")
    room["name"] = name
    return rid


def _add_puzzles(data: dict[str, Any], rng: Random, size: str, style: dict[str, Any], forbidden: set[str] | None = None) -> list[str]:
    weights = {"tiny": [0, 1, 1, 2], "medium": [0, 1, 1, 2, 2], "large": [0, 1, 1, 2, 2, 2]}
    count = rng.choice(weights[size])
    forbidden = set(forbidden or set())
    forbidden.add("1")
    candidates = _eligible_room_ids(data, forbidden)
    rng.shuffle(candidates)
    chosen = candidates[:count]
    style_key = data["dungeon"].get("style", "reliquary")
    puzzle_names = _fragment_pool(style_key, "puzzle_tag", _style_pool(style, "puzzles", COMMON_PUZZLES))
    puzzle_devices = _fragment_pool(style_key, "puzzle_device", [])
    puzzle_inputs = _fragment_pool(style_key, "puzzle_input", [])
    puzzle_logics = _fragment_pool(style_key, "puzzle_logic", [])
    puzzle_results = _fragment_pool(style_key, "puzzle_result", [])
    rng.shuffle(puzzle_names)
    for index, rid in enumerate(chosen):
        room = room_index(data)[rid]
        room["puzzle_tags"].append(puzzle_names[index % len(puzzle_names)])
        if puzzle_devices and puzzle_inputs and puzzle_logics:
            device = rng.choice(puzzle_devices)
            inputs = rng.choice(puzzle_inputs)
            logic = rng.choice(puzzle_logics)
            result = rng.choice(puzzle_results or ["It clearly controls the way forward."])
            room["contents"].append(f"{device} that accepts {inputs}")
            room["contents"].append(f"its rule seems to involve {logic}")
        else:
            room["contents"].append("worked mechanism with an obvious rule")
    return chosen


def _add_treasures(data: dict[str, Any], rng: Random, size: str, style: dict[str, Any]) -> None:
    count = _choose_count(rng, SIZE_CONFIG[size]["treasures"])
    candidates = _eligible_room_ids(data, {"1"})
    rng.shuffle(candidates)
    style_key = data["dungeon"].get("style", "reliquary")
    for rid in candidates[:count]:
        room = room_index(data)[rid]
        prize = _compose_treasure(style_key, rng)
        room["treasure_tags"].append(_sslib.slugify(prize))
        room["contents"].append(prize)
        room["role_tags"].append("treasure_room")


def _add_weird_npc(data: dict[str, Any], rng: Random, probability: float, style: dict[str, Any]) -> None:
    if rng.random() > probability:
        return
    candidates = _eligible_room_ids(data, {"1"})
    if not candidates:
        return
    rid = rng.choice(candidates)
    style_key = data["dungeon"].get("style", "reliquary")
    npc = _compose_weird_npc(style_key, rng)
    data["weird_npcs"].append({"id": _sslib.slugify(npc), "name": npc, "room": rid})
    room = room_index(data)[rid]
    room["contents"].append(npc)
    room["role_tags"].append("weird_npc")


def _add_factions(data: dict[str, Any], rng: Random, probability: float, style: dict[str, Any]) -> None:
    if rng.random() > probability:
        return
    style_key = data["dungeon"].get("style", "reliquary")
    choices: list[dict[str, str]] = []
    seen: set[str] = set()
    for _ in range(16):
        faction = _compose_faction_profile(style_key, rng)
        if faction["name"] in seen:
            continue
        seen.add(faction["name"])
        choices.append(faction)
        if len(choices) == 2:
            break
    if len(choices) < 2:
        fallback_pool = _style_pool(style, "factions")
        if len(fallback_pool) < 2:
            return
        choices = [
            {"name": name, "want": want, "culture": "dug-in locals", "loadout": "mixed scavenged gear", "tactic": "favor numbers and ambushes"}
            for name, want in rng.sample(fallback_pool, 2)
        ]
    rooms = [room["id"] for room in data["rooms"] if room["id"] != "1"]
    if len(rooms) < 4:
        return
    rng.shuffle(rooms)
    split = max(2, len(rooms) // 3)
    territory_a = sorted(rooms[:split], key=int)
    territory_b = sorted(rooms[-split:], key=int)
    for faction, territory in zip(choices, (territory_a, territory_b)):
        fid = _sslib.slugify(faction["name"])
        data["factions"].append({"id": fid, "name": faction["name"], "wants": faction["want"], "holds": territory, "culture": faction["culture"], "loadout": faction["loadout"], "tactic": faction["tactic"]})
        for offset, rid in enumerate(territory):
            room = room_index(data)[rid]
            room["faction_tags"].append(fid)
            if offset == 0:
                room["contents"].append(f"{faction['name']} sentries with {faction['loadout']}")
            else:
                room["contents"].append(f"clear traces of {faction['name'].lower()} passage")


def _maybe_add_solo_monster(
    data: dict[str, Any],
    rng: Random,
    probability: float,
    preferred: list[str],
    style: dict[str, Any],
    forbidden: set[str] | None = None,
) -> str | None:
    if rng.random() > probability:
        return None
    forbidden = forbidden or set()
    candidates = [rid for rid in preferred if rid and rid not in forbidden]
    if not candidates:
        candidates = _eligible_room_ids(data, {"1"} | set(forbidden))
    if not candidates:
        return None
    rid = candidates[0]
    style_key = data["dungeon"].get("style", "reliquary")
    name, description = _compose_solo(style_key, rng)
    sid = _sslib.slugify(name)
    data["solo_monsters"].append({"id": sid, "name": name, "range": [rid]})
    room = room_index(data)[rid]
    room["solo_monster_tags"].append(sid)
    room["contents"].append(description)
    room["role_tags"].append("approach")
    return rid


def _maybe_add_boss(data: dict[str, Any], rng: Random, probability: float, preferred: str, style: dict[str, Any]) -> str | None:
    if rng.random() > probability:
        return None
    room = room_index(data)[preferred]
    style_key = data["dungeon"].get("style", "reliquary")
    boss_name = _compose_boss(style_key, rng)
    bid = _sslib.slugify(boss_name)
    data["bosses"].append({"id": bid, "name": boss_name, "lair": preferred})
    room["boss_tags"].append(bid)
    room["contents"].append(f"{boss_name} holds court here")
    room["role_tags"].append("boss_room")
    return preferred


def _add_monster_ecology(data: dict[str, Any], rng: Random, size: str) -> None:
    style_key = data["dungeon"].get("style", "reliquary")
    counts = {"tiny": [1, 1, 2], "medium": [1, 2, 2], "large": [2, 2, 3]}
    group_count = rng.choice(counts[size])
    seen: set[str] = set()
    groups: list[dict[str, str]] = []
    for _ in range(24):
        group = _compose_monster_group(style_key, rng)
        if group["name"] in seen:
            continue
        seen.add(group["name"])
        groups.append(group)
        if len(groups) >= group_count:
            break
    if not groups:
        return
    data["monster_groups"].extend(
        {"id": _sslib.slugify(group["name"]), "name": group["name"], "trait": group["trait"], "sign": group["sign"]}
        for group in groups
    )
    candidates = _eligible_room_ids(data, {"1"})
    rng.shuffle(candidates)
    for group, rid in zip(groups, candidates):
        room = room_index(data)[rid]
        room["contents"].append(f"signs of {group['name']}: {group['sign']}")


def _generated_site_name(rng: Random, style: dict[str, Any]) -> str:
    style_key = next((key for key, value in STYLE_PACKS.items() if value is style), "")
    if style_key:
        return _compose_site_name(style_key, rng, style)
    first = rng.choice(_style_pool(style, "site_names_first"))
    second = rng.choice(_style_pool(style, "site_names_second"))
    return f"{first} {second}"




def _pick_unique_name(candidates: list[str], used: set[str], fallback_prefix: str) -> str:
    for name in candidates:
        if name not in used:
            used.add(name)
            return name
    base = candidates[0] if candidates else fallback_prefix
    index = 2
    candidate = f"{base} {index}"
    while candidate in used:
        index += 1
        candidate = f"{base} {index}"
    used.add(candidate)
    return candidate


def _name_and_describe_rooms(data: dict[str, Any], rng: Random, style: dict[str, Any]) -> None:
    rooms = room_index(data)
    used_names: set[str] = set()
    room_name_parts = style["room_name_parts"]
    style_key = data["dungeon"].get("style", "reliquary")
    atmospheres = _fragment_pool(style_key, "atmosphere", _style_pool(style, "atmospheres"))
    contents_pool = _fragment_pool(style_key, "content", _style_pool(style, "contents"))
    for room in data["rooms"]:
        roles = set(room.get("role_tags", []))
        if "start" in roles:
            pool = room_name_parts["start"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Entry")
        elif "boss_room" in roles:
            pool = room_name_parts["boss"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Boss Room")
        elif "puzzle_room" in roles:
            pool = room_name_parts["puzzle"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Puzzle Room")
        elif "approach" in roles:
            pool = room_name_parts["approach"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Approach")
        elif "hub" in roles:
            pool = room_name_parts["hub"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Crossing")
        elif "treasure_room" in roles:
            pool = room_name_parts["treasure"][:]
            rng.shuffle(pool)
            room["name"] = _pick_unique_name(pool, used_names, "Treasure Room")
        else:
            if room["name"] != f"Room {room['id']}" and room["name"] not in used_names:
                used_names.add(room["name"])
            else:
                pool = room_name_parts["generic"][:]
                rng.shuffle(pool)
                room["name"] = _pick_unique_name(pool, used_names, "Chamber")

        if not room["atmosphere"]:
            room["atmosphere"] = rng.choice(atmospheres)
        if not room["contents"]:
            room["contents"] = [rng.choice(contents_pool)]

        visible_exits = [str(item["to"]) for item in room.get("exits", [])]
        room["discovered"]["visible_exits"] = visible_exits if room["id"] == "1" else room["discovered"].get("visible_exits", [])
        if not room["description"]:
            room["description"] = _describe_room(data, room, rooms)
        if not room["discovered"]["notes"] and room["id"] == "1":
            room["discovered"]["notes"] = [room["atmosphere"]]


def _add_player_hook(data: dict[str, Any], rng: Random) -> None:
    dungeon = data["dungeon"]
    rooms = room_index(data)
    start_room = rooms[dungeon["start_room"]]
    pitch_scale = {"tiny": "a short", "medium": "a substantial", "large": "a larger but still bounded"}
    pitch_danger = {"soft": "forgiving", "medium": "dangerous", "hard": "lethal"}
    style_key = dungeon.get("style", "reliquary")
    style_pitch = dungeon.get("style_pitch", "an old and dangerous underplace")
    subtheme = dungeon.get("subtheme") or style_pitch
    public_place = rng.choice(_public_pool(style_key, "places", ["the underways", "the hidden vaults"]))
    public_artifact = _with_indefinite_article(_compose_treasure(style_key, rng))
    public_rescue = _compose_rescue_target(style_key, rng)
    public_boss = "a hidden tyrant"
    public_solo = "a roaming hunter"
    public_faction = "rival claimants below"
    public_motif = rng.choice(_public_pool(style_key, "motifs", ["stone", "shadow", "dust"]))
    boss_name = data["bosses"][0]["name"] if data.get("bosses") else ""
    solo_name = data["solo_monsters"][0]["name"] if data.get("solo_monsters") else ""
    factions = [f["name"] for f in data.get("factions", [])]
    keys = [key["name"] for key in data.get("keys", [])]
    weird_npc = data["weird_npcs"][0]["name"] if data.get("weird_npcs") else ""
    trap_room = next((room["name"] for room in data["rooms"] if room.get("trap_tags")), "")
    puzzle_room = next((room["name"] for room in data["rooms"] if room.get("puzzle_tags")), "")
    treasure_room = next((room["name"] for room in data["rooms"] if room.get("treasure_tags")), "")
    artifact = _compose_treasure(style_key, rng)
    rescue = _compose_rescue_target(style_key, rng)
    recruit = _compose_recruit_target(style_key, rng)
    local_presence = bool(factions) or bool(weird_npc)
    treasure_objective = _compose_treasure_objective(style_key, rng)

    hook_bits = []
    if boss_name:
        hook_bits.append(f"{public_boss} waiting in the deeper chambers")
    if factions:
        if len(factions) > 1:
            hook_bits.append(public_faction)
        else:
            hook_bits.append("a claimed site with locals already dug in")
    if solo_name:
        hook_bits.append(public_solo)
    if keys:
        hook_bits.append("sealed inner routes that will not yield to blunt force")
    if trap_room:
        hook_bits.append("at least one room built to kill the impatient")
    if puzzle_room:
        hook_bits.append("old mechanisms that matter to navigation, not just decoration")
    if treasure_room:
        hook_bits.append("something valuable enough to justify the risk")
    if weird_npc:
        hook_bits.append("a survivor or holdout who may know more than they should")
    if not hook_bits:
        hook_bits.append("a compact ruin with enough mystery and plunder for a hard evening's delve")
    rng.shuffle(hook_bits)

    focus = hook_bits[: min(3, len(hook_bits))]
    if len(focus) == 1:
        feature_text = focus[0]
    elif len(focus) == 2:
        feature_text = f"{focus[0]}, and {focus[1]}"
    else:
        feature_text = f"{focus[0]}, {focus[1]}, and {focus[2]}"

    objective_candidates: list[tuple[str, str, str, str]] = []
    if boss_name:
        objective_candidates.extend(
            [
                ("end_boss", f"bring down {public_boss}", f"Break the grip of {public_boss} before the deeper chambers spill their trouble upward.", public_boss),
                ("kill_boss", f"bring down {public_boss}", f"Hunt down {public_boss} and make sure the threat below stops there.", public_boss),
                ("stop_rite", "stop whatever is underway below", f"Interrupt whatever is gathering strength in {public_place} before it gets worse.", public_boss),
            ]
        )
    if solo_name:
        objective_candidates.extend(
            [
                ("hunt_solo", f"track {public_solo}", f"Learn how {public_solo} moves and survive long enough to make use of that knowledge.", public_solo),
                ("bait_solo", f"outwit {public_solo}", f"Figure out how {public_solo} hunts and use that knowledge to cross the site alive.", public_solo),
            ]
        )
    if keys:
        objective_candidates.extend(
            [
                ("secure_key", "open the sealed interior", f"Find what opens the sealed interior before the site chews through your time and supplies.", "sealed way"),
                ("race_key", "reach the inner doors first", f"Beat the other claimants to whatever opens the deeper route.", "sealed way"),
            ]
        )
    objective_candidates.extend(
        [
            ("artifact_heist", f"steal {public_artifact}", f"Steal {public_artifact} and get it back out in one piece.", public_artifact),
            ("artifact_recover", f"recover {public_artifact}", f"Recover {public_artifact} for the patron, buyer, temple, or blackmailer waiting above.", public_artifact),
            ("rescue", f"bring back {public_rescue}", f"Find {public_rescue} and get them out before the way back turns worse.", public_rescue),
            ("treasure", "hit the richest cache you can reach", treasure_objective[:1].upper() + treasure_objective[1:] + ".", "hidden prize"),
            ("survey", "prove there is a route worth reusing", f"Map a usable route through {public_place} and return with enough certainty to lead others back in.", public_place),
        ]
    )
    if local_presence:
        objective_candidates.extend(
            [
                ("recruit", "win over someone local", f"Turn one local group, guide, or holdout into leverage before the site turns fully hostile.", "local ally"),
            ]
        )
    if factions:
        objective_candidates.extend(
            [
                ("broker", "cut a temporary deal inside the site", f"Broker a fragile arrangement inside {public_place} before the locals decide you are the easiest victim.", "local deal"),
            ]
        )
    if len(factions) > 1:
        objective_candidates.extend(
            [
                ("faction_play", "play one side against the other", f"Exploit the split among {public_faction} long enough to reach what you actually came for.", public_faction),
                ("faction_recruit", "turn one side into a temporary ally", f"Choose which side below is safer to trust and survive what that choice costs you.", public_faction),
            ]
        )
    if weird_npc:
        objective_candidates.extend(
            [
                ("npc_contact", "find the one person who knows the way", f"Find the survivor, holdout, or witness who still knows something useful before someone else reaches them.", "witness"),
            ]
        )
    if puzzle_room and _has_route_complexity(data):
        objective_candidates.extend(
            [
                ("puzzle_route", "open a better route", f"Work out the old mechanism that opens a cleaner way through the site.", "hidden route"),
            ]
        )
    if trap_room:
        objective_candidates.extend(
            [
                ("trap_cross", "survive the kill-room", f"Reach the far side of the worst room in the site without losing the delver you brought in.", "kill-room"),
            ]
        )

    objective_type, teaser, motivation, focus = rng.choice(objective_candidates)
    dungeon["hook_type"] = objective_type
    dungeon["hook_summary"] = teaser
    dungeon["hook_target"] = focus

    blurb_templates = [
        f"{dungeon['name']} lies below {start_room['name']}, in {subtheme}. It is {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} delve for anyone who wants to {teaser}; expect {feature_text}.",
        f"Rumor says {dungeon['name']} hides inside {subtheme}. It offers {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} delve if you mean to {teaser}, with {feature_text}.",
        f"If the table wants {style_pitch}, {dungeon['name']} is a good fit. This is {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} site where the draw is to {teaser}, and the pressure comes from {feature_text}.",
        f"{dungeon['name']} is reached through {start_room['name']} and shaped by {subtheme}. It plays as {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} delve where you go in to {teaser}, but {feature_text} decide whether that plan survives contact with the place.",
        f"Under {start_room['name']} waits {dungeon['name']}, {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} bad ground built around {subtheme}. Go there to {teaser}, and expect {feature_text}.",
        f"{dungeon['name']} starts at {start_room['name']} and opens into {subtheme}. The pitch is simple enough: {teaser}. The problem is {feature_text}, in {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} fashion.",
        f"The table goes to {dungeon['name']} if it wants {style_pitch} and a reason to {teaser}. It is {pitch_scale[dungeon['size']]} {pitch_danger[dungeon['difficulty']]} site, and {feature_text} are the price of entry.",
    ]
    dungeon["player_blurb"] = rng.choice(blurb_templates)
    dungeon["character_motivation"] = motivation


def _describe_room(data: dict[str, Any], room: dict[str, Any], rooms: dict[str, dict[str, Any]]) -> str:
    contents = [item for item in room.get("contents", []) if item]
    lead = contents[0] if contents else "old stone and trouble"
    second = contents[1] if len(contents) > 1 else ""
    exits = len(room.get("exits", []))

    if room.get("boss_tags"):
        return f"{room['name']} is the site's deep chamber: {lead}, {second or 'a final authority in the dark'}, and the feel of a room built to end arguments badly."
    if room.get("trap_tags"):
        return f"{room['name']} looks workable at a glance, but {lead}; the room is dressed with just enough warning to reward caution and kill hurry."
    if room.get("puzzle_tags"):
        return f"{room['name']} centers on {lead}; {second or 'the dressing around it suggests the mechanism matters to movement, not ceremony alone'}."
    if room.get("solo_monster_tags"):
        return f"{room['name']} is the sort of threshold a hunter would own: {lead}{', ' + second if second else ''}."
    if room.get("faction_tags"):
        faction = next((f for f in data.get("factions", []) if f["id"] == room["faction_tags"][0]), None)
        if faction:
            motive = faction.get("wants", "control of the room")
            return f"{room['name']} is clearly claimed by {faction['name']}: {lead}{', ' + second if second else ''}; they want {motive} and have arranged the room accordingly."
    if room.get("treasure_tags"):
        return f"{room['name']} offers a tempting payoff in plain view or near enough: {lead}{', ' + second if second else ''}."
    if "start" in room.get("role_tags", []):
        return f"{room['name']} is the threshold of the delve, marked by {lead}{', ' + second if second else ''}."
    if exits == 1:
        return f"{room['name']} is a short end-room with {lead}{', ' + second if second else ''}, and only one obvious way back out."
    if exits > 2:
        return f"{room['name']} is a decision room: {lead}{', ' + second if second else ''}, with several ways onward."
    return f"{room['name']} holds {lead}{', ' + second if second else ''}."
