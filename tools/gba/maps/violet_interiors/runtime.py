#!/usr/bin/env python3
"""Headless mGBA checks for Violet's interiors: every warp in every built interior, from the cell next to
it (or standing on an exit mat), lands on its destination warp; Violet's doors land inside on the exit.

    MGBA_FLAGS='-I... -L... -lmgba ...' python3 tools/gba/maps/violet_interiors/runtime.py ENGINE OUT [MAP ...]
"""
from __future__ import annotations
import json, os, shlex, shutil, struct, subprocess, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent / 'violet_city')]

PROOF = ['SproutTower1F', 'SproutTower2F', 'SproutTower3F', 'VioletUniversity', 'VioletLectureHall',
         'VioletHouse1', 'VioletHouse2', 'VioletHouse3', 'VioletHouse4', 'VioletHouse5',
         'CherrygrovePokemonCenter', 'CherrygroveCenterUpstairs', 'CherrygroveMart',
         'VioletPokemonCenter', 'VioletCenterUpstairs', 'VioletMart',       # the Johto Center, basement and Mart (johto_shops.py)
         'SandgemPokemonCenter', 'SandgemCenterUpstairs']                  # the Sinnoh Center (sinnoh_shops.py)

def proof_index(engine):
    """Each map's index in sMapProofMaps (src/apocrypha_map_proof.c)."""
    import re
    src = (engine / 'src/apocrypha_map_proof.c').read_text()
    body = re.search(r'sMapProofMaps\[\] = \{(.*?)\};', src, re.S).group(1)
    return {m.strip(): i for i, m in enumerate(body.split(','))}
VIOLET = 43
KEYS = dict(RIGHT=16, LEFT=32, UP=64, DOWN=128)

TEMPLATE = r'''
#define main unused_map_qualification_main
#include "RUNTIME_C"
#undef main
static const char *out;
static void go(unsigned map,unsigned x,unsigned y){call("MapProof_Enter",map|(x<<8)|(y<<16));frames(360,0);}
static int fails=0;
static void test(unsigned map,unsigned x,unsigned y,unsigned key,unsigned wantmap,unsigned wx,unsigned wy,const char*tag){
 go(map,x,y);observe(tag);
 if(state[3]!=x||state[4]!=y){printf("{\"test\":\"%s\",\"ok\":0,\"why\":\"start\",\"at\":[%u,%u]}\n",tag,state[3],state[4]);fails++;return;}
 c->setKeys(c,key);for(int i=0;i<12;i++)c->runFrame(c);c->setKeys(c,0);frames(400,0);observe(tag);
 char t[96];sprintf(t,"arrive-%s",tag);screenshot(out,t);
 int ok=state[2]==wantmap&&state[3]==wx&&state[4]==wy;if(!ok)fails++;
 printf("{\"test\":\"%s\",\"ok\":%d,\"map\":%u,\"at\":[%u,%u],\"want\":[%u,%u,%u]}\n",tag,ok,state[2],state[3],state[4],wantmap,wx,wy);fflush(stdout);}
int main(int argc,char**argv){
 out=argv[3];FILE*f=fopen(argv[2],"r");if(!f)return 3;while(ns<128&&fscanf(f,"%79s %x",names[ns],&addrs[ns])==2)ns++;fclose(f);
 struct mLogger log={.log=quiet};mLogSetDefaultLogger(&log);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 4;mCoreConfigInit(&c->config,"violet-interiors");c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 5;
 c->rtc.override=RTC_FIXED;c->rtc.value=1789315200000LL;
 c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);
TESTS c->deinit(c);return fails?40:0;}
'''

def walkable(engine, layout_folder, W, H):
    w = struct.unpack('<%dH' % (W * H), (engine / 'data/layouts' / layout_folder / 'map.bin').read_bytes())
    return lambda x, y: 0 <= x < W and 0 <= y < H and (w[y * W + x] & 0x0C00) == 0

