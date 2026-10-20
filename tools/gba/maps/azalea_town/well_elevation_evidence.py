from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parents[4];S=H/'gba/art/azalea-town/source';D=S/'well-elevation-rebuild';E=S.parent/'evidence';geo=json.loads((D/'geometry.json').read_text());plan=json.loads((D/'elevation-plan.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
ref=Image.new('RGB',(1024,528),'#223039');ref.paste(Image.open(S/'hgss-reference.png'),(64,16));now=Image.open(E/'native-map.png').convert('RGB');before=np.array(Image.open(D/'before-background.png'));fg=np.array(Image.open(D/'before-foreground.png'));before[fg[...,3]>0]=fg[fg[...,3]>0];before=Image.fromarray(before).convert('RGB');box=(656,80,896,320);scale=3
sheet=Image.new('RGB',(1490,910),'#223039');d=ImageDraw.Draw(sheet)
for x,label,im in [(12,'HGSS reference',ref),(758,'Current native tiles (no resized faces)',now)]:
 d.text((x,10),label,font=font,fill='white');sheet.paste(im.crop(box).resize((720,720),Image.Resampling.NEAREST),(x,40))
for i,line in enumerate(['Town lawn: 0   |   well court: +1   |   upper terrace: +2   |   north rim: +4',
 'Northern wall has two separate courses; +3 is their seam, not an invented walking strip.',
 'Levels are inferred ordinal tiers from the overview; exact DS heights are not available here.',
 'Native adaptation: complete 16px courses replace the rejected stretched/tapered 24/12/8px faces.',
 'Existing stairs are retained placeholders. Building interiors / well descent remain unwired.']):d.text((12,780+i*23),line,font=font,fill='white')
sheet.save(E/'well-elevation-comparison.png')
# A separate labelled topographic diagram overlays only ground, not the wall artwork.
sh=Image.new('RGB',(1484,818),'#223039');d=ImageDraw.Draw(sh)
for xx,label,im in [(12,'HGSS: measured screen-space boundaries',ref),(752,'Native: receiving ground levels',now)]:
 sh.paste(im.crop(box).resize((720,720),Image.Resampling.NEAREST),(xx,36));d.text((xx,9),label,font=font,fill='white')
 for y0,y1,col in [(104,128,'#ffcc55'),(128,144,'#ff8877'),(176,192,'#68cfff'),(256,272,'#bb99ff')]:
  x0,x1=(688,864) if y0==104 else (704,832) if y0==128 else (736,832) if y0==176 else (704,800)
  d.rectangle((xx+(x0-box[0])*3,36+(y0-box[1])*3,xx+(x1-box[0])*3-1,36+(y1-box[1])*3-1),outline=col,width=2)
 for tx,ty,label in [(745,99,'Rim +4'),(735,157,'Terrace +2'),(737,243,'Court +1'),(753,302,'Town 0')]:
  px=xx+(tx-box[0])*3;py=36+(ty-box[1])*3;w=d.textbbox((0,0),label,font=small)[2];d.rectangle((px-2,py-1,px+w+2,py+16),fill='#223039');d.text((px,py),label,font=small,fill='white')
d.text((12,768),'Outlined bands are measured face courses; numbers are inferred relative tiers, not decoded DS Z values.',font=font,fill='white');d.text((12,792),'Northern projected depths: 24px + 8–16px. Court north and south faces: 16px each.',font=font,fill='white');sh.save(E/'well-elevation-plan.png')
now.crop(box).resize((720,720),Image.Resampling.NEAREST).save(E/'well-elevation-current.png')
# Verify visible scope and occupancy from fixed pre-repair snapshots.
a=np.array(before);b=np.array(now);mask=np.any(a!=b,2);allowed=np.zeros(mask.shape,bool);allowed[96:304,640:880]=True;assert not mask[~allowed].any()
oldsolid=np.load(D/'before-solid.npy');solid=np.load(S/'solid.npy');cells=np.zeros(solid.shape,bool);cells[6:19,40:55]=True;assert not (solid!=oldsolid)[~cells].any()
rep=json.loads((E/'well-elevation-rebuild.json').read_text());rep.update(visible_changed_pixels=int(mask.sum()),visible_changes_outside_well=0,collision_changes_outside_well=0,Kurt_property_visible_changes=0,gate_visible_changes=0,whole_shared_modules=len(geo['whole_tiles']),resized_or_sliced_wall_modules=0)
(E/'well-elevation-rebuild.json').write_text(json.dumps(rep,indent=2)+'\n')
