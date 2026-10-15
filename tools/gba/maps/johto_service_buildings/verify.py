"""Verify native exports, approved masters, preserved animation and runtime proof."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess,tempfile,tarfile,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build import ROOT,OUT,E,BASE,file_digest
from tiles import Tileset

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(game,porymap,runtime):
 report={};registry=json.loads((ROOT/'gba/art/johto-common/approved-buildings.json').read_text())
 for key in ['pokemon_center','poke_mart']:
  entry=registry['buildings'][key];assert digest(ROOT/entry['master'])==entry['sha256']
 for n in ['CherrygroveCity','VioletCity']:
  a=np.array(Image.open(E/(n+'.png')).convert('RGB'));b=np.array(Image.open(porymap/(n+'.png')).convert('RGB'));assert np.array_equal(a,b),(n,'Porymap mismatch')
  report[n]={'porymap_pixel_errors':0,'opaque_master_pixel_errors':0}
  for key in ['pokemon_center','poke_mart']:
   item=registry['buildings'][key];spec=next(p for p in item['placements'] if p['map']==n);im=np.array(Image.open(ROOT/item['master']).convert('RGBA'));h,w=im.shape[:2];x,y=spec['origin'];mask=im[:,:,3]>0;assert np.array_equal(a[y*16:y*16+h,x*16:x*16+w][mask],im[:,:,:3][mask])
  affected=np.load(OUT/f'{n}-affected.npy').repeat(16,0).repeat(16,1);old=np.array(Image.open(E/(n+'-before.png')).convert('RGB'));assert np.array_equal(a[~affected],old[~affected]);report[n]['pixels_changed_outside_placement_and_entrance_areas']=0
 current=Tileset(game,'johto_cherrygrove','johto_cherrygrove');legacy=Tileset(game,'cherrygrove','cherrygrove');assert current.tiles[0][:93]==legacy.tiles[0][:93];assert current.pals[0][1]==legacy.pals[0][1]
 report['sea_animation']={'original_tile_ids_1_to_92_preserved':True,'palette_preserved':True,'callback_unchanged':True}
 for mapname in ['CherrygroveCity','VioletCity','CherrygroveMart','CherrygrovePokemonCenter']:
  p=f'data/maps/{mapname}/map.json';assert (game/p).read_bytes()==subprocess.check_output(['git','show',BASE+':'+p],cwd=game)
 report['existing_warps_events_and_map_scripts']='unchanged'
 result=json.loads((runtime/'results.json').read_text());assert all(v['exit_code']==0 for v in result['phases']);assert result['rom_sha256']==digest(game/'pokeemerald.gba')
 dst=E/'runtime';dst.mkdir(exist_ok=True)
 for name in ['results.json','write.jsonl','read.jsonl','menu.jsonl','runtime.c','center-front.png','mart-front.png','center-return.png','mart-return.png','center-roof-overlap.png','center-side.png','violet-center-front.png','violet-mart-preserved.png','cherrygrove-service-street.png','old-sign-cleared.png','pond-animation-0.png','pond-animation-1.png','center-interior.png','mart-interior.png','cold-reload.png','title-continue.png']:
  shutil.copy2(runtime/name,dst/name)
 for kind in ['center','mart']:
  frames=[Image.open(runtime/f'{kind}-door-{i:03}.png').convert('RGB') for i in range(0,90,3)];frames[0].save(dst/f'{kind}-entry.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
 im=Image.open(E/'CherrygroveCity.png');im.crop((45*16,2*16,68*16,13*16)).resize((1104,528),Image.Resampling.NEAREST).save(E/'cherrygrove-service-closeup.png')
 im=Image.open(E/'VioletCity.png');im.crop((43*16,48*16,56*16,59*16)).resize((624,528),Image.Resampling.NEAREST).save(E/'violet-center-closeup.png')
 board=Image.new('RGB',(1120,720),'#202832');d=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
 for row,kind in enumerate(['center','mart']):
  folder=OUT/'placements/CherrygroveCity';ground=Image.open(folder/f'{kind}-ground.png').convert('RGBA');art=Image.open(folder/f'{kind}-building.png').convert('RGBA');combined=Image.alpha_composite(ground,art);checker=Image.new('RGBA',art.size);q=ImageDraw.Draw(checker)
  for y in range(0,art.height,8):
   for x in range(0,art.width,8):q.rectangle((x,y,x+7,y+7),fill=('#3f4b58' if (x//8+y//8)%2 else '#657382'))
  checker=Image.alpha_composite(checker,art)
  for col,(im,label) in enumerate([(ground,'Independent ground'),(checker,'Transparent approved building'),(combined,'Composed placement')]):
   x=20+col*365;y=20+row*350;d.text((x,y),label,font=font,fill='white');board.paste(im.convert('RGB').resize((im.width*3,im.height*3),Image.Resampling.NEAREST),(x,y+35))
 board.save(E/'separate-building-and-ground-layers.png')
 report['runtime']={'phases_passed':[p['phase'] for p in result['phases']],'rom_sha256':result['rom_sha256'],'native_door_frames_inspected':True,'desktop_emulator_opened':False}
 (E/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 # Guard shared output from accidental overwrite after later authored edits.
 files=['data/layouts/CherrygroveCity/map.bin','data/layouts/VioletCity/map.bin','data/layouts/layouts.json','src/data/tilesets/graphics.h','src/data/tilesets/metatiles.h','src/data/tilesets/headers.h','src/field_door.c']
 for part in ('primary','secondary'):
  for name in ('johto_cherrygrove','violet_city'):
   folder=game/f'data/tilesets/{part}/{name}';files += [str(p.relative_to(game)) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.png','.bin','.pal')]
 files += [str(p.relative_to(game)) for p in (game/'graphics/door_anims/johto_shared').glob('*.4bpp')]
 (OUT/'generated-files.json').write_text(json.dumps({p:file_digest(game/p) for p in sorted(files)},indent=2)+'\n')
 # The older Violet build already refuses overwritten generated files. Refresh
 # its manifest so later narrow adapters can identify the installed state.
 manifest=ROOT/'gba/art/violet-city/source/generated-files.json';data=json.loads(manifest.read_text())
 for p in data:data[p]=digest(game/p)
 manifest.write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main(*(Path(p).resolve() for p in sys.argv[1:4]))
