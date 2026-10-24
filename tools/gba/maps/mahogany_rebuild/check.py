"""Check original/native cell contracts and actual compiled artwork before review."""
from pathlib import Path
from collections import deque
import hashlib,json,subprocess,sys
import numpy as np
from PIL import Image,ImageDraw
from build import ART,SRC,EV,N,O
from render_native import render

def main(g):
    img=np.array(render(g,'MahoganyTown'));Image.fromarray(img).save(EV/'native.png')
    grid=np.frombuffer((g/'data/layouts/MahoganyTown/map.bin').read_bytes(),'<u2').reshape(N,N)
    attrs=[np.frombuffer((g/f'data/tilesets/{k}/mahogany_rebuild/metatile_attributes.bin').read_bytes(),'<u2') for k in ['primary','secondary']]
    atlases=[[np.array(Image.open(SRC/k/(n+'.png')).convert('RGBA')) for n in ('bottom','middle','top')] for k in ('primary','secondary')]
    expected_pixels=np.zeros_like(img)
    art=np.load(SRC/'layers.npz');ref=np.load(ART/'reference/topdown.npz');beh=np.zeros((N,N),int);layer=np.zeros((N,N),int)
    owner=art['owner'];behaviors=art['behavior'];ledger=[];changes=[]
    for y,x in np.ndindex(N,N):
        m=int(grid[y,x]&1023);a=int(attrs[m>=512][m%512]);beh[y,x]=a&255;layer[y,x]=(a>>12)&3
        assert beh[y,x]==int(behaviors[y,x]),(x,y,'behavior')
        actual=int(grid[y,x]>>10&3);role='apron';original=None
        if O<=x<O+32 and O<=y<O+32:
            ox,oy=x-O,y-O;q=ref['material'][oy*16:(oy+1)*16,ox*16:(ox+1)*16];u,c=np.unique(q,return_counts=True);v=int(u[np.argmax(c)]);role=str(ref['names'][v]) if v>=0 else 'occluded-original-ground';original=int(ref['collision'][oy,ox]&128)>0
            if actual!=int(original):changes.append([ox,oy,actual])
        # Independently reconstruct the editable layer atlas at this actual map
        # entry, then compare RGB5 pixels with the engine tiles/palettes decode.
        tile=np.zeros((16,16,3),np.uint8);i=m%512;sx=i%8*16;sy=i//8*16
        for atlas in atlases[m>=512]:
            patch=atlas[sy:sy+16,sx:sx+16];mask=patch[...,3]>0;tile[mask]=patch[mask,:3]
        expected_pixels[y*16:(y+1)*16,x*16:(x+1)*16]=tile
        ledger.append(dict(native=[x,y],original=[x-O,y-O] if original is not None else None,original_material=role,native_metatile=m,collision=actual,elevation=int(grid[y,x]>>12),behavior=int(beh[y,x]),layer=int(layer[y,x]),foreground_features=sorted(set(owner[y*16:(y+1)*16,x*16:(x+1)*16].ravel())-{''}),decoded_rgb5_sha256=hashlib.sha256((img[y*16:(y+1)*16,x*16:(x+1)*16]>>3).tobytes()).hexdigest()))
    pixel_mismatches=int(((expected_pixels>>3)!=(img>>3)).any(-1).sum())
    assert pixel_mismatches==0,('Editable source vs decoded native',pixel_mismatches)
    expected={(x,y) for x in range(20,25) for y in (18,19)}|{(12,5),(13,5),(22,23)}
    assert {(x,y) for x,y,c in changes}==expected,changes
    c=np.array(Image.open(SRC/'approved-center.png').convert('RGBA'));mask=c[...,3]>0
    assert np.array_equal((img[21*16:26*16,22*16:27*16,:3]>>3)[mask],(c[...,:3]>>3)[mask]),'C06 changed'
    plan=json.loads((SRC/'plan.json').read_text());roots=[]
    for x,y in plan['trees']:roots += [(x+dx,y+dy) for dx in (0,1) for dy in (0,1)]
    assert len(roots)==len(set(roots)),'Tree root footprints overlap'
    highest=0;counts=[]
    for k in ['primary','secondary']:
        p=g/f'data/tilesets/{k}/mahogany_rebuild';v=np.frombuffer((p/'metatiles.bin').read_bytes(),'<u2');highest=max(highest,int((v&1023).max()));counts.append(len(v)//8)
    assert highest<1008 and max(counts)<=512
    old=json.loads(subprocess.check_output(['git','-C',str(g),'show','origin/apocrypha:data/maps/map_groups.json']));new=json.loads((g/'data/maps/map_groups.json').read_text())
    for k,v in old.items():
        if isinstance(v,list):assert new[k][:len(v)]==v
    (SRC/'material-traversal-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    review=Image.fromarray(img).resize((N*32,N*32),Image.Resampling.NEAREST);d=ImageDraw.Draw(review)
    for i in range(N):d.line((i*32,0,i*32,N*32),fill=(60,65,65));d.line((0,i*32,N*32,i*32),fill=(60,65,65));d.text((i*32+2,2),str(i),fill='white',stroke_width=1,stroke_fill='black');d.text((2,i*32+2),str(i),fill='white',stroke_width=1,stroke_fill='black')
    review.save(EV/'native-grid.png')
    result=dict(native_cells=N*N,original_cells=1024,original_offset=[O,O],tree_count=len(plan['trees']),root_footprints_disjoint=True,canonical_center_exact=True,source_vs_native_rgb5_pixel_mismatches=pixel_mismatches,highest_tile=highest,tile_limit_excluding_door_scratch=1008,metatiles=counts,collision_adaptations=changes,existing_ids_preserved=True)
    (EV/'native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
