"""One-shot guarded native Union Cave 1F authoring from its original material trace."""
from pathlib import Path
import sys,json,struct,hashlib
from collections import Counter
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/union-cave-1f/source';E=S.parent/'evidence';G=Path(sys.argv[1]);manifest=S/'generated-files.json'
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
if (G/'data/tilesets/primary/union_cave').exists():
 assert manifest.exists(),'Existing cave art has no matching guard manifest'
 changed=[p for p,h in json.loads(manifest.read_text()).items() if not (G/p).exists() or digest(G/p)!=h]
 assert not changed,('Preserve owner edits',changed)
else:
 baseline=json.loads((S/'baseline-owned-files.json').read_text())
 assert all((G/p).exists() and digest(G/p)==h for p,h in baseline.items()),'Preserve edited entrance test room'
a=np.array(Image.open(S/'clean-terrain.png').convert('RGB'));label=np.load(S/'hgss-pixel-materials.npy');pal=[];indices=[]
r,g,b=a.transpose(2,0,1).astype(int);patchbank=np.zeros((120,68),int)
for yy in range(120):
 for xx in range(68):
  sl=np.s_[yy*8:yy*8+8,xx*8:xx*8+8];ll=label[sl];rr,gg,bb=r[sl],g[sl],b[sl]
  if np.count_nonzero((rr>=160)&(gg>=160)&(bb>=144))>=8:bank=4
  elif np.count_nonzero(ll=='W')>=16:bank=2
  elif np.count_nonzero(ll=='O')>=8:bank=3
  else:bank=int(np.count_nonzero(ll=='R')>=32)
  patchbank[yy,xx]=bank
pixelbank=np.repeat(np.repeat(patchbank,8,0),8,1)
for bank in range(5):
 pixels=a[pixelbank==bank];im=Image.fromarray(pixels.reshape(-1,1,3));q=im.quantize(colors=15,method=Image.Quantize.MEDIANCUT);co=np.array(q.getpalette()[:45],int).reshape(15,3)&248;co=np.vstack(([0,0,0],co));co[15]=0;pal.append(co)
 diff=((a.astype(np.int32)[...,None,:]-co[None,None,:,:])**2).sum(3);diff[...,0]=1000000000;indices.append(diff.argmin(2).astype(np.uint8))
