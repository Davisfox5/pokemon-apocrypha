#!/usr/bin/env python3
"""Verify the route corridor and optional Potion using directed ledge movement."""
import json,struct,sys
from pathlib import Path
from collections import deque
import numpy as np

def check(game):
    layouts=json.loads((game/'data/layouts/layouts.json').read_text())['layouts']
    report={}
    for route,start,targets in [(29,(0,16),[(97,16),(62,25),(87,15)]),
                                 (30,(8,73),[(10,0),(10,30),(25,8)])]:
        m=json.loads((game/f'data/maps/CherrygroveRoute{route}Approach/map.json').read_text())
        l=next(l for l in layouts if l['id']==m['layout'])
        grid=np.frombuffer((game/l['blockdata_filepath']).read_bytes(),dtype='<u2').reshape(l['height'],l['width'])
        solid=(grid&0xc00)!=0
        attrs=[]
        for folder in ['primary/cherrygrove',f'secondary/claude_route{route}']:
            d=(game/f'data/tilesets/{folder}/metatile_attributes.bin').read_bytes()
            attrs.append(struct.unpack('<'+'H'*(len(d)//2),d))
        def behavior(x,y):
            mid=int(grid[y,x]&1023)
            return attrs[mid>=512][mid-512 if mid>=512 else mid]&255
        seen={start};q=deque([start])
        while q:
            x,y=q.popleft()
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                xx,yy=x+dx,y+dy
                if not (0<=xx<l['width'] and 0<=yy<l['height']):continue
                if dy==1 and behavior(xx,yy)==59:yy+=1
                if yy>=l['height'] or solid[yy,xx] or (xx,yy) in seen:continue
                seen.add((xx,yy));q.append((xx,yy))
        assert all(t in seen for t in targets),(route,'corridor or Potion blocked')
        report[str(route)]=dict(reachable_cells=len(seen),reachable_targets=targets)
    return report

if __name__=='__main__':print(json.dumps(check(Path(sys.argv[1]).resolve()),indent=2))
