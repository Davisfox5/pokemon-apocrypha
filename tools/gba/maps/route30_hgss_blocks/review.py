#!/usr/bin/env python3
"""Reproduce source/native review boards and survey-to-engine verification."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from claude_routes import seams
OUT=ROOT/'gba/art/route30-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
def main():
 game=Path(sys.argv[1]);probe=Path(sys.argv[2]);baseline=Path(sys.argv[3])
 grid=np.fromfile(game/'data/layouts/CherrygroveRoute30Approach/map.bin','<u2').reshape(86,35);p=np.load(S/'plan.npy');under=np.array([list(s) for s in (S/'terrain.txt').read_text().splitlines()]);f=json.loads((S/'structures.json').read_text())
 t=Tileset(game,'claude_route30','cherrygrove');native=t.map_image(grid.ravel().tolist(),35)
 native.save(E/'native-proposal.png');assert np.array_equal(np.asarray(native),np.asarray(Image.open(probe/'CherrygroveRoute30Approach.png').convert('RGB')))
 display=native.copy()
 for event in json.loads((game/'data/maps/CherrygroveRoute30Approach/map.json').read_text())['object_events']:
  if event['graphics_id']=='OBJ_EVENT_GFX_CUTTABLE_TREE':
   sprite=Image.open(game/'graphics/object_events/pics/misc/cuttable_tree.png').crop((0,0,16,16));px=np.asarray(sprite);rgba=np.asarray(sprite.convert('RGBA')).copy();rgba[px==0,3]=0
   sprite=Image.fromarray(rgba);display.paste(sprite,(event['x']*16,event['y']*16),sprite)
   sprite.save(S/'native-cut-tree.png')
 display.save(E/'native-proposal-with-objects.png')
 solid=np.isin(p,list('TR#AW!_'))
 for house in f['houses']:
  x,y=house['x'],house['y'];solid[y:y+5,x:x+5]=under[y:y+5,x:x+5]=='#';solid[y+1:y+5,x+1:x+5]=True
 actual=(grid&0xc00)!=0;errors=int(np.count_nonzero(solid[:74]!=actual[:74]));assert errors==0,errors
 ledger=json.loads((S/'block-ledger.json').read_text())
 for q in ledger:
  q['native_blocked']=bool(actual[q['y'],q['x']]);q['blocked']=q['native_blocked']
  q['collision_basis']='image inference plus explicit structure footprint; not DS collision data'
  q['reference_visible_width']=13 if q['x']==34 else 16
 (S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape)
 checks={k:int(np.count_nonzero(beh[p==c]!=b)) for k,c,b in [('grass_behavior_errors','G',2),('water_behavior_errors','W',16),('ledge_behavior_errors','_',59)]};assert not any(checks.values()),checks
 unchanged=['CherrygroveCity','CherrygroveRoute29Approach','NewBarkTown','JohtoRoute31','VioletCityEntrance']
 for name in unchanged:assert np.array_equal(np.asarray(Image.open(probe/(name+'.png'))),np.asarray(Image.open(baseline/(name+'.png')))),name
 source=Image.open(S/'hgss-reference.png').convert('RGB').crop((6,4,566,1188))
 # Last source column has only thirteen pixels; its three missing pixels are marked, never invented as source evidence.
 ImageDraw.Draw(source).rectangle((557,0,559,1183),fill=(55,55,55))
 board=Image.new('RGB',(1144,1224),(24,28,34));d=ImageDraw.Draw(board);d.text((12,8),'HGSS source: registered 16px grid',fill='white');d.text((584,8),'Native Route 30: terrain + native object preview',fill='white');board.paste(source,(12,28));board.paste(display.crop((0,0,560,1184)),(584,28));board.save(E/'whole-map-comparison.png')
 for lo in range(0,74,12):
  hi=min(74,lo+12);a=source.crop((0,lo*16,560,hi*16));b=native.crop((0,lo*16,560,hi*16));page=Image.new('RGB',(1144,(hi-lo)*16+48),(24,28,34));dr=ImageDraw.Draw(page);dr.text((12,8),f'HGSS rows {lo}-{hi-1}; columns 0-34',fill='white');dr.text((584,8),'Native reconstruction; same block coordinates',fill='white');page.paste(a,(12,28));page.paste(b,(584,28));page.save(E/f'comparison-rows-{lo:02}-{hi-1:02}.png')
 footprint=native.copy();d=ImageDraw.Draw(footprint)
 assembly=json.loads((E/'assembly.json').read_text())
 for x,y in assembly['new_tree_positions']:
  d.rectangle((x*16,y*16,(x+2)*16-1,(y+1)*16-1),outline=(90,190,255),width=1);d.rectangle((x*16,(y+1)*16,(x+2)*16-1,(y+3)*16-1),outline=(255,190,50),width=1)
 for tr in f['divider_trees']:
  x,y,w,h=tr['ground_rect'];d.rectangle((x*16,y*16,(x+w)*16-1,(y+h)*16-1),outline=(255,190,50),width=2)
 footprint.save(E/'tree-footprints.png')
 report={'core_blocks':2590,'source_basis':'HGSS overview with owner-authorized whole-tree expansion, native Emerald terrain and object-based Cut barrier','collision_disagreements':errors,'cut_barrier':'native object; underlying terrain passable; standard Cut script',**checks,'Porymap_pixel_errors':0,'unaffected_maps':unchanged}
 # Every camera-visible foreign block must render identically using the current map libraries.
 seam_reports=[]
 for name,sec,w,h,ox,oy,start in [('CherrygroveCity','cherrygrove',80,48,-35,86,(43,0)),('JohtoRoute31','route31',63,30,-28,-30,(38,29))]:
  ng,ns=seams.read_layout(game,name,w,h);nt=Tileset(game,sec,'cherrygrove');nr=seams.reachable(ns,start);rr=seams.reachable(actual,(8,85));to_r=seams.visible_across(nr,actual.shape,-ox,-oy);to_n=seams.visible_across(rr,ns.shape,ox,oy)
  counts=[]
  for owner,foreign,data,mask in [(t,nt,grid&1023,to_r),(nt,t,ng,to_n)]:
   mismatches=[int(mid) for mid in np.unique(data[mask]) if not np.array_equal(np.asarray(owner.render(int(mid))),np.asarray(foreign.render(int(mid))))];counts.append(len(mismatches));assert not mismatches,(name,mismatches)
  cache_errors=0;offscreen_palette_blocks=0
  wa,wb,_=seams.crossing_windows(ns,actual,-ox,-oy)
  for owner,foreign,data,mask in [(t,nt,grid&1023,wb),(nt,t,ng,wa)]:
   for mid in np.unique(data[mask]):
    entries=owner.blocks[int(mid>=512)][int(mid)-512 if mid>=512 else int(mid)]
    for en in entries:
     tid=en&1023;part=int(tid>=512);idx=tid-512 if part else tid
     cache_errors+=int(idx>=len(foreign.tiles[part]) or owner.tiles[part][idx]!=foreign.tiles[part][idx])
    offscreen_palette_blocks+=int(not np.array_equal(np.asarray(owner.render(int(mid))),np.asarray(foreign.render(int(mid)))))
  assert cache_errors==0,(name,cache_errors)
  seam_reports.append({'neighbor':name,'camera_visible_palette_and_pixel_mismatches':counts,'cached_window_tile_pixel_errors':cache_errors,'offscreen_window_palette_differences':offscreen_palette_blocks,'camera_margins':{'horizontal':8,'up':5,'down':6}})
 if len(sys.argv)>4:
  runtime=Path(sys.argv[4]);dest=E/'gameplay';dest.mkdir(exist_ok=True)
  for file in runtime.glob('*.png'):shutil.copyfile(file,dest/file.name)
  for name in ['results.json','write.jsonl','read.jsonl','menu.jsonl']:shutil.copyfile(runtime/name,dest/name)
  names=['southern-house','native-grass-walking','mr-pokemon-house','original-cut-barrier','ledge-bypass-canopy','upper-pond','route30-south-seam','northern-ledge','title-continue']
  gallery=Image.new('RGB',(1456,1056),(24,28,34));draw=ImageDraw.Draw(gallery)
  for i,name in enumerate(names):
   x=8+i%3*484;y=i//3*352;draw.text((x,y+7),name.replace('-',' '),fill='white');gallery.paste(Image.open(runtime/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+26))
  gallery.save(E/'gameplay-gallery.png')
  frames=[Image.open(runtime/(name+'.png')).resize((480,320),Image.Resampling.NEAREST) for name in ['north-crossing-before','north-crossing-28','north-crossing-29','north-crossing-00','north-crossing-01','north-crossing-02']]
  frames[0].save(E/'north-crossing.gif',save_all=True,append_images=frames[1:],duration=650,loop=0)
 report['connection_camera_checks']=seam_reports;(E/'block-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
