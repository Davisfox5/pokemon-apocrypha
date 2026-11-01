"""The apartment block's floors as a plan for the owner (2026-11-01): each floor of HGSS's
Celadon Condominiums (hgss_rooms.py) beside a draft of it in FireRed's Condominiums pieces,
stacked as the building, with the stairs and elevators that join them. Only 1F is built
(interiors.py, `apartments`); the rest is this plan.

    python3 tools/gba/maps/celadon_elements/apartments_plan.py

Writes gba/art/celadon-elements/evidence/apartments/draft_*.png and evidence/apartments-plan.png.
"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'/home/user/pokemon-apocrypha/tools/gba/maps/celadon_elements')
import common as C
sys.path.append(str(C.HERE.parent / 'saffron'))
import frlg, interiors as I
eng=Path('/home/user/pokeemerald-expansion')
S=str(Path(__file__).resolve().parents[4] / 'gba/art/celadon-elements/evidence/apartments') + '/'
pair=frlg.Pair(eng,'building_frlg','condominiums_frlg')
FR={k: frlg.layout(eng, f'CeladonCity_Condominiums_{k}_Frlg')[0] for k in ('1F','2F','3F','Roof')}
mid=lambda g: (g.astype(int) & 0x3ff)

def shell(W=15,H=14):
    m=np.full((H,W),0x281); m[2,:]=0x282; m[:,0]=0x282
    m[0,:]=0x289; m[1,:]=0x291; m[H-1,:]=0x8
    return m
def stamp(m, src, sx, sy, w, h, dx, dy):
    m[dy:dy+h, dx:dx+w]=mid(FR[src])[sy:sy+h, sx:sx+w]
def door(m,x):        # FireRed's doorway, 3 cells with its frame
    m[0,x:x+3]=[0x2db,0x2dc,0x2eb]; m[1,x:x+3]=[0x2e3,0x2e4,0x2ec]
def window(m,x): m[0,x],m[1,x]=0x2f8,0x2f9
def plant(m,x,y,wall=False): m[y-1,x]=0x2ca if wall else 0x2c9; m[y,x]=0x2d1
def mat(m,x): m[-2,x:x+3]=[0x2e8,0x2e9,0x2ea]; m[-1,x:x+3]=[0x1a,0x1b,0x1c]
def divider(m,x,y0,y1):   # FireRed's two-cell wall seen from above, its face and plaque at the south end
    m[y0:y1-1,x]=0x294; m[y0:y1-1,x+1]=0x290; m[y0,x]=0x28c; m[y0,x+1]=0x288
    m[y1-2,x:x+2]=[0x2fa,0x2f4]; m[y1-1,x:x+2]=[0x2fb,0x2fc]

def f1():
    return mid(I.apartments_grid())
def f2():
    m=shell(); door(m,1); door(m,4); window(m,11); window(m,13)
    plant(m,0,2,True); plant(m,0,12)
    divider(m,8,0,10)
    stamp(m,'2F',5,0,2,4,13,6)               # the stairs down, against the east wall (HGSS (13, 9))
    for x,y in ((10,3),(10,4),(10,5),(14,3),(14,4),(14,5)):
        m[y,x]=0x2b4                         # HGSS's chairs along the east room, FireRed's lobby stool
    return m
def f3():
    m=shell(); door(m,1); window(m,6); window(m,11); window(m,13); m[0,4],m[1,4]=0x28b,0x293
    plant(m,0,2,True); plant(m,13,4)         # HGSS's plant, and a plant where HGSS has its globe
    stamp(m,'1F',1,9,4,5,5,6)                # HGSS's meeting table: FireRed's lobby table with its stools
    for x,y in ((0,4),(0,7),(0,10),(12,5),(12,8),(12,11)): # HGSS's desks along both walls: FireRed 3F's desk with its PC
        stamp(m,'3F',0,8,3,2,x,y)
    return m
def roof():
    g=mid(FR['Roof']); W,H=17,13
    m=np.full((H,W),0x306); m[0,:]=0x328
    m[1,:]=0x320; m[1,0]=0x319; m[1,-1]=0x31a; m[2:-1,0]=0x321; m[2:-1,-1]=0x322
    m[-1,:]=0x320; m[-1,0]=0x329; m[-1,-1]=0x32a
    m[2:4,1:8]=[[0x289]*7,[0x291]*7]; door(m.__setitem__ and m[2:], 1) if False else None
    m[2,1:4]=[0x2db,0x2dc,0x2eb]; m[3,1:4]=[0x2e3,0x2e4,0x2ec]; m[2,5:8]=[0x2db,0x2dc,0x2eb]; m[3,5:8]=[0x2e3,0x2e4,0x2ec]
    m[2:12,4]=0x337                          # HGSS's low wall between the two elevator lobbies
    m[3:8,11:15]=g[[5,6,7,10,11],1:5]        # the penthouse, FireRed roof's own building, its door at HGSS's (12, 7)
    for x,y in ((1,6),(1,9),(8,9),(14,9)):
        m[y:y+2,x:x+2]=g[4:6,11:13]          # planters
    return m
def roof_room():
    m=shell(11,12); window(m,3); window(m,7)
    stamp(m,'2F',5,5,2,4,1,0); stamp(m,'2F',5,5,2,4,8,0)   # bookcases either side, as HGSS
    stamp(m,'2F',1,8,4,3,3,4)                # the table
    plant(m,1,6); plant(m,9,6); plant(m,1,9); plant(m,9,9)
    mat(m,4); return m

def elevator():
    sp=frlg.Pair(eng,'building_frlg','condominiums_frlg')
    sd=eng/'data/tilesets/secondary/silph_co_frlg'
    sm=np.frombuffer((sd/'metatiles.bin').read_bytes(),'<u2').reshape(-1,8); sa=np.frombuffer((sd/'metatile_attributes.bin').read_bytes(),'<u4')
    sp.meta.update({frlg.NT+i:[int(v) for v in sm[i]] for i in range(len(sm))}); sp.attr.update({frlg.NT+i:int(sa[i]) for i in range(len(sa))})
    g,_=frlg.layout(eng,'CeladonCity_DepartmentStore_Elevator_Frlg')
    return sp, mid(g)

def draw(m, p=pair):
    g=m.astype(np.uint16); b,t=frlg.render(p,g); return frlg.flat(b,t)
out={}
for name,fn in (('1F',f1),('2F',f2),('3F',f3),('Roof',roof),('Roof room',roof_room)):
    out[name]=draw(fn())
ep,eg=elevator(); out['Elevator']=draw(eg,ep)
for k,v in out.items(): Image.fromarray(v).save(S+f'draft_{k.replace(" ","_")}.png')
print({k:v.shape for k,v in out.items()})

# --------------------------------------------------------------------------- the plan sheet
R=Path('/home/user/pokemon-apocrypha/gba/art/celadon-elements/source/hgss-rooms')
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
def hg(room, box):
    x0,y0,x1,y1=box
    return np.array(Image.open(R/f'condominiums_{room}/hgss-render.png').convert('RGB'))[y0*16:y1*16,x0*16:x1*16]
FLOORS=[  # label, HGSS room, crop, draft, notes
 ('Roof', 'roof', (0,0,17,14), 'Roof', ["Open roof: both elevators come up here (left, right)", "Planters; the penthouse door (12, 7)"]),
 ('Penthouse', 'roof_room', (0,0,13,13), 'Roof room', ["HGSS's roof room: table, bookcases, four plants", "Door back to the roof"]),
 ('3F', '3f', (0,0,17,15), '3F', ["HGSS: Game Freak's office, a meeting table and desks", "along both walls (FireRed 3F's desks with PCs)", "The floor's role in this building is your call", "Left elevator"]),
 ('2F', '2f', (0,0,17,15), '2F', ["Open hall, chairs along the east room as HGSS", "Stairs down to 1F (east room); right elevator"]),
 ('1F (built)', '1f', (0,0,17,15), '1F', ["Lobby, door to Celadon (28, 14)", "Stairs up to 2F; left elevator"]),
 ('Elevator', 'left_elevator', (0,0,7,8), 'Elevator', ["One car, as HGSS (left and right are the same room)", "Left: 1F, 3F, roof.  Right: 2F, roof", "(FireRed Dept Store elevator)"]),
]
SC=2
blocks=[]
for label, room, box, draft, notes in FLOORS:
    a=hg(room, box); b=np.array(Image.open(S+f'draft_{draft.replace(" ","_")}.png'))
    A=Image.fromarray(a).resize((a.shape[1]*SC//2*1, a.shape[0]*SC//2*1)); B=Image.fromarray(b).resize((b.shape[1]*SC,b.shape[0]*SC),Image.NEAREST)
    w=A.width+B.width+460; h=max(A.height,B.height)+34
    im=Image.new('RGB',(w,h),(24,28,36)); d=ImageDraw.Draw(im)
    d.text((6,4),label,font=F,fill=(255,230,120))
    d.text((6,22),'HGSS',font=f,fill=(180,180,180)); d.text((A.width+16,22),'Gen 3 (FireRed pieces)',font=f,fill=(180,180,180))
    im.paste(A,(6,38)); im.paste(B,(A.width+16,38))
    for i,n in enumerate(notes): d.text((A.width+B.width+30,44+i*20),n,font=f,fill=(235,235,235))
    blocks.append(im)
W=max(b.width for b in blocks)+20; H=sum(b.height+14 for b in blocks)+70
o=Image.new('RGB',(W,H),(16,18,24)); d=ImageDraw.Draw(o)
d.text((10,8),"Celadon apartments (HGSS's Condominiums), floor by floor, top to bottom",font=F,fill=(255,255,255))
d.text((10,30),"Stairs: 1F <-> 2F.  Left elevator: 1F, 3F, roof.  Right elevator: 2F, roof.  Roof door -> penthouse.  Only 1F is built; the rest is this plan.",font=f,fill=(200,200,200))
y=60
for b in blocks: o.paste(b,(10,y)); y+=b.height+14
o.save(Path(S).parent / 'apartments-plan.png'); print(o.size)
