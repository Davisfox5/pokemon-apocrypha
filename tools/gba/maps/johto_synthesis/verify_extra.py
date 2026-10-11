"""Native wall/forest boundaries, surf transitions and animated VRAM protection."""
from compose import *
import json,subprocess,hashlib,shutil
G=Path(sys.argv[1]).resolve();O=Path(sys.argv[2]).resolve();TC=Path(sys.argv[3]).resolve();O.mkdir(parents=True,exist_ok=False);EV=OUT/'evidence'
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
flags=['-I/opt/homebrew/include','-L/opt/homebrew/lib','-lmgba'];keys={1:128,2:64,3:32,4:16}
probes=[(m,x,y,keys[d],0,1-blocked,0) for m,x,y,d,blocked in json.loads((EV/'probes.json').read_text())]
layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];groups=json.loads((G/'data/maps/map_groups.json').read_text())['gMapGroup_Cherrygrove'];surf={}
for n,sec in [('CherrygroveRoute29Approach','claude_route29'),('CherrygroveRoute30Approach','claude_route30'),('NewBarkTown','new_bark'),('JohtoRoute31','route31')]:
 m=groups.index(n);l=next(l for l in layouts if l['name']==n+'_Layout');g=np.frombuffer((G/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width']);t=Tileset(G,sec,'cherrygrove')
 for y in range(1,len(g)-1):
  for x in range(1,g.shape[1]-1):
   if g[y,x]>>12!=1:continue
   for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
    v=int(g[y+dy,x+dx]);mid=v&1023;b=t.attrs[mid>=512][mid%512]&255
    if b in (105,97,59):continue
    expect=int(not v&0xc00);surf.setdefault((m,mid,expect),(m,x,y,key,1,expect,mid))
probes+=list(surf.values());(O/'probes.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in probes))
raw=subprocess.check_output([str(TC/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','gMapProofState','ArePlayerFieldControlsLocked','SetPlayerAvatarTransitionFlags'};rows=[l.split() for l in raw.splitlines()];(O/'symbols.txt').write_text(''.join(f'{r[2]} {r[0]}\n' for r in rows if len(r)==3 and r[2] in wanted))
romhash=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()
source=(ROOT/'tools/gba/maps/johto_collision_runtime.c').read_text().replace('#include "runtime.c"','#include "'+str(ROOT/'tools/gba/maps/runtime.c')+'"')
# Each collision case is an independent new game. Repeated test-only warps
# during field effects previously hit an allocation assertion; ordinary travel
# has its own sustained walking proof. The assertion cause is not established.
anchor='  call("MapProof_Enter",map|(x<<8)|(y<<16));'
source=source.replace(anchor,'  c->reset(c);frames(600,0);call("MapProof_Boot",0);frames(240,0);\n'+anchor)
(O/'collision.c').write_text(source)
run(['cc',O/'collision.c',*flags,'-o',O/'collision'])
# Independent emulator processes share no field state and can run concurrently.
from concurrent.futures import ThreadPoolExecutor
chunks=[probes[i:i+(len(probes)+3)//4] for i in range(0,len(probes),(len(probes)+3)//4)]
def shard(item):
 i,chunk=item;d=O/f'shard-{i}';d.mkdir()
 (d/'probes.tsv').write_text(''.join(' '.join(map(str,p))+'\n' for p in chunk))
 with (d/'collision.jsonl').open('w') as f:run([O/'collision',G/'pokeemerald.gba',O/'symbols.txt',d/'probes.tsv',d],stdout=f,timeout=900)
 return (d/'collision.jsonl').read_text()
with ThreadPoolExecutor(max_workers=4) as pool:outputs=list(pool.map(shard,enumerate(chunks)))
(O/'collision.jsonl').write_text(''.join(outputs))
rows=[json.loads(l) for l in (O/'collision.jsonl').read_text().splitlines()];assert len(rows)==len(probes) and all(r['passed'] for r in rows)
source=(ROOT/'tools/gba/maps/cherrygrove_synthesis/water_runtime.c').read_text().replace('#include "../runtime.c"','#include "'+str(ROOT/'tools/gba/maps/runtime.c')+'"').replace('(29<<8)|(20<<16)','29|(33<<8)|(17<<16)');(O/'water.c').write_text(source);run(['cc',O/'water.c',*flags,'-o',O/'water'])
with (O/'water.json').open('w') as f:run([O/'water',G/'pokeemerald.gba',O/'symbols.txt',O,92],stdout=f)
assert hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest()==romhash
for p in O.glob('*.ppm'):Image.open(p).save(p.with_suffix('.png'))
frames=[Image.open(p) for p in sorted(O.glob('water-*.png'))[:32]];frames[0].save(EV/'route31-water.gif',save_all=True,append_images=frames[1:],duration=133,loop=0)
report=dict(rom_sha256=romhash,walk_and_surf_probes=len(rows),surf_probes=len(surf),passed=True,water=json.loads((O/'water.json').read_text()),desktop_emulator_launched=False)
(EV/'extra-runtime.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(O/'collision.jsonl',EV/'collision-runtime.jsonl');print(json.dumps(report,indent=2))
