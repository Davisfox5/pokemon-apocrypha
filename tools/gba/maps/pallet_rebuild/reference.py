"""Pin FRLG geography before authoring art; do not infer materials from collision.

The rejected Pallet conversion is not an input. Read-only native decoders are reused.
One north and two south apron rows complete the taller shared tree silhouettes.
"""
from pathlib import Path
import hashlib, json, shutil, sys
import numpy as np
from PIL import Image
from native import Bank, words, numbered

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / 'gba/art/pallet-town-rebuild'
SOURCE, EV = ART/'source', ART/'evidence'
SPECS = [
    ('ApocPalletTown', 'PalletTown_Frlg', 'general_frlg', 'pallet_town_frlg', 24, 20),
    ('ApocPalletRedHouse1F', 'PalletTown_PlayersHouse_1F_Frlg', 'building_frlg', 'generic_building_1_frlg', 13, 10),
    ('ApocPalletRedHouse2F', 'PalletTown_PlayersHouse_2F_Frlg', 'building_frlg', 'generic_building_1_frlg', 12, 9),
    ('ApocPalletOakHouse', 'PalletTown_RivalsHouse_Frlg', 'building_frlg', 'generic_building_2_frlg', 13, 10),
    ('ApocPalletLab', 'PalletTown_ProfessorOaksLab_Frlg', 'building_frlg', 'lab_frlg', 13, 14),
]

def main(engine):
    layouts=json.loads((engine/'data/layouts/layouts.json').read_text())['layouts']
    # Select by the original map metadata, not any previous author's layout/ledger.
    records=[]
    for name, donor, pr, se, w, h in SPECS:
        meta=json.loads((engine/f'data/maps/{donor}/map.json').read_text())
        layout=next(l for l in layouts if l['id']==meta['layout'])
        assert (layout['width'],layout['height'])==(w,h)
        bank=Bank(engine,'primary/'+pr,'secondary/'+se)
        grid=words(engine/layout['blockdata_filepath'])
        image=bank.map(grid,w)
        d=SOURCE/name; d.mkdir(parents=True,exist_ok=True)
        image.save(d/'frlg.png'); numbered(image).save(EV/f'{name}-original-grid.png')
        mids=sorted({v&1023 for v in grid})
        atlas=Image.new('RGB',(16*12,32*((len(mids)+11)//12)))
        from PIL import ImageDraw
        draw=ImageDraw.Draw(atlas)
        for i,mid in enumerate(mids):
            x,y=(i%12)*16,(i//12)*32
            atlas.paste(bank.render(mid),(x,y));draw.text((x,y+17),f'{mid:03x}',fill='white')
        atlas.resize((atlas.width*3,atlas.height*3),Image.Resampling.NEAREST).save(EV/f'{name}-original-materials.png')
        arr=np.array(image);cells=[]
        for i,v in enumerate(grid):
            attr=bank.attr(v&1023)
            cells.append(dict(x=i%w,y=i//w,metatile=v&1023,collision=(v>>10)&3,elevation=v>>12,behavior=attr&511))
        (d/'traversal.json').write_text(json.dumps(cells,indent=1)+'\n')
        # This is the editable reference, independent of the native authoring labels.
        np.savez_compressed(d/'decoded.npz',pixels=arr,entries=np.array(grid,dtype=np.uint16),attributes=np.array([bank.attr(v&1023) for v in grid],np.uint32))
        rec=dict(map=name,donor=donor,layout=layout,reference='Decoded original FRLG data, not a screenshot trace',scale=16,
                 native_offset=[0,1] if name=='ApocPalletTown' else [0,0],crop=None,
                 expansion='one north/two south canopy apron rows' if name=='ApocPalletTown' else None)
        (d/'reference.json').write_text(json.dumps(rec,indent=2)+'\n');records.append(rec)
    identity=dict(engine_base='2722eaf7601ec02dc5a684fa8cdef9206c0dc377',
                  hgss='9d8b7591f09b65804da2fb2dfd56f320633e0d36',maps=records)
    (SOURCE/'reference.json').write_text(json.dumps(identity,indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
