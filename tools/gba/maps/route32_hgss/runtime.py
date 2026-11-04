#!/usr/bin/env python3
"""Headless mGBA checks for Route 32's two maps (JohtoRoute32 north of the viaduct, JohtoRoute32South south
of it; each phase a fresh emulator process).

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/route32_hgss/runtime.py ENGINE OUT [write read menu]

write  new game; Violet City -> Route 32 -> across the map seam under the viaduct -> the Union Cave forecourt
       and back to Violet by walking, every
       step checked against the route the native traversal predicts (Gen 3 ledge rules); a walking tour into
       every area the route reaches on foot (under the viaduct included); every ledge run jumps and refuses
       the climb back; the gatehouse doorway, the cave mouth, the cuttable tree, the breakable rock, the signs
       and the sea block; tall grass with an empty party starts no battle; the signs read; the Center door
       leads into Route 32's Center and back out; the item balls are picked up and disappear; the hidden
       items are found once; ordinary save
read   cold flash reload of that save (the item flags survive)
menu   title screen -> Continue

Every capture is compared with the installed native decode at the camera position (Violet included where
the camera looks across the seam), outside the player sprite: results.json records the share of identical
pixels per frame.
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

ART = ROOT / 'gba/art/route32-hgss'
from pack import SPLIT                                       # noqa: E402
GROUP = 80
A, B, RIGHT, LEFT, UP, DOWN = 1, 2, 16, 32, 64, 128
KEY = {(1, 0): RIGHT, (-1, 0): LEFT, (0, 1): DOWN, (0, -1): UP}
VIOLET_W = 80

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
static const char *out;
static int shots;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);shots++;}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[1]==GROUP&&state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static void step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<32&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?40:8,0);frames(16,0);}
static void tap(unsigned key){frames(2,key);frames(12,0);}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static int overworld(void){unsigned cb=c->busRead32(c,sym("gMain")+4);return (cb&~1u)==(sym("CB2_Overworld")&~1u);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,B);frames(40,0);}need(!locked(),"dialogue-closes");}
struct mv{unsigned char key;unsigned short map,x,y;const char*tag;};
static void walk(const struct mv*m,int n){for(int i=0;i<n;i++){step(m[i].key);char t[96];sprintf(t,"walk-%s",m[i].tag?m[i].tag:"step");at(m[i].map,m[i].x,m[i].y,t);need(overworld()&&!locked(),"walk-no-interruption");if(m[i].tag)shot(m[i].tag);}}
static void ledge(unsigned mi,unsigned mn,unsigned x,unsigned y,unsigned key,int dx,int dy,const char*tag){char t[64];go(mi,x,y);step(key);sprintf(t,"%s-jump",tag);at(mn,x+2*dx,y+2*dy,t);unsigned back=key==DOWN?UP:key==UP?DOWN:key==LEFT?RIGHT:LEFT;step(back);sprintf(t,"%s-no-climb",tag);at(mn,x+2*dx,y+2*dy,t);}
static void blocked(unsigned mi,unsigned mn,unsigned x,unsigned y,unsigned key,const char*tag){go(mi,x,y);step(key);at(mn,x,y,tag);}
static void read_sign(unsigned mi,unsigned x,unsigned y,const char*tag){go(mi,x,y+1);tap(UP);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();}
static void ball(unsigned mi,unsigned mn,unsigned x,unsigned y,unsigned fx,unsigned fy,unsigned key,unsigned flag,const char*tag){char t[64];go(mi,fx,fy);tap(key);sprintf(t,"%s-facing",tag);at(mn,fx,fy,t);need(call("FlagGet",flag)==0,tag);frames(1,A);frames(150,0);need(locked(),tag);shot(tag);close_dialog();frames(60,0);need(call("FlagGet",flag)==1,tag);step(key);sprintf(t,"%s-gone",tag);at(mn,x,y,t);shot(t);}
static void hidden(unsigned mi,unsigned mn,unsigned bx,unsigned by,unsigned fx,unsigned fy,unsigned key,unsigned flag,const char*tag){char t[64];go(mi,bx,by);step(key);sprintf(t,"%s-facing",tag);at(mn,fx,fy,t);need(call("FlagGet",flag)==0,tag);frames(1,A);frames(150,0);need(locked(),tag);shot(tag);close_dialog();frames(60,0);need(call("FlagGet",flag)==1,tag);frames(1,A);frames(120,0);need(!locked(),tag);}
MOVES
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read|menu\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"route32-hgss");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/route32.sav",argv[3]);
 if(!strcmp(argv[4],"read")||!strcmp(argv[4],"menu")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;}
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);
 if(!strcmp(argv[4],"menu")){
  frames(1,8);frames(180,0);frames(1,A);frames(300,0);frames(1,A);frames(180,0);shot("continue-menu");frames(1,A);frames(300,0);shot("title-continue");at(R32,SAVE_X,SAVE_Y,"title-continue");
 }else if(!strcmp(argv[4],"read")){
  unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(R32,SAVE_X,SAVE_Y,"cold-reload");
  FLAGS_SURVIVE
 }else{
  call("MapProof_Boot",0);frames(240,0);observe("new-game");
  {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
  need(call("CalculatePlayerPartyCount",0)==0,"empty-party");
  // Violet -> Route 32 -> the Union Cave forecourt on foot, every step checked; then back to Violet.
  go(VIOLETI,START_X,START_Y);at(VIOLET,START_X,START_Y,"start-violet");shot("violet-start");
  walk(ROUTE_OUT,sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0]));
  walk(ROUTE_BACK,sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0]));
  printf("{\"walked\":\"Violet-Route32-south-and-back\",\"steps\":%d}\n",(int)(sizeof(ROUTE_OUT)/sizeof(ROUTE_OUT[0])+sizeof(ROUTE_BACK)/sizeof(ROUTE_BACK[0])));
  go(R32I,TOUR_X,TOUR_Y);at(R32,TOUR_X,TOUR_Y,"tour-start");
  walk(TOUR,sizeof(TOUR)/sizeof(TOUR[0]));
  // The Center: in through its door, out again onto the door's front.
  go(R32SI,DOOR_X,DOOR_Y+1);tap(UP);step(UP);frames(240,0);observe("center-inside");shot("center-inside");need(state[2]==CENTER,"center-entered");
  step(DOWN);frames(240,0);at(R32S,DOOR_X,DOOR_Y+1,"center-exit");shot("center-exit");
  BALLS
  HIDDEN
  printf("{\"items\":\"balls picked up and gone, hidden items found once\"}\n");
  LEDGES
  BLOCKS
  go(GRASS_MI,GRASS_X,GRASS_Y);for(int i=0;i<GRASS_N;i++){step(GRASS_KEY);need(overworld()&&!locked(),"grass-no-battle");}shot("tall-grass");
  printf("{\"tall_grass_steps_without_battle\":%d}\n",GRASS_N);
  SIGNS
  go(R32I,SAVE_X,SAVE_Y);at(R32,SAVE_X,SAVE_Y,"save-spot");shot("save-spot");
  unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 }
 c->deinit(c);return 0;
}
'''

def loc(nums, x, y):
    """Native (x, y) -> (proof index macro, map number, local x, local y)."""
    if y < SPLIT:
        return 'R32I', nums['JohtoRoute32'], x, y
    return 'R32SI', nums['JohtoRoute32South'], x, y - SPLIT

def load_trav():
    t = json.loads((ART / 'source/pack/traversal.json').read_text())
    return {(c['x'], c['y']): c for c in t}

JUMP = {'ledge_south': (0, 1), 'ledge_east': (1, 0), 'ledge_west': (-1, 0)}

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

def path_ok(trav, a, b, objs):
    try:
        path(trav, a, b, avoid=objs); return True
    except AssertionError:
        return False

def cmoves(name, moves):
    rows = ['{%d,%d,%d,%d,%s}' % (KEY[d], m, x, y, f'"{tag}"' if tag else '0') for (d, (m, x, y), tag) in moves]
    return f'static const struct mv {name}[]={{' + ','.join(rows) + '};\n'

def map_numbers(engine):
    g = json.loads((engine / 'data/maps/map_groups.json').read_text())
    grp = next(v for k, v in g.items() if isinstance(v, list) and 'VioletCity' in v)
    return {n: grp.index(n) for n in ('VioletCity', 'JohtoRoute32', 'JohtoRoute32South', 'Route32PokemonCenter')}

def proof_index(engine, map_id):
    """Index of a map in the engine's test-only warp list (MapProof_Enter takes this, not the map number)."""
    import re
    lst = re.search(r'sMapProofMaps\[\] = \{([^}]*)\}', (engine / 'src/apocrypha_map_proof.c').read_text()).group(1)
    return [m.strip() for m in lst.split(',')].index(map_id)

