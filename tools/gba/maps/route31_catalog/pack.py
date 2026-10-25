"""Route 31: traversal from the decoded HGSS permissions, layer types, events, and the map's side of the
joint Route 30/31 pack (Route 30's pack.py, for Route 31).

    python3 tools/gba/maps/route31_catalog/pack.py ENGINE_CHECKOUT --spec FILE | --install-words FILE

The tilesets are packed and installed by tools/gba/maps/route30_catalog/pair_pack.py, which runs this file
with --spec (this map's layers, traversal and layer types) and --install-words (its map words, events and
checks). Route 31 shares Route 30's primary (`route30_31`) and draws its own art from `route31_hgss`.

Traversal (source/trace/ledger.json, decoded HGSS permissions): woods under a tree root, rock, the
gatehouse, the cave mouth's rock, signs and ledge ends blocked (collision 1, elevation 0 as vanilla);
ledges MB_JUMP_SOUTH / MB_JUMP_EAST; pond water MB_POND_WATER (collision 0, elevation 1); tall grass
MB_TALL_GRASS; the gatehouse doorway MB_WEST_ARROW_WARP on HGSS's two gate warps; the Dark Cave opening
MB_NON_ANIMATED_DOOR on HGSS's cave warp; stairs and everything else open.
"""
from __future__ import annotations
import json, re, struct, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.append(str(HERE.parent / 'route30_catalog'))
import reference as Rf                               # noqa: E402
from reference import W, H                           # noqa: E402
from tiles import Tileset                            # noqa: E402

ROOT = HERE.parents[3]
ART = ROOT / 'gba/art/route31-catalog'
SRC, EV = ART / 'source', ART / 'evidence'
OUT, OEV = SRC / 'pack', EV / 'pack'
MAP, LAYOUT = 'JohtoRoute31', 'LAYOUT_JOHTO_ROUTE31'
TS_NAME, TS_SYM = 'route31_hgss', 'Route31Hgss'
PRI_NAME, PRI_SYM = 'route30_31', 'Route30Route31Primary'
BASE_REV = '2722eaf7601ec02dc5a684fa8cdef9206c0dc377'
# JOHTO_ITEMS.md: Route 31's Poke Ball and Potion balls (HGSS's two item balls).
ITEMS = dict(poke_ball=('FLAG_ITEM_APOC_ROUTE31_POKE_BALL', 'FLAG_UNUSED_0x268', 'ITEM_POKE_BALL'),
             potion=('FLAG_ITEM_APOC_ROUTE31_POTION', 'FLAG_UNUSED_0x269', 'ITEM_POTION'))
SIGN_SCRIPTS = {'Rt. 31': 'JohtoRoute31_RouteSign', 'Dark Cave': 'JohtoRoute31_DarkCaveSign'}
# HGSS warps: 0 and 1 the gatehouse doorway, 2 Dark Cave. The engine's gate and cave already return to
# Route 31's warps 0 (gate) and 1 (cave), so the cave is warp 1 here and the second doorway cell warp 2.
WARPS = {(6, 13): (0, 'MAP_VIOLET_EAST_GATE', '2'), (53, 13): (1, 'MAP_DARK_CAVE_ENTRANCE', '0'),
         (6, 14): (2, 'MAP_VIOLET_EAST_GATE', '2')}

def rgb5(a): return (np.asarray(a).astype(np.int32) >> 3)

def behaviors(engine):
    names = re.findall(r'^\s+(MB_[A-Z0-9_]+),', (engine / 'include/constants/metatile_behaviors.h').read_text(), re.M)
    return {n: i for i, n in enumerate(names)}

