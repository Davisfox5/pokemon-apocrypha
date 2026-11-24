import pickle,struct,sys,numpy as np
from pathlib import Path
from PIL import Image
ENG=Path(sys.argv[1])
mt,attr,sheets,pals,w=pickle.load(open(''+sys.argv[2]+'','rb'))
T=ENG/'data/tilesets'
for part,p in enumerate(['primary','secondary']):
    d=T/p/'violet_city'
    (d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*E) for E in mt[part]))
    (d/'metatile_attributes.bin').write_bytes(struct.pack('<%dH'%len(attr[part]),*attr[part]))
    im=Image.open(d/'tiles.png'); pal=im.getpalette()
    new=Image.fromarray(sheets[part].astype(np.uint8),'P'); new.putpalette(pal); new.save(d/'tiles.png')
    for b in (range(6) if part==0 else range(6,13)):
        f=d/'palettes'/f'{b:02}.pal'; old=f.read_text().splitlines()
        lines=old[:3]+[' '.join(str(int(v)) for v in c) for c in pals[b]]
        f.write_text('\r\n'.join(lines)+'\r\n' if '\r\n' in f.read_text() else '\n'.join(lines)+'\n')
(ENG/'data/layouts/VioletCity/map.bin').write_bytes(struct.pack('<%dH'%w.size,*[int(v) for v in w.ravel()]))