def plan(engine, nums):
    R32 = nums['JohtoRoute32']
    VIOLET = nums['VioletCity']
    trav = load_trav()
    evn = json.loads((engine / 'data/maps/JohtoRoute32/map.json').read_text())
    evs = json.loads((engine / 'data/maps/JohtoRoute32South/map.json').read_text())
    native = lambda e, dy: {**e, 'y': e['y'] + dy}
    ev = dict(bg_events=[native(b, 0) for b in evn['bg_events']] + [native(b, SPLIT) for b in evs['bg_events']],
              object_events=[native(o, 0) for o in evn['object_events']] + [native(o, SPLIT) for o in evs['object_events']])
    M = lambda x, y: (loc(nums, x, y)[1], x, loc(nums, x, y)[3])
    signs = [(b['x'], b['y']) for b in ev['bg_events'] if b['type'] == 'sign']
    hidden = [(b['x'], b['y'], b['flag']) for b in ev['bg_events'] if b['type'] == 'hidden_item']
    balls = [(o['x'], o['y'], o['flag']) for o in ev['object_events'] if o['graphics_id'] == 'OBJ_EVENT_GFX_ITEM_BALL']
    objs = {(o['x'], o['y']) for o in ev['object_events']}
    vb = (engine / 'data/layouts/VioletCity/map.bin').read_bytes()
    violet = np.array(struct.unpack('<%dH' % (len(vb) // 2), vb)).reshape(-1, VIOLET_W)
    vx = min(Rf.VIOLET_ROAD) + Rf.VIOLET_SHIFT + 1                # Violet's road, middle column
    assert not any((violet[y, vx] >> 10) & 3 for y in range(violet.shape[0] - 4, violet.shape[0]))
    start = (vx, violet.shape[0] - 4)
    x32 = vx - Rf.VIOLET_SHIFT
    out = [((0, 1), (VIOLET, vx, violet.shape[0] - 3 + i), None) for i in range(3)]
    out += [((0, 1), (R32, x32, 0), 'cross-into-route32')]
    door = next(p for p, c in trav.items() if c['code'] == 'D')
    south = max((p for p, c in trav.items() if c['foot'] == 'open' and path_ok(trav, (x32, 0), p, objs)), key=lambda p: (p[1], -p[0]))
    seg = path(trav, (x32, 0), south, avoid=objs)
    for i, (d, p) in enumerate(seg):
        out.append((d, M(*p), f'route-{i:03d}' if i % 12 == 11 or i == len(seg) - 1 else None))
    back = []
    seg = path(trav, south, (x32, 0), avoid=objs)
    for i, (d, p) in enumerate(seg):
        back.append((d, M(*p), f'back-{i:03d}' if i % 24 == 23 else None))
    back += [((0, -1), (VIOLET, vx, violet.shape[0] - 1), 'cross-back-into-violet')]
    reach = set()
    q = deque([(x32, 0)]); reach.add((x32, 0))
    while q:
        pnt = q.popleft()
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (pnt[0] + d[0], pnt[1] + d[1])
            if n in trav and trav[n]['foot'] in JUMP:
                if JUMP[trav[n]['foot']] != d:
                    continue
                n = (n[0] + d[0], n[1] + d[1])
            if n in trav and trav[n]['foot'] == 'open' and n not in objs and n not in reach:
                reach.add(n); q.append(n)
    picks = [(x32, 0)]
    cand = sorted(reach)
    while len(picks) < 24:
        picks.append(max(cand, key=lambda c: min(abs(c[0] - p_[0]) + abs(c[1] - p_[1]) for p_ in picks)))
    targets = [(t, f'area-{t[0]}-{t[1]}') for t in picks[1:]]
    ordered, cur_ = [], (x32, 0)
    while targets:
        t = min(targets, key=lambda t: abs(t[0][0] - cur_[0]) + abs(t[0][1] - cur_[1]))
        targets.remove(t); ordered.append(t); cur_ = t[0]
    tour, cur = [], (x32, 0)
    for (t, name) in ordered:
        seg = path(trav, cur, t, avoid=objs)
        for i, (d, p) in enumerate(seg):
            tour.append((d, M(*p), name if i == len(seg) - 1 else None))
        cur = t
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
        if trav.get(src, {}).get('foot') == 'open' and trav.get(dst, {}).get('foot') == 'open' and dst not in objs \
                and path_ok(trav, (x32, 0), src, objs):
            ledges.append((src, KEY[d], d, f'{f}-{mid[0]}-{mid[1]}'))
    blocks = []
    for code, name in (('w', 'gatehouse-doorway-shut'), ('C', 'cave-mouth-shut')):
        for (x, y), c in sorted(trav.items()):
            if c['code'] != code:
                continue
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s = (x - d[0], y - d[1])
                if trav.get(s, {}).get('foot') == 'open' and path_ok(trav, (x32, 0), s, objs):
                    blocks.append((s, KEY[d], f'{name}-{x}-{y}')); break
    for o in ev['object_events']:
        if o['graphics_id'] in ('OBJ_EVENT_GFX_CUTTABLE_TREE', 'OBJ_EVENT_GFX_BREAKABLE_ROCK'):
            for d in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                s = (o['x'] - d[0], o['y'] - d[1])
                if trav.get(s, {}).get('foot') == 'open' and s not in objs and path_ok(trav, (x32, 0), s, objs):
                    blocks.append((s, KEY[d], f"{o['graphics_id'][14:].lower()}-{o['x']}-{o['y']}")); break
    for (x, y) in signs:
        blocks.append(((x, y + 1), UP, f'sign-{x}-{y}'))
    water = sorted(p for p, c in trav.items() if c['foot'] == 'water')
    for p in water[::max(1, len(water) // 4)]:
        for d in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            s = (p[0] - d[0], p[1] - d[1])
            if trav.get(s, {}).get('foot') == 'open' and s not in objs and path_ok(trav, (x32, 0), s, objs):
                blocks.append((s, KEY[d], f'sea-edge-{p[0]}-{p[1]}')); break
    grass = None
    for (x, y), c in sorted(trav.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if c['foot'] == 'open' and all(trav.get((x, y + i), {}).get('behavior') == 'MB_TALL_GRASS' for i in range(1, 7)) \
                and path_ok(trav, (x32, 0), (x, y), objs):
            grass = (x, y, DOWN, 6); break
    def facing(x, y):                                           # the test warps to an open cell beside the item
        return next(((x - d[0], y - d[1], KEY[d]) for d in ((0, -1), (0, 1), (-1, 0), (1, 0))
                    if trav.get((x - d[0], y - d[1]), {}).get('foot') == 'open' and (x - d[0], y - d[1]) not in objs), None)
    ball_plan = [(x, y, *facing(x, y), f) for x, y, f in balls if facing(x, y)]
    def approach(x, y):                                         # two open cells in a line: walk into the facing cell
        open_ = lambda c: trav.get(c, {}).get('foot') == 'open' and c not in objs
        return next(((x - 2 * d[0], y - 2 * d[1], x - d[0], y - d[1], KEY[d]) for d in ((0, -1), (0, 1), (-1, 0), (1, 0))
                     if open_((x - d[0], y - d[1])) and open_((x - 2 * d[0], y - 2 * d[1]))), None)
    hidden_plan = [(*approach(x, y), f, x, y) for x, y, f in hidden if approach(x, y)]
    surf_only = [dict(item=f, cell=[x, y]) for x, y, f in balls if not facing(x, y)] + \
                [dict(item=f, cell=[x, y]) for x, y, f in hidden if not approach(x, y)]      # no open land beside it
    save = (x32, Rf.ROW0 + 2)
    return dict(start=start, out=out, back=back, tour=tour, ledges=ledges, blocks=blocks, signs=sorted(signs), grass=grass,
                balls=ball_plan, hidden=hidden_plan, surf_only=surf_only, save=save, x32=x32, door=door, south=south)

def flag_values(engine):
    s = (engine / 'include/constants/flags.h').read_text()
    import re
    out = {}
    for m in re.finditer(r'#define (FLAG_\w*APOC_ROUTE32\w*) FLAG_UNUSED_(0x[0-9A-F]+)', s):
        out[m.group(1)] = int(m.group(2), 16)
    return out

def generate(engine):
    nums = map_numbers(engine)
    p = plan(engine, nums)
    fv = flag_values(engine)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c'))
    src = src.replace('MOVES', cmoves('ROUTE_OUT', p['out']) + cmoves('ROUTE_BACK', p['back']) + cmoves('TOUR', p['tour']))
    L = lambda x, y: loc(nums, x, y)                    # native -> (index macro, map number, local x, local y)
    def ly(x, y): return L(x, y)[3]
    # every check runs in the map that holds its cell; tags keep native coordinates
    src = src.replace('LEDGES', ''.join(f'ledge({L(*s)[0]},{L(*s)[1]},{s[0]},{ly(*s)},{k},{d[0]},{d[1]},"{t}");' for s, k, d, t in p['ledges']
                                        if L(*s)[1] == L(s[0] + 2 * d[0], s[1] + 2 * d[1])[1]))
    src = src.replace('BLOCKS', ''.join(f'blocked({L(*s)[0]},{L(*s)[1]},{s[0]},{ly(*s)},{k},"{t}");shot("{t}");' for s, k, t in p['blocks']))
    src = src.replace('BALLS', ''.join(f'ball({L(fx, fy)[0]},{L(fx, fy)[1]},{x},{ly(x, y)},{fx},{ly(fx, fy)},{k},{fv[f]},"item-ball-{x}-{y}");'
                                       for x, y, fx, fy, k, f in p['balls']))
    src = src.replace('HIDDEN', ''.join(f'hidden({L(bx, by)[0]},{L(bx, by)[1]},{bx},{ly(bx, by)},{fx},{ly(fx, fy)},{k},{fv[f]},"hidden-{x}-{y}");'
                                        for bx, by, fx, fy, k, f, x, y in p['hidden']))
    src = src.replace('SIGNS', ''.join(f'read_sign({L(x, y + 1)[0]},{x},{ly(x, y + 1) - 1},"read-sign-{x}-{y}");' for x, y in p['signs']))
    tested = {f for *_, f in p['balls']} | {h[5] for h in p['hidden']}
    src = src.replace('FLAGS_SURVIVE', 'need(' + '&&'.join(f'call("FlagGet",{v})==1' for k, v in fv.items() if k in tested) + ',"item-flags-survive-save");')
    g = p['grass']
    # MapProof_Enter takes the index into its own list (the Apocrypha group's order); the state reports map numbers.
    rep = dict(START_X=p['start'][0], START_Y=p['start'][1], TOUR_X=p['x32'], TOUR_Y=0, GRASS_X=g[0], GRASS_Y=ly(g[0], g[1]),
               GRASS_MI=L(g[0], g[1])[0], GRASS_KEY=g[2], GRASS_N=g[3],
               SAVE_X=p['save'][0], SAVE_Y=p['save'][1], DOOR_X=p['door'][0], DOOR_Y=p['door'][1] - SPLIT, GROUP=GROUP,
               R32=nums['JohtoRoute32'], R32I=proof_index(engine, 'MAP_JOHTO_ROUTE32'),
               R32S=nums['JohtoRoute32South'], R32SI=proof_index(engine, 'MAP_JOHTO_ROUTE32_SOUTH'), VIOLET=nums['VioletCity'],
               VIOLETI=proof_index(engine, 'MAP_VIOLET_CITY'),
               CENTER=nums['Route32PokemonCenter'], RIGHT=RIGHT, LEFT=LEFT, UP=UP, DOWN=DOWN)
    defines = ''.join(f'#define {k} {v}\n' for k, v in rep.items()) + '#define A 1\n#define B 2\n'
    return src.replace('#undef main\n', '#undef main\n' + defines, 1), p, nums

# --------------------------------------------------------------------------- frame parity
def world(engine, nums):
    """Route 32's native decode with Violet above it, as the connection joins them."""
    from seams import layout
    def img(layout_id):
        words, t = layout(engine, layout_id)
        return np.array(t.map_image(words.ravel().tolist(), words.shape[1]).convert('RGB'))
    r = np.concatenate([img('LAYOUT_JOHTO_ROUTE32'), img('LAYOUT_JOHTO_ROUTE32_SOUTH')])
    v = img('LAYOUT_VIOLET_CITY')
    pad = 16 * 16
    canvas = np.zeros((pad + v.shape[0] + r.shape[0] + pad, pad + v.shape[1] + pad, 3), np.int16) - 1
    canvas[pad:pad + v.shape[0], pad:pad + v.shape[1]] = v
    ox = pad + Rf.VIOLET_SHIFT * 16
    canvas[pad + v.shape[0]:pad + v.shape[0] + r.shape[0], ox:ox + r.shape[1]] = r
    return canvas, {nums['JohtoRoute32']: (ox, pad + v.shape[0]), nums['JohtoRoute32South']: (ox, pad + v.shape[0] + SPLIT * 16),
                    nums['VioletCity']: (pad, pad)}

def parity(engine, nums, outdir, shots):
    canvas, origin = world(engine, nums)
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
    src, p, nums = generate(engine)
    (out / 'route32_runtime.c').write_text(src)
    (out / 'plan.json').write_text(json.dumps({k: v for k, v in p.items() if k not in ('out', 'back', 'tour')} | dict(
        steps_out=len(p['out']), steps_back=len(p['back']), tour_steps=len(p['tour']), map_numbers=nums), indent=1, default=list) + '\n')
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'route32_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
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
                           capture_output=True, text=True, timeout=7200)
        (out / (phase + '.jsonl')).write_text(r.stdout)
        obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        for file in out.glob('*.ppm'):
            Image.open(file).save(file.with_suffix('.png')); file.unlink()
        results.append(dict(phase=phase, exit_code=r.returncode, stderr=r.stderr[-2000:], observations=len(obs),
                            parity=parity(engine, nums, out, [o for o in obs if 'shot' in o])))
        (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
        print(phase, r.returncode, r.stderr[-600:], flush=True)
        if r.returncode != 0:
            sys.exit(r.returncode)
    print('All phases passed.')

if __name__ == '__main__':
    main()
