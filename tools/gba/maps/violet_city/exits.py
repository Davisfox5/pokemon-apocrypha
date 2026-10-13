"""HGSS gate silhouette rebuilt from repeating native 8px roof/wall modules."""
from claude_cherrygrove.pixel import Canvas,Palette


def west_gate():
    # Teal hipped roof, cream masonry, ribbon windows and east-facing steps
    # follow the preserved Violet HGSS reference (0,416)-(112,528).
    p=Palette(2,[(56,64,48),(88,80,56),(128,112,80),(176,160,120),(208,192,152),
                 (40,112,104),(40,144,136),(48,160,152),(72,176,168),(112,192,184),
                 (48,80,88),(72,136,168),(112,184,208),(112,120,112),(160,168,160)],
              ['ink','brown','shade','wall','cream','teal_dark','teal','roof','roof_light','edge','glass_dark','glass','shine','step_dark','step'])
    c=Canvas(112,112,p)
    c.rect(0,40,8,48,'teal_dark');c.rect(0,42,6,44,'roof')
    c.rect(88,40,8,48,'teal_dark');c.rect(88,42,6,44,'roof')
    c.rect(8,16,80,88,'brown');c.rect(10,18,76,84,'cream');c.rect(14,20,68,80,'wall')
    # Aligned hip planes with repeatable diagonal cap modules.
    for y in range(64):
        for x in range(16,80):
            dx=min(x-16,79-x);dy=min(y,63-y);d=min(dx,dy)
            tone='teal' if d>=16 else 'edge' if d==15 else 'roof_light' if dy<=dx and y<32 else 'teal_dark' if dy<=dx else 'roof'
            if d==0:tone='teal_dark'
            c.put(x,y,tone)
    c.hline(16,64,64,'brown');c.hline(16,66,64,'cream')
    for x in range(16,80,16):
        c.rect(x,72,16,16,'brown');c.rect(x+2,74,12,12,'glass_dark');c.rect(x+3,75,10,10,'glass')
        for k in range(8):c.hline(x+3,75+k,8-k,'shine')
        c.rect(x,88,16,12,'wall');c.hline(x,90,8,'cream');c.hline(x+8,96,8,'shade')
    # Symmetric roof hips and matching wing modules share flipped hardware tiles.
    c.px[:104,48:88]=c.px[:104,8:48][:,::-1]
    # Steps are long north/south treads, so the player travels east/west.
    for x in range(88,112,8):
        y=96
        c.rect(x,72,8,y-72,'step_dark');c.rect(x+2,73,4,y-74,'step');c.vline(x+6,73,y-73,'ink')
        c.hline(x,y,8,'cream')
    return c


def lily_pads(pal):
    """Small original floating pads; use the Violet home's existing green shades."""
    import numpy as np
    c=Canvas(16,16,pal);colors=np.array(pal.gba(),int)
    def tone(rgb):return int(((colors[1:]-np.array(rgb))**2).sum(1).argmin()+1)
    dark=tone((48,80,40));green=tone((88,128,56));light=tone((128,160,88))
    for cx,cy,rx,ry in [(6,6,6,5),(12,13,3,2)]:
        for y in range(16):
            for x in range(16):
                if ((x-cx)/rx)**2+((y-cy)/ry)**2<=1 and not(x>=cx and y<cy and x-cx<=cy-y):
                    c.px[y,x]=dark if y>=cy+ry-1 else light if y<=cy-ry+1 else green
    return c