# --------------------------------------------------------------------------- traversal
def traversal(engine, grid, cells):
    MB = behaviors(engine)
    out = np.empty((H, W), object)
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            hx, hz = Rf.to_hgss(x, y)
            c = dict(x=x, y=y, code=ch, hgss=dict(type=cells[hz][hx]['type'], collision=cells[hz][hx]['collision'], label=cells[hz][hx]['lab']))
            if ch == 'L':
                c.update(foot='ledge_south', behavior='MB_JUMP_SOUTH', collision=1, elevation=0)
            elif ch == 'E':
                c.update(foot='ledge_east', behavior='MB_JUMP_EAST', collision=1, elevation=0)
            elif ch == 'Q':
                c.update(foot='ledge_west', behavior='MB_JUMP_WEST', collision=1, elevation=0)
            elif ch == '~':
                c.update(foot='water', behavior='MB_POND_WATER', collision=0, elevation=1)
            elif ch == 'W':
                c.update(foot='open', behavior='MB_WEST_ARROW_WARP', collision=0, elevation=3, warp=WARPS[(x, y)][0])
            elif ch == 'V':
                c.update(foot='open', behavior='MB_NON_ANIMATED_DOOR', collision=0, elevation=3, warp=WARPS[(x, y)][0])
            elif ch in 'tkoRBCsJX':
                c.update(foot='blocked', behavior='MB_NORMAL', collision=1, elevation=0)
            elif ch == 'G':
                c.update(foot='open', behavior='MB_TALL_GRASS', collision=0, elevation=3)
            else:
                c.update(foot='open', behavior='MB_NORMAL', collision=0, elevation=3)
            c['behavior_id'] = MB[c['behavior']]
            out[y, x] = c
    return out

JUMP = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

def reach(trav, start, cut_open=False, cut=()):
    """Cells reachable on foot from start, with Gen 3 ledge rules (jump over a ledge in its direction)."""
    seen = {start}; q = deque([start])
    walk = lambda p: 0 <= p[0] < W and 0 <= p[1] < H and trav[p[1], p[0]]['foot'] == 'open' and (cut_open or p not in cut)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < W and 0 <= n[1] < H):
                continue
            f = trav[n[1], n[0]]['foot']
            if f in JUMP and JUMP[f] == (dx, dy):
                n = (n[0] + dx, n[1] + dy)
            if walk(n) and n not in seen:
                seen.add(n); q.append(n)
    return seen

def hgss_reach(cells, start):
    """The same search on HGSS's own permissions; water and the cave opening are not walked."""
    types = {0x3B: (0, 1), 0x38: (1, 0), 0x39: (-1, 0)}
    open_ = lambda hx, hz: (0 <= hx < Rf.HW and 0 <= hz < Rf.HH and not cells[hz][hx]['blocked']
                            and cells[hz][hx]['type'] not in (0x10, 0x69))
    seen = {start}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < Rf.HW and 0 <= n[1] < Rf.HH):
                continue
            t = cells[n[1]][n[0]]['type']
            if t in types and types[t] == (dx, dy):
                n = (n[0] + dx, n[1] + dy)
            if open_(*n) and n not in seen:
                seen.add(n); q.append(n)
    return seen

# --------------------------------------------------------------------------- layer types
def above_player(trav, top, owner):
    """Walkable cells whose object art belongs to something standing further south draw above the
    player (Route 43's rule: a crown or roof the player walks behind)."""
    art = top[..., 3] > 0
    base = {}
    for name in set(owner[art].ravel().tolist()) - {''}:
        base[name] = int(np.nonzero((owner == name).any(1))[0].max()) // 16
    out = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            if trav[y, x]['foot'] != 'open':
                continue
            sl = np.s_[y * 16:y * 16 + 16, x * 16:x * 16 + 16]
            a = art[sl]
            if not a.any():
                continue
            names = set(owner[sl][a].ravel().tolist()) - {''}
            out[y, x] = any(base[n] > y for n in names)
    return out

def prepare(engine):
    z = np.load(SRC / 'assemble/layers.npz', allow_pickle=True)
    ground, flat, top, owner = z['ground'], z['flat'], z['objects'], z['owner'].astype(object)
    grid = [list(l.split()[1]) for l in (SRC / 'trace/material-grid.txt').read_text().splitlines() if l[:3].isdigit()]
    cells = json.loads((SRC / 'trace/ledger.json').read_text())['cells']
    trav = traversal(engine, grid, cells)
    above = above_player(trav, top, owner)
    want = ground.copy()
    for layer in (flat, top):
        a = layer[..., 3] > 0; want[a] = layer[a, :3]
    from claude_cherrygrove import ground as Gr
    import assemble as As
    yy, xx = np.mgrid[0:H * 16, 0:W * 16]
    lawn_t = Gr.textures()[Gr.GRASS]
    road_t = As.road_texture(engine)
    plains = [lawn_t[(yy + Rf.YPHASE) % 32, (xx + Rf.XPHASE) % 32].astype(np.uint8),
              road_t[(yy + Rf.YPHASE) % 32, (xx + Rf.XPHASE) % 32].astype(np.uint8)]
    return dict(ground=ground, flat=flat, top=top, owner=owner, grid=grid, cells=cells, trav=trav, above=above, want=want, plains=plains)

