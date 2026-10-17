"""Clear audited orphan backing on clipped map-edge and path-adjacent trees."""
from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rollout import P,dump,save,split,encode
from johto_common.rollout_review import scene
from johto_common.rollout_scenery import setup
from johto_service_buildings.build import decode
from claude_cherrygrove import ground
G=Path(sys.argv[1]);reports=[]
for c in json.loads((P/'source/initial-inventory.json').read_text()):
 before,g,attrs,t=scene(G,c);changed=np.all(before[:,:,:3]==(64,136,104),2)
 if not changed.any():continue
 assert c['map'] in ['CherrygroveRoute29Approach','CherrygroveCity','CherrygroveRoute30Approach']
 # These remaining coordinates were visually inspected as obsolete tree backing.
 layers,_,es,_=decode(t,g);setup(t,g,es,np.fromfile(G/c['layout']['border_filepath'],'<u2')&1023);raw=ground.textures()[ground.GRASS];pal=np.array(t.pals[0][0][1:],int);tex=pal[np.square(raw[:,:,None,:].astype(int)-pal).sum(3).argmin(2)];ys,xs=np.indices(changed.shape);bg=np.dstack([tex[ys%tex.shape[0],xs%tex.shape[1]],np.full(changed.shape,255,np.uint8)]);t.background=bg;target=before.copy();target[changed]=bg[changed]
 foreground=~np.any([np.all(target[:,:,:3]==color,2) for color in [(88,176,136),(96,192,144),(104,200,152),(104,208,152)]],axis=0)
 split(target,layers,changed,t,foreground);info=encode(G,c,t,g,attrs,layers,target,changed);info.update(map=c['map'],removed_shadow_pixels=int(changed.sum()),remaining_shadow_pixels=int(np.all(target[:,:,:3]==(64,136,104),2).sum()));reports.append(info);save(P/'review'/f'{c["map"]}.png',target);print(info)
dump(P/'evidence/edge-shadows.json',reports)
