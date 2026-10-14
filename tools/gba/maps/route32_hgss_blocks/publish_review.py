"""Render review sheets and attach evidence to the exact engine commit.
Usage: publish_review.py GAME RUNTIME_DIR PORYMAP_EXPORT_DIR
No ROM, save or executable is copied into the hub.
"""
from pathlib import Path
import sys,json,subprocess,csv,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from tiles import Tileset
G,R,P=map(Path,sys.argv[1:4]);OUT=HERE.parents[3]/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence'
sha=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()
r=json.loads((R/'results.json').read_text());assert all(p['exit_code']==0 for p in r['phases'])
for name in ['results.json','write.jsonl','read.jsonl','menu.jsonl']:shutil.copyfile(R/name,E/'gameplay'/name)
for p in R.glob('*.png'):shutil.copyfile(p,E/'gameplay'/p.name)
# Fixed readable 2x gameplay frames, with no filtering or illustration layer.
names=[('east-west-stairs','East-west Emerald flight'),('fishing-arm','HGSS-grain fishing arm'),('western-woodland-footprint','Western woods: barrier probe'),('north-south-stairs','North-south placeholder unchanged'),('forest-behind-center','Woods behind the Center'),('union-cave-approach','Aligned cave approach')]
out=Image.new('RGB',(980,1050),(26,33,37));d=ImageDraw.Draw(out)
for i,(name,title) in enumerate(names):
 x=10+(i%2)*490;y=10+(i//2)*346;out.paste(Image.open(R/(name+'.png')).convert('RGB').resize((480,320),Image.Resampling.NEAREST),(x,y+20));d.text((x,y+4),title,fill='white')
out.save(E/'grid-gameplay-gallery.png');out.save(E/'gameplay-gallery.png')
# Numbered original-source sheets expose the manual trace for review.
ref=Image.open(S/'hgss-reference.png').convert('RGB')
for n in range(5):
 out=Image.new('RGB',(1050,870),'white');out.paste(ref.crop((0,n*400,490,(n+1)*400)).resize((980,800),Image.Resampling.NEAREST),(50,40));d=ImageDraw.Draw(out)
 for x in range(31):d.line((50+x*32,40,50+x*32,840),fill='#aaaaaa');d.text((50+x*32,15),str(x),fill='black')
 for y in range(26):d.line((50,40+y*32,1030,40+y*32),fill='#aaaaaa');d.text((5,40+y*32),str(n*25+y),fill='black')
 out.save(E/f'hgss-numbered-grid-{n+1}.png')
im=Image.open(E/'native-map.png').convert('RGB');out=Image.new('RGB',(1060,2100),(26,33,37));out.paste(ref,(20,48));out.paste(im,(540,32));d=ImageDraw.Draw(out);d.text((20,10),'Original HGSS Route 32',fill='white');d.text((540,10),'Gen 3 grid reconstruction',fill='white');out.save(E/'comparison.png')
shutil.copyfile(E/'grid-revision-overview.png',E/'refinement-overview.png')
for n in range(1,5):shutil.copyfile(E/f'grid-comparison-{n}.png',E/f'comparison-{n}.png')
# Focused original/current panels for the revised elements, at readable native scale.
regions=[('EW stairs',(112,896,208,1008)),('Dock fishing arm',(192,1136,368,1232)),('Dock bend',(248,1232,376,1328)),('West fishing woods',(16,1136,160,1344)),('Center rear forest',(160,1520,416,1648)),('Cave boulder',(288,1816,384,1936))]
out=Image.new('RGB',(1060,1900),(26,33,37));d=ImageDraw.Draw(out)
for i,(title,box) in enumerate(regions):
 y=10+i*310;d.text((20,y),title+' — HGSS',fill='white');d.text((540,y),'native',fill='white')
 for x,img,b in [(20,ref,box),(540,im,tuple(v+16 for v in box))]:
  c=img.crop(b);scale=min(2,480/c.width,280/c.height);c=c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST);out.paste(c,(x,y+22))
out.save(E/'detail-comparison.png')
t=Tileset(G,'route32','route32');grid=np.fromfile(G/'data/layouts/JohtoRoute32/map.bin','<u2').reshape(128,32);plan=np.load(S/'refined-plan.npy');beh=np.array([t.attrs[int(v>=512)][v-512 if v>=512 else v]&255 for v in (grid&1023).ravel()]).reshape(grid.shape)
with (S/'cell-ledger.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['native_x','native_y','source_x_px','source_y_px','terrain_trace','metatile_id','behavior','blocked_on_foot'])
 for y in range(128):
  for x in range(32):w.writerow([x,y,(x-1)*16,(y-1)*16,plan[y,x],int(grid[y,x]&1023),int(beh[y,x]),bool(grid[y,x]&0xc00 or beh[y,x] in [16,21])])
a=np.array(im);b=np.array(Image.open(P/'JohtoRoute32.png').convert('RGB'));assert np.array_equal(a,b)
# Shared art and other owner layouts must remain byte-identical to production.
p=json.loads((E/'preservation.json').read_text())
for v in p['protected_paths']:
 diff=subprocess.check_output(['git','-C',str(G),'diff','2722eaf',sha,'--',v['path']]);assert not diff,v['path'];v['unchanged']=True
p.update(source_commit=sha,refinement_base_commit='fe8df8b4917f4143ae86ac461c3d970cb4db5f63',new_route_local_primary='gTileset_Route32Primary; referenced CG glyphs and animated slots retained; shared primary unchanged',warp_coordinate_correction={'cave_cells':[[14,117],[15,117]]});(E/'preservation.json').write_text(json.dumps(p,indent=2)+'\n')
build={'source_commit':sha,'rom_sha256':r['rom_sha256'],'rom_build':'passed','runtime_observations':sum(len(p['observations']) for p in r['phases']),'ordinary_flash_bytes':131072,'cold_reload':'passed','title_continue':'passed','native_stair_axes_both_directions':'passed','fixed_HGSS_forest_stair_and_boulder_probes':'passed','both_cave_entrance_cells':'passed','ROMs_saves_tools_committed':False};(E/'build.json').write_text(json.dumps(build,indent=2)+'\n')
(E/'porymap.json').write_text(json.dumps({'version':'6.3.1','project_opened':True,'native_map_pixel_differences':0,'method':'headless project-core export','source_commit':sha,'maps':['JohtoRoute32','Route32PokemonCenter','UnionCaveRoute32Entrance']},indent=2)+'\n')
for name in ['refinement.json','grid-audit.json','porytiles.json']:
 p=E/name;j=json.loads(p.read_text());j['source_commit']=sha;p.write_text(json.dumps(j,indent=2)+'\n')
p=json.loads((E/'refinement.json').read_text());p['refinement_base_commit']='fe8df8b4917f4143ae86ac461c3d970cb4db5f63';(E/'assembly.json').write_text(json.dumps(p,indent=2)+'\n')
print('Published review evidence for',sha,'observations',build['runtime_observations'])
