#!/usr/bin/env python3
"""Build artwork-library/ from the four decomps' PNG assets (straight copies + renames)."""
import re, shutil, sys
from pathlib import Path

ROOT = Path("/Users/davisfox/Documents/GitHub/the-omni-hack")
D = ROOT / "disasm"
OUT = ROOT / "artwork-library"

counts = {}

def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    key = str(dst.relative_to(OUT).parts[0:2])
    counts[dst.parent] = counts.get(dst.parent, 0) + 1

def copy_glob(srcdir: Path, pattern: str, dstdir: Path, prefix=""):
    n = 0
    for p in sorted(srcdir.glob(pattern)):
        if p.is_file():
            copy(p, dstdir / (prefix + p.name))
            n += 1
    return n

# ---------------- Gen 3 (emerald, firered) ----------------
def gen3(game, outname):
    g = D / game / "graphics"
    o = OUT / outname

    # pokemon: per-species dirs with front/back/icon
    for sp in sorted((g / "pokemon").iterdir()):
        if not sp.is_dir():
            continue
        for part in ("front", "back", "icon"):
            f = sp / f"{part}.png"
            if f.exists():
                copy(f, o / "pokemon" / f"{sp.name}_{part}.png")

    # trainers
    copy_glob(g / "trainers" / "front_pics", "*.png", o / "trainers", "")
    copy_glob(g / "trainers" / "back_pics", "*.png", o / "trainers", "back_")

    # overworld people + objects
    pics = g / "object_events" / "pics"
    copy_glob(pics / "people", "**/*.png", o / "overworld-people")
    for sub in ("misc", "dolls", "cushions", "berry_trees", "pokemon"):
        d = pics / sub
        if d.exists():
            for p in sorted(d.glob("**/*.png")):
                copy(p, o / "overworld-objects" / f"{sub}_{p.stem}.png")

    # items
    icons = g / "items" / "icons"
    if icons.exists():
        copy_glob(icons, "**/*.png", o / "items")

    # doors
    doors = g / "door_anims"
    if doors.exists():
        copy_glob(doors, "*.png", o / "doors")

    # tileset tile sheets (raw tiles; block sheets rendered separately)
    ts = D / game / "data" / "tilesets"
    for kind in ("primary", "secondary"):
        kd = ts / kind
        if not kd.exists():
            continue
        for t in sorted(kd.iterdir()):
            f = t / "tiles.png"
            if f.exists():
                copy(f, o / "tilesets" / "tiles" / f"{kind}_{t.name}_tiles.png")

gen3("pokeemerald", "emerald-hoenn")
gen3("pokefirered", "firered-kanto")

# ---------------- Platinum ----------------
o = OUT / "platinum-sinnoh"
for sp in sorted((D / "pokeplatinum" / "res" / "pokemon").iterdir()):
    if not sp.is_dir():
        continue
    for part in ("male_front", "male_back", "female_front", "female_back", "icon"):
        f = sp / f"{part}.png"
        if f.exists():
            copy(f, o / "pokemon" / f"{sp.name}_{part}.png")
copy_glob(D / "pokeplatinum" / "res" / "graphics" / "signposts", "*.png", o / "overworld-objects")

# ---------------- HeartGold PNGs ----------------
o = OUT / "heartgold-johto"
# species number -> name map
species = {}
sh = D / "pokeheartgold" / "include" / "constants" / "species.h"
for m in re.finditer(r"#define SPECIES_(\w+)\s+(\d+)", sh.read_text()):
    n = int(m.group(2))
    if n not in species:
        species[n] = m.group(1).lower()

pg = D / "pokeheartgold" / "files" / "poketool" / "pokegra" / "pokegra"
for sp in sorted(pg.iterdir()):
    if not sp.is_dir() or not sp.name.isdigit():
        continue
    n = int(sp.name)
    name = species.get(n, sp.name)
    for sex in ("male", "female"):
        for part in ("front", "back"):
            f = sp / sex / f"{part}.png"
            if f.exists():
                suffix = f"{part}.png" if sex == "male" else f"female_{part}.png"
                copy(f, o / "pokemon" / f"{sp.name}_{name}_{suffix}")

copy_glob(D / "pokeheartgold" / "files" / "poketool" / "icongra" / "poke_icon", "*.png",
          o / "pokemon-icons")
copy_glob(D / "pokeheartgold" / "files" / "fielddata" / "graphic" / "preview_graphic" / "preview_graphic",
          "*.png", o / "trainers")

# ---------------- report ----------------
total = 0
for d in sorted(counts):
    print(f"{counts[d]:5d}  {d.relative_to(OUT)}")
    total += counts[d]
print(f"TOTAL {total}")
