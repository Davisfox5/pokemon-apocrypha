#!/usr/bin/env python3
"""Native Route 36, surveyed from HGSS and built from approved Johto materials."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from claude_cherrygrove import build as native,ground
from claude_cherrygrove.pixel import Canvas,Palette
from route30_hgss_blocks import ground_native,layers
from tiles import Tileset
OUT=ROOT/'gba/art/route36';S=OUT/'source';E=OUT/'evidence';W,H=82,32
BASE='ac6e1ee42257ba3551452a9f193b8d9c3a3fd1e3'
def dump(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n') if p.suffix=='.pal' else p.read_bytes()).hexdigest()
def main(game):
 guard=S/'generated-files.json'
 if guard.exists():
  changed=[p for p,h in json.loads(guard.read_text()).items() if not (game/p).exists() or digest(game/p)!=h]
  assert not changed,('Preserving later authored edits',changed)
 elif (game/'data/maps/JohtoRoute36').exists():raise SystemExit('Existing Route 36 has no authoring manifest; preserve it.')
 t=Tileset(game,'claude_route30','cherrygrove')
 pals={i:Palette(i,t.pals[i>=6][i][1:],[str(j) for j in range(15)]) for i in range(13)}
 assets={};materials=S/'materials';materials.mkdir(exist_ok=True)
 def import_asset(name,path,bank):
  rgba=np.array(Image.open(path).convert('RGBA'));c=Canvas(rgba.shape[1],rgba.shape[0],pals[bank]);mask=rgba[:,:,3]>0;colors=np.array(pals[bank].gba(),int)
  ids=((rgba[mask,:3].astype(int)[:,None]-colors[None,1:])**2).sum(2).argmin(1)+1;c.px[mask]=ids
  assert np.array_equal(c.to_rgba()[mask,:3],rgba[mask,:3]),('Import color mismatch',name)
  assets[name]=c;Image.fromarray(c.to_rgba()).save(materials/(name+'.png'));return c
 r30=ROOT/'gba/art/route30-hgss-blocks/source/materials'
 for name,bank in [('tree',3),('sign',5),('apricorn',3)]+[(f'flower-{i}',4) for i in range(4)]+[(f'grass-{i:04b}',12) for i in range(16)]+[(f'cliff-{d}-0',8) for d in ['west','east','cap']]+[(f'step-{d}',8) for d in ['left','middle','right']]:import_asset(name,r30/(name+'.png'),bank)
 gate=ROOT/'gba/art/violet-city/source/preserved-west-gate.png';rgba=np.array(Image.open(gate).convert('RGBA'));colors=[tuple(map(int,c)) for c in np.unique(rgba[rgba[:,:,3]>0,:3],axis=0)];colors+= [colors[-1]]*(15-len(colors));pals[9]=Palette(9,colors,[str(i) for i in range(15)]);import_asset('gate',gate,9)
 # Whole-tree clearings and path centerlines transcribed from the HGSS overview.
 plan=np.full((H,W),'T',dtype='<U1')
 def rect(ch,x,y,w,h):plan[y:y+h,x:x+w]=ch
 def poly(ch,points):
  m=Image.new('1',(W,H));ImageDraw.Draw(m).polygon(points,fill=1);plan[np.array(m,dtype=bool)]=ch
 poly('.',[(16,0),(28,0),(28,4),(30,5),(32,7),(34,10),(35,12),(37,16),(44,17),(44,19),(50,19),(50,16),(81,16),(81,22),(63,22),(62,25),(62,31),(56,31),(56,24),(53,22),(49,22),(48,21),(44,21),(44,23),(33,24),(33,16),(30,15),(16,15)])
 rect('.',0,10,14,15);rect('.',7,23,7,9);rect('.',15,16,18,9)
 rect('T',0,16,8,16);rect('T',12,10,3,12);rect('T',16,11,16,4)
 rect('T',20,5,10,5);rect('T',26,17,6,5)
 rect('.',34,15,11,2);rect('T',34,16,10,3);rect('.',44,16,2,7)
 rect('P',18,0,3,4);rect('P',18,3,9,2)
 rect('P',0,14,12,2);rect('P',9,14,3,10);rect('P',9,22,24,2);rect('P',9,24,3,8)
 rect('P',53,19,28,3);rect('P',57,21,4,10)
 rect('G',15,18,11,4)
 rect('T',16,15,16,3);rect('T',14,24,20,4)
 # Surveyed raised west terrace: continuous wall ends at the stair opening.
 rect('R',14,3,1,19);rect('R',0,4,15,1);rect('R',32,16,1,6)
 rect('S',14,22,1,2);rect('S',32,22,1,2)
 # Complete gate footprints; the right one leads to Violet, other destinations pending.
 gates=[{'name':'Violet gate','at':[75,15],'flip':True,'door':[75,20],'active':True},
        {'name':'National Park gate','at':[0,9],'flip':False,'door':[6,14],'active':False},
        {'name':'Alph gate','at':[56,25],'flip':False,'door':[59,30],'active':False}]
 # Alph uses a north-facing gate facade from the accepted regional house family.
 for g in gates[:2]:
  x,y=g['at'];rect('.',x,y,7,7)
 rect('P',6,14,6,2);rect('P',72,19,4,3)
 # Keep the reference's eastern flower strip outside the walking line.
 flowers=[(x,17+(x%3==0)) for x in range(53,70,2)]
 signs=[{'at':[23,1],'name':'North','text':'ROUTE 37\\nNorth toward ECRUTEAK CITY.'},
        {'at':[7,12],'name':'Park','text':'NATIONAL PARK\\nWest through the gate.'},
        {'at':[70,17],'name':'Violet','text':'ROUTE 36\\nEast: VIOLET CITY'},
        {'at':[55,20],'name':'Alph','text':'RUINS OF ALPH\\nSouth through the gate.'}]
 mc=native.MapCanvas(W,H);fg=native.MapCanvas(W,H);solid=np.zeros((H,W),bool);beh=np.zeros((H,W),np.uint8);cells=np.full((H,W),ground.GRASS,np.int8);cells[np.isin(plan,['P','S'])]=ground.PATH
 def put(name,x,y,front=False,flip=False):
  c=assets[name];mc.blit(c,x*16,y*16,flip=flip)
  if front:fg.blit(c,x*16,y*16,flip=flip)
 for y in range(H):
  for x in range(W):
   ch=plan[y,x]
   if ch=='G':
    bits=''.join(str(int(0<=xx<W and 0<=yy<H and plan[yy,xx]=='G')) for xx,yy in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)])
    put('grass-'+bits,x,y);beh[y,x]=2
   elif ch=='R':put('cliff-'+('cap' if y==4 else 'east' if x==14 else 'west')+'-0',x,y);solid[y,x]=True
 # Existing Emerald treads used by the route family, quarter-turned for east/west travel.
 stair=Canvas(16,32,pals[8]);stair.px=np.rot90(np.concatenate([assets['step-left'].px,assets['step-middle'].px],axis=1)).copy();assets['stair']=stair
 for x in [14,32]:
  put('stair',x,22);put('cliff-'+('east' if x==14 else 'west')+'-0',x,24);solid[24,x]=True
 for i,(x,y) in enumerate(flowers):put('flower-'+str(i%4),x,y)
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 trees=[[x,15] for x in range(15,33,2)]
 for y in range(0,H-2,2):
  for x in range(0,W-1,2):
   overlap=any(x<tx+2 and tx<x+2 and y+1<ty+3 and ty+1<y+3 for tx,ty in trees)
   if not overlap and (plan[y:y+3,x:x+2]=='T').all():trees.append([x,y])
 for x,y in sorted(trees,key=lambda v:(v[1],v[0])):
  put('tree',x,y,True);solid[y+1:y+3,x:x+2]=True;mc.above[y,x:x+2]=True
 # Unfilled slivers become lawn, never invisible forest blockers. Outer edge
 # collision is the boundary of this isolated map, with onward routes pending.
 solid[0,:]=True;solid[-1,:]=True;solid[:,0]=True;solid[:,-1]=True
 for g in gates[:2]:
  x,y=g['at'];put('gate',x,y,True,g['flip']);solid[y+1:y+7,x:x+7]=True;mc.above[y,x:x+7]=True
  if g['active']:solid[20,75]=False;beh[20,75]=0x62
 # North/south gate variant uses the same teal roof and masonry modules,
 # with a central passage rather than a residential gable.
 c=Canvas(80,96,pals[9]);c.px=assets['gate'].px[8:104,8:88].copy()
 colors=np.array(pals[9].gba(),int)
 def tone(rgb):return str(int(((colors[1:]-np.array(rgb))**2).sum(1).argmin()))
 c.rect(28,76,24,20,tone((88,80,56)));c.rect(30,78,20,18,tone((48,80,88)))
 c.rect(32,80,16,16,tone((56,64,48)));c.rect(28,94,24,2,tone((160,168,160)))
 assets['alph_gate']=c;Image.fromarray(c.to_rgba()).save(materials/'alph_gate.png')
 put('alph_gate',57,25,True);solid[26:31,57:62]=True;mc.above[25,57:62]=True
 for sign in signs:
  x,y=sign['at'];put('sign',x,y-1,True);solid[y,x]=True;mc.above[y-1,x]=True
 # Native apricorn silhouette at the original central grassy branch; no harvest script yet.
 put('apricorn',31,9,True);solid[10,31]=True;mc.above[9,31]=True
 mc.fore_bank=fg.bank;mc.fore_idx=fg.idx
 comp={'W':W,'H':H,'canvas':mc,'cells':cells,'solid':solid,'behavior':beh,'tag':'Route36'}
 ground_native.install(game,pals)
 class RoutePacker(native.Packer):
  def tile(self,bank,arr,pos=None):
   for hf in (0,1):
    for vf in (0,1):
     a=arr[::-1] if vf else arr;a=a[:,::-1] if hf else a;k=a.tobytes()
     if k in self.lookup:return self.lookup[k]|hf<<10|vf<<11
   count=sum(len(v) for v in self.tiles.values());assert count<1008,('scenery capacity',count)
   pool='primary' if len(self.tiles['primary'])<512 else 'secondary';tid=(0 if pool=='primary' else 512)+len(self.tiles[pool]);self.tiles[pool].append((bank,arr.copy()));self.lookup[arr.tobytes()]=tid;return tid
  def metatile(self,entries,attr):
   k=(tuple(entries),attr)
   if k in self.block_lookup:return self.block_lookup[k]
   pool='primary' if len(self.blocks['primary'])<512 else 'secondary';assert len(self.blocks[pool])<512
   mid=(0 if pool=='primary' else 512)+len(self.blocks[pool]);self.blocks[pool].append(tuple(entries));self.attrs[pool].append(attr);self.block_lookup[k]=mid;return mid
 packer=RoutePacker(pals);grid=np.zeros((H,W),np.uint16);report=layers.pack(comp,packer,pals,grid,S,composite_bank=1)
 if not packer.blocks['secondary']:packer.blocks['secondary'].append((0,)*8);packer.attrs['secondary'].append(0)
 for kind,brange in [('primary',range(6)),('secondary',range(6,13))]:native.write_tileset(game,kind,'johto_route36',packer.tiles[kind],packer.blocks[kind],packer.attrs[kind],pals,brange)
 register(game)
 from porygon.core.blockdata import Blockdata
 laydir=game/'data/layouts/JohtoRoute36';laydir.mkdir(exist_ok=True);raw=grid.astype('<u2').tobytes();(laydir/'map.bin').write_bytes(Blockdata.decode(raw,W,H).encode());(laydir/'border.bin').write_bytes(grid[2:4,2:4].astype('<u2').tobytes())
 lj=game/'data/layouts/layouts.json';layouts=json.loads(lj.read_text())
 layout={'id':'LAYOUT_JOHTO_ROUTE36','name':'JohtoRoute36_Layout','width':W,'height':H,'build_target':'emerald','primary_tileset':'gTileset_JohtoRoute36Primary','secondary_tileset':'gTileset_JohtoRoute36','border_filepath':'data/layouts/JohtoRoute36/border.bin','blockdata_filepath':'data/layouts/JohtoRoute36/map.bin'}
 gate_layout=next(l.copy() for l in layouts['layouts'] if l['id']=='LAYOUT_VIOLET_EAST_GATE');gate_layout.update(id='LAYOUT_VIOLET_WEST_GATE',name='VioletWestGate_Layout')
 layouts['layouts']=[l for l in layouts['layouts'] if l['id'] not in [layout['id'],gate_layout['id']]]+[layout,gate_layout];dump(lj,layouts)
 groups_path=game/'data/maps/map_groups.json';groups=json.loads(groups_path.read_text());group=groups['gMapGroup_Cherrygrove']
 for name in ['JohtoRoute36','VioletWestGate']:
  if name not in group:group.append(name)
 dump(groups_path,groups)
 route=json.loads((game/'data/maps/VioletCity/map.json').read_text());route.update(id='MAP_JOHTO_ROUTE36',name='JohtoRoute36',layout='LAYOUT_JOHTO_ROUTE36',music='MUS_ROUTE101',region_map_section='MAPSEC_JOHTO_ROUTE_36',map_type='MAP_TYPE_ROUTE',warp_events=[{'x':75,'y':20,'elevation':0,'dest_map':'MAP_VIOLET_WEST_GATE','dest_warp_id':'0'}],bg_events=[{'type':'sign','x':v['at'][0],'y':v['at'][1],'elevation':0,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'JohtoRoute36_'+v['name']} for v in signs])
 dump(game/'data/maps/JohtoRoute36/map.json',route)
 script='raw `JohtoRoute36_MapScripts::\n    .byte 0\n`\n\n'+''.join('script JohtoRoute36_'+v['name']+' {\n    msgbox("'+v['text']+'", MSGBOX_SIGN)\n    end\n}\n\n' for v in signs)
 (game/'data/maps/JohtoRoute36/scripts.pory').write_text(script.rstrip()+'\n')
 subprocess.run([str(game/'tools/poryscript/poryscript'),'-i','data/maps/JohtoRoute36/scripts.pory','-o','data/maps/JohtoRoute36/scripts.inc','-fc','tools/poryscript/font_config.json','-cc','tools/poryscript/command_config.json'],cwd=game,check=True)
 gate_map=json.loads((game/'data/maps/VioletEastGate/map.json').read_text());gate_map.update(id='MAP_VIOLET_WEST_GATE',name='VioletWestGate',layout='LAYOUT_VIOLET_WEST_GATE')
 for i,w in enumerate(gate_map['warp_events']):w.update(dest_map='MAP_JOHTO_ROUTE36' if i<2 else 'MAP_VIOLET_CITY',dest_warp_id='0' if i<2 else '1')
 dump(game/'data/maps/VioletWestGate/map.json',gate_map);(game/'data/maps/VioletWestGate/scripts.inc').write_text('VioletWestGate_MapScripts::\n    .byte 0\n')
 # Patch only Violet's existing west threshold. No regenerated city artwork.
 cp=game/'data/layouts/VioletCity/map.bin';city=np.fromfile(cp,'<u2').reshape(72,80).copy();ct=Tileset(game,'violet_city','violet_city');oldmid=int(city[30,5]&1023);oldblock=ct.blocks[oldmid>=512][oldmid-512 if oldmid>=512 else oldmid]
 ap=game/'data/tilesets/secondary/violet_city/metatile_attributes.bin';mp=game/'data/tilesets/secondary/violet_city/metatiles.bin';attrs=np.frombuffer(ap.read_bytes(),'<u2').tolist();blocks=ct.blocks[1]
 newattr=(ct.attrs[oldmid>=512][oldmid-512 if oldmid>=512 else oldmid]&0xff00)|0x63
 match=next((i for i,(block,attr) in enumerate(zip(blocks,attrs)) if block==oldblock and attr==newattr),None)
 if match is None:
  import struct
  match=len(blocks);mp.write_bytes(mp.read_bytes()+struct.pack('<8H',*oldblock));ap.write_bytes(ap.read_bytes()+struct.pack('<H',newattr))
 city[30,5]=0x3000|512+match;cp.write_bytes(city.astype('<u2').tobytes())
 cp=game/'data/maps/VioletCity/map.json';citymap=json.loads(cp.read_text());citymap['warp_events']=citymap['warp_events'][:1]+[{'x':5,'y':30,'elevation':0,'dest_map':'MAP_VIOLET_WEST_GATE','dest_warp_id':'2'}];dump(cp,citymap)
 ep=game/'data/event_scripts.s';text=ep.read_text()
 for name in ['JohtoRoute36','VioletWestGate']:
  inc=f'.include "data/maps/{name}/scripts.inc"'
  if inc not in text:text+='\n'+inc+'\n'
 ep.write_text(text)
 proof=game/'src/apocrypha_map_proof.c';text=proof.read_text()
 if 'MAP_JOHTO_ROUTE36' not in text:text=text.replace('MAP_VIOLET_CITY};','MAP_VIOLET_CITY, MAP_JOHTO_ROUTE36, MAP_VIOLET_WEST_GATE};')
 proof.write_text(text)
 section=game/'src/data/region_map/region_map_sections.json';j=json.loads(section.read_text())
 entries=j['map_sections'];entry={'id':'MAPSEC_JOHTO_ROUTE_36','name':'ROUTE 36','x':1,'y':4,'width':1,'height':1}
 if not any(v['id']==entry['id'] for v in entries):entries.append(entry)
 dump(section,j)
 np.save(S/'plan.npy',plan);np.save(S/'solid.npy',solid);(S/'blocks.txt').write_text('\n'.join(''.join(row) for row in plan)+'\n');dump(S/'features.json',{'gates':gates,'signs':signs,'trees':trees,'stairs':[[14,22],[32,22]],'future_exits':[[19,1],[10,30]],'map_id':group.index('JohtoRoute36'),'gate_map_id':group.index('VioletWestGate')})
 image=Tileset(game,'johto_route36','johto_route36').map_image(grid.ravel().tolist(),W);image.save(E/'native-overview.png')
 report.update(size=[W,H],tiles={k:len(v) for k,v in packer.tiles.items()},metatiles={k:len(v) for k,v in packer.blocks.items()},tree_count=len(trees),base=BASE,source='HGSS reference geometry; exact accepted CG trees, ground and Route30 grass; existing Emerald-derived terrain family',pending='Other destination maps, NPCs, encounters, story barriers, apricorn harvest')
 dump(E/'assembly.json',report)
 paths=subprocess.check_output(['git','diff','--name-only',BASE],cwd=game,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=game,text=True).splitlines()
 dump(guard,{p:digest(game/p) for p in sorted(set(paths)) if (game/p).is_file()})
 print(json.dumps({k:report[k] for k in ['size','tiles','metatiles','tree_count']}))
def register(game):
 for filename in ['graphics.h','metatiles.h','headers.h']:
  p=game/'src/data/tilesets'/filename;s=p.read_text();marker='// Route 36 exterior\n'
  if marker in s:s=s[:s.index(marker)]
  block=''
  for kind,sym,secondary in [('primary','JohtoRoute36Primary','FALSE'),('secondary','JohtoRoute36','TRUE')]:
   prefix=f'data/tilesets/{kind}/johto_route36'
   if filename=='graphics.h':block+=f'const u32 gTilesetTiles_{sym}[] = INCGFX_U32("{prefix}/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'INCGFX_U16("{prefix}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n'
   elif filename=='metatiles.h':block+=f'const u16 gMetatiles_{sym}[] = INCBIN_U16("{prefix}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{prefix}/metatile_attributes.bin");\n'
   else:block+=f'const struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = {secondary}, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatileSymbols_PLACEHOLDER, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n'.replace('gMetatileSymbols_PLACEHOLDER','gMetatiles_'+sym)
  p.write_text(s.rstrip()+'\n\n'+marker+block)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
