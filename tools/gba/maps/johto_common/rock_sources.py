"""Read-only rock-family survey of local HGSS and Platinum texture/map data."""
from pathlib import Path
import sys,re,json,hashlib
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tools/hoennconv'));import narc
from nsbtx import Tex0
import argparse
ROOT=Path(__file__).resolve().parents[4]
p=argparse.ArgumentParser();p.add_argument('--donors',type=Path,required=True);args=p.parse_args()
R=args.donors;O=ROOT/'gba/art/johto-common/rocks/source-data';O.mkdir(parents=True,exist_ok=True);allrecords=[];bad=[]
sys.path.insert(0,str(ROOT/'tools/regionport'));from mdlview import Model
# Read actual model material->palette bindings. Do not guess texture palettes.
for game,blobs in [('hgss',narc.load(R/'pokeheartgold/files/a/0/6/5')),('platinum',[p.read_bytes() for p in sorted((R/'pokeplatinum/res/field/maps/data').glob('*.bin'))])]:
    pairs={}
    for blob in blobs:
        start=blob.find(b'BMD0')
        if start<0:continue
        m=Model(blob[start:])
        for mat,name in m.mat_tex.items():
            pal=m.mat_pal.get(mat)
            if pal:pairs.setdefault(name,set()).add(pal)
    (O/('bindings-'+game+'.json')).write_text(json.dumps({k:sorted(v) for k,v in pairs.items()},indent=2)+'\n')
registry=json.loads((O/'source-ids.json').read_text()) if (O/'source-ids.json').exists() else {}
prior={tuple(k.split('/')):v for k,v in registry.items()}
next_id={g:1+max([int(v[1:]) for (game,digest),v in prior.items() if game==g] or [0]) for g in ['HGSS','Platinum']}
pattern=r'^(c3_iwa|c3_slope|c09_ice|cliff|cave|wall0[12]|wallkn|wall_area|allpeak|dcliff|dwall|dallpeak|gsm_dcliff|ice_fe|chole|dslope|r_dwall|r_dcliff|r_dslope|r_chole|r_climb|dr_climb|icehole|ymb_hole|wcliff|a_9wcliff|enccliff|fpeak|dhole|dun_(wall|allpeak|slope|dansou|ent|sside|level)|fice_|magma|s_snow)'
for game,blobs in [('HGSS',[(str(i),b) for i,b in enumerate(narc.load(R/'pokeheartgold/files/a/0/4/4'))]),('Platinum',[(p.name,p.read_bytes()) for p in sorted((R/'pokeplatinum/res/field/maps/texture_sets').glob('*.nsbtx'))])]:
 seen={};records=[]
 for member,b in blobs:
  try:t=Tex0(b)
  except ValueError:continue
  for e in t.textures:
   if not re.search(pattern,e.name):continue
   bindings=json.loads((O/('bindings-'+game.lower()+'.json')).read_text())
   pals=[p for p in t.palettes if p.name in bindings.get(e.name,[])]
   if not pals:pals=[p for p in t.palettes if p.name in (e.name,e.name+'_pl')]
   if not pals and e.name=='a_9wcliff':pals=[p for p in t.palettes if p.name=='a9_criff']
   if not pals:bad.append((game,member,e.name,'palette?',','.join(p.name for p in t.palettes)));continue
   for pal in pals:
    t.pal_for=lambda _,p=pal:p
    try:im=t.render(e)
    except Exception as err:bad.append((game,member,e.name,str(err)));continue
    digest=hashlib.sha256(im.tobytes()+str(im.size).encode()).hexdigest();origin=dict(member=member,texture=e.name,palette=pal.name,format=e.fmt,blob_sha256=hashlib.sha256(b).hexdigest())
    if digest in seen:seen[digest]['sources'].append(origin);continue
    key=prior.get((game,digest))
    if key is None:key=('H' if game=='HGSS' else 'D')+str(next_id[game]).zfill(3);next_id[game]+=1
    f=game+'-'+key+'.png';im.save(O/f)
    record=dict(id=key,game=game,name=e.name,palette=pal.name,size=list(im.size),file=f,pixel_sha256=digest,sources=[origin]);seen[digest]=record;records.append(record)
 allrecords+=records
 print(game,len(records))
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
 for page in range((len(records)+29)//30):
  group=records[page*30:(page+1)*30];sheet=Image.new('RGB',(1000,((len(group)+4)//5)*150),'#28343d');d=ImageDraw.Draw(sheet)
  for j,r in enumerate(group):
   x=j%5*200;y=j//5*150;d.text((x+5,y+3),r['id']+' '+r['name'],font=font,fill='white');d.text((x+5,y+18),r['palette'],font=font,fill='#aabbcc');im=Image.open(O/r['file']);z=max(1,min(3,180//im.width,108//im.height));im=im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST);sheet.paste(im,(x+4,y+37),im)
  sheet.save(O/(game+'-survey-'+str(page)+'.png'))
(O/'records.json').write_text(json.dumps(allrecords,indent=2));(O/'errors.json').write_text(json.dumps(bad,indent=2));print('unresolved',len(bad));print(str(bad)[:2200])

(O/'source-ids.json').write_text(json.dumps({r['game']+'/'+r['pixel_sha256']:r['id'] for r in allrecords},indent=2)+'\n')
