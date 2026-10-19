"""Publish the checked native wall/stair revision; preserve the rejected pass."""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'gba/art/olivine-city';S=BASE/'source/terrain-rebuild';E=BASE/'evidence/terrain-rebuild';G,R=map(Path,sys.argv[1:3]);PARENT='c26b9b21d095ca6e0f8a7e5a46a091bc82701e52'
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
old=np.array(Image.open(BASE/'evidence/native-map.png').convert('RGB'));now=np.array(Image.open(E/'native-map.png').convert('RGB'));bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));expected=bg.copy();m=fg[...,3]>0;expected[m]=fg[m];assert np.array_equal(expected[...,:3],now)
allowed=(np.array(Image.open(S/'retired-wall-mask.png'))>0)|(np.array(Image.open(S/'wall-mask.png'))>0)
for x,y,r,b in [(576,312,624,336),(624,528,688,592)]:allowed[y+16:b+16,x+64:r+64]=True
changed=np.any(now!=old,2);assert not np.any(changed&~allowed),'Unexpected pixels outside the wall/stair patch.'
ref=Image.open(BASE/'source/hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,896),'#223039');registered.paste(ref,(64,16));before=Image.fromarray(old);after=Image.fromarray(now);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
# Source-native comparisons keep one common crop/scale and coordinate origin.
boxes=[('western-wall',(112,144,416,512)),('northern-branches',(496,16,768,416)),('upper-stair',(584,304,760,416)),('lighthouse-courses',(664,528,952,680)),('timber-ramp',(648,512,824,648)),('eastern-shore',(864,208,1152,672))]
for name,box in [('whole-map',(0,0,1152,896)),*boxes]:
 w,h=box[2]-box[0],box[3]-box[1];scale=1 if name=='whole-map' else 2;sh=Image.new('RGB',(3*(w*scale+16)+16,h*scale+48),'#223039');d=ImageDraw.Draw(sh)
 for i,(label,im) in enumerate([('HGSS reference',registered),('Rejected first terrain pass',before),('Rebuilt native rock / stairs',after)]):
  x=16+i*(w*scale+16);d.text((x,8),label,font=font,fill='white');sh.paste(im.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,40))
 sh.save(E/(name+'-before-after.png'))
# Explicit visual course guide: these are observed local courses, not DS z data.
box=(664,528,952,680);w,h=box[2]-box[0],box[3]-box[1];guide=Image.new('RGB',(2*w*3+32,h*3+48),'#223039');d=ImageDraw.Draw(guide)
for i,(label,im) in enumerate([('HGSS: three visible courses',registered),('Native: cap, face, shoulder, return',after)]):
 x=8+i*(w*3+16);guide.paste(im.crop(box).resize((w*3,h*3),Image.Resampling.NEAREST),(x,40));d.text((x,8),label,font=font,fill='white')
 for sy,text,color in [(576,'3: upper lawn face','#ffff99'),(600,'2: middle shoulder / face','#ffbb88'),(624,'1: shoreline face','#99ddff')]:
  y=40+(sy+16-box[1])*3;d.line((x+100,y,x+w*3-12,y),fill=color,width=2);d.text((x+110,y-20),text,font=font,fill=color)
guide.save(E/'course-guide.png')
run=json.loads((R/'results.json').read_text());rom=sha(G/'pokeemerald.gba');assert run['rom_sha256']==rom and all(p['exit_code']==0 for p in run['phases']);write(E/'runtime.json',run);(E/'gameplay').mkdir(exist_ok=True)
for p in R.glob('*.png'):shutil.copyfile(p,E/'gameplay'/p.name)
shots=['north-retaining-wall','western-retaining-wall','beach-wall-return','east-stair-head','east-stair-lane','lighthouse-ramp-west','lighthouse-terrace','headland-three-courses','headland-eastern-turn','lighthouse-door','save-Olivine','cold-reload'];gallery=Image.new('RGB',(1440,1408),'#223039');d=ImageDraw.Draw(gallery)
for i,n in enumerate(shots):
 x,y=i%3*480,i//3*352;d.text((x+8,y+8),n,font=font,fill='white');gallery.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+32))
