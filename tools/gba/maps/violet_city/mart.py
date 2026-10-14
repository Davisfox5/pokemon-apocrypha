"""Original Violet shop, retaining the HGSS Mart's blue/steel identity and sign.
The existing palette is shared unchanged with the cleaned donor sign.
"""
import numpy as np
from claude_cherrygrove.pixel import Canvas,Palette


def building(source_palette):
    p=Palette(9,source_palette.colors,[str(i) for i in range(15)])
    colors=np.array(p.gba()[1:],int)
    for name,rgb in {
        'ink':(32,32,32),'shadow':(40,48,56),'steel_dark':(72,80,80),
        'steel':(96,104,96),'steel_light':(152,168,152),'edge':(176,192,184),
        'roof_dark':(16,72,144),'roof':(24,104,192),'roof_light':(16,128,208),
        'blue':(16,152,224),'glass':(72,176,216),'reflection':(64,144,216),
        'slate':(80,96,112),
    }.items():p.index[name]=1+int(((colors-rgb)**2).sum(1).argmin())
    c=Canvas(80,64,p)
    # Compact steel-and-stone storefront. The left doorway stays centered on
    # world tile (21,40); the right display bay faces the projecting HGSS sign.
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
    # Deep parallel roof with short rounded corners and a steel drip edge.
    # Blue overlapping courses retain the original shop's color silhouette.
    for y in range(3,35):
        inset=3 if y in (3,34) else 1 if y in (4,33) else 0
        left,right=4+inset,68-inset
        c.rect(left,y,right-left,1,'roof_dark')
        for x in range(left+2,right-2):
            dy=(y-5)%4;dx=(x+4*((y-5)//4%2))%8
            tone='roof_light' if dy==0 else 'roof'
            if dy==1 and dx in (1,2,3,4,5):tone='blue'
            if dy==3:tone='roof_dark'
            if dx==0 and dy in (1,2):tone='roof_dark'
            c.put(x,y,tone)
        c.put(left,y,'glass');c.put(left+1,y,'roof_light')
    c.rect(8,2,56,1,'glass');c.rect(7,35,58,2,'steel_dark')
    c.rect(8,35,56,1,'edge');c.rect(8,37,56,1,'shadow')
    return c
