from __future__ import annotations

from random import Random
from typing import Any

import _delvekit as core

_fragment_pool = core._fragment_pool
_compose_rescue_target = core._compose_rescue_target
_compose_treasure = core._compose_treasure
_format_title_template = core._format_title_template
_public_patron = core._public_patron
_public_teaser = core._public_teaser
_with_article = core._with_article
_with_indefinite_article = core._with_indefinite_article
_choose_title_variant = core._choose_title_variant
_english_join = core._english_join
_title_focus_text = core._title_focus_text

def _pitch_skeleton(data: dict[str, Any], rng: Random) -> dict[str, Any]:
    dungeon = data["dungeon"]
    style_key = dungeon.get("style", "reliquary")
    teaser = _public_teaser(style_key, rng)
    patron = _public_patron(style_key, rng)
    place = teaser["place"]
    motif = teaser["motif"]
    motif_2 = teaser["motif_2"]
    artifact = _with_indefinite_article(_compose_treasure(style_key, rng))
    rescue = _compose_rescue_target(style_key, rng)
    boss = rng.choice(
        [
            "a power in the dark",
            "a hidden tyrant below",
            f"the will behind {_with_article(place)}",
            "something in the inner dark with followers",
        ]
    )
    solo = rng.choice(
        [
            "a roaming hunter",
            "something that stalks the halls",
            "a patient thing that owns the side passages",
            "an old guardian that changes how you move",
        ]
    )
    factions = rng.choice(
        [
            "rivals below",
            "two hostile camps",
            "feuding claimants",
            "locals already at knives' edge",
        ]
    )
    hook_type = dungeon.get("hook_type", "")

    pressures = []
    if data.get("factions"):
        pressures.append(factions)
    if data.get("keys"):
        pressures.append("sealed ways and hidden inner doors")
    if any(room.get("trap_tags") for room in data.get("rooms", [])):
        pressures.append("old death-traps built to punish haste")
    if any(room.get("puzzle_tags") for room in data.get("rooms", [])):
        pressures.append("strange mechanisms that matter")
    if data.get("solo_monsters"):
        pressures.append(solo)
    if data.get("bosses"):
        pressures.append(boss)
    if any(room.get("treasure_tags") for room in data.get("rooms", [])):
        pressures.append("something worth carrying back out")
    if data.get("weird_npcs"):
        pressures.append("someone below who knows more than they should")
    if not pressures:
        pressures.append("old danger and bad reasons to stay too long")
    rng.shuffle(pressures)

    hook_briefs = {
        "artifact_heist": {
            "ask": f"steal {artifact}",
            "setup": f"{patron['full']} swears there is {artifact} somewhere below.",
            "payoff": patron["reward"],
        },
        "artifact_recover": {
            "ask": f"recover {artifact}",
            "setup": f"{patron['full']} wants {artifact} brought back.",
            "payoff": patron["reward"],
        },
        "rescue": {
            "ask": f"bring back {rescue}",
            "setup": f"{patron['full']} says {_with_indefinite_article(rescue)} never came back from below.",
            "payoff": patron["reward"],
        },
        "survey": {
            "ask": "chart a usable route",
            "setup": f"{patron['full']} believes there is a workable road through {place}.",
            "payoff": patron["reward"],
        },
        "broker": {
            "ask": "come back with terms",
            "setup": f"{patron['full']} thinks no one truly owns {place}.",
            "payoff": patron["reward"],
        },
        "recruit": {
            "ask": "win an ally below",
            "setup": f"{patron['full']} says there is help to be won below.",
            "payoff": patron["reward"],
        },
        "faction_play": {
            "ask": "play one side against the other",
            "setup": f"{patron['full']} knows the camps below are already at each other's throats.",
            "payoff": patron["reward"],
        },
        "faction_recruit": {
            "ask": "turn one side into a temporary ally",
            "setup": f"{patron['full']} thinks the real prize is whichever side below can be bent to your purpose.",
            "payoff": patron["reward"],
        },
        "npc_contact": {
            "ask": "find the one person who knows the truth",
            "setup": f"{patron['full']} says someone below knows the truth of the place.",
            "payoff": patron["reward"],
        },
        "puzzle_route": {
            "ask": "open a hidden route",
            "setup": f"{patron['full']} is certain the old way through is not the only way through.",
            "payoff": patron["reward"],
        },
        "trap_cross": {
            "ask": "cross the kill-room alive",
            "setup": f"{patron['full']} wants what lies beyond a room that has buried better delvers than you.",
            "payoff": patron["reward"],
        },
        "hunt_solo": {
            "ask": "learn what hunts below",
            "setup": f"{patron['full']} wants proof about the thing hunting the passages below.",
            "payoff": patron["reward"],
        },
        "bait_solo": {
            "ask": "outwit the hunter below",
            "setup": f"{patron['full']} says the dark below belongs to a patient hunter.",
            "payoff": patron["reward"],
        },
        "stop_rite": {
            "ask": "stop whatever is building below",
            "setup": f"{patron['full']} fears something below is building toward a bad end.",
            "payoff": patron["reward"],
        },
        "end_boss": {
            "ask": "break the hold of whatever rules below",
            "setup": f"{patron['full']} believes there is a master below.",
            "payoff": patron["reward"],
        },
        "kill_boss": {
            "ask": "put down the will in the inner dark",
            "setup": f"{patron['full']} wants a dangerous will in the inner dark put down for good.",
            "payoff": patron["reward"],
        },
        "race_key": {
            "ask": "open the deeper chambers first",
            "setup": f"{patron['full']} says the deeper chambers are shut but not forever.",
            "payoff": patron["reward"],
        },
        "secure_key": {
            "ask": "open the sealed road",
            "setup": f"{patron['full']} says the best part of {place} is locked away.",
            "payoff": patron["reward"],
        },
        "treasure": {
            "ask": "take the richest prize you can reach",
            "setup": f"{patron['full']} wants a share of whatever is buried below.",
            "payoff": patron["reward"],
        },
    }
    hook = hook_briefs.get(
        hook_type,
        {
            "ask": "get in, take something valuable, and get out",
            "setup": f"{patron['full']} has reasons of their own for sending you below.",
            "payoff": patron["reward"],
        },
    )

    fallback_title_cues = {
        "artifact_heist": ["The {adjective} {noun}", "The Prize Below {place}", "Raid on {place}", "Hands on the {noun}"],
        "artifact_recover": ["The Lost {noun}", "What Was Buried in {place}", "The Thing Below {place}", "Back from {place}"],
        "rescue": ["Bring Them Back", "Out of {place}", "Lost in {place}", "One Soul More"],
        "survey": ["A Road Through {place}", "The Route No One Kept", "Maps for the Underway", "The Lost Way Below"],
        "broker": ["Terms in the Dark", "Bargains Beneath {place}", "The Price of Passage", "A Deal Below"],
        "recruit": ["An Ally Below", "Friends in the Dark", "The Side Beneath {place}", "The Price of Help"],
        "faction_play": ["The Feud Below", "Knives Under {place}", "Two Flags in the Dark", "War for the Underway"],
        "faction_recruit": ["Terms of Survival", "The Side You Choose", "Knives Under {place}", "A Knife for Hire"],
        "npc_contact": ["The Last One Who Knows", "Whispers Under {place}", "What the Survivor Saw", "The Witness Below"],
        "puzzle_route": ["The Secret of {place}", "The Mechanism Below", "Open the Hidden Way", "Beyond the Locked Road"],
        "trap_cross": ["Alive Through the Kill-Room", "Past the Killing Floor", "One Room Too Far", "The Price of {motif}"],
        "hunt_solo": ["What Hunts in {place}", "Tracks in the Dark", "The Hunter Under Stone", "Shadow of {motif}"],
        "bait_solo": ["The Thing in the Passages", "What Waits in {place}", "Tracks in the Dust", "Teeth Under {motif}"],
        "stop_rite": ["The Last Rite of {motif}", "Before the Dark Wakes", "The Work Below", "The Last Bell Before Midnight"],
        "end_boss": ["The Tyrant Below", "The Throne Under {place}", "What Rules Below", "Down to {place}"],
        "kill_boss": ["The Tyrant Below", "The Last Chamber", "The Throne Under {place}", "What Rules Below"],
        "race_key": ["Before the Doors Close", "The Sealed Way", "The Inner Gate", "The Locked Road"],
        "secure_key": ["The Sealed Way", "What Lies Past the Door", "The Inner Gate", "The Locked Road"],
        "treasure": ["Fortune Under Stone", "Take What They Buried", "The Hidden Prize", "Gold Under {place}"],
    }.get(hook_type, ["The {adjective} {noun}", "The Secret of {place}", "{motif} Below", "What Waits in {place}"])
    title_cues = [
        _format_title_template(template, teaser)
        for template in _fragment_pool("*", f"title_{hook_type}", fallback_title_cues)
    ]

    return {
        "patron": patron,
        "public_place": place,
        "public_motifs": [motif, motif_2],
        "hook_type": hook_type,
        "job": hook["ask"],
        "setup": hook["setup"],
        "reward": hook["payoff"],
        "pressures": pressures[:4],
        "title_cues": title_cues,
        "spoiler_guard": "Do not reveal exact monster names, exact faction names, room names, lock items, or final treasure identities.",
    }

