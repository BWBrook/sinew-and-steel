from __future__ import annotations

import json
from typing import Any

import _delvekit as core
import _sslib
import yaml

SCHEMA_VERSION = core.SCHEMA_VERSION
validate_dungeon = core.validate_dungeon
room_index = core.room_index
edge_key = core.edge_key
all_edge_meta = core.all_edge_meta
_pretty_key_name = core._pretty_key_name


def render_map(
    data: dict[str, Any],
    *,
    mode: str = "gm",
    frontier: bool = False,
    reveal_rooms: list[str] | None = None,
    reveal_secret_connections: list[str] | None = None,
    position: str | None = None,
    include_notes: bool = True,
) -> str:
    validate_dungeon(data)
    rooms = room_index(data)
    current_position = position or data.get("player_map", {}).get("current_room")
    discovered_rooms = set(str(rid) for rid in data.get("player_map", {}).get("discovered_rooms", []))
    discovered_rooms.update(str(rid) for rid in reveal_rooms or [])
    reveal_rooms_set = set(str(rid) for rid in reveal_rooms or [])
    discovered_secret = set(data.get("player_map", {}).get("discovered_secret_connections", []))
    discovered_secret.update(reveal_secret_connections or [])
    discovered_connections = set(data.get("player_map", {}).get("discovered_connections", []))

    visible_rooms: dict[str, dict[str, Any]] = {}
    placeholder_rooms: dict[str, dict[str, Any]] = {}
    if mode == "gm":
        visible_rooms = rooms
    else:
        visible_rooms = {rid: room for rid, room in rooms.items() if rid in discovered_rooms}
        if frontier:
            for rid in list(visible_rooms):
                room_visible_exits = set(str(item) for item in rooms[rid].get("discovered", {}).get("visible_exits", []))
                if rid in reveal_rooms_set:
                    room_visible_exits.update(str(item["to"]) for item in rooms[rid].get("exits", []))
                for item in rooms[rid].get("exits", []):
                    target = str(item["to"])
                    if target in discovered_rooms or target not in rooms:
                        continue
                    if target not in room_visible_exits:
                        continue
                    placeholder_rooms[target] = {
                        "id": target,
                        "name": "?",
                        "x": rooms[target]["x"],
                        "y": rooms[target]["y"],
                        "placeholder": True,
                    }

    if not visible_rooms and not placeholder_rooms:
        return "(no visible rooms)"

    display_rooms = dict(visible_rooms)
    display_rooms.update(placeholder_rooms)
    edges = []
    notes = []
    for meta in all_edge_meta(data):
        a = meta["a"]
        b = meta["b"]
        if mode == "gm":
            if a not in display_rooms or b not in display_rooms:
                continue
            edges.append(meta)
        else:
            if meta["kind"] == "secret":
                if edge_key(a, b) not in discovered_secret:
                    continue
                if a not in display_rooms or b not in display_rooms:
                    continue
                edges.append(meta)
            else:
                if a in display_rooms and b in display_rooms:
                    a_visible = set(str(item) for item in rooms[a].get("discovered", {}).get("visible_exits", []))
                    b_visible = set(str(item) for item in rooms[b].get("discovered", {}).get("visible_exits", []))
                    if a in reveal_rooms_set:
                        a_visible.update(str(item["to"]) for item in rooms[a].get("exits", []))
                    if b in reveal_rooms_set:
                        b_visible.update(str(item["to"]) for item in rooms[b].get("exits", []))
                    if (
                        edge_key(a, b) in discovered_connections
                        or b in a_visible
                        or a in b_visible
                    ):
                        edges.append(meta)

    box_w = 26
    box_h = 3
    h_gap = 8
    v_gap = 4
    xs = [room["x"] for room in display_rooms.values()]
    ys = [room["y"] for room in display_rooms.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = (max_x - min_x + 1) * (box_w + h_gap) + 4
    height = (max_y - min_y + 1) * (box_h + v_gap) + 4
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    def put(x: int, y: int, char: str) -> None:
        if 0 <= x < width and 0 <= y < height:
            canvas[y][x] = char

    def write_text(x: int, y: int, text: str) -> None:
        for offset, char in enumerate(text):
            put(x + offset, y, char)

    pos_map = {}
    for rid, room in display_rooms.items():
        top_x = 2 + (room["x"] - min_x) * (box_w + h_gap)
        top_y = 1 + (room["y"] - min_y) * (box_h + v_gap)
        pos_map[rid] = (top_x, top_y)
        center = top_x + box_w // 2
        for col in range(1, box_w - 1):
            put(top_x + col, top_y, "─")
            put(top_x + col, top_y + box_h - 1, "─")
        put(top_x, top_y, "┌")
        put(top_x + box_w - 1, top_y, "┐")
        put(top_x, top_y + box_h - 1, "└")
        put(top_x + box_w - 1, top_y + box_h - 1, "┘")
        put(top_x, top_y + 1, "│")
        put(top_x + box_w - 1, top_y + 1, "│")
        label = "?" if room.get("placeholder") else f"{rid}. {room['name']}"
        marker = " @ " if current_position and str(current_position) == rid else ""
        text = f"{label}{marker}"[: box_w - 2]
        write_text(top_x + 1, top_y + 1, text.ljust(box_w - 2))
        pos_map[rid] = (top_x, top_y, center)

    for meta in edges:
        first = display_rooms[meta["a"]]
        second = display_rooms[meta["b"]]
        if first["x"] == second["x"]:
            top_room, bottom_room = (first, second) if first["y"] < second["y"] else (second, first)
            _, top_y, top_center = pos_map[top_room["id"]]
            _, bottom_y, bottom_center = pos_map[bottom_room["id"]]
            put(top_center, top_y + box_h - 1, "┬")
            put(bottom_center, bottom_y, "┴")
            for y in range(top_y + box_h, bottom_y):
                put(top_center, y, "│")
        elif first["y"] == second["y"]:
            left_room, right_room = (first, second) if first["x"] < second["x"] else (second, first)
            left_x, left_y, _ = pos_map[left_room["id"]]
            right_x, right_y, _ = pos_map[right_room["id"]]
            row_y = left_y + 1
            put(left_x + box_w - 1, row_y, "┤")
            put(right_x, right_y + 1, "├")
            for x in range(left_x + box_w, right_x):
                put(x, row_y, "─")
        if include_notes:
            note_bits = []
            if meta["kind"] == "secret":
                note_bits.append("secret door")
            if meta["locks"]:
                for lock in meta["locks"]:
                    lock_note = lock.get("map_label") or lock.get("type", "lock").replace("_", " ")
                    if lock.get("requires"):
                        lock_note += f" ({_pretty_key_name(lock['requires'])})"
                    note_bits.append(lock_note)
            if meta.get("label") and not note_bits:
                note_bits.append(meta["label"])
            if note_bits:
                notes.append(f"- {meta['a']} <-> {meta['b']}: {', '.join(note_bits)}")

    lines = ["".join(row).rstrip() for row in canvas]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    output = "\n".join(lines)
    if include_notes and notes:
        output += "\n\nConnector Notes\n" + "\n".join(sorted(set(notes)))
    return output

def dungeon_to_markdown(data: dict[str, Any]) -> str:
    validate_dungeon(data)
    dungeon = data["dungeon"]
    lines = [
        f"# {dungeon['name']}",
        "",
        "Generated with `tools/delvekit_seed.py`.",
        "",
        f"- size: `{dungeon['size']}`",
        f"- difficulty: `{dungeon['difficulty']}`",
        f"- seed: `{dungeon.get('seed', '')}`",
        f"- title draft: {dungeon.get('title_draft', '') or dungeon.get('name', '') or 'n/a'}",
        f"- player blurb draft: {dungeon.get('player_blurb_draft', '') or dungeon.get('player_blurb', '') or 'n/a'}",
        f"- player blurb: {dungeon.get('player_blurb', '') or 'n/a'}",
        f"- character motivation: {dungeon.get('character_motivation', '') or 'n/a'}",
        "",
        "## Hidden GM Map",
        "",
        "```text",
        render_map(data, mode="gm"),
        "```",
        "",
        "## Room Key",
        "",
    ]
    for room in sorted(data["rooms"], key=lambda item: int(item["id"])):
        lines.extend(
            [
                f"### {room['id']}. {room['name']}",
                "",
                f"- **Description:** {room['description']}",
                f"- **Atmosphere:** {room['atmosphere']}",
                f"- **Visible exits:** {_room_exit_summary(room.get('exits', []))}",
                f"- **Hidden exits:** {_room_exit_summary(room.get('secret_exits', []))}",
                f"- **Contents:** {', '.join(room.get('contents', [])) or 'none'}",
                f"- **Tags:** {', '.join(sorted(set(room.get('role_tags', []) + room.get('trap_tags', []) + room.get('puzzle_tags', []) + room.get('faction_tags', []) + room.get('solo_monster_tags', []) + room.get('boss_tags', []) + room.get('treasure_tags', [])))) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"

def pitch_polish_payload(data: dict[str, Any]) -> dict[str, Any]:
    validate_dungeon(data)
    dungeon = data["dungeon"]
    return {
        "size": dungeon.get("size", "tiny"),
        "difficulty": dungeon.get("difficulty", "medium"),
        "style_label": dungeon.get("style_label", ""),
        "subtheme": dungeon.get("subtheme", ""),
        "draft_title": dungeon.get("title_draft") or dungeon.get("name", ""),
        "draft_blurb": dungeon.get("player_blurb_draft") or dungeon.get("player_blurb", ""),
        "pitch_skeleton": dungeon.get("pitch_skeleton", {}),
    }

def apply_polished_pitch(data: dict[str, Any], *, title: str, blurb: str) -> dict[str, Any]:
    validate_dungeon(data)
    dungeon = data["dungeon"]
    dungeon["name"] = title.strip()
    dungeon["id"] = _sslib.slugify(dungeon["name"], fallback="delvekit_site")
    dungeon["player_blurb"] = blurb.strip()
    return data

def render_pitch_polish_prompt(data: dict[str, Any], prompt_text: str) -> str:
    payload = pitch_polish_payload(data)
    return (
        f"{prompt_text.rstrip()}\n\n"
        "### Delvekit Pitch Payload\n\n"
        "```json\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
        "```\n"
    )

def adventure_polish_payload(data: dict[str, Any]) -> dict[str, Any]:
    validate_dungeon(data)
    dungeon = data["dungeon"]
    rooms = []
    for room in sorted(data["rooms"], key=lambda item: int(item["id"])):
        rooms.append(
            {
                "id": room["id"],
                "name": room["name"],
                "description": room["description"],
                "atmosphere": room["atmosphere"],
                "contents": room.get("contents", []),
                "visible_exits": room.get("exits", []),
                "hidden_exits": room.get("secret_exits", []),
                "locks": room.get("locks", []),
                "trap_tags": room.get("trap_tags", []),
                "puzzle_tags": room.get("puzzle_tags", []),
                "faction_tags": room.get("faction_tags", []),
                "solo_monster_tags": room.get("solo_monster_tags", []),
                "boss_tags": room.get("boss_tags", []),
                "treasure_tags": room.get("treasure_tags", []),
                "role_tags": room.get("role_tags", []),
            }
        )
    return {
        "dungeon": {
            "name": dungeon.get("name", ""),
            "title_draft": dungeon.get("title_draft", ""),
            "player_blurb": dungeon.get("player_blurb", ""),
            "player_blurb_draft": dungeon.get("player_blurb_draft", ""),
            "style_label": dungeon.get("style_label", ""),
            "subtheme": dungeon.get("subtheme", ""),
            "size": dungeon.get("size", "tiny"),
            "difficulty": dungeon.get("difficulty", "medium"),
            "hook_type": dungeon.get("hook_type", ""),
            "hook_summary": dungeon.get("hook_summary", ""),
            "hook_target": dungeon.get("hook_target", ""),
            "character_motivation": dungeon.get("character_motivation", ""),
            "pitch_skeleton": dungeon.get("pitch_skeleton", {}),
        },
        "maps": {
            "hidden_gm_map": render_map(data, mode="gm"),
            "player_map_start": render_map(data, mode="player", frontier=True),
        },
        "keys": data.get("keys", []),
        "factions": data.get("factions", []),
        "monster_groups": data.get("monster_groups", []),
        "solo_monsters": data.get("solo_monsters", []),
        "bosses": data.get("bosses", []),
        "weird_npcs": data.get("weird_npcs", []),
        "rooms": rooms,
    }

def render_adventure_polish_prompt(data: dict[str, Any], prompt_text: str) -> str:
    payload = adventure_polish_payload(data)
    return (
        f"{prompt_text.rstrip()}\n\n"
        "### Delvekit Adventure Payload\n\n"
        "```json\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
        "```\n"
    )

def _room_exit_summary(exits: list[dict[str, Any]]) -> str:
    if not exits:
        return "none"
    return ", ".join(f"{item.get('label', 'passage')} -> {item['to']}" for item in exits)

def yaml_template() -> str:
    template = {
        "schema_version": SCHEMA_VERSION,
        "dungeon": {
            "id": "example_delve",
            "name": "Example Delve",
            "style": "reliquary",
            "style_label": "candlelit reliquary",
            "subtheme": "a shrine-complex of ash and broken vows",
            "skin": "candlelight_dungeons",
            "addon": "candlelight_delvekit",
            "size": "tiny",
            "difficulty": "medium",
            "start_room": "1",
            "hook_type": "artifact_heist",
            "hook_summary": "steal a single relic and get out alive",
            "hook_target": "the saint-bone lantern",
            "pitch_skeleton": {},
            "title_draft": "A short draft title generated from the pitch skeleton.",
            "player_blurb_draft": "A draft player-facing pitch generated from the pitch skeleton.",
            "player_blurb": "A final polished player-facing pitch for the site.",
            "character_motivation": "A concrete reason a delver would brave the place.",
        },
        "rooms": [
            {
                "id": "1",
                "name": "Entry Stairs",
                "x": 0,
                "y": 0,
                "description": "Cold steps descend into damp dark.",
                "atmosphere": "wet limestone and candle ash",
                "contents": ["spent torches"],
                "exits": [{"to": "2", "label": "north passage"}],
                "secret_exits": [],
                "locks": [],
                "trap_tags": [],
                "puzzle_tags": [],
                "faction_tags": [],
                "solo_monster_tags": [],
                "boss_tags": [],
                "treasure_tags": [],
                "role_tags": ["start"],
                "discovered": {"room": True, "visible_exits": ["2"], "secret_exits": [], "notes": ["cold draught"]},
            }
        ],
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
    return yaml.safe_dump(template, sort_keys=False)
