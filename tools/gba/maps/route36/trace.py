"""Per-cell Route 36 survey of the original HGSS raster, independent of GBA maps.

Image classification describes visible terrain. Explicit structures and canopy
corrections resolve hidden ground; this is not recovered DS collision data.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'gba/art/route36/source';E=S.parent/'evidence'
W,H=82,32
COLORS={
 'P':[(224,200,136),(216,184,136),(184,168,136)],
 '.':[(104,208,160),(104,200,160),(88,176,144),(96,192,152),(72,168,136)],
 'T':[(80,96,48),(112,152,32),(88,112,40),(72,80,56),(96,128,32),(120,168,40),(64,56,48),(64,72,48),(136,184,48),(64,64,48)],
 'G':[(56,152,88),(40,136,80),(32,112,80),(64,168,112),(80,192,120)],
 'R':[(184,136,104),(136,96,72),(104,72,56),(160,120,88)]}
def trace():
 original=np.asarray(Image.open(S/'hgss-reference.png').convert('RGB'))
 px=np.pad(original,((0,H*16-original.shape[0]),(0,W*16-original.shape[1]),(0,0)),mode='edge')
 scores={}
 for k,colors in COLORS.items():
  delta=((px.astype(np.int32)[...,None,:]-np.array(colors))**2).sum(3).min(2)
  scores[k]=(delta<64).reshape(H,16,W,16).mean((1,3))
 raw=np.full((H,W),'.',dtype='<U1')
 for y in range(H):
  for x in range(W):
   votes={k:float(a[y,x]) for k,a in scores.items()}
   raw[y,x]=max(votes,key=votes.get)
 plan=raw.copy();plan[np.isin(plan,['R','P'])]='.';notes={}
 def rect(ch,x,y,w,h,reason):
  for yy in range(y,min(H,y+h)):
   for xx in range(x,min(W,x+w)):
    plan[yy,xx]=ch;notes[(xx,yy)]=reason
 # Source-measured path edges. Each retained source cell keeps its pixel box.
 for x,y,w,h in [(18,0,3,4),(18,3,9,1),(2,14,10,2),(9,14,3,10),(9,22,24,2),(9,24,3,8),(53,19,23,3),(57,21,5,4)]:
  rect('P',x,y,w,h,'HGSS path grid, rounded to whole movement cells')
 # Western plateau is higher than BOTH flanking routes. Its upper north edge
 # continues into the Route 37 terrain; the eastern neck is the lower ground.
 for x,y,w,h in [(0,4,15,1),(14,5,1,17),(32,16,1,6),(14,24,1,2),(32,24,1,2),(8,26,1,6)]:
  rect('R',x,y,w,h,'HGSS cliff boundary; continuous vertical course')
 for x in (14,32):rect('S',x,22,1,2,'Two-cell east-west stair opening; opposite ascent directions')
 # Raster silhouettes contain canopy overhang. These are the actual native
 # forest footprints, with whole crowns placed separately over the top row.
 # Each run is individually measured at the source's ground/tree boundary.
 forest_runs={
  0:[(0,17),(28,82)],1:[(0,17),(28,82)],2:[(0,17),(30,82)],3:[(31,82)],
  4:[(33,82)],5:[(0,14),(16,18),(20,26),(34,82)],
  6:[(0,14),(16,18),(20,28),(35,82)],7:[(0,14),(16,18),(20,30),(35,82)],
  8:[(0,14),(16,18),(20,30),(34,82)],9:[(0,8),(12,14),(16,18),(23,25),(34,82)],
  10:[(0,8),(12,14),(16,18),(34,82)],11:[(12,14),(16,18),(29,31),(34,82)],
  12:[(12,14),(16,33),(35,82)],13:[(12,14),(16,33),(35,82)],
  14:[(12,14),(35,75)],15:[(12,14),(15,32),(34,44),(45,50),(77,82)],
  16:[(0,8),(12,14),(15,32),(34,44),(45,50)],17:[(0,8),(12,14),(26,32),(34,44),(45,50)],
  18:[(0,8),(12,14),(26,32),(34,44)],19:[(0,8),(12,14),(26,32),(45,50)],
  20:[(0,8),(12,14),(45,51)],21:[(0,6),(45,55),(63,82)],
  22:[(0,6),(38,56),(63,82)],23:[(0,6),(36,57),(63,82)],
  24:[(0,6),(15,32),(34,57),(63,82)],25:[(0,6),(10,32),(34,57),(63,82)],
  26:[(0,6),(10,57),(63,82)],27:[(0,6),(10,57),(63,82)],
  28:[(0,6),(10,57),(63,82)],29:[(0,6),(10,57),(63,82)],
  30:[(0,6),(10,57),(63,82)],31:[(0,6),(10,57),(63,82)]}
 # Forest runs are a separate measured envelope, not inferred by broad rectangles.
 plan[plan=='T']='.'
 for y,runs in forest_runs.items():
  for x,end in runs:rect('T',x,y,end-x,1,'HGSS tree envelope; complete native crown adaptation')
 # South Route 35 narrows and turns west beneath the western stair.
 rect('.',6,24,3,8,'HGSS Route 35 lower corridor, west of rock divider')
 rect('.',6,25,2,7,'HGSS narrow grassy southern exit, shifted from old draft x9..11')
 rect('R',8,26,1,6,'HGSS south cliff with forest on raised east side')
 rect('T',9,26,1,6,'Forest meets the raised side of the southern cliff')
 rect('.',8,24,4,2,'HGSS stair landing to Route 35 elbow')
 # Tall grass occupies eleven by four cells, bordered by the plateau trees.
 rect('G',15,18,11,4,'HGSS western tall-grass patch')
 rect('.',15,17,11,1,'One-tile top edge below forest crown overhang')
 rect('.',26,20,6,2,'Southern landing under eastern terrace trees')
 rect('R',14,24,1,2,'Cliff foot joins the southern forest without a bypass')
 rect('R',32,24,1,2,'Cliff foot joins the southern forest without a bypass')
 # Preserve all stair mouths after canopy survey.
 for x in (14,32):rect('S',x,22,1,2,'West climbs east; east descends east')
 rect('P',9,22,5,2,'West lower stair landing');rect('P',15,22,17,2,'Plateau walking strip')
 # Continuous two-cell passage between the north/south tree bands.
 rect('.',44,15,1,8,'HGSS central neck one-tile trunk corridor with canopy overhang')
 rect('.',33,20,12,2,'HGSS lower east-west lane below central forest divider')
 # Re-audit: the Route37 connector passes ABOVE the forest divider.
 # The old map blocked that corridor and instead opened a false north/south
 # lane between the divider's western trees and the terrace cliff.
 rect('.',33,14,2,2,'HGSS diagonal approach to the upper divider corridor')
 rect('.',34,15,10,1,'HGSS corridor above central divider, reopened')
 rect('T',33,16,11,4,'HGSS divider meets the cliff; false western bypass closed')
 rect('.',35,11,1,5,'HGSS eastern side of the wooded peninsula, reopened')
 rect('T',32,12,2,2,'HGSS peninsula west face; close shifted shortcut')
 rect('T',33,14,2,2,'HGSS peninsula tip beside the upper connector')
 rect('.',38,22,6,1,'HGSS lower clearing extends below divider, reopened')
 # Clear the raster's actor pixels only to their measured underlying terrain.
 rect('.',31,9,2,2,'HGSS lawn south of the Apricorn, restored')
 rect('.',22,0,5,3,'Route 37 sign lawn')
 # Native complete gate footprints replace truncated edge buildings; door
 # centerlines remain at HGSS path heights, south gate extends into padding.
 for box in [(75,15,7,7),(0,9,7,7),(55,24,7,8)]:rect('H',*box,'Whole native gate asset; edge-clipped original expanded')
 rect('P',7,14,5,2,'National Park gate approach');rect('P',72,19,3,3,'Violet gate approach')
 rect('P',56,22,5,2,'Alph gate approach shifted with the accepted building')
 rect('T',53,24,2,8,'West tree bank abuts the shifted Alph gate')
 rect('T',62,24,2,8,'New east tree bank closes the former gate bypass')
 # Source reference ends at row29. Remaining rows finish forest/closed exits.
 np.save(S/'survey-plan.npy',plan)
 ledger=[]
 for y in range(H):
  for x in range(W):ledger.append({'x':x,'y':y,'source_box':[x*16,y*16,16,16] if y<30 and x<81 else None,'sample_type':str(raw[y,x]),'type':str(plan[y,x]),'source_fraction':round(float(scores.get(str(raw[y,x]),scores['.'])[y,x]),3),'interpretation':notes.get((x,y),'Dominant actual source palette; actor/edge pixels resolved during survey')})
 (S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 (S/'survey-blocks.txt').write_text('\n'.join(''.join(r) for r in plan)+'\n')
 (S/'elevation-survey.json').write_text(json.dumps({'west_stair':{'at':[14,22],'high_side':'east','low_side':'west'},'east_stair':{'at':[32,22],'high_side':'west','low_side':'east'},'plateau_level':1,'low_routes_level':0,'engine':'ordinary same-surface movement; cliff collisions enforce separation','source':'HGSS overview inferred relative heights, not DS elevation records'},indent=2)+'\n')
 colors={'.':(116,205,160),'P':(226,200,136),'T':(63,91,36),'G':(38,133,77),'R':(145,101,72),'S':(219,216,183),'H':(40,142,145)}
 im=Image.fromarray(np.array([[colors[ch] for ch in row] for row in plan],np.uint8)).resize((W*16,H*16),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
 for y in range(H):
  for x in range(W):d.rectangle((x*16,y*16,x*16+15,y*16+15),outline=(25,45,35));d.text((x*16+4,y*16+2),plan[y,x],fill='white')
 im.save(E/'survey-blocks.png')
 return plan
if __name__=='__main__':
 p=trace()
 for y,row in enumerate(p):print(f'{y:02} '+''.join(row))
