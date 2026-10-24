"""Route 29 review evidence: numbered HGSS/native sheets, the material audit, the gameplay gallery.

    python3 tools/gba/maps/route29_catalog/review.py ENGINE_CHECKOUT RUNTIME_OUT PORYMAP_OUT

Writes gba/art/route29-catalog/evidence/review/:
  whole.png            HGSS (decoded, rendered 1:1) above the installed native map, same cells, numbered
  sheet-N-*.png        four sections, HGSS left and native right, cell grid and coordinates on both
  material-audit.json  every HGSS cell: decoded material against what the native cell holds
  gameplay.png         every headless capture, labelled
  porymap.json         Porymap 6.3.1 export versus the native decode
  hashes.json          source, tileset and ROM identities
"""
from __future__ import annotations
import hashlib, json, struct, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                                       # noqa: E402
from reference import W, H, PX, COL0, ROW0, HW, HH, COAST_ROW  # noqa: E402
from tiles import Tileset                                    # noqa: E402

ART = Rf.ART
OUT = ART / 'evidence/review'

def hgss_in_frame():
    """The decoded HGSS render placed in the native frame (padding and coast left dark)."""
    ref = np.array(Image.open(ART / 'source/hgss/hgss-render.png').convert('RGB'))
    out = np.full((H * PX, W * PX, 3), 24, np.uint8)
    out[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX] = ref
    return out

def sheet(a, b, x0, y0, x1, y1, title):
    s = 2
    pa = Rf.numbered(a, x0, y0, x1, y1, s, title='HGSS (decoded land_data, 1:1)')
    pb = Rf.numbered(b, x0, y0, x1, y1, s, title='native Route 29 (installed)')
    out = Image.new('RGB', (pa.width + pb.width + 12, pa.height + 22), (24, 26, 30))
    out.paste(pa, (0, 22)); out.paste(pb, (pa.width + 12, 22))
    ImageDraw.Draw(out).text((4, 4), title, fill='white')
    return out

def audit(engine):
    trav = {(c['x'], c['y']): c for c in json.loads((ART / 'source/pack/traversal.json').read_text())}
    cells = json.loads((ART / 'source/trace/ledger.json').read_text())['cells']
    z = np.load(ART / 'source/assemble/layers.npz', allow_pickle=True)
    owner, flat_owner = z['owner'].astype(str), z['flat_owner'].astype(str)
    rows, counts = [], Counter()
    for hz in range(HH):
        for hx in range(HW):
            x, y = Rf.to_map(hx, hz)
            if y >= COAST_ROW:
                counts['coast (declared: replaces HGSS forest border rows 29-31)'] += 1
                continue
            c, t = cells[hz][hx], trav[(x, y)]
            sl = np.s_[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX]
            own = set(owner[sl].ravel().tolist()) - {''}
            fl = set(flat_owner[sl].ravel().tolist()) - {''}
            lab = c['lab']
            if lab == 'F':
                tree = any(o.startswith('tree') for o in own)
                ok = tree and (t['foot'] == 'blocked' or 'adaptation' in t)
                why = 'woods: tree art' + ('' if t['foot'] == 'blocked' else ', open under a crown (declared)')
            elif lab == 'G':
                ok = t.get('behavior') == 'MB_TALL_GRASS' and 'tall_grass' in fl
                why = 'tall grass: G15 and MB_TALL_GRASS'
            elif lab in 'LQE':
                want = {'L': 'MB_JUMP_SOUTH', 'Q': 'MB_JUMP_WEST', 'E': 'MB_JUMP_EAST'}[lab]
                ok = t.get('behavior') == want and 'ledge' in fl
                why = f'ledge: art and {want}'
            elif lab in 'JX':
                ok = t['foot'] == 'blocked'
                why = 'blocked corner / prop'
            elif c['type'] == 0x6E:
                ok = t['foot'] == 'blocked' and any(o.startswith('gate') for o in own)
                why = 'gatehouse doorway (declared: shut, no interior)'
            else:
                ok = t['foot'] == 'open' and not t.get('code') == 't'
                why = 'open ground: ' + ('road' if c['floor'] == 'sand' else 'lawn') + (' with flowers' if 'flowers' in fl else '') + (' light patch' if 'light_lawn' in fl else '')
                if c['blocked']:
                    ok = t['foot'] == 'blocked'
                    why = 'blocked in HGSS (sign or model)'
            counts[('match' if ok else 'MISMATCH') + ': ' + why.split(':')[0]] += 1
            if not ok:
                rows.append(dict(hgss=[hx, hz], native=[x, y], label=lab, native_foot=t['foot'], native_behavior=t.get('behavior'),
                                 objects=sorted(own), details=sorted(fl)))
    adapt = Counter(t['adaptation'].split(';')[0] for t in trav.values() if 'adaptation' in t)
    return dict(cells=HW * HH, summary=dict(counts), mismatches=rows, declared_adaptations=dict(adapt))

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
    whole = Image.new('RGB', (W * PX + 16, 2 * H * PX + 60), (24, 26, 30)); d = ImageDraw.Draw(whole)
    d.text((4, 4), 'HGSS Route 29, decoded and rendered 1:1, in the native frame (HGSS cell = native cell - (4, 3))', fill='white')
    whole.paste(Image.fromarray(a), (8, 20))
    d.text((4, H * PX + 30), 'native Route 29 as installed (rows 32-50: the accepted Cherrygrove coast)', fill='white')
    whole.paste(Image.fromarray(b), (8, H * PX + 46))
    whole.resize((whole.width // 2, whole.height // 2), Image.Resampling.LANCZOS).save(OUT / 'whole.png')
    for i, (x0, y0, x1, y1) in enumerate(Rf.SHEETS, 1):
        sheet(a, b, x0, y0, x1, y1, f'Route 29 cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}: HGSS left, native right').save(OUT / f'sheet-{i}-x{x0}-{x1 - 1}.png')
    au = audit(engine)
    (OUT / 'material-audit.json').write_text(json.dumps(au, indent=1) + '\n')
    n = gallery(run)
    res = json.loads((run / 'results.json').read_text())
    def native_img(layout, sec, w):
        bb = (engine / f'data/layouts/{layout}/map.bin').read_bytes()
        return np.array(Tileset(engine, sec, 'cherrygrove').map_image(list(struct.unpack('<%dH' % (len(bb) // 2), bb)), w).convert('RGB'))
    pm = {}
    for name, sec, w in (('CherrygroveRoute29Approach', 'route29_hgss', W), ('CherrygroveCity', 'cherrygrove', 80), ('NewBarkTown', 'new_bark', 36)):
        p = np.array(Image.open(pory / f'{name}.png').convert('RGB')).astype(int) >> 3
        nimg = native_img(name, sec, w).astype(int) >> 3
        pm[name] = dict(size=list(p.shape[:2][::-1]), differing_pixels=int((p != nimg).any(-1).sum()) if p.shape == nimg.shape else 'size differs')
    (OUT / 'porymap.json').write_text(json.dumps(dict(porymap='6.3.1', method="Porymap's own Project::loadMap and Layout::render "
                                                       "(tools/gba/maps/route29_catalog/porymap_probe.cpp), compared in RGB555", maps=pm), indent=1) + '\n')
    files = [engine / 'data/layouts/CherrygroveRoute29Approach/map.bin', engine / 'data/maps/CherrygroveRoute29Approach/map.json',
             engine / 'data/layouts/layouts.json'] + sorted((engine / 'data/tilesets/secondary/route29_hgss').rglob('*.*')) + \
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
    main(*(Path(a).resolve() for a in sys.argv[1:4]))
