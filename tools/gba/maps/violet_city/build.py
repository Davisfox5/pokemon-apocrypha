#!/usr/bin/env python3
"""First native Violet exterior. New-map authoring only; never regenerate owner edits.
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
 for name,b in [('tree',3),('blossom',10),('house',6),('gable',6),('center',8),('mart',9)]:
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
 # Library is a second wing in the school's existing architectural vocabulary.
 A['library']=A['academy']
 # Repeat original bridge deck and urban paving, with no rotated staircase art.
 infrastructure=banks.Bank(11,'VIOLET_STONE_WOOD','secondary')
 for name,box in [('paving',(256,480,288,512)),('bridge',(608,304,656,336)),('rail_left',(600,304,608,336)),('rail_right',(656,304,664,336)),('island',(528,384,560,416)),('sign',(640,744,656,768))]:
  ar=np.array(ref.crop(box));infrastructure.add(name,ar)
 A.update(infrastructure.build());pals[11]=infrastructure.palette
 # Reuse Route 30's native freshwater glyphs and complete tree art exactly.
 rt=Tileset(game,'claude_route30','cherrygrove');pals[12]=Palette(12,rt.pals[1][12][1:],[str(j) for j in range(15)])
 for p in (ROOT/'gba/art/route30-hgss-blocks/source/materials').glob('pond-*.png'):
  ar=np.array(Image.open(p).convert('RGBA'));c=Canvas(16,16,pals[12]);colors=np.array(pals[12].gba(),int);mask=ar[:,:,3]>0;c.px[mask]=((ar[mask,:3].astype(int)[:,None]-colors[None])**2).sum(2).argmin(1);A[p.stem]=c
 # Original Emerald cliff courses reused at original colors.
 donor=Tileset(game);rb=banks.Bank(2,'EMERALD_ROCK','primary')
 for name,mid in [('rock',0x7c),('rock_w',0x76),('rock_e',0x75),('ledge',0x87)]:
  ar=np.array(donor.render(mid).convert('RGBA'));g=ar[:,:,1].astype(int);ar[:,:,3][(g>ar[:,:,0].astype(int)+15)&(g>ar[:,:,2].astype(int)+15)]=0;rb.add(name,ar)
 A.update(rb.build());pals[2]=rb.palette
 # Snap new palette colors to GBA RGB555 before lossless compilation.
 for pal in pals.values():pal.colors=[tuple(v//8*8 for v in color) for color in pal.colors]
 # Preserve editable native indexed assets and compile new landmarks with Porytiles.
 material=S/'materials';material.mkdir(exist_ok=True)
 for name,c in A.items():Image.fromarray(c.to_rgba()).save(material/f'{name}.png')
 psrc=S/'porytiles-landmarks';psrc.mkdir(exist_ok=True);bot=Image.new('RGBA',(128,320));top=bot.copy();mid=bot.copy()
 atlas=[]
 for key in ['tower','academy']:
  c=A[key];ar=c.to_rgba()
  for y in range(0,c.h,16):
   for x in range(0,c.w,16):atlas.append((key,x,y,ar[y:y+16,x:x+16]))
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
 rect('.',54,34,22,16);rect('P',51,43,22,4);rect('P',68,43,5,13);rect('Q',56,48,9,7)
 rect('.',21,67,5,5);rect('P',22,67,3,3)
 buildings=[('tower','Sprout Tower',36,1,3,11),('gym','Lecture Hall',28,36,3,5),('academy','University',44,35,4,6),('library','Library',60,35,4,6),('mart','Poke Mart',20,37,1,3),('center','Pokemon Center',46,50,3,5),('house','West Residence',9,34,1,4),('gable','South Residence',34,57,2,4)]
 for key,label,x,y,dx,dy in buildings:
  c=A[key];rect('.',x,y,c.w//16,c.h//16)
  rect('P',x+dx,y+c.h//16,2,2)
 # Connect each approach to the HGSS road spine, explicit grid geometry.
 rect('P',37,13,5,4);rect('P',20,40,3,5);rect('P',28,41,7,4);rect('P',44,41,7,5);rect('P',60,41,7,5);rect('P',47,55,5,4);rect('P',10,39,7,3);rect('P',36,62,7,3)
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
   elif ch in ['P','Q']:
    src=A['paving' if ch=='P' else 'island'];c=Canvas(16,16,src.pal);c.px=src.px[y%2*16:y%2*16+16,x%2*16:x%2*16+16].copy()
    # Native cell edge masks: curb encloses the road, grass remains outside it.
    if ch=='P':
     yy,xx=np.indices((16,16));dist=np.full((16,16),99)
     for neighbor,edge in [((x,y-1),yy),((x,y+1),15-yy),((x-1,y),xx),((x+1,y),15-xx)]:
      nx,ny=neighbor
      if not (0<=nx<W and 0<=ny<H and plan[ny,nx] in ['P','B','Q']):dist=np.minimum(dist,edge)
     c.px[dist==0]=0
     pal=np.array(c.pal.gba(),int);rim=int(((pal-np.array([144,136,120]))**2).sum(1)[1:].argmin()+1);c.px[dist==1]=rim
    if ch=='Q' and 31<=x<43 and 23<=y<29:
     # Keep the original island footprint, giving the stone platform a readable rim.
     yy,xx=np.indices((16,16));edge=((x==31)&(xx<2))|((x==42)&(xx>13))|((y==23)&(yy<2))|((y==28)&(yy>12))
     if x in [38,39,40]:
      if y==23:edge&=yy>=2
      if y==28:edge&=yy<=12
     pal=np.array(c.pal.gba(),int);dark=int(((pal-np.array([96,96,112]))**2).sum(1)[1:].argmin()+1);c.px[edge]=dark
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
 for x,y in trees:stamp('tree',x,y,True);mc.above[y,x:x+2]=True
 # Whole blossom trees punctuate the campus; all are outside building footprints.
 pink=[(54,36),(54,40),(74,36),(74,40),(54,50),(66,50)]
 for x,y in pink:
  stamp('blossom',x,y,True);solid[y+1:y+3,x:x+2]=True;mc.above[y,x:x+2]=True
 anchors=[]
 for key,label,x,y,dx,dy in buildings:
  c=A[key];stamp(key,x,y,True);cw,ch=c.w//16,c.h//16
  solid[y+1:y+ch,x:x+cw]=True;mc.above[y,x:x+cw]=True
  # Door threshold remains closed until that building's interior is authored.
  anchors.append({'name':label,'asset':key,'box':[x,y,cw,ch],'door':[x+dx,y+dy],'approach':[x+dx,y+ch]})
 # No open edges toward unbuilt Routes 32/36. Original rock makes the boundaries legible.
 for x in range(21,26):stamp('rock',x,70);solid[70,x]=True
 for y in range(28,32):stamp('rock_e',8,y);solid[y,8]=True
 # Campus courts reuse native paving; no trainer content/encounters invented.
 # Stone signs at campus, tower and arrival; their locations remain off the main walk line.
 signs=[(43,43,'University'),(35,14,'Tower'),(65,43,'Library'),(27,42,'Lecture'),(70,59,'City')]
 for x,y,label in signs:
  stamp('sign',x,y-1,True);solid[y,x]=True;mc.above[y-1,x]=True
 # Gate facade reuses the complete accepted gable module, with its real door anchor.
 A['gate']=A['gable']
 stamp('gate',72,52,True);solid[53:57,73:77]=True;solid[56,74]=False;beh[56,74]=0x60;mc.above[52,72:77]=True
 mc.fore_bank=fg.bank;mc.fore_idx=fg.idx
 # Opaque gate module includes its authored floor, no third background layer.
 comp={'W':W,'H':H,'canvas':mc,'cells':cells,'behavior':beh,'solid':solid,'tag':'VioletCity'}
 # New city-only tile pools. Reuse accepted pixels; never repack shared map tilesets.
 class CityPacker(native.Packer):
  def tile(self,bank,arr,pos=None):
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
 ground_native.install(game,pals);packer=CityPacker(pals);grid=np.zeros((H,W),np.uint16)
 # Keep tower palette 7 intact; unused bank 1 holds exact under-canopy composites.
 result=layers.pack(comp,packer,pals,grid,S,composite_bank=1)
 if not packer.blocks['secondary']:
  packer.blocks['secondary'].append((0,)*8);packer.attrs['secondary'].append(0)
 for kind,banks_used in [('primary',range(6)),('secondary',range(6,13))]:native.write_tileset(game,kind,'violet_city',packer.tiles[kind],packer.blocks[kind],packer.attrs[kind],pals,banks_used)
 register(game)
 folder=game/'data/layouts/VioletCity';folder.mkdir(exist_ok=True)
 # Actual map writes go through porygon's checked binary API.
 from porygon.core.blockdata import Blockdata
 raw=grid.astype('<u2').tobytes();bd=Blockdata.decode(raw,W,H);assert bd.encode()==raw;(folder/'map.bin').write_bytes(bd.encode());(folder/'border.bin').write_bytes(struct.pack('<4H',*[int(grid[2,2])]*4))
 lay={'id':'LAYOUT_VIOLET_CITY','name':'VioletCity_Layout','width':W,'height':H,'build_target':'emerald','primary_tileset':'gTileset_VioletCityPrimary','secondary_tileset':'gTileset_VioletCity','border_filepath':'data/layouts/VioletCity/border.bin','blockdata_filepath':'data/layouts/VioletCity/map.bin'}
 layouts=json.loads((game/'data/layouts/layouts.json').read_text())
 layouts['layouts']=[l for l in layouts['layouts'] if l['id']!=lay['id']]+[lay];(game/'data/layouts/layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
 groups=json.loads((game/'data/maps/map_groups.json').read_text());group=groups['gMapGroup_Cherrygrove']
 if 'VioletCity' not in group:group.append('VioletCity')
 (game/'data/maps/map_groups.json').write_text(json.dumps(groups,indent=2)+'\n')
 m=json.loads((game/'data/maps/VioletCityEntrance/map.json').read_text());m.update(id='MAP_VIOLET_CITY',name='VioletCity',layout='LAYOUT_VIOLET_CITY',warp_events=[{'x':74,'y':56,'elevation':0,'dest_map':'MAP_VIOLET_EAST_GATE','dest_warp_id':'0'}],bg_events=[{'type':'sign','x':x,'y':y,'elevation':0,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'VioletCity_'+label} for x,y,label in signs])
 mf=game/'data/maps/VioletCity';mf.mkdir(exist_ok=True);(mf/'map.json').write_text(json.dumps(m,indent=2)+'\n')
 (mf/'scripts.pory').write_text('raw `VioletCity_MapScripts::\n    .byte 0\n`\n\n'+''.join('script VioletCity_'+name+' {\n    msgbox("'+text+'", MSGBOX_SIGN)\n    end\n}\n\n' for name,text in [('University','VIOLET UNIVERSITY'),('Tower','SPROUT TOWER'),('Library','UNIVERSITY LIBRARY'),('Lecture','LECTURE HALL\\nBATTLE PRACTICUM'),('City','VIOLET CITY')]))
 script=mf/'scripts.pory';script.write_text(script.read_text().rstrip()+'\n')
 subprocess.run([str(game/'tools/poryscript/poryscript'),'-i',str(mf/'scripts.pory'),'-o',str(mf/'scripts.inc'),'-fc',str(game/'tools/poryscript/font_config.json'),'-cc',str(game/'tools/poryscript/command_config.json')],check=True)
 ep=game/'data/event_scripts.s';text=ep.read_text();inc='.include "data/maps/VioletCity/scripts.inc"\n'
 if inc not in text:ep.write_text(text+inc)
 proof=game/'src/apocrypha_map_proof.c';text=proof.read_text()
 if 'MAP_VIOLET_CITY};' not in text:proof.write_text(text.replace('MAP_CHERRYGROVE_REGIONAL_PREVIEW_30};','MAP_CHERRYGROVE_REGIONAL_PREVIEW_30, MAP_VIOLET_CITY};'))
 # Gate destination wiring is the only existing-map change; IDs and its room stay intact.
 gatepath=game/'data/maps/VioletEastGate/map.json';m=json.loads(gatepath.read_text())
 for i in (0,1):m['warp_events'][i]['dest_map']='MAP_VIOLET_CITY'
 gatepath.write_text(json.dumps(m,indent=2)+'\n')
 np.save(S/'plan.npy',plan);np.save(S/'solid.npy',solid);(S/'landmarks.json').write_text(json.dumps(anchors,indent=2)+'\n')
 image=Tileset(game,'violet_city','violet_city').map_image(grid.ravel().tolist(),W);image.save(EV/'native-overview.png')
 report={'base':'aa8ea35eea378b5d69c58b5f5c0c2f566689c6ac','size':[W,H],'tiles':{k:len(v) for k,v in packer.tiles.items()},'metatiles':{k:len(v) for k,v in packer.blocks.items()},'complete_trees':len(trees)+len(pink),'layers':result,'buildings':anchors,'source':'HGSS geography reference with east campus extension; shared Cherrygrove exact assets; native Emerald rocks','interiors':'not implemented; entrances closed except east gate','new_map_id':group.index('VioletCity')}
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
