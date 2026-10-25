"""Exact Porytiles conversion of the fresh editable receiving layers.

Only Pallet's private native banks/layouts are replaced, by explicit owner restart.
Deduplication requires identical pixels, layer role AND behavior, never RGB proximity.
"""
from pathlib import Path
import hashlib,json,math,shutil,struct,subprocess,sys
from PIL import Image
from native import words
ROOT=Path(__file__).resolve().parents[4];ART=ROOT/'gba/art/pallet-town-rebuild';S=ART/'source';PACK=S/'porytiles'
E=Path(sys.argv[1]).resolve();PT=Path(sys.argv[2]).resolve()
SPECS=[('ApocPalletTown','palletoutdoor','pallettown',24,23),('ApocPalletRedHouse1F','palletindoor','palletredhouse',13,10),
       ('ApocPalletRedHouse2F','palletbedroomprimary','palletbedroom',12,9),('ApocPalletOakHouse','palletoakprimary','palletoakhouse',13,10),
       ('ApocPalletLab','palletlabprimary','palletlab',13,14)]
PACK.mkdir(exist_ok=True)

def sheet(pairs,path,outdoor):
    path.mkdir(exist_ok=True);size=(128,math.ceil(len(pairs)/8)*16)
    layers=[Image.new('RGBA',size) for _ in range(3)]
    for i,(bg,fg) in enumerate(pairs):
        x,y=i%8*16,i//8*16;layers[1 if outdoor else 0].paste(bg,(x,y));layers[2 if outdoor else 1].paste(fg,(x,y))
    for n,im in zip(['bottom','middle','top'],layers):im.save(path/(n+'.png'))
def compile(mode,path,primary=None):
    out=path.with_name(path.name+'-compiled');out.mkdir(exist_ok=True)
    cmd=[str(PT),mode,'-dual-layer','-o',str(out),str(path)]
    if primary:cmd.append(str(primary))
    cmd.append(str(E/'include/constants/metatile_behaviors.h'))
    subprocess.run(cmd,check=True);return out