patches=[];banks=[];keys=[];forekeys=[];heads=np.load(S/'hgss-overhead-rock-heads.npy')
for y in range(0,960,8):
 for x in range(0,544,8):
  bank=int(patchbank[y//8,x//8]);p=indices[bank][y:y+8,x:x+8].copy();patches.append(p);banks.append(bank);keys.append((bank,p.tobytes()));fp=np.where(heads[y:y+8,x:x+8],indices[3][y:y+8,x:x+8],0).astype(np.uint8);forekeys.append((3,fp.tobytes()) if fp.any() else (0,bytes(64)))
counts=Counter(keys+forekeys);print('Raw native glyphs',len(counts))
# Retain exact boundary tiles. Compress interior texture variation only, per material.
boundary=set()
for i,(bank,p) in enumerate(keys):
 y=i//68*8;x=i%68*8;l=label[y:y+8,x:x+8]
 if len(set(l.ravel()))>1:boundary.add((bank,p))
print('Boundary glyphs',len(boundary))
# Boundaries with very low-count differing pixels are texture speckles, not terrain edges.
critical=set()
for i,k in enumerate(keys):
 y=i//68*8;x=i%68*8;l=label[y:y+8,x:x+8];u,n=np.unique(l,return_counts=True)
 if len(u)>1 and n.min()>=8:critical.add(k)
print('Critical glyphs',len(critical))
# Native budget: 1007 static glyphs including black; reserve 1008..1023 scratch.
selected=list(dict.fromkeys(forekeys))+[(0,bytes(64))]+[k for bank in range(5) for k,n in sorted(((k,n) for k,n in counts.items() if k[0]==bank),key=lambda q:-q[1])[:12]];selected+=sorted(critical,key=lambda k:-counts[k]);selected=list(dict.fromkeys(selected));assert len(selected)<1008,len(selected)
for k,n in counts.most_common():
 if k not in selected:selected.append(k)
 if len(selected)==1008:break
# RGB nearest native glyph; penalize losing black void/water shapes heavily.
lookup={k:i for i,k in enumerate(selected)};cache={};errors=[]
for k in counts:
 if k in lookup:continue
 bank,p=k;src=np.frombuffer(p,np.uint8).reshape(8,8);choices=[(i,np.frombuffer(v,np.uint8).reshape(8,8)) for i,(b,v) in enumerate(selected) if b==bank];rgb=pal[bank][src].astype(int);cost=[]
 for i,v in choices:
  d=pal[bank][v].astype(int)-rgb;loss=int((d*d).sum())+int(np.count_nonzero((v==0)!=(src==0)))*100000;cost.append(loss)
 j=int(np.argmin(cost));lookup[k]=choices[j][0];errors.append(min(cost))
print('Packed glyphs',len(selected),'approximated texture glyphs',len(errors))
# Pack metatiles, using private primary and secondary entries only.
entries=[];mids={};grid=np.zeros((60,34),np.uint16);attrs=[];plan=np.array([list(r) for r in (S/'hgss-material-grid.txt').read_text().splitlines()]);foot_blocked=np.load(S/'hgss-foot-blocked.npy')
for y in range(60):
 for x in range(34):
  es=[];ts=[]
  for q in range(4):
   i=(y*2+q//2)*68+x*2+q%2;k=keys[i];fk=forekeys[i];es.append(lookup[k]|(k[0]<<12));ts.append(lookup[fk]|(fk[0]<<12))
  behavior=101 if (x,y)==(28,19) else (16 if plan[y,x]=='W' else 0);blocked=bool(foot_blocked[y,x]);attr=behavior|(0 if heads[y*16:y*16+16,x*16:x*16+16].any() else 0x1000);key=tuple(es+ts)+(attr,)
  if key not in mids:mids[key]=len(entries);entries.append(tuple(es+ts));attrs.append(attr)
  grid[y,x]=mids[key]|(0xc00 if blocked else 0)|0x3000
print('Metatiles',len(entries));assert len(entries)<=1024
for part,typ in enumerate(['primary','secondary']):
 d=G/'data/tilesets'/typ/'union_cave';(d/'palettes').mkdir(parents=True,exist_ok=True)
 tiledata=selected[part*512:(part+1)*512];im=Image.new('P',(128,256));im.putpalette([v for c in pal[0] for v in map(int,c)]+[0]*720)
 for i,(bank,p) in enumerate(tiledata):im.paste(Image.fromarray(np.frombuffer(p,np.uint8).reshape(8,8),'P'),(i%16*8,i//16*8))
 im.save(d/'tiles.png')
 for n in range(16):
  co=pal[n] if n<5 else pal[0];(d/'palettes'/f'{n:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in co)+'\n')
 blocks=entries[part*512:(part+1)*512];at=attrs[part*512:(part+1)*512];blocks+= [(0,)*8]*(512-len(blocks));at+=[0]*(512-len(at));(d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks));(d/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*at))
layout=G/'data/layouts/UnionCaveRoute32Entrance';grid.astype('<u2').tofile(layout/'map.bin');np.full(4,0xc00|0x3000,dtype='<u2').tofile(layout/'border.bin')
f=G/'data/layouts/layouts.json';j=json.loads(f.read_text())
for l in j['layouts']:
 if l['id']=='LAYOUT_UNION_CAVE_ROUTE32_ENTRANCE':l.update(width=34,height=60,primary_tileset='gTileset_UnionCavePrimary',secondary_tileset='gTileset_UnionCaveSecondary')
content=json.dumps(j,indent=2)+'\n'
if f.read_text()!=content:f.write_text(content)
for typ in ['Primary','Secondary']:
 lower=typ.lower();name='UnionCave'+typ;d=f'data/tilesets/{lower}/union_cave';reg={'graphics.h':f'const u32 gTilesetTiles_{name}[] = INCGFX_U32("{d}/tiles.png", ".4bpp.fastSmol");\n'+f'const u16 gTilesetPalettes_{name}[][16] = {{\n'+''.join(f'INCGFX_U16("{d}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n','metatiles.h':f'const u16 gMetatiles_{name}[] = INCBIN_U16("{d}/metatiles.bin");\nconst u16 gMetatileAttributes_{name}[] = INCBIN_U16("{d}/metatile_attributes.bin");\n','headers.h':f'const struct Tileset gTileset_{name} = {{ .isCompressed = TRUE, .isSecondary = '+('TRUE' if typ=='Secondary' else 'FALSE')+f', .tiles = gTilesetTiles_{name}, .palettes = gTilesetPalettes_{name}, .metatiles = gMetatiles_{name}, .metatileAttributes = gMetatileAttributes_{name}, .callback = NULL }};\n'}
 for fn,entry in reg.items():
  p=G/'src/data/tilesets'/fn;s=p.read_text();tag='// Union Cave 1F '+typ+'\n'
  if tag not in s:p.write_text(s+'\n'+tag+entry)
  else:assert entry in s
f=G/'data/maps/UnionCaveRoute32Entrance/map.json';j=json.loads(f.read_text());j['warp_events'][0].update(x=28,y=19);j['region_map_section']='MAPSEC_UNION_CAVE';j.update(allow_escaping=True,show_map_name=True);content=json.dumps(j,indent=2)+'\n'
if f.read_text()!=content:f.write_text(content)
# Append the real map section without renumbering any existing named location.
f=G/'src/data/region_map/region_map_sections.json';j=json.loads(f.read_text())
if not any(v['id']=='MAPSEC_UNION_CAVE' for v in j['map_sections']):
 j['map_sections'].append({'id':'MAPSEC_UNION_CAVE','name':'UNION CAVE','x':2,'y':8,'width':1,'height':1});f.write_text(json.dumps(j,indent=2)+'\n')
f=G/'include/regions.h';text=f.read_text()
if 'case MAPSEC_UNION_CAVE:' not in text:f.write_text(text.replace('case MAPSEC_DARK_CAVE:', 'case MAPSEC_UNION_CAVE: return REGION_JOHTO;\n    case MAPSEC_DARK_CAVE:'))
# Route32 destination warp ID remains unchanged, so the exterior is untouched.
np.save(S/'native-metatile-grid.npy',grid);np.save(S/'native-material-grid.npy',plan)
sys.path.insert(0,str(Path(__file__).resolve().parent.parent));from tiles import Tileset
t=Tileset(G,'union_cave','union_cave');t.map_image(list(map(int,grid.ravel())),34).save(E/'native-map.png')
paths=[f for d in [layout,G/'data/tilesets/primary/union_cave',G/'data/tilesets/secondary/union_cave',G/'data/maps/UnionCaveRoute32Entrance'] for f in d.rglob('*') if f.is_file() and f.name not in ['header.inc','events.inc','connections.inc']];manifest.write_text(json.dumps({str(p.relative_to(G)):digest(p) for p in paths},indent=2)+'\n')
(E/'packing.json').write_text(json.dumps({'raw_glyphs':len(counts),'static_glyphs':len(selected),'metatiles':len(entries),'critical_boundary_glyphs':len(critical),'approximated_interior_texture_glyphs':len(errors),'quantization':'five private native 15-color palettes; exact retained critical boundaries; nearest reusable native texture glyph for remaining rare interiors','source':'original HGSS 1F; characters/items removed; no campaign actors invented','water':'native surfable behavior; static art in this pass'},indent=2)+'\n')
