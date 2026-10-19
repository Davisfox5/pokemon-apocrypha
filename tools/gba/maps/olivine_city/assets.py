"""First-authoring local HGSS Olivine masters and unchanged shared art.
Explicit silhouettes; geographic authority is the original overview, not DS data.
"""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/olivine-city/source';M=S/'masters';M.mkdir(parents=True,exist_ok=True)
ref=Image.open(S/'hgss-reference.png').convert('RGB');report=[];shared=[]
for name in ['tree','center','mart','grass','P12','P13']:
 p=ROOT/'gba/art/azalea-town/source/masters'/f'{name}.png';shutil.copyfile(p,M/p.name);shared.append(dict(name=name,source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(S/'shared-provenance.json').write_text(json.dumps(shared,indent=2)+'\n')
def extract(name,box,polys=None,colors=15,palette=None):
 a=np.array(ref.crop(box));mask=Image.new('L',(box[2]-box[0],box[3]-box[1]),255 if polys is None else 0);d=ImageDraw.Draw(mask)
 for poly in polys or []:d.polygon([(x-box[0],y-box[1]) for x,y in poly],fill=255)
 m=np.array(mask)>0
 if palette is None:
  q=Image.fromarray(a[m].reshape(-1,1,3)).quantize(colors=colors,method=Image.Quantize.MEDIANCUT);palette=np.unique(np.array(q.getpalette()[:colors*3],np.uint8).reshape(-1,3)&248,axis=0)
 out=np.zeros((*m.shape,4),np.uint8);v=a[m].astype(int);out[m,:3]=palette[np.argmin(np.sum((v[:,None]-palette.astype(int))**2,2),1)];out[m,3]=255
 Image.fromarray(out).save(M/f'{name}.png');report.append(dict(name=name,box=box,polygons=polys,colors=len(palette),origin='HGSS Olivine overview; explicit unobscured silhouette, RGB5 native palette'))
 return palette
# Retain each roof ridge, projecting eave, glazing and complete foundation.
extract('civic-hall',(176,144,304,256),[[(196,174),(216,161),(235,155),(255,159),(278,170),(290,183),(294,203),(290,223),(278,235),(260,241),(214,241),(195,233),(186,220),(184,200),(189,181)]])
extract('house',(272,272,352,368),[[(278,292),(286,282),(300,275),(311,272),(319,276),(334,283),(344,295),(345,322),(339,327),(339,352),(283,352),(283,327),(276,323)]])
extract('house-pair',(496,176,576,280),[[(501,210),(513,201),(530,190),(537,188),(552,196),(564,203),(568,218),(568,244),(562,249),(562,269),(507,269),(507,249),(499,245)]])
extract('cafe',(144,400,224,480),[[(149,409),(189,409),(189,404),(205,404),(205,414),(213,416),(213,441),(217,445),(213,453),(211,473),(150,473),(149,451),(145,449)]])
extract('lighthouse',(688,336,816,528),[[(738,352),(753,349),(767,359),(774,374),(770,387),(806,390),(808,409),(808,478),(801,486),(796,516),(704,516),(702,487),(693,484),(693,393),(725,390),(727,368)]])
extract('terminal',(304,688,480,816),[[(327,710),(385,696),(414,696),(465,710),(469,769),(462,777),(460,799),(325,799),(325,780),(312,780),(312,767),(320,763),(320,716)]])
# A compact original repeated material core preserves the cobbled civic paving.
extract('paving',(360,112,392,144),colors=7)
extract('sand',(368,40,384,56),colors=5)
extract('deck',(368,560,384,592),colors=7)
extract('water',(784,744,816,776),colors=6)
# Every cliff orientation uses one shared material ramp, including caps and toes.
cliff=extract('cliff-front',(704,584,736,616),colors=10)
extract('cliff-side',(640,416,672,448),palette=cliff)
extract('cliff-top',(560,160,592,176),palette=cliff)
extract('cliff-toe',(704,616,736,648),palette=cliff)
extract('cliff-left',(96,184,112,216),palette=cliff)
# Source rock heads have independent silhouettes, kept clear of water/foam.
rock=extract('sea-rock',(952,304,984,336),[[(958,311),(971,308),(978,316),(983,326),(977,333),(960,333),(952,326)]],colors=9)
extract('land-rock',(520,336,552,368),[[(530,342),(540,343),(546,352),(549,364),(538,369),(525,366),(522,358)]],palette=cliff)
extract('stairs',(576,312,616,336),[[(579,315),(612,315),(612,334),(579,334)]],palette=cliff)
extract('ramp',(624,528,688,592),[[(630,548),(678,527),(679,567),(632,590)]],colors=10)
# White quayside ironwork and furniture share a cool neutral ladder.
rail=extract('rail',(144,624,176,648),[[(144,633),(147,633),(147,630),(150,630),(150,638),(154,638),(154,630),(157,630),(157,638),(161,638),(161,630),(164,630),(164,638),(168,638),(168,630),(171,630),(171,638),(175,638),(175,644),(144,644)]],colors=8)
extract('bench',(128,576,208,608),[[(136,580),(198,580),(201,594),(194,597),(194,605),(141,605),(141,597),(135,595)]],palette=rail)
extract('umbrella',(136,544,200,592),[[(141,569),(153,552),(164,546),(177,549),(191,567),(180,574),(168,572),(169,587),(165,587),(164,573),(154,575)]],colors=12)
extract('boat',(248,608,336,688),[[(283,609),(290,612),(291,625),(311,646),(310,652),(321,655),(324,674),(314,678),(288,676),(251,666),(253,661),(269,651),(282,631)]],colors=12)
extract('bunting',(104,272,256,328),[[(110,279),(115,276),(119,279),(119,287),(126,288),(235,288),(237,278),(241,275),(246,278),(246,290),(243,293),(243,319),(248,321),(249,329),(235,329),(235,318),(238,316),(238,297),(118,297),(118,317),(121,320),(121,329),(108,329),(108,319),(112,316),(112,291),(109,288)]],colors=12)
# Remove the original Gym emblem: this is a civic/port building in Apocrypha,
# not an active Gym. Preserve the original architectural shell and glazing.
a=np.array(Image.open(M/'civic-hall.png'));a[66:79,50:74,:3]=[112,144,152]
im=Image.fromarray(a);d=ImageDraw.Draw(im);d.line([(231-176,211-144),(240-176,216-144),(249-176,211-144)],fill=(200,216,216,255),width=2);d.line((240-176,207-144,240-176,219-144),fill=(200,216,216,255),width=2);im.save(M/'civic-hall.png')
report.append(dict(name='civic-hall',adaptation='Former Gym exterior retained at HGSS footprint; original Gym badge removed, small maritime crest is an exterior proposal. No Gym mechanics.'))
# Adjacent rails, benches and deck have independent palette families. No global
# blurring, no scaling, and no geometry-changing nearest-tile substitutions.
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print('masters',len(list(M.glob('*.png'))))
# One maritime prop ramp protects cool fabric, cream sails, dark rigging and
# ochre pennants. Reserve native banks for landmarks, not duplicate prop grays.
marine=np.array([(24,40,48),(48,64,64),(80,88,80),(120,128,120),(168,176,152),(216,216,184),(240,240,208),(24,80,112),(32,120,152),(40,160,192),(88,192,208),(88,64,32),(144,104,40),(208,168,64),(248,208,96)],np.uint8)
for name in ['boat','umbrella','bunting']:
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=marine[np.argmin(np.sum((v[:,None]-marine.astype(int))**2,2),1)];Image.fromarray(a).save(M/f'{name}.png')
for name in ['ramp']:
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=cliff[np.argmin(np.sum((v[:,None]-cliff.astype(int))**2,2),1)];Image.fromarray(a).save(M/f'{name}.png')
report.append(dict(names=['boat','umbrella','bunting'],adaptation='shared native maritime palette, masks and unscaled texture detail preserved'))
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
# A shared ground ramp makes every lawn/paver/cliff/sand corner fit one bank.
# Texture patterns stay intact; six-to-seven step rock shading is retained.
def native_colors(n):
 q=np.array(Image.open(M/f'{n}.png').convert('RGBA'));return np.unique(q[q[...,3]>0,:3],axis=0)
cliff7=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.uint8)
pave4=np.array([(112,144,144),(136,160,160),(160,176,176),(184,192,184)],np.uint8)
for name in ['cliff-front','cliff-side','cliff-top','cliff-toe','cliff-left','land-rock','stairs','ramp']:
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=cliff7[np.argmin(np.sum((v[:,None]-cliff7.astype(int))**2,2),1)];Image.fromarray(a).save(M/f'{name}.png')
for name,p in [('paving',pave4),('sand',cliff7[-2:])]:
 a=np.array(Image.open(M/f'{name}.png').convert('RGBA'));m=a[...,3]>0;v=a[m,:3].astype(int);a[m,:3]=p[np.argmin(np.sum((v[:,None]-p.astype(int))**2,2),1)];Image.fromarray(a).save(M/f'{name}.png')
report.append(dict(names=['cliff-front','cliff-side','cliff-top','cliff-toe','cliff-left','land-rock','stairs','ramp','paving','sand'],adaptation='coherent 15-color native ground family with unchanged shared grass, seven rock shades and four cobble shades; preserve masks, orientation and texture'))
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
# Restore the original sand's sparse grain explicitly. A nearest-color remap
# would collapse all of this pale donor to one entry in the warm ground bank.
a=np.array(ref.crop((368,40,384,56)));lum=a.astype(int).mean(2);out=np.zeros((16,16,4),np.uint8);out[...,:3]=[216,184,120];out[lum<np.quantile(lum,.12),:3]=[192,152,96];out[...,3]=255;Image.fromarray(out).save(M/'sand.png')
report.append(dict(name='sand',adaptation='source grain positions retained by a local low-luminance threshold into two warm ground-bank colors; avoids flat nearest-color reduction'))
(S/'local-asset-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
