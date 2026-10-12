#!/usr/bin/env python3
"""Read-only extraction of the HGSS area-2 texture set with explicit aliases."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/hoennconv'))
import narc
from nsbtx import Tex0
from PIL import Image,ImageDraw
src=ROOT/'disasm/pokeheartgold/files/a/0/4/4';out=ROOT/'gba/art/johto-v4/sources';out.mkdir(parents=True,exist_ok=True)
t=Tex0(narc.load(src)[2]);original=t.pal_for
aliases={'tree01gs':'tree01','cliff01gs':'cliff01','grass01gs':'grass01','allpeakgs':'apeak','allpeak_pgs':'apeak','sea_on':'sea_f02_pl'}
t.pal_for=lambda e: next(p for p in t.palettes if p.name==aliases[e.name]) if e.name in aliases else original(e)
names=['fieldkk01','tree01gs','tree01_re','tree01_un','cliff01gs','grass02','grass02_r','road01','road01_r','road01_sub','beach01','beach01_r','beach_sub','sea_on','sea_un','sea_line02','sea_rock','sea_rock_m','rock01','wall01_d','wall01_g','flower01','flower02','flower03','yo_sp1','fence_a','bridge_a','bridge_b','bridge_c','pond_edge','pond_on','pond_un','f_kage']
report=[];board=Image.new('RGB',(1024,((len(names)+5)//6)*170),'#26343c');d=ImageDraw.Draw(board)
for i,name in enumerate(names):
 e=next(e for e in t.textures if e.name==name);im=t.render(e);im.save(out/(name+'.png'));x=i%6*170;y=i//6*170;board.paste(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),(x,y+18),im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST));d.text((x,y),name,fill='white')
 report.append(dict(name=name,palette=t.pal_for(e).name,size=im.size,colors=len(im.getcolors(10000)),alpha_bbox=im.getbbox()))
(ROOT/'gba/art/johto-v4/evidence/texture-atlas.png').parent.mkdir(exist_ok=True)
board.save(ROOT/'gba/art/johto-v4/evidence/texture-atlas.png')
(ROOT/'gba/art/johto-v4/provenance.json').write_text(json.dumps(dict(source=str(src.relative_to(ROOT)),member=2,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),assets=report,credit='Game Freak / Nintendo / Creatures; HGSS game-derived art, read-only extraction.'),indent=2)+'\n')
print('Extracted',len(names),'native HGSS textures')
