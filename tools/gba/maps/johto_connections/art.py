"""Native campus modules and cave entrance. Original pixel work; HGSS houses reused separately."""
import numpy as np
from PIL import Image, ImageDraw

INK = '#284850'
TEAL = '#408888'
LIGHT = '#88b8b0'
WHITE = '#e8e8d8'
SHADE = '#b0c0b0'
GLASS = '#487880'
GOLD = '#d8c098'

def institute(width=10, height=7):
    """Repeating roof/wall/window modules, with one aligned 16px entrance."""
    w, h = width * 16, height * 16
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rectangle((8, 40, w-9, h-1), fill=INK)
    d.rectangle((9, 41, w-10, h-3), fill=WHITE)
    d.rectangle((w-16, 42, w-10, h-3), fill=SHADE)
    d.polygon([(0,40),(16,8),(w-17,8),(w-1,40)], fill=INK)
    d.polygon([(3,38),(18,10),(w-19,10),(w-4,38)], fill=TEAL)
    for y in range(14, 38, 8):
        inset = max(4, 16-(y-8)//2)
        d.line((inset,y,w-inset-1,y), fill=LIGHT)
        d.line((inset,y+1,w-inset-1,y+1), fill='#387878')
    d.rectangle((16,7,w-17,9), fill=GOLD)
    d.rectangle((8,39,w-9,43), fill=INK)
    d.line((9,40,w-10,40), fill=GOLD)
    for x in range(16,w-24,32):
        d.rectangle((x,50,x+23,67), fill=INK)
        d.rectangle((x+2,52,x+21,64), fill=GLASS)
        d.line((x+3,53,x+20,53), fill=LIGHT)
        d.line((x+12,52,x+12,64), fill=WHITE)
        d.rectangle((x-1,68,x+24,70), fill=SHADE)
    door = (width//2-1)*16
    if height >= 7:
        for x in [16,w-40]:
            d.rectangle((x,h-29,x+23,h-12),fill=INK)
            d.rectangle((x+2,h-27,x+21,h-15),fill=GLASS)
            d.line((x+3,h-26,x+20,h-26),fill=LIGHT)
            d.line((x+12,h-27,x+12,h-15),fill=WHITE)
            d.rectangle((x-1,h-11,x+24,h-9),fill=SHADE)
    for y in range(74,h-5,12):
        for x in [11,w-25]:d.line((x,y,x+10,y),fill=SHADE)
    d.rectangle((door-2,h-29,door+17,h-1), fill=INK)
    d.rectangle((door,h-27,door+15,h-2), fill=GLASS)
    d.line((door+1,h-26,door+14,h-26), fill=LIGHT)
    d.line((door+7,h-25,door+7,h-2), fill=INK)
    d.point((door+10,h-12),fill=GOLD)
    d.rectangle((door-8,h-36,door+23,h-31), fill=TEAL)
    d.line((door-7,h-35,door+22,h-35),fill=LIGHT)
    d.line((9,h-4,door-3,h-4),fill=SHADE)
    d.line((door+18,h-4,w-10,h-4),fill=SHADE)
    return np.array(im)

def paving():
    im = Image.new('RGBA',(16,16),'#d0d8c8'); d=ImageDraw.Draw(im)
    d.line((0,0,15,0),fill='#e8e8d8'); d.line((0,0,0,15),fill='#e8e8d8')
    d.line((0,15,15,15),fill='#98b0a8'); d.line((15,0,15,15),fill='#98b0a8')
    d.point((5,6),fill='#c0c8b8'); d.point((12,10),fill='#c0c8b8')
    return np.array(im)

def crate():
    im=Image.new('RGBA',(16,16));d=ImageDraw.Draw(im)
    d.rectangle((1,4,14,15),fill=INK); d.rectangle((2,5,13,14),fill=SHADE)
    d.rectangle((2,2,13,6),fill=WHITE);d.line((2,2,13,2),fill=GOLD)
    d.rectangle((4,8,11,11),fill=TEAL);d.line((5,9,10,9),fill=LIGHT)
    return np.array(im)

def dish():
    im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
    d.rectangle((14,17,18,29),fill=INK); d.line((16,18,16,29),fill=SHADE)
    d.rectangle((7,29,25,31),fill=INK)
    d.ellipse((3,1,28,20),fill=INK);d.ellipse((5,2,26,17),fill=WHITE)
    d.arc((6,3,25,17),0,180,fill=SHADE,width=2)
    d.line((16,11,25,2),fill=TEAL,width=2);d.rectangle((23,0,26,3),fill=INK)
    return np.array(im)

def cave():
    im=Image.new('RGBA',(96,80));d=ImageDraw.Draw(im)
    d.polygon([(0,79),(3,34),(18,9),(39,1),(72,6),(91,29),(95,79)],fill=INK)
    d.polygon([(3,76),(7,34),(22,12),(41,5),(70,10),(87,31),(92,76)],fill='#788890')
    for x,y in [(13,29),(35,13),(63,18),(79,39),(8,59),(69,61)]:
        d.polygon([(x,y),(x+12,y-4),(x+17,y+9),(x+1,y+13)],fill='#98a8a8')
        d.line((x,y,x+12,y-4),fill='#c0c8b8',width=2)
        d.line((x+1,y+13,x+17,y+9),fill='#586878',width=2)
    d.rounded_rectangle((31,37,64,79),radius=16,fill=INK)
    d.rounded_rectangle((34,41,61,79),radius=13,fill='#182830')
    d.rectangle((32,67,63,79),fill='#182830')
    d.line((32,78,63,78),fill='#586878')
    for x,y in [(12,33),(23,11),(68,12),(80,41),(7,65)]:
        d.line((x,y,x+8,y-2),fill='#588078',width=2)
    return np.array(im)
