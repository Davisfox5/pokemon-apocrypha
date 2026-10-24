"""Read original HGSS binary geography; write registered reference and material data."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
import hgss_reference as R
from build import ART

def main(phg):
    dest=ART/'reference';dest.mkdir(exist_ok=True,parents=True)
    land,tex,models,chunks,meta=R.load(phg);ch=R.hgss_map.MapChunk.parse(land[85]);model=R.mdlview.Model(ch.model)
    cv=R.Canvas(512,512);R.draw_model(cv,model,tex,lambda x,y,z:(x+16,y,z+16),-1,None,flat=True)
    np.savez_compressed(dest/'topdown.npz',height=cv.height,material=cv.mat,names=np.array(R.MATERIAL_NAMES),rgb=cv.rgb.astype('uint8'),types=np.array(ch.types).reshape(32,32),collision=np.array(ch.collisions).reshape(32,32))
    (dest/'textures').mkdir(exist_ok=True)
    for mid,name in model.mat_tex.items():
        m=R.Material(model,mid,tex)
        if m.tex is not None:Image.fromarray(m.tex).save(dest/'textures'/(name+'.png'))
    R.SNAP=False;r=R.render(phg);r['full'].save(dest/'original-hgss.png');R.SNAP=True
    source={p:hashlib.sha256((phg/p).read_bytes()).hexdigest() for p in ['files/a/0/6/5','files/a/0/4/2','files/a/0/4/4','files/a/0/4/0','files/fielddata/mapmatrix/map_matrix/map_matrix_0000_EVERYWHERE.bin']}
    (dest/'provenance.json').write_text(json.dumps(dict(repository='Davisfox5/pokeheartgold',revision='9d8b7591f09b65804da2fb2dfd56f320633e0d36',land_data_chunk=85,area_bank=8,original_cells=[32,32],native_cell_px=16,native_offset=[2,2],files=source,buildings=r['buildings'],metadata=meta),indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
