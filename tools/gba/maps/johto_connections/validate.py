#!/usr/bin/env python3
"""Check native tile references, connected camera windows and reachable exterior doors."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from claude_routes import seams
from tiles import Tileset

def inspect(game,layouts,name):
    l=next(l for l in layouts if l['name']==name+'_Layout')
    raw=np.frombuffer((game/l['blockdata_filepath']).read_bytes(),dtype='<u2').reshape(l['height'],l['width'])
    sec=l['secondary_tileset'].removeprefix('gTileset_')
    sec={'NewBark':'new_bark','Route31':'route31','VioletEntrance':'violet_entrance','ClaudeRoute29':'claude_route29','ClaudeRoute30':'claude_route30'}[sec]
    ts=Tileset(game,sec,'cherrygrove')
    for mid in set((raw&1023).ravel().tolist()):
        entries=ts.blocks[mid>=512][mid-512 if mid>=512 else mid]
        for e in entries:
            tid=e&1023;assert tid-(512 if tid>=512 else 0)<len(ts.tiles[tid>=512]),(name,mid,tid)
            assert e>>12<13,(name,mid,'sprite palette bank',e>>12)
    solid=(raw&0xC00)!=0
    return raw,solid,ts

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();game=a.game.resolve()
    layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts'];report={}
    for name,neighbor,origin,start,nstart in [('NewBarkTown','CherrygroveRoute29Approach',(98,0),(0,16),(97,16)),('JohtoRoute31','CherrygroveRoute30Approach',(-28,-30),(38,29),(10,0))]:
        cg,cs,ct=inspect(game,layouts,name);ng,ns,nt=inspect(game,layouts,neighbor)
        reach=seams.reachable(cs,start);nreach=seams.reachable(ns,nstart);ox,oy=origin
        nvis=seams.visible_across(reach,ns.shape,-ox,-oy);cvis=seams.visible_across(nreach,cs.shape,ox,oy)
        nw,cw,cross=seams.crossing_windows(ns,cs,ox,oy);nvis|=nw;cvis|=cw
        checked=set((cg[cvis]&1023).tolist())|set((ng[nvis]&1023).tolist())
        for mid in checked:
            assert ct.render(mid).tobytes()==nt.render(mid).tobytes(),(name,neighbor,'seam pixels differ',mid)
            attr=lambda t:t.attrs[mid>=512][mid-512 if mid>=512 else mid]
            assert attr(ct)==attr(nt),(name,mid,'seam behavior differs')
        m=json.loads((game/f'data/maps/{name}/map.json').read_text())
        for warp in m['warp_events']:assert reach[warp['y'],warp['x']],(name,'unreachable door',warp)
        for sign in m['bg_events']:
            x,y=sign['x'],sign['y'];assert any(reach[y+dy,x+dx] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)] if 0<=y+dy<reach.shape[0] and 0<=x+dx<reach.shape[1]),(name,'sign cannot be read',sign)
        report[name]=dict(passable_cells=int((~cs).sum()),reachable_cells=int(reach.sum()),connection_crossings=cross,seam_metatiles_pixel_and_behavior_identical=len(checked),reachable_doors=len(m['warp_events']))
    vg,vs,vt=inspect(game,layouts,'VioletCityEntrance');vr=seams.reachable(vs,(22,14))
    vm=json.loads((game/'data/maps/VioletCityEntrance/map.json').read_text())
    assert all(vr[w['y'],w['x']] for w in vm['warp_events'])
    assert vr[12,10],'Violet forecourt is disconnected from its gate'
    report['VioletCityEntrance']=dict(reachable_cells=int(vr.sum()),reachable_doors=len(vm['warp_events']))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
