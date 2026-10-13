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

def lecture_hall():
    """New auditorium architecture, retaining the HGSS gym's copper/cyan identity.

    Broad angular roofs and a raised clerestory replace the old oval building.
    Copper ribs, cyan facade bands and a curved glass entrance recall the gym.
    """
    p=Palette(5,[(64,64,56),(80,72,56),(112,88,56),(136,104,72),
                 (176,128,80),(200,144,88),(168,88,24),(40,104,152),
                 (56,120,160),(104,176,216),(136,208,232),(144,144,144),
                 (176,176,176),(216,208,184),(96,80,56)],
                ['ink','shadow','roof_dark','roof','roof_light','copper','rib',
                 'blue_dark','blue','glass','glass_light','stone','stone_light','cream','wood'])
    c=Canvas(144,112,p)
    # Rectangular lecture wings with tall daylight windows and a deep central entry.
    c.rect(8,56,128,51,'stone');c.rect(8,105,128,4,'shadow')
    c.rect(10,62,124,3,'stone_light');c.rect(10,89,124,4,'blue')
    c.rect(10,89,124,1,'glass_light');c.rect(10,99,124,4,'blue_dark')
    for x in (16,40,88,112):
        c.rect(x,67,16,21,'shadow');c.rect(x+1,68,14,19,'cream')
        c.rect(x+3,70,10,15,'blue_dark');c.rect(x+4,71,8,12,'glass')
        c.rect(x+4,71,8,3,'glass_light');c.rect(x+7,70,2,15,'stone_light')
        c.rect(x-1,87,18,2,'stone_light')
    # Broad angular copper roofs, standing seams and shaded eaves.
    for y in range(28,61):
        inset=max(0,(48-y)//2);left=2+inset;right=142-inset
        c.rect(left,y,right-left,1,'roof_light')
        if y%8==0:c.rect(left,y,right-left,1,'roof')
        if y%8==1:c.rect(left,y,right-left,1,'copper')
        for x in range(8,140,16):
            if left<x<right-1:
                c.rect(x,y,1,1,'roof_dark');c.rect(x+1,y,1,1,'copper')
    c.rect(12,26,120,2,'copper');c.rect(2,61,140,3,'roof_dark')
    c.rect(4,64,136,2,'shadow');c.rect(8,66,128,1,'cream')
    # Raised glazed clerestory establishes a new civic-hall silhouette.
    c.rect(48,12,48,30,'roof_dark');c.rect(50,15,44,23,'stone_light')
    for x in (54,66,78):
        c.rect(x,18,10,15,'blue_dark');c.rect(x+1,19,8,11,'glass')
        c.rect(x+1,19,8,3,'glass_light');c.rect(x+1,30,8,2,'blue')
    for y in range(2,15):
        inset=(14-y)//2;c.rect(40+inset,y,64-inset*2,1,'roof')
        if y%4==0:c.rect(40+inset,y,64-inset*2,1,'copper')
    c.rect(40,15,64,2,'roof_dark');c.rect(48,38,48,3,'copper')
    # Exposed warm ribs echo the original orange structural accents.
    for x in (9,49,91,131):
        c.rect(x,67,4,37,'rib');c.rect(x,67,1,37,'copper')
        c.rect(x-1,104,6,3,'roof_dark')
    # Recessed central glass doors, kept on the existing world doorway axis.
    c.rect(55,73,34,35,'roof_dark');c.rect(58,76,28,30,'cream')
    c.rect(60,78,24,28,'wood')
    for x in (62,74):
        c.rect(x,80,8,22,'blue_dark');c.rect(x+1,81,6,16,'glass')
        c.rect(x+1,81,6,3,'glass_light')
    c.rect(69,92,2,4,'copper');c.rect(73,92,2,4,'copper')
    # A broad fanlight canopy quotes the old blue projecting entrance.
    c.ellipse(71.5,72,25,14,'blue_dark');c.rect(47,72,50,7,'blue_dark')
    c.ellipse(71.5,70,23,12,'blue');c.rect(49,70,46,5,'blue')
    c.ellipse(71.5,68,21,9,'glass');c.rect(51,69,42,3,'glass')
    for x in (57,71,85):c.rect(x,64,1,10,'glass_light')
    # Open-book crest: new use is legible while the historic colors stay dominant.
    c.rect(66,62,12,9,'roof_dark');c.rect(67,63,4,6,'cream');c.rect(73,63,4,6,'cream')
    c.rect(68,66,2,1,'roof');c.rect(74,66,2,1,'roof')
    for y in (106,109):c.rect(55,y,34,2,'stone_light');c.rect(55,y+2,34,1,'stone')
    return c
