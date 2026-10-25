"""The Johto stair pieces Routes 30 and 31 reuse, lifted pixel for pixel from the maps they were built for.

    python3 tools/gba/maps/route30_catalog/stair_pieces.py ENGINE_REPO

North-south flights take the earlier Route 30's grey treads (engine 4f01430776, the revision the editor
library's route30 package records; its "04 Stairs | middle" prefab, CherrygroveRoute30Approach (9..11, 28)):
a left end, a middle and a right end, one 16 px row per tread row, as Route 32's flight (codex/route32-hgss-blocks)
and the earlier Route 31's south flight draw them. East-west flights take Route 36's plank flight through
a one-column wall (engine 1643f58a48, the editor library's latest package, "04 Stairs | East-west flight 1",
JohtoRoute36 (14, 21..23)): the top cell with its dark rock cheek, the plank cell, and the bottom cell with
its brown cheek.

Writes gba/art/route30-catalog/source/shared-art/stairs/*.png and provenance.json (Route 31 reads them from
there).
"""
from __future__ import annotations
import hashlib, json, re, shutil, struct, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'gba/art/route30-catalog/source/shared-art/stairs'
SOURCES = {
    'ns-left': ('4f01430776', 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', (9, 28)),
    'ns-mid': ('4f01430776', 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', (10, 28)),
    'ns-right': ('4f01430776', 'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH', (11, 28)),
    'ew-top': ('1643f58a48', 'LAYOUT_JOHTO_ROUTE36', (14, 21)),
    'ew-mid': ('1643f58a48', 'LAYOUT_JOHTO_ROUTE36', (14, 22)),
    'ew-bottom': ('1643f58a48', 'LAYOUT_JOHTO_ROUTE36', (14, 23)),
}

def render(eng, layout_id):
    L = {l['id']: l for l in json.loads((eng / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}[layout_id]
    g = (eng / 'src/data/tilesets/graphics.h').read_text()
    name = {m.group(1): m.group(2) for m in re.finditer(r'gTilesetTiles_(\w+)\[\] = INCGFX_U32\("data/tilesets/\w+/(\w+)/tiles\.png"', g)}
    b = (eng / L['blockdata_filepath']).read_bytes()
    words = list(struct.unpack('<%dH' % (len(b) // 2), b))
    t = Tileset(eng, name[L['secondary_tileset'][9:]], name[L['primary_tileset'][9:]])
    return np.array(t.map_image(words, L['width']).convert('RGB')), np.array(words).reshape(L['height'], L['width'])

def main(repo):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='stair-src-'))
    prov, cache = {}, {}
    try:
        for name, (rev, layout, (x, y)) in SOURCES.items():
            if (rev, layout) not in cache:
                wt = tmp / rev
                if not wt.exists():
                    subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '-q', '--detach', str(wt), rev], check=True)
                cache[(rev, layout)] = render(wt, layout)
            img, words = cache[(rev, layout)]
            piece = img[y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
            f = OUT / f'{name}.png'
            Image.fromarray(piece).save(f)
            v = int(words[y, x])
            prov[name] = dict(engine_revision=rev, layout=layout, cell=[x, y], metatile=v & 1023, collision=(v >> 10) & 3,
                              elevation=v >> 12, sha256=hashlib.sha256(f.read_bytes()).hexdigest())
    finally:
        for wt in tmp.iterdir():
            subprocess.run(['git', '-C', str(repo), 'worktree', 'remove', '--force', str(wt)], check=False)
        shutil.rmtree(tmp, ignore_errors=True)
    (OUT / 'provenance.json').write_text(json.dumps(dict(
        note='Native 16x16 renders of the cells named, from the engine revisions named (editor library packages route30 and latest).',
        pieces=prov), indent=1) + '\n')
    print(json.dumps(prov, indent=1))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
