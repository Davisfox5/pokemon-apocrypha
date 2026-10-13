#!/usr/bin/env python3
"""Independent HGSS image-to-block survey. Never reads Gen 3 map blockdata."""
from pathlib import Path
import json,csv
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/route30-hgss-blocks';S=OUT/'source';EV=OUT/'evidence'
W,H=35,74;OX,OY=6,4
# Palette samples from the actual HGSS render, not the existing native map.
COLORS={
 'P':[(224,200,128),(224,200,136),(216,184,128),(216,184,136),(184,168,128),(216,168,128),(216,168,136),(152,144,112)],
 '.':[(104,208,152),(104,200,152),(96,192,144),(88,176,136),(96,200,152),(112,208,160),(104,216,152)],
 'G':[(56,152,88),(40,136,80),(64,168,112),(32,112,80),(80,192,120),(32,120,88)],
 'T':[(64,56,40),(64,64,40),(72,72,48),(80,88,40),(88,104,32),(88,112,32),(96,120,32),(112,144,32),(120,152,32),(136,168,40)],
 'W':[(64,168,216),(72,176,224),(80,184,232),(88,192,232),(96,200,240),(88,184,224)]}
# Independently measured structures in HGSS pixel coordinates / Gen 3 cells.
FEATURES={
 'houses':[{'name':'MrPokemon','asset':'gable','x':25,'y':1,'width':5,'height':5,'door_front':[27,6],'reference_box_px':[409,34,80,75]},
           {'name':'SouthernHouse','asset':'house_mirror','x':13,'y':48,'width':5,'height':5,'door_front':[16,53],'reference_box_px':[208,787,80,72]}],
 'stairs':[{'name':'north','rect':[9,0,3,2]},{'name':'upper-plateau','rect':[15,6,1,2],'orientation':'east-west'},{'name':'middle','rect':[9,28,3,1]},{'name':'southwest','rect':[6,63,4,1]},{'name':'southeast','rect':[17,63,4,1]}],
 'ledges':[[9,4,3,1],[7,12,6,1],[8,21,5,1],[8,32,3,1],[6,51,4,1],[5,68,5,1]],
 'signs':[{'name':'NorthernRouteSign','at':[8,24]},{'name':'MrPokemonDirection','at':[20,34]},{'name':'Route30','at':[13,58]}],
 'apricorns':[[21,5],[12,52]],
 'flower_boxes':[[22,8,2,2],[26,8,4,2],[12,23,3,3],[22,32,3,2],[12,35,3,3],[11,57,3,2]],
 'cliff_rects':[[0,0,9,1],[12,0,23,1],[16,1,19,3],[33,0,2,46],[15,6,1,22],[8,28,1,6],[3,35,5,1],[3,36,1,38],[4,63,2,1],[10,63,7,1],[21,63,14,1]],
 'cliff_openings':[[9,0,3,2],[15,6,1,2],[9,28,3,1],[6,63,4,1],[17,63,4,1]],
 'ponds':[{'name':'upper','rect':[21,48,6,11]},{'name':'southern','rect':[25,70,8,4],'reference_clipped_at_south':True}],
 'manual_clearings':[[12,6,5,1],[23,4,2,4],[30,4,1,5],[12,52,1,3],[13,53,6,1],[25,6,5,1]],
 'canopy_corridors':[{'rect':[13,7,1,15],'reason':'HGSS grass strip beside ledge ends is beneath the western canopy; the trunk/barrier is in column 14.'}],
 'cut_barriers':[{'ground':[18,7],'source_box':[292,100,24,32],'native_canvas_offset':[-2,-16],'interaction':'static original barrier; Cut script not added'}],
 'divider_trees':[{'x':13,'y':y,'ground_rect':[14,y+1,1,2]} for y in range(7,20,2)],
 'original_reference_rows':74,
 'interpretation':'Image-measured terrain; sprite canopy overhang is not raw Gen 4 collision data. Native roofs align by door/ground anchor.'}

