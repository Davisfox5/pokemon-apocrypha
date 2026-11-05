"""Ice Path: its four floors built the way Dark Cave is, in HGSS's Ice Path colours.

    python3 tools/gba/maps/ice_path/assemble.py PATH/TO/pokeheartgold ENGINE_CHECKOUT

The owner's cave method (Dark Cave, accepted 2026-11-03): each floor is mapped cell by cell from
HGSS's own data (floor heights and tier tops from its mesh, ice, ladders, exits, rock objects),
drawn with the Johto routes' own pieces (FRLG rock laid out by the routes' rock_frlg, the routes'
road), then every colour is swapped for HGSS's own Ice Path colours (texture set 76). The layout
code is Dark Cave's assemble.py, used as a library; nothing of Dark Cave's art or tilesets is used.

Ice Path's own features are FRLG Icefall Cave's pieces (seafoam_islands_frlg), recoloured the
same way, colour for colour by brightness, never redrawn:

    slide ice       843   (HGSS's ice_fe01b floor, 0x20; Gen 3 MB_ICE, the player slides)
    ice crystals    679   (HGSS's rock piles d_rock01 and d_rock01s on the ice floors: crystals)
    drop holes      646   (B1F's four holes, which HGSS triggers by script; Gen 3 MB_MT_PYRE_HOLE)
    stairs          644   (Seafoam Islands' ice stairs: HGSS's two-cell flights in a one-row ice wall,
                           its floor cells with the slope bit, 0x08/0x06)
    ladder down     645   (a ladder into a hole: HGSS's dun_stairdw)
    ladder up       654 over 662   (HGSS's dun_stairup: its two warp cells take FRLG Seafoam's two
                           halves, the top over the foot, as Seafoam stacks them)

Writes source/assemble/<floor>{.png,-class.npy,-ledger.json,-terrace-grid.txt} and
evidence/assemble/<floor>-before-after.png.
"""
from __future__ import annotations
import importlib.util, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MAPS = HERE.parent
sys.path.insert(0, str(HERE))
import pack as P                                      # noqa: E402

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

R = _load('ice_path_hgss_render', HERE / 'hgss_render.py')
sys.path.insert(0, str(MAPS / 'dark_cave'))
A = _load('dark_cave_assemble', MAPS / 'dark_cave/assemble.py')   # the cave method: layout, ground, colour swap
E, D = A.E, A.D
ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/ice-path'
SRC, EV = ART / 'source', ART / 'evidence'
A.SRC, A.EV = SRC, EV
PX = 16
VOID, FLOOR, FACE, TOP, RIM, BOULDER, STAIRS, WATER, EXIT = range(9)
ICEFALL = ('general_frlg', 'seafoam_islands_frlg')
PIECE = dict(ice=843, crystal=679, rock=643, hole=646, ladder_down=645, ladder_up=662, ladder_top=654, stairs=644,
             pillar_tl=648, pillar_tr=650, pillar_bl=664, pillar_br=709)   # the pillar: Icefall B1F (8-9, 4-6), its top and foot rows
SNOW = (641, 657)                                    # Icefall's plain floors: their colours are the snow cut from a piece
HOLES = {'b1f': [(11, 10), (10, 18), (18, 7), (19, 19)]}      # zone 223_D39R0102's coord triggers

# --------------------------------------------------------------------------- colours
lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

def tones(tex0, *names):
    dec = {e.name: e for e in tex0.textures}
    out = set()
    for n in names:
        if n in dec:
            out |= {tuple(int(v) for v in c) for c in R.decode(tex0, dec[n], n + '_pl')[..., :3].reshape(-1, 3)}
    return sorted(out, key=lum)

def ramp(cols):
    """A route-rock ramp (outline, then six tones light to dark) from a texture's own colours."""
    cs = sorted(cols, key=lum)
    pick = [cs[min(len(cs) - 1, int(round(q * (len(cs) - 1))))] for q in (0.97, 0.82, 0.66, 0.5, 0.34, 0.18)]
    outline = tuple(int(v * 0.55) for v in cs[0])
    return [outline] + pick

