#!/usr/bin/env python3
"""Headless mGBA checks for Route 31 (Route 30's runtime.py; each phase a fresh emulator process).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/route31_catalog/runtime.py ENGINE OUT [write read menu]

write  new game; Route 30's north end -> Route 31 -> the Violet gatehouse doorway by walking, every step
       checked against the route the native traversal predicts (Gen 3 ledge rules); west into the doorway
       warps to the Violet gate; Route 31 -> Dark Cave's opening, north into it warps to the cave; back
       across the seam into Route 30; a walking tour into every area HGSS reaches; every ledge run jumps and
       refuses the climb back; both cuttable trees, both signs, the pond, the gatehouse wall and the rock
       block; tall grass with an empty party starts no battle; both signs read; both item balls are picked
       up and disappear; ordinary save
read   cold flash reload of that save (the item flags survive)
menu   title screen -> Continue

Every capture is compared with the installed native decode at the camera position (Route 30 included
where the camera looks across the seam), outside the player sprite: results.json records the share of
identical pixels per frame.
"""
from __future__ import annotations
import json, os, shlex, shutil, struct, subprocess, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import reference as Rf                                       # noqa: E402
from reference import W, H                                   # noqa: E402
from tiles import Tileset                                    # noqa: E402

ART = ROOT / 'gba/art/route31-catalog'
R30, R31, GATE, CAVE = 10, 29, 33, 34
R30_W, R30_H = 36, 102
A, B, RIGHT, LEFT, UP, DOWN = 1, 2, 16, 32, 64, 128
KEY = {(1, 0): RIGHT, (-1, 0): LEFT, (0, 1): DOWN, (0, -1): UP}
FLAGS = dict(poke_ball=0x268, potion=0x269)

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
static const char *out;
static int shots;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);shots++;}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[1]==80&&state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void on(unsigned map,const char*tag){observe(tag);need(state[1]==80&&state[2]==map,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void tap(unsigned key){frames(2,key);frames(12,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,B);frames(40,0);}need(!locked(),"dialogue-closes");}
struct mv{unsigned char key;unsigned short map,x,y;const char*tag;};
static void walk(const struct mv*m,int n){for(int i=0;i<n;i++){step(m[i].key);char t[96];sprintf(t,"walk-%s",m[i].tag?m[i].tag:"step");at(m[i].map,m[i].x,m[i].y,t);need(overworld()&&!locked(),"walk-no-interruption");if(m[i].tag)shot(m[i].tag);}}
static void warp_into(unsigned key,unsigned map,const char*tag){frames(2,key);for(int i=0;i<120;i++){frames(8,key);call("MapProof_ReadState",0);if(c->busRead32(c,sym("gMapProofState")+8)==map)break;}frames(240,0);on(map,tag);shot(tag);}
static void ledge(unsigned x,unsigned y,unsigned key,int dx,int dy,const char*tag){char t[64];go(R31,x,y);step(key);sprintf(t,"%s-jump",tag);at(R31,x+2*dx,y+2*dy,t);unsigned back=key==DOWN?UP:key==UP?DOWN:key==LEFT?RIGHT:LEFT;step(back);sprintf(t,"%s-no-climb",tag);at(R31,x+2*dx,y+2*dy,t);}
static void blocked(unsigned x,unsigned y,unsigned key,const char*tag){go(R31,x,y);step(key);at(R31,x,y,tag);}
static void read_sign(unsigned x,unsigned y,const char*tag){go(R31,x,y+1);tap(UP);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();}
static void ball(unsigned x,unsigned y,unsigned flag,const char*tag){char t[64];go(R31,x,y+1);tap(UP);sprintf(t,"%s-facing",tag);at(R31,x,y+1,t);need(call("FlagGet",flag)==0,tag);frames(1,A);frames(150,0);need(locked(),tag);shot(tag);close_dialog();frames(60,0);need(call("FlagGet",flag)==1,tag);step(UP);sprintf(t,"%s-gone",tag);at(R31,x,y,t);shot(t);}
MOVES
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read|menu\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"route31-catalog");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/route31.sav",argv[3]);
 if(!strcmp(argv[4],"read")||!strcmp(argv[4],"menu")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);shot("title-continue");at(R31,SAVE_X,SAVE_Y,"title-continue");
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(R31,SAVE_X,SAVE_Y,"cold-reload");
  need(call("FlagGet",FLAG_POKE_BALL)==1&&call("FlagGet",FLAG_POTION)==1,"item-flags-survive-save");
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  need(call("CalculatePlayerPartyCount",0)==0,"empty-party");
  // Route 30's north end -> Route 31 -> the gatehouse doorway on foot, every step checked; west warps.
  go(R30,START_X,START_Y);at(R30,START_X,START_Y,"start-route30");shot("route30-start");
  walk(TO_GATE,sizeof(TO_GATE)/sizeof(TO_GATE[0]));
  warp_into(LEFT,GATE,"gatehouse-warp");
  // From the gatehouse's return warp (doorway cell) to Dark Cave's opening on foot; north warps.
  go(R31,DOOR_X,DOOR_Y);at(R31,DOOR_X,DOOR_Y,"doorway");
  walk(TO_CAVE,sizeof(TO_CAVE)/sizeof(TO_CAVE[0]));
  warp_into(UP,CAVE,"dark-cave-warp");
  // Back across the seam into Route 30.
  go(R31,BACK_X,BACK_Y);at(R31,BACK_X,BACK_Y,"seam-start");
  walk(TO_R30,sizeof(TO_R30)/sizeof(TO_R30[0]));
  printf("{\"walked\":\"Route30-Route31-gate, gate warp, doorway-Dark Cave, cave warp, Route31-Route30\"}\n");
  go(R31,TOUR_X,TOUR_Y);at(R31,TOUR_X,TOUR_Y,"tour-start");
  walk(TOUR,sizeof(TOUR)/sizeof(TOUR[0]));
  BALLS
  printf("{\"items\":\"both balls picked up and gone\"}\n");
  LEDGES
  BLOCKS
  go(R31,GRASS_X,GRASS_Y);for(int i=0;i<GRASS_N;i++){step(GRASS_KEY);need(overworld()&&!locked(),"grass-no-battle");}shot("tall-grass");
  printf("{\"tall_grass_steps_without_battle\":%d}\n",GRASS_N);
  SIGNS
  go(R31,SAVE_X,SAVE_Y);at(R31,SAVE_X,SAVE_Y,"save-spot");shot("save-spot");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

