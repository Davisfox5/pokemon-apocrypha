"""Publish the fresh Olivine terrain against rejected 601d1b07."""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'gba/art/olivine-city';S=BASE/'source/terrain-reset';E=BASE/'evidence/terrain-reset';G,R,P=map(Path,sys.argv[1:4]);PARENT='601d1b073e4e4723066a3dc88c679c21d317991b'
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
# Normalize retained textual palette evidence; native source keeps its own attributes.
for p in E.glob('*-compiled/palettes/*.pal'):p.write_text(p.read_text())
old=np.array(Image.open(BASE/'evidence/terrain-rebuild/native-map.png').convert('RGB'));now=np.array(Image.open(E/'native-map.png').convert('RGB'));allowed=np.array(Image.open(S/'scope-mask.png'))>0;changed=np.any(now!=old,2)
assert not np.any(changed&~allowed),'Unexpected visible change outside terrain/stair receiving quadrants.'
ref=Image.open(BASE/'source/hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,896),'#223039');registered.paste(ref,(64,16));before=Image.fromarray(old);after=Image.fromarray(now);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
boxes=[('western-wall',(112,144,416,512)),('northern-branches',(496,16,768,432)),('upper-stair',(592,304,760,416)),('lighthouse-courses',(680,528,960,680)),('timber-ramp',(648,512,824,648)),('eastern-shore',(880,208,1152,672)),('western-rock-spur',(64,528,240,688))]
for name,box in [('whole-map',(0,0,1152,896)),*boxes]:
 w,h=box[2]-box[0],box[3]-box[1];scale=1 if name=='whole-map' else 2;sh=Image.new('RGB',(3*(w*scale+16)+16,h*scale+48),'#223039');d=ImageDraw.Draw(sh)
 for i,(caption,im) in enumerate([('HGSS reference',registered),('Rejected wall assembly (601d1b07)',before),('Fresh native contour / tile assembly',after)]):
  x=16+i*(w*scale+16);d.text((x,8),caption,font=font,fill='white');sh.paste(im.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,40))
 sh.save(E/(name+'-before-after.png'))
# Mark the actual reference-registered height transitions and three side faces.
box=(680,528,960,680);w,h=box[2]-box[0],box[3]-box[1];guide=Image.new('RGB',(2*w*3+32,h*3+48),'#223039');d=ImageDraw.Draw(guide)
for i,(caption,im) in enumerate([('HGSS observed courses',registered),('Native: three connected front / west faces',after)]):
 x=8+i*(w*3+16);guide.paste(im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(x,40));d.text((x,8),caption,font=font,fill='white')
 for sy,caption,color in [(576,'3: lighthouse lawn edge','#ffff99'),(600,'2: middle terrace','#ffbb88'),(624,'1: shore course','#99ddff')]:
  y=40+(sy+16-box[1])*3;d.line((x+130,y,x+w*3-12,y),fill=color,width=2);d.text((x+140,y-20),caption,font=font,fill=color)
guide.save(E/'course-guide.png')
run=json.loads((R/'results.json').read_text());rom=sha(G/'pokeemerald.gba');assert run['rom_sha256']==rom and all(p['exit_code']==0 for p in run['phases']);write(E/'runtime.json',run)
for dirname,src in [('gameplay',R),('porymap',P)]:
 (E/dirname).mkdir(exist_ok=True)
 for p in src.glob('*.png'):shutil.copyfile(p,E/dirname/p.name)
shots=['north-retaining-wall','western-retaining-wall','beach-wall-return','east-stair-head','east-stair-lane','lighthouse-ramp-west','lighthouse-terrace','headland-three-courses','headland-eastern-turn','western-rock-spur','western-rock-spur-head','cold-reload'];gallery=Image.new('RGB',(1440,1408),'#223039');d=ImageDraw.Draw(gallery)
for i,n in enumerate(shots):
 x,y=i%3*480,i//3*352;d.text((x+8,y+8),n,font=font,fill='white');gallery.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+32))
gallery.save(E/'gameplay-gallery.png')
head=git('rev-parse','HEAD');assert head!=PARENT;files=git('diff','--name-only',PARENT,head).splitlines()
assert all(any('/'+name+'/' in p for name in ['olivine_city','olivine_quay','JohtoOlivineCity','JohtoOlivineQuay']) for p in files),files
manifest=[]
for p in files:
 raw=subprocess.check_output(['git','-C',str(G),'show',head+':'+p]);manifest.append(dict(path=p,git_blob=git('rev-parse',head+':'+p),sha256=hashlib.sha256(raw).hexdigest()))
review=json.loads((E/'review.json').read_text());observations=sum(len(p['observations']) for p in run['phases'])
write(E/'preservation.json',dict(source_commit=head,rejected_baseline=PARENT,source_PR='https://github.com/Davisfox5/pokeemerald-expansion/pull/21',source_manifest=manifest,ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,outside_terrain_scope_pixel_changes=0,changed_visible_pixels=int(changed.sum()),unchanged='Shared foreground buildings/trees/props, Harbor source, other maps, all map/layout/event/warp IDs and registries.',source_authority='Decoded current native 601d1b07 input; original HGSS geography; entirely new terrain traces/tiles, not the former wall-strip assembly.',owner_visual_acceptance='pending'))
write(E/'build.json',dict(exit_code=0,command='PATH=ARM_BIN:$PATH make -j5',ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Arm GNU 14.2.1',compiler='Porytiles legacy 2.0.0, exact RGB5 bank covering',Porymap='6.3.1 actual project exports',mGBA='0.10.5 headless',runtime_observations=observations,phases=[dict(phase=p['phase'],exit_code=p['exit_code']) for p in run['phases']],district_usage=review['district_usage']))
write(E/'visual-review.json',dict(owner_request='Scrap the rejected terrain and try again from scratch.',rejected_baseline=PARENT,reviewed_regions=[dict(name=n,native_crop=list(b)) for n,b in boxes],method='Fresh original-reference contours and explicit same-facing repeated native runs. Native edge templates preserve contacts/corners/components and move their contour by at most one pixel. Stone texture medoids are restricted to the same face orientation; full accepted foreground remains exact.',corrections=['Restored southwest plateau/outcrop missing in both rejected versions.','Restored actual narrow shelves, recessed steps, round tips and all three connected lighthouse courses.','Retained purple/neutral rock shadows, removing false green cracks between rock courses.','Completed exposed upper residential shelf end where the native tree differs from the source crown.','Removed detached original tree-root/prop fragments from the rock layer.','Rebuilt both timber openings with opaque source treads/rails and proper receiving ground; no grey patch beneath the ramp.'],limits=['Visible source contours and height interpretation, not extracted DS heights/collision.','Existing native architecture/tree footprints, ordinary district fades, static water and unwired interiors/Routes39/40/shipping remain.','Owner acceptance is pending; functional checks do not establish visual acceptance.']))
print(json.dumps(dict(source_commit=head,ROM_sha256=rom,changed_visible_pixels=int(changed.sum()),outside_scope=0,observations=observations),indent=2))
