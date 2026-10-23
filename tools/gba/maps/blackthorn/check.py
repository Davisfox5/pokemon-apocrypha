"""Prior three-section draft, kept for reference; superseded by the element build (elements.py, pack.py,
install_elements.py). Its evidence lives in evidence/sections-draft/.

Audit the installed native Blackthorn source: decoded art, traversal, reachability, preservation.

Reads only the engine's native files (map.bin, metatiles, attributes, tiles.png, palettes)
and compares them with the build ledger and the HGSS-derived composition.

    python3 tools/gba/maps/blackthorn/check.py ENGINE_CHECKOUT
"""
from __future__ import annotations
import json, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import build as B                                   # noqa: E402
from stream import tileset                           # noqa: E402

EV = B.EV
W, H = B.W, B.H

def decode_sections(g):
    """City image, behaviour, layer type and collision decoded from the native section files."""
    img = np.zeros((H * 16, W * 16, 3), np.uint8)
    beh = np.zeros((H, W), np.int32); layer = np.zeros((H, W), np.int32); coll = np.zeros((H, W), np.int32)
    elev = np.zeros((H, W), np.int32); metatile = np.zeros((H, W), np.int32)
    palettes = None
    for name, y0, y1 in B.SECTIONS:
        folder = name.lower().replace('city', '_city')
        pt, pb, pa, pp, _ = tileset(g, 'primary', folder)
        st, sb, sa, sp, _ = tileset(g, 'secondary', folder)
        pals = [B.read_pal(g / f'data/tilesets/{"primary" if i < 6 else "secondary"}/{folder}/palettes/{i:02}.pal') for i in range(16)]
        palettes = palettes or pals
        assert pals == palettes, name
        tiles = pt[:512] + [np.zeros((8, 8), np.uint8)] * (512 - len(pt[:512])) + st
        blocks = list(pb[:512]) + [None] * (512 - len(pb[:512])) + list(sb)
        attrs = list(pa[:512]) + [0] * (512 - len(pa[:512])) + list(sa)
        grid = np.frombuffer((g / f'data/layouts/{name}/map.bin').read_bytes(), '<u2').reshape(y1 - y0, W)
        for y, x in np.ndindex(grid.shape):
            v = int(grid[y, x]); mid = v & 1023; gy = y0 + y
            metatile[gy, x] = mid; coll[gy, x] = (v >> 10) & 3; elev[gy, x] = v >> 12
            beh[gy, x] = int(attrs[mid]) & 0xFF; layer[gy, x] = (int(attrs[mid]) >> 12) & 3
            for i, e in enumerate(blocks[mid]):
                e = int(e); t = tiles[e & 1023]
                if e & 1024: t = t[:, ::-1]
                if e & 2048: t = t[::-1]
                q = i % 4; oy, ox = gy * 16 + (q // 2) * 8, x * 16 + (q % 2) * 8
                m = t > 0
                img[oy:oy + 8, ox:ox + 8][m] = np.array(pals[e >> 12])[t[m]]
    return img, beh, layer, coll, elev, metatile

def main(g):
    img, beh, layer, coll, elev, metatile = decode_sections(g)
    Image.fromarray(img).save(EV / 'native.png')
    built = np.array(Image.open(EV / 'native-decoded.png').convert('RGB'))
    # Palette files store 8-bit values; compare in the GBA's 5-bit space.
    assert ((img.astype(int) >> 3) == (built.astype(int) >> 3)).all(), 'installed sections differ from the build decode'
    ledger = json.loads((EV / 'material-traversal-ledger.json').read_text())['cells']
    MB = B.behaviors(g)
    for c in ledger:
        x, y = c['x'], c['y']
        assert beh[y, x] == MB[c['behavior']], (x, y, c['behavior'])
        assert coll[y, x] == c['collision'] and elev[y, x] == c['elevation'], (x, y)
        assert layer[y, x] == (0 if c['layer'] == 'normal' else 1), (x, y)
    # Reachability from the Center approach, the way the engine moves the player:
    # open and door cells, jump-south ledges crossed downward, and (with Surf) water.
    foot = {(c['x'], c['y']): c['foot'] for c in ledger}
    def reach(surf):
        start = (34, 49); seen = {start}; q = deque([start])
        passable = ('open', 'door', 'water') if surf else ('open', 'door')
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if foot.get(n) in passable:
                    if n not in seen: seen.add(n); q.append(n)
                elif foot.get(n) == 'ledge_south' and dy == 1 and foot.get((x, y + 2)) in passable and (x, y + 2) not in seen:
                    seen.add((x, y + 2)); q.append((x, y + 2))
        return seen
    seen, surfed = reach(False), reach(True)
    open_cells = {k for k, v in foot.items() if v in ('open', 'door')}
    unreachable = sorted(open_cells - surfed)
    surf_only = sorted(open_cells & surfed - seen)
    approaches = dict(center=(34, 49), mart=(27, 49), gym=(28, 24), dragons_den=(32, 5), ice_path=(57, 17), bridge_south=(23, 63),
                      city_sign=(52, 43), gym_sign=(26, 26), den_sign=(31, 7), west_house=(20, 38), east_house=(44, 41), tutor_house=(18, 49))
    needs_surf = []
    for k, p in approaches.items():
        assert p in surfed, ('unreachable approach', k, p)
        if p not in seen:
            needs_surf.append(k)
    # Shared Center and Mart: every opaque source pixel survives in the native top layer.
    c = B.compose()
    shared = c['source'] >= 2
    exact = ((img.astype(int) >> 3) == (c['top'][..., :3].astype(int) >> 3)).all(-1)
    assert exact[shared].all()
    assert (g / 'data/tilesets/primary/blackthorn_city03/palettes/08.pal').read_text() == (g / 'data/tilesets/secondary/cherrygrove/palettes/08.pal').read_text()
    # Preservation: existing map ids keep their order; only expected files changed.
    before = json.loads(subprocess.check_output(['git', '-C', str(g), 'show', 'origin/apocrypha:data/maps/map_groups.json']))
    groups = json.loads((g / 'data/maps/map_groups.json').read_text())
    for key, values in before.items():
        if isinstance(values, list):
            assert groups[key][:len(values)] == values, key
    changed = subprocess.check_output(['git', '-C', str(g), 'diff', '--name-only', 'origin/apocrypha'], text=True).splitlines()
    changed += subprocess.check_output(['git', '-C', str(g), 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
    allowed = {'Makefile', 'data/event_scripts.s', 'data/layouts/layouts.json', 'data/maps/map_groups.json', 'include/regions.h',
               'src/apocrypha_map_proof.c', 'src/data/region_map/region_map_sections.json', 'src/data/tilesets/graphics.h',
               'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h', 'src/field_camera.c', 'src/malloc.c', 'src/overworld.c',
               'include/apocrypha_city_view.h', 'src/apocrypha_city_view.c', 'src/data/apocrypha_city_views.h'}
    prefixes = ('data/layouts/BlackthornCity0', 'data/maps/Blackthorn', 'data/tilesets/primary/blackthorn_city0',
                'data/tilesets/secondary/blackthorn_city0', 'data/city_views/', 'src/data/city_views/', 'tools/city_view/')
    unexpected = sorted(p for p in set(changed) if p not in allowed and not p.startswith(prefixes))
    assert not unexpected, unexpected
    # Coordinate-labelled native grid for review.
    big = Image.fromarray(img).resize((W * 32, H * 32), Image.Resampling.NEAREST); d = ImageDraw.Draw(big)
    for i in range(W):
        d.line((i * 32, 0, i * 32, H * 32), fill=(60, 60, 70)); d.text((i * 32 + 2, 2), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for i in range(H):
        d.line((0, i * 32, W * 32, i * 32), fill=(60, 60, 70)); d.text((2, i * 32 + 3), str(i), fill='white', stroke_width=1, stroke_fill='black')
    for _, y0, _ in B.SECTIONS[1:]:
        d.line((0, y0 * 32, W * 32, y0 * 32), fill=(255, 220, 0), width=2)
    big.save(EV / 'native-grid.png')
    result = dict(cells_audited=len(ledger), installed_matches_build_decode=True, ledger_behaviour_collision_elevation_layer=True,
                  reachable_foot_cells=len(seen), open_cells=len(open_cells), unreachable_open_cells=unreachable,
                  open_cells_reached_only_by_surf=len(surf_only), approaches_needing_surf=needs_surf, approaches=approaches, shared_building_pixels_exact=int(shared.sum()),
                  center_bank8_palette_identical_to_cherrygrove=True, existing_map_ids_preserved=True,
                  changed_files_within_scope=True)
    (EV / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
