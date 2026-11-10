#!/usr/bin/env python3
"""Headless mGBA checks for Canalave City (the shared runtime.c harness; each phase a fresh emulator).

    python3 tools/gba/maps/canalave_city/runtime.py CACHE ENGINE OUT [write read]

write  new game; warp into Canalave; every walkable land cell away from the wandering residents: a step in
       each of the four directions moves or stays as the native grid predicts (Platinum's permissions), and
       steps back; every door leads to its interior and back out below the door; the Center's stairs go up
       and down; the nurse and the clerk answer; the signs, the shut Harbor Inn door, the gate notice and
       Sailor Eldritch answer; a screenshot tour; an ordinary save
read   cold flash reload of that save

Every tour capture is compared with the installed native decode at the camera position outside the player,
the residents' cells and the animated water: results.json records the share of identical pixels per frame.
"""
from __future__ import annotations
import json, os, shlex, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import install as I                                           # noqa: E402
import cn_compose as C                                        # noqa: E402
import cn_cleanup as CL                                       # noqa: E402
from cn_reference import W, H, MARGIN                         # noqa: E402
from tiles import Tileset                                     # noqa: E402

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
#define A 1
#define B 2
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
DEFINES
static const char *out;
static void shot(const char*t){screenshot(out,t);call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");printf("{\"shot\":\"%s\",\"map\":%u,\"x\":%u,\"y\":%u}\n",t,c->busRead32(c,a+8),c->busRead32(c,a+12),c->busRead32(c,a+16));fflush(stdout);}
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static void need(int ok,const char*tag){if(!ok){fprintf(stderr,"FAILED %s (map %u at %u,%u)\n",tag,state[2],state[3],state[4]);shot(tag);exit(40);}}
static void at(unsigned map,unsigned x,unsigned y,const char*tag){observe(tag);need(state[2]==map&&state[3]==x&&state[4]==y,tag);}
static void pos(unsigned*m,unsigned*x,unsigned*y){call("MapProof_ReadState",0);unsigned a=sym("gMapProofState");*m=c->busRead32(c,a+8);*x=c->busRead32(c,a+12);*y=c->busRead32(c,a+16);}
static int step(unsigned key){unsigned m0,x0,y0,m1,x1,y1;pos(&m0,&x0,&y0);int moved=0;for(int t=0;t<20&&!moved;t++){frames(2,key);pos(&m1,&x1,&y1);moved=(m1!=m0||x1!=x0||y1!=y0);}frames(moved?24:4,0);return moved;}
static int locked(void){return call("ArePlayerFieldControlsLocked",0);}
static void close_dialog(void){for(int i=0;i<40&&locked();i++){frames(1,A);frames(40,0);}need(!locked(),"dialogue-closes");}
static void talk(unsigned x,unsigned y,unsigned key,const char*tag){go(CITY,x,y);frames(2,key);frames(12,0);frames(1,A);frames(120,0);need(locked(),tag);shot(tag);close_dialog();printf("{\"talk\":\"%s\",\"ok\":1}\n",tag);fflush(stdout);}
static void door(unsigned x,unsigned y,unsigned inside,const char*name){char t[64];go(CITY,x,y+1);at(CITY_NUM,x,y+1,name);
 step(UP);frames(300,0);observe(name);need(state[2]==inside,name);sprintf(t,"inside-%s",name);shot(t);
 step(DOWN);frames(300,0);observe(name);need(state[2]==CITY_NUM&&state[3]==x&&state[4]==y+1,name);sprintf(t,"out-%s",name);shot(t);
 printf("{\"door\":\"%s\",\"ok\":1}\n",name);fflush(stdout);}
struct edge{unsigned char x,y,mask;};
static const struct edge edges[]={EDGES};
static const unsigned keys[4]={RIGHT,LEFT,DOWN,UP};static const int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};static const unsigned back[4]={LEFT,RIGHT,UP,DOWN};
int main(int argc,char**argv){
 if(argc!=5){fprintf(stderr,"runtime ROM SYMBOLS OUT write|read\n");return 2;}
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"canalave-city");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 char flash[2048];snprintf(flash,sizeof(flash),"%s/canalave.sav",argv[3]);
 if(!strcmp(argv[4],"read")){unsigned char data[131072];f=fopen(flash,"rb");if(!f||fread(data,1,sizeof(data),f)!=sizeof(data))return 6;fclose(f);if(!c->savedataRestore(c,data,sizeof(data),false))return 7;
  c->reset(c);frames(600,0);unsigned s=call("LoadGameSave",0);need(s==1,"load-status");call("MapProof_Resume",0);frames(240,0);shot("cold-reload");at(CITY_NUM,SAVE_X,SAVE_Y,"cold-reload");printf("{\"reload\":1}\n");c->deinit(c);return 0;}
 c->reset(c);frames(600,0);
 call("MapProof_Boot",0);frames(240,0);observe("new-game");
 {static const unsigned char nm[]={0xCA,0xC6,0xBB,0xD3,0xBF,0xCC,0xFF,0xFF};unsigned sb2=c->busRead32(c,sym("gSaveBlock2Ptr"));for(int i=0;i<8;i++)c->busWrite8(c,sb2+i,nm[i]);}
 go(CITY,SAVE_X,SAVE_Y);at(CITY_NUM,SAVE_X,SAVE_Y,"arrive");need(state[0]==REGION_SINNOH_ID,"region-sinnoh");shot("arrive");
 // the screenshot tour