def install(out,folder):
    d=E/'data/tilesets'/folder;(d/'palettes').mkdir(parents=True,exist_ok=True)
    for f in ['tiles.png','metatiles.bin','metatile_attributes.bin']:shutil.copyfile(out/f,d/f)
    for i in range(16):
        p=out/'palettes'/f'{i:02}.pal'
        (d/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
def cell(im,x,y):return im.crop((x*16,y*16,x*16+16,y*16+16))

def palette_plan(names):
    sets=set()
    for name in names:
        for layer in ['ground','foreground']:
            im=Image.open(S/name/(layer+'.png')).convert('RGBA')
            for y in range(0,im.height,8):
                for x in range(0,im.width,8):
                    cs=frozenset(tuple(c[:3]) for c in im.crop((x,y,x+8,y+8)).getdata() if c[3])
                    if cs:sets.add(cs)
    maximal=[s for s in sets if not any(s<t for t in sets)]
    pals=[]
    for cs in sorted(maximal,key=lambda s:(-len(s),sorted(s))):
        fits=[(len(p|cs),i) for i,p in enumerate(pals) if len(p|cs)<=15]
        if fits:pals[min(fits)[1]]|=cs
        else:pals.append(set(cs))
    assert len(pals)<=13,('exact palette family budget',names,len(pals))
    return pals
def overrides(path,pals,primary):
    d=path/'palette-overrides';d.mkdir(exist_ok=True)
    for p in d.glob('*.pal'):p.unlink()
    for i in range(6) if primary else range(6,len(pals)):
        colors=sorted(pals[i]) if i<len(pals) else []
        lines=['-']+['%d %d %d'%c for c in colors]+['-']*(15-len(colors))
        (d/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')

plans={p:palette_plan([n for n,pp,ss,w,h in SPECS if pp==p]) for p in {p for n,p,s,w,h in SPECS}}

primary={};report=[]
layouts_path=E/'data/layouts/layouts.json';layouts=json.loads(layouts_path.read_text())
for name,pr,se,w,h in SPECS:
    outdoor=name=='ApocPalletTown';g=Image.open(S/name/'ground.png');f=Image.open(S/name/'foreground.png')
    if pr not in primary:
        samples=[(x,y) for y in range(3) for x in range(2)]+[(10,10),(11,10),(10,11),(11,11),(8,19),(9,19)] if outdoor else [(2,7),(3,7),(2,6),(3,6),(6,0),(7,0),(6,1),(7,1)]
        if not outdoor:samples=samples[:4]
        pairs=[(cell(g,x,y),cell(f,x,y) if outdoor else Image.new('RGBA',(16,16))) for x,y in samples]
        if not outdoor:
            needed=set()
            for bg,fg in pairs:
                for im in [bg,fg]:
                    for y in (0,8):
                        for x in (0,8):
                            cs={tuple(c[:3]) for c in im.crop((x,y,x+8,y+8)).getdata() if c[3]}
                            if cs:needed.add(next(i for i,p in enumerate(plans[pr]) if cs<=p))
            assert len(needed)<=6
            plans[pr]=[plans[pr][i] for i in sorted(needed)]+[p for i,p in enumerate(plans[pr]) if i not in needed]
        primary[pr]=PACK/pr;sheet(pairs,primary[pr],outdoor);overrides(primary[pr],plans[pr],True);install(compile('compile-primary',primary[pr]),'primary/'+pr)
    reference=json.loads((S/name/'reference.json').read_text());old=words(E/reference['layout']['blockdata_filepath'])
    original_attrs=__import__('numpy').load(S/name/'decoded.npz')['attributes']
    if outdoor:
        original=[old[x+min(max(y-1,0),19)*24] for y in range(h) for x in range(w)]
        attrs=[int(original_attrs[x+min(max(y-1,0),19)*24]) for y in range(h) for x in range(w)]
    else:original=old;attrs=list(map(int,original_attrs))
    # The palette packing sees every unique cell; behavior-aware deduplication
    # preserves e.g. stair direction even if two cells look the same.
    pairs=[];unique={};indices=[];behaviors=[]
    for i,v in enumerate(original):
        bg,fg=cell(g,i%w,i//w),cell(f,i%w,i//w);behavior=attrs[i]&255
        key=(bg.tobytes(),fg.tobytes(),behavior)
        if key not in unique:
            unique[key]=len(pairs);pairs.append((bg,fg));behaviors.append(behavior)
        indices.append(unique[key])
    borderidx=[]
    for y in range(2):
        for x in range(2):
            pair=(cell(g,x,y+1),cell(f,x,y+1)) if outdoor else (Image.new('RGBA',(16,16),(0,0,0,255)),Image.new('RGBA',(16,16)))
            borderidx.append(len(pairs));pairs.append(pair);behaviors.append(0)
    assert len(pairs)<=512,(name,len(pairs))
    folder=PACK/se;sheet(pairs,folder,outdoor);overrides(folder,plans[pr],False);out=compile('compile-secondary',folder,primary[pr])
    at=words(out/'metatile_attributes.bin')
    for i,behavior in enumerate(behaviors):at[i]=(at[i]&0xf000)|behavior
    (out/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at),*at));install(out,'secondary/'+se)
    grid=[(v&0xfc00)|(512+j) for v,j in zip(original,indices)]
    d=E/'data/layouts'/name
    (d/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(d/'border.bin').write_bytes(struct.pack('<4H',*[512+j for j in borderidx]))
    layout=next(l for l in layouts['layouts'] if l['name']==name+'_Layout');layout['width']=w;layout['height']=h
    symbol={'palletbedroomprimary':'PalletBedroomPrimary','palletoakprimary':'PalletOakPrimary'}.get(pr)
    if symbol:
        layout['primary_tileset']='gTileset_'+symbol
        if 'gTileset_'+symbol+' =' not in (E/'src/data/tilesets/headers.h').read_text():
            rel='data/tilesets/primary/'+pr
            with (E/'src/data/tilesets/graphics.h').open('a') as stream:
                stream.write(f'\nconst u32 gTilesetTiles_{symbol}[] = INCGFX_U32("{rel}/tiles.png", ".4bpp.smol");\nconst u16 gTilesetPalettes_{symbol}[][16] = {{\n'+''.join(f'    INCGFX_U16("{rel}/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n')
            with (E/'src/data/tilesets/metatiles.h').open('a') as stream:
                stream.write(f'\nconst u16 gMetatiles_{symbol}[] = INCBIN_U16("{rel}/metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{rel}/metatile_attributes.bin");\n')
            with (E/'src/data/tilesets/headers.h').open('a') as stream:
                stream.write(f'\nconst struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary=FALSE, .tiles=gTilesetTiles_{symbol}, .palettes=gTilesetPalettes_{symbol}, .metatiles=gMetatiles_{symbol}, .metatileAttributes=gMetatileAttributes_{symbol}, .callback=NULL }};\n')
    tiles=Image.open(out/'tiles.png');count=tiles.width*tiles.height//64
    assert count<=496,(name,count)
    (S/name/'native-cell-indices.json').write_text(json.dumps(dict(width=w,height=h,indices=indices,original_entries=original),indent=1)+'\n')
    report.append(dict(map=name,width=w,height=h,cells=w*h,unique_native_metatiles=len(pairs),secondary_tiles=count,exact_color_conversion=True))
layouts_path.write_text(json.dumps(layouts,indent=2)+'\n')
# Translate only the exterior events once, preserving event order and warp IDs.
p=E/'data/maps/ApocPalletTown/map.json';m=json.loads(p.read_text())
if m['warp_events'][0]['y']==7:
    for key in ['object_events','warp_events','coord_events','bg_events']:
        for ev in m[key]:ev['y']+=1
    p.write_text(json.dumps(m,indent=2)+'\n')
assert m['warp_events'][0]['y']==8
(ART/'evidence/pack.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
