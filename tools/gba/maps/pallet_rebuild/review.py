"""Independent native/editor/preservation audit and readable original/before/after sheets.

Pixel equality establishes conversion accuracy only. Material review and declared
model adaptations remain a separate record; no blanket visual-match percentage.
"""
from pathlib import Path
import csv,hashlib,json,struct,subprocess,sys
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from native import Bank,words,numbered
from materials import material
ROOT=Path(__file__).resolve().parents[4];A=ROOT/'gba/art/pallet-town-rebuild';S=A/'source';V=A/'evidence';E=Path(sys.argv[1])
SPECS=[('ApocPalletTown','palletoutdoor','pallettown'),('ApocPalletRedHouse1F','palletindoor','palletredhouse'),
       ('ApocPalletRedHouse2F','palletbedroomprimary','palletbedroom'),('ApocPalletOakHouse','palletoakprimary','palletoakhouse'),
       ('ApocPalletLab','palletlabprimary','palletlab')]
layouts=json.loads((E/'data/layouts/layouts.json').read_text())['layouts'];features=json.loads((S/'foreground-material-grid.json').read_text())
results=[];manifest={}

def panel(images,labels,path,scale=2):
    width=sum(im.width for im in images)*scale+16*(len(images)-1);height=max(im.height for im in images)*scale+28
    out=Image.new('RGB',(width,height),'#202830');draw=ImageDraw.Draw(out);x=0
    for im,label in zip(images,labels):
        draw.text((x+4,7),label,fill='white');out.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(x,28));x+=im.width*scale+16
    out.save(path)

for name,pr,se in SPECS:
    layout=next(l for l in layouts if l['name']==name+'_Layout');w,h=layout['width'],layout['height'];outdoor=name=='ApocPalletTown'
    bank=Bank(E,'primary/'+pr,'secondary/'+se,False);grid=words(E/layout['blockdata_filepath']);ref=np.load(S/name/'decoded.npz')
    original=json.loads((S/name/'reference.json').read_text());ow,oh=original['layout']['width'],original['layout']['height']
    after=bank.map(grid,w);expected=Image.open(S/name/'ground.png').convert('RGBA');expected.alpha_composite(Image.open(S/name/'foreground.png').convert('RGBA'))
    assert np.array_equal(np.array(after)>>3,np.array(expected)[...,:3]>>3),(name,'native converted-pixel mismatch')
    editor=Image.open(V/'porymap'/(name+'.png')).convert('RGB');assert not ImageChops.difference(editor,after).getbbox(),(name,'Porymap mismatch')
    before=Image.open(S/name/'frlg.png').convert('RGB');aligned=Image.new('RGB',after.size,'#586068');aligned.paste(before,(0,16 if outdoor else 0))
    after.save(V/(name+'-native.png'));numbered(after).save(V/(name+'-native-grid.png'));numbered(aligned).save(V/(name+'-registered-reference-grid.png'))
    panel([aligned,after],['ORIGINAL FRLG / gray = apron','ACTUAL NATIVE HGSS CONVERSION'],V/(name+'-comparison.png'))
    rejected=Image.open(ROOT/'gba/art/pallet-town/evidence'/(name+'-native.png')).convert('RGB')
    panel([rejected,after],['REJECTED VERSION','FRESH REBUILD / ACTUAL NATIVE'],V/(name+'-before-after.png'))
    rows=[];traversal=[];core_count=0
    for i,v in enumerate(grid):
        x,y=i%w,i//w;oy=y-1 if outdoor else y;inside=0<=oy<oh;ri=(min(max(oy,0),oh-1)*ow+x)
        old=int(ref['entries'][ri]);attr=bank.attr(v&1023);refattr=int(ref['attributes'][ri]);assert v&0xfc00==old&0xfc00
        assert attr&255==refattr&511
        mid=old&1023;refmat=material(name,x,min(max(oy,0),oh-1),mid)
        origpatch=ref['pixels'][min(max(oy,0),oh-1)*16:(min(max(oy,0),oh-1)+1)*16,x*16:(x+1)*16]
        if not origpatch.any():refmat='void'
        feature=features.get(name,{}).get(f'{x},{y}',[])
        if not outdoor and y<2:feature=['HGSS-wall-cap-and-face']+feature
        ground='HGSS wood floor / original void' if not outdoor else 'shared lawn / explicit light-lawn mask'
        if outdoor and refmat in ('water','shore_lip_and_water'):ground='HGSS water / rock shore lip'
        inferred=bool(outdoor and refmat.startswith(('home_','lab_','tree_')))
        adaptation=[]
        if not inside:adaptation.append('canopy apron; original edge traversal extended')
        if outdoor and y in (3,4) and (5<=x<=9 or 14<=x<=18):adaptation.append('complete HGSS roof above original building footprint')
        if inferred:adaptation.append('hidden receiving lawn inferred from surroundings')
        if not outdoor and refmat=='telephone':adaptation.append('HGSS refrigerator occupies original telephone footprint')
        if name=='ApocPalletLab' and refmat=='laboratory_tile_floor':adaptation.append('HGSS lab wood floor replaces FRLG tile floor')
        rows.append(dict(x=x,y=y,reference_x=x if inside else '',reference_y=oy if inside else '',reference_material=refmat if inside else 'outside reference',
                         native_ground=ground,native_visible_features=';'.join(feature),reference_metatile=f'{mid:03x}' if inside else '',native_metatile=f'{v&1023:03x}',
                         native_layer=attr>>12,native_entries=' '.join(f'{e:04x}' for e in bank.entries(v&1023)),
                         hidden_ground_interpretation=inferred,adaptation=';'.join(adaptation)))
        traversal.append(dict(x=x,y=y,reference_core=inside,collision=(v>>10)&3,elevation=v>>12,behavior=attr&255,reference_collision=(old>>10)&3,
                              reference_elevation=old>>12,reference_behavior=refattr&511))
        core_count+=inside
    with (S/name/'material-grid.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys(),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    (S/name/'native-traversal.json').write_text(json.dumps(traversal,indent=1)+'\n')
    for p in [E/layout['blockdata_filepath'],E/layout['border_filepath']]:manifest[str(p.relative_to(E))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for d in [E/'data/tilesets/primary'/pr,E/'data/tilesets/secondary'/se]:
        for p in d.rglob('*'):
            if p.is_file() and p.suffix in ('.png','.pal','.bin','.inc'):manifest[str(p.relative_to(E))]=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n') if p.suffix=='.pal' else p.read_bytes()).hexdigest()
    results.append(dict(map=name,native_cells=len(grid),registered_reference_cells=core_count,added_apron_cells=len(grid)-core_count,
                        source_rgb5_pixel_differences=0,porymap_pixel_differences=0,reference_core_collision_elevation_behavior_equal=True,
                        material_grid='source/'+name+'/material-grid.csv',visual_acceptance='owner review pending; pixel parity is not material/visual acceptance'))

base='2722eaf7601ec02dc5a684fa8cdef9206c0dc377'
for file,key in [('data/maps/map_groups.json',None),('data/layouts/layouts.json','layouts')]:
    old=json.loads(subprocess.check_output(['git','-C',str(E),'show',base+':'+file]));new=json.loads((E/file).read_text())
    if key:assert old[key]==new[key][:len(old[key])]
    else:
        for k,v in old.items():assert (new[k][:len(v)] if isinstance(v,list) else new[k])==v
(V/'native-audit.json').write_text(json.dumps(results,indent=2)+'\n');(V/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Checked',sum(r['native_cells'] for r in results),'native cells;',sum(r['registered_reference_cells'] for r in results),'FRLG reference cells. Material adaptations recorded separately.')
