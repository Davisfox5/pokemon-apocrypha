#!/usr/bin/env python3
"""Explicit visual terrain classification for every current exterior metatile.
Graphic tiles are preserved. One visible fence closes a newly accessible edge.
"""
from pathlib import Path
import json,struct,hashlib
from collections import Counter
from PIL import Image,ImageDraw
from tiles import Tileset
R=Path(__file__).resolve().parents[3];G=R/'tools/vendor/gba/johto-restart-game';S=R/'tools/vendor/gba/johto-before-collision-audit-20260922';A=R/'gba/art/johto-restart/evidence'
t=Tileset(S,'cherrygrove','cherrygrove')
def ids(s):return {int(x,16) for x in s.split()}
# Reviewed against the complete native contact sheet: bare ground, beach, paths,
# flowers, and dock deck. Tiny building corner overhangs have clear footing.
walk=ids('004 119 120 121 122 129 12a 202 204 20b 20c 20d 228 250 265 26a 270 275 277 279 27b 27c 27d 27e 280 281 287 28d 2c8 2c9 2ca 2cd 2ce 2d4 2dc 2e5 2e6 2e7 2ef 302 30b 30c 312 31d 31e 31f 320 324 325 326 32b 353')
# Water/bank tiles have no props. Footing uses the center of the lower tile,
# matching the player's contact point. All boat/rock/tree fragments stay solid.
shore=ids('11b 11d 12b 12d 19d 210 271 272 273 274 27a 286 2c7 2cf 2d0 2d2 2f0 2f1 2f2 2f3 2f5 2f7 2f9 2fb 2fc 2fd 33c 354 355 369 36a 36b 36c 36d 36e 36f 370')
doors=ids('268 26e 2bc 350 366')
classification={};water_ratios={}
allmids=set();maps={}
layouts={l['blockdata_filepath'].split('/')[-2]:l for l in json.loads((S/'data/layouts/layouts.json').read_text())['layouts']}
for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach']:
 p=S/f'data/layouts/{name}/map.bin';data=p.read_bytes();vals=list(struct.unpack('<'+'H'*(len(data)//2),data));maps[name]=vals;allmids|={v&1023 for v in vals}
for mid in sorted(allmids):
 kind='door' if mid in doors else 'walk' if mid in walk else 'solid'
 if mid in shore:
  px=list(t.render(mid).crop((4,8,12,16)).getdata());ratio=sum(b>g+8 and g>r+8 for r,g,b in px)/len(px);water_ratios[f'{mid:03x}']=ratio;kind='water' if ratio>=.5 else 'walk'
 classification[mid]=kind
# Explicit structure classes default solid: all facade, cliff-face, sign, fence,
# tree/canopy/trunk, bench, boat, offshore island rock and reef cells were reviewed.
changes=[];counts={};hashes={}
for name,old in maps.items():
 p=G/f'data/layouts/{name}/map.bin';expected=(S/f'data/layouts/{name}/map.bin').read_bytes()
 prior=A/'collision-audit.json';allowed={hashlib.sha256(expected).hexdigest()}
 if prior.exists():allowed.add(json.loads(prior.read_text())['map_hashes'].get(name,''))
 assert hashlib.sha256(p.read_bytes()).hexdigest() in allowed,'New owner edits; stop before overwriting.'
 new=[];counts[name]=dict(Counter(classification[v&1023] for v in old))
 for i,v in enumerate(old):
  mid=v&1023
  if name=='CherrygroveCity' and i==6*80+8:mid=0x297 # Visible fence closes the newly walkable cliff-top edge.
  kind=classification[mid];flags={'walk':0x3000,'water':0x1000,'solid':0x3c00,'door':0}[kind];nv=flags|mid;new.append(nv)
  if nv!=v:changes.append(dict(map=name,x=i%layouts[name]['width'],y=i//layouts[name]['width'],before=f'{v:04x}',after=f'{nv:04x}',kind=kind))
 counts[name]=dict(Counter(classification[v&1023] for v in new))
 p.write_bytes(struct.pack('<'+'H'*len(new),*new));hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
# Use native behavior matching the visual terrain. Covered scenery remains behind actors.
for part in range(2):
 attrs=list(t.attrs[part]);changed_attrs=[]
 for mid,kind in classification.items():
  if int(mid>=512)!=part:continue
  index=mid%512;behavior={'walk':0,'water':0x15,'solid':0,'door':0x69}[kind];attrs[index]=(attrs[index]&~255)|behavior
  if attrs[index]!=t.attrs[part][index]:changed_attrs.append(mid)
 folder=G/f'data/tilesets/{"secondary" if part else "primary"}/cherrygrove';(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
installed=Tileset(G,'cherrygrove','cherrygrove')
for mid in allmids:assert installed.render(mid).tobytes()==t.render(mid).tobytes()
report=dict(unique_metatiles_reviewed=len(allmids),tile_graphics_unchanged=True,visible_barrier_additions=[dict(map='CherrygroveCity',x=8,y=6,kind='fence',reason='closes exposed cliff-top walking strip')],classes={f'{k:03x}':v for k,v in classification.items()},shore_footing_water_fraction=water_ratios,counts=counts,changed_cells=changes,map_hashes=hashes)
(A/'collision-audit.json').write_text(json.dumps(report,indent=2)+'\n')
drawmap=maps['CherrygroveCity'].copy();drawmap[6*80+8]=0x3e97
base=installed.map_image(drawmap,80).convert('RGBA');ov=Image.new('RGBA',base.size);d=ImageDraw.Draw(ov);colors={'walk':(30,230,80,65),'water':(25,160,255,65),'solid':(240,45,55,75),'door':(255,200,0,100)}
for i,v in enumerate(drawmap):x=i%80*16;y=i//80*16;d.rectangle((x,y,x+15,y+15),fill=colors[classification[v&1023]])
Image.alpha_composite(base,ov).convert('RGB').save(A/'collision-audit-overlay.png');print('Reviewed',len(allmids),'metatiles; corrected',len(changes),'cells.');print(json.dumps(counts,indent=2))
