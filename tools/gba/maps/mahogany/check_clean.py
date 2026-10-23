"""Audit actual native cells, local visual changes, IDs, budgets and warp contracts."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import check_convert as C
import clean_native as N

ROOT=HERE.parents[3];ART=ROOT/'gba/art/mahogany-town';OUT=ART/'evidence/clean'
DOORS={(16,14):105,(25,14):105,(11,23):105,(12,5):96,(13,5):96}

def main(g):
    img,beh,layer,coll,elev,mid,_,sm=C.decode(g)
    before=np.array(Image.open(ART/'evidence/convert/native.png').convert('RGB'))
    owners=np.load(ART/'source/convert/layers.npz',allow_pickle=True)['owner']
    changed=(img!=before).any(-1)
    assert not (changed&~np.isin(owners,N.FEATURES)).any()
    assert not (changed&(owners=='pokemon_center')).any()
    ledger=json.loads((ART/'source/convert/traversal.json').read_text())
    materials=json.loads((ART/'source/elements/ledger.json').read_text())
    current=[]
    for c in ledger:
        c=dict(c);x,y=c['x'],c['y'];p=(x,y)
        if p in DOORS:
            assert (beh[y,x],coll[y,x],elev[y,x])==(DOORS[p],0,3)
            c.update(behavior_id=DOORS[p],behavior='MB_ANIMATED_DOOR' if DOORS[p]==105 else 'MB_NON_ANIMATED_DOOR',collision=0,elevation=3,foot='door',adaptation='Original HGSS visible entrance is now wired to a visitable native room; gate behavior translated to Emerald')
        else:
            assert (beh[y,x],coll[y,x],elev[y,x])==(c['behavior_id'],c['collision'],c['elevation']),(x,y)
        assert layer[y,x]==(0 if c['layer']=='normal' else 1),(x,y,'layer')
        c['original_material']=materials['cells'][y][x]
        c['native_metatile']=int(mid[y,x]);current.append(c)
    (ART/'source/clean-traversal.json').write_text(json.dumps(current,indent=2)+'\n')
    foot={(c['x'],c['y']):c['foot'] for c in current};seen=C.reach(foot,False)
    open_cells={p for p,v in foot.items() if v in ('open','door')}
    assert open_cells-seen=={(8,7),(8,8)},open_cells-seen
    for p in DOORS:assert p in seen,p
    # Decode matches the current authoring preview, independent of the old draft.
    assert np.array_equal(img,np.array(Image.open(OUT/'native.png').convert('RGB')))
    groups=json.loads((g/'data/maps/map_groups.json').read_text())
    old=json.loads(subprocess.check_output(['git','-C',str(g),'show',N.BASE+':data/maps/map_groups.json']))
    for k,v in old.items():
        if isinstance(v,list):assert groups[k][:len(v)]==v,k
    native_maps={}
    for name in groups['gMapGroup_Cherrygrove']:
        m=json.loads((g/'data/maps'/name/'map.json').read_text());native_maps[m['id']]=m
    audited_warps=[]
    for mid_,m in native_maps.items():
        if not m['name'].startswith('Mahogany'):continue
        for w in m['warp_events']:
            target=native_maps[w['dest_map']];idx=int(w['dest_warp_id']);assert 0<=idx<len(target['warp_events']),(mid_,w)
            audited_warps.append([m['name'],w['x'],w['y'],target['name'],idx])
    dirs,pats,metas,pals,grid=N.read(g)
    max_tile=max((e&1023) for ents,attr in metas.values() for e in ents)
    assert max_tile<1008 and sm<=512
    for d in dirs:
        for p in (d/'palettes').glob('*.pal'):
            prior=subprocess.check_output(['git','-C',str(g),'show',N.BASE+':'+str(p.relative_to(g))]);assert p.read_text().splitlines()==prior.decode().splitlines(),p
    # All seven map views are exported from actual native source for review.
    from render_native import render
    for name in [m['name'] for m in native_maps.values() if m['name'].startswith('Mahogany')]:render(g,name).save(OUT/(name+'.png'))
    for title,im in [('native',Image.fromarray(img)),('reference',Image.open(ART/'source/hgss/hgss-reference-true-heights.png').convert('RGB'))]:
        im=im.resize((1024,1024),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
        for i in range(32):
            d.line((i*32,0,i*32,1024),fill=(60,60,70));d.line((0,i*32,1024,i*32),fill=(60,60,70));d.text((i*32+2,2),str(i),fill='white',stroke_width=1,stroke_fill='black');d.text((2,i*32+2),str(i),fill='white',stroke_width=1,stroke_fill='black')
        im.save(OUT/(title+'-grid.png'))
    ref=Image.open(ART/'source/hgss/hgss-reference-true-heights.png').convert('RGB')
    pair=Image.new('RGB',(1040,540),(28,34,38));pair.paste(ref,(0,28));pair.paste(Image.fromarray(img),(528,28));d=ImageDraw.Draw(pair);d.text((6,8),'Original HGSS data / 16 px per cell',fill='white');d.text((534,8),'Clean Gen 3 / actual native tiles',fill='white');pair.save(OUT/'original-native.png')
    result=dict(base_engine=N.BASE,cells_audited=1024,material_grid_preserved=True,behavior_collision_elevation_layer_checked=True,
        traversal_changes=[list(p) for p in DOORS],unchanged_cells=1019,reachable_foot_cells=len(seen),open_cells=len(open_cells),
        unreachable_original_enclosed_cells=sorted(open_cells-seen),terrain_pixels_changed=0,center_pixels_changed=0,
        changed_architecture_pixels=int(changed.sum()),palettes_preserved=True,existing_map_ids_preserved=True,
        highest_native_tile=max_tile,tile_capacity_excluding_door_scratch=1008,secondary_metatiles=sm,warp_references=audited_warps)
    (OUT/'native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='warp_references'}))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
