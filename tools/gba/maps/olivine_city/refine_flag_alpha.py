"""Guarded native edit: lift existing flag silhouettes above the player.
Remove captured ground from flag masks; preserve all unrelated city pixels, source collision/elevation and section IDs.
"""
from pathlib import Path
import sys,json,subprocess,struct
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=R/'gba/art/olivine-city/source';E=S.parent/'evidence';O=E/'flag-alpha-cleanup';O.mkdir(exist_ok=True)
BASE='83936f1b20920137a816535dd900e7429928a79f'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==BASE
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True)
sys.path.insert(0,str(R/'tools/gba/maps'));from tiles import Tileset
bg=np.array(Image.open(S/'native-ground.png'));fg=np.array(Image.open(S/'shared-foreground.png'));before=bg.copy();m=fg[...,3]>0;before[m]=fg[m,:3];above=np.load(S/'above.npy').copy()
# Refine the existing masks: ground/grass colors must not occlude sprites.
oldmask=np.array(Image.open(S/'flag-foreground-mask.png'))>0
colors=fg[...,:3].astype(np.int32);red,green,blue=colors.transpose(2,0,1);Y,X=np.indices(oldmask.shape)
keep=(red>=green+8)|(blue>=green+16)|((red>=216)&(green>=216)&(blue>=192))
banner=np.zeros_like(oldmask)
for dx,dy in [(0,0),(224,112)]:
 banner|=((X>=156+dx)&(X<=172+dx)&(Y>=284+dy)&(Y<=297+dy))|((X>=220+dx)&(X<=239+dx)&(Y>=282+dy)&(Y<=295+dy))
keep|=(red<=104)&(green<=112)&(blue<=112)&~banner
newmask=oldmask&keep
for dx,dy in [(0,0),(224,112)]:
 newmask[((X<120+dx)&(X>=112+dx)&(Y<283+dy)&(Y>=276+dy))|((X>=238+dx)&(X<=244+dx)&(Y>=276+dy)&(Y<=302+dy))]=False
removed=oldmask&~newmask;mask=oldmask
# Repair the ground that the old rectangles incorrectly carried into the span.
# Lawn beneath the west banner belongs to the Gym plinth; all other removed
# pixels belong to the street. Native palette fitting changes only these pixels.
pave=bg[496:504,352:360].copy();lawn=bg[208:216,144:152].copy();ground=bg.copy()
for y,x in zip(*np.nonzero(removed)):
 ground[y,x]=lawn[(y-208)%8,(x-144)%8] if 136<=x<184 else pave[(y-496)%8,(x-352)%8]
