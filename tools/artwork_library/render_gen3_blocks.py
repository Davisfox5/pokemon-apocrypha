#!/usr/bin/env python3
"""Render Gen 3 tileset metatiles (16x16 blocks) into colored PNG block sheets."""
from pathlib import Path
from PIL import Image

ROOT = Path("/Users/davisfox/Documents/GitHub/the-omni-hack")
D = ROOT / "disasm"
GAMES = {
    "pokeemerald": dict(out="emerald-hoenn", prim_tiles=512, prim_pals=6, main_primary="general"),
    "pokefirered": dict(out="firered-kanto", prim_tiles=640, prim_pals=7, main_primary="general"),
}
COLS = 8  # metatiles per row in output sheet


def load_jasc(path):
    lines = path.read_text().splitlines()
    n = int(lines[2])
    return [tuple(int(v) for v in ln.split()) for ln in lines[3:3 + n]]


def load_palettes(tsdir):
    pals = {}
    pd = find_asset_dir(tsdir) / "palettes"
    if not pd.exists():
        pd = tsdir / "palettes"
    for p in sorted(pd.glob("*.pal")):
        try:
            pals[int(p.stem)] = load_jasc(p)
        except (ValueError, IndexError):
            pass
    return pals


def find_asset_dir(tsdir):
    """Some tilesets (e.g. secret_base) keep tiles/palettes in variant subdirs."""
    if (tsdir / "tiles.png").exists():
        return tsdir
    for sub in sorted(tsdir.iterdir()):
        if sub.is_dir() and (sub / "tiles.png").exists():
            return sub
    return tsdir


def load_tiles(tsdir):
    """Return list of 8x8 index arrays from tiles.png (16 tiles per row)."""
    img = Image.open(find_asset_dir(tsdir) / "tiles.png").convert("P")
    w, h = img.size
    px = img.load()
    tiles = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            tiles.append([[px[tx*8 + x, ty*8 + y] for x in range(8)] for y in range(8)])
    return tiles


def render(metatiles_bin, tile_lookup, pal_lookup, out_path):
    data = metatiles_bin.read_bytes()
    n = len(data) // 16
    if n == 0:
        return 0
    rows = (n + COLS - 1) // COLS
    sheet = Image.new("RGBA", (COLS * 16, rows * 16), (0, 0, 0, 0))
    px = sheet.load()
    for m in range(n):
        mx, my = (m % COLS) * 16, (m // COLS) * 16
        for layer in range(2):
            for q in range(4):  # quadrant: 2x2 tiles
                e = int.from_bytes(data[m*16 + layer*8 + q*2: m*16 + layer*8 + q*2 + 2], "little")
                tid, xf, yf, pi = e & 0x3FF, e & 0x400, e & 0x800, (e >> 12) & 0xF
                tile = tile_lookup(tid)
                pal = pal_lookup(pi)
                if tile is None or pal is None:
                    continue
                ox, oy = mx + (q % 2) * 8, my + (q // 2) * 8
                for y in range(8):
                    for x in range(8):
                        ci = tile[7 - y if yf else y][7 - x if xf else x]
                        if ci % 16 == 0:  # color 0 = transparent
                            continue
                        c = pal[ci % 16] if ci % 16 < len(pal) else (255, 0, 255)
                        px[ox + x, oy + y] = (c[0], c[1], c[2], 255)
    sheet.save(out_path)
    return n


for game, cfg in GAMES.items():
    ts = D / game / "data" / "tilesets"
    outdir = ROOT / "artwork-library" / cfg["out"] / "tilesets" / "blocks"
    outdir.mkdir(parents=True, exist_ok=True)
    PT, PP = cfg["prim_tiles"], cfg["prim_pals"]

    prim_dir = ts / "primary" / cfg["main_primary"]
    prim_tiles = load_tiles(prim_dir)
    prim_pals = load_palettes(prim_dir)

    total = 0
    # primary tilesets standalone
    for t in sorted((ts / "primary").iterdir()):
        if not (t / "metatiles.bin").exists():
            continue
        tiles = load_tiles(t)
        pals = load_palettes(t)
        n = render(t / "metatiles.bin",
                   lambda tid, tl=tiles: tl[tid] if tid < len(tl) else None,
                   lambda pi, pl=pals: pl.get(pi),
                   outdir / f"primary_{t.name}_blocks.png")
        total += n

    # secondary tilesets paired with main primary
    for t in sorted((ts / "secondary").iterdir()):
        if not (t / "metatiles.bin").exists():
            continue
        src = t
        if not list(t.glob("**/tiles.png")):
            # silph_co borrows condominiums' tiles/palettes (see headers.h)
            alt = t.parent / {"silph_co": "condominiums"}.get(t.name, "")
            if alt.name and (alt / "tiles.png").exists():
                src = alt
            else:
                print(f"  skip {t.name}: no tiles.png")
                continue
        tiles = load_tiles(src)
        pals = load_palettes(src)

        def tlook(tid, tl=tiles):
            if tid < PT:
                return prim_tiles[tid] if tid < len(prim_tiles) else None
            return tl[tid - PT] if tid - PT < len(tl) else None

        def plook(pi, pl=pals):
            if pi < PP:
                return prim_pals.get(pi)
            return pl.get(pi)

        n = render(t / "metatiles.bin", tlook, plook,
                   outdir / f"secondary_{t.name}_blocks.png")
        total += n
    print(f"{game}: rendered {total} metatiles into {len(list(outdir.glob('*.png')))} sheets")