JUMP = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

def load_trav(art):
    t = json.loads((art / 'source/pack/traversal.json').read_text())
    return {(c['x'], c['y']): c for c in t}

def path(trav, a, b, avoid=()):
    """Shortest walk from a to b on the native traversal (Gen 3 ledge rules). Returns [(d, landing)]."""
    ok = lambda p: p in trav and trav[p]['foot'] == 'open' and p not in avoid
    prev = {a: None}; q = deque([a])
    while q:
        p = q.popleft()
        if p == b:
            break
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (p[0] + d[0], p[1] + d[1])
            if n in trav and trav[n]['foot'] in JUMP:
                if JUMP[trav[n]['foot']] != d:
                    continue
                n = (n[0] + d[0], n[1] + d[1])
            if ok(n) and n not in prev:
                prev[n] = (p, d); q.append(n)
    assert b in prev, (a, b)
    out, p = [], b
    while prev[p] is not None:
        pp, d = prev[p]; out.append((d, p)); p = pp
    return out[::-1]

def cmoves(name, moves):
    rows = ['{%d,%d,%d,%d,%s}' % (KEY[d], m, x, y, f'"{tag}"' if tag else '0') for (d, (m, x, y), tag) in moves]
    return f'static const struct mv {name}[]={{' + ','.join(rows) + '};\n'

