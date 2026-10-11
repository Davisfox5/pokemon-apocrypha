"""Cut facade-specific native door animation frames from the installed maps."""
from compose import *
import json,re,struct
G=Path(sys.argv[1]).resolve();src=G/'src/field_door.c';s=src.read_text();start='// Johto synthesis doors\n';end='// End Johto synthesis doors\n'
if start in s:s=s[:s.index(start)]+s[s.index(end)+len(end):]
s=re.sub(r'^.*sJohtoSynthesisDoor.*\n','',s,flags=re.M)
marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{';decl=[];table=[]
layouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];quads=[(x+dx,y+dy) for x,y in [(0,0),(0,16),(16,0),(16,16)] for dx,dy in [(0,0),(8,0),(0,8),(8,8)]]
for name,kind in [('NewBarkTown','new_bark'),('JohtoRoute31','route31'),('VioletCityEntrance','violet_entrance')]:
 m=json.loads((G/'data/maps'/name/'map.json').read_text());l=next(x for x in layouts if x['id']==m['layout']);w=l['width'];grid=np.frombuffer((G/l['blockdata_filepath']).read_bytes(),'<u2');t=Tileset(G,kind,'cherrygrove');rgb=np.array(t.map_image(grid.tolist(),w),int);sym=l['secondary_tileset'];decl.append('extern const struct Tileset '+sym+';')
 for i,door in enumerate(m['warp_events']):
  x,y=door['x'],door['y'];mid=int(grid[y*w+x]&1023)
  if t.attrs[mid>=512][mid%512]&255!=105:continue
  label=name+'_'+str(i);closed=rgb[(y-1)*16:(y+1)*16,x*16:(x+2)*16].copy();top=8 if i==0 and name=='NewBarkTown' else 13;bot=31 if top==8 else 29;right=20 if top==8 or i in (1,2,4,6) and name=='NewBarkTown' else 16
  frames=[]
  for n in (1,2,3):
   f=closed.copy();f[top:bot,:right]=[24,32,40];keep=right-right*n//3
   if keep:f[top:bot,:keep]=closed[top:bot,np.linspace(0,right-1,keep).astype(int)]
   frames.append(f)
  bs=[];raw=bytearray()
  for qx,qy in quads:
   cs=np.concatenate([f[qy:qy+8,qx:qx+8].reshape(-1,3) for f in frames]);cost=[]
   for bank in range(13):
    pp=np.array(t.pals[bank>=6][bank][1:]);cost.append(((cs[:,None]-pp)**2).sum(-1).min(-1).sum())
   bs.append(int(np.argmin(cost)))
  for f in frames:
   for (qx,qy),bank in zip(quads,bs):
    pp=np.array(t.pals[bank>=6][bank][1:]);cs=f[qy:qy+8,qx:qx+8].reshape(-1,3);ids=((cs[:,None]-pp)**2).sum(-1).argmin(-1)+1
    raw.extend(int(ids[k])|(int(ids[k+1])<<4) for k in range(0,64,2))
  out=G/'graphics/door_anims/johto_synthesis'/f'{label}.4bpp';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
  decl.append(f'static const u8 sJohtoSynthesisDoor_{label}[] = INCBIN_U8("graphics/door_anims/johto_synthesis/{label}.4bpp");\nstatic const u8 sJohtoSynthesisDoorPal_{label}[20] = {{'+','.join(map(str,bs+[0]*4))+'};')
  table.append(f'    {{.metatileNum={mid}, .tileset=&{sym}, .sound=DOOR_SOUND_NORMAL, .size=DOOR_SIZE_2x2_LEFT, .tiles=sJohtoSynthesisDoor_{label}, .palettes=sJohtoSynthesisDoorPal_{label}}},')
s=s.replace(marker,start+'\n'.join(decl)+'\n'+end+marker+'\n'+'\n'.join(table));src.write_text(s)
print('Facade animations:',len(table))