TOUR
 // traversal: every listed cell, four directions
 int bad=0,tested=0;
 for(unsigned i=0;i<sizeof(edges)/sizeof(edges[0]);i++){
  go(CITY,edges[i].x,edges[i].y);unsigned m,x,y;pos(&m,&x,&y);if(m!=CITY_NUM||x!=edges[i].x||y!=edges[i].y){printf("{\"edge_arrive_failed\":[%u,%u]}\n",edges[i].x,edges[i].y);bad++;continue;}
  for(int d=0;d<4;d++){int want=(edges[i].mask>>d)&1;int moved=step(keys[d]);pos(&m,&x,&y);
   int ok=want?(moved&&m==CITY_NUM&&x==(unsigned)(edges[i].x+dx[d])&&y==(unsigned)(edges[i].y+dy[d])):(!moved);tested++;
   if(!ok){bad++;printf("{\"edge_mismatch\":[%u,%u,%d],\"want\":%d,\"got\":[%u,%u,%u]}\n",edges[i].x,edges[i].y,d,want,m,x,y);fflush(stdout);}
   if(moved){if(m!=CITY_NUM){go(CITY,edges[i].x,edges[i].y);}else{step(back[d]);pos(&m,&x,&y);if(x!=edges[i].x||y!=edges[i].y)go(CITY,edges[i].x,edges[i].y);}}}
 }
 printf("{\"edges_tested\":%d,\"edge_mismatches\":%d}\n",tested,bad);fflush(stdout);
 // doors
DOORS
 // the Center: upstairs and back, the nurse
 go(CENTER,8,9);at(CENTER_NUM,8,9,"center");shot("center-1f");
 go(CENTER,2,8);step(LEFT);frames(300,0);observe("upstairs");need(state[2]==UPSTAIRS_NUM,"center-upstairs");shot("center-2f");
 go(CENTER,8,4);frames(2,UP);frames(12,0);frames(1,A);frames(120,0);need(locked(),"nurse");shot("nurse");for(int i=0;i<60&&locked();i++){frames(1,B);frames(60,0);}need(!locked(),"nurse-done");printf("{\"talk\":\"nurse\",\"ok\":1}\n");
 go(MART,2,3);frames(2,LEFT);frames(12,0);frames(1,A);frames(120,0);need(locked(),"clerk");shot("clerk");for(int i=0;i<30&&locked();i++){frames(1,B);frames(60,0);}need(!locked(),"clerk-done");printf("{\"talk\":\"clerk\",\"ok\":1}\n");
 // signs and notices
