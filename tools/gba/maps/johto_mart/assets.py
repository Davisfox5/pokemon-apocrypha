"""Original Johto retail pavilion: one raised sapphire roof and recessed glazing."""
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


def building(p):
    c=Canvas(112,96,p)
    # One rectangular raised volume. The vertical facade sits beneath the
    # projecting roof, like the neighboring HGSS house and lecture hall.
    c.rect(10,46,94,46,'ink');c.rect(12,48,88,44,'stone')
    c.rect(100,50,4,42,'shade');c.rect(12,90,88,3,'stone_dark')
    c.rect(10,93,94,2,'shade')
    c.rect(14,54,84,34,'light')
    # Recessed double doors retain the existing map entrance axis at x=40.
    c.rect(30,56,24,36,'shade');c.rect(32,58,20,34,'stone_dark')
    c.rect(34,60,16,30,'glass_dark');c.rect(35,61,14,28,'glass')
    c.rect(35,61,14,3,'glass_light');c.rect(35,78,14,2,'cyan')
    c.rect(41,61,2,28,'shade')
    c.rect(39,78,1,5,'gold');c.rect(44,78,1,5,'gold')
    c.rect(32,90,20,3,'white');c.rect(32,93,20,2,'stone')
    # Slim repeated glazing, merchandise and reflected sky; no fascia text.
    for x in (16,56,72,88):
        c.rect(x-2,58,16,30,'glass_dark')
        c.rect(x,60,12,25,'glass');c.rect(x,60,12,4,'glass_light')
        c.rect(x,64,12,3,'cyan');c.rect(x+1,70,10,1,'glass_light')
        c.rect(x,78,12,1,'shade');c.rect(x,85,12,3,'stone_dark')
        c.rect(x+2,74,3,4,'cyan');c.rect(x+7,75,3,3,'gold')
        c.rect(x+3,72,1,2,'light');c.rect(x+8,74,1,1,'white')
        c.rect(x+12,58,2,30,'light')
    c.rect(12,88,18,2,'white');c.rect(54,88,46,2,'white')
    # Parallel side verges and a single continuous sloping roof plane.
    # Front eaves project past the walls and occlude the tops of the glazing.
    for y in range(12,59):
        inset=4 if y in (12,58) else 2 if y in (13,57) else 0
        l,r=4+inset,108-inset
        c.rect(l,y,r-l,1,'light')
        tone='cyan' if y<16 else 'blue_mid' if y<26 else 'blue' if y<49 else 'blue_dark'
        c.rect(l+2,y,r-l-4,1,tone)
        c.put(r-1,y,'stone_dark')
    # Narrow shaded hip faces distinguish the sloping top from the vertical
    # wall. Their diagonal folds terminate at the same front eave.
    for y in range(16,56):
        hip=18-(y-16)//4
        c.rect(6,y,hip-6,1,'blue')
        c.put(hip,y,'cyan' if y<26 else 'blue_mid')
        c.rect(112-hip,y,106-(112-hip),1,'blue_dark')
        c.put(111-hip,y,'shade')
    # Standing seams run down the main plane and stop at its folded edges.
    for x in (16,32,48,64,80,96):
        for y in range(17,54):
            hip=18-(y-16)//4
            if hip+2<x<109-hip:
                c.put(x,y,'blue_dark')
                c.put(x+1,y,'cyan' if y<26 else 'blue_mid' if y<49 else 'blue')
    c.rect(8,59,96,2,'white');c.rect(10,61,92,3,'stone_dark')
    c.rect(12,64,88,3,'shade');c.rect(14,67,84,2,'glass_dark')
    c.rect(16,64,12,1,'gold');c.rect(84,64,12,1,'gold')
    # Small roof-mounted medallion, with a short base and local cast shadow.
    # Its compact mounting replaces the former full-height sign tower.
    c.rect(31,31,22,3,'blue_dark')
    c.rect(30,15,22,17,'stone_dark');c.rect(30,13,20,17,'white')
    c.rect(32,15,16,13,'blue')
    emblem(c,40,21)
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
        'region':'Johto','status':'Owner-approved Johto Mart exterior; installed in Violet City',
        'palette_bank':bank,'transparent_index':0,'building_pixels':[112,96],
        'brandmark_pixels':[32,32],'building_door_tile':[2,5],'building_approach_tile':[2,6],
        'signage':'Small roof-mounted emblem only; no text, pole sign or tower',
        'placement':'Compile native tile IDs per town. Terrain remains separate. Set roof overlap and wall collision from the destination footprint.',
        'source':'Original indexed artwork in tools/gba/maps/johto_mart/assets.py; sapphire/white Mart identity with new architecture.'
    },indent=2)+'\n')
