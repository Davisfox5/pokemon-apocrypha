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
    c.rect(24,72,304,64,'stone');c.rect(24,137,304,5,'shade')
    for x in (32,56,80,104,144,176,216,240,264,288):
        c.rect(x,76,1,60,'stone_dark');c.rect(x+1,76,2,60,'stone_light')
        for y in (80,108):
            c.rect(x+8,y,16,20,'stone_dark');c.rect(x+9,y,14,18,'trim')
            c.rect(x+10,y+2,12,14,'glass_dark');c.rect(x+11,y+3,10,11,'glass')
            c.rect(x+11,y+3,10,3,'glass_light');c.rect(x+15,y+2,2,14,'trim')
            c.rect(x+8,y+18,16,2,'stone_light')
    c.rect(24,102,304,3,'stone_light');c.rect(24,105,304,2,'stone_dark')
    c.rect(24,132,304,4,'stone_dark');c.rect(24,132,304,1,'stone_light')
    # HGSS parallel projection: deep roof planes with parallel side verges.
    # Keep the slate module, but remove the converging hip ends and let the
    # eaves cover the upper wall/window line. The tower remains the same design.
    for y in range(34,84):
        l,r=20,332
        c.rect(l,y,r-l,1,'roof')
        if y%4==0:c.rect(l,y,r-l,1,'roof_dark')
        if y%4==1:c.rect(l,y,r-l,1,'roof_light')
        for x in range(24+(4 if y//4%2 else 0),328,8):
            c.put(x,y,'roof_dark')
        c.put(l,y,'roof_light');c.put(r-1,y,'roof_dark')
    c.rect(20,32,312,2,'roof_light')
    c.rect(20,84,312,3,'roof_dark');c.rect(20,87,312,2,'trim')
    c.rect(24,89,304,3,'shade')
    # Entry projection: broad limestone pilasters, recessed doors, shallow steps.
    c.rect(144,64,64,73,'stone_light');c.rect(148,66,56,64,'stone')
    c.rect(144,88,64,4,'trim');c.rect(146,93,6,41,'trim');c.rect(200,93,6,41,'trim')
    c.rect(157,98,38,34,'stone_dark');c.rect(160,99,32,33,'wood')
    c.rect(162,101,12,26,'glass_dark');c.rect(178,101,12,26,'glass_dark')
    c.rect(163,102,10,11,'glass');c.rect(179,102,10,11,'glass')
    c.rect(172,116,2,5,'brass');c.rect(178,116,2,5,'brass')
    for y in (132,136,140):c.rect(144,y,64,3,'stone_light');c.rect(144,y+3,64,1,'stone_dark')
    # Projecting lintel casts a short shadow over the recessed upper door.
    c.rect(142,92,68,9,'stone_light');c.rect(142,101,68,3,'trim')
    c.rect(144,104,64,6,'shade')
    # Clock tower uses the same parallel projection as the classroom wings:
    # a deeper cap, straight side verges, and a short shadow across the face.
    c.rect(152,16,48,70,'stone_light');c.rect(156,20,40,64,'stone')
    for y in range(4,28):
        c.rect(148,y,56,1,'roof_dark' if y%4==0 else 'roof')
        if y%4==1:c.rect(148,y,56,1,'roof_light')
        c.put(148,y,'roof_light');c.put(203,y,'roof_dark')
    c.rect(148,28,56,2,'roof_dark');c.rect(148,30,56,2,'trim')
    c.rect(152,32,48,3,'shade')
    # Preserve the clock/hands while mildly foreshortening the vertical face.
    c.ellipse(175.5,48,14,12,'stone_dark');c.ellipse(175.5,48,12,10,'trim')
    c.rect(175,40,2,10,'wood');c.rect(175,48,8,2,'wood')
    for x,y in [(175,39),(175,56),(165,48),(186,48)]:c.rect(x,y,2,2,'brass')
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
    c.rect(12,56,120,51,'stone');c.rect(12,105,120,4,'shadow')
    c.rect(14,62,116,3,'stone_light');c.rect(14,89,116,4,'blue')
    c.rect(14,89,116,1,'glass_light');c.rect(14,99,116,4,'blue_dark')
    for x in (20,40,88,108):
        c.rect(x,67,16,21,'shadow');c.rect(x+1,68,14,19,'cream')
        c.rect(x+3,70,10,15,'blue_dark');c.rect(x+4,71,8,12,'glass')
        c.rect(x+4,71,8,3,'glass_light');c.rect(x+7,70,2,15,'stone_light')
        c.rect(x-1,87,18,2,'stone_light')
    # Short overlapping copper tiles: staggered joints, lit curved faces and
    # dark lower lips. The old continuous 16x8 grid read as floor paving.
    def roof_course(y,left,right,origin):
        row=(y-origin)//4;dy=(y-origin)%4
        for x in range(left,right):
            dx=(x+4*(row%2))%8
            tone=('copper' if 1<=dx<=6 else 'roof') if dy==0 else 'roof_light'
            if dy==2 and dx in (0,7):tone='roof'
            if dy==3:tone='roof_dark' if 1<=dx<=6 else 'roof'
            c.put(x,y,tone)
        # Parallel verges retain the roof thickness without perspective taper.
        c.put(left,y,'roof');c.put(left+1,y,'copper')
        c.put(right-2,y,'roof');c.put(right-1,y,'roof_dark')
    for y in range(20,69):
        roof_course(y,10,134,20)
    c.rect(10,18,124,2,'copper');c.rect(10,69,124,3,'roof_dark')
    c.rect(10,72,124,2,'cream');c.rect(12,74,120,3,'shadow')
    # Upper story follows the main roof's parallel projection and overhang.
    # Its three original glass bays sit below the deeper copper cap.
    c.rect(48,12,48,30,'roof_dark');c.rect(50,15,44,23,'stone_light')
    for x in (54,66,78):
        c.rect(x,22,10,15,'blue_dark');c.rect(x+1,23,8,11,'glass')
        c.rect(x+1,23,8,3,'glass_light');c.rect(x+1,34,8,2,'blue')
    for y in range(2,22):roof_course(y,44,100,2)
    c.rect(44,22,56,2,'roof_dark');c.rect(44,24,56,1,'cream')
    c.rect(48,25,48,2,'shadow');c.rect(48,38,48,3,'copper')
    # Exposed warm ribs echo the original orange structural accents.
    for x in (13,49,91,127):
        c.rect(x,77,4,27,'rib');c.rect(x,77,1,27,'copper')
        c.rect(x-1,104,6,3,'roof_dark')
    # Recessed central glass doors, kept on the existing world doorway axis.
    c.rect(55,73,34,35,'roof_dark');c.rect(58,76,28,30,'cream')
    c.rect(60,78,24,28,'wood')
    for x in (62,74):
        c.rect(x,80,8,22,'blue_dark');c.rect(x+1,81,6,16,'glass')
        c.rect(x+1,81,6,3,'glass_light')
    c.rect(69,92,2,4,'copper');c.rect(73,92,2,4,'copper')
    # A broad fanlight canopy quotes the old blue projecting entrance.
    c.ellipse(71.5,78,25,14,'blue_dark');c.rect(47,78,50,7,'blue_dark')
    c.ellipse(71.5,76,23,12,'blue');c.rect(49,76,46,5,'blue')
    c.ellipse(71.5,74,21,9,'glass');c.rect(51,75,42,3,'glass')
    for x in (57,71,85):c.rect(x,70,1,10,'glass_light')
    # Open-book crest: new use is legible while the historic colors stay dominant.
    c.rect(66,68,12,9,'roof_dark');c.rect(67,69,4,6,'cream');c.rect(73,69,4,6,'cream')
    c.rect(68,72,2,1,'roof');c.rect(74,72,2,1,'roof')
    for y in (106,109):c.rect(55,y,34,2,'stone_light');c.rect(55,y+2,34,1,'stone')
    return c
