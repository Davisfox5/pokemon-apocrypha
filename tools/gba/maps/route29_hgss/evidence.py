#!/usr/bin/env python3
"""Review evidence for the decoded-HGSS Route 29 rebuild.

  python3 tools/gba/maps/route29_hgss/evidence.py ENGINE_DIR [RUNTIME_OUT_DIR]

Writes into gba/art/route29-hgss/evidence/:
  compare-NN-xA-yB.png   coordinate-labelled HGSS render (with the decoded material letter on every cell) beside the
                         native render of the same cells, one sheet per 24x14-cell window of the reconstructed region
  overview.png           the whole route: HGSS render above, native below, both at cell scale with a column ruler
  audit.json             square-by-square check of native collision and material class against the decoded grids,
                         with every disagreement listed and classified (declared adaptation or defect)
  gameplay.png           contact sheet of the headless mGBA frames when RUNTIME_OUT_DIR is given
  hashes.json            sha256 of the layout, tileset files, map.json and the ROM/ELF when present
"""
from __future__ import annotations
import hashlib, json, re, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from tiles import Tileset  # noqa: E402

GAME = Path(sys.argv[1]).resolve()
OUT = ROOT / 'gba/art/route29-hgss'
EV = OUT / 'evidence'
MAP, TS = 'CherrygroveRoute29Approach', 'route29_hgss'
COL0, ROW0, W, H = 1, 3, 98, 54
REGION_COLS, RIDGE_DST = range(10, 88), 35
RENDER = ROOT / 'gba/art/claude-routes/references/route29-hgss.png'
ORIGIN = (4, 5)
FONT = ImageFont.load_default()


def load():
    mat = (OUT / 'source/material-grid.txt').read_text().splitlines()
    trav = (OUT / 'source/traversal-grid.txt').read_text().splitlines()
    grid = np.frombuffer((GAME / f'data/layouts/{MAP}/map.bin').read_bytes(), dtype='<u2').reshape(H, W)
    ts = Tileset(GAME, TS, 'cherrygrove')
    return mat, trav, grid, ts


def label_grid(img, x0, y0, cols, rows, cell, letters=None, scale=2):
    """Scale a cell-aligned crop, draw the cell grid and coordinate rulers, and optionally a letter per cell."""
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    pad = 14
    out = Image.new('RGB', (img.width + pad, img.height + pad), (24, 24, 28)); out.paste(img, (pad, pad)); d = ImageDraw.Draw(out)
    cs = cell * scale
    for i in range(cols + 1):
        d.line([(pad + i * cs, pad), (pad + i * cs, pad + rows * cs)], fill=(0, 0, 0), width=1)
        if i < cols and i % 2 == 0: d.text((pad + i * cs + 2, 1), str(x0 + i), fill=(255, 255, 255), font=FONT)
    for j in range(rows + 1):
        d.line([(pad, pad + j * cs), (pad + cols * cs, pad + j * cs)], fill=(0, 0, 0), width=1)
        if j < rows: d.text((1, pad + j * cs + 2), str(y0 + j), fill=(255, 255, 255), font=FONT)
    if letters:
        for j in range(rows):
            for i in range(cols):
                ch = letters(x0 + i, y0 + j)
                if ch and ch != '.': d.text((pad + i * cs + cs - 8, pad + j * cs + cs - 11), ch, fill=(255, 255, 0), font=FONT)
    return out


