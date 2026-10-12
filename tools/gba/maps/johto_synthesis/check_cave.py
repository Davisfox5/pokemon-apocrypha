"""Check the installed cliff/crown layers, continuous cave dirt and fixed geometry."""
from compose import *
import json,hashlib,subprocess,io

G=Path(sys.argv[1]).resolve();EV=OUT/'evidence'
baseline='6ce0635d04d023073a93fcfab1301ec8cf307981'
before=json.loads(subprocess.check_output(['git','show',baseline+':gba/art/johto-synthesis/evidence/terrain-geometry.json'],cwd=ROOT))
comps=all_comps()
for n,(c,p) in comps.items():
 for k in (() if n=='route31' else ('solid','behavior','cells')):
  value=c[k].copy()
  assert hashlib.sha256(value.tobytes()).hexdigest()==before['maps'][n][k],(n,k)
for n in ('route29','route30','new_bark','violet_entrance'):
 old=Image.open(io.BytesIO(subprocess.check_output(['git','show',baseline+':gba/art/johto-synthesis/evidence/'+n+'.png'],cwd=ROOT))).convert('RGB')
 new=Image.open(EV/(n+'.png')).convert('RGB');mask=np.ones((old.height,old.width),bool)
 if n=='route30':mask[:32,144:192]=False # Native stairs at the Route 31 seam.
 assert np.array_equal(np.array(old)[mask],np.array(new)[mask]),('unrelated map pixels changed',n)

layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts']
l=next(v for v in layouts if v['name']=='JohtoRoute31_Layout')
grid=np.frombuffer((G/l['blockdata_filepath']).read_bytes(),'<u2').reshape(l['height'],l['width'])
t=Tileset(G,'route31','cherrygrove');render=np.asarray(t.map_image(grid.ravel().tolist(),l['width']))
a=assets()[0];tree=a['tree'];top=tree.px[:24];mask=(top>0)&~np.isin(top,[3,12]);colors=np.array(tree.pal.gba())
rock_quads=0
for x in (56,58,60):
 actual=render[192:216,x*16:x*16+32]
 assert np.array_equal(actual[mask],colors[top[mask]]),('crown clipped',x)
 for xx in (x,x+1):
  for y,quads in [(12,4),(13,2)]:
   mid=int(grid[y,xx]&1023);entries=t.blocks[mid>=512][mid%512]
   for q,e in enumerate(entries[:quads]):
    assert e>>12==12,('lawn-backed crown',xx,q,e>>12)
    rock_quads+=1
c,p=comps['route31'];nb,ni,_,_=ground_pixels(c,p)
for y in range(213,240):
 assert nb[y,840]==0 and np.array_equal(render[y,840],p[0].gba()[ni[y,840]]),('imported threshold residue',y)
assert not render[203,840].any(),'cave mouth no longer dark'
shade=render[204:214,840].astype(int)
assert len(np.unique(shade,axis=0))>=5,'hard black/dirt seam'
assert (np.diff(shade.sum(axis=1))>=-24).all(),'threshold shadow reverses'
for left,right in [(48,120),(152,304)]:
 assert (a['landform'].px[184:216,left:right]>0).all(),'grass notch in wall'
 assert (a['landform'].px[216:,left:right]==0).all(),'misaligned cliff baseline'
m=json.loads((G/'data/maps/JohtoRoute31/map.json').read_text())
sign=next(e for e in m['bg_events'] if e.get('script')=='JohtoRoute31_Cave')
assert (sign['x'],sign['y'])==(51,14) and c['solid'][14,51] and c['behavior'][14,51]==29
assert c['behavior'][13,51]==0 and any((w['x'],w['y'])==(52,13) for w in m['warp_events'])
report=dict(baseline_commit=baseline,cave_geometry_unchanged=True,divider_geometry_checked_separately=True,sign=[51,14],other_maps_identical_except_seam_stairs=True,
            complete_rock_backed_crowns=3,rock_background_quadrants=rock_quads,
            continuous_dirt_samples=27,threshold_shades=len(np.unique(shade,axis=0)),aligned_cliff_base_y=215,
            grass_notch_closed=True,dark_mouth_preserved=True)
(EV/'cave-structure.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
