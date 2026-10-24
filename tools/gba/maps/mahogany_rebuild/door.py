"""C06 doorway frames made from this build's decoded native palette/tile pair."""
from pathlib import Path
import numpy as np,sys
from PIL import Image
from render_native import render

def main(g):
    im=np.array(render(g,'MahoganyTown'));x,y=24,25
    closed=im[(y-1)*16:(y+1)*16,x*16:(x+1)*16].copy()
    palettes=[]
    for b in range(13):
        kind='primary' if b<6 else 'secondary';p=g/f'data/tilesets/{kind}/mahogany_rebuild/palettes/{b:02}.pal'
        palettes.append(np.array([list(map(int,s.split())) for s in p.read_text().splitlines()[3:19]],int))
    frames=[]
    for n in (1,2,3):
        a=closed.copy();a[16:31,1:15]=[40,48,56];keep=14*(3-n)//3
        if keep:a[16:31,1:1+keep]=closed[16:31,np.linspace(1,14,keep).astype(int)]
        frames.append(a)
    quads=[(0,0),(8,0),(0,8),(8,8),(0,16),(8,16),(0,24),(8,24)];banks=[]
    for qx,qy in quads:
        p=np.concatenate([a[qy:qy+8,qx:qx+8].reshape(-1,3) for a in frames]).astype(int)
        banks.append(int(np.argmin([((p[:,None,:]-pal[1:])**2).sum(-1).min(-1).sum() for pal in palettes])))
    data=bytearray()
    for a in frames:
        for (qx,qy),b in zip(quads,banks):
            p=a[qy:qy+8,qx:qx+8].reshape(-1,3).astype(int);v=((p[:,None,:]-palettes[b][1:])**2).sum(-1).argmin(-1)+1
            data.extend(int(v[i])|(int(v[i+1])<<4) for i in range(0,64,2))
    out=g/'graphics/door_anims/mahogany_rebuild/center.4bpp';out.parent.mkdir(exist_ok=True,parents=True);out.write_bytes(data)
    grid=np.frombuffer((g/'data/layouts/MahoganyTown/map.bin').read_bytes(),'<u2').reshape(36,36);mid=int(grid[y,x]&1023)
    decl='extern const struct Tileset gTileset_MahoganyRebuild;\nstatic const u8 sMahoganyRebuildCenterDoor[] = INCBIN_U8("graphics/door_anims/mahogany_rebuild/center.4bpp");\nstatic const u8 sMahoganyRebuildCenterDoorPal[8] = {'+','.join(map(str,banks))+'};\n'
    line=f'    {{.metatileNum={mid}, .tileset=&gTileset_MahoganyRebuild, .sound=DOOR_SOUND_SLIDING, .size=DOOR_SIZE_1x2, .tiles=sMahoganyRebuildCenterDoor, .palettes=sMahoganyRebuildCenterDoorPal}},\n'
    p=g/'src/field_door.c';s=p.read_text();marker='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{\n'
    if 'sMahoganyRebuildCenterDoor[]' in s:raise SystemExit('Door is already installed; edit native source directly.')
    p.write_text(s.replace(marker,decl+marker+line))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