gallery.save(E/'gameplay-gallery.png')
head=git('rev-parse','HEAD');assert head!=PARENT,'Commit the checked native change before publishing.';files=git('diff','--name-only',PARENT,head).splitlines()
assert all(('/olivine_city/' in p or '/olivine_quay/' in p or '/JohtoOlivineCity/' in p or '/JohtoOlivineQuay/' in p) for p in files),files
assert not git('diff','--name-only',PARENT,head,'--','data/layouts/JohtoOlivineHarbor','data/tilesets/primary/olivine_harbor','data/tilesets/secondary/olivine_harbor')
manifest=[]
for p in files:
 raw=subprocess.check_output(['git','-C',str(G),'show',head+':'+p]);manifest.append(dict(path=p,git_blob=git('rev-parse',head+':'+p),sha256=hashlib.sha256(raw).hexdigest()))
review=json.loads((E/'review.json').read_text());write(E/'preservation.json',dict(source_commit=head,rejected_baseline=PARENT,source_PR='https://github.com/Davisfox5/pokeemerald-expansion/pull/21',source_manifest=manifest,ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,outside_wall_stair_pixel_changes=0,changed_visible_pixels=int(changed.sum()),unchanged='All other source maps, map/layout/warp/event IDs, registries and native Harbor files; shared foreground pixels re-audited.',source_authority='Current native sources; narrow terrain patch input is the immutable rejected c26b9b21, not a replay of the town builder.',owner_visual_acceptance='pending'))
write(E/'build.json',dict(exit_code=0,command='PATH=ARM_BIN:$PATH make -j5',ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Arm GNU 14.2.1',compiler='Porytiles legacy 2.0.0 with exact RGB5 palette covering',palette_solver='OR-Tools candidate set cover; every assigned quadrant checked without nearest-tile substitutions',Porymap='6.3.1 actual project exports',mGBA='0.10.5 headless',runtime_observations=sum(len(p['observations']) for p in run['phases']),phases=[dict(phase=p['phase'],exit_code=p['exit_code']) for p in run['phases']],district_usage=review['district_usage']))
write(E/'visual-review.json',dict(owner_request='Reject all prior walls/ledges; rebuild from scratch with established Johto wall tiles, correct depth/courses, continuous caps/corners/ends, and seated stairs.',rejected_baseline=PARENT,reviewed_regions=[dict(name=n,native_crop=list(b)) for n,b in boxes],changes=['Removed the complete rejected wall paint footprint, including minority 8px fragments missed by its cell-majority material labels.','Rebuilt the northwest one-course forest return with a connected south lip, long east face and beach corner.','Separated the northern long retaining face, upper residential terrace, forest course and short inner spur; corners and termination roles are recorded individually.','Rebuilt the lighthouse as three separately traced 24px-pitch courses, with separate rocky shoulders, stepped east outline, full west/east returns and shoreline toes.','Traced all three eastern shoreline courses through their inward steps and lower returns, rather than one broad repeated face.','Corrected the concave corner orientation where the upper south-facing terrace joins the west-facing lighthouse retaining wall.','Rebuilt the upper stair opening as an opaque 48x24 native seat with complete timber treads and side shoulders; no paving inside the opening.','Retained the east/west timber slope direction and seated it over continuous retaining stone; removed the rejected grey rectangle beneath it.'],native_art='Route36 cap/face/toe/corner masks from 698db52a, Route31 plateau donor from 1643f58a. Unscaled 8px cap plus 16px face/toe assembly gives the observed 24px course pitch. Five face shades and two plateau shades preserve native texture while fitting 13 BG banks.',limits=['Course counts and occluded connections are visual interpretations of HGSS overview geometry, not extracted DS height/collision data.','Tree footprints, architecture, existing district fades, static water, closed interiors and unwired neighboring routes/shipping remain as before.','Owner visual acceptance remains pending; build and traversal checks do not establish it.']))
print(json.dumps(dict(source_commit=head,ROM_sha256=rom,changed_pixels=int(changed.sum()),outside_scope_pixels=0,observations=sum(len(p['observations']) for p in run['phases'])),indent=2))
