#!/usr/bin/env python3
"""Native Violet exterior with owner-requested edge finishing. New-map authoring only; never regenerate owner edits.
HGSS geography is interpreted on 16px cells; eastern campus is a canon-led proposal.
"""
import sys,json,struct,hashlib,subprocess,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
from claude_cherrygrove import build as native,ground,banks
from claude_cherrygrove.pixel import Canvas,Palette
from route30_hgss_blocks import ground_native,layers
from tiles import Tileset,palette
from edges import soften_building,shoreline,rounded_distance
import campus,exits,cleanup,packing
from johto_mart import assets as mart
OUT=ROOT/'gba/art/violet-city';S=OUT/'source';EV=OUT/'evidence';W,H=80,72

def digest(path):
 raw=path.read_bytes()
 if path.suffix==".pal":raw=raw.replace(b"\r\n",b"\n")
 return hashlib.sha256(raw).hexdigest()

def main(game):
 guard=S/'generated-files.json'
 if (game/'data/maps/VioletCity/map.json').exists():
  if not guard.exists():raise SystemExit('Existing Violet map has no matching authoring manifest; preserve owner edits.')
  changed=[p for p,h in json.loads(guard.read_text()).items() if not (game/p).exists() or digest(game/p)!=h]
  if changed:raise SystemExit('Preserving edits since this proposal was generated: '+', '.join(changed))
 cg=ROOT/'gba/art/cherrygrove-synthesis';t=Tileset(game,'cherrygrove','cherrygrove')
 pals={i:Palette(i,t.pals[i>=6][i][1:],[str(j) for j in range(15)]) for i in range(13)}
 A={}
 for name,b in [('tree',3),('house',6),('gable',6),('center',8)]:
  ar=np.array(Image.open(cg/'refined'/f'{name}.png'));c=Canvas(ar.shape[1],ar.shape[0],pals[b]);c.px=ar;A[name]=c
 ref=Image.open(S/'hgss-reference.png').convert('RGBA')
 # Explicit source silhouettes, preserving original pixel scale.
 def cut(name,box,points):
  im=ref.crop(box);m=Image.new('L',im.size);ImageDraw.Draw(m).polygon(points,fill=255);im.putalpha(m);return np.array(im)
 special={
 'tower':cut('tower',(576,16,688,208),[(45,0),(66,0),(66,23),(106,24),(110,32),(110,152),(96,161),(96,175),(96,181),(16,181),(16,160),(4,156),(3,31),(8,25),(44,25)]),
 'academy':cut('academy',(704,560,848,672),[(35,12),(70,12),(77,18),(77,41),(134,41),(137,45),(137,80),(134,80),(134,105),(8,105),(8,81),(6,79),(6,44),(10,41),(35,41)]),
 'gym':cut('gym',(448,576,560,672),[(37,0),(76,0),(76,7),(93,15),(105,29),(109,51),(110,69),(101,82),(77,90),(24,90),(7,82),(2,66),(3,39),(10,23),(31,11),(37,11)]),
 }
 # Violet's distinctive tall purple gable and timber-fronted homes.
 house_pixels=cleanup.house(ref);post=cleanup.bridge_post(ref)
 housebank=banks.Bank(6,'VIOLET_HOMES_PROPS','secondary').add('house',house_pixels).add('bridge_post',post).keep((89,140,186),(115,166,200),(32,32,32),(136,152,168),(176,168,104),(120,104,24))
 A.update(housebank.build());pals[6]=housebank.palette
 A['gable']=A['house']
 # Exclude foliage behind the spire before indexing the source silhouette.
 top=special['tower'][:24];top[:,:,3][top[:,:,1].astype(int)>top[:,:,0].astype(int)]=0
 purple=banks.Bank(7,'VIOLET_LANDMARKS','secondary').add('tower',special['tower']).add('academy',special['academy']);A.update(purple.build());pals[7]=purple.palette
 gymbank=banks.Bank(5,'FORMER_GYM','primary').add('gym',special['gym']);A.update(gymbank.build());pals[5]=gymbank.palette
 # Native repeating roof modules keep the source silhouette and edge courses.
 # Repeat only interior courses, retaining the hip/ridge boundaries.
 for key,boxes in [('tower',[(16,40,24,56),(72,40,24,56)]),('academy',[(16,56,112,16)])]:
  c=A[key]
  for x,y,w,h in boxes:
   pattern=c.px[y:y+8,x:x+8].copy();c.px[y:y+h,x:x+w]=np.tile(pattern,(h//8,w//8))
 for key in ['tower','academy','gym','center']:soften_building(A[key])
 A['mart'],A['mart_brandmark']=mart.make_assets(9);pals[9]=A['mart'].pal
 mart.export_assets(ROOT/'gba/art/johto-mart/source',9)
 A['gym']=campus.lecture_hall();pals[5]=A['gym'].pal;soften_building(A['gym'])
 # Original modular university facade; its library is planned inside the main hall.
 A['university']=campus.university();pals[10]=A['university'].pal
 A['court']=campus.court();pals[4]=A['court'].pal
 soften_building(A['university'])
 # Repeat original bridge deck and urban paving, with no rotated staircase art.
 infrastructure=banks.Bank(11,'VIOLET_STONE_WOOD','secondary')
 for name,box in [('paving',(256,480,288,512)),('bridge',(608,304,656,336)),('rail_left',(600,304,608,336)),('rail_right',(656,304,664,336)),('island',(528,384,560,416)),('sign',(640,744,656,768))]:
  ar=np.array(ref.crop(box));infrastructure.add(name,ar)
 A.update(infrastructure.build());pals[11]=infrastructure.palette
 cleanup.sign_mask(A['sign'])
 # Reuse Route 30's native freshwater glyphs and complete tree art exactly.
 rt=Tileset(game,'claude_route30','cherrygrove');pals[12]=Palette(12,rt.pals[1][12][1:],[str(j) for j in range(15)])
 for phase in range(4):
  ar=np.array(Image.open(ROOT/'gba/art/route30-hgss-blocks/source/materials'/f'pond-15-{phase}.png').convert('RGBA'));c=Canvas(16,16,pals[12]);colors=np.array(pals[12].gba(),int);mask=ar[:,:,3]>0;c.px[mask]=((ar[mask,:3].astype(int)[:,None]-colors[None])**2).sum(2).argmin(1)
  for bits in range(16):A[f'pond-{bits}-{phase}']=shoreline(c,bits)
 # Repeating shoreline modules leave native capacity for the stone landing bevel.
 for bits in range(15):
  for phase in range(1,4):A[f'pond-{bits}-{phase}']=A[f'pond-{bits}-0']
 # Native HGSS-style west gate replaces the temporary boundary rock bank.
 A['west_gate']=exits.west_gate();pals[2]=A['west_gate'].pal
 # Clean silhouettes are imported before quantization; retain the full islet face.
 A['lily_pads']=exits.lily_pads(pals[6])
 island=cleanup.islet(ref)
 # Preserve the accepted gate colors exactly; its ten shades also supply
 # turf and deep soil tones. Five slots carry the island's foliage/earth.
 gate=np.array(Image.open(S/'preserved-west-gate.png').convert('RGBA'))
 gate_colors=[tuple(map(int,c)) for c in np.unique(gate[gate[:,:,3]>0,:3],axis=0)]
 colors=gate_colors+[(80,96,48),(96,128,32),(120,168,40),(136,96,72),(160,120,88)]
 pals[2]=Palette(2,colors,[str(i) for i in range(15)])
 for name,rgba in [('west_gate',gate),('lake_islet',island)]:
  c=Canvas(rgba.shape[1],rgba.shape[0],pals[2]);mask=rgba[:,:,3]>0
  c.px[mask]=((rgba[mask,:3].astype(int)[:,None]-np.array(colors,int)[None])**2).sum(2).argmin(1)+1;A[name]=c
 # Snap new palette colors to GBA RGB555 before lossless compilation.
 for pal in pals.values():pal.colors=[tuple(v//8*8 for v in color) for color in pal.colors]
 # Equal RGB555 colors share an index. This reduces storage without changing
 # a single visible pixel or cutting detail from the imported artwork.
 for c in A.values():
  colors=c.pal.gba();lut=np.arange(16,dtype=np.uint8)
  for i in range(1,16):
   for j in range(1,i):
    if colors[i]==colors[j]:lut[i]=j;break
  c.px=lut[c.px]
 # Preserve editable native indexed assets and compile new landmarks with Porytiles.
 material=S/'materials';material.mkdir(exist_ok=True)
 for name,c in A.items():Image.fromarray(c.to_rgba()).save(material/f'{name}.png')
 psrc=S/'porytiles-landmarks';psrc.mkdir(exist_ok=True)
 atlas=[]
 for key in ['tower','university','gym']:
  c=A[key];ar=c.to_rgba()
  for y in range(0,c.h,16):
   for x in range(0,c.w,16):atlas.append((key,x,y,ar[y:y+16,x:x+16]))
 bot=Image.new('RGBA',(128,((len(atlas)+7)//8)*16));top=bot.copy();mid=bot.copy()
 for i,(_,x,y,ar) in enumerate(atlas):mid.paste(Image.fromarray(ar),(i%8*16,i//8*16))
 for name,img in [('bottom',bot),('middle',mid),('top',top)]:img.save(psrc/f'{name}.png')
 subprocess.run(['porytiles-legacy','compile-primary','-dual-layer','-o',str(S/'porytiles-compiled'),str(psrc),str(game/'include/constants/metatile_behaviors.h')],check=True)
 # Decode Porytiles output and import it only after exact RGB/alpha equality.
 cp=S/'porytiles-compiled'
 for palfile in (cp/'palettes').glob('*.pal'):palfile.write_bytes(palfile.read_bytes().replace(b'\r\n',b'\n'))
 sheet=np.array(Image.open(cp/'tiles.png'));ts=[sheet[y:y+8,x:x+8] for y in range(0,sheet.shape[0],8) for x in range(0,128,8)]
 bl=list(struct.iter_unpack('<8H',(cp/'metatiles.bin').read_bytes()));ps={int(p.stem):np.array(palette(p)) for p in (cp/'palettes').glob('*.pal')}
 for i,(key,x,y,expected) in enumerate(atlas):
  decoded=np.zeros((16,16,4),np.uint8)
  for layer in range(2):
   for q in range(4):
    en=bl[i][layer*4+q];a=ts[en&1023].copy()
    if en&1024:a=a[:,::-1]
    if en&2048:a=a[::-1]
    part=decoded[q//2*8:q//2*8+8,q%2*8:q%2*8+8];m=a>0;part[m,:3]=ps[en>>12][a[m]];part[m,3]=255
  assert np.array_equal(decoded,expected),('Porytiles changed landmark pixels',key,x,y,decoded[np.any(decoded!=expected,2)][:5].tolist(),expected[np.any(decoded!=expected,2)][:5].tolist())
  c=A[key];pal=np.array(c.pal.gba());mask=decoded[:,:,3]>0;part=c.px[y:y+16,x:x+16];part[mask]=((decoded[mask,:3].astype(int)[:,None]-pal[None])**2).sum(2).argmin(1)
 (EV/'porytiles.json').write_text(json.dumps({'version':'2.0.0 legacy compiler','compiled_landmark_metatiles':len(atlas),'RGB_alpha_errors':0})+'\n')
 # 64x72 original geography + an eastern campus annex, without stretching the city.
 plan=np.full((H,W),'T',dtype='<U1')
 def rect(ch,x,y,w,h):plan[y:y+h,x:x+w]=ch
 for box in [(10,28,10,15),(15,42,35,6),(18,46,4,11),(18,55,6,8),(35,56,13,11),(40,46,7,18),(46,57,19,5),(56,51,22,11),(36,34,6,13),(27,35,26,8),(23,16,32,19),(34,12,11,7),(34,2,11,12),(8,26,12,7),(54,33,22,21)]:rect('.',*box)
 rect('W',24,16,30,19);rect('.',35,13,9,6);rect('Q',31,23,12,6);rect('B',37,17,5,6);rect('B',37,29,5,6)
 for box in [(15,29,4,17),(11,28,7,4),(15,43,35,4),(37,35,5,11),(40,45,6,19),(36,61,11,6),(44,57,34,4),(57,52,19,8),(49,43,24,4),(68,40,5,16)]:rect('P',*box)
 # Campus court, library garden and a bounded southern/western path reserve.
 rect('.',54,34,22,16);rect('P',51,43,22,4);rect('P',68,43,5,13);rect('.',54,47,14,9);rect('C',55,48,12,7)
 # City-side approaches follow HGSS: west gate and southern woodland lane.
 rect('.',0,25,12,9);rect('P',6,28,12,4)
 rect('.',18,55,8,17);rect('P',20,55,3,10)
 rect('P',20,64,5,3);rect('P',22,65,3,7)
 buildings=[('tower','Sprout Tower',36,1,3,11),('gym','Lecture Hall',27,35,4,6),('university','University and Library',46,33,11,8),('mart','Poke Mart',19,35,2,5),('center','Pokemon Center',46,50,3,5),('house','West Residence',9,33,1,5),('house','South Residence',35,56,1,5),('house','Northwest Residence',10,22,1,5),('house','West Garden Residence',25,51,1,5),('house','South Garden Residence',55,59,1,5)]
 # Three modest residential clearings connect to the existing street spine.
 for box in [(8,22,10,11),(22,50,12,10),(53,59,12,8)]:rect('.',*box)
 for key,label,x,y,dx,dy in buildings:
  c=A[key]
  if key=='university':rect('.',x,y+3,c.w//16,c.h//16-3)
  else:rect('.',x,y,c.w//16,c.h//16)
  rect('P',x+dx,y+c.h//16,2,2)
 # The larger retail pavilion needs a clear east aisle and showroom frontage.
 # Remove legacy forest blockers from the old sign and narrow gap to the hall.
 rect('.',26,35,1,7);rect('.',23,41,3,1)
 # Connect each approach to the HGSS road spine, explicit grid geometry.
 rect('P',37,13,5,4);rect('P',20,40,3,5);rect('P',28,41,7,4);rect('P',54,42,6,4);rect('P',47,55,5,4);rect('P',10,39,7,3);rect('P',36,62,7,3)
 rect('P',11,28,7,3);rect('P',26,57,15,3);rect('P',60,59,3,8);rect('P',56,65,7,2)
 rect('P',6,28,12,4);rect('P',19,46,4,11);rect('P',20,55,3,10);rect('P',20,64,5,3);rect('P',22,65,3,7)
 # Arrival arch at eastern end; its warp is a cave-style threshold under the roof.
 rect('P',73,56,5,5)
 # Ground floor, structures, and upper foreground remain distinct layers.
 mc=native.MapCanvas(W,H);fg=native.MapCanvas(W,H);solid=np.zeros((H,W),bool);beh=np.zeros((H,W),np.uint8)
 cells=np.full((H,W),ground.GRASS,np.int8)
 def stamp(key,x,y,front=False):
  c=A[key];mc.blit(c,x*16,y*16)
  if front:fg.blit(c,x*16,y*16)
 for y in range(H):
  for x in range(W):
   ch=plan[y,x]
   if ch=='W':
    bits=sum((1<<i)*int(0<=xx<W and 0<=yy<H and plan[yy,xx] in ['W','B','Q']) for i,(xx,yy) in enumerate([(x,y-1),(x,y+1),(x-1,y),(x+1,y)]))
    stamp(f'pond-{bits}-{y%2*2+x%2}',x,y);solid[y,x]=True;beh[y,x]=16
   elif ch=='C':
    src=A['court'];c=Canvas(16,16,src.pal);c.px=src.px[(y-48)*16:(y-47)*16,(x-55)*16:(x-54)*16].copy();mc.blit(c,x*16,y*16)
    if y in [48,54] and x in [56,57,64,65]:solid[y,x]=True
   elif ch in ['P','Q']:
    src=A['paving' if ch=='P' else 'island'];c=Canvas(16,16,src.pal);c.px=src.px[y%2*16:y%2*16+16,x%2*16:x%2*16+16].copy()
    # Native cell edge masks: curb encloses the road, grass remains outside it.
    if ch=='P':
     missing=[not(0<=nx<W and 0<=ny<H and plan[ny,nx] in ['P','B','Q','C']) for nx,ny in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)]]
     dist=rounded_distance(missing,4)
     c.px[dist<1]=0
     pal=np.array(c.pal.gba(),int);rim=int(((pal-np.array([144,136,120]))**2).sum(1)[1:].argmin()+1);c.px[(dist>=1)&(dist<2)]=rim
    if ch=='Q' and 31<=x<43 and 23<=y<29:
     # Rounded stone landing corners reveal water, never a patch of grass.
     yy,xx=np.indices((16,16));missing=[y==23,y==28,x==31,x==42]
     if x in [37,38,39,40,41]:missing[:2]=[False,False]
     distance=rounded_distance(missing,5)
     pal=np.array(c.pal.gba(),int)
     def tone(rgb):return int(((pal[1:]-np.array(rgb))**2).sum(1).argmin()+1)
     c.px[distance<0]=0
     c.px[(distance>=0)&(distance<1)]=tone([112,120,136])
     c.px[(distance>=1)&(distance<2)]=tone([144,152,168])
     stamp(f'pond-15-{y%2*2+x%2}',x,y)
     mc.blit(c,x*16,y*16);fg.blit(c,x*16,y*16)
     continue
    if ch=='Q' and 56<=x<65 and 48<=y<55:
     # Practice court perimeter and center stripe use the native stone light tone.
     yy,xx=np.indices((16,16));line=((x==56)&(xx==4))|((x==64)&(xx==11))|((y==48)&(yy==4))|((y==54)&(yy==11))|((x==60)&(xx==7))
     pal=np.array(c.pal.gba(),int);white=int(((pal-np.array([224,224,224]))**2).sum(1)[1:].argmin()+1);c.px[line]=white
    mc.blit(c,x*16,y*16)
   elif ch=='B':
    # Three-cell deck and one-half-cell stone rails on each side.
    col=x-37;src=A['bridge'];c=Canvas(16,16,src.pal)
    if col in [0,4]:
     s=A['rail_left' if col==0 else 'rail_right'];c.px[:,:]=np.tile(s.px[y%2*16:y%2*16+16],(1,2));solid[y,x]=True
    else:c.px=src.px[y%2*16:y%2*16+16,(col-1)*16:col*16].copy()
    mc.blit(c,x*16,y*16)
 # Forests are complete 2x3 crowns with exclusive 2x2 trunk/ground footprints.
 trees=[]
 for y in range(0,H-2,2):
  for x in range(0,W-1,2):
   if (plan[y:y+3,x:x+2]=='T').all():trees.append((x,y));solid[y+1:y+3,x:x+2]=True
 # Narrow unfinished forest cells stay physically closed, never a shortcut.
 solid[plan=='T']=True
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 for y in range(23,29):
  for x in range(31,43):
   if x in [37,40] and y in [24,25]:
    fg.bank[y*16:(y+1)*16,x*16:(x+1)*16]=-1;fg.idx[y*16:(y+1)*16,x*16:(x+1)*16]=0
    continue  # Opaque landing under finials uses BG3, leaving BG2 for the prop.
   c=A[f'pond-15-{y%2*2+x%2}'];mc.background_bank[y*16:y*16+16,x*16:x*16+16]=12;mc.background_idx[y*16:y*16+16,x*16:x*16+16]=c.px
 for x,y in trees:stamp('tree',x,y,True);mc.above[y,x:x+2]=True
 # Green campus trees retain footprints. Pink trees are exclusive to Cherrygrove.
 campus_trees=[(70,35),(74,35),(70,39),(74,39)]
 for x,y in campus_trees:
  stamp('tree',x,y,True);solid[y+1:y+3,x:x+2]=True;mc.above[y,x:x+2]=True
 anchors=[]
 for key,label,x,y,dx,dy in buildings:
  c=A[key];stamp(key,x,y,True);cw,ch=c.w//16,c.h//16
  solid[y+(3 if key=='university' else 1):y+ch,x:x+(4 if key=='house' else cw)]=True;mc.above[y,x:x+cw]=True
  if key=='university':
   # Narrower parallel roof/walls leave one clear column on either side.
   solid[y+3:y+ch,x]=False;solid[y+3:y+ch,x+cw-1]=False
   solid[y+1:y+3,x+9:x+13]=True
   mc.above[y+2:y+3,x+1:x+cw-1]=True
  # Door threshold remains closed until that building's interior is authored.
  anchors.append({'name':label,'asset':key,'box':[x,y,cw,ch],'door':[x+dx,y+dy],'approach':[x+dx,y+ch]})
 # HGSS bridge/landing finials and small floating lily-pad clusters.
 posts=[(36,17),(42,17),(36,35),(42,35),(37,25),(40,25)]
 for x,y in posts:
  stamp('bridge_post',x,y-1,True);solid[y,x]=True;mc.above[y-1,x]=True
 for x,y in [(27,19),(49,19),(45,29),(28,31),(51,28)]:stamp('lily_pads',x,y,True)
 stamp('lake_islet',47,22,True);beh[23:27,47:51]=0
 # Mart signage is integrated in its corner tower; no detached pole blocks the street.
 # West gate has its HGSS east-facing steps. Its interior/Route 36 are next scope.
 stamp('west_gate',0,25,True);solid[26:32,0:6]=True;mc.above[25,0:6]=True
 # Close grass at outer boundaries; only the surveyed Route 32 lane is open.
 solid[-1,:]=True;solid[-1,22:25]=False;solid[:,0]=True
 route_exits=[{'name':'Route 36 gate','approach':[7,30],'connection':'west gate interior pending','active':False},
        {'name':'Route 32 south','approach':[23,71],'connection':'down, offset pending Route 32 layout','active':False}]
 # Campus courts reuse native paving; no trainer content/encounters invented.
 # Stone signs at campus, tower and arrival; their locations remain off the main walk line.
 signs=[(53,43,'University'),(35,14,'Tower'),(68,43,'Library'),(26,42,'Lecture'),(70,59,'City'),(54,47,'Practice'),(9,32,'Route36'),(25,67,'Route32')]
 for x,y,label in signs:
  stamp('sign',x,y-1,True);solid[y,x]=True;mc.above[y-1,x]=True
 # Gate facade reuses the complete accepted gable module, with its real door anchor.
 A['gate']=A['house']
 stamp('gate',73,51,True);solid[52:57,73:77]=True;solid[56,74]=False;beh[56,74]=0x60;mc.above[51,73:77]=True
 mc.fore_bank=fg.bank;mc.fore_idx=fg.idx
 # Opaque gate module includes its authored floor, no third background layer.
 comp={'W':W,'H':H,'canvas':mc,'cells':cells,'behavior':beh,'solid':solid,'tag':'VioletCity'}
 # New city-only tile pools. Reuse accepted pixels; never repack shared map tilesets.
 class CityPacker(native.Packer):
  def tile(self,bank,arr,pos=None):
   arr=palette_maps[bank][arr]
   for hf in (0,1):
    for vf in (0,1):
     aa=(arr[::-1] if vf else arr);aa=aa[:,::-1] if hf else aa;k=aa.tobytes()
     if k in self.lookup:return self.lookup[k]|hf<<10|vf<<11
   pool='primary' if len(self.tiles['primary'])<512 else 'secondary';base=0 if pool=='primary' else 512
   assert base+len(self.tiles[pool])<1008,('Violet exceeds 1008 scenery tiles',__import__('collections').Counter(b for ts in self.tiles.values() for b,_ in ts))
   tid=base+len(self.tiles[pool]);self.tiles[pool].append((bank,arr.copy()));self.lookup[arr.tobytes()]=tid;return tid
  def metatile(self,entries,attr):
   k=(tuple(entries),attr)
   if k in self.block_lookup:return self.block_lookup[k]
   pool='primary' if len(self.blocks['primary'])<512 else 'secondary';assert len(self.blocks[pool])<512
   mid=(0 if pool=='primary' else 512)+len(self.blocks[pool]);self.blocks[pool].append(tuple(entries));self.attrs[pool].append(attr);self.block_lookup[k]=mid;return mid
 ground_native.install(game,pals);grid=np.zeros((H,W),np.uint16)
 probe=packing.Probe();layers.pack(comp,probe,pals,grid,S,composite_bank=1)
 palette_maps,packing_report=packing.optimize(probe)
 (S/'palette-index-map.json').write_text(json.dumps(packing_report,indent=2)+'\n')
 print('Lossless packing:',packing_report['unique_tiles_before'],packing_report['unique_tiles_after'],flush=True)
 packer=CityPacker(pals)
 # Keep tower palette 7 intact; unused bank 1 holds exact under-canopy composites.
 result=layers.pack(comp,packer,pals,grid,S,composite_bank=1)
 assert sum(len(a) for a in packer.tiles.values())<=1008,('Full city scenery budget',sum(len(a) for a in packer.tiles.values()),__import__('collections').Counter(b for ts in packer.tiles.values() for b,_ in ts))
 if not packer.blocks['secondary']:
  packer.blocks['secondary'].append((0,)*8);packer.attrs['secondary'].append(0)
 packing.apply_palettes(pals,palette_maps)
 for kind,banks_used in [('primary',range(6)),('secondary',range(6,13))]:native.write_tileset(game,kind,'violet_city',packer.tiles[kind],packer.blocks[kind],packer.attrs[kind],pals,banks_used)
 register(game)
 folder=game/'data/layouts/VioletCity';folder.mkdir(exist_ok=True)
 # Actual map writes go through porygon's checked binary API.
 from porygon.core.blockdata import Blockdata
 raw=grid.astype('<u2').tobytes();bd=Blockdata.decode(raw,W,H);assert bd.encode()==raw;(folder/'map.bin').write_bytes(bd.encode());(folder/'border.bin').write_bytes(grid[4:6,2:4].astype('<u2').tobytes())
 lay={'id':'LAYOUT_VIOLET_CITY','name':'VioletCity_Layout','width':W,'height':H,'build_target':'emerald','primary_tileset':'gTileset_VioletCityPrimary','secondary_tileset':'gTileset_VioletCity','border_filepath':'data/layouts/VioletCity/border.bin','blockdata_filepath':'data/layouts/VioletCity/map.bin'}
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())
 layouts['layouts']=[l for l in layouts['layouts'] if l['id']!=lay['id']]+[lay];(game/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
 groups=json.loads((game/'data/maps/map_groups.json').read_text());group=groups['gMapGroup_Cherrygrove']
 if 'VioletCity' not in group:group.append('VioletCity')
 (game/'data/maps/map_groups.json').write_text(json.dumps(groups,indent=2)+'\n')
 m=json.loads((game/'data/maps/VioletCityEntrance/map.json').read_text());m.update(id='MAP_VIOLET_CITY',name='VioletCity',layout='LAYOUT_VIOLET_CITY',warp_events=[{'x':74,'y':56,'elevation':0,'dest_map':'MAP_VIOLET_EAST_GATE','dest_warp_id':'0'}],bg_events=[{'type':'sign','x':x,'y':y,'elevation':0,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'VioletCity_'+label} for x,y,label in signs])
 mf=game/'data/maps/VioletCity';mf.mkdir(exist_ok=True);(mf/'map.json').write_text(json.dumps(m,indent=2)+'\n')
 (mf/'scripts.pory').write_text('raw `VioletCity_MapScripts::\n    .byte 0\n`\n\n'+''.join('script VioletCity_'+name+' {\n    msgbox("'+text+'", MSGBOX_SIGN)\n    end\n}\n\n' for name,text in [('University','VIOLET UNIVERSITY\\nMain hall, library and classrooms.'),('Tower','SPROUT TOWER'),('Library','LIBRARY AND CLASSROOMS\\nInside the main university hall.'),('Lecture','LECTURE HALL\\nBATTLE PRACTICUM\\nFormer VIOLET GYM'),('City','VIOLET CITY'),('Practice','UNIVERSITY PRACTICE COURT\\nObserve. Practice. Discuss.'),('Route36','ROUTE 36\\nWest through the gate.'),('Route32','ROUTE 32\\nSouth toward UNION CAVE.')]))
 script=mf/'scripts.pory';script.write_text(script.read_text().rstrip()+'\n')
 subprocess.run([str(game/'tools/poryscript/poryscript'),'-i','data/maps/VioletCity/scripts.pory','-o','data/maps/VioletCity/scripts.inc','-fc','tools/poryscript/font_config.json','-cc','tools/poryscript/command_config.json'],cwd=game,check=True)
 ep=game/'data/event_scripts.s';text=ep.read_text();inc='.include "data/maps/VioletCity/scripts.inc"\n'
 if inc not in text:ep.write_text(text+inc)
 proof=game/'src/apocrypha_map_proof.c';text=proof.read_text()
 if 'MAP_VIOLET_CITY};' not in text:proof.write_text(text.replace('MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};','MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, MAP_VIOLET_CITY};'))
 # Gate destination wiring is the only existing-map change; IDs and its room stay intact.
 gatepath=game/'data/maps/VioletEastGate/map.json';m=json.loads(gatepath.read_text())
 for i in (0,1):m['warp_events'][i]['dest_map']='MAP_VIOLET_CITY'
 gatepath.write_text(json.dumps(m,indent=2)+'\n')
 (S/'exits.json').write_text(json.dumps(route_exits,indent=2)+'\n')
 np.save(S/'plan.npy',plan);np.save(S/'solid.npy',solid);(S/'landmarks.json').write_text(json.dumps(anchors,indent=2)+'\n')
 image=Tileset(game,'violet_city','violet_city').map_image(grid.ravel().tolist(),W);image.save(EV/'native-overview.png')
 report={'base':'aa8ea35eea378b5d69c58b5f5c0c2f566689c6ac','size':[W,H],'tiles':{k:len(v) for k,v in packer.tiles.items()},'metatiles':{k:len(v) for k,v in packer.blocks.items()},'complete_trees':len(trees)+len(campus_trees),'layers':result,'buildings':anchors,'source':'HGSS geography reference with east campus extension; HGSS Violet houses and gate; Cherrygrove green trees and HGSS Center; shared Johto Mart; bridge finials and native lily pads','interiors':'not implemented; entrances closed except east gate','new_map_id':group.index('VioletCity'),'teaching_court':[55,48,12,7]}
 # A successful regeneration updates only hashes for this authoring manifest.
 if guard.exists():guard.write_text(json.dumps({p:digest(game/p) for p in json.loads(guard.read_text())},indent=2)+'\n')
 (EV/'assembly.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

def register(game):
 for filename in ['graphics.h','metatiles.h','headers.h']:
  path=game/'src/data/tilesets'/filename;s=path.read_text();mark='// Violet City exterior\n'
  if mark in s:s=s[:s.index(mark)]
  block=''
  for kind,sym,secondary in [('primary','VioletCityPrimary','FALSE'),('secondary','VioletCity','TRUE')]:
   prefix=f'data/tilesets/{kind}/violet_city'
   if filename=='graphics.h':block+=f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{prefix}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("{prefix}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n'
   elif filename=='metatiles.h':block+=f'const u16 gMetatiles_{sym}[] = INCBIN_U16("{prefix}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{prefix}/metatile_attributes.bin");\n'
   else:block+=f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {secondary}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'
  path.write_text(s.rstrip()+'\n\n'+mark+block)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