def trace():
 im=np.asarray(Image.open(S/'hgss-reference.png').convert('RGB'));px=np.pad(im,((0,0),(0,3),(0,0)),mode='edge')[OY:OY+H*16,OX:OX+W*16]
 scores={}
 for k,colors in COLORS.items():
  delta=((px.astype(np.int32)[...,None,:]-np.asarray(colors))**2).sum(3).min(2)
  scores[k]=(delta<=144).reshape(H,16,W,16).mean((1,3))
 grid=np.full((H,W),'T',dtype='<U1');confidence=np.zeros((H,W))
 # Colors vote by occupied source pixels; paths/grass are ground, canopy is a
 # barrier envelope. The structural records below resolve hidden ground.
 for y in range(H):
  for x in range(W):
   votes={k:float(a[y,x]) for k,a in scores.items()}
   if votes['W']>.12:ch='W'
   elif votes['P']>.22:ch='P'
   elif votes['G']>.18:ch='G'
   elif votes['T']>.16:ch='T'
   elif votes['.']>.12:ch='.'
   else:ch='T'
   grid[y,x]=ch;confidence[y,x]=votes.get(ch,0)
 def rect(r,ch):x,y,w,h=r;grid[y:y+h,x:x+w]=ch
 for r in FEATURES['cliff_rects']:rect(r,'#')
 for r in FEATURES['manual_clearings']:rect(r,'.')
 for pond in FEATURES['ponds']:rect(pond['rect'],'W')
 for r in FEATURES['ledges']:rect(r,'_')
 for r in FEATURES['cliff_openings']:rect(r,'S')
 for house in FEATURES['houses']:rect([house['x'],house['y'],5,5],'H');x,y=house['door_front'];grid[y,x]='.'
 for sign in FEATURES['signs']:x,y=sign['at'];grid[y-1,x]='.';grid[y,x]='!'
 for x,y in FEATURES['apricorns']:grid[y,x]='A'
 # Reference path centerlines retain narrow HGSS widths and actual junctions.
 # These are hand measured directly on the grid, independent of prior stencils.
 for r in [[9,2,3,26],[9,29,2,5],[8,34,3,4],[7,38,2,25],[9,37,17,2],[25,34,2,5],[9,54,7,2],[15,54,2,9],[7,61,10,2],[7,64,2,10]]:rect(r,'P')
 # Restore structures after centerline stitching so paths do not erase ledges.
 for r in FEATURES['ledges']:rect(r,'_')
 for r in FEATURES['cliff_openings']:rect(r,'S')
 terrain=grid.copy()
 for house in FEATURES['houses']:
  x,y=house['x'],house['y'];terrain[y:y+5,x:x+5]='.'
 for box in FEATURES['cliff_rects']:
  x,y,w,h=box;terrain[y:y+h,x:x+w]='#'
 for box in FEATURES['cliff_openings']:
  x,y,w,h=box;terrain[y:y+h,x:x+w]='S'
 (S/'terrain.txt').write_text('\n'.join(''.join(row) for row in terrain)+'\n')
 for q in FEATURES['canopy_corridors']:rect(q['rect'],'c')
 grid[7,14]='c'
 # Lawn passage around the first ledge's eastern end, beneath HGSS canopy.
 grid[3,12]='c'
 grid[6,18]='c'
 grid[7,18]='K'
 # Cell-level corrections are authored only after reviewing the HGSS survey.
 overrides=S/'cell-overrides.json'
 if overrides.exists():
  for q in json.loads(overrides.read_text()):grid[q['y'],q['x']]=q['type']
 np.save(S/'tree-source-fractions.npy',scores['T'])
 (S/'blocks.txt').write_text('\n'.join(''.join(r) for r in grid)+'\n')
 (S/'structures.json').write_text(json.dumps(FEATURES,indent=2)+'\n')
 ledger=[]
 for y in range(H):
  for x in range(W):ledger.append({'x':x,'y':y,'type':str(grid[y,x]),'reference_box':[OX+x*16,OY+y*16,16,16],'source_color_fraction':round(float(confidence[y,x]),3),'blocked':bool(grid[y,x] in 'T#H!AW_K'),'source':'HGSS image survey'})
 (S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 colors={'K':(100,70,30),'c':(112,192,148),'.':(130,215,166),'P':(226,200,136),'G':(46,145,86),'T':(71,94,34),'W':(70,170,220),'#':(147,103,78),'S':(220,176,110),'_':(123,82,58),'H':(218,115,140),'!':(40,40,40),'A':(146,65,140)}
 rgb=np.array([[colors[ch] for ch in row] for row in grid],dtype=np.uint8)
 p=Image.fromarray(rgb).resize((560,1184),Image.Resampling.NEAREST);d=ImageDraw.Draw(p)
 for y in range(H):
  for x in range(W):d.rectangle((x*16,y*16,x*16+15,y*16+15),outline=(20,30,20));d.text((x*16+4,y*16+2),grid[y,x],fill=(255,255,255))
 p.save(EV/'survey-blocks.png')
 for y in range(0,H,12):
  h=min(12,H-y);a=Image.fromarray(px[y*16:(y+h)*16]).resize((1120,h*32),Image.Resampling.NEAREST);b=p.crop((0,y*16,560,(y+h)*16)).resize((1120,h*32),Image.Resampling.NEAREST)
  board=Image.new('RGB',(2240,h*32));board.paste(a);board.paste(b,(1120,0));board.save(EV/f'survey-rows-{y:02}-{y+h-1:02}.png')
 print('Independently surveyed',W*H,'HGSS blocks')
if __name__=='__main__':trace()
