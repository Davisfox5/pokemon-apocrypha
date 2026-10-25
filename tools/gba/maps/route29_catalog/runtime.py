#!/usr/bin/env python3
"""Headless mGBA checks for Route 29 (each phase a fresh emulator process).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/route29_catalog/runtime.py ENGINE OUT [write read menu]

write  new game; Cherrygrove -> Route 29 -> New Bark and back again by walking, every step checked against
       the route the native traversal predicts (computed here with Gen 3 ledge rules); a walking tour
       into every area HGSS reaches (upper lawn, gatehouse front, north-east grass, the south pocket and
       the lookout); every ledge run jumps and refuses the climb back; the gatehouse, both cuttable
       trees and both signs block; tall grass with an empty party starts no battle; both signs read;
       HGSS's item ball is picked up on foot and disappears; ordinary save
read   cold flash reload of that save
menu   title screen -> Continue

Every capture is compared with the installed native decode at the camera position (both towns
included where the camera looks across a seam), outside the player sprite: results.json records
the share of identical pixels per frame.
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

ART = ROOT / 'gba/art/route29-catalog'
TOWN, R29, NEWBARK = 0, 9, 28
A, B, RIGHT, LEFT, UP, DOWN = 1, 2, 16, 32, 64, 128
KEY = {(1, 0): RIGHT, (-1, 0): LEFT, (0, 1): DOWN, (0, -1): UP}
ITEM_FLAG = 0x264
TOWN_W, NB_W, NB_OFFSET = 80, 36, 6

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
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void tap(unsigned key){frames(2,key);frames(12,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,B);frames(40,0);}need(!locked(),"dialogue-closes");}
struct mv{unsigned char key;unsigned short map,x,y;const char*tag;};
static void walk(const struct mv*m,int n){for(int i=0;i<n;i++){step(m[i].key);char t[96];sprintf(t,"walk-%s",m[i].tag?m[i].tag:"step");at(m[i].map,m[i].x,m[i].y,t);need(overworld()&&!locked(),"walk-no-interruption");if(m[i].tag)shot(m[i].tag);}}
static void ledge(unsigned x,unsigned y,unsigned key,int dx,int dy,const char*tag){char t[64];go(R29,x,y);step(key);sprintf(t,"%s-jump",tag);at(R29,x+2*dx,y+2*dy,t);unsigned back=key==DOWN?UP:key==UP?DOWN:key==LEFT?RIGHT:LEFT;step(back);sprintf(t,"%s-no-climb",tag);at(R29,x+2*dx,y+2*dy,t);}
static void blocked(unsigned x,unsigned y,unsigned key,const char*tag){go(R29,x,y);step(key);at(R29,x,y,tag);}
static void read_sign(unsigned x,unsigned y,const char*tag){go(R29,x,y+1);tap(UP);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();}
MOVES
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read|menu\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"route29-catalog");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/route29.sav",argv[3]);
 if(!strcmp(argv[4],"read")||!strcmp(argv[4],"menu")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);shot("title-continue");at(R29,SAVE_X,SAVE_Y,"title-continue");
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(R29,SAVE_X,SAVE_Y,"cold-reload");
  need(call("FlagGet",ITEM_FLAG)==1,"item-ball-flag-survives-save");
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  need(call("CalculatePlayerPartyCount",0)==0,"empty-party");
  // Cherrygrove -> Route 29 -> New Bark on foot, every step checked; then back to Cherrygrove.
  go(TOWN,START_X,START_Y);at(TOWN,START_X,START_Y,"start-cherrygrove");shot("cherrygrove-start");
  walk(ROUTE_OUT,sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0]));
  walk(ROUTE_BACK,sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0]));
  printf("{\"walked\":\"Cherrygrove-Route29-NewBark-and-back\",\"steps\":%d}\n",(int)(sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0])+sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0])));
  // A walking tour into every area: no warps between targets.
  go(R29,TOUR_X,TOUR_Y);at(R29,TOUR_X,TOUR_Y,"tour-start");
  walk(TOUR,sizeof(TOUR)/sizeof(TOUR[0]));
  // HGSS's item ball, reached on foot by the tour: it blocks, the player faces it and picks it up, then it is gone.
  FACE_POTION
  need(call("FlagGet",ITEM_FLAG)==0,"item-ball-flag-clear");
  frames(1,A);frames(150,0);need(locked(),"item-ball-picked-up");shot("item-ball-potion");close_dialog();frames(60,0);
  need(call("FlagGet",ITEM_FLAG)==1,"item-ball-flag-set");
  step(UP);at(R29,POTION_X,POTION_Y,"item-ball-gone");shot("item-ball-gone");
  printf("{\"item_ball\":\"Potion picked up once, ball removed\",\"flag\":%u}\n",ITEM_FLAG);
  LEDGES
  BLOCKS
  go(R29,GRASS_X,GRASS_Y);for(int i=0;i<6;i++){step(RIGHT);need(overworld()&&!locked(),"grass-no-battle");}shot("tall-grass");
  printf("{\"tall_grass_steps_without_battle\":6}\n");
  read_sign(WEST_SIGN_X,WEST_SIGN_Y,"sign-west");read_sign(EAST_SIGN_X,EAST_SIGN_Y,"sign-east");
  go(R29,SAVE_X,SAVE_Y);at(R29,SAVE_X,SAVE_Y,"save-spot");shot("save-spot");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

def load_trav():
    t = json.loads((ART / 'source/pack/traversal.json').read_text())
    return {(c['x'], c['y']): c for c in t}

JUMP = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

def path(trav, a, b, avoid=()):
    """Shortest walk from a to b on the native traversal (Gen 3 ledge rules). Returns (dx, dy, landing)."""
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
    out = []
    p = b
    while prev[p] is not None:
        pp, d = prev[p]; out.append((d, p)); p = pp
    return out[::-1]

def cmoves(name, moves):
    rows = []
    for (d, (m, x, y), tag) in moves:
        rows.append('{%d,%d,%d,%d,%s}' % (KEY[d], m, x, y, f'"{tag}"' if tag else '0'))
    return f'static const struct mv {name}[]={{' + ','.join(rows) + '};\n'

def plan(engine):
    trav = load_trav()
    ev = json.loads((engine / 'data/maps/CherrygroveRoute29Approach/map.json').read_text())
    signs = [(b['x'], b['y']) for b in ev['bg_events'] if b['type'] == 'sign']
    potion = next((o['x'], o['y']) for o in ev['object_events'] if o['graphics_id'] == 'OBJ_EVENT_GFX_ITEM_BALL')
    cut = {(o['x'], o['y']) for o in ev['object_events'] if o['graphics_id'] in ('OBJ_EVENT_GFX_CUTTABLE_TREE', 'OBJ_EVENT_GFX_ITEM_BALL')}
    tb = (engine / 'data/layouts/CherrygroveCity/map.bin').read_bytes()
    town = np.array(struct.unpack('<%dH' % (len(tb) // 2), tb)).reshape(-1, TOWN_W)
    road_y = 18
    assert not (town[road_y, TOWN_W - 1] >> 10) & 3
    start = (TOWN_W - 4, road_y)
    # Out: three town cells, Route 29 west edge to east edge, two cells into New Bark.
    out = [((1, 0), (TOWN, TOWN_W - 3 + i, road_y), None) for i in range(3)]
    out += [((1, 0), (R29, 0, road_y), 'cross-into-route29')]
    seg = path(trav, (0, road_y), (W - 1, road_y), avoid=cut)
    for i, (d, p) in enumerate(seg):
        tag = f'route-{i:03d}' if i % 8 == 7 or i == len(seg) - 1 else None
        out.append((d, (R29, *p), tag))
    out += [((1, 0), (NEWBARK, 0, road_y - NB_OFFSET), 'cross-into-new-bark'), ((1, 0), (NEWBARK, 1, road_y - NB_OFFSET), None)]
    back = [((-1, 0), (NEWBARK, 0, road_y - NB_OFFSET), None), ((-1, 0), (R29, W - 1, road_y), 'cross-back-into-route29')]
    seg = path(trav, (W - 1, road_y), (0, road_y), avoid=cut)
    for i, (d, p) in enumerate(seg):
        back.append((d, (R29, *p), f'back-{i:03d}' if i % 16 == 15 else None))
    back += [((-1, 0), (TOWN, TOWN_W - 1, road_y), 'cross-back-into-cherrygrove')]
    # Tour: every area HGSS reaches, walked between targets.
    targets = [((24, 12), 'upper-lawn'), ((33, 10), 'north-grass'), ((54, 9), 'gatehouse-front'), ((72, 6), 'north-east-grass'),
               ((88, 15), 'east-sign-lawn'), ((84, 22), 'east-grass'), ((70, 27), 'south-east-pocket'), ((52, 24), 'centre'),
               ((40, 27), 'south-lawn'), ((60, 30), 'south-pocket'), ((potion[0], potion[1] + 1), 'by-the-item-ball')]
    tour, cur = [], (2, road_y)
    for (t, name) in targets:
        assert trav[t]['foot'] == 'open', (t, name, trav[t])
        seg = path(trav, cur, t, avoid=cut)
        for i, (d, p) in enumerate(seg):
            tour.append((d, (R29, *p), name if i == len(seg) - 1 else None))
        cur = t
    # Ledge probes: one per run, from the high side.
    ledges, seen = [], set()
    for (x, y), c in sorted(trav.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        f = c['foot']
        if f not in JUMP or (x, y) in seen:
            continue
        d = JUMP[f]
        run = [(x, y)]
        while True:
            n = (run[-1][0] + abs(d[1]), run[-1][1] + abs(d[0]))
            if n in trav and trav[n]['foot'] == f:
                run.append(n)
            else:
                break
        seen |= set(run)
        mid = run[len(run) // 2]
        src = (mid[0] - d[0], mid[1] - d[1]); dst = (mid[0] + d[0], mid[1] + d[1])
        if src in trav and dst in trav and trav[src]['foot'] == 'open' and trav[dst]['foot'] == 'open':
            ledges.append((src, KEY[d], d, f'{f}-{mid[0]}-{mid[1]}'))
    blocks = []
    gate_door = next((x, y) for (x, y), c in trav.items() if c['code'] == 'D')
    blocks.append(((gate_door[0], gate_door[1] + 1), UP, 'gatehouse-door-shut'))
    for (x, y) in sorted(c for c in cut if c != potion):
        blocks.append(((x, y + 1), UP, f'cut-tree-{x}-{y}'))
    for (x, y) in signs:
        blocks.append(((x, y + 1), UP, f'sign-{x}-{y}'))
    grass = next((x, y) for (x, y), c in sorted(trav.items(), key=lambda kv: (kv[0][1], kv[0][0]))
                 if all(trav.get((x + i, y), {}).get('behavior') == 'MB_TALL_GRASS' for i in range(1, 7)) and trav[(x, y)]['foot'] == 'open')
    # Face the item ball from the cell south of it: the ball blocks, so a tap north is a turn.
    face = f'go(R29,{potion[0]},{potion[1] + 1});tap(UP);at(R29,{potion[0]},{potion[1] + 1},"facing-item-ball");'
    save = (potion[0], potion[1] + 1)
    return dict(start=start, out=out, back=back, tour=tour, ledges=ledges, blocks=blocks, signs=sorted(signs), grass=grass,
                face=face, save=save, potion=potion)

def generate(engine):
    p = plan(engine)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    moves = cmoves('ROUTE_OUT', p['out']) + cmoves('ROUTE_BACK', p['back']) + cmoves('TOUR', p['tour'])
    src = src.replace('MOVES', moves)
    src = src.replace('LEDGES', ''.join(f'ledge({s[0]},{s[1]},{k},{d[0]},{d[1]},"{t}");' for s, k, d, t in p['ledges']))
    src = src.replace('BLOCKS', ''.join(f'blocked({s[0]},{s[1]},{k},"{t}");shot("{t}");' for s, k, t in p['blocks']))
    src = src.replace('FACE_POTION', p['face'])
    rep = dict(START_X=p['start'][0], START_Y=p['start'][1], TOUR_X=2, TOUR_Y=18, GRASS_X=p['grass'][0], GRASS_Y=p['grass'][1],
               WEST_SIGN_X=p['signs'][0][0], WEST_SIGN_Y=p['signs'][0][1], EAST_SIGN_X=p['signs'][-1][0], EAST_SIGN_Y=p['signs'][-1][1],
               SAVE_X=p['save'][0], SAVE_Y=p['save'][1], POTION_X=p['potion'][0], POTION_Y=p['potion'][1], ITEM_FLAG=ITEM_FLAG, TOWN=TOWN, R29=R29, NEWBARK=NEWBARK,
               RIGHT=RIGHT, LEFT=LEFT, UP=UP, DOWN=DOWN)
    defines = ''.join(f'#define {k} {v}\n' for k, v in rep.items()) + '#define A 1\n#define B 2\n'
    return src.replace('#undef main\n', '#undef main\n' + defines, 1), p

# --------------------------------------------------------------------------- frame parity
def world(engine):
    """Route 29's native decode with Cherrygrove west of it and New Bark east of it, as the connections join them."""
    def img(layout, sec, w):
        b = (engine / f'data/layouts/{layout}/map.bin').read_bytes()
        return np.array(Tileset(engine, sec, 'cherrygrove').map_image(list(struct.unpack('<%dH' % (len(b) // 2), b)), w).convert('RGB'))
    r = img('CherrygroveRoute29Approach', 'route29_hgss', W)
    cg = img('CherrygroveCity', 'cherrygrove', TOWN_W)
    nb = img('NewBarkTown', 'new_bark', NB_W)
    ox, oy = cg.shape[1], 16 * 16
    canvas = np.zeros((max(r.shape[0], cg.shape[0], nb.shape[0] + NB_OFFSET * 16) + 2 * oy, cg.shape[1] + r.shape[1] + nb.shape[1], 3), np.int16) - 1
    canvas[oy:oy + cg.shape[0], :cg.shape[1]] = cg
    canvas[oy:oy + r.shape[0], ox:ox + r.shape[1]] = r
    canvas[oy + NB_OFFSET * 16:oy + NB_OFFSET * 16 + nb.shape[0], ox + r.shape[1]:ox + r.shape[1] + nb.shape[1]] = nb
    origin = {TOWN: (0, oy), R29: (ox, oy), NEWBARK: (ox + r.shape[1], oy + NB_OFFSET * 16)}
    return canvas, origin

def parity(engine, outdir, shots):
    canvas, origin = world(engine)
    canvas = np.where(canvas >= 0, canvas >> 3, -1)
    res = []
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True        # the player and its shadow, generously
    offset = (-112, -72)            # the player's cell sits 7 cells from the left and 4.5 from the top
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] not in origin or not f.exists():
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3      # compare in the GBA's RGB555
        ox, oy = origin[s['map']]
        def crop(dx, dy):
            x0, y0 = ox + s['x'] * 16 + dx, oy + s['y'] * 16 + dy
            if x0 < 0 or y0 < 0 or x0 + 240 > canvas.shape[1] or y0 + 160 > canvas.shape[0]:
                return None
            return canvas[y0:y0 + 160, x0:x0 + 240]
        if offset is None:
            best = None
            for dy in range(-96, -40, 4):
                for dx in range(-128, -96, 4):
                    c = crop(dx, dy)
                    if c is None:
                        continue
                    m = ((c == frame).all(-1) & ~sprite & (c[..., 0] >= 0)).mean()
                    if best is None or m > best[0]:
                        best = (m, dx, dy)
            offset = best[1:]
        c = crop(*offset)
        if c is None:
            continue
        valid = (c[..., 0] >= 0) & ~sprite
        same = ((c == frame).all(-1) & valid).sum() / max(1, valid.sum())
        res.append(dict(shot=s['shot'], map=s['map'], x=s['x'], y=s['y'], identical=round(float(same), 4)))
    return dict(camera_offset=offset, frames=res)

def main():
    engine = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    src, p = generate(engine)
    (out / 'route29_runtime.c').write_text(src)
    (out / 'plan.json').write_text(json.dumps({k: v for k, v in p.items() if k not in ('out', 'back', 'tour')} | dict(
        steps_out=len(p['out']), steps_back=len(p['back']), tour_steps=len(p['tour'])), indent=1, default=list) + '\n')
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'route29_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
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
