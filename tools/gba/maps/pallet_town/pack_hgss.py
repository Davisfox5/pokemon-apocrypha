#!/usr/bin/env python3
"""Compile converted HGSS layers through Porytiles, then install only Pallet sources.
Never run on owner-edited layouts. Native files, not this initial compiler, own later edits.
"""
from pathlib import Path
import sys,math,json,struct,subprocess,shutil
import numpy as np
from PIL import Image
from native import words
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];E=Path(sys.argv[1]);PT=Path(sys.argv[2]);ART=ROOT/'gba/art/pallet-town';SRC=ART/'source/hgss';PACK=SRC/'porytiles';PACK.mkdir(exist_ok=True)
SPECS=[('ApocPalletTown','palletoutdoor','pallettown',24,20),('ApocPalletRedHouse1F','palletindoor','palletredhouse',13,10),('ApocPalletRedHouse2F','palletindoor','palletbedroom',12,9),('ApocPalletOakHouse','palletindoor','palletoakhouse',13,10),('ApocPalletLab','palletlabprimary','palletlab',13,14)]
def sheet(bg,fg,w,h,folder,extra=[]):
 count=w*h+len(extra);size=(128,math.ceil(count/8)*16);bottom=Image.new('RGBA',size);middle=Image.new('RGBA',size);top=Image.new('RGBA',size)
 pairs=[]
 for y in range(h):
  for x in range(w):pairs.append((bg.crop((x*16,y*16,x*16+16,y*16+16)),fg.crop((x*16,y*16,x*16+16,y*16+16))))
 pairs+=extra
 for i,(b,f) in enumerate(pairs):middle.paste(b,(i%8*16,i//8*16));top.paste(f,(i%8*16,i//8*16))
 if folder.name not in ('palletoutdoor','pallettown'):
  # FRLG/HGSS interior floor and furniture sit behind sprites, including flat carpets and stair treads.
  bottom,middle,top=middle,top,Image.new('RGBA',size)
 folder.mkdir(exist_ok=True);bottom.save(folder/'bottom.png');middle.save(folder/'middle.png');top.save(folder/'top.png');return count
# Common native families sit in the primary; each map gets its own editable secondary cell sheet.
prim={}
for name,pr,se,w,h in SPECS:
 if pr in prim:continue
 if name=='ApocPalletTown':
  bg=Image.open(SRC/'town-ground.png');fg=Image.open(SRC/'town-foreground.png');pairs=[]
  for x,y in [(0,0),(1,0),(0,1),(1,1),(10,10),(11,10),(10,11),(11,11),(8,18),(9,18),(8,19),(9,19)]:pairs.append((bg.crop((x*16,y*16,x*16+16,y*16+16)),fg.crop((x*16,y*16,x*16+16,y*16+16))))
 else:
  bg=Image.open(SRC/name/'ground.png');fg=Image.open(SRC/name/'foreground.png');pairs=[]
  for x,y in [(2,7),(3,7),(2,6),(3,6),(6,0),(7,0),(6,1),(7,1)]:pairs.append((bg.crop((x*16,y*16,x*16+16,y*16+16)),fg.crop((x*16,y*16,x*16+16,y*16+16))))
 if pr=='palletindoor':
  # Reserve the HGSS laboratory's wood-floor family in otherwise spare shared primary palettes.
  lg=Image.open(SRC/'ApocPalletLab/ground.png');lf=Image.open(SRC/'ApocPalletLab/foreground.png')
  for x,y in [(6,11),(7,11)]:pairs.append((lg.crop((x*16,y*16,x*16+16,y*16+16)),lf.crop((x*16,y*16,x*16+16,y*16+16))))
 p=PACK/pr;sheet(Image.new('RGBA',(0,0)),Image.new('RGBA',(0,0)),0,0,p,pairs);out=PACK/(pr+'-compiled');out.mkdir(exist_ok=True)
 subprocess.run([str(PT),'compile-primary','-dual-layer','-o',str(out),str(p),str(E/'include/constants/metatile_behaviors.h')],check=True);prim[pr]=(p,out)
 (E/'data/tilesets/primary'/pr/'palettes').mkdir(parents=True,exist_ok=True)
 for file in ['tiles.png','metatiles.bin','metatile_attributes.bin']:shutil.copyfile(out/file,E/'data/tilesets/primary'/pr/file)
 # Porytiles emits only the used palette slots; pad the ordinary source's full editor table.
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';dst=E/'data/tilesets/primary'/pr/'palettes'/f'{i:02}.pal'
  dst.write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
# The laboratory uses its own primary families so its original furniture silhouettes fit without reduction across materials.
if 'gTileset_PalletLabPrimary =' not in (E/'src/data/tilesets/headers.h').read_text():
 sym='PalletLabPrimary';rel='data/tilesets/primary/palletlabprimary'
 with (E/'src/data/tilesets/graphics.h').open('a') as f:
  f.write(f'\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("{rel}/tiles.png", ".4bpp.smol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'    INCGFX_U16("{rel}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n')
 with (E/'src/data/tilesets/metatiles.h').open('a') as f:f.write(f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{rel}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{rel}/metatile_attributes.bin");\n')
 with (E/'src/data/tilesets/headers.h').open('a') as f:f.write(f'\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = FALSE, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')
p=E/'data/layouts/layouts.json';j=json.loads(p.read_text());next(l for l in j['layouts'] if l['name']=='ApocPalletLab_Layout')['primary_tileset']='gTileset_PalletLabPrimary';p.write_text(json.dumps(j,indent=2)+'\n')
report=[]
for name,pr,se,w,h in SPECS:
 bg=Image.open(SRC/('town-ground.png' if name=='ApocPalletTown' else name+'/ground.png'));fg=Image.open(SRC/('town-foreground.png' if name=='ApocPalletTown' else name+'/foreground.png'))
 # A coherent 2x2 repeated forest border outdoors, black void indoors.
 border=[]
 for y in range(2):
  for x in range(2):
   if name=='ApocPalletTown':border.append((bg.crop((x*16,y*16,x*16+16,y*16+16)),fg.crop((x*16,y*16,x*16+16,y*16+16))))
   else:border.append((Image.new('RGBA',(16,16),(0,0,0,255)),Image.new('RGBA',(16,16))))
 folder=PACK/se;n=sheet(bg,fg,w,h,folder,border);out=PACK/(se+'-compiled');out.mkdir(exist_ok=True)
 subprocess.run([str(PT),'compile-secondary','-dual-layer','-o',str(out),str(folder),str(prim[pr][0]),str(E/'include/constants/metatile_behaviors.h')],check=True)
 d=E/'data/tilesets/secondary'/se;(d/'palettes').mkdir(parents=True,exist_ok=True)
 for file in ['tiles.png','metatiles.bin']:shutil.copyfile(out/file,d/file)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(d/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 # Porytiles supplies native layer roles; FRLG's independently stored behaviors/collision/elevation survive.
 ref=json.loads((ART/f'source/{name}-reference.json').read_text())['layout'];original=words(E/ref['blockdata_filepath']);sys.path.insert(0,str(HERE));from native import Bank
 srcpair={'ApocPalletTown':('general_frlg','pallet_town_frlg'),'ApocPalletRedHouse1F':('building_frlg','generic_building_1_frlg'),'ApocPalletRedHouse2F':('building_frlg','generic_building_1_frlg'),'ApocPalletOakHouse':('building_frlg','generic_building_2_frlg'),'ApocPalletLab':('building_frlg','lab_frlg')}[name];native=Bank(E,'primary/'+srcpair[0],'secondary/'+srcpair[1]);attrs=words(out/'metatile_attributes.bin')
 for i,v in enumerate(original):attrs[i]=(attrs[i]&0xf000)|(native.attr(v&1023)&255)
 (d/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
 values=[(v&0xfc00)|(512+i) for i,v in enumerate(original)];layout=E/'data/layouts'/name;(layout/'map.bin').write_bytes(struct.pack('<'+'H'*len(values),*values));(layout/'border.bin').write_bytes(struct.pack('<4H',*[512+w*h+i for i in range(4)]))
 tiles=Image.open(d/'tiles.png').width*Image.open(d/'tiles.png').height//64;assert tiles<=496,(name,tiles)
 report.append(dict(map=name,secondary=se,secondary_tiles=tiles,metatiles=n,layout_cells=w*h,collision_elevation_behavior_preserved=True))
 # Red bedroom has a distinct artwork sheet, with the same shared indoor primary.
 if se=='palletbedroom' and 'gTileset_PalletBedroom =' not in (E/'src/data/tilesets/headers.h').read_text():
  sym='PalletBedroom';rel='data/tilesets/secondary/'+se
  with (E/'src/data/tilesets/graphics.h').open('a') as f:
   f.write(f'\nconst u32 gTilesetTiles_{sym}[] = INCGFX_U32("{rel}/tiles.png", ".4bpp.smol");\nconst u16 gTilesetPalettes_{sym}[][16] = {{\n'+''.join(f'    INCGFX_U16("{rel}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n')
  with (E/'src/data/tilesets/metatiles.h').open('a') as f:f.write(f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{rel}/metatiles.bin");\nconst u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{rel}/metatile_attributes.bin");\n')
  with (E/'src/data/tilesets/headers.h').open('a') as f:f.write(f'\nconst struct Tileset gTileset_{sym} = {{ .isCompressed = TRUE, .isSecondary = TRUE, .tiles = gTilesetTiles_{sym}, .palettes = gTilesetPalettes_{sym}, .metatiles = gMetatiles_{sym}, .metatileAttributes = gMetatileAttributes_{sym}, .callback = NULL }};\n')
  p=E/'data/layouts/layouts.json';j=json.loads(p.read_text());next(l for l in j['layouts'] if l['name']==name+'_Layout')['secondary_tileset']='gTileset_PalletBedroom';p.write_text(json.dumps(j,indent=2)+'\n')
# The FRLG callback's hard-coded tile addresses must never touch the HGSS-compiled tiles.
p=E/'src/data/tilesets/headers.h';s=p.read_text();start=s.index('const struct Tileset gTileset_PalletOutdoor');end=s.index('\n};',start)+3;s=s[:start]+s[start:end].replace('InitTilesetAnim_General_Frlg','NULL')+s[end:];p.write_text(s)
# Remove draft door animations: original FRLG door graphics must not paint over HGSS facades.
p=E/'src/field_door.c';s=p.read_text();s='\n'.join(line for line in s.split('\n') if 'sApocPallet' not in line and 'extern const struct Tileset gTileset_ApocPallet;' not in line);p.write_text(s)
(ART/'evidence/hgss-pack.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
