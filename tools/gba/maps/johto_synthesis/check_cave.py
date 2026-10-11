"""Check the installed cliff/crown layers, continuous cave dirt and fixed geometry."""
from compose import *
import json,hashlib,subprocess,io

G=Path(sys.argv[1]).resolve();EV=OUT/'evidence'
baseline='74b13f561c9063250a3ce5ad935db3c8b88c6426'
before=json.loads(subprocess.check_output(['git','show',baseline+':gba/art/johto-synthesis/evidence/terrain-geometry.json'],cwd=ROOT))
comps=all_comps()
for n,(c,p) in comps.items():
 for k in ('solid','behavior','cells'):
  assert hashlib.sha256(c[k].tobytes()).hexdigest()==before['maps'][n][k],(n,k)
for n in ('route29','route30','new_bark','violet_entrance'):
 old=Image.open(io.BytesIO(subprocess.check_output(['git','show',baseline+':gba/art/johto-synthesis/evidence/'+n+'.png'],cwd=ROOT))).convert('RGB')
 assert old.tobytes()==Image.open(EV/(n+'.png')).convert('RGB').tobytes(),('unrelated map pixels changed',n)

layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts']
l=next(v for v in layouts if v['name']=='JohtoRoute31_Layout')
grid=np.frombuffer((G/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width'])
t=Tileset(G,'route31','cherrygrove');render=np.asarray(t.map_image(grid.ravel().tolist(),l['width']))
tree=assets()[0]['tree'];top=tree.px[:16];mask=(top>0)&~np.isin(top,[3,12]);colors=np.array(tree.pal.gba())
rock_quads=0
for x in (56,58,60):
 actual=render[192:208,x*16:x*16+32]
 assert np.array_equal(actual[mask],colors[top[mask]]),('crown clipped',x)
 for xx in (x,x+1):
  mid=int(grid[12,xx]&1023);entries=t.blocks[mid>=512][mid%512]
  for q,e in enumerate(entries[:4]):
   assert e>>12==12,('lawn-backed crown',xx,q,e>>12)
   rock_quads+=1
c,p=comps['route31'];nb,ni,_,_=ground_pixels(c,p)
for y in range(206,240):
 assert nb[y,840]==0 and np.array_equal(render[y,840],p[0].gba()[ni[y,840]]),('imported threshold residue',y)
assert not render[203,840].any(),'cave mouth no longer dark'
report=dict(baseline_commit=baseline,geometry_unchanged=True,other_maps_pixel_identical=True,
            complete_rock_backed_crowns=3,rock_background_quadrants=rock_quads,
            continuous_dirt_samples=34,dark_mouth_preserved=True)
(EV/'cave-structure.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
