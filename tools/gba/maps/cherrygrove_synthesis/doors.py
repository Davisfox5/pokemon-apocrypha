"""Door animations cut from the synthesized facades at E's unchanged warp cells."""
from pathlib import Path
import sys,json,struct,re
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from tiles import Tileset
R=HERE.parents[3];A=R/'gba/art/cherrygrove-synthesis';G=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R/'tools/vendor/gba/cherrygrove-synthesis-work';t=Tileset(G,'cherrygrove','cherrygrove')
report=json.loads((A/'evidence/integration.json').read_text());spec=report['maps'][0]['buildings'];rgb=np.array(Image.open(A/'evidence/CherrygroveCity.png')).astype(int);grid=struct.unpack('<3840H',(G/'data/layouts/CherrygroveCity/map.bin').read_bytes())
source=(G/'src/field_door.c').read_text();marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{'
source=re.sub(r'^.*sRestartDoor.*\n','',source,flags=re.M).replace('// Fresh custom Johto facade animations.\n','').replace('extern const struct Tileset gTileset_Cherrygrove;\n','')
folder=G/'graphics/door_anims/johto_restart';folder.mkdir(exist_ok=True,parents=True);decl=['extern const struct Tileset gTileset_Cherrygrove;'];table=[]
quads=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
for b in spec:
 name=b['name'];x,y=b['door'];closed=rgb[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();l,top,r,bot={'house':(0,12,20,29),'house_mirror':(0,12,16,29),'house2':(0,12,20,29),'gable':(0,13,16,29),'center':(0,16,20,32),'mart':(0,17,20,31)}[b['style']];frames=[]
 for progress in (1,2,3):
  f=closed.copy();f[top:bot,l:r]=(24,32,40);width=r-l;keep=width-width*progress//3
  if keep:f[top:bot,l:l+keep]=closed[top:bot,l+np.linspace(0,width-1,keep).astype(int)]
  frames.append(f)
 banks=[];raw=bytearray();views=[]
 for qx,qy in quads:
  colors=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in frames]);best=None
  for bank in range(13):
   pal=np.array(t.pals[bank>=6][bank][1:]);cost=((colors[:,None,:]-pal)**2).sum(-1).min(-1).sum()
   if best is None or cost<best[0]:best=(cost,bank)
  banks.append(best[1])
 for f in frames:
  view=np.zeros((32,32,3),np.uint8)
  for (qx,qy),bank in zip(quads,banks):
   pal=np.array(t.pals[bank>=6][bank][1:]);colors=f[qy:qy+8,qx:qx+8].reshape(-1,3);ids=((colors[:,None,:]-pal)**2).sum(-1).argmin(-1);view[qy:qy+8,qx:qx+8]=pal[ids].reshape(8,8,3);ids+=1
   raw.extend(int(ids[i])|(int(ids[i+1])<<4) for i in range(0,64,2))
  views.append(view)
 (folder/f'{name}.4bpp').write_bytes(raw);Image.fromarray(np.concatenate([closed.astype(np.uint8)]+views,axis=1)).resize((512,128),Image.Resampling.NEAREST).save(A/f'evidence/door-{name}.png')
 decl.append(f'static const u8 sRestartDoor_{name}[] = INCBIN_U8("graphics/door_anims/johto_restart/{name}.4bpp");\nstatic const u8 sRestartDoorPal_{name}[20] = {{'+','.join(map(str,banks+[0]*4))+'};')
 mid=grid[y*80+x]&1023;table.append(f'    {{.metatileNum={mid}, .tileset=&gTileset_Cherrygrove, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_2x2_LEFT, .tiles=sRestartDoor_{name}, .palettes=sRestartDoorPal_{name}}},')
source=source.replace(marker,'// Fresh custom Johto facade animations.\n'+'\n'.join(decl)+'\n'+marker+'\n'+'\n'.join(table));(G/'src/field_door.c').write_text(source)
print('Seven facade-specific door animations generated.')