def save_pair_spec(engine, path):
    """This map's input to the joint Route 30/31 pack (route30_catalog/pair_pack.py)."""
    import pair_pack as PP
    d = prepare(engine)
    trav = d['trav']
    get = lambda k: np.array([[trav[y, x][k] for x in range(W)] for y in range(H)])
    PP.save_spec(path, 'route31', W, H, d['ground'], d['flat'], d['top'], d['owner'], d['above'], get('behavior_id'),
                 get('collision'), get('elevation'), {}, {}, set(), d['plains'])

# --------------------------------------------------------------------------- write
def write_flags(engine):
    f = engine / 'include/constants/flags.h'; s = f.read_text()
    anchor = next(l for l in s.splitlines() if l.startswith('#define FLAG_HIDDEN_ITEM_APOC_ROUTE30_POTION'))
    add = [f'#define {name} {slot} // Route 31: {what} (JOHTO_ITEMS.md, HGSS item ball)'
           for k, (name, slot, what) in ITEMS.items() if f'#define {name} ' not in s]
    if add:
        s = s.replace(anchor, anchor + '\n' + '\n'.join(add), 1); f.write_text(s)

SCRIPTS = '''JohtoRoute31_MapScripts::
    .byte 0

JohtoRoute31_RouteSign::
    msgbox JohtoRoute31_RouteSign_Text, MSGBOX_SIGN
    end

JohtoRoute31_RouteSign_Text:
    .string "ROUTE 31\\nWEST TO VIOLET CITY$"

JohtoRoute31_DarkCaveSign::
    msgbox JohtoRoute31_DarkCaveSign_Text, MSGBOX_SIGN
    end

JohtoRoute31_DarkCaveSign_Text:
    .string "DARK CAVE$"
'''

