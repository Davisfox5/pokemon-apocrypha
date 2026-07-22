#!/usr/bin/env python3
"""Pack the artwork library into compact contact sheets for use in Claude Design.

Sheets stay <= ~1024px so vision models see them without downscaling.
Animation strips are represented by their first frame.
"""
from pathlib import Path
from PIL import Image

LIB = Path("/Users/davisfox/Documents/GitHub/the-omni-hack/artwork-library")
OUT = LIB / "_contact-sheets"
OUT.mkdir(exist_ok=True)
MAXW = MAXH = 1024
PAD = 2

def first_frame(img, frame=0):
    w, h = img.size
    if h >= 2 * w:
        f = frame if h >= (frame + 1) * w else 0
        return img.crop((0, f * w, w, (f + 1) * w))
    if w >= 2 * h:
        return img.crop((0, 0, h, h))
    return img

def make_sheets(files, name, crop_strips=False, cap=96, frame=0):  # frame: which strip frame to show
    thumbs = []
    for f in files:
        try:
            img = Image.open(f).convert("RGBA")
        except Exception:
            continue
        if crop_strips:
            img = first_frame(img, frame)
        if img.width > cap or img.height > cap:
            img = img.crop((0, 0, min(img.width, cap), min(img.height, cap)))
        thumbs.append(img)
    if not thumbs:
        return 0
    cw = max(t.width for t in thumbs) + PAD
    ch = max(t.height for t in thumbs) + PAD
    cols = max(1, MAXW // cw)
    rows_per_sheet = max(1, MAXH // ch)
    per_sheet = cols * rows_per_sheet
    nsheets = (len(thumbs) + per_sheet - 1) // per_sheet
    for s in range(nsheets):
        batch = thumbs[s*per_sheet:(s+1)*per_sheet]
        rows = (len(batch) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
        for i, t in enumerate(batch):
            x, y = (i % cols) * cw, (i // cols) * ch
            sheet.paste(t, (x + (cw - PAD - t.width)//2, y + (ch - PAD - t.height)//2), t)
        suffix = f"_{s+1:02d}" if nsheets > 1 else ""
        sheet.save(OUT / f"{name}{suffix}.png")
    return nsheets

def retile_blocks(game_dir, name):
    """Reflow 8-col block sheets into 32-col rows, stacked per game, split at 1024px."""
    sheets_out, strips = 0, []
    for f in sorted((game_dir / "tilesets" / "blocks").glob("*.png")):
        img = Image.open(f).convert("RGBA")
        bw = img.width // 16
        blocks = []
        for by in range(img.height // 16):
            for bx in range(bw):
                blocks.append(img.crop((bx*16, by*16, bx*16+16, by*16+16)))
        cols = 64
        rows = (len(blocks) + cols - 1) // cols
        strip = Image.new("RGBA", (cols * 16, rows * 16), (0, 0, 0, 0))
        for i, b in enumerate(blocks):
            strip.paste(b, ((i % cols) * 16, (i // cols) * 16), b)
        strips.append(strip)
    # stack strips with 8px gap, cut into <=1024-tall pages
    page, y = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)), 0
    for strip in strips:
        if y and y + strip.height > 1024:
            sheets_out += 1
            page.crop((0, 0, 1024, y)).save(OUT / f"{name}_{sheets_out:02d}.png")
            page, y = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)), 0
        sh = strip
        while sh.height > 1024:  # single strip taller than a page
            page.paste(sh.crop((0, 0, sh.width, 1024)), (0, 0))
            sheets_out += 1
            page.save(OUT / f"{name}_{sheets_out:02d}.png")
            page, y = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)), 0
            sh = sh.crop((0, 1024, sh.width, sh.height))
        page.paste(sh, (0, y), sh)
        y += sh.height + 8
    if y:
        sheets_out += 1
        page.crop((0, 0, 1024, y - 8)).save(OUT / f"{name}_{sheets_out:02d}.png")
    return sheets_out

total = 0
def run(files, name, **kw):
    global total
    n = make_sheets(sorted(files), name, **kw)
    print(f"{name}: {n} sheet(s)")
    total += n

# Pokemon (fronts only; full library has backs/females)
run((LIB/"heartgold-johto/pokemon").glob("*_front.png") - set() if False else
    [f for f in (LIB/"heartgold-johto/pokemon").glob("*_front.png") if "female" not in f.name],
    "hg_pokemon", cap=96)
run((LIB/"platinum-sinnoh/pokemon").glob("*_male_front.png"), "plat_pokemon", cap=96)
run((LIB/"emerald-hoenn/pokemon").glob("*_front.png"), "em_pokemon", cap=96)
run((LIB/"firered-kanto/pokemon").glob("*_front.png"), "fr_pokemon", cap=96)

run((LIB/"heartgold-johto/pokemon-icons").glob("*.png"), "hg_pokemon_icons", cap=64)

run((LIB/"heartgold-johto/trainers").glob("*.png"), "hg_trainer_mugshots", cap=192)
run((LIB/"emerald-hoenn/trainers").glob("*.png"), "em_trainers", cap=96)
run((LIB/"firered-kanto/trainers").glob("*.png"), "fr_trainers", cap=96)

run((LIB/"heartgold-johto/overworld-sprites").glob("*.png"), "hg_overworld_sprites",
    crop_strips=True, cap=64, frame=1)  # frame 1 = front-facing in HGSS strips
run((LIB/"emerald-hoenn/overworld-people").glob("*.png"), "em_overworld_people",
    crop_strips=True, cap=64)
run((LIB/"firered-kanto/overworld-people").glob("*.png"), "fr_overworld_people",
    crop_strips=True, cap=64)
run((LIB/"emerald-hoenn/overworld-objects").glob("*.png"), "em_overworld_objects",
    crop_strips=True, cap=64)
run((LIB/"firered-kanto/overworld-objects").glob("*.png"), "fr_overworld_objects",
    crop_strips=True, cap=64)
run((LIB/"platinum-sinnoh/overworld-objects").glob("*.png"), "plat_signposts",
    crop_strips=True, cap=64)

run((LIB/"heartgold-johto/items").glob("*.png"), "hg_items", cap=32)
run((LIB/"emerald-hoenn/items").glob("*.png"), "em_items", cap=32)
run((LIB/"firered-kanto/items").glob("*.png"), "fr_items", cap=32)

run((LIB/"emerald-hoenn/doors").glob("*.png"), "em_doors", crop_strips=True, cap=64)
run((LIB/"firered-kanto/doors").glob("*.png"), "fr_doors", crop_strips=True, cap=64)

n = retile_blocks(LIB/"emerald-hoenn", "em_blocks"); print(f"em_blocks: {n} sheet(s)"); total += n
n = retile_blocks(LIB/"firered-kanto", "fr_blocks"); print(f"fr_blocks: {n} sheet(s)"); total += n

print(f"TOTAL {total} contact sheets")
