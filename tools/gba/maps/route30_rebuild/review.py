#!/usr/bin/env python3
"""Render review boards from the proposal and recorded native gameplay frames."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'gba/art/route30-rebuild';EV=OUT/'evidence'
p=Image.open(EV/'proposal.png').convert('RGB')
proof=p.copy();d=ImageDraw.Draw(proof)
for x,y,w,h in json.loads((EV/'tree-footprints.json').read_text())['footprint_rectangles']:
 d.rectangle((x,y,x+w-1,y+h-1),outline=(255,200,30),width=1)
proof.save(EV/'footprint-review.png')
g=np.fromfile(OUT/'source/proposed-map.bin',dtype='<u2').reshape(86,35)
a=np.zeros((1376,560,4),np.uint8)
a[np.repeat(np.repeat((g&0xc00)!=0,16,0),16,1)]=[220,35,40,90]
Image.alpha_composite(p.convert('RGBA'),Image.fromarray(a)).convert('RGB').save(EV/'blocked-terrain.png')
ref=Image.open(ROOT/'gba/art/claude-routes/references/route30-hgss.png').convert('RGB')
before=Image.open(EV/'before.png').convert('RGB')
board=Image.new('RGB',(1712,1420),(245,245,239));d=ImageDraw.Draw(board)
for x,title,im in [(8,'HGSS reference (original 74 rows)',ref),(576,'Previous Route 30 (86 rows)',before),(1144,'Revised Route 30 (86 rows)',p)]:
 d.text((x,10),title,fill=(25,25,25));board.paste(im,(x,36))
board.save(EV/'comparison.png')
scenes=[('mr-pokemon-house','Mr. Pokemon house'),('grass-walking','Grass / tree alignment'),('middle-stair-landing','Stairs / path / ledge'),('southern-house','Southern house'),('route30-south-seam','Cherrygrove connection'),('route30-north-seam','Route 31 connection')]
board=Image.new('RGB',(1472,720),(245,245,239));d=ImageDraw.Draw(board)
for i,(name,title) in enumerate(scenes):
 x=8+i%3*488;y=8+i//3*352;d.text((x,y),title,fill=(25,25,25))
 frame=Image.open(EV/'gameplay'/(name+'.png')).convert('RGB');board.paste(frame.resize((480,320),Image.Resampling.NEAREST),(x,y+24))
board.save(EV/'gameplay-comparison.png')
