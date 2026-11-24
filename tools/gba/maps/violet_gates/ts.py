import struct,numpy as np
from pathlib import Path
from PIL import Image
class TS:
    def __init__(s,root):
        T=Path(root)/'data/tilesets'; P=['primary','secondary']
        s.mt=[list(struct.iter_unpack('<8H',(T/p/'violet_city/metatiles.bin').read_bytes())) for p in P]
        s.attr=[list(struct.unpack('<%dH'%((T/p/'violet_city/metatile_attributes.bin').stat().st_size//2),(T/p/'violet_city/metatile_attributes.bin').read_bytes())) for p in P]
        s.sheets=[np.array(Image.open(T/p/'violet_city/tiles.png'))%16 for p in P]
        s.pals={}
        for p,r in [('primary',range(6)),('secondary',range(6,13))]:
            for n in r:
                L=list(map(int,(T/p/'violet_city/palettes'/f'{n:02}.pal').read_text().split()[3:]))
                s.pals[n]=np.array(L).reshape(16,3)
        s.w=np.frombuffer((Path(root)/'data/layouts/VioletCity/map.bin').read_bytes(),'<u2').reshape(72,80).copy()
    def ents(s,m): m&=1023; return s.mt[0][m] if m<512 else s.mt[1][m-512]
    def tile(s,t):
        sh=s.sheets[t>=512]; i=t-512 if t>=512 else t
        if (i//16)*8>=sh.shape[0]: return np.zeros((8,8),np.uint8)
        return sh[(i//16)*8:(i//16)*8+8,(i%16)*8:(i%16)*8+8]
    def idx(s,e):
        t=s.tile(e&1023)
        if e&1024: t=t[:,::-1]
        if e&2048: t=t[::-1]
        return t
    def rgba(s,e,lower):
        i=s.idx(e); c=s.pals[e>>12][i]
        if lower: c=c.copy(); c[i==0]=s.pals[0][0]
        a=np.ones((8,8),bool) if lower else (i!=0)
        out=np.zeros((8,8,4),int); out[...,:3]=c; out[...,3]=a*255; out[~a]=0
        return out
