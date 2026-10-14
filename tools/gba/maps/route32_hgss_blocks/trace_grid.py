"""Provenance for owner-authorized visual source-cell review; never edits game files."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import refine,build
S=refine.S
# Source-only registration: 30 complete columns and 125 complete rows.
# Initial terrain outlines are original HGSS measurements, not a native layout.
m={name:refine.raster(poly)[1:126,1:31] for name,poly in build.TRACES.items()}
p=np.full((125,30),'.',dtype='<U1')
for name,ch in [('water','W'),('path','P'),('grass','G'),('cliff','R'),('dock','D')]:p[m[name]]=ch
# Review source ocean boundary row by row; decks are overlaid separately below.
# (first row, exclusive last row, first marine column); islands stay rock.
coast=[(59,62,19),(62,77,10),(77,86,14),(86,109,25),(109,122,28),(122,125,29)]
for ya,yb,x in coast:
 p[ya:yb,x:]='W'
# Land bank behind the railway, visible above/below it, not inferred from rail colors.
p[65:69,:8]='.';p[65:69,8:10]='R';p[65:69,10:]='W'
# Exact deck cell courses observed on the annotated source grid.
p[62:81,16:19]='D';p[72:76,12:19]='D';p[78:81,16:22]='D';p[80:87,19:22]='D'
p[86,19:22]='D';p[87:93,19:22]='P'
# Northern grass bank, before the pier; retain inaccessible rock on its east.
p[59:62,10:19]='G';p[59:64,22:25]='R'
# Small eastern sea islands, reviewed in the original rather than inherited ocean fills.
for ya,yb,xa,xb in [(75,78,27,30),(80,83,26,28)]:p[ya:yb,xa:xb]='R'
# West bank and cliff edges: the original continuous west rock is six cells wide.
p[18:25,:6]='R';p[61:77,8:10]='R';p[77:87,12:14]='R';p[87:89,4:14]='R';p[89:101,3:5]='R';p[99:101,:5]='R'
# Source landing/grass details immediately adjacent to the two flights.
p[58:61,8:10]='S';p[58,9]='R';p[60,8]='R';p[58:61,7]='P';p[59:62,10]='G'
p[86:88,5:8]='S';p[88,5:8]='P';p[85,5:8]='G';p[86:89,4]='R';p[86:89,8]='R'
p[26,23:26]='_';p[44,19:21]='_'
# Forecourt and cave steps remain original ground; adapted native Center footprint
# is recorded separately rather than deleting the forest behind its roof.
p[105:111,17:23]='P';p[116,13:15]='.';p[117:119,10:17]='P';p[124,11:22]='R'
# Explicit full-tree anchors, measured on the source grid, not color-score packing.
anchors=[]
def row(y,xs):
 for x in xs:anchors.append([x,y])
def span(y,a,b):row(y,range(a,b+1,2))
for y in [0,2]:span(y,0,20);span(y,25,29)
span(4,0,12);span(4,25,29)
for y in [6,8,10]:row(y,[29])
span(12,0,12);row(12,[29])
span(14,0,18);row(14,[29])
span(16,6,12);row(16,[23,29])
span(18,6,10);row(18,[29])
span(20,6,8);row(20,[29])
for y in range(22,34,2):span(y,6 if y==22 else 0,12);row(y,[29])
row(28,[14])
span(34,0,12);row(34,[26,29])
span(36,0,16)
span(38,0,8)
span(40,0,6)
for y in range(42,60,2):span(y,0,4)
for y in [60,62,64,66,68,70]:row(y,[0])
# Original western fishing clearing is enclosed by a central stand, not open lawn.
for y in [72,74,76,78]:row(y,[0,4,6])
for y in [80,82,84,86,88,90]:row(y,[0])
for y in [86,88]:row(y,[14,16,24])
row(90,[12,14,16,24]);row(92,[0,2,24])
for y in [94,96]:row(y,[0,2,5,15,17,19,21,24])
row(98,[0,2,5,11,13,15,17,19,21,24])
row(100,[5,12,15,17,19,21,24])
row(102,[0,2,4,6,23,25])
row(104,[0,2,4,6,23,25])
row(106,[10,12,23,25])
row(108,[23,25,27])
for y in range(110,122,2):row(y,[22,24,26,28] if y==116 else [21,23,25,27])
row(122,[23,25,27,29]);row(124,[21,23,25,27,29])
# Visual material below trees is lawn. Their two-by-two root footprints are the
# collision authority; their rear canopy row is rendered above the player.
forest=np.zeros_like(p,dtype=bool);crowns=np.zeros_like(p,dtype=bool)
for x,y in anchors:
 if x>=30 or y+2>=125:continue
 for yy in range(y+1,min(125,y+3)):
  for xx in range(x,min(30,x+2)):
   assert not forest[yy,xx],('overlapping root',x,y)
   forest[yy,xx]=True;p[yy,xx]='.'
 crowns[y,x:min(30,x+2)]=True
# Two canonical source small boulders block individual floor squares.
signs=[{'name':'north-sign','source_cell':[14,8]},{'name':'terrace-sign','source_cell':[20,15]},{'name':'cave-sign','source_cell':[18,122]}]
props=[{'name':'southern-boulder','source_cell':[12,122]}, {'name':'cave-side-boulder','source_cell':[21,117]}]
# Actual source building footprints; native prefab differences are explicit.
expected=np.isin(p,list('RW_'))|forest
expected[5:12,0:6]=True;expected[103:107,17:22]=True
for q in props+signs:x,y=q['source_cell'];expected[y,x]=True
text='\n'.join(''.join(r) for r in p)+'\n'
(S/'hgss-cell-grid.txt').write_text(text)
np.save(S/'hgss-reference-blocked.npy',expected)
(S/'hgss-tree-footprints.json').write_text(json.dumps({'registration':'source (x,y) + (1,1) = native (x,y); 16px squares','anchors':anchors,'root_size':[2,2],'root_offset':[0,1],'canopy_size':[2,1],'source':'manually reviewed numbered HGSS Route32 reference grid','props':props,'signs':signs},indent=2)+'\n')
(S/'hgss-grid-review.json').write_text(json.dumps({'reference':'hgss-reference.png','source_cells':[30,125],'cell_pixels':16,'native_offset':[1,1],'right_clipped_pixels':10,'method':'visual square-by-square terrain and rooted-tree tracing; not decoded DS collision','coast_row_runs':coast,'terrain_characters':{'.':'ordinary grass','P':'path','G':'tall grass','R':'inaccessible rock','W':'water (Surf)','D':'wood deck','S':'stairs','_':'one-way ledge'},'preserve':'accepted rock material/color; native north-south Emerald placeholder','adaptations':['whole 2x3 Cherrygrove trees on reviewed source grid','112x96 Violet Center preserves established door coordinate; footprint is wider than HGSS building','western clipped gate remains a visual stub; adjacent maps not wired','native cave portal moved onto source cell (13,116), native (14,117)']},indent=2)+'\n')
print('Source grid:',p.shape,'tree anchors',len(anchors))