TALKS
 // ordinary save
 go(CITY,SAVE_X,SAVE_Y);at(CITY_NUM,SAVE_X,SAVE_Y,"save-spot");
 unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{\"save_status\":%u,\"flash_bytes\":%zu}\n",status,size);
 need(bad==0,"traversal-matches-the-native-grid");
 c->deinit(c);return 0;
}
'''

SAVE = I.N(15, 12)
# where the player stands under or on the top layer (Platinum cells)
LAYER_SHOTS = {'behind-east-house': (20, 24), 'behind-mart': (21, 33), 'bridge-middle': (15, 20), 'bridge-south-rail': (15, 22),
               'bridge-north-rail': (14, 19), 'gym-door': (7, 28), 'statue': (3, 18), 'dock': (12, 46), 'canal-edge': (11, 30),
               'behind-center': (26, 15), 'gate': (31, 50), 'south-clearing': (4, 60)}

def plan(cache, engine):
    """Predicted on-foot traversal from the installed map's own blocks, and the cells to test."""
    words = np.frombuffer((engine / 'data/layouts/CanalaveCity/map.bin').read_bytes(), '<u2').reshape(H, W)
    ts = Tileset(engine, 'canalave_city', 'canalave_city')
    coll = (words >> 10) & 3
    elev = words >> 12
    beh = np.array([[(ts.attrs[int(m) >= 512][int(m) - 512 if int(m) >= 512 else int(m)]) & 0xFF for m in row] for row in (words & 1023)])
    mj = json.loads((engine / 'data/maps/CanalaveCity/map.json').read_text())
    npcs = [(o['x'], o['y'], o['movement_range_x'], o['movement_range_y'], o['movement_type']) for o in mj['object_events']]
    doors = {(w['x'], w['y']) for w in mj['warp_events']}
    def foot(x, y):
        return 0 <= x < W and 0 <= y < H and coll[y, x] == 0 and beh[y, x] != C.MB_OCEAN_WATER
    def near_npc(x, y):
        for nx, ny, rx, ry, mv in npcs:
            r = 2 if 'WANDER' in mv else 1
            if abs(x - nx) <= max(rx, 1) + r - 1 and abs(y - ny) <= max(ry, 1) + r - 1:
                return True
        return False
    edges = []
    for y in range(H):
        for x in range(W):
            if not foot(x, y) or (x, y) in doors or near_npc(x, y):
                continue
            mask = 0; skip = False
            for d, (ax, ay) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
                tx, ty = x + ax, y + ay
                if (tx, ty) in doors: skip = True
                if foot(tx, ty) and elev[ty, tx] == elev[y, x]:
                    mask |= 1 << d
            if not skip:
                edges.append((x, y, mask))
    return dict(edges=edges, coll=coll, beh=beh, elev=elev, npcs=npcs, doors=doors, mj=mj)

def generate(cache, engine, proof):
    p = plan(cache, engine)
    city = proof['MAP_CANALAVE_CITY']
    defs = [f'#define CITY {city}', f'#define CITY_NUM {city}', f'#define SAVE_X {SAVE[0]}', f'#define SAVE_Y {SAVE[1]}',
            f'#define CENTER {proof["MAP_CANALAVE_POKEMON_CENTER"]}', f'#define CENTER_NUM {proof["MAP_CANALAVE_POKEMON_CENTER"]}',
            f'#define UPSTAIRS_NUM {proof["MAP_CANALAVE_CENTER_UPSTAIRS"]}', f'#define MART {proof["MAP_CANALAVE_MART"]}', '#define REGION_SINNOH_ID 4']
    doors = ''.join(f' door({I.N(*cell)[0]},{I.N(*cell)[1]},{proof["MAP_" + I.snake(name)]},"{name}");\n' for name, cell, *_ in I.DOORS)
    talks = ''
    for cell, (_, script) in CL.SIGNS.items():
        x, y = I.N(*cell); talks += f' talk({x},{y + 1},UP,"{script}");\n'
    x, y = I.N(*I.SHUT_DOOR); talks += f' talk({x},{y + 1},UP,"harbor-inn-door");\n'
    x, y = I.N(*I.GATE[0]); talks += f' talk({x},{y},RIGHT,"gate");\n'
    x, y = I.N(13, 46); talks += f' talk({x - 1},{y},RIGHT,"sailor-eldritch");\n'
    tour = ''
    pts = [(x, y) for y in range(MARGIN + 3, H - MARGIN, 9) for x in range(MARGIN + 4, W - MARGIN, 8)]
    used = []
    walk = [(e[0], e[1]) for e in p['edges']]
    for tx, ty in pts:
        bx, by = min(walk, key=lambda c: (c[0] - tx) ** 2 + (c[1] - ty) ** 2)
        if (bx, by) not in used:
            used.append((bx, by)); tour += f' go(CITY,{bx},{by});shot("tour-{bx}-{by}");\n'
    for name, (px, pz) in LAYER_SHOTS.items():
        x, y = I.N(px, pz); tour += f' go(CITY,{x},{y});at(CITY_NUM,{x},{y},"{name}");shot("layer-{name}");\n'
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c')).replace('DEFINES', '\n'.join(defs))
    src = src.replace('EDGES', ','.join('{%d,%d,%d}' % e for e in p['edges'])).replace('DOORS\n', doors).replace('TALKS\n', talks).replace('TOUR\n', tour)
    return src, p

def decode(engine):
    ts = Tileset(engine, 'canalave_city', 'canalave_city')
    words = [int(x) for x in np.frombuffer((engine / 'data/layouts/CanalaveCity/map.bin').read_bytes(), '<u2')]
    return np.array(ts.map_image(words, W).convert('RGB')), ts, np.array(words).reshape(H, W)

def water_mask(ts, words):
    """Pixels drawn from the animated deep-water tiles."""
    m = np.zeros((H * 16, W * 16), bool)
    for r in range(H):
        for x in range(W):
            mid = int(words[r, x]) & 1023
            ent = ts.blocks[mid >= 512][mid - 512 if mid >= 512 else mid]
            for q in range(4):
                if (ent[q] & 1023) in (1, 2) and not (ent[4 + q] & 1023):
                    m[r * 16 + (q // 2) * 8:r * 16 + (q // 2) * 8 + 8, x * 16 + (q % 2) * 8:x * 16 + (q % 2) * 8 + 8] = True
                elif (ent[q] & 1023) in (1, 2):
                    m[r * 16 + (q // 2) * 8:r * 16 + (q // 2) * 8 + 8, x * 16 + (q % 2) * 8:x * 16 + (q % 2) * 8 + 8] = True
    return m

def parity(engine, outdir, shots, city, npcs):
    img, ts, words = decode(engine)
    wm = water_mask(ts, words)
    for nx, ny, rx, ry, mv in npcs:                      # residents and where they may stand
        r = 1 if 'WANDER' in mv else 0
        wm[max(0, (ny - ry - r - 1)) * 16:(ny + ry + r + 1) * 16, max(0, nx - rx - r) * 16:(nx + rx + r + 1) * 16] = True
    pad = 16 * 16
    canvas = np.full((img.shape[0] + 2 * pad, img.shape[1] + 2 * pad, 3), -1, np.int16)
    canvas[pad:pad + img.shape[0], pad:pad + img.shape[1]] = img
    canvas = np.where(canvas >= 0, canvas >> 3, -1)
    skip = np.ones((img.shape[0] + 2 * pad, img.shape[1] + 2 * pad), bool); skip[pad:pad + img.shape[0], pad:pad + img.shape[1]] = wm
    sprite = np.zeros((160, 240), bool); sprite[40:96, 96:144] = True
    res = []
    for s in shots:
        f = outdir / f"{s['shot']}.png"
        if s['map'] != city or not f.exists() or not s['shot'].startswith(('tour', 'arrive', 'out-')):
            continue
        frame = np.array(Image.open(f).convert('RGB')).astype(np.int16) >> 3
        x0, y0 = pad + s['x'] * 16 - 112, pad + s['y'] * 16 - 72
        cc = canvas[y0:y0 + 160, x0:x0 + 240]
        valid = (cc[..., 0] >= 0) & ~sprite & ~skip[y0:y0 + 160, x0:x0 + 240]
        res.append(dict(shot=s['shot'], x=s['x'], y=s['y'], identical=round(float(((cc == frame).all(-1) & valid).sum() / max(1, valid.sum())), 4)))
    return res

def main():
    cache, engine, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    phases = sys.argv[4:] or ['write', 'read']
    out.mkdir(parents=True, exist_ok=True)
    s = (engine / 'src/apocrypha_map_proof.c').read_text()
    import re
    ids = [x.strip() for x in re.search(r'const u16 sMapProofMaps\[\] = \{(.*?)\};', s).group(1).split(',')]
    proof = {n: i for i, n in enumerate(ids)}
    src, p = generate(cache, engine, proof)
    (out / 'canalave_runtime.c').write_text(src)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(out / 'canalave_runtime.c'), *flags, '-o', str(out / 'runtime')], check=True)
    lines = subprocess.check_output([shutil.which('arm-none-eabi-nm'), str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'MapProof_Resume', 'gMapProofState', 'TrySavingData', 'LoadGameSave',
              'ArePlayerFieldControlsLocked', 'gSaveBlock2Ptr'}
    symbols = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    assert symbols.keys() == wanted, wanted - symbols.keys()
    (out / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in symbols.items()))
    results = {}
    for ph in phases:
        r = subprocess.run([str(out / 'runtime'), str(engine / 'pokeemerald.gba'), str(out / 'symbols.txt'), str(out), ph],
                           capture_output=True, text=True, timeout=7200)
        (out / f'run-{ph}.jsonl').write_text(r.stdout)
        for file in out.glob('*.ppm'):
            Image.open(file).save(file.with_suffix('.png')); file.unlink()
        obs = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
        res = dict(exit_code=r.returncode, stderr=r.stderr[-2000:])
        if ph == 'write':
            res['edges'] = next((o for o in obs if 'edges_tested' in o), None)
            res['edge_mismatches'] = [o for o in obs if 'edge_mismatch' in o or 'edge_arrive_failed' in o]
            res['doors'] = [o['door'] for o in obs if 'door' in o]
            res['talks'] = [o['talk'] for o in obs if 'talk' in o]
            res['save'] = next((o for o in obs if 'save_status' in o), None)
            res['parity'] = parity(engine, out, [o for o in obs if 'shot' in o], proof['MAP_CANALAVE_CITY'], p['npcs'])
        else:
            res['reload'] = any('reload' in o for o in obs)
        results[ph] = res
        print(ph, r.returncode, r.stderr[-400:])
    (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
    sys.exit(max(v['exit_code'] for v in results.values()))

if __name__ == '__main__':
    main()