fg[oldmask]=0;fg[newmask,:3]=bg[newmask];fg[newmask,3]=255
sections=json.loads((E/'sections.json').read_text());plans=[];records=[]
for sec in sections:
 n=sec['name'];x0,y0,x1,y1=sec['box']
 if not mask[y0*16:y1*16,x0*16:x1*16].any():continue
 ts=Tileset(G,n.lower(),n.lower());grid=np.fromfile(G/f'data/layouts/{n}/map.bin','<u2').reshape(y1-y0,x1-x0);newgrid=grid.copy();glyphs=[np.zeros((8,8),np.uint8)];lookup={glyphs[0].tobytes():0};blocks={};attrs={};assigned={}
 def entry(a,bank):
  key=a.tobytes()
  if key not in lookup:
   tid=len(glyphs);glyphs.append(a)
   for h in range(2):
    for v in range(2):lookup.setdefault(a[::-1 if v else 1,::-1 if h else 1].tobytes(),tid|h<<10|v<<11)
  return lookup[key]|bank<<12
 for cy,cx in np.ndindex(grid.shape):
  y,x=(cy+y0)*16,(cx+x0)*16;mid=int(grid[cy,cx]&1023);es=ts.blocks[mid>=512][mid%512];aa=ts.attrs[mid>=512][mid%512];out=[];affected=mask[y:y+16,x:x+16].any()
  for layer in range(2):
   for q in range(4):
    e=es[layer*4+q];tid=e&1023;bank=e>>12;a=np.array(ts.tiles[tid>=512][tid%512],np.uint8).reshape(8,8)[::-1 if e&2048 else 1,::-1 if e&1024 else 1].copy();yy=y+q//2*8;xx=x+q%2*8;mm=mask[yy:yy+8,xx:xx+8]
    if mm.any():
     bottom=es[q];bb=bottom>>12;bt=bottom&1023;ba=np.array(ts.tiles[bt>=512][bt%512],np.uint8).reshape(8,8)[::-1 if bottom&2048 else 1,::-1 if bottom&1024 else 1];pal=np.array(ts.pals[bb>=6][bb],np.uint8)
     if layer==1:
      a[mm]=0;nm=newmask[yy:yy+8,xx:xx+8];a[nm]=ba[nm];bank=bb
     else:
      rm=removed[yy:yy+8,xx:xx+8].copy();qy,qx=np.indices((8,8));wx=qx+xx;wy=qy+yy;protected=((wx<124)&(wy<284))|((wx>=232)&(wx<248)&(wy<286))|((wx>=332)&(wx<352)&(wy>=376)&(wy<400))|((wx>=336)&(wx<344)&(wy>=384)&(wy<448))|((wx>=456)&(wx<480)&(wy>=376)&(wy<400));rm&=~protected;desired=ground[yy:yy+8,xx:xx+8].copy()
      if (352<=xx<456 or (xx==456 and yy>=400)) and yy>=384:
       # The central banners carried green source backing over street. Restore
       # the entire receiving quadrant with native paving, not a foliage palette.
       bank=1;pal=np.array(ts.pals[0][bank],np.uint8);desired=pave.copy();rm=np.ones((8,8),bool);removed[yy:yy+8,xx:xx+8]=True
      elif 152<=xx<176 and 280<=yy<304:
       bank=3;pal=np.array(ts.pals[0][bank],np.uint8);desired=lawn.copy();rm=np.ones((8,8),bool);removed[yy:yy+8,xx:xx+8]=True
      elif (216<=xx<232 or (xx==232 and yy>=288)) and 280<=yy<304:
       bank=1;pal=np.array(ts.pals[0][bank],np.uint8);desired=pave.copy();rm=np.ones((8,8),bool);removed[yy:yy+8,xx:xx+8]=True
      dist=((desired.astype(np.int32)[:,:,None]-pal.astype(np.int32)[None,None,1:])**2).sum(3);a[rm]=(dist.argmin(2)+1)[rm];bg[yy:yy+8,xx:xx+8][rm]=pal[a][rm]
     # Refit only the receiving ground quadrants. Original pole pixels are
     # protected separately; foreground contains the cleaned silhouette only.

    out.append(entry(a,bank))
  if affected:aa&=~0x3000;above[cy+y0,cx+x0]=True
  key=tuple(out)+(aa,)
  if key not in assigned:
   preferred=mid if mid not in blocks else next(i for i in range(1024) if i not in blocks);assigned[key]=preferred;blocks[preferred]=out;attrs[preferred]=aa
  newgrid[cy,cx]=(int(grid[cy,cx])&~1023)|assigned[key]
 assert np.array_equal(grid&0xfc00,newgrid&0xfc00)
 assert len(glyphs)<=1008,(n,len(glyphs));plans.append((n,glyphs,blocks,attrs,newgrid));records.append(dict(map=n,glyphs=len(glyphs),foreground_cells=int(sum(mask[y:y+16,x:x+16].any() for y in range(y0*16,y1*16,16) for x in range(x0*16,x1*16,16)))))
for n,glyphs,blocks,attrs,grid in plans:
 for part in range(2):
  p=G/f'data/tilesets/{"secondary" if part else "primary"}/{n.lower()}';start=part*512;count=512 if part==0 else max(1,len(glyphs)-512);im=Image.new('P',(128,((count+15)//16)*8));im.putpalette([c for i in range(256) for c in (i*17%256,)*3])
  for i in range(count):
   if start+i<len(glyphs):im.paste(Image.fromarray(glyphs[start+i]).convert('P'),(i%16*8,i//16*8))
  im.save(p/'tiles.png',bits=4);(p/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*blocks.get(i,[0]*8)) for i in range(start,start+512)));(p/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*[attrs.get(i,0x1000) for i in range(start,start+512)]))
 grid.tofile(G/f'data/layouts/{n}/map.bin');np.full((2,2),int(grid[0,0])|0xc00,'<u2').tofile(G/f'data/layouts/{n}/border.bin')
comp=bg.copy();m=fg[...,3]>0;comp[m]=fg[m,:3];assert np.array_equal(comp[~removed],before[~removed]),'Only removed ground contamination may change the displayed scene'
Image.fromarray((newmask*255).astype(np.uint8)).save(S/'flag-foreground-mask.png');Image.fromarray((removed*255).astype(np.uint8)).save(O/'removed-ground-mask.png')
Image.fromarray(bg).save(S/'native-ground.png');Image.fromarray(fg).save(S/'shared-foreground.png');np.save(S/'above.npy',above);Image.fromarray(fg).save(O/'foreground.png');Image.fromarray(comp).save(O/'native-map.png');(O/'native-edit.json').write_text(json.dumps(dict(baseline=BASE,sections=records,mask_pixels=int(mask.sum()),alpha_removed_pixels=int((oldmask&~newmask).sum()),receiving_ground_pixels=int(removed.sum()),retained_flag_pixels=int(newmask.sum()),outside_cleanup_RGB_errors=0,collision_elevation_changes=0,method='Remove grass/pavement from foreground alpha; restore local ground behind removed contamination; keep native cloth, ropes and physical supports'),indent=2)+'\n');print(records)