# --------------------------------------------------------------------------- the mapped shapes
def ledger(side):
    """assemble.ledger's records for an Ice Path floor (lab, floor, peak, ground, level, flags), plus
    kind: floor, ice, ladder, exit, hole, blocked; and piece: the Icefall piece drawn on the cell."""
    hg = SRC / f'hgss/{side}'
    W, H = P.SIZE[side]
    m = np.load(hg / 'hgss-ground-materials.npz')
    names = [str(v) for v in m['names']]
    hcls = np.array([P.CLASS.get(n, FLOOR) for n in names] + [VOID], np.int16)[m['material']]
    major = np.array([[Counter(hcls[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX].ravel().tolist()).most_common(1)[0][0]
                       for x in range(W)] for y in range(H)])
    perm = np.load(hg / 'hgss-permissions.npz')
    types, coll = perm['types'], perm['collision']
    height = np.nan_to_num(np.load(hg / 'hgss-cell-peak.npy'))
    foot = np.nan_to_num(np.load(hg / 'hgss-cell-foot.npy'))
    count = lambda n: (m['material'] == names.index(n)).reshape(H, PX, W, PX).sum((1, 3)) if n in names else np.zeros((H, W), int)
    big, small = count('d_rock01'), count('d_rock01s')
    piles = big + small
    ev = json.loads((SRC / f'hgss-events/{side}.json').read_text())
    floor_no = {'MAP_ICE_PATH_1F': 1, 'MAP_ICE_PATH_B1F': 2, 'MAP_ICE_PATH_B2F': 3, 'MAP_ICE_PATH_B3F': 4}
    here = {'1f': 1, 'b1f': 2, 'b2f': 3, 'b3f': 4}[side]
    ladder = {tuple(w['cell']): ('ladder_down' if floor_no.get(w['dest'], 0) > here else 'ladder_up')
              for w in ev['warps'] if w['dest'] in floor_no}
    holes = set(HOLES.get(side, []))
    void = (types == 0) & (coll == 0)
    top = float(height.max()) + 1
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            t, k, h = int(types[y, x]), int(coll[y, x]), float(height[y, x])
            c = dict(x=x, y=y, lab='.', floor='sand', ground=h, peak=h, level=h, material=major[y, x], kind='floor')
            if (x, y) in holes:
                # HGSS draws its hole on a void-typed cell and drops the player by script
                near = [float(height[y + dy, x + dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= x + dx < W and 0 <= y + dy < H and types[y + dy, x + dx] == 0x08]
                g = min(near) if near else h
                c.update(ground=g, peak=g, level=g, kind='hole', piece='hole')
            elif void[y, x]:
                c.update(lab='T', peak=top, void=True, kind='blocked')
            elif (x, y) in ladder:
                c.update(kind='ladder', piece=ladder[(x, y)])
            elif t == 0x6F:
                c.update(kind='exit', exit=True)
            elif t == 0x20 and not k & 0x80:
                c.update(kind='ice', ice=True, piece='ice')
            elif t == 0x08 and k == 0x06:
                # HGSS's stairs (floor with its slope bit): a two-cell flight cut into a one-row ice wall.
                # A flight as Dark Cave lays it (assemble.flights: the wall runs on unbroken), drawn with
                # FRLG Seafoam Islands' ice stairs (644), set two wide in a wall as Seafoam sets them
                c.update(lab='s', piece='stairs')
            elif k & 0x80:
                if piles[y, x] >= 40 and major[y, x] not in (FACE, TOP, RIM):
                    # HGSS's rock objects on Ice Path's floors are ice: its 2x2 clusters (d_rock01) Icefall's
                    # pillar, its single crystals (d_rock01s) Icefall's crystal or ice rock
                    c.update(boulder=True, kind='blocked', crystal=True, big=bool(big[y, x] >= 40),
                             piece='crystal' if (x * 7 + y * 13) % 10 < 7 else 'rock')
                else:
                    c.update(lab='T', kind='blocked')
            row.append(c)
        cells.append(row)
    # an up-ladder's two warp cells are one ladder: FRLG Seafoam's top half over its foot (owner review, Nov 5)
    for (x, y), nm in ladder.items():
        if nm == 'ladder_up' and ladder.get((x, y + 1)) == 'ladder_up':
            cells[y][x]['piece'] = 'ladder_top'
    # the big clusters in 2x2 blocks, read top-left first: each block is one pillar
    taken = set()
    for y in range(H - 1):
        for x in range(W - 1):
            blk = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if all(cells[b][a].get('big') and (a, b) not in taken for a, b in blk):
                for (a, b), nm in zip(blk, ('pillar_tl', 'pillar_tr', 'pillar_bl', 'pillar_br')):
                    cells[b][a]['piece'] = nm
                taken |= set(blk)
    for row in cells:                                        # a blocked floor cell stands on the floor beside it
        for c in row:
            if c.get('boulder'):
                near = [cells[c['y'] + dy][c['x'] + dx]['ground'] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= c['x'] + dx < W and 0 <= c['y'] + dy < H and cells[c['y'] + dy][c['x'] + dx]['lab'] == '.']
                if near:
                    c['ground'] = min(near)
    return cells, hcls, major

# --------------------------------------------------------------------------- Icefall's pieces
def pieces(engine, floor_tones, ice_tones, rock, wood):
    """Each Icefall piece composed (bottom, then top) and recoloured colour for colour: wood to
    HGSS's ladder wood, snow and stone to the floor or rock tones, ice to HGSS's ice tones; near
    black (the holes) kept."""
    out = {}
    snow = set()
    for mid in SNOW:
        b, _ = D.metatile_layers(engine, *ICEFALL, mid)
        snow |= {tuple(int(v) for v in p) for p in b[..., :3].reshape(-1, 3)}
    for name, mid in PIECE.items():
        b, t = D.metatile_layers(engine, *ICEFALL, mid)
        a = b.copy(); m = t[..., 3] > 0; a[m] = t[m]
        if name not in ('ice', 'stairs'):                # the snow round a piece is cut away, so it stands on the cave floor
            cut = np.array([[tuple(int(v) for v in a[yy, xx, :3]) in snow for xx in range(16)] for yy in range(16)]) & ~m
            a[cut, 3] = 0
        cols = sorted({tuple(int(v) for v in p) for p in a[a[..., 3] > 0][:, :3]}, key=lum)
        woody = [c for c in cols if c[0] - c[2] > 40]
        dark = [c for c in cols if lum(c) < 36 and c not in woody]
        rest = [c for c in cols if c not in woody and c not in dark]
        cmap = {c: c for c in dark}
        cmap.update(D.ranked(woody, wood))
        target = (ice_tones if name == 'ice' else floor_tones if name.startswith('ladder')
                  else rock[1:] if name in ('hole', 'stairs') else sorted(set(ice_tones) | set(rock[1:]), key=lum))
        cmap.update(D.ranked(rest, target))
        out[name] = (D.remap(a, cmap), t[..., 3] > 0)
    return out

# --------------------------------------------------------------------------- build
def main(phg, engine):
    land, tex0, models, chunks, meta = R.load(phg)
    floor_t = tones(tex0, 'droad01')
    ice_t = tones(tex0, 'ice_fe01b')                  # one flat colour; the ice's own tones come from HGSS's render (below)
    rock_t = tones(tex0, 'dwall_s', 'dcliff01', 'dallpeak_p')
    ICE_RAMP = ramp(rock_t)
    A.CAVE_RAMP = ICE_RAMP
    A.FLOOR_TEX = np.array(floor_t, np.uint8).reshape(1, -1, 3)
    A.WATER_TEX = np.array(ice_t, np.uint8).reshape(1, -1, 3)
    A.POND = A.pond_pieces(engine)
    out_dir = SRC / 'assemble'; out_dir.mkdir(parents=True, exist_ok=True)
    (EV / 'assemble').mkdir(parents=True, exist_ok=True)
    tex = E.cherry_textures()
    tex['water'] = np.tile(A.POND[('M', 'M')][0], (2, 2, 1))
    fr = E.frlg_pieces(engine)
    exit_names = {'chole_in', 'chole_light', 'light'}
    report = {}
    for side in P.SIDES:
        W, H = P.SIZE[side]
        A.W, A.H = E.W, E.H = W, H
        cells, hcls, major = ledger(side)
        ref = np.array(Image.open(SRC / f'hgss/{side}/hgss-render.png').convert('RGB'))
        lad = ref[np.repeat(np.repeat(np.array([[c['kind'] == 'ladder' for c in row] for row in cells]), PX, 0), PX, 1)]
        wood = sorted({tuple(int(v) for v in p) for p in lad if int(p[0]) - int(p[2]) > 30}, key=lum) or [(140, 90, 50)]
        # HGSS's ice as it renders (its texture is one flat colour; the render carries the stripes and shading)
        icem = np.repeat(np.repeat(np.array([[c['kind'] == 'ice' for c in row] for row in cells]), PX, 0), PX, 1)
        seen = Counter(tuple(int(v) for v in p) for p in ref[icem]) if icem.any() else Counter()
        ice_side = sorted((c for c, n in seen.most_common(6) if n > 40), key=lum) or ice_t
        art = pieces(engine, floor_t, ice_side, ICE_RAMP, wood)
        A.ROCK_BASE = int(np.floor(min(c['ground'] for row in cells for c in row if c['lab'] == '.') + 0.5))
        fl = A.flights(cells)
        rc = A.rock_cells(cells, fl)
        d, face, isrock = A.terraces(rc)
        fixes = A.regularise(rc, d, isrock)
        d, face, isrock = A.terraces(rc)
        E.layers = lambda _cells, _d=d, _f=face, _r=isrock: (_d, _f, _r)
        ground = A.paint_ground(np.full((H * 2, W * 2), A.G.PATH, np.int8), tex)
        # A raised floor's north edge (rock with lower floor north and floor at its own height south)
        # is a drop: HGSS shows only the floor's rim there. Dark Cave's back-slope rule would turn it
        # into a face looking south onto the raised floor, so it applies here only where the floor
        # south is really lower; the edge keeps the rock's light top, HGSS's pale lip (owner review, Nov 5)
        back = A.south_faces(rc, d, isrock)
        drops = {(x, y) for x, y in back if d[y + 1, x] >= d[y, x]}
        bottom, over, _, piece = E.rock_frlg(rc, ground, fr, tex, None, A.topped(rc, d, isrock), back - drops, ())
        comp = bottom[..., :3].copy()
        a = over[..., 3] > 0
        comp[a] = over[a, :3]
        comp, cmap = A.recolour(comp, tex)
        # Icefall's pieces over the recoloured floor: ice, holes and ladders fill their cell where no
        # rock overhangs it; crystals stand on the floor
        iced = lambda x, y: 0 <= x < W and 0 <= y < H and rc[y][x]['kind'] == 'ice'
        for row in rc:                                   # a crystal standing in the ice has ice under it
            for c in row:
                if c.get('crystal') and sum(iced(c['x'] + dx, c['y'] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2:
                    sl = np.s_[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                    img, _ = art['ice']
                    comp[sl][~a[sl]] = img[~a[sl]][:, :3]
        for row in rc:
            for c in row:
                if not c.get('piece'):
                    continue
                img, top_mask = art[c['piece']]
                sl = np.s_[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX]
                free = ~a[sl] if c['piece'] != 'stairs' else np.ones((PX, PX), bool)   # a flight replaces the wall it cuts
                m = (img[..., 3] > 0) & free
                comp[sl][m] = img[m, :3]
        m = np.load(SRC / f'hgss/{side}/hgss-ground-materials.npz')
        names = [str(v) for v in m['names']]
        ex = np.isin(m['material'], [names.index(n) for n in exit_names if n in names])
        comp[ex] = ref[ex]
        cls = np.full((H * PX, W * PX), FLOOR, np.int16)
        cls[a] = FACE
        for row in rc:
            for c in row:
                if c.get('piece') == 'stairs':
                    cls[c['y'] * PX:(c['y'] + 1) * PX, c['x'] * PX:(c['x'] + 1) * PX] = STAIRS
        cls[ex] = EXIT
        Image.fromarray(comp).save(out_dir / f'{side}.png')
        np.save(out_dir / f'{side}-class.npy', cls.astype(np.int8))
        (out_dir / f'{side}-ledger.json').write_text(json.dumps(dict(cells=[
            dict(x=c['x'], y=c['y'], kind=c['kind'], lab=c['lab'], piece=c.get('piece'), void=bool(c.get('void')))
            for row in rc for c in row])) + '\n')
        (out_dir / f'{side}-terrace-grid.txt').write_text(
            f'# Ice Path {side}: one line per cell row. Ground: its terrace level (0-9); rock: a letter (A = level 0 ...);\n'
            f'# ice ~, ladders H, exits E, holes O, ice crystals *, void #. Decoded from HGSS land_data (assemble.ledger).\n' +
            ''.join(f'{y:02d}  ' + ''.join(
                '#' if c.get('void') else 'H' if c['kind'] == 'ladder' else 'E' if c['kind'] == 'exit' else 'O' if c['kind'] == 'hole'
                else '*' if c.get('crystal') else '~' if c['kind'] == 'ice' else chr(65 + d[y, x]) if isrock[y, x] else str(min(9, d[y, x]))
                for x, c in enumerate(cells[y])) + '\n' for y in range(H)))
        both = Image.new('RGB', (W * 32 + 12, H * 16), (24, 26, 30))
        both.paste(Image.fromarray(ref), (0, 0)); both.paste(Image.fromarray(comp), (W * 16 + 12, 0))
        both.save(EV / f'assemble/{side}-before-after.png')
        report[side] = dict(flights=len(fl), rock_cells=int(isrock.sum()), regularised={k: len(v) for k, v in fixes.items()},
                            kinds=dict(Counter(c['kind'] for row in rc for c in row)), crystals=sum(bool(c.get('crystal')) for row in rc for c in row))
        print(side, report[side])
    (EV / 'assemble/report.json').write_text(json.dumps(dict(ice_ramp=ICE_RAMP, floor_tones=floor_t, ice_tones=ice_t, floors=report), indent=1) + '\n')
    return report

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