def tests(engine, names):
    groups = json.loads((engine / 'data/maps/map_groups.json').read_text())
    grp = next(g for g in groups['group_order'] if 'VioletCity' in groups[g])
    num = {n: i for i, n in enumerate(groups[grp])}
    L = {l['id']: l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}
    load = lambda n: json.loads((engine / 'data/maps' / n / 'map.json').read_text())
    by_id = {}
    for n in groups[grp]:
        p = engine / 'data/maps' / n / 'map.json'
        if p.exists():
            by_id[load(n)['id']] = n
    idx = proof_index(engine)
    snake = lambda n: load(n)['id'][4:]
    out = []
    for n in names:
        mj = load(n)
        lay = L[mj['layout']]
        ok = walkable(engine, Path(lay['blockdata_filepath']).parent.name, lay['width'], lay['height'])
        warp_cells = {(w['x'], w['y']) for w in mj['warp_events']}
        for i, wv in enumerate(mj['warp_events']):
            dest = by_id[wv['dest_map']]
            dw = load(dest)['warp_events'][int(wv['dest_warp_id'])]
            city = wv['dest_map'].endswith(('_CITY', '_TOWN'))
            wx, wy = dw['x'], dw['y'] + (1 if city else 0)
            if dest.endswith(('PokemonCenter', 'CenterUpstairs')) and n.endswith(('PokemonCenter', 'CenterUpstairs')):
                # off an escalator: east, or west where its east side is solid (src/field_effect.c, sEscalatorWestward)
                dl = L[load(dest)['layout']]
                dok = walkable(engine, Path(dl['blockdata_filepath']).parent.name, dl['width'], dl['height'])
                wx += -1 if (not dok(wx + 1, wy) and dok(wx - 1, wy)) else 1
            x, y = wv['x'], wv['y']
            if city:
                start, key = (x, y), 'DOWN'          # standing on the exit mat, walk out
            else:
                cand = [((x, y + 1), 'UP'), ((x - 1, y), 'RIGHT'), ((x + 1, y), 'LEFT'), ((x, y - 1), 'DOWN')]
                cand = [(s, k) for s, k in cand if ok(*s) and s not in warp_cells]
                if not cand:
                    continue
                start, key = cand[0]
            out.append(f' test({idx["MAP_" + snake(n)]},{start[0]},{start[1]},{KEYS[key]},{num[dest]},{wx},{wy},"{n}-{i}");\n')
    return out

def main():
    engine, outdir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    names = sys.argv[3:] or [n for n in PROOF if (engine / 'data/maps' / n / 'map.json').exists()]
    if outdir.exists(): shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    src = TEMPLATE.replace('RUNTIME_C', str(ROOT / 'tools/gba/maps/runtime.c')).replace('TESTS', ''.join(tests(engine, names)))
    (outdir / 'rt.c').write_text(src)
    flags = shlex.split(os.environ.get('MGBA_FLAGS', '')) or ['-lmgba']
    subprocess.run(['cc', '-O1', str(outdir / 'rt.c'), *flags, '-o', str(outdir / 'rt')], check=True)
    lines = subprocess.check_output([shutil.which('arm-none-eabi-nm'), str(engine / 'pokeemerald.elf')], text=True)
    wanted = {'MapProof_Boot', 'MapProof_Enter', 'MapProof_ReadState', 'gMapProofState'}
    syms = {r[2]: r[0] for l in lines.splitlines() if len(r := l.split()) == 3 and r[2] in wanted}
    (outdir / 'symbols.txt').write_text(''.join(f'{k} {v}\n' for k, v in syms.items()))
    r = subprocess.run([str(outdir / 'rt'), str(engine / 'pokeemerald.gba'), str(outdir / 'symbols.txt'), str(outdir)],
                       capture_output=True, text=True, timeout=3600)
    for f in outdir.glob('*.ppm'):
        Image.open(f).save(f.with_suffix('.png')); f.unlink()
    res = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{"test"')]
    (outdir / 'results.json').write_text(json.dumps(dict(exit=r.returncode, stderr=r.stderr[-1500:], tests=res), indent=1) + '\n')
    print(r.returncode, sum(t['ok'] for t in res), '/', len(res), r.stderr[-400:])
    for t in res:
        if not t['ok']:
            print(t)

if __name__ == '__main__':
    main()
