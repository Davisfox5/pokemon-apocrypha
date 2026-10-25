"""Decode the actual FRLG/EMERALD source formats, without tracing screenshots."""
from pathlib import Path
import json, struct
from PIL import Image, ImageDraw

def words(p, fmt='H'):
    b=Path(p).read_bytes(); return list(struct.unpack('<'+fmt*(len(b)//struct.calcsize(fmt)),b))
def pal(p):return [tuple(map(int,s.split())) for s in Path(p).read_text().splitlines()[3:19]]
class Bank:
    def __init__(self,engine,primary,secondary,frlg=True):
        self.frlg=frlg;self.split=640 if frlg else 512;self.psplit=7 if frlg else 6
        self.dirs=[Path(engine)/'data/tilesets'/s for s in (primary,secondary)]
        self.tiles=[]; self.blocks=[]; self.attrs=[]; self.pals=[]
        for d in self.dirs:
            im=Image.open(d/'tiles.png');self.tiles.append([im.crop((x,y,x+8,y+8)) for y in range(0,im.height,8) for x in range(0,im.width,8)])
            self.blocks.append(list(struct.iter_unpack('<8H',(d/'metatiles.bin').read_bytes())))
            self.attrs.append(words(d/'metatile_attributes.bin','I' if frlg else 'H'))
            self.pals.append([pal(d/'palettes'/f'{i:02}.pal') for i in range(16)])
    def entries(self,mid):return self.blocks[mid>=self.split][mid-self.split if mid>=self.split else mid]
    def attr(self,mid):return self.attrs[mid>=self.split][mid-self.split if mid>=self.split else mid]
    def tile(self,tid):return self.tiles[tid>=self.split][tid-self.split if tid>=self.split else tid]
    def render(self,mid):
        out=Image.new('RGB',(16,16),self.pals[0][0][0])
        for i,e in enumerate(self.entries(mid)):
            tile=self.tile(e&1023); bank=e>>12; colors=self.pals[bank>=self.psplit][bank]
            for y in range(8):
                for x in range(8):
                    v=tile.getpixel((7-x if e&1024 else x,7-y if e&2048 else y))
                    if v:out.putpixel(((i%4%2)*8+x,(i%4//2)*8+y),colors[v])
        return out
    def map(self,grid,w):
        im=Image.new('RGB',(w*16,len(grid)//w*16)); cache={m&1023:self.render(m&1023) for m in set(grid)}
        for i,m in enumerate(grid):im.paste(cache[m&1023],(i%w*16,i//w*16))
        return im

def numbered(im,scale=3):
    w,h=im.width//16,im.height//16;out=Image.new('RGB',(im.width*scale+28,im.height*scale+26),'#202830');out.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(28,26));d=ImageDraw.Draw(out)
    for x in range(w):d.text((28+x*16*scale+4,8),str(x),fill='white');d.line((28+x*16*scale,26,28+x*16*scale,out.height),fill='#555555')
    for y in range(h):d.text((3,26+y*16*scale+5),str(y),fill='white');d.line((28,26+y*16*scale,out.width,26+y*16*scale),fill='#555555')
    return out
