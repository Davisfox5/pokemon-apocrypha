"""Original Johto retail pavilion: layered sapphire roofs and illuminated glazing."""
from claude_cherrygrove.pixel import Canvas,Palette


def palette(bank=9):
    return Palette(bank,
        [(24,40,64),(40,64,96),(104,128,144),(160,184,192),(216,232,232),
         (248,248,232),(16,64,128),(24,104,176),(32,136,208),(88,184,224),
         (32,88,112),(72,144,160),(160,224,224),(224,184,104),(48,80,120)],
        ['ink','shade','stone_dark','stone','light','white','blue_dark','blue',
         'blue_mid','cyan','glass_dark','glass','glass_light','gold','roof'])


def emblem(c,x,y):
    """Open white ring and a gold center: the pavilion's small brand medallion."""
    c.ellipse(x,y,8,7,'blue_dark');c.ellipse(x,y,6,5,'white')
    c.ellipse(x,y,4,3,'blue');c.rect(x-6,y,13,2,'blue_dark')
    c.ellipse(x,y,3,3,'white');c.ellipse(x,y,1,1,'gold')


def wordmark(c,x,y):
    glyphs={'M':['10001','11011','10101','10101','10001','10001','10001'],
            'A':['01110','10001','10001','11111','10001','10001','10001'],
            'R':['11110','10001','10001','11110','10100','10010','10001'],
            'T':['11111','00100','00100','00100','00100','00100','00100']}
    for i,ch in enumerate('MART'):
        for yy,row in enumerate(glyphs[ch]):
            for xx,v in enumerate(row):
                if v=='1':c.put(x+i*6+xx,y+yy,'white')


def building(p):
    c=Canvas(112,96,p)
    # Recessed two-volume storefront: a narrow entrance beside a broad showroom.
    c.rect(12,42,92,50,'ink');c.rect(14,44,88,46,'stone')
    c.rect(14,88,88,4,'stone_dark');c.rect(12,92,92,3,'shade')
    c.rect(28,52,28,40,'shade');c.rect(30,53,24,38,'stone_dark')
    c.rect(32,60,20,32,'light');c.rect(34,62,16,28,'glass_dark')
    c.rect(35,63,14,26,'glass');c.rect(35,63,14,3,'glass_light')
    c.rect(35,78,14,2,'cyan');c.rect(41,63,2,26,'shade')
    c.rect(39,78,1,5,'gold');c.rect(44,78,1,5,'gold')
    c.rect(32,90,20,3,'white');c.rect(32,93,20,2,'stone')
    # Three tall glass bays, slim frames, interior shelving and reflected sky.
    c.rect(54,54,50,35,'glass_dark')
    for x in (56,72,88):
        c.rect(x,62,12,23,'glass');c.rect(x,62,12,3,'glass_light')
        c.rect(x,65,12,2,'cyan');c.rect(x+1,70,10,1,'glass_light')
        c.rect(x,78,12,1,'shade');c.rect(x,85,12,2,'stone_dark')
        c.rect(x+2,74,3,4,'cyan');c.rect(x+7,75,3,3,'gold')
        c.rect(x+3,72,1,2,'light');c.rect(x+8,74,1,1,'white')
        c.rect(x+12,61,2,26,'light')
    c.rect(56,87,46,3,'light');c.rect(56,89,46,1,'white')
    c.rect(56,54,46,8,'blue_dark')
    # Main floating roof: a sapphire plane with a pale perimeter and dark soffit.
    for y in range(14,52):
        inset=4 if y in (14,51) else 2 if y in (15,50) else 0
        l,r=40+inset,108-inset
        c.rect(l,y,r-l,1,'light')
        tone='cyan' if y<18 else 'blue_mid' if y<25 else 'blue' if y<43 else 'blue_dark'
        c.rect(l+2,y,r-l-4,1,tone)
        c.put(r-1,y,'stone_dark')
    c.rect(42,52,64,2,'white');c.rect(44,54,60,2,'shade')
    # A raised skylight, framed in steel, breaks the broad roof plane.
    c.rect(54,23,50,17,'shade');c.rect(54,22,50,16,'light')
    c.rect(56,24,46,12,'glass_dark')
    for x in (56,72,88):
        c.rect(x,25,12,9,'glass');c.rect(x,25,12,2,'glass_light')
        c.rect(x,27,12,2,'cyan');c.rect(x+12,24,2,12,'stone')
        c.rect(x+2,30,4,1,'cyan')
    c.rect(54,38,50,2,'blue_dark')
    # Lower, projecting entrance canopy; its white rim and shadow show depth.
    for y in range(48,68):
        inset=3 if y in (48,67) else 1 if y in (49,66) else 0
        l,r=24+inset,60-inset
        c.rect(l,y,r-l,1,'light')
        c.rect(l+2,y,r-l-4,1,'cyan' if y<52 else 'blue_mid' if y<59 else 'blue')
        c.put(r-1,y,'stone_dark')
    c.rect(26,68,32,2,'white');c.rect(28,70,28,3,'shade')
    # Corner brand tower: architectural stone fin with blue enamel face,
    # recessed warm lights, and the same medallion on every Johto shop.
    c.rect(8,10,22,80,'shade');c.rect(8,8,20,80,'light')
    c.rect(10,6,16,82,'white');c.rect(12,12,12,64,'blue_dark')
    c.rect(13,13,10,61,'blue');c.rect(13,13,1,61,'cyan')
    emblem(c,18,27)
    for y in (44,50,56):
        c.rect(15,y,7,2,'glass_light');c.rect(15,y+2,7,1,'blue_dark')
    c.rect(14,66,9,2,'gold');c.rect(10,80,16,2,'stone')
    c.rect(6,88,24,4,'stone_dark');c.rect(7,88,22,1,'light')
    wordmark(c,67,55)
    return c


def brandmark(p):
    c=Canvas(32,32,p);emblem(c,15,15);return c


def make_assets(bank=9):
    p=palette(bank);return building(p),brandmark(p)


def export_assets(destination,bank=9):
    from pathlib import Path
    import json
    from PIL import Image
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    pair=make_assets(bank);pal=pair[0].pal
    for name,c in zip(('building','brandmark'),pair):
        Image.fromarray(c.to_rgba()).save(destination/(name+'.png'))
        image=Image.fromarray(c.px.astype('uint8'),mode='P')
        image.putpalette([v for color in pal.gba() for v in color]+[0]*(768-48))
        image.save(destination/(name+'.indexed.png'),transparency=0)
    (destination/'palette.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,rgb)) for rgb in pal.gba())+'\n')
    (destination/'manifest.json').write_text(json.dumps({
        'region':'Johto','status':'Original retail pavilion proposal; Violet review installation',
        'palette_bank':bank,'transparent_index':0,'building_pixels':[112,96],
        'brandmark_pixels':[32,32],'building_door_tile':[2,5],'building_approach_tile':[2,6],
        'signage':'Architectural corner tower and fascia wordmark, both integrated in the building; no pole sign',
        'placement':'Compile native tile IDs per town. Terrain remains separate. Set roof overlap and wall collision from the destination footprint.',
        'source':'Original indexed artwork in tools/gba/maps/johto_mart/assets.py; sapphire/white Mart identity with new architecture.'
    },indent=2)+'\n')
