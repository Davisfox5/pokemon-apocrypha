"""Native modular Violet university facade and teaching court.
Original pixel modules composed on the 8px hardware grid, with Johto-scale detail.
"""
import numpy as np
from claude_cherrygrove.pixel import Canvas,Palette


def university():
    names=['ink','shade','stone_dark','stone','stone_light','trim','roof_dark','roof','roof_light','glass_dark','glass','glass_light','wood','brass','red']
    colors=[(48,56,64),(80,88,88),(136,128,112),(184,176,152),(216,208,184),(240,232,208),(56,72,104),(72,96,128),(104,128,152),(48,72,88),(80,128,152),(136,184,192),(96,72,56),(192,160,80),(152,72,56)]
    p=Palette(10,colors,names);c=Canvas(352,144,p)
    # Two classroom wings, joined by a projecting central entrance and clock.
    c.rect(8,72,336,64,'stone');c.rect(8,137,336,5,'shade')
    for x in range(16,336,32):
        c.rect(x,76,1,60,'stone_dark');c.rect(x+1,76,2,60,'stone_light')
        for y in (80,108):
            c.rect(x+8,y,16,20,'stone_dark');c.rect(x+9,y,14,18,'trim')
            c.rect(x+10,y+2,12,14,'glass_dark');c.rect(x+11,y+3,10,11,'glass')
            c.rect(x+11,y+3,10,3,'glass_light');c.rect(x+15,y+2,2,14,'trim')
            c.rect(x+8,y+18,16,2,'stone_light')
    c.rect(8,102,336,3,'stone_light');c.rect(8,105,336,2,'stone_dark')
    c.rect(8,132,336,4,'stone_dark');c.rect(8,132,336,1,'stone_light')
    # Repeating slates, clipped at hip ends. Shared roof modules avoid stretched art.
    for y in range(48,75):
        inset=max(0,(64-y)//2);l=4+inset;r=348-inset
        c.rect(l,y,r-l,1,'roof')
        if y%4==0:c.rect(l,y,r-l,1,'roof_dark')
        if y%4==1:c.rect(l,y,r-l,1,'roof_light')
        for x in range(8+(4 if y//4%2 else 0),344,8):
            if l<=x<r:c.put(x,y,'roof_dark')
    c.rect(12,46,328,2,'roof_light');c.rect(4,75,344,3,'shade');c.rect(4,78,344,2,'trim')
    # Entry projection: broad limestone pilasters, recessed doors, shallow steps.
    c.rect(144,64,64,73,'stone_light');c.rect(148,66,56,64,'stone')
    c.rect(144,88,64,4,'trim');c.rect(146,93,6,41,'trim');c.rect(200,93,6,41,'trim')
    c.rect(157,98,38,34,'stone_dark');c.rect(160,99,32,33,'wood')
    c.rect(162,101,12,26,'glass_dark');c.rect(178,101,12,26,'glass_dark')
    c.rect(163,102,10,11,'glass');c.rect(179,102,10,11,'glass')
    c.rect(172,116,2,5,'brass');c.rect(178,116,2,5,'brass')
    for y in (132,136,140):c.rect(144,y,64,3,'stone_light');c.rect(144,y+3,64,1,'stone_dark')
    # A compact clock tower marks a civic institution instead of another house.
    c.rect(152,16,48,70,'stone_light');c.rect(156,20,40,64,'stone')
    for y in range(4,20):
        half=min(32,8+y);c.rect(176-half,y,half*2,1,'roof_dark' if y%4==0 else 'roof')
    c.rect(144,20,64,3,'shade');c.rect(152,23,48,2,'trim')
    c.ellipse(175.5,44,14,14,'stone_dark');c.ellipse(175.5,44,12,12,'trim')
    c.rect(175,34,2,12,'wood');c.rect(175,44,8,2,'wood')
    for x,y in [(175,33),(175,54),(165,44),(186,44)]:c.rect(x,y,2,2,'brass')
    c.rect(156,63,40,4,'trim');c.rect(168,72,16,8,'roof_dark');c.rect(172,74,8,4,'brass')
    # Matching faculty banners flank the door, with a simple book-like crest.
    for x in (132,212):
        c.rect(x,91,8,31,'roof_dark');c.rect(x+1,92,6,26,'roof')
        c.rect(x+2,98,4,6,'brass');c.rect(x+3,98,1,6,'trim')
    return c


def court():
    p=Palette(4,[(64,80,80),(96,112,104),(184,176,144),(224,216,176),(240,232,200),(176,88,64),(192,112,80),(64,120,152),(80,144,176),(96,160,184),(96,152,112),(112,168,120),(72,112,88),(136,112,80),(64,80,72)],['ink','shade','stone','sand','white','red','red_light','blue','blue_light','blue_high','green','green_light','green_dark','wood','line'])
    c=Canvas(192,112,p);c.rect(0,0,192,112,'green')
    # Terracotta running surround and a blue/red teaching court as in SV's schoolyard.
    c.rect(8,8,176,96,'stone');c.rect(10,10,172,92,'sand')
    c.rect(16,16,160,80,'red');c.rect(96,16,80,80,'blue')
    for y in range(16,96,8):
        c.rect(16,y,160,1,'red_light');c.rect(96,y,80,1,'blue_light')
    c.box(16,16,160,80,'white');c.rect(95,16,2,80,'white')
    c.ellipse(95.5,55.5,15,15,'white');c.ellipse(95.5,55.5,12,12,'red')
    yy,xx=np.indices(c.px.shape);right=((xx-95.5)**2+(yy-55.5)**2<=12**2)&(xx>=96);c.px[right]=c.c('blue')
    c.rect(80,54,32,4,'white');c.ellipse(95.5,55.5,5,5,'white');c.ellipse(95.5,55.5,3,3,'sand')
    for x in (32,144):c.box(x,40,16,32,'white')
    # Access gaps north/south and softened corners keep this an open class court.
    for y in (0,104):
        c.rect(80,y,32,8,'sand')
        for x in (16,144):
            c.rect(x,y,32,7,'wood');c.rect(x,y,32,1,'sand');c.rect(x,y+3,32,1,'sand')
            c.rect(x+2,y+7,3,1,'ink');c.rect(x+27,y+7,3,1,'ink')
    return c


def renovate_gym(c):
    """Retain the HGSS gym silhouette/roof; renovate only its campus-facing trim.

    Bank 5 is exclusive to this building. Keep the warm roof/wood and embedded
    ground shades; map the old cyan and gray facade shades to campus slate/stone.
    """
    replacements={1:(152,184,208),3:(104,128,152),9:(72,96,128),14:(56,72,104),
                  2:(216,208,184),5:(184,176,152),13:(136,128,112)}
    for slot,rgb in replacements.items():c.pal.colors[c.pal.by_slot[slot]]=rgb
    # Reface the existing orange entry supports without changing their outlines.
    yy,xx=np.indices(c.px.shape)
    supports=(yy>=58)&(yy<88)&(xx>=16)&(xx<92)&(c.px==10)
    c.px[supports]=5
    upright=(yy>=64)&(yy<87)&(((xx>=17)&(xx<28))|((xx>=81)&(xx<92)))
    c.px[upright & np.isin(c.px,[4,6,10,11,12])]=5
    # Cream highlights follow the original upright masonry instead of new boxes.
    for x in (20,21,82,83):
        for y in range(68,86):
            if c.px[y,x]==5:c.px[y,x]=2
    # Open-book university crest on the original projecting blue entrance hood.
    c.px[52:64,46:66]=3
    crest=['..gggg....gggg..', '.gppppg..gppppg.', 'gppppppggppppppg', 'gppppppggppppppg',
           'gpddddpggpddddpg', 'gppppppggppppppg', 'gpddddpggpddddpg', 'gppppppggppppppg',
           '.ggggggddgggggg.', '...ggggddgggg...']
    ink={'g':4,'p':2,'d':15}
    for y,row in enumerate(crest,53):
        for x,ch in enumerate(row,48):
            if ch!='.':c.px[y,x]=ink[ch]
    return c
