"""Render one layer of a metatile (bottom 0, top 1) as RGB plus a drawn-pixel mask."""
import numpy as np
def render_layer(ts, mid, layer, bg=True):
    """RGB array + mask of drawn pixels for one metatile layer."""
    out=np.zeros((16,16,3),int); mask=np.zeros((16,16),bool)
    if bg: out[:]=ts.pals[0][0][0]
    entries=ts.blocks[mid>=512][mid-512 if mid>=512 else mid]
    for q in range(4):
        e=entries[layer*4+q]; tid=e&1023; bank=e>>12
        tiles=ts.tiles[tid>=512]; idx=tid-512 if tid>=512 else tid
        if idx>=len(tiles): continue
        colors=ts.pals[bank>=6][bank]
        for y in range(8):
            for x in range(8):
                v=tiles[idx][(7-y if e&2048 else y)*8+(7-x if e&1024 else x)]%16
                if v:
                    out[(q//2)*8+y,(q%2)*8+x]=colors[v]; mask[(q//2)*8+y,(q%2)*8+x]=True
    return out,mask
