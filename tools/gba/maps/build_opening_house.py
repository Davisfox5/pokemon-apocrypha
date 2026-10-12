"""Native, dedicated Johto home tiles; never edits the shared Emerald rooms."""
from pathlib import Path
import json, struct, sys
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[3]
game = root / 'tools/vendor/gba/opening-house-work'
art = root / 'gba/art/opening-house'
colors = [(0,0,0),(32,32,40),(64,48,48),(88,64,48),(120,80,56),
          (152,104,64),(184,136,88),(216,176,120),(232,208,160),
          (248,232,192),(80,104,104),(104,144,144),(152,192,192),
          (184,216,208),(104,64,80),(152,96,112)]
W,H = 11,9

def room(bedroom):
    # Exact native-scale fragments from the same HGSS map-render source used
    # for Cherrygrove. Retile floor/rug cells to remove the source's actors.
    src=Image.open(art/'references'/('bedroom-hgss.png' if bedroom else 'house-1f-hgss.png')).convert('RGB')
    im=src.crop((40,17,216,161 if not bedroom else 177))
    if bedroom:
        floor=src.crop((88,81,104,97))
        for yy in range(61,81):
            for xx in range(75,100):im.putpixel((xx,yy),floor.getpixel(((xx-48)%16,(yy-64)%16)))
        # Carpet repeat, sampled from an unobstructed part of the original rug.
        rug=src.crop((145,112,161,128))
        for yy in range(81,96):
            for xx in range(75,100):im.putpixel((xx,yy),rug.getpixel(((xx-105)%16,(yy-95)%16)))
        blocked={(x,y) for y in range(3) for x in range(11)}
        blocked.update({(0,y) for y in range(10)}|{(10,y) for y in range(10)}|{(x,9) for x in range(11)})
        blocked.update({(2,3),(5,3),(6,3),(7,3),(8,3),(9,3),(0,6),(1,6),(2,6),(0,7),(1,7),(2,7),(0,8),(1,8),(2,8),(9,7),(9,8)})
        blocked.discard((2,3));blocked.add((1,3))
    else:
        floor=src.crop((56,81,88,113))
        for yy in range(48,81):
            for xx in range(71,101):im.putpixel((xx,yy),floor.getpixel(((xx-16)%32,(yy-64)%32)))
        rug=src.crop((184,113,200,129))
        for yy in range(80,97):
            for xx in range(71,100):im.putpixel((xx,yy),rug.getpixel(((xx-144)%16,(yy-96)%16)))
        im.paste(src.crop((120,114,136,130)),(80,81))
        # The actors covered the curved upper-left rug edge as well as floor.
        # Recover that edge from the matching unoccupied right-hand curve.
        for sy in range(88,98):
            for sx in range(111,141):
                rgb=src.getpixel((312-sx,sy))
                if rgb[2]>rgb[0]+8:im.putpixel((sx-40,sy-17),rgb)
        blocked={(x,y) for y in range(2) for x in range(11)}
        blocked.update({(0,y) for y in range(3,9)}|{(10,y) for y in range(9)}|{(x,8) for x in range(11)})
        blocked.update({(2,2),(4,2),(5,2),(7,2),(8,2),(9,2),(6,3),(7,3),(8,3),(9,3),(6,4),(7,4),(5,5),(5,6),(6,5),(7,5),(8,5),(6,6),(7,6),(8,6),(0,7),(10,7)})
        blocked.discard((2,7));blocked.discard((3,7));blocked.discard((2,2));blocked.add((1,2))
    return im,blocked

def bank_for(bedroom,x,y):
    if bedroom:
        if (5<=x<=9 and 2<=y<=3) or (x<=2 and 6<=y<=8):return 11
        if (4<=x<=7 and 5<=y<=8) or (x==9 and y>=7):return 12
        return 10
    if x in (0,10) and y>=6:return 9
    if 4<=x<=9 and 5<=y<=7:return 8
    if x>=4 and 1<=y<=3:return 7
    return 6