def build_module_blurb(data: dict[str, Any], rng: Random) -> tuple[str, str]:
    dungeon = data["dungeon"]
    size = dungeon.get("size", "tiny")
    difficulty = dungeon.get("difficulty", "medium")
    skeleton = _pitch_skeleton(data, rng)
    dungeon["pitch_skeleton"] = skeleton

    place = skeleton["public_place"]
    motif, motif_2 = skeleton["public_motifs"]
    title = dungeon["name"]
    pressure_bits = skeleton["pressures"]
    pressure_text = _english_join(pressure_bits[:3])

    size_tone = rng.choice(
        {
            "tiny": [
                "A short descent, if you move fast.",
                "Short enough for one hard push, if nothing goes wrong.",
                "A compact delve, but not a harmless one.",
            ],
            "medium": [
                "A full night's work, if the place lets you have one.",
                "A proper night's descent, not a quick in-and-out.",
                "Long enough to matter, short enough to think you can finish it.",
            ],
            "large": [
                "A real expedition, not a quick raid.",
                "Broad enough to swallow the careless and keep them.",
                "The kind of site you enter with a plan and leave with fewer certainties.",
            ],
        }[size]
    )
    danger_tone = rng.choice(
        {
            "soft": [
                "Dangerous, but a capable delver can still force the pace.",
                "Risky, but survivable for a table that respects the place.",
                "Hard enough to bite, forgiving enough to tempt a second push.",
            ],
            "medium": [
                "Dangerous in the old way: caution, nerve, and luck all matter.",
                "Proper old-school danger: one bad turn will not always kill you, but it may own the rest of the night.",
                "A dangerous site where patience matters as much as steel.",
            ],
            "hard": [
                "Lethal enough that a single bad choice can end the venture.",
                "Hard country below: mistakes are paid for in blood or bodies.",
                "Openly lethal once the delvers stop paying attention.",
            ],
        }[difficulty]
    )

    hook_lines = {
        "artifact_heist": [
            "Go down, take the prize, and get back out before the dark closes over the road behind you.",
            "Go down light, steal clean, and leave before the place can remember your shape.",
            "Go down for the prize and keep enough nerve in hand to carry it back out.",
            "Take a small light, a hard friend, and the nerve to steal quickly.",
        ],
        "artifact_recover": [
            "Go down, find what was lost, and leave before someone else decides it belongs to them.",
            "Go down, recover the thing, and get back to daylight before the claim turns bloody.",
            "Go down for what was taken and do not linger once it is in your hands.",
            "Bring the thing back up, and do not die debating who owned it first.",
        ],
        "rescue": [
            "Go down quickly. If the lost one still lives, bring them back.",
            "Go down fast and come back with someone breathing.",
            "Go down before fear, hunger, or the place itself finishes the work for you.",
            "Make haste. Every extra minute below belongs to the dungeon, not to you.",
        ],
        "survey": [
            "Go down, mark a road worth reusing, and come back with more than rumor.",
            "Go down, chart the way, and return with something better than guesswork.",
            "Go down with chalk and caution, and come back with a road others might trust.",
            "Take notes the old way and come back with a route a sane crew might actually use.",
        ],
        "broker": [
            "Go down, make terms if you can, and survive what such terms are worth below.",
            "Go down ready to bargain, and ready to pay for it if the bargain holds.",
            "Go down to talk terms in a place where talk is never the whole price.",
            "Speak softly, lie only when needed, and leave before the bill comes due.",
        ],
        "recruit": [
            "Go down, win an ally if you can, and learn what that alliance costs.",
            "Go down looking for help and expect help to come with a blade behind it.",
            "Go down to find a useful hand and the trouble attached to it.",
            "Find help below if you must, but remember that need is not the same thing as loyalty.",
        ],
        "faction_play": [
            "Go down, play one side against the other, and take what that confusion buys you.",
            "Go down, turn their quarrel into your road, and leave before they compare notes.",
            "Go down and make their bad blood pay for your passage.",
            "Make the feud work for you, then vanish before they decide who really profited.",
        ],
        "faction_recruit": [
            "Go down, choose your side carefully, and live with the choice.",
            "Go down, back the better enemy, and pray you chose correctly.",
            "Go down and buy yourself one ally before the rest decide you are meat.",
            "Pick the side least likely to betray you first, then keep moving.",
        ],
        "npc_contact": [
            "Go down, find the one who still knows the truth, and decide whether to trust them.",
            "Go down for the witness and hope they are worth reaching first.",
            "Go down, find the last useful voice below, and hear what it costs to listen.",
            "Reach the witness before fear, greed, or worse teaches them to keep quiet forever.",
        ],
        "puzzle_route": [
            "Go down, work the old mechanism, and see what the sealed road was hiding.",
            "Go down, solve the old work, and open the way the builders kept back.",
            "Go down and make the dead machinery admit there was always another road.",
            "Find the trick in the old work and turn it before someone else guesses it first.",
        ],
        "trap_cross": [
            "Go down only if you mean to cross the worst room in the place alive.",
            "Go down ready to beat the kill-room, or not at all.",
            "Go down knowing the road forward was built to choose victims.",
            "The room ahead was built to sort the clever from the dead. Cross accordingly.",
        ],
        "hunt_solo": [
            "Go down, learn how the hunter moves, and pray it learns less about you.",
            "Go down to read the beast's habits before it writes yours in blood.",
            "Go down and study the hunter fast enough to survive the lesson.",
            "Track it if you can, but remember that hunters learn from the chase too.",
        ],
        "bait_solo": [
            "Go down, outthink what stalks the halls, and make the site fear you back.",
            "Go down, call the hunter close, and live through what answers.",
            "Go down ready to set bait in a place where you might be it.",
            "Draw it out on your terms if you can, and pray the dark agrees those are still your terms.",
        ],
        "stop_rite": [
            "Go down before the work below is finished.",
            "Go down and break the rite before it learns how to answer back.",
            "Go down now, because waiting is the same as helping them finish.",
            "Do not wait for certainty. If the work below ripens, you will know too late.",
        ],
        "end_boss": [
            "Go down and break the thing that holds the place together.",
            "Go down to the root of the trouble and put it in the ground for good.",
            "Go down and bring the ruling thing below to heel or ruin.",
            "Find the hand at the throat of the place and break it before the whole site tightens.",
        ],
        "kill_boss": [
            "Go down and settle the matter at its source.",
            "Go down to the deepest room and end the problem where it sits.",
            "Go down and kill the thing below before it sends more trouble upward.",
            "Take the fight to the chamber that matters and leave nothing there that can stand back up.",
        ],
        "race_key": [
            "Go down before the deeper doors are opened by hands other than yours.",
            "Go down first, move fast, and reach the lock before the others do.",
            "Go down now, because the road only belongs to the first hands on the key.",
            "Be first to the lock, or be ready to argue with whoever opens it without you.",
        ],
        "secure_key": [
            "Go down, find what opens the sealed road, and use it before the chance is lost.",
            "Go down for the key to the place and keep hold of it once you have it.",
            "Go down and bring back the one thing the inner door still obeys.",
            "Find the one token, phrase, or sign the inner road still respects, then move.",
        ],
        "treasure": [
            "Go down with an empty pack and a clear idea of what you are willing to die for.",
            "Go down hungry for profit and honest about the price of it.",
            "Go down to get rich, or at least rich enough to try this again.",
            "Take only what justifies the risk, because greed weighs as much as silver on the way back out.",
        ],
    }

    opener = rng.choice(
        [
            f"Below {place} lies a place of {motif}, {motif_2}, and old trouble.",
            f"{title} lies under {place}, where {motif} has outlived better hopes.",
            f"Men still talk about {title}, usually after dark and never with much certainty.",
            f"Not every buried place wants to stay buried. {title} proves the point.",
            f"Old hands still lower their voices when {title} comes up.",
            f"Under {place}, the old work was never finished cleanly.",
            f"There is a bad road under {place}, and {title} begins where it gives up pretending to be safe.",
            f"{title} starts below {place}, where old intentions curdled and never truly died.",
            f"Below {place}, someone once built for order. What remains is {title}.",
            f"Under {place} lies {title}, and the route down still remembers what it was built to do to strangers.",
            f"{title} waits under {place}, where even the useful rooms feel like traps delayed by time.",
            f"The way into {title} still exists under {place}; the safer way out is another question.",
        ]
    )
    middle = rng.choice(
        [
            skeleton["setup"],
            f"They say something hidden there is still waiting, for anyone hard enough to take it.",
            f"Down there, the road is still worth killing for.",
            f"Whatever was built under {place} still draws the desperate and the ambitious.",
            f"No one agrees on who owns the dark below {place}, only that someone means to try.",
            f"Enough wealth and danger remain below to keep drawing the wrong sort of people in.",
            f"Every road into the place promises one kind of profit and another kind of trouble.",
            f"People still head below for reasons that sound sensible above ground and foolish by lanternlight.",
            f"Anyone with sense stays above. Anyone with need starts making excuses and heads down anyway.",
            f"The place still offers enough reward to tempt fools and enough structure to tempt professionals.",
            f"However it began, the site now runs on fear, opportunity, and whoever reaches the next door first.",
        ]
    )
    pressure_line = rng.choice(
        [
            f"Expect {pressure_text}.",
            f"Below that, there is {pressure_text}.",
            f"Count on {pressure_text}.",
            f"What waits there is {pressure_text}.",
            f"The true pressure comes from {pressure_text}.",
            f"If you go, plan around {pressure_text}.",
        ]
    )
    blurb = " ".join(
        [
            opener,
            middle,
            pressure_line,
            size_tone,
            danger_tone,
            rng.choice(hook_lines.get(skeleton["hook_type"], [f"Go down and see whether {skeleton['job']} sounds easier above ground than it feels below."])),
        ]
    )

    extra_title_cues = {
        "artifact_heist": [
            f"Steal from {_title_focus_text(place)}",
            f"{_title_focus_text(motif)} for the Taking",
            f"The Prize Beneath {_title_focus_text(place)}",
        ],
        "artifact_recover": [
            f"What Was Taken to {_title_focus_text(place)}",
            f"The Lost {_title_focus_text(motif)}",
            f"Bring Back the {_title_focus_text(motif)}",
        ],
        "rescue": [
            f"Out of {_title_focus_text(place)}",
            f"The Lost Below {_title_focus_text(place)}",
            f"Bring Them Back from {_title_focus_text(place)}",
        ],
        "survey": [
            f"The Way Through {_title_focus_text(place)}",
            f"A Road Under {_title_focus_text(place)}",
            f"Chart the Broken Way",
        ],
        "broker": [
            f"Bargains Under {_title_focus_text(place)}",
            f"The Price of Safe Passage",
            f"Terms Under {_title_focus_text(place)}",
        ],
        "recruit": [
            f"The Price of Help Below",
            f"An Ally Under {_title_focus_text(place)}",
            f"Win One Hand in the Dark",
        ],
        "faction_play": [
            f"Knives Beneath {_title_focus_text(place)}",
            f"The War Under {_title_focus_text(place)}",
            f"Two Camps in the Dark",
        ],
        "faction_recruit": [
            f"Choose a Side Under {_title_focus_text(place)}",
            f"The Side That Lives",
            f"One Enemy Bought Dear",
        ],
        "npc_contact": [
            f"The Last Witness Under {_title_focus_text(place)}",
            f"Find the One Who Stayed",
            f"The Voice Left Below",
        ],
        "puzzle_route": [
            f"The Other Road Through {_title_focus_text(place)}",
            f"The Door Behind the Door",
            f"What Opens the Dark",
        ],
        "trap_cross": [
            f"Past the Killing Room",
            f"The Price of One More Step",
            f"The Floor That Chooses",
        ],
        "hunt_solo": [
            f"Read the Tracks in Darkness",
            f"What Moves Before You Hear It",
            f"The Thing that Tracks Torchlight",
        ],
        "bait_solo": [
            f"Call the Stalker Close",
            f"Torchbait in the Underways",
            f"What Hunts Before Dawn",
        ],
        "stop_rite": [
            f"Before the Last Prayer Lands",
            f"The Work Beneath the Stone",
            f"Break the Rite Below",
        ],
        "end_boss": [
            f"What Rules Beneath {_title_focus_text(place)}",
            f"The Throne in the Lower Dark",
            f"The Master Below {_title_focus_text(place)}",
        ],
        "kill_boss": [
            f"The Last Chamber Below {_title_focus_text(place)}",
            f"Put Down the Thing Below",
            f"Kill What Waits Beneath",
        ],
        "race_key": [
            f"Before the Inner Door Yields",
            f"The First Hands on the Key",
            f"The Race for the Sealed Way",
        ],
        "secure_key": [
            f"What Opens the Inner Road",
            f"The Thing the Door Obeys",
            f"The Key to the Lower Dark",
        ],
        "treasure": [
            f"Take What Stone Kept",
            f"The Buried Take",
            f"Fortune Under {_title_focus_text(place)}",
        ],
    }
    title = _choose_title_variant(
        rng,
        list(skeleton["title_cues"]) + extra_title_cues.get(skeleton["hook_type"], []),
    )
    return title, blurb