def tagged(seg, m, prefix, every):
    return [(d, (m, *p), f'{prefix}-{i:03d}' if i % every == every - 1 or i == len(seg) - 1 else None) for i, (d, p) in enumerate(seg)]

def plan(engine):
    trav = load_trav(ART)
    ev = json.loads((engine / 'data/maps/JohtoRoute31/map.json').read_text())
    signs = [(b['x'], b['y']) for b in ev['bg_events'] if b['type'] == 'sign']
    balls = [(o['x'], o['y'], o['flag']) for o in ev['object_events'] if o['graphics_id'] == 'OBJ_EVENT_GFX_ITEM_BALL']
    objs = {(o['x'], o['y']) for o in ev['object_events']}
    gate = next(w for w in ev['warp_events'] if w['dest_map'] == 'MAP_VIOLET_EAST_GATE')
    cave = next(w for w in ev['warp_events'] if w['dest_map'] == 'MAP_DARK_CAVE_ENTRANCE')
    off = -Rf.R30_OFFSET                                        # Route 30 column x is Route 31 column x + 28
    entry31 = (39, H - 1)                                       # the road above Route 30's stairs
    start30 = (entry31[0] - off, 2)
    to_gate = [((0, -1), (R30, start30[0], 1), None), ((0, -1), (R30, start30[0], 0), None),
               ((0, -1), (R31, *entry31), 'cross-into-route31')]
    to_gate += tagged(path(trav, entry31, (gate['x'], gate['y']), avoid=objs), R31, 'to-gate', 8)
    to_cave = tagged(path(trav, (gate['x'], gate['y']), (cave['x'], cave['y'] + 1), avoid=objs), R31, 'to-cave', 8)
    back = (cave['x'], cave['y'] + 1)
    to_r30 = tagged(path(trav, back, entry31, avoid=objs), R31, 'to-seam', 16) + [((0, 1), (R30, entry31[0] - off, 0), 'cross-back-into-route30')]
    # Tour: farthest-point picks over the reachable open cells, visited nearest-next.
    reach = set([entry31]); q = deque([entry31])
    while q:
        pnt = q.popleft()
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (pnt[0] + d[0], pnt[1] + d[1])
            if n in trav and trav[n]['foot'] in JUMP:
                if JUMP[trav[n]['foot']] != d:
                    continue
                n = (n[0] + d[0], n[1] + d[1])
            if n in trav and trav[n]['foot'] == 'open' and n not in objs and n not in reach and trav[n]['code'] not in 'WV':
                reach.add(n); q.append(n)
    picks = [entry31]; cand = sorted(reach)
    while len(picks) < 15:
        picks.append(max(cand, key=lambda c: min(abs(c[0] - p_[0]) + abs(c[1] - p_[1]) for p_ in picks)))
    targets = [(t, f'area-{t[0]}-{t[1]}') for t in picks[1:]]
    ordered, cur_ = [], entry31
    while targets:
        t = min(targets, key=lambda t: abs(t[0][0] - cur_[0]) + abs(t[0][1] - cur_[1]))
        targets.remove(t); ordered.append(t); cur_ = t[0]
    tour, cur = [], entry31
    for (t, name) in ordered:
        seg = path(trav, cur, t, avoid=objs | {p for p, c in trav.items() if c['code'] in 'WV'})
        tour += [(d, (R31, *p), name if i == len(seg) - 1 else None) for i, (d, p) in enumerate(seg)]
        cur = t
    ledges, seen = [], set()
    for (x, y), c in sorted(trav.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        f = c['foot']
        if f not in JUMP or (x, y) in seen:
            continue
        d = JUMP[f]
        run = [(x, y)]
        while (n := (run[-1][0] + abs(d[1]), run[-1][1] + abs(d[0]))) in trav and trav[n]['foot'] == f:
            run.append(n)
        seen |= set(run)
        mid = run[len(run) // 2]
        src = (mid[0] - d[0], mid[1] - d[1]); dst = (mid[0] + d[0], mid[1] + d[1])
        if trav.get(src, {}).get('foot') == 'open' and trav.get(dst, {}).get('foot') == 'open' and dst not in objs:
            ledges.append((src, KEY[d], d, f'{f}-{mid[0]}-{mid[1]}'))
    blocks = []
    for o in ev['object_events']:
        if o['graphics_id'] == 'OBJ_EVENT_GFX_CUTTABLE_TREE':
            blocks.append(((o['x'], o['y'] + 1), UP, f"cut-tree-{o['x']}-{o['y']}"))
    for (x, y) in signs:
        blocks.append(((x, y + 1), UP, f'sign-{x}-{y}'))
    def edge(code, name, foot=None):
        for p in sorted(p for p, c in trav.items() if (c['foot'] == foot if foot else c['code'] == code)):
            for d in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                s = (p[0] - d[0], p[1] - d[1])
                if s in reach:
                    return [(s, KEY[d], name)]
        return []
    blocks += edge(None, 'pond-edge', foot='water') + edge('B', 'gatehouse-wall') + edge('R', 'rock') + edge('C', 'cave-rock')
    grass = None
    for (x, y), c in sorted(trav.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if (x, y) in reach and all(trav.get((x, y + i), {}).get('behavior') == 'MB_TALL_GRASS' for i in range(1, 7)):
            grass = (x, y, DOWN, 6); break
    save = entry31
    return dict(start30=start30, to_gate=to_gate, to_cave=to_cave, to_r30=to_r30, back=back, tour=tour, ledges=ledges,
                blocks=blocks, signs=sorted(signs), grass=grass, balls=balls, save=save, door=(gate['x'], gate['y']), tour_start=entry31)

def generate(engine):
    p = plan(engine)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    src = src.replace('MOVES', cmoves('TO_GATE', p['to_gate']) + cmoves('TO_CAVE', p['to_cave']) + cmoves('TO_R30', p['to_r30']) + cmoves('TOUR', p['tour']))
    src = src.replace('LEDGES', ''.join(f'ledge({s[0]},{s[1]},{k},{d[0]},{d[1]},"{t}");' for s, k, d, t in p['ledges']))
    src = src.replace('BLOCKS', ''.join(f'blocked({s[0]},{s[1]},{k},"{t}");shot("{t}");' for s, k, t in p['blocks']))
    fl = {'FLAG_ITEM_APOC_ROUTE31_POKE_BALL': 'FLAG_POKE_BALL', 'FLAG_ITEM_APOC_ROUTE31_POTION': 'FLAG_POTION'}
    src = src.replace('BALLS', ''.join(f'ball({x},{y},{fl[f]},"item-ball-{x}-{y}");' for x, y, f in p['balls']))
    src = src.replace('SIGNS', ''.join(f'read_sign({x},{y},"read-sign-{x}-{y}");' for x, y in p['signs']))
    g = p['grass']
    rep = dict(START_X=p['start30'][0], START_Y=p['start30'][1], DOOR_X=p['door'][0], DOOR_Y=p['door'][1], BACK_X=p['back'][0], BACK_Y=p['back'][1],
               TOUR_X=p['tour_start'][0], TOUR_Y=p['tour_start'][1], GRASS_X=g[0], GRASS_Y=g[1], GRASS_KEY=g[2], GRASS_N=g[3],
               SAVE_X=p['save'][0], SAVE_Y=p['save'][1], FLAG_POKE_BALL=FLAGS['poke_ball'], FLAG_POTION=FLAGS['potion'],
               R30=R30, R31=R31, GATE=GATE, CAVE=CAVE, RIGHT=RIGHT, LEFT=LEFT, UP=UP, DOWN=DOWN)
    defines = ''.join(f'#define {k} {v}\n' for k, v in rep.items()) + '#define A 1\n#define B 2\n'
    return src.replace('#undef main\n', '#undef main\n' + defines, 1), p

# --------------------------------------------------------------------------- frame parity
def world(engine):
    """Route 31's native decode with Route 30 below it, as the connection joins them."""
    def img(layout, sec, pri, w):
        b = (engine / f'data/layouts/{layout}/map.bin').read_bytes()
        return np.array(Tileset(engine, sec, pri).map_image(list(struct.unpack('<%dH' % (len(b) // 2), b)), w).convert('RGB'))
    r31 = img('JohtoRoute31', 'route31_hgss', 'cherrygrove_route31', W)
    r30 = img('CherrygroveRoute30Approach', 'route30_hgss', 'cherrygrove_route30', R30_W)
    pad = 16 * 16
    canvas = np.zeros((pad + r31.shape[0] + r30.shape[0] + pad, pad + r31.shape[1] + pad, 3), np.int16) - 1
    canvas[pad:pad + r31.shape[0], pad:pad + r31.shape[1]] = r31
    ox = pad - Rf.R30_OFFSET * 16
    canvas[pad + r31.shape[0]:pad + r31.shape[0] + r30.shape[0], ox:ox + r30.shape[1]] = r30
    return canvas, {R31: (pad, pad), R30: (ox, pad + r31.shape[0])}

def parity(engine, outdir, shots):
    canvas, origin = world(engine)
    canvas = np.where(canvas >= 0, canvas >> 3, -1)
    res = []
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True
    offset = (-112, -72)
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] not in origin or not f.exists():
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3
        ox, oy = origin[s['map']]
        x0, y0 = ox + s['x'] * 16 + offset[0], oy + s['y'] * 16 + offset[1]
        if x0 < 0 or y0 < 0 or x0 + 240 > canvas.shape[1] or y0 + 160 > canvas.shape[0]:
            continue
        cc = canvas[y0:y0 + 160, x0:x0 + 240]
        valid = (cc[..., 0] >= 0) & ~sprite
        same = ((cc == frame).all(-1) & valid).sum() / max(1, valid.sum())
        res.append(dict(shot=s['shot'], map=s['map'], x=s['x'], y=s['y'], identical=round(float(same), 4)))
    return dict(camera_offset=offset, frames=res)

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    src, p = generate(engine)
    (out / 'route31_runtime.c').write_text(src)
    (out / 'plan.json').write_text(json.dumps({k: v for k, v in p.items() if k not in ('to_gate', 'to_cave', 'to_r30', 'tour')} | dict(
        steps_to_gate=len(p['to_gate']), steps_to_cave=len(p['to_cave']), steps_to_route30=len(p['to_r30']), tour_steps=len(p['tour'])), indent=1, default=list) + '\n')
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'route31_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
    nm = shutil.which('arm-none-eabi-nm')
    lines = subprocess.check_output([nm, str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData', 'LoadGameSave',
              'ArePlayerFieldControlsLocked', 'FlagGet', 'CalculatePlayerPartyCount', 'gMain', 'CB2_Overworld', 'gSaveBlock2Ptr'}
    symbols = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted, wanted - symbols.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in symbols.items()))
    results = []
    for phase in (sys.argv[3:] or ['write', 'read', 'menu']):
        r = subprocess.run([str(out / 'runtime'), str(engine / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out), phase],
                           capture_output=True, text=True, timeout=5400)
        (out / (phase + '.jsonl')).write_text(r.stdout)
        obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        for file in out.glob('*.ppm'):
            Image.open(file).save(file.with_suffix('.png')); file.unlink()
        results.append(dict(phase=phase, exit_code=r.returncode, stderr=r.stderr[-2000:], observations=len(obs),
                            parity=parity(engine, out, [o for o in obs if 'shot' in o])))
        (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
        print(phase, r.returncode, r.stderr[-600:], flush=True)
        if r.returncode != 0:
            sys.exit(r.returncode)
    print('All phases passed.')

if __name__ == '__main__':
    main()
