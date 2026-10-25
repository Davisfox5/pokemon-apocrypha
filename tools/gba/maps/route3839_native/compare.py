"""Read-only original/native material comparison and coordinate-labelled visual review."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'));from tiles import Tileset
G=Path(sys.argv[1]);S=ROOT/'gba/art/route38-39-native/source';E=S.parent/'evidence';t=Tileset(G,'route3839_native','route3839_native');reports=[];native={};source={}
def grid(a,ox=0,oy=0):
 im=Image.new('RGB',(a.width+32,a.height+32),(30,35,38));im.paste(a,(32,32));d=ImageDraw.Draw(im)
 for x in range(a.width//16+1):
  d.line((32+x*16,32,32+x*16,im.height),fill=(70,90,80))
  if x%4==0:d.text((32+x*16,10),str(ox+x),fill='white')
 for y in range(a.height//16+1):
  d.line((32,32+y*16,im.width,32+y*16),fill=(70,90,80))
  if y%4==0:d.text((2,32+y*16),str(oy+y),fill='white')
 return im
for n,W,H in [(38,64,32),(39,32,64)]:
 native[n]=Image.open(E/f'route{n}-native.png').convert('RGB');source[n]=Image.open(S/f'route{n}-hgss/original.png').convert('RGB');layers=np.load(S/f'route{n}-layers.npz');clear=np.load(S/f'route{n}-hgss/cleared.npz');a=np.array(native[n]);rgb=clear['rgb'].astype(int);names=list(clear['names']);ids=[i for i,s in enumerate(names) if s.startswith('road01')];road=np.isin(clear['material'],ids)&(rgb[...,0]>=rgb[...,1])&(rgb[...,0]>180)&(rgb[...,2]<175);q=road.reshape(H*2,8,W*2,8).mean((1,3))>=.5
 assert np.array_equal(q,layers['quadrants'])
 # Compare real native material pixels at the center of every unoccluded 8px square.
 # The gray lawn rim has R<G; road shades have R>G, including its contact outline.
 v=a[4::8,4::8];decoded=v[...,0]>v[...,1];eligible=np.repeat(np.repeat(np.isin(layers['material'],['L','P']),2,0),2,1);mismatch=eligible&(decoded!=q);assert not mismatch.any(),np.argwhere(mismatch).tolist()
 defined=clear['defined'].reshape(H*2,8,W*2,8).mean((1,3))>=.5
 reports.append(dict(route=n,original_quadrants=int(q.size),reviewed_ground_quadrants=int(eligible.sum()),original_ground_defined_reviewed=int((eligible&defined).sum()),original_ground_undefined_reviewed=int((eligible&~defined).sum()),native_road_quadrants=int(q[eligible].sum()),original_material_matches=int((eligible&defined&~mismatch).sum()),adapted_undefined_ground_quadrants=int((eligible&~defined).sum()),material_mismatches=int((mismatch&defined).sum()),excluded_rock_stair_ramp_quadrants=int((~eligible).sum()),note='Undefined original backing is lawn by explicit adaptation. Wall/stair/ramp squares are reviewed separately, not counted as ground material matches.'))
 if n==38:
  whole=Image.new('RGB',(1024,1056),(28,33,38));whole.paste(source[n],(0,24));whole.paste(native[n],(0,544));d=ImageDraw.Draw(whole);d.text((8,5),'HGSS original, 16px/cell, offset (0,0)',fill='white');d.text((8,525),'NATIVE terrain-only rebuild, same grid',fill='white')
 else:
  whole=Image.new('RGB',(1056,1048),(28,33,38));whole.paste(source[n],(0,24));whole.paste(native[n],(544,24));d=ImageDraw.Draw(whole);d.text((8,5),'HGSS original',fill='white');d.text((552,5),'NATIVE terrain-only, same cells',fill='white')
 whole.save(E/f'route{n}-original-native.png')
 for part in [0,1]:
  box=(part*512,0,(part+1)*512,512) if n==38 else (0,part*512,512,(part+1)*512)
  src=grid(source[n].crop(box),box[0]//16,box[1]//16);dst=grid(native[n].crop(box),box[0]//16,box[1]//16);sheet=Image.new('RGB',(1104,568),(28,33,38));sheet.paste(src,(0,24));sheet.paste(dst,(560,24));d=ImageDraw.Draw(sheet);d.text((8,5),f'Route {n}: original HGSS',fill='white');d.text((568,5),'Native: same numbered squares',fill='white');sheet.save(E/f'route{n}-grid-comparison-{part+1}.png')
(E/'material-comparison.json').write_text(json.dumps(reports,indent=2)+'\n')
# Whole-turn review crops, original and native, including the independent source level.
items=[(38,6,15,'Western turn'),(38,31,21,'South bank inner corner'),(38,58,20,'South bank eastern return'),(38,0,9,'East-facing junction stairs'),(39,15,24,'Farm stair shoulders'),(39,3,31,'Paddock return'),(39,23,44,'East terrace courses'),(39,19,54,'South stair shoulders')]
sheet=Image.new('RGB',(1024,880),(28,33,38));d=ImageDraw.Draw(sheet)
for i,(n,x,y,label) in enumerate(items):
 X=(i%4)*256;Y=(i//4)*440;box=(x*16,y*16,(x+6)*16,(y+6)*16)
 d.text((X+4,Y+4),f'R{n} ({x},{y}) {label}',fill='white');sheet.paste(source[n].crop(box).resize((192,192),Image.Resampling.NEAREST),(X,Y+24));sheet.paste(native[n].crop(box).resize((192,192),Image.Resampling.NEAREST),(X,Y+232))
sheet.save(E/'wall-original-native.png');print(reports)
