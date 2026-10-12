#!/usr/bin/env python3
"""Generate Chapter 1's continuous three-person Cherrygrove tour.

The three actors occupy successive cells of one collision-checked route.
Regenerate after changing the city layout, then verify actors in native mGBA.
"""
from collections import deque
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
if len(sys.argv) != 2:
    raise SystemExit("usage: build_chapter1_tour.py ISOLATED_GAME_WORKBENCH")
WORK = Path(sys.argv[1]).resolve()
MAP = WORK / "data/layouts/CherrygroveCity/map.bin"
SCRIPT = WORK / "data/maps/CherrygroveCity/scripts.inc"
WIDTH, HEIGHT = 80, 48
CELLS = struct.unpack("<" + "H" * (WIDTH * HEIGHT), MAP.read_bytes())

# Fixed residents are locked for the cutscene. Avoid their tiles, plus the
# player's battle spectators. Gold and Kestra are deliberately excluded.
OCCUPIED = {
    (37, 20), (44, 8), (47, 21), (59, 23), (56, 12),
    (66, 18), (47, 12), (38, 22), (62, 29), (51, 21),
}
STOPS = [
    ("Mart", [(49, 11), (51, 11)], "CherrygroveCity_TourMart", ("left", "right", "right")),
    ("Center", [(61, 11)], "CherrygroveCity_TourCenter", ("left", "right", "right")),
    ("Route29", [(73, 17), (73, 18), (75, 18)], "CherrygroveCity_TourRoute29", ("left", "right", "right")),
    ("Shore", [(35, 20)], "CherrygroveCity_TourShore", ("right", "left", "down")),
    ("House", [(49, 20)], None, ("left", "right", "right")),
]
DIRS = [((0, -1), "up"), ((1, 0), "right"), ((0, 1), "down"), ((-1, 0), "left")]


def free(point):
    x, y = point
    if not 0 <= x < WIDTH or not 0 <= y < HEIGHT:
        return False
    cell = CELLS[y * WIDTH + x]
    return not cell & 0xC00 and cell >> 12 == 3 and point not in OCCUPIED


def path(start, target, trailing):
    queue = deque([start])
    previous = {start: None}
    while queue:
        point = queue.popleft()
        if point == target:
            break
        for (dx, dy), _ in DIRS:
            neighbor = point[0] + dx, point[1] + dy
            if neighbor not in previous and neighbor not in trailing and free(neighbor):
                previous[neighbor] = point
                queue.append(neighbor)
    if target not in previous:
        raise ValueError(f"No clear tour route from {start} to {target}")
    result = []
    point = target
    while point != start:
        result.append(point)
        point = previous[point]
    return result[::-1]


def movement(points):
    result = []
    for first, second in zip(points, points[1:]):
        delta = second[0] - first[0], second[1] - first[1]
        direction = next(name for (dx, dy), name in DIRS if (dx, dy) == delta)
        result.append(f"    walk_fast_{direction}")
    return result + ["    step_end"]


def make():
    # Route 30 reconnects at the north edge of town. Gold leads the two kids
    # south from that entrance; nobody is warped to his doorstep.
    points = [(44, 0), (44, 1), (44, 2)]
    chunks = []
    for name, via, message, faces in STOPS:
        prior = len(points) - 1
        for target in via:
            points.extend(path(points[-1], target, set(points[-3:-1])))
        end = len(points) - 1
        chunks.append((name, prior, end, message, faces))

    lines = [
        "CherrygroveCity_TourWalk:",
        "    @ Walk into town from the Route 30 connection without a scene warp.",
    ]
    for name, _, _, message, _ in chunks:
        for actor in ("GOLD", "KESTRA", "PLAYER"):
            lines.append(f"    applymovement LOCALID_{'CAST_' if actor != 'PLAYER' else ''}{actor}, CherrygroveCity_Tour{name}{actor}")
        lines.append("    waitmovement 0")
        for actor in ("GOLD", "KESTRA", "PLAYER"):
            lines.append(f"    applymovement LOCALID_{'CAST_' if actor != 'PLAYER' else ''}{actor}, CherrygroveCity_Tour{name}{actor}Face")
        lines.append("    waitmovement 0")
        if message:
            lines += [f"    msgbox {message}, MSGBOX_DEFAULT", "    closemessage"]
    lines += ["    return"]
    for name, prior, end, _, faces in chunks:
        # At segment start: player=prior-2, Kestra=prior-1, Gold=prior.
        # All take the same number of steps, leaving two cells of separation.
        for actor, shift, face in zip(("GOLD", "KESTRA", "PLAYER"), (0, -1, -2), faces):
            lines.append(f"CherrygroveCity_Tour{name}{actor}:")
            lines.extend(movement(points[prior + shift : end + shift + 1]))
            lines += [f"CherrygroveCity_Tour{name}{actor}Face:", f"    face_{face}", "    step_end"]
    return "\n".join(lines) + "\n", chunks, points