def write_map(engine, words, trav):
    (engine / f'data/layouts/{MAP}/map.bin').write_bytes(struct.pack('<%dH' % (W * H), *words.ravel().tolist()))
    lj = engine / 'data/layouts/layouts.json'; L = json.loads(lj.read_text())
    for l in L['layouts']:
        if l['id'] == LAYOUT:
            l['primary_tileset'] = 'gTileset_' + PRI_SYM; l['secondary_tileset'] = 'gTileset_' + TS_SYM; l['width'] = W; l['height'] = H
    lj.write_text(json.dumps(L, indent=2) + '\n')
    base = json.loads(subprocess.check_output(['git', '-C', str(engine), 'show', f'{BASE_REV}:data/maps/{MAP}/map.json']))
    events = json.loads((SRC / 'hgss-events.json').read_text())
    moves, bgs, objs = [], [], []
    for s in events['signs']:
        x, y = Rf.to_map(*s['cell'])
        script = next(v for k, v in SIGN_SCRIPTS.items() if k in s['text'])
        assert trav[y, x]['code'] == 's', ('sign cell is not a sign', x, y)
        bgs.append(dict(type='sign', x=x, y=y, elevation=0, player_facing_dir='BG_EVENT_PLAYER_FACING_ANY', script=script))
        moves.append(dict(event=script, cell=[x, y], hgss=s['cell'], text=s['text']))
    warps = [None] * len(WARPS)
    for (x, y), (i, dest, dw) in WARPS.items():
        assert trav[y, x]['code'] in 'WV', ('warp cell is not a doorway', x, y)
        warps[i] = dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=dw)
    for w in events['warps']:
        x, y = Rf.to_map(*w['cell'])
        moves.append(dict(event=f'HGSS warp {w["index"]} to {w["dest"]}', cell=[x, y], hgss=w['cell'], native_warp=WARPS[(x, y)][0]))
    cut = [Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE']
    for n, (x, y) in enumerate(cut):
        assert trav[y, x]['foot'] == 'open', ('cut tree cell is not open ground', x, y)
        objs.append(dict(graphics_id='OBJ_EVENT_GFX_CUTTABLE_TREE', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_LOOK_AROUND',
                         movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
                         script='EventScript_CutTree', flag=f'FLAG_TEMP_{11 + n}'))
    for o in events['objects']:
        if o['sprite'] != 'SPRITE_MONSTARBALL':
            continue
        k = 'poke_ball' if 'POKE_BALL' in o['flag'] else 'potion'
        name, _, item = ITEMS[k]
        x, y = Rf.to_map(*o['cell'])
        assert trav[y, x]['foot'] == 'open', ('item ball cell is not open ground', x, y)
        objs.append(dict(graphics_id='OBJ_EVENT_GFX_ITEM_BALL', x=x, y=y, elevation=3, movement_type='MOVEMENT_TYPE_FACE_DOWN',
                         movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id=item,
                         script='Common_EventScript_FindItem', flag=name))
        moves.append(dict(event=f'item ball {item}', cell=[x, y], hgss=o['cell'], flag=name, hgss_flag=o['flag']))
    for o in events['objects']:
        if o['sprite'] not in ('SPRITE_TREE', 'SPRITE_MONSTARBALL'):
            moves.append(dict(event=o['id'], hgss=o['cell'], note='NPC or Apricorn tree: not placed (no scripts yet)'))
    M = dict(base)
    M['bg_events'] = bgs
    M['object_events'] = objs
    M['warp_events'] = warps
    M['connections'] = [dict(map='MAP_CHERRYGROVE_ROUTE30_APPROACH', direction='down', offset=-Rf.R30_OFFSET)]
    (engine / f'data/maps/{MAP}/map.json').write_text(json.dumps(M, indent=2) + '\n')
    (engine / f'data/maps/{MAP}/scripts.inc').write_text(SCRIPTS)
    write_flags(engine)
    return dict(moves=moves, cut_trees=cut)

# --------------------------------------------------------------------------- checks
def decode(engine, words):
    t = Tileset(engine, TS_NAME, PRI_NAME)
    return np.array(t.map_image(words.ravel().tolist(), W).convert('RGB'))

def reach_report(trav, cells, events):
    cut = {Rf.to_map(*o['cell']) for o in events['objects'] if o['sprite'] == 'SPRITE_TREE'}
    start = (39, H - 1)                                  # the road where Route 30's stairs arrive
    hs = hgss_reach(cells, Rf.to_hgss(*start))
    ns_cut = reach(trav, start, cut_open=True)
    ns = reach(trav, start, cut=cut)
    hs_map = {Rf.to_map(*p) for p in hs}
    return dict(native_with_cut=len(ns_cut), native_before_cut=len(ns), hgss=len(hs),
                native_only=sorted(list(p) for p in ns_cut if p not in hs_map),
                hgss_only=sorted(list(p) for p in hs_map if p not in ns_cut),
                gate_reached=all(p in ns for p in ((6, 13), (6, 14))), cave_reached=(53, 13) in ns)

def install_pair(engine, words_path):
    OUT.mkdir(parents=True, exist_ok=True); OEV.mkdir(parents=True, exist_ok=True)
    d = prepare(engine)
    words = np.load(words_path)
    for y in range(H):
        for x in range(W):
            d['trav'][y, x]['metatile'] = int(words[y, x]) & 1023
    report = dict(events=write_map(engine, words, d['trav']))
    native = decode(engine, words)
    Image.fromarray(native).save(OEV / 'native.png')
    report['native_pixels_differing'] = int((rgb5(native) != rgb5(d['want'])).any(-1).sum())
    report['reach'] = reach_report(d['trav'], d['cells'], json.loads((SRC / 'hgss-events.json').read_text()))
    (OUT / 'traversal.json').write_text(json.dumps([d['trav'][y, x] for y in range(H) for x in range(W)], default=int) + '\n')
    (OEV / 'install.json').write_text(json.dumps(report, indent=1, default=int) + '\n')
    print(json.dumps(dict(native_pixels_differing=report['native_pixels_differing'], reach={k: v for k, v in report['reach'].items() if not isinstance(v, list) or len(v) < 12})))

if __name__ == '__main__':
    eng = Path(sys.argv[1]).resolve()
    if '--spec' in sys.argv:
        save_pair_spec(eng, sys.argv[sys.argv.index('--spec') + 1])
    elif '--install-words' in sys.argv:
        install_pair(eng, sys.argv[sys.argv.index('--install-words') + 1])
    else:
        sys.exit(__doc__)
