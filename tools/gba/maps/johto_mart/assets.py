"""Reusable Johto Mart: blue enamel roof, clean shop sign, native indexed pixels."""
from claude_cherrygrove.pixel import Canvas,Palette


def palette(bank=9):
    names=['ink','shadow','steel_dark','steel','steel_light','edge',
           'roof_dark','roof','roof_light','blue','glass','reflection',
           'slate','roof_glint','navy']
    colors=[(24,40,56),(40,56,72),(72,88,104),(112,136,152),(176,192,200),(232,240,232),
            (24,64,128),(24,96,176),(32,128,208),(48,152,224),(136,208,232),(80,176,224),
            (80,112,144),(104,192,240),(16,56,104)]
    return Palette(bank,colors,names)


def building(p):
    c=Canvas(80,64,p)
    # Compact steel-and-stone storefront. The left doorway stays centered on
    # local tile (1,3); the display bay faces the common Johto shop sign.
    c.rect(6,28,60,34,'shadow');c.rect(8,30,56,32,'steel_light')
    c.rect(8,58,56,4,'steel');c.rect(6,62,60,2,'shadow')
    c.rect(10,44,52,14,'steel_dark')
    c.rect(14,42,22,20,'shadow');c.rect(16,44,18,18,'edge')
    c.rect(18,45,14,16,'roof_dark');c.rect(19,46,12,13,'glass')
    c.rect(20,47,10,2,'reflection');c.rect(20,54,10,2,'reflection')
    c.rect(24,46,1,14,'steel_dark');c.rect(28,54,2,2,'edge')
    c.rect(16,61,18,2,'edge')
    # Recessed display glazing, narrow frame and visible shelves.
    c.rect(39,44,23,15,'edge');c.rect(41,46,19,11,'roof_dark')
    c.rect(42,47,17,3,'glass');c.rect(42,51,17,5,'reflection')
    for x in (44,50,56):
        c.rect(x,52,2,3,'glass');c.put(x,51,'edge')
    c.rect(41,50,19,1,'steel_dark');c.rect(50,46,1,11,'steel_dark')
    c.rect(39,59,23,2,'steel_dark')
    for x in (8,35,62):
        c.rect(x,42,2,19,'steel');c.rect(x,42,1,18,'edge')
    # Blue fascia and a small white shop emblem above the recessed entry.
    c.rect(8,37,56,6,'roof_dark');c.rect(10,38,52,3,'blue')
    c.rect(10,41,52,2,'shadow')
    c.ellipse(24,39,5,3,'edge');c.rect(20,39,9,1,'roof_dark')
    c.rect(23,38,3,3,'roof_dark');c.put(24,39,'edge')
    # Smooth enamel shell: broad curved highlight and darker front roll.
    # No shingle pattern or paving-like grid. The parallel sides and shallow
    # rounded corners use the same projection as the other Johto buildings.
    for y in range(3,35):
        inset=4 if y in (3,34) else 2 if y in (4,33) else 1 if y in (5,32) else 0
        left,right=4+inset,68-inset
        c.rect(left,y,right-left,1,'navy')
        if y<7:tone='roof_glint'
        elif y<10:tone='blue'
        elif y<19:tone='roof_light'
        elif y<28:tone='roof'
        else:tone='roof_dark'
        c.rect(left+2,y,right-left-4,1,tone)
        c.put(left,y,'steel_light');c.put(left+1,y,'glass')
        c.put(right-2,y,'roof_dark')
    # Two long pressed seams run down the roof; they never form a tile grid.
    for x in (24,48):
        c.rect(x,10,1,18,'roof');c.rect(x+1,10,1,18,'roof_light')
    c.rect(10,3,52,1,'glass');c.rect(8,35,56,2,'steel_dark')
    c.rect(8,35,56,1,'edge');c.rect(8,37,56,1,'shadow')
    return c


def sign(p):
    """Stand-alone 32x64 board/post; no town name or donor background."""
    c=Canvas(32,64,p)
    # Post and short attachment bracket share the storefront's steel finish.
    c.rect(13,24,4,34,'shadow');c.rect(13,24,2,33,'steel_light')
    c.rect(11,57,8,2,'steel_dark');c.rect(12,57,6,1,'steel_light')
    c.rect(0,12,7,3,'steel_dark');c.rect(0,12,7,1,'edge')
    # Compact blue enamel sign with a clean light border and modest depth.
    c.rect(5,4,24,28,'shadow');c.rect(3,4,24,26,'steel_light')
    c.rect(4,3,22,28,'edge');c.rect(5,5,20,24,'roof_dark')
    c.rect(6,6,18,22,'roof');c.rect(6,6,18,1,'blue')
    # White shopping bag with a Poké Ball mark: legible at native resolution.
    c.rect(12,8,7,6,'edge');c.rect(14,9,3,3,'roof')
    c.rect(10,12,11,7,'edge');c.rect(11,19,9,1,'edge')
    c.rect(11,15,9,1,'roof_dark');c.rect(14,14,3,3,'roof_dark')
    c.put(15,15,'edge')
    # Tiny but exact 3x5 lettering, common to every Johto storefront.
    glyphs={'M':['101','111','111','101','101'],
            'A':['010','101','111','101','101'],
            'R':['110','101','110','101','101'],
            'T':['111','010','010','010','010']}
    for i,ch in enumerate('MART'):
        for y,row in enumerate(glyphs[ch]):
            for x,v in enumerate(row):
                if v=='1':c.put(8+i*4+x,21+y,'edge')
    return c


def make_assets(bank=9):
    p=palette(bank)
    return building(p),sign(p)


def export_assets(destination,bank=9):
    """Export reusable indexed artwork, review cutouts, palette and anchors."""
    from pathlib import Path
    import json
    from PIL import Image
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    pair=make_assets(bank);pal=pair[0].pal
    for name,c in zip(('building','sign'),pair):
        Image.fromarray(c.to_rgba()).save(destination/(name+'.png'))
        image=Image.fromarray(c.px.astype('uint8'),mode='P')
        image.putpalette([v for color in pal.gba() for v in color]+[0]*(768-48))
        image.save(destination/(name+'.indexed.png'),transparency=0)
    (destination/'palette.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,rgb)) for rgb in pal.gba())+'\n')
    (destination/'manifest.json').write_text(json.dumps({
        'region':'Johto','status':'Reusable proposal; installed in Violet for review',
        'palette_bank':bank,'transparent_index':0,'building_pixels':[80,64],
        'sign_pixels':[32,64],'building_door_tile':[1,3],'building_approach_tile':[1,4],
        'sign_offset_from_building_tiles':[4,1],
        'sign_solid_tiles':[[0,1],[0,2],[0,3]],
        'placement':'Use native tile packing per town; do not copy Violet tile IDs. Keep terrain on the background layer.',
        'source':'Original indexed pixel artwork in tools/gba/maps/johto_mart/assets.py; HGSS blue shop identity is the visual reference.'
    },indent=2)+'\n')