def main():
    generated, chunks, points = make()
    source = SCRIPT.read_text()
    source = source.replace(
        "    call_if_eq VAR_APOC_CHAPTER_STAGE, 30, CherrygroveCity_TourCenterPosition\n"
        "    call_if_eq VAR_APOC_CHAPTER_STAGE, 31, CherrygroveCity_TourMartPosition\n"
        "    call_if_eq VAR_APOC_CHAPTER_STAGE, 32, CherrygroveCity_TourRoutePosition\n"
        "    call_if_eq VAR_APOC_CHAPTER_STAGE, 33, CherrygroveCity_TourShorePosition\n"
        "    call_if_eq VAR_APOC_CHAPTER_STAGE, 34, CherrygroveCity_TourHousePosition\n", "")
    source = source.replace(
        "    map_script_2 VAR_APOC_CHAPTER_STAGE, 30, CherrygroveCity_TourCenterScene\n"
        "    map_script_2 VAR_APOC_CHAPTER_STAGE, 31, CherrygroveCity_TourMartScene\n"
        "    map_script_2 VAR_APOC_CHAPTER_STAGE, 32, CherrygroveCity_TourRouteScene\n"
        "    map_script_2 VAR_APOC_CHAPTER_STAGE, 33, CherrygroveCity_TourShoreScene\n"
        "    map_script_2 VAR_APOC_CHAPTER_STAGE, 34, CherrygroveCity_TourHouseScene\n", "")
    if "CherrygroveCity_TourCenterPosition:" in source:
        pos_start = source.index("CherrygroveCity_TourCenterPosition:")
        pos_end = source.index("CherrygroveCity_OnFrame:", pos_start)
        source = source[:pos_start] + source[pos_end:]
    start_label = "CherrygroveCity_TourCenterScene:" if "CherrygroveCity_TourCenterScene:" in source else "CherrygroveCity_TourWalk:"
    start = source.index(start_label)
    end = source.index("CherrygroveCity_KestraInsists:", start)
    source = source[:start] + generated + source[end:]
    source = source.replace(
        "    msgbox CherrygroveCity_GoldTourStart, MSGBOX_DEFAULT\n"
        "    closemessage\n"
        "    setvar VAR_APOC_CHAPTER_STAGE, 30\n"
        "    fadescreen FADE_TO_BLACK\n"
        "    warp MAP_CHERRYGROVE_CITY, 60, 12\n"
        "    waitstate\n"
        "    end\n",
        "    lockall\n"
        "    msgbox CherrygroveCity_GoldTourStart, MSGBOX_DEFAULT\n"
        "    closemessage\n"
        "    call CherrygroveCity_TourWalk\n"
        "    goto CherrygroveCity_GoldCeremony\n",
    )
    # The tour locked every actor; fully release them after the starter beat.
    source = source.replace("    removeobject LOCALID_CAST_GOLD\n    release\n    end\nCherrygroveCity_GoldAfterStarter:",
                            "    removeobject LOCALID_CAST_GOLD\n    releaseall\n    end\nCherrygroveCity_GoldAfterStarter:")
    SCRIPT.write_text(source)
    for name, prior, end, _, _ in chunks:
        print(name, end - prior, "steps", "player/Kestra/Gold", points[end-2:end+1])


if __name__ == "__main__":
    main()
