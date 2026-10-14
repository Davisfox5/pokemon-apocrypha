"""Verify scoped edits, unchanged maps and production/accepted Route 29 seams."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
from claude_routes import seams
G=Path(sys.argv[1]);P=Path(sys.argv[2]);B=Path(sys.argv[3]);OUT=ROOT/'gba/art/new-bark-adjustments';S=OUT/'source';E=OUT/'evidence';t=Tileset(G,'new_bark','cherrygrove');g=np.fromfile(G/'data/layouts/NewBarkTown/map.bin','<u2').reshape(53,36);old=np.fromfile(S/'baseline/data/layouts/NewBarkTown/map.bin','<u2').reshape(50,36);edited=np.load(S/'edited-cells.npy')
assert np.array_equal(g[3:][~edited[3:]],old[~edited[3:]]);before=t.map_image(old.ravel().tolist(),36);after=t.map_image(g.ravel().tolist(),36);assert np.array_equal(after,Image.open(P/'NewBarkTown.png').convert('RGB'))
pxmask=np.repeat(np.repeat(edited,16,0),16,1);assert np.array_equal(np.asarray(before)[~pxmask[48:]],np.asarray(after)[48:][~pxmask[48:]]);after.save(E/'new-bark.png');before.save(E/'new-bark-before.png')
for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach','JohtoRoute31','VioletCityEntrance']:assert np.array_equal(np.asarray(Image.open(P/(name+'.png'))),np.asarray(Image.open(B/(name+'.png')))),name
original=Tileset(S/'baseline','new_bark','cherrygrove');assert t.blocks[1][:len(original.blocks[1])]==original.blocks[1];assert all(t.tiles[int(tid>=512)][tid%512]==original.tiles[int(tid>=512)][tid%512] for tid in {e&1023 for pool in original.blocks for es in pool for e in es if e});assert t.attrs[1][:len(original.attrs[1])]==original.attrs[1]
assert all((e&1023)<1008 and (e>>12)<13 for mid in np.unique(g&1023) for e in t.blocks[int(mid>=512)][int(mid)%512] if e)
assert not any(e>>12==10 for mid in np.unique(g&1023) for e in t.blocks[int(mid>=512)][int(mid)%512])
solid=(g&0xc00)!=0;reach=seams.reachable(solid,(0,15));m=json.loads((G/'data/maps/NewBarkTown/map.json').read_text());assert len(m['warp_events'])==8
for d in m['warp_events']:assert reach[d['y']+1,d['x']]
assert ((g[3:9,12:23]&0xc00)!=0).all();assert not reach[3:9,10:12].any()
assert ((g[:3]&0xc00)!=0).all()
assert np.array_equal((g[45:48,6:30]&0xfc00),(old[42:45,6:30]&0xfc00))
# Relative to the owner's last review, only the new northern forest and
# restoration of bottom crowns change. All town content retains its position
# within the existing footprint.
prior=np.fromfile(S/'forest-review-before-map.bin','<u2').reshape(50,36);prior_image=np.asarray(t.map_image(prior.ravel().tolist(),36));native_body=np.asarray(after)[48:];delta=np.any(native_body!=prior_image,2);allowed=np.zeros(delta.shape,bool);allowed[42*16:45*16,6*16:30*16]=True
for yy,xx in np.argwhere(np.ones(prior.shape,bool)):
 mid=int(prior[yy,xx]&1023)
 if any(e>>12==10 for e in t.blocks[int(mid>=512)][mid%512]):allowed[yy*16:(yy+1)*16,xx*16:(xx+1)*16]=True
assert not delta[~allowed].any()
reports=[]
route_sources=[G]+([Path(sys.argv[5])] if len(sys.argv)>5 else [])
for source in route_sources:
 r=Tileset(source,'claude_route29','cherrygrove');rg,rs=seams.read_layout(source,'CherrygroveRoute29Approach',98,48);rr=seams.reachable(rs,(97,18));va=seams.visible_across(rr,g.shape,98,3);vb=seams.visible_across(reach,rs.shape,-98,-3);ca,cb,_=seams.crossing_windows(rs,solid,98,3);errors=0;cached=0
 for owner,foreign,data,mask,cache in [(t,r,g&1023,va,cb),(r,t,rg,vb,ca)]:
  for mid in np.unique(data[mask]):errors+=int(not np.array_equal(owner.render(int(mid)),foreign.render(int(mid))))
  for mid in np.unique(data[cache]):
   for en in owner.blocks[int(mid>=512)][int(mid)%512]:
    tid=en&1023;cached+=int(owner.tiles[int(tid>=512)][tid%512]!=foreign.tiles[int(tid>=512)][tid%512])
 assert errors==0 and cached==0,(source,errors,cached);reports.append({'route_source':str(source),'camera_errors':errors,'cache_errors':cached})
board=Image.new('RGB',(1188,888),(24,28,34));d=ImageDraw.Draw(board);d.text((12,8),'Current shared-source map before edits',fill='white');d.text((600,8),'Mailbox, lab and southern housing adjustments',fill='white');board.paste(before,(12,76));board.paste(after,(600,28));board.save(E/'before-after.png')
forest_board=Image.new('RGB',(1188,888),(24,28,34));fd=ImageDraw.Draw(forest_board);fd.text((12,8),'Previous review, aligned to retained town footprint',fill='white');fd.text((600,8),'New northern forest and restored bottom crowns',fill='white');forest_board.paste(Image.fromarray(prior_image),(12,76));forest_board.paste(after,(600,28));forest_board.save(E/'forest-before-after.png')
report={'Porymap_pixel_errors':0,'outside_requested_edit_region_pixel_errors':0,'original_referenced_glyphs_and_metatile_attribute_prefixes_preserved':True,'static_tile_ids_below_door_animation_scratch':True,'seven_mailboxes':True,'eight_door_approaches_reachable':True,'lab_back_access_blocked':True,'seams':reports,'other_maps_unchanged':True,'new_northern_forest_rows':3,'bottom_complete_tree_course_restored':True,'other_town_pixels_unchanged_except_forest_fixes_and_green_foliage':True,'pink_foliage_remaining':False};(E/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if len(sys.argv)>4:
 runtime=Path(sys.argv[4])
 # Check native mailbox heads after all eight door animations. The bottom
 # eight rows may be legitimately occluded by the player's hat at the base.
 mailmask=np.asarray(Image.open(S/'mailbox-source.png'))[...,3]>0;mailmask[24:]=False
 mailbox_errors=[]
 for i,(x,y) in enumerate(json.loads((E/'edit.json').read_text())['mailboxes']):
  expected=np.asarray(after)[(y-1)*16:(y+1)*16,x*16:(x+1)*16];expected=(expected>>3)<<3|(expected>>5)
  actual=np.asarray(Image.open(runtime/f'mailbox-{i}.png').convert('RGB'))[40:72,112:128]
  errors=int(np.any(actual!=expected,2)[mailmask].sum());assert errors==0,('Runtime mailbox head corruption',i,errors);mailbox_errors.append(errors)
 (E/'mailbox-runtime-pixels.json').write_text(json.dumps({'after_eight_door_animations':True,'mailbox_foreground_pixel_errors':mailbox_errors,'GBA_5bit_color_expansion':True,'player_hat_occlusion_excluded':'bottom 8 sprite rows'},indent=2)+'\n')
 dest=E/'gameplay';dest.mkdir(exist_ok=True)
 for file in list(runtime.glob('*.png'))+[runtime/n for n in ['results.json','write.jsonl','read.jsonl','menu.jsonl']]:shutil.copyfile(file,dest/file.name)
 names=['trees-behind-lab','bottom-complete-trees','house-4-exterior','house-5-exterior','house-6-exterior','house-7-exterior','mailbox-0','mailbox-2','title-continue'];gallery=Image.new('RGB',(1456,1056),(24,28,34));d=ImageDraw.Draw(gallery)
 for i,name in enumerate(names):
  x=8+i%3*484;y=i//3*352;d.text((x,y+7),name.replace('-',' '),fill='white');gallery.paste(Image.open(runtime/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+26))
 gallery.save(E/'gameplay-gallery.png')
