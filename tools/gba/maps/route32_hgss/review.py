"""Route 32 (HGSS textures) review evidence: numbered HGSS/native sheets, the material and traversal audit,
the rock/stair audit, the gameplay gallery, the Porymap comparison and hashes.

    python3 tools/gba/maps/route32_hgss/review.py ENGINE RUNTIME_OUT PORYMAP_OUT

Writes gba/art/route32-hgss/evidence/review/:
  whole.png            HGSS (decoded land_data, rendered 1:1) beside the installed native route (both maps)
  sheet-N-*.png        HGSS left, native right, cell grid and native coordinates on both
  seam.png             the rows either side of the JohtoRoute32 / JohtoRoute32South seam, native
  material-audit.json  every HGSS cell: decoded label against the native cell's foot and behaviour, and the
                       native pixels against the composed HGSS art (Lab error per cell)
  rock-stair-audit.json  every rock, ledge and stair cell: decoded slope direction, native foot, pixel error
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                                       # noqa: E402
from reference import W, H, PX, COL0, ROW0, HW, HH           # noqa: E402
from tiles import Tileset                                    # noqa: E402
from pack import MAPS, SPLIT, lab                            # noqa: E402

ART = Rf.ART
OUT = ART / 'evidence/review'
# HGSS label -> native foot it must have (decoded permissions)
FOOT = {'F': 'blocked', 'G': 'open', '~': 'water', 'L': 'ledge_south', 'E': 'ledge_east', 'Q': 'ledge_west', 'J': 'blocked',
        '^': 'open', 's': 'blocked', 'R': 'blocked', 'X': 'blocked', 'H': 'blocked', 'D': 'door', 'B': 'open', 'O': 'blocked',
        'C': 'blocked', 'w': 'blocked', '.': 'open'}
DECLARED = {'w': "gatehouse doorway shut: no Ruins of Alph gatehouse interior on this branch",
            'C': "Union Cave mouth shut: no Union Cave on this branch"}

def hgss_in_frame():
    ref = np.array(Image.open(ART / 'source/hgss/hgss-render.png').convert('RGB'))
    out = np.full((H * PX, W * PX, 3), 24, np.uint8)
    out[ROW0 * PX:ROW0 * PX + HH * PX, COL0 * PX:COL0 * PX + HW * PX] = ref
    return out

def sheet(a, b, x0, y0, x1, y1, title):
    pa = Rf.numbered(a, x0, y0, x1, y1, 2, title='HGSS (decoded land_data, 1:1)')
    pb = Rf.numbered(b, x0, y0, x1, y1, 2, title='native Route 32 (installed; rows >= %d are JohtoRoute32South, its row = native - %d)' % (SPLIT, SPLIT))
    out = Image.new('RGB', (pa.width + pb.width + 12, max(pa.height, pb.height) + 22), (24, 26, 30))
    out.paste(pa, (0, 22)); out.paste(pb, (pa.width + 12, 22))
    ImageDraw.Draw(out).text((4, 4), title, fill='white')
    return out

def audit(native, art):
    trav = {(c['x'], c['y']): c for c in json.loads((ART / 'source/pack/traversal.json').read_text())}
    cells = json.loads((ART / 'source/trace/ledger.json').read_text())['cells']
    d = np.sqrt(((lab(native.reshape(-1, 3).astype(float)) - lab(art.reshape(-1, 3).astype(float))) ** 2).sum(-1)).reshape(H * PX, W * PX)
    per = d.reshape(H, PX, W, PX).transpose(0, 2, 1, 3).reshape(H, W, -1)
    mean, worst = per.mean(-1), per.max(-1)
    rows, counts, art_err = [], Counter(), Counter()
    for hz in range(HH):
        for hx in range(HW):
            x, y = Rf.to_map(hx, hz)
            c, t = cells[hz][hx], trav[(x, y)]
            lab_ = c['lab']
            want = 'blocked' if (lab_ == '.' and c['blocked']) else FOOT[lab_]
            if lab_ in DECLARED and t['foot'] == 'blocked':
                counts['declared: ' + DECLARED[lab_]] += 1
            elif t['foot'] == want:
                counts['match: ' + lab_] += 1
            else:
                counts['MISMATCH: ' + lab_] += 1
                rows.append(dict(hgss=[hx, hz], native=[x, y], label=lab_, native_foot=t['foot'], native_behavior=t.get('behavior')))
            m = mean[y, x]
            art_err['<1' if m < 1 else '1-3' if m < 3 else '3-6' if m < 6 else '>=6'] += 1
    flagged = sorted(([int(x), int(y), round(float(mean[y, x]), 2), round(float(worst[y, x]), 1)]
                      for y in range(H) for x in range(W) if mean[y, x] >= 6), key=lambda r: -r[2])
    return dict(cells=HW * HH, traversal=dict(sorted(counts.items())), traversal_mismatches=rows,
                native_vs_hgss_art=dict(mean_lab_per_cell=dict(sorted(art_err.items())), cells_mean_6_or_more=flagged,
                                        note='Lab distance between the installed native pixels and the composed HGSS-texture art; '
                                             'the difference is palette reduction and logged tile merges (source/pack/merges.json).'))

def rock_stairs(native, art):
    cells = json.loads((ART / 'source/trace/ledger.json').read_text())['cells']
    trav = {(c['x'], c['y']): c for c in json.loads((ART / 'source/pack/traversal.json').read_text())}
    h = np.load(ART / 'source/hgss/hgss-cell-height.npy')
    d = np.sqrt(((lab(native.reshape(-1, 3).astype(float)) - lab(art.reshape(-1, 3).astype(float))) ** 2).sum(-1)).reshape(H * PX, W * PX)
    stairs, rock = [], Counter()
    for hz in range(HH):
        for hx in range(HW):
            c = cells[hz][hx]; x, y = Rf.to_map(hx, hz)
            e = float(d[y * PX:(y + 1) * PX, x * PX:(x + 1) * PX].mean())
            if c['lab'] == '^':
                gx = (h[hz, min(hx + 1, HW - 1)] - h[hz, max(hx - 1, 0)]) / 2
                gy = (h[min(hz + 1, HH - 1), hx] - h[max(hz - 1, 0), hx]) / 2
                stairs.append(dict(native=[x, y], hgss=[hx, hz], slope_x=round(float(gx), 3), slope_y=round(float(gy), 3),
                                   axis='east-west' if abs(gx) > abs(gy) else 'north-south', native_foot=trav[(x, y)]['foot'],
                                   mean_lab=round(e, 2)))
            elif c['lab'] in 'RJLEQ':
                rock[c['lab'] + (': ' + c['face'] if c['face'] else '')] += 1
    return dict(stairs=stairs, rock_and_ledge_cells=dict(sorted(rock.items())),
                note='Stairs, rock faces, caps and ledges are drawn from HGSS\'s own render of each cell, so their direction, '
                     'height and shading are HGSS\'s; the slope is the decoded mesh height gradient across the cell.')

def gallery(run):
    shots = [json.loads(l) for l in (run / 'write.jsonl').read_text().splitlines() if l.startswith('{') and '"shot"' in l]
    names = [s['shot'] for s in shots] + ['cold-reload', 'continue-menu', 'title-continue']
    files = [run / f'{n}.png' for n in dict.fromkeys(names) if (run / f'{n}.png').exists()]
    cols, tw, th = 6, 240, 174
    out = Image.new('RGB', (cols * (tw + 4), ((len(files) + cols - 1) // cols) * (th + 4)), (24, 24, 28)); dr = ImageDraw.Draw(out)
    for i, f in enumerate(files):
        x, y = (i % cols) * (tw + 4), (i // cols) * (th + 4)
        out.paste(Image.open(f).convert('RGB'), (x, y + 14)); dr.text((x + 2, y + 1), f.stem[:40], fill='white')
    out.save(OUT / 'gameplay.png')
    return len(files)

def main(engine, run, pory):
    OUT.mkdir(parents=True, exist_ok=True)
    a = hgss_in_frame()
    b = np.array(Image.open(ART / 'evidence/pack/native.png').convert('RGB'))
    comp = np.array(Image.open(ART / 'evidence/compose/native-art.png').convert('RGB')) >> 3 << 3
    whole = Image.new('RGB', (2 * W * PX + 40, H * PX + 40), (24, 26, 30)); dr = ImageDraw.Draw(whole)
    dr.text((4, 4), f'HGSS Route 32, decoded and rendered 1:1 (native cell = HGSS cell + ({COL0}, {ROW0}))', fill='white')
    whole.paste(Image.fromarray(a), (8, 20))
    dr.text((W * PX + 32, 4), f'native Route 32 as installed (JohtoRoute32 rows 0-{SPLIT - 1}, JohtoRoute32South below)', fill='white')
    whole.paste(Image.fromarray(b), (W * PX + 32, 20))
    whole.save(OUT / 'whole.png')
    for f in OUT.glob('sheet-*.png'):
        f.unlink()
    for i, (x0, y0, x1, y1) in enumerate(Rf.SHEETS, 1):
        sheet(a, b, x0, y0, x1, y1, f'Route 32 cells x{x0}-{x1 - 1}, y{y0}-{y1 - 1}: HGSS left, native right').save(
            OUT / f'sheet-{i}-x{x0}-{x1 - 1}-y{y0}-{y1 - 1}.png')
    sheet(a, b, 0, SPLIT - 8, W, SPLIT + 8, f'the map seam (native row {SPLIT}) under the viaduct').save(OUT / 'seam.png')
    au = audit(b, comp)
    (OUT / 'material-audit.json').write_text(json.dumps(au, indent=1) + '\n')
    rs = rock_stairs(b, comp)
    (OUT / 'rock-stair-audit.json').write_text(json.dumps(rs, indent=1) + '\n')
    n = gallery(run)
    res = json.loads((run / 'results.json').read_text())
    pm = {}
    for m, c in MAPS.items():
        bb = (engine / f'data/layouts/{c["name"]}/map.bin').read_bytes()
        nimg = np.array(Tileset(engine, c['ts'], c['ts']).map_image(list(struct.unpack('<%dH' % (len(bb) // 2), bb)), W).convert('RGB')).astype(int) >> 3
        p = np.array(Image.open(pory / f'{c["name"]}.png').convert('RGB')).astype(int) >> 3
        pm[c['name']] = dict(size=list(p.shape[:2][::-1]), differing_pixels=int((p != nimg).any(-1).sum()) if p.shape == nimg.shape else 'size differs')
    (OUT / 'porymap.json').write_text(json.dumps(dict(porymap='6.3.1', method="Porymap's own Project::loadMap and Layout::render "
                                                   "(tools/gba/maps/route29_catalog/porymap_probe.cpp), compared in RGB555", maps=pm), indent=1) + '\n')
    files = [engine / 'data/layouts/layouts.json', engine / 'pokeemerald.gba', engine / 'pokeemerald.elf']
    for c in MAPS.values():
        files += [engine / f'data/layouts/{c["name"]}/map.bin', engine / f'data/maps/{c["name"]}/map.json']
        for kind in ('primary', 'secondary'):
            files += sorted((engine / f'data/tilesets/{kind}/{c["ts"]}').rglob('*.*'))
    hashes = {str(f.relative_to(engine)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.exists()}
    (OUT / 'hashes.json').write_text(json.dumps(hashes, indent=1) + '\n')
    parity = {p['phase']: dict(frames=len(p['parity']['frames']),
                               fully_identical=sum(f['identical'] >= 0.9999 for f in p['parity']['frames']),
                               below_99_5=[(f['shot'], f['identical']) for f in p['parity']['frames'] if f['identical'] < 0.995]) for p in res}
    (OUT / 'runtime-summary.json').write_text(json.dumps(dict(phases=[dict(phase=p['phase'], exit=p['exit_code'], observations=p['observations']) for p in res],
                                                             frame_parity=parity), indent=1) + '\n')
    print(json.dumps(dict(traversal=au['traversal'], mismatches=len(au['traversal_mismatches']), art=au['native_vs_hgss_art']['mean_lab_per_cell'],
                          flagged=len(au['native_vs_hgss_art']['cells_mean_6_or_more']), stairs=rs['stairs'], gallery=n, porymap=pm,
                          parity=parity), indent=1))

if __name__ == '__main__':
    main(*[Path(a).resolve() for a in sys.argv[1:4]])
