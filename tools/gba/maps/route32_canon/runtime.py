"""Headless mGBA tour of the two-map Route 32 rebuild: north map 43, south map 47 (group 80).
Walks the whole route via BFS on the native collision of both layouts, crosses the seam both
ways, enters the Center and the cave, probes fixed barriers, and does ordinary flash save /
cold reload / title Continue. Usage: runtime.py ENGINE OUT --toolchain /usr"""
from pathlib import Path
import sys, json
from collections import deque
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent/'route32_native_cleanup'))
from native import Part, PRIMARY_GLYPHS, SECONDARY_GLYPHS
from johto_connections import runtime as r
G = Path(sys.argv[1]); OUT = HERE.parents[3]/'gba/art/route32-rebuild'; E = OUT/'evidence'; E.mkdir(parents=True, exist_ok=True)
N, S, SPLIT = 43, 47, 78
prim = Part(G/'data/tilesets/primary/route32', PRIMARY_GLYPHS, 0)
def load(name, sec):
    g = np.fromfile(G/f'data/layouts/{name}/map.bin', '<u2').reshape(-1, 32); s = Part(G/f'data/tilesets/secondary/{sec}', SECONDARY_GLYPHS, 512)
    beh = np.array([(prim.attrs[v] if v < 512 else s.attrs[v-512]) & 255 for v in (g & 1023).ravel()]).reshape(g.shape)
    solid = ((g & 0xc00) != 0) | np.isin(beh, [0x15, 0x61, 0x3b])
    return g, beh, solid
gN, bN, sN = load('JohtoRoute32', 'route32'); gS, bS, sS = load('JohtoRoute32South', 'route32_south')
solid = np.concatenate([sN, sS]); beh = np.concatenate([bN, bS]); H = solid.shape[0]
def mapof(z): return (N, z) if z < SPLIT else (S, z-SPLIT)
def path(start, goal):
    q = deque([start]); parent = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal: break
        for dx, dy, key in [(0, -1, 'UP'), (1, 0, 'RIGHT'), (-1, 0, 'LEFT'), (0, 1, 'DOWN')]:
            xx, yy = x+dx, y+dy
            if not (0 <= xx < 32 and 0 <= yy < H) or solid[yy, xx]: continue
            if (xx, yy) not in parent: parent[(xx, yy)] = ((x, y), key); q.append((xx, yy))
    assert goal in parent, ('Destination blocked', start, goal)
    steps = []; node = goal
    while parent[node] is not None: prev, key = parent[node]; steps.append((key, *node)); node = prev
    return steps[::-1]
goals = [('north-lawn', (20, 3)), ('first-terrace', (14, 22)), ('terrace-path', (18, 24)), ('ledge-pocket', (26, 27)), ('central-grass', (26, 36)), ('west-clearing', (9, 50)), ('ew-stairs-top', (12, 58)),
         ('tall-grass-shelf', (10, 72)), ('under-railway-dock', (18, 80)), ('fishing-arm', (15, 88)), ('pier-south', (18, 95)), ('south-clearing', (8, 110)),
         ('center-forecourt', (16, 131)), ('cave-forecourt', (14, 148))]
legs = []; walk = []; current = (23, 3)
for name, goal in goals:
    steps = path(current, goal); legs.append({'name': name, 'start': current, 'goal': goal, 'steps': len(steps)})
    for key, x, y in steps:
        m, yy = mapof(y); walk.append(f'step({key},1);at({m},{x},{yy},"{name}");')
    walk.append(f'shot("{name}");'); current = goal
(E/'walk-plan.json').write_text(json.dumps(legs, indent=1)+'\n')
m0, y0 = mapof(3)
door = (18, 52); cave = [(12, 65), (13, 65)]
r.MAIN = r.MAIN[:r.MAIN.index('  // Actual east connection')] + f'go({N},23,3);shot("northern-approach");\n' + '\n'.join(walk) + f'''
 go({S},{door[0]},{door[1]+1});step(UP,1);frames(360,0);observe("center-entry");need(state[2]==44,"center-entry");shot("center-interior");step(DOWN,1);frames(360,0);at({S},{door[0]},{door[1]+1},"center-return");shot("center-return");
 go({S},{cave[0][0]},{cave[0][1]+1});step(UP,1);frames(360,0);observe("cave-entry");need(state[2]==46,"cave-entry");shot("cave-room");step(DOWN,1);frames(360,0);at({S},{cave[0][0]},{cave[0][1]},"cave-return");step(DOWN,1);shot("cave-return");
 go({N},18,{SPLIT-1});step(DOWN,1);at({S},18,0,"seam-south");shot("seam-south");step(UP,1);at({N},18,{SPLIT-1},"seam-north");shot("seam-north");
 go({N},20,3);shot("gate-and-flowers");go({N},22,20);shot("terraces");go({N},8,60);shot("ew-stairs");go({S},20,8);shot("pylon");go({S},16,30);shot("pier-and-boulders");go({S},18,56);shot("center-area");go({S},14,66);shot("cave-mouth");
 go({S},18,0);shot("save-under-railway");unsigned status=call("TrySavingData",0);void*data=NULL;size_t size=c->savedataClone(c,&data);f=fopen(flash,"wb");if(status!=1||size!=131072||!f||fwrite(data,1,size,f)!=size)return 11;fclose(f);free(data);printf("{{\\"save_status\\":%u,\\"flash_bytes\\":%zu}}\\n",status,size);
 }}
 c->deinit(c);return 0;
}}
'''
r.MAIN = r.MAIN.replace('11,27,18', f'{S},18,0').replace('cold-reload-new-bark', 'cold-reload-route32')
if __name__ == '__main__': r.main()
