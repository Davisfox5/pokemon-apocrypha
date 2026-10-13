#!/usr/bin/env python3
"""Produce source/native comparisons and verify unchanged maps and seams."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from claude_routes import seams
OUT=ROOT/'gba/art/route29-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
def main():
 game=Path(sys.argv[1]);probe=Path(sys.argv[2]);baseline=Path(sys.argv[3]);grid=np.fromfile(game/'data/layouts/CherrygroveRoute29Approach/map.bin','<u2').reshape(48,98);p=np.load(S/'plan.npy');protected=np.load(S/'protected.npy');t=Tileset(game,'claude_route29','cherrygrove');native=t.map_image(grid.ravel().tolist(),98)
 assert np.array_equal(np.asarray(native),np.asarray(Image.open(probe/'CherrygroveRoute29Approach.png').convert('RGB')));native.save(E/'native-proposal.png')
 s=(grid&0xc00)!=0;expected=np.load(S/'solid.npy');assert np.array_equal(s,expected)
 b=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(p.shape)
 assert (b[(p=='G')&~protected]==2).all();assert (b[(p=='_')&~protected]==59).all()
 unchanged=['CherrygroveCity','CherrygroveRoute30Approach','NewBarkTown','JohtoRoute31','VioletCityEntrance']
 for name in unchanged:assert np.array_equal(np.asarray(Image.open(probe/(name+'.png'))),np.asarray(Image.open(baseline/(name+'.png')))),name
 old=np.fromfile(S/'baseline/data/layouts/CherrygroveRoute29Approach/map.bin','<u2').reshape(48,98);assert np.array_equal(grid[protected],old[protected])
 reports=[];rr=seams.reachable(s,(0,18))
 for name,sec,w,h,ox,oy,start in [('CherrygroveCity','cherrygrove',80,48,-80,0,(79,18)),('NewBarkTown','new_bark',36,50,98,6,(0,12))]:
  ng,ns=seams.read_layout(game,name,w,h);nt=Tileset(game,sec,'cherrygrove');nr=seams.reachable(ns,start);a=seams.visible_across(nr,p.shape,-ox,-oy);bb=seams.visible_across(rr,ns.shape,ox,oy);wa,wb,_=seams.crossing_windows(ns,s,-ox,-oy);pixel_errors=0;tile_errors=0
  for owner,foreign,data,mask,cache in [(t,nt,grid&1023,a,wb),(nt,t,ng,bb,wa)]:
   for mid in np.unique(data[mask]):pixel_errors+=int(not np.array_equal(np.asarray(owner.render(int(mid))),np.asarray(foreign.render(int(mid)))))
   for mid in np.unique(data[cache]):
    for en in owner.blocks[int(mid>=512)][int(mid)-512 if mid>=512 else int(mid)]:
     tid=en&1023;part=int(tid>=512);idx=tid-512 if part else tid;tile_errors+=int(idx>=len(foreign.tiles[part]) or owner.tiles[part][idx]!=foreign.tiles[part][idx])
  assert pixel_errors==0,(name,pixel_errors);assert tile_errors==0,(name,tile_errors);reports.append({'neighbor':name,'camera_palette_pixel_errors':pixel_errors,'cached_glyph_errors':tile_errors})
 reference=Image.open(S/'hgss-reference.png').convert('RGB').crop((4,5,1572,437));core=native.crop((0,32,1568,464));board=Image.new('RGB',(1592,928),(24,28,34));d=ImageDraw.Draw(board);d.text((12,8),'HGSS reference rows 0-26',fill='white');board.paste(reference,(12,28));d.text((12,468),'Native rows 2-28; whole-tree liberties and town/lookout adapters',fill='white');board.paste(core,(12,488));board.save(E/'whole-map-comparison.png')
 for name,lo,hi in [('west',0,33),('central',33,66),('east',66,98)]:
  width=(hi-lo)*16;page=Image.new('RGB',(2*width+36,480),(24,28,34));d=ImageDraw.Draw(page);d.text((12,8),f'HGSS columns {lo}-{hi-1}',fill='white');d.text((width+24,8),'Native reconstruction',fill='white');page.paste(reference.crop((lo*16,0,hi*16,432)),(12,28));page.paste(core.crop((lo*16,0,hi*16,432)),(width+24,28));page.save(E/f'comparison-{name}.png')
 previous=Image.open(ROOT/'gba/art/apoc-route29/route29-overview.png').convert('RGB');board=Image.new('RGB',(1592,1600),(24,28,34));d=ImageDraw.Draw(board);d.text((12,8),'Claude HGSS-slice proposal (preserved)',fill='white');board.paste(previous,(12,28));d.text((12,804),'Independent reconstruction with complete trees and Emerald terrain',fill='white');board.paste(native,(12,828));board.save(E/'claude-before-after.png')
 footprints=native.copy();d=ImageDraw.Draw(footprints);assembly=json.loads((E/'assembly.json').read_text())
 for x,y in assembly['trees']:d.rectangle((x*16,y*16,(x+2)*16-1,(y+1)*16-1),outline=(90,190,255));d.rectangle((x*16,(y+1)*16,(x+2)*16-1,(y+3)*16-1),outline=(255,190,50))
 footprints.save(E/'tree-footprints.png')
 ledger=json.loads((S/'block-ledger.json').read_text())
 for cell in ledger:
  x,y=cell['x'],cell['native_y'];cell['native_category']=str(p[y,x]);cell['native_blocked']=bool(s[y,x]);cell['adapted_or_preserved']=bool(protected[y,x]);cell['collision_basis']='image-inferred terrain and native footprint adaptations; not DS collision records'
 (S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 report={'Porymap':'6.3.1 project-core export','Porymap_native_pixel_errors':0,'collision_errors':0,'grass_behavior_errors':0,'ledge_behavior_errors':0,'unchanged_maps':unchanged,'preserved_adapter_cells':int(protected.sum()),'connection_checks':reports,'native_footprints_not_raw_DS_collision':True};(E/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if len(sys.argv)>4:
  runtime=Path(sys.argv[4]);dest=E/'gameplay';dest.mkdir(exist_ok=True)
  for file in runtime.glob('*.png'):shutil.copyfile(file,dest/file.name)
  for name in ['results.json','write.jsonl','read.jsonl','menu.jsonl']:shutil.copyfile(runtime/name,dest/name)
  names=['apricorn-clearing','route46-gate','native-grass-walking','western-ledge','central-ledge','coastal-lookout','cherrygrove-east-seam','new-bark-west-seam','title-continue'];gallery=Image.new('RGB',(1456,1056),(24,28,34));d=ImageDraw.Draw(gallery)
  for i,name in enumerate(names):
   x=8+i%3*484;y=i//3*352;d.text((x,y+7),name.replace('-',' '),fill='white');gallery.paste(Image.open(runtime/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+26))
  gallery.save(E/'gameplay-gallery.png');frames=[Image.open(runtime/(name+'.png')).resize((480,320),Image.Resampling.NEAREST) for name in ['east-crossing-before','east-crossing-0','east-crossing-1','east-crossing-2','east-crossing-3','east-crossing-4']];frames[0].save(E/'new-bark-crossing.gif',save_all=True,append_images=frames[1:],duration=650,loop=0)
if __name__=='__main__':main()