def build():
    folder=game/'data/tilesets/secondary/apoc_home';(folder/'palettes').mkdir(parents=True,exist_ok=True)
    pal='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n'
    for i in range(16):(folder/'palettes'/f'{i:02}.pal').write_text(pal)
    tiles=[bytes(64)];blocks=[];attrs=[]
    tile_index={tiles[0]:0}
    layouts=json.loads((game/'data/layouts/layouts.json').read_text())
    behavior_names=(game/'include/constants/metatile_behaviors.h').read_text().split('enum {')[1].split('};')[0]
    behaviors=[s.strip().split(',')[0] for s in behavior_names.splitlines() if s.strip().startswith('MB_') or s.strip().startswith('NUM_')]
    global H
    for bedroom,name in [(False,'CherrygrovePlayerHouse'),(True,'CherrygrovePlayerBedroom')]:
        H=10 if bedroom else 9
        im,blocked=room(bedroom);grid=[]
        palettes={}
        for bank in set(bank_for(bedroom,x,y) for y in range(H) for x in range(W)):
            cells=[im.crop((x*16,y*16,x*16+16,y*16+16)) for y in range(H) for x in range(W) if bank_for(bedroom,x,y)==bank]
            sample=Image.new('RGB',(16,len(cells)*16))
            for i,cell in enumerate(cells):sample.paste(cell,(0,i*16))
            quant=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
            rgbpal=[0,0,0]+quant.getpalette()[:45]
            palettes[bank]=quant
            paltext='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,rgbpal[i:i+3])) for i in range(0,48,3))+'\n'
            (folder/'palettes'/f'{bank:02}.pal').write_text(paltext)
        preview=Image.new('RGB',im.size)
        for y in range(H):
            for x in range(W):
                bank=bank_for(bedroom,x,y)
                cell=im.crop((x*16,y*16,x*16+16,y*16+16)).quantize(palette=palettes[bank],dither=Image.Dither.NONE)
                preview.paste(cell.convert('RGB'),(x*16,y*16))
                es=[]
                for q in range(4):
                    data=bytes(v+1 for v in cell.crop(((q%2)*8,(q//2)*8,(q%2)*8+8,(q//2)*8+8)).getdata())
                    if data not in tile_index:tile_index[data]=len(tiles);tiles.append(data)
                    es.append(tile_index[data]+(bank<<12))
                blocks.append(es+[(bank<<12)]*4)
                beh=('MB_DOWN_LEFT_STAIR_WARP' if bedroom else 'MB_UP_LEFT_STAIR_WARP') if (x,y)==(2,3 if bedroom else 2) else 'MB_NORMAL'
                if not bedroom and y==7 and x in (2,3):beh='MB_SOUTH_ARROW_WARP'
                attrs.append(behaviors.index(beh))
                solid=(x,y) in blocked
                if not bedroom and y==7 and x in (2,3):solid=False
                grid.append(512+len(blocks)-1+(0xC00 if solid else 0)+0x3000)
        layname='Apocrypha_Home_2F' if bedroom else 'Apocrypha_Home_1F'
        ld=game/'data/layouts'/layname;ld.mkdir(exist_ok=True)
        (ld/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid))
        (ld/'border.bin').write_bytes(struct.pack('<4H',*(grid[0],)*4))
        layouts['layouts']=[l for l in layouts['layouts'] if l['id']!='LAYOUT_'+layname.upper()]
        layouts['layouts'].append({'id':'LAYOUT_'+layname.upper(),'name':layname,'width':W,'height':H,'primary_tileset':'gTileset_ApocHomeBase','secondary_tileset':'gTileset_ApocHome','border_filepath':f'data/layouts/{layname}/border.bin','blockdata_filepath':f'data/layouts/{layname}/map.bin'})
        mp=game/'data/maps'/name/'map.json';m=json.loads(mp.read_text());m['layout']='LAYOUT_'+layname.upper()
        m['warp_events'] = ([{'x':2,'y':7,'elevation':0,'dest_map':'MAP_CHERRYGROVE_CITY','dest_warp_id':'0'}, {'x':3,'y':7,'elevation':0,'dest_map':'MAP_CHERRYGROVE_CITY','dest_warp_id':'0'}, {'x':2,'y':2,'elevation':0,'dest_map':'MAP_CHERRYGROVE_PLAYER_BEDROOM','dest_warp_id':'0'}] if not bedroom else [{'x':2,'y':3,'elevation':0,'dest_map':'MAP_CHERRYGROVE_PLAYER_HOUSE','dest_warp_id':'2'}])
        if bedroom:
            m['bg_events']=[{'type':'sign','x':5,'y':3,'elevation':3,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'CherrygrovePlayerBedroom_PC'}]
        else:
            for obj,pos in zip(m['object_events'],[(5,4),(3,6),(4,7)]):obj['x'],obj['y']=pos
            for obj in m['object_events'][1:]:obj['graphics_id']='1037'
            m['coord_events']=[{'type':'trigger','x':x,'y':6,'elevation':3,'var':'VAR_APOC_HOME_STAGE','var_value':'1','script':'CherrygrovePlayerHouse_ExitGuard'} for x in (2,3)]
        content=json.dumps(m,indent=2)+'\n'
        if mp.read_text()!=content:mp.write_text(content)
        preview.resize((W*48,H*48),Image.Resampling.NEAREST).save(art/(layname+'.png'))
    # Indoor camera padding is a blocked black void, never a tiled wall.
    black=bytes([1]*64)
    if black not in tile_index:tile_index[black]=len(tiles);tiles.append(black)
    border_mid=512+len(blocks)
    blocks.append([tile_index[black]]*4+[0]*4);attrs.append(0)
    (folder/'palettes/00.pal').write_text('JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
    for layname in ('Apocrypha_Home_1F','Apocrypha_Home_2F'):
        (game/'data/layouts'/layname/'border.bin').write_bytes(struct.pack('<4H',*[border_mid+0x3C00]*4))
    content=json.dumps(layouts,indent=2)+'\n'
    if (game/'data/layouts/layouts.json').read_text()!=content:(game/'data/layouts/layouts.json').write_text(content)
    assert len(tiles)<=1024
    primary=game/'data/tilesets/primary/apoc_home';(primary/'palettes').mkdir(parents=True,exist_ok=True)
    for bank in range(16):(primary/'palettes'/f'{bank:02}.pal').write_bytes((folder/'palettes'/f'{bank:02}.pal').read_bytes())
    (primary/'metatiles.bin').write_bytes(bytes(512*16))
    (primary/'metatile_attributes.bin').write_bytes(bytes(512*2))
    for part,dest in [(0,primary),(1,folder)]:
        data=tiles[part*512:(part+1)*512]
        if part==0:data+= [bytes(64)]*(512-len(data))
        sheet=Image.new('P',(128,((len(data)+15)//16)*8));sheet.putpalette([0,0,0]+rgbpal[3:48]+[0]*720)
        for i,pixels in enumerate(data):
            tile=Image.new('P',(8,8));tile.putdata(pixels);sheet.paste(tile,((i%16)*8,(i//16)*8))
        sheet.save(dest/'tiles.png')
    (folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks))
    (folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(attrs),*attrs))
    print(f'{len(tiles)} native patterns; {len(blocks)} metatiles')

if __name__=='__main__':build()
