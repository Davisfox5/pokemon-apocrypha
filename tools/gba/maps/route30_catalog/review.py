"""Route 30 / Route 31 review evidence: numbered HGSS/native sheets, the material audit, the gameplay gallery
(Route 29's review.py, for either route).

    python3 tools/gba/maps/route30_catalog/review.py 30|31 ENGINE_CHECKOUT RUNTIME_OUT PORYMAP_OUT

Writes gba/art/route3N-catalog/evidence/review/:
  whole.png            HGSS (decoded, rendered 1:1) beside the installed native map, same cells
  sheet-N-*.png        sections, HGSS left and native right, cell grid and coordinates on both
  material-audit.json  every HGSS cell: decoded label against what the native cell holds and does
  gameplay.png         every headless capture, labelled
  porymap.json         Porymap 6.3.1 export (route29_catalog/porymap_probe.cpp) versus the native decode
  hashes.json          map, tileset and ROM identities
  runtime-summary.json phases and frame parity
"""
from __future__ import annotations
import hashlib, json, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROUTE = sys.argv[1] if __name__ == '__main__' else '30'
HERE = Path(__file__).resolve().parent
DIR = HERE if ROUTE == '30' else HERE.parent / 'route31_catalog'
sys.path.insert(0, str(DIR)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                                       # noqa: E402
from reference import W, H, PX, COL0, ROW0, HW, HH           # noqa: E402
from tiles import Tileset                                    # noqa: E402

ART = Rf.ART
OUT = ART / 'evidence/review'
MAP = dict(name='CherrygroveRoute30Approach', ts='route30_hgss', pri='cherrygrove_route30') if ROUTE == '30' else \
      dict(name='JohtoRoute31', ts='route31_hgss', pri='cherrygrove_route31')
NEIGHBOURS = [('CherrygroveRoute30Approach', 'route30_hgss', 'cherrygrove_route30', 37), ('JohtoRoute31', 'route31_hgss', 'cherrygrove_route31', 64),
              ('CherrygroveCity', 'cherrygrove', 'cherrygrove', 80)]
# HGSS label -> native codes it may become, the native foot, and the art the cell must hold (any one of;
# art drawn over a cell counts: a roof over the woods behind a house, Mr. Pokemon's mailbox in his house art).
EXPECT = {'F': ('tko', 'blocked', ('tree', 'house')), 'G': ('G', 'open', 'tall_grass'), '~': ('~', 'water', None),
          'L': ('L', 'ledge_south', 'ledge'), 'E': ('E', 'ledge_east', 'ledge'), 'Q': ('Q', 'ledge_west', 'ledge'),
          'J': ('J', 'blocked', None), '^': ('^', 'open', None), 's': ('s', 'blocked', ('sign', 'house', 'mailbox')), 'R': ('R', 'blocked', None),
          'X': ('XR', 'blocked', None), 'H': ('H', 'blocked', ('house', 'fence')), 'D': ('D', 'blocked', 'house'), 'n': ('n', 'blocked', 'fence'),
          'B': ('B', 'blocked', 'gate'), 'W': ('W', 'open', 'gate'), 'V': ('V', 'open', None), 'C': ('C', 'blocked', None),
          '.': ('gdflc', 'open', None)}
# Declared: HGSS's Route 31 gatehouse base reaches row 16; G02 is seven rows (9-15, its stairs on HGSS's two
# gate warps), so row 16 under the base is lawn and stays solid as HGSS's footprint.
DECLARED = {'31': {(x, 16): 'gatehouse base row: lawn, solid as HGSS' for x in range(6)}}.get(ROUTE, {})

def hgss_in_frame():
    ref = np.array(Image.open(ART / 'source/hgss/hgss-render.png').convert('RGB'))
    out = np.full((H * PX, W * PX, 3), 24, np.uint8)
    out[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX] = ref
    return out

def sheet(a, b, x0, y0, x1, y1, title):
    pa = Rf.numbered(a, x0, y0, x1, y1, 2, title='HGSS (decoded land_data, 1:1)')
    pb = Rf.numbered(b, x0, y0, x1, y1, 2, title=f'native Route {ROUTE} (installed)')
    out = Image.new('RGB', (pa.width + pb.width + 12, max(pa.height, pb.height) + 22), (24, 26, 30))
    out.paste(pa, (0, 22)); out.paste(pb, (pa.width + 12, 22))
    ImageDraw.Draw(out).text((4, 4), title, fill='white')
    return out

def audit():
    trav = {(c['x'], c['y']): c for c in json.loads((ART / 'source/pack/traversal.json').read_text())}
    cells = json.loads((ART / 'source/trace/ledger.json').read_text())['cells']
    z = np.load(ART / 'source/assemble/layers.npz', allow_pickle=True)
    owner, flat_owner = z['owner'].astype(str), z['flat_owner'].astype(str)
    rows, counts = [], Counter()
    for hz in range(HH):
        for hx in range(HW):
            x, y = Rf.to_map(hx, hz)
            c, t = cells[hz][hx], trav[(x, y)]
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            art = {o.rstrip('0123456789_').split('_')[0] if not o.endswith('house') else 'house' for o in set(owner[sl].ravel().tolist()) - {''}}
            art |= set(flat_owner[sl].ravel().tolist()) - {''}
            codes, foot, need = EXPECT[c['lab']]
            ok = t['code'] in codes and t['foot'] == foot and (need is None or bool(set((need,) if isinstance(need, str) else need) & art))
            if c['lab'] == '.' and c['blocked']:
                ok = t['foot'] == 'blocked'
            if not ok and (x, y) in DECLARED and t['code'] in codes and t['foot'] == foot:
                counts['declared: ' + DECLARED[(x, y)]] += 1
                continue
            counts[('match' if ok else 'MISMATCH') + ': ' + c['lab']] += 1
            if not ok:
                rows.append(dict(hgss=[hx, hz], native=[x, y], label=c['lab'], native_code=t['code'], native_foot=t['foot'],
                                 native_behavior=t.get('behavior'), art=sorted(art)))
    adapt = Counter(t['adaptation'].split(';')[0] for t in trav.values() if 'adaptation' in t)
    return dict(cells=HW * HH, summary=dict(sorted(counts.items())), mismatches=rows, declared_adaptations=dict(adapt))

def gallery(run):
    shots = [json.loads(l) for l in (run / 'write.jsonl').read_text().splitlines() if l.startswith('{') and '"shot"' in l]
    names = [s['shot'] for s in shots] + ['cold-reload', 'continue-menu', 'title-continue']
    files = [run / f'{n}.png' for n in dict.fromkeys(names) if (run / f'{n}.png').exists()]
    cols, tw, th = 6, 240, 174
    out = Image.new('RGB', (cols * (tw + 4), ((len(files) + cols - 1) // cols) * (th + 4)), (24, 24, 28)); d = ImageDraw.Draw(out)
    for i, f in enumerate(files):
        x, y = (i % cols) * (tw + 4), (i // cols) * (th + 4)
        out.paste(Image.open(f).convert('RGB'), (x, y + 14)); d.text((x + 2, y + 1), f.stem[:40], fill='white')
    out.save(OUT / 'gameplay.png')
    return len(files)

def main(engine, run, pory):
    OUT.mkdir(parents=True, exist_ok=True)
    a = hgss_in_frame()
    b = np.array(Image.open(ART / 'evidence/pack/native.png').convert('RGB'))
    side = W < H                                         # a tall map goes side by side, a wide one stacked
    size = (2 * W * PX + 40, H * PX + 40) if side else (W * PX + 16, 2 * H * PX + 60)
    whole = Image.new('RGB', size, (24, 26, 30)); d = ImageDraw.Draw(whole)
    d.text((4, 4), f'HGSS Route {ROUTE}, decoded and rendered 1:1 (native cell = HGSS cell + ({COL0}, {ROW0}))', fill='white')
    whole.paste(Image.fromarray(a), (8, 20))
    pos = (W * PX + 32, 20) if side else (8, H * PX + 46)
    d.text((pos[0], pos[1] - 16 if not side else H * PX + 24), f'native Route {ROUTE} as installed', fill='white')
    whole.paste(Image.fromarray(b), pos)
    whole.resize((whole.width // 2, whole.height // 2), Image.Resampling.LANCZOS).save(OUT / 'whole.png')
    for i, (x0, y0, x1, y1) in enumerate(Rf.SHEETS, 1):
        sheet(a, b, x0, y0, x1, y1, f'Route {ROUTE} cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}: HGSS left, native right').save(OUT / f'sheet-{i}-x{x0}-{x1 - 1}-y{y0}-{y1 - 1}.png')
    au = audit()
    (OUT / 'material-audit.json').write_text(json.dumps(au, indent=1) + '\n')
    n = gallery(run)
    res = json.loads((run / 'results.json').read_text())
    pm = {}
    for name, sec, pri, w in NEIGHBOURS:
        bb = (engine / f'data/layouts/{name}/map.bin').read_bytes()
        nimg = np.array(Tileset(engine, sec, pri).map_image(list(struct.unpack('<%dH' % (len(bb) // 2), bb)), w).convert('RGB')).astype(int) >> 3
        p = np.array(Image.open(pory / f'{name}.png').convert('RGB')).astype(int) >> 3
        pm[name] = dict(size=list(p.shape[:2][::-1]), differing_pixels=int((p != nimg).any(-1).sum()) if p.shape == nimg.shape else 'size differs')
    (OUT / 'porymap.json').write_text(json.dumps(dict(porymap='6.3.1', method="Porymap's own Project::loadMap and Layout::render "
                                                       "(tools/gba/maps/route29_catalog/porymap_probe.cpp), compared in RGB555", maps=pm), indent=1) + '\n')
    files = [engine / f'data/layouts/{MAP["name"]}/map.bin', engine / f'data/maps/{MAP["name"]}/map.json', engine / 'data/layouts/layouts.json'] + \
            sorted((engine / f'data/tilesets/secondary/{MAP["ts"]}').rglob('*.*')) + sorted((engine / f'data/tilesets/primary/{MAP["pri"]}').rglob('*.*')) + \
            [engine / 'pokeemerald.gba', engine / 'pokeemerald.elf']
    hashes = {str(f.relative_to(engine)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.exists()}
    (OUT / 'hashes.json').write_text(json.dumps(hashes, indent=1) + '\n')
    parity = {p['phase']: dict(frames=len(p['parity']['frames']),
                               fully_identical=sum(f['identical'] >= 0.9999 for f in p['parity']['frames']),
                               below_99_5=[(f['shot'], f['identical']) for f in p['parity']['frames'] if f['identical'] < 0.995]) for p in res}
    (OUT / 'runtime-summary.json').write_text(json.dumps(dict(phases=[dict(phase=p['phase'], exit=p['exit_code'], observations=p['observations']) for p in res],
                                                             frame_parity=parity), indent=1) + '\n')
    print(json.dumps(dict(audit=au['summary'], mismatches=len(au['mismatches']), gallery=n, porymap=pm, parity=parity), indent=1))

if __name__ == '__main__':
    main(*(Path(a).resolve() for a in sys.argv[2:5]))
