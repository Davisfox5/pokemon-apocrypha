"""Inspect/render native Emerald tiles and metatiles; no engine or editor emulation."""
import struct
from pathlib import Path
from PIL import Image, ImageDraw

def palette(path):
    return [tuple(map(int, line.split())) for line in path.read_text().splitlines()[3:19]]

class Tileset:
    def __init__(self, game, secondary='petalburg', primary='general'):
        base = Path(game) / 'data/tilesets'
        self.dirs = [base/'primary'/primary, base/'secondary'/secondary]
        self.tiles = []
        self.pals = []
        self.blocks = []
        self.attrs = []
        for part, folder in enumerate(self.dirs):
            image = Image.open(folder/'tiles.png')
            self.tiles.append([list(image.crop((x,y,x+8,y+8)).getdata())
                               for y in range(0,image.height,8) for x in range(0,image.width,8)])
            self.pals.append([palette(folder/'palettes'/f'{n:02}.pal') for n in range(16)])
            data=(folder/'metatiles.bin').read_bytes()
            self.blocks.append(list(struct.iter_unpack('<8H',data)))
            self.attrs.append(list(struct.unpack('<'+'H'*((folder/'metatile_attributes.bin').stat().st_size//2),(folder/'metatile_attributes.bin').read_bytes())))

    def render(self, mid):
        result=Image.new('RGB',(16,16),self.pals[0][0][0])
        entries=self.blocks[mid>=512][mid-512 if mid>=512 else mid]
        for layer in range(2):
            for q in range(4):
                e=entries[layer*4+q]; tid=e&1023; bank=e>>12
                tiles=self.tiles[tid>=512]; idx=tid-512 if tid>=512 else tid
                if idx>=len(tiles):continue
                colors=self.pals[bank>=6][bank]
                for y in range(8):
                    for x in range(8):
                        value=tiles[idx][(7-y if e&2048 else y)*8+(7-x if e&1024 else x)]%16
                        if value:result.putpixel(((q%2)*8+x,(q//2)*8+y),colors[value])
        return result

    def sheet(self, path):
        image=Image.new('RGB',(16*48,64*48),(30,35,40));draw=ImageDraw.Draw(image)
        for part in range(2):
            for index in range(len(self.blocks[part])):
                mid=part*512+index;x=(mid%16)*48;y=(mid//16)*48
                image.paste(self.render(mid).resize((32,32),Image.Resampling.NEAREST),(x,y))
                draw.text((x,y+32),f'{mid:03X}',fill='white')
        image.save(path)

    def map_image(self, grid, width):
        out=Image.new('RGB',(width*16,(len(grid)//width)*16))
        cache={mid&1023:self.render(mid&1023) for mid in set(grid)}
        for i,mid in enumerate(grid):out.paste(cache[mid&1023],((i%width)*16,(i//width)*16))
        return out