def comparisons(mat, trav, grid, ts):
    ref = Image.open(RENDER).convert('RGB')
    native = ts.map_image(grid.ravel().tolist(), W)
    native.save(EV / 'native-map.png')
    HH, HW = len(mat), len(mat[0])
    def letter(hx, hz): return mat[hz][hx] if 0 <= hz < HH and 0 <= hx < HW else ''
    n = 0; index = []
    for hz0 in range(0, 29, 14):
        for hx0 in range(9, 87, 24):
            cols, rows = min(24, 87 - hx0), min(14, 29 - hz0)
            ox, oy = ORIGIN
            o = ref.crop((ox + hx0 * 16, oy + hz0 * 16, ox + (hx0 + cols) * 16, oy + (hz0 + rows) * 16))
            m = native.crop(((hx0 + COL0) * 16, (hz0 + ROW0) * 16, (hx0 + cols + COL0) * 16, (hz0 + rows + ROW0) * 16))
            a = label_grid(o, hx0, hz0, cols, rows, 16, letter); b = label_grid(m, hx0 + COL0, hz0 + ROW0, cols, rows, 16)
            sheet = Image.new('RGB', (a.width + b.width + 24, max(a.height, b.height) + 18), (24, 24, 28)); d = ImageDraw.Draw(sheet)
            d.text((4, 2), f'HGSS render + decoded material (HGSS cells x{hx0}-{hx0 + cols - 1}, z{hz0}-{hz0 + rows - 1})', fill=(255, 255, 255), font=FONT)
            d.text((a.width + 28, 2), f'native Emerald render (map cells x{hx0 + COL0}-{hx0 + cols + COL0 - 1}, y{hz0 + ROW0}-{hz0 + rows + ROW0 - 1})', fill=(255, 255, 255), font=FONT)
            sheet.paste(a, (0, 18)); sheet.paste(b, (a.width + 24, 18))
            name = f'compare-{n:02d}-x{hx0}-z{hz0}.png'; sheet.save(EV / name); index.append(name); n += 1
    # overview: both at half scale with a ruler
    o = ref.crop((ORIGIN[0], ORIGIN[1], ORIGIN[0] + HW * 16, ORIGIN[1] + HH * 16)).resize((HW * 8, HH * 8), Image.LANCZOS)
    m = native.resize((W * 8, H * 8), Image.LANCZOS)
    sheet = Image.new('RGB', (max(o.width, m.width) + 16, o.height + m.height + 44), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    d.text((4, 2), 'HGSS Route 29 (decoded DS map, rendered 1:1, HGSS cell 0,0 at the top-left)', fill=(255, 255, 255), font=FONT)
    sheet.paste(o, (8 + COL0 * 8, 14))
    d.text((4, o.height + 22), 'native Emerald layout (map cell 0,0 at the top-left; columns 0-9 and 88-97 and rows 35-53 are the carried adapters and ridge)', fill=(255, 255, 255), font=FONT)
    sheet.paste(m, (8, o.height + 34))
    for x in range(0, W, 10): d.text((8 + x * 8, o.height + 34 + m.height + 1), str(x), fill=(255, 255, 255), font=FONT)
    sheet.save(EV / 'overview.png')
    return index


def audit(mat, trav, grid, ts, adaptations):
    mb = {i: n for i, n in enumerate(re.findall(r'^\s+(MB_[A-Z0-9_]+),', (GAME / 'include/constants/metatile_behaviors.h').read_text(), re.M))}
    absorbed = {tuple(a['cell']) for a in adaptations['tree_fitting'] if 'absorbed' in a['change']}
    leftover = {tuple(a['cell']) for a in adaptations['tree_fitting'] if 'left without' in a['change']}
    cut = {tuple(c) for c in adaptations.get('cuttable_trees', [])}
    cache = {}
    def klass(mid):
        if mid not in cache:
            ents = ts.blocks[mid >= 512][mid - 512 if mid >= 512 else mid]
            if any(e and (e >> 12) in (3, 10) for e in ents): cache[mid] = 'tree'; return 'tree'       # tree or blossom tiles (palette banks 3 and 10)
            im = np.asarray(ts.render(mid)).astype(int); r, g, b = im[..., 0], im[..., 1], im[..., 2]
            sand = ((r > 190) & (g > 170) & (b < 170) & (b > 90)).mean(); lawn = ((g > 180) & (r < 150) & (b > 130)).mean()
            dark_green = ((g > 60) & (g < 150) & (r < 130) & (b < 110)).mean(); pink = ((r > 140) & (b > 140) & (r > g + 20) & (b > g + 20)).mean()
            cache[mid] = 'sand' if sand > 0.5 else 'tree' if (dark_green > 0.45 or pink > 0.3) else 'lawn' if lawn > 0.6 else 'other'
        return cache[mid]
    rows = []; counts = Counter()
    HH, HW = len(mat), len(mat[0])
    for hz in range(HH):
        for hx in range(HW):
            x, y = hx + COL0, hz + ROW0
            if x not in REGION_COLS or y >= RIDGE_DST: continue
            v = int(grid[y, x]); mid = v & 1023; blocked = bool((v >> 10) & 3)
            beh = mb.get((ts.attrs[mid >= 512][mid - 512 if mid >= 512 else mid]) & 0xFF, '?')
            m, t = mat[hz][hx], trav[hz][hx]
            want_blocked = t in 'Xv' or m == '_'            # ledges are impassable in native layouts; the jump overrides it
            k = klass(mid)
            ok_trav = (blocked == want_blocked)
            ok_mat = {'T': k == 'tree', 'G': beh == 'MB_TALL_GRASS', '_': beh == 'MB_JUMP_SOUTH', 'P': k == 'sand', '.': k in ('lawn', 'other'),
                      '|': True, '!': True, 'c': True, 'g': True, 'D': True, 's': True, 'A': True, 'x': k == 'lawn'}.get(m, True)
            if m in '|!c' and k == 'tree': ok_mat = False
            if ok_trav and ok_mat: counts['agree'] += 1; continue
            why = 'defect'
            if (x, y) in absorbed and m == '.' and blocked: why = 'declared: lawn absorbed under a whole tree'
            elif (x, y) in leftover: why = 'declared: forest cell without tree art (blocked)'
            elif m == 'D' and blocked: why = 'declared: gate door kept blocked (interior map not built)'
            elif m == 'x' and not blocked and (x, y) in cut: why = 'declared: HGSS tree sprite -> native cuttable-tree object event (object blocks)'
            elif m == '.' and k == 'tree' and not blocked: why = 'defect: tree art on an open cell'
            counts[why] += 1
            rows.append(dict(hgss=[hx, hz], map=[x, y], material=m, traversal=t, native_blocked=blocked, native_behavior=beh, native_class=k, metatile=f'{mid:#05x}', verdict=why))
    return dict(cells_checked=sum(counts.values()), summary=dict(counts), disagreements=rows)


def gallery(run):
    files = sorted(run.glob('*.png'))
    if not files: return None
    cols = 6; th = 160 + 14; tw = 240
    sheet = Image.new('RGB', (cols * (tw + 4), ((len(files) + cols - 1) // cols) * (th + 4)), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        x, y = (i % cols) * (tw + 4), (i // cols) * (th + 4)
        sheet.paste(Image.open(f).convert('RGB'), (x, y + 14)); d.text((x + 2, y + 1), f.stem[:38], fill=(255, 255, 255), font=FONT)
    sheet.save(EV / 'gameplay.png'); return len(files)


def main():
    EV.mkdir(parents=True, exist_ok=True)
    mat, trav, grid, ts = load()
    adaptations = json.loads((OUT / 'source/adaptations.json').read_text())
    index = comparisons(mat, trav, grid, ts)
    a = audit(mat, trav, grid, ts, adaptations); (EV / 'audit.json').write_text(json.dumps(a, indent=2) + '\n')
    n = gallery(Path(sys.argv[2])) if len(sys.argv) > 2 else None
    files = [GAME / f'data/layouts/{MAP}/map.bin', GAME / f'data/maps/{MAP}/map.json', GAME / 'data/layouts/layouts.json'] + sorted((GAME / 'data/tilesets/secondary' / TS).rglob('*.*')) + [GAME / 'pokeemerald.gba', GAME / 'pokeemerald.elf']
    hashes = {str(f.relative_to(GAME)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.exists()}
    (EV / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(json.dumps(dict(comparisons=index, audit=a['summary'], gameplay_frames=n, hashed=len(hashes))))


if __name__ == '__main__':
    main()
