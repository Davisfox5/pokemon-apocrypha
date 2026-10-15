"""Decode all native cave floors, audit physics/layers, and render readable evidence."""
from pathlib import Path
import sys,json,csv,subprocess
import numpy as np
from PIL import Image,ImageDraw
from config import FLOORS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
G,P=map(Path,sys.argv[1:3]);base='6abf7e84e27828356c1bb390b048611c1997d4e4';summaries={}
for key,c in FLOORS.items():
 W,H=c['size'];S=ROOT/f'gba/art/union-cave-{key}/source';E=S.parent/'evidence';t=Tileset(G,c['set'],c['set']);g=np.fromfile(G/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W);plan=np.load(S/'native-material-grid.npy');foot=np.load(S/'native-foot-blocked.npy');water=np.load(S/'native-water-plane.npy');im=t.map_image(list(map(int,g.ravel())),W);rgb=np.array(im);pm=np.array(Image.open(P/(c['name']+'.png')).convert('RGB'));diff=int(np.any(rgb!=pm,2).sum());assert diff==0,(key,diff);im.save(E/'native-map.png');ref=Image.open(S/'hgss-reference.png').convert('RGB');errors=[];rows=[];transparent=0;maxglyph=0;maxbank=0;behaviors=np.zeros(g.shape,np.uint8)
 for y in range(H):
  for x in range(W):
   v=int(g[y,x]);mid=v&1023;part=int(mid>=512);ix=mid-512 if part else mid;attr=t.attrs[part][ix];behavior=attr&255;behaviors[y,x]=behavior;blocked=bool(v&0xc00);onfoot=blocked or behavior in [16,17,18,21];elev=v>>12
   if onfoot!=bool(foot[y,x]):errors.append([x,y,'foot collision'])
   if water[y,x] and (behavior!=16 or blocked or elev!=1):errors.append([x,y,'Surf water collision/elevation'])
   if (x,y) in c['ladders'] and (behavior!=97 or blocked or elev!=3):errors.append([x,y,'stair warp behavior/elevation'])
   if not water[y,x] and not blocked and elev!=3:errors.append([x,y,'ordinary floor elevation'])
   for q,en in enumerate(t.blocks[part][ix]):
    tid=en&1023;bank=en>>12;maxglyph=max(maxglyph,tid);maxbank=max(maxbank,bank)
    if q<4:
     px=np.array(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid]);transparent+=int((px==0).sum())
   rows.append([x,y,str(plan[y,x]),mid,behavior,blocked,onfoot,elev,attr>>12])
 assert not errors,(key,errors);assert transparent==0 and maxglyph<1008 and maxbank<6
 with (S/'cell-ledger.csv').open('w',newline='') as f:
  writer=csv.writer(f,lineterminator='\n');writer.writerow(['native_x','native_y','reviewed_material','metatile','behavior','engine_collision','blocked_on_foot','elevation','BG_layer_type']);writer.writerows(rows)
 # Verify dictionary metadata against actual tile bytes and source geometry.
 dictionary=json.loads((S/'native-glyph-order.json').read_text())['glyphs'];lab=np.load(S/'hgss-pixel-materials.npy').astype('S1');lab[lab==b'O']=b'.'
 for sx,sy in c['ladders']:lab[sy*16:sy*16+16,sx*16:sx*16+16]=b'S'
 shape_bad=[];wall_cells=[];shade=[]
 for y in range(H):
  for x in range(W):
   mid=int(g[y,x])&1023;part=int(mid>=512);ix=mid-512 if part else mid
   if (lab[y*16:y*16+16,x*16:x*16+16]==b'R').any():wall_cells.append((x,y))
   for q,en in enumerate(t.blocks[part][ix][:4]):
    tid=en&1023;bank=en>>12;eb,px,mask=dictionary[tid];actual=bytes(t.tiles[int(tid>=512)][tid-512 if tid>=512 else tid]);assert actual==bytes.fromhex(px) and bank==eb,(key,tid,'actual tile/dictionary mismatch')
    expected=lab[y*16+q//2*8:y*16+q//2*8+8,x*16+q%2*8:x*16+q%2*8+8].tobytes()
    if bytes.fromhex(mask)!=expected:shape_bad.append([x,y,q])
 assert not shape_bad,(key,'material silhouette mismatch',shape_bad)
 # Number every wall-containing native cell, with a reference/current pair.
 atlas=Image.new('RGB',(960,((len(wall_cells)+11)//12)*58+30),'#1a2125');ad=ImageDraw.Draw(atlas)
 clean=Image.open(S/'clean-terrain.png').convert('RGB')
 for i,(x,y) in enumerate(wall_cells):
  ax=i%12*80;ay=30+i//12*58;box=(x*16,y*16,x*16+16,y*16+16)
  atlas.paste(clean.crop(box).resize((32,32),Image.Resampling.NEAREST),(ax,ay));atlas.paste(im.crop(box).resize((32,32),Image.Resampling.NEAREST),(ax+34,ay));ad.text((ax,ay+34),f'{x},{y}',fill='white')
 ad.text((8,8),key.upper()+': every wall cell; cleaned HGSS source / decoded native',fill='white');atlas.save(E/'wall-cell-review.png')
 wall_report={'floor':key,'wall_containing_cells':len(wall_cells),'native_quadrants_checked':W*H*4,'actual_tile_bytes_match_geometry_dictionary':True,'wall_floor_water_void_silhouette_errors':shape_bad,'stair_coordinates':c['ladders'],'stair_art':'original Union Cave d_level01 stone treads; up/down variants; existing native warp behavior 97 retained','lighting':'shared wall palette ramps across ordinary ground and water banks; border-weighted shade reuse within identical material masks','limit':'interior shading uses a finite 1008-tile dictionary; not a pixel-exact screenshot import'};(E/'wall-review.json').write_text(json.dumps(wall_report,indent=2)+'\n')
 report={'floor':key,'native_cells':W*H,'basis':'visible original HGSS terrain trace; actual DS warp graph registered separately to original branch-end landmarks; not extracted original DS collision','native_physics_errors':errors,'Porymap_pixel_differences':diff,'opaque_background_zero_index_pixels':transparent,'maximum_static_tile':maxglyph,'maximum_BG_palette':maxbank,'water_cells':int(water.sum()),'water_contract':'collision=0, elevation=1, MB_POND_WATER; ordinary land elevation=3. Walking is blocked by elevation; Surf and disembark verified in native runtime.','foreground_geometry':'cleaned complete rock silhouettes in foreground; original HGSS Union Cave d_level01 stone-step texture at registered floor transitions','terrain_classification_limit':'mixed pixels, occlusion and projection remain interpreted; the source grid is not a claim of exact original DS collision','unqualified':['campaign Surf badge/party activation','Strength pushing','off-image upper Alph transit rooms','Route33 exterior'],'water_animation':'static'};(E/'audit.json').write_text(json.dumps(report,indent=2)+'\n');summaries[key]=report
 out=Image.new('RGB',(W*32+44,H*16+64),'#1a2125');d=ImageDraw.Draw(out);out.paste(ref,(10,32));out.paste(im,(W*16+30,32));d.text((10,10),'HGSS Union Cave '+key.upper(),fill='white');d.text((W*16+30,10),'Native Gen 3 reconstruction',fill='white');out.save(E/'comparison.png')
 # Each numbered half gives a readable source/native comparison at 1x.
 for n,start in enumerate(range(0,H,20),1):
  count=min(20,H-start);out=Image.new('RGB',(W*32+44,count*16+68),'#1a2125');d=ImageDraw.Draw(out);box=(0,start*16,W*16,(start+count)*16);out.paste(ref.crop(box),(10,30));out.paste(im.crop(box),(W*16+30,30));d.text((10,8),f'HGSS {key.upper()} rows {start}-{start+count-1}',fill='white');d.text((W*16+30,8),'Native: material, shore and rock geometry',fill='white');out.save(E/f'material-comparison-{n}.png')
# Preserve every unrelated layout and shared tileset byte-for-byte.
protected=['data/layouts/JohtoRoute32','data/maps/JohtoRoute32','data/tilesets/primary/route32','data/tilesets/secondary/route32','data/tilesets/primary/cherrygrove','data/tilesets/secondary/cherrygrove','src/field_door.c']
for p in protected:assert not subprocess.check_output(['git','-C',str(G),'diff',base,'--',p]),p
old=json.loads(subprocess.check_output(['git','-C',str(G),'show',base+':data/maps/map_groups.json'],text=True));new=json.loads((G/'data/maps/map_groups.json').read_text());assert new['gMapGroup_Cherrygrove'][:len(old['gMapGroup_Cherrygrove'])]==old['gMapGroup_Cherrygrove']
for group in old:
 if group!='gMapGroup_Cherrygrove':assert old[group]==new[group],group
oldlayouts=json.loads(subprocess.check_output(['git','-C',str(G),'show',base+':data/layouts/layouts.json'],text=True))['layouts'];newlayouts=json.loads((G/'data/layouts/layouts.json').read_text())['layouts'];assert newlayouts[:len(oldlayouts)]==oldlayouts
for key,c in FLOORS.items():
 m=json.loads((G/'data/maps'/c['name']/'map.json').read_text())
 for w in m['warp_events']:
  dest=next((c2 for c2 in FLOORS.values() if c2['id']==w['dest_map']),None)
  if dest:
   dm=json.loads((G/'data/maps'/dest['name']/'map.json').read_text());return_warp=dm['warp_events'][int(w['dest_warp_id'])];assert return_warp['dest_map']==c['id']
E=ROOT/'gba/art/union-cave-1f/evidence';(E/'all-floors-audit.json').write_text(json.dumps({'floors':summaries,'protected_paths':protected,'existing_map_ids_preserved':True,'total_reviewed_cells':sum(q['native_cells'] for q in summaries.values()),'visible_stair_pairs_bidirectional':True,'source_base':base},indent=2)+'\n')
# Focused entrance and rock review: original, accepted first pass, current.
S=E.parent/'source';original=Image.open(S/'hgss-reference.png');before=Image.open(E/'previous-de6922a/native-map.png');after=Image.open(E/'native-map.png');regions=[('Route32 threshold',(416,256,512,336)),('Northern branch / actual stair position',(48,48,176,128)),('Beige boulder retained as rock',(64,224,144,288)),('Small clusters / wall-to-floor edge',(176,256,432,320)),('Southern beige boulder',(432,560,512,640)),('Water-separated southern stair',(48,880,144,944)),('Southern lighted threshold',(416,880,512,960))];out=Image.new('RGB',(1540,len(regions)*210+32),'#1a2125');d=ImageDraw.Draw(out)
for i,(title,box) in enumerate(regions):
 y=i*210+10
 for x,img,label in [(10,original,'HGSS original'),(520,before,'Previous de6922a'),(1030,after,'Refined native')]:
  d.text((x,y),title+' | '+label,fill='white');c=img.crop(box);scale=min(2,490/c.width,180/c.height);out.paste(c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST),(x,y+22))
out.save(E/'entrances-rocks-before-after.png')
print('Native audit passed for',sum(q['native_cells'] for q in summaries.values()),'cells; all Porymap/background/physics checks passed')
