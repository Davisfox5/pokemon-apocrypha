"""Build Violet's interiors: compose each room (rooms.py), pack each building's rooms into its own tileset
pair (ipack.py), and install layouts, maps and warps into the engine.

    python3 tools/gba/maps/violet_interiors/build.py ENGINE [--preview] [ROOM ...]
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'route30_catalog'), str(HERE.parent / 'violet_city')]
import ipack as IP                       # noqa: E402
import rooms as RS                       # noqa: E402
from tiles import Tileset                # noqa: E402

ART = ROOT / 'gba/art/violet-interiors'
WALK, BLOCK = 0x3000, 0x3400             # elevation 3; collision 0 / 1
MB = dict(normal=0x00, exit=0x65, ladder=0x61, bookshelf=0xE1, pc=0x83, tv=0x86, counter=0x80,
          escalator_up=0x6A, escalator_down=0x6B)

def cells(room):
    """The room's native cells: layers, behaviour, collision. Outside the room: black and blocked."""
    low, up = room.layers()
    out = []
    for y in range(room.H):
        for x in range(room.W):
            sl = np.s_[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
            if not room.inside(x, y):
                out.append(IP.Cell(np.zeros((16, 16, 3), np.uint8), np.zeros((16, 16, 4), np.uint8), 0, BLOCK))
                continue
            name = room.behaviors.get((x, y))
            beh = MB[name] if name else (getattr(room, 'beh', {}).get((x, y), 0) & 0xFF)   # native pieces keep their own
            out.append(IP.Cell(low[sl], up[sl], beh, BLOCK if room.blocked[y, x] else WALK))
    return out

def register(engine, prim, sec, psym, ssym):
    import pair_pack as PP
    PP.register(engine, psym, prim, primary=True)
    PP.register(engine, ssym, sec, primary=False)

def layout(engine, lid, folder, W, H, words, psym, ssym, black):
    d = engine / 'data/layouts' / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / 'map.bin').write_bytes(struct.pack('<%dH' % words.size, *[int(w) for w in words.ravel()]))
    (d / 'border.bin').write_bytes(struct.pack('<4H', *[black] * 4))
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    entry = dict(id=lid, name=f'{folder}_Layout', width=W, height=H, primary_tileset=f'gTileset_{psym}',
                 secondary_tileset=f'gTileset_{ssym}', border_filepath=f'data/layouts/{folder}/border.bin',
                 blockdata_filepath=f'data/layouts/{folder}/map.bin', layout_version='emerald')
    L['layouts'] = [l for l in L['layouts'] if l.get('id') != lid] + [entry]
    lj.write_text(json.dumps(L, indent=2) + '\n')

def build(engine, names, preview):
    report = {}
    for group, spec in RS.GROUPS.items():
        rooms = {n: RS.ROOMS[n]() for n in spec['rooms'] if not names or n in names or group in names}
        if not rooms:
            continue
        log = []
        groups = {n: (r.W, r.H, cells(r)) for n, r in rooms.items()}
        out = ART / 'evidence'; out.mkdir(parents=True, exist_ok=True)
        for n, r in rooms.items():
            Image.fromarray(np.where(np.repeat(np.repeat(np.array([[r.inside(x, y) for x in range(r.W)] for y in range(r.H)]), 16, 0), 16, 1)[..., None],
                                     r.image(), 0).astype(np.uint8)).save(out / f'{n}-composed.png')
        if preview:
            continue
        pk = IP.pack(groups, log)
        IP.write(engine, spec['primary'], spec['secondary'], pk)
        register(engine, spec['primary'], spec['secondary'], spec['psym'], spec['ssym'])
        t = Tileset(engine, spec['secondary'], spec['primary'])
        for n, r in rooms.items():
            m = RS.MAPS[n]
            img = r.image()
            black = lambda x, y: not img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16].any()
            out_cells = [(x, y) for y in range(r.H) for x in range(r.W) if not r.inside(x, y) or black(x, y)]
            assert out_cells, ('no black cell for the border', n)
            bx, by = out_cells[0]
            layout(engine, m['layout'], m['folder'], r.W, r.H, pk['words'][n], spec['psym'], spec['ssym'], int(pk['words'][n][by, bx]))
            got = np.array(t.map_image([int(w) & 1023 for w in pk['words'][n].ravel()], r.W).convert('RGB'))
            Image.fromarray(got).save(out / f'{n}-installed.png')
            want = np.array(Image.open(out / f'{n}-composed.png').convert('RGB'))
            report[n] = dict(size=[r.W, r.H], px_changed_by_palette=int(((got >> 3) != (want >> 3)).any(-1).sum()), notes=r.notes)
        report[group] = dict(log=log, tiles=len(pk['tiles']), metatiles=len(pk['metas']))
    if not preview:
        RS.install_maps(engine, [n for g in RS.GROUPS.values() for n in g["rooms"] if not names or n in names or any(n in GG["rooms"] for k, GG in RS.GROUPS.items() if k in names)])
    (ART / 'evidence').mkdir(parents=True, exist_ok=True)
    if not preview:
        f = ART / 'evidence/build.json'
        old = json.loads(f.read_text()) if f.exists() else {}
        old.update(report)
        f.write_text(json.dumps(old, indent=1) + '\n')
    print(json.dumps(report, indent=1))
    return report

if __name__ == '__main__':
    args = sys.argv[2:]
    build(Path(sys.argv[1]), [a for a in args if not a.startswith('--')], '--preview' in args)
