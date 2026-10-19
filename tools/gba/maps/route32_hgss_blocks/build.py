"""Author a new Route32 from HGSS pixel-coordinate traces; never reads an older route layout."""
from pathlib import Path
import sys,json,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE))
from tiles import Tileset,palette
from claude_cherrygrove.pixel import Canvas,Palette
from claude_cherrygrove import build as native,ground
from claude_routes import build as packing
import ground_native,layers,preservation
ROOT=HERE.parents[3];OUT=ROOT/'gba/art/route32-hgss-blocks';S=OUT/'source';E=OUT/'evidence';W,H=32,128
# All coordinates below are measured on the original 490x2000 HGSS overview.
TRACES={
 'path': [[(90,140),(302,140),(302,175),(90,175)],[(225,330),(321,330),(321,359),(285,359),(285,423),(220,423)],[(354,350),(418,350),(418,430),(370,430),(370,394),(354,394)],[(308,616),(358,616),(358,818),(293,818),(293,853),(138,853),(138,938),(91,938),(91,824),(230,824),(230,778),(315,778)],[(92,926),(138,926),(138,996),(105,996),(105,1005),(25,1005),(25,964),(92,964)],[(87,1386),(134,1386),(134,1450),(194,1450),(194,1486),(340,1486),(340,1400),(350,1400),(350,1533),(185,1533),(185,1700),(264,1700),(264,1736),(353,1736),(353,1805),(337,1805),(337,1841),(353,1841),(353,1980),(180,1980),(180,1880),(245,1880),(245,1770),(138,1770),(138,1533),(171,1533),(171,1500),(135,1500),(135,1458),(86,1458)]],
 'cliff': [[(0,280),(79,280),(79,406),(0,406)],[(218,260),(368,260),(368,299),(420,299),(420,356),(270,356),(270,331),(184,331),(184,283),(218,283)],[(272,396),(361,396),(361,548),(260,548),(260,423),(272,423)],[(187,666),(302,666),(302,774),(187,774)],[(359,616),(388,616),(388,572),(490,572),(490,946),(140,946),(140,850),(280,850),(280,813),(359,813)],[(137,998),(168,998),(168,1230),(235,1230),(235,1403),(79,1403),(79,1380),(199,1380),(199,1260),(137,1260)],[(58,1380),(86,1380),(86,1617),(0,1617),(0,1590),(58,1590)],[(0,1710),(145,1710),(145,1759),(273,1759),(273,1870),(182,1870),(182,2000),(0,2000)]],
 'water': [[(170,950),(490,950),(490,2000),(425,2000),(425,1725),(398,1725),(398,1430),(362,1430),(362,1260),(233,1260),(233,1220),(168,1220)]],
 'grass': [[(404,112),(464,112),(464,256),(432,256),(432,215),(404,215)],[(368,427),(432,427),(432,395),(470,395),(470,515),(432,515),(432,545),(464,545),(464,617),(378,617),(378,600),(346,600),(346,629),(276,629),(276,581),(303,581),(303,546),(368,546)],[(88,680),(120,680),(120,650),(185,650),(185,775),(234,775),(234,817),(88,817)],[(168,946),(314,946),(314,996),(168,996)],[(71,1110),(137,1110),(137,1150),(106,1150),(106,1190),(201,1190),(201,1380),(134,1380),(134,1327),(49,1327),(49,1294),(83,1294),(83,1263),(36,1263),(36,1224),(70,1224)],[(27,1378),(57,1378),(57,1488),(27,1488)],[(86,1432),(195,1432),(195,1501),(168,1501),(168,1530),(86,1530)]],
 'dock': [[(265,996),(310,996),(310,1294),(265,1294)],[(197,1159),(310,1159),(310,1208),(197,1208)],[(265,1249),(357,1249),(357,1294),(265,1294)],[(312,1284),(357,1284),(357,1400),(312,1400)]],
 'stairs': [[(130,930),(162,930),(162,978),(130,978)],[(86,1380),(134,1380),(134,1428),(86,1428)]],
}
def masks():
 result={}
 for name,polys in TRACES.items():
  im=Image.new('1',(W,H));d=ImageDraw.Draw(im)
  for poly in polys:d.polygon([(round(x/16)+1,round(y/16)+1) for x,y in poly],fill=1)
  result[name]=np.asarray(im,bool)
 return result

def main(game):
 preservation.check(game,S)
 S.mkdir(exist_ok=True,parents=True);E.mkdir(exist_ok=True,parents=True)
 ref=ROOT/'gba/art/violet-route-references/route32-hgss.png';shutil.copyfile(ref,S/'hgss-reference.png')
 (S/'trace.json').write_text(json.dumps({'original_size':[490,2000],'native_size':[W,H],'registration':'16px source cell, offset +1,+1; padded forest boundaries; source projection is not claimed to be decoded DS collision','polygons_px':TRACES},indent=2)+'\n')
 cg=game/'data/tilesets';pals={i:Palette(i,palette(cg/f'{"primary" if i<6 else "secondary"}/cherrygrove/palettes/{i:02}.pal')[1:],[f'c{j}' for j in range(15)]) for i in range(16)}
 a={}
 def indexed(name,bank):
  im=Image.open(ROOT/f'gba/art/cherrygrove-synthesis/refined/{name}.png');c=Canvas(im.width,im.height,pals[bank]);c.px=np.asarray(im).copy();return c
 a['tree']=indexed('tree',3)
 def convert(name,rgba,bank):
  rgba=np.asarray(rgba);c=Canvas(rgba.shape[1],rgba.shape[0],pals[bank]);ok=rgba[...,3]>0;pp=np.asarray(pals[bank].gba()[1:],int);c.px[ok]=((rgba[ok,:3].astype(int)[:,None]-pp)**2).sum(2).argmin(1)+1;a[name]=c;return c
 # Owner-selected canonical Violet Center: exact pixels and alpha, no new reconstruction.
 center_ref=np.asarray(Image.open(S/'shared-art/violet-pokemon-center.png').convert('RGBA'));center=convert('center',center_ref,8);assert np.array_equal(center.to_rgba(),center_ref), 'Canonical Center colors/alpha changed'
 # Reuse the separately Porytiles-validated accepted HGSS TEX0 family.
 old=S/'shared-art'
 pals[12]=Palette(12,[(32,112,80),(32,120,88),(40,136,80),(56,152,88),(64,168,112),(80,192,120),(104,208,152),(104,200,152),(88,176,136),(96,192,144)],[f'g{i}' for i in range(10)])
 for f in (old/'materials').glob('grass-*.png'):convert(f.stem,Image.open(f).convert('RGBA'),12)
 shutil.copytree(old/'porytiles-native',S/'porytiles-native',dirs_exist_ok=True)
 # Native Emerald cliff family: all nine edges/corners, not repeated cliff faces.
 donor=Tileset(game);ids=list(range(0x70,0x79))+[0xaf,0xcf,0xd5,0x87,0xd6,0xa6,0xa7,0xa8,0x7c]
 pics={m:np.asarray(donor.render(m)) for m in ids};colors=sorted({tuple(map(int,c)) for pic in pics.values() for c in pic.reshape(-1,3) if not(c[1]>int(c[0])+15 and c[1]>int(c[2])+15)})
 # Donor native cliff palette already fits a single bank.
 if len(colors)>15:colors=colors[:15]
 pals[11]=Palette(11,colors,[f'e{i}' for i in range(len(colors))])
 for m,pic in pics.items():
  rgba=np.dstack([pic,np.full((16,16),255,np.uint8)]);rgba[...,3][(pic[...,1].astype(int)>pic[...,0].astype(int)+15)&(pic[...,1].astype(int)>pic[...,2].astype(int)+15)]=0;convert('emerald-'+str(m),rgba,11)
 # Missing broad plateau surface: retain donor soil colors but remove corner-sized motifs from the interior.
 pp=np.asarray(pals[11].gba(),int);base=int(((pp-[222,180,164])**2).sum(1).argmin());shade=int(((pp-[189,148,139])**2).sum(1).argmin());dark=int(((pp-[156,115,115])**2).sum(1).argmin())
 a['emerald-113'].px[:]=base
 for xx,yy in [(2,3),(10,7),(6,13)]:
  a['emerald-113'].px[yy,xx:xx+3]=shade;a['emerald-113'].px[yy+1,xx+1:xx+3]=shade;a['emerald-113'].px[yy+1,xx]=dark
 # Native wood: source dock top from an unoccupied HGSS board section. Whole repeating 8px quarters.
 raw=np.asarray(Image.open(ref).convert('RGBA'));wood=raw[1020:1052,271:303].copy()
 woodcolors=[(72,64,40),(104,88,56),(128,112,72),(152,128,88),(168,144,96),(184,160,112),(200,176,128)]
 pals[9]=Palette(9,woodcolors,[f'w{i}' for i in range(7)]);convert('boards',wood[:16,:16],9)
 # Rail overpass, source sampled clean central span; three native courses and end supports.
 rail=raw[1040:1104,145:161].copy();railcolors=[(40,40,48),(56,56,64),(72,72,80),(88,88,96),(112,112,120),(136,144,144),(160,168,168),(184,192,192),(208,216,216),(224,232,232),(8,64,72),(16,80,88),(24,104,96)]
 pals[10]=Palette(10,railcolors,[f'r{i}' for i in range(13)])
 for i in range(4):convert('rail-'+str(i),rail[i*16:(i+1)*16],10)
 # HGSS coastal boulder family: literal native-scale crop, gray/foam mask, rail bank's gray ramp.
 rock=raw[1105:1137,396:428].copy();rr=rock[...,:3].astype(int);rock[...,3]=((np.abs(rr[...,0]-rr[...,1])<25)&(np.abs(rr[...,1]-rr[...,2])<25)&(rr[...,0]>65))*255;convert('coastal-rock',rock,10)
 # NW original Ruins gate is clipped in the source; preserve its real visible silhouette.
 gate=raw[80:176,0:96].copy();mask=Image.new('L',(96,96));d=ImageDraw.Draw(mask);d.polygon([(0,7),(72,7),(78,16),(78,31),(88,32),(88,53),(95,57),(95,94),(0,94)],fill=255);gate[...,3]=np.asarray(mask)
 gatecolors=[(32,32,32),(8,112,88),(24,128,112),(32,144,136),(48,160,152),(56,176,176),(112,96,64),(128,104,80),(176,160,128),(192,168,144),(112,192,224),(144,216,248),(88,96,88),(136,136,136),(176,176,176)]
 pals[6]=Palette(6,gatecolors,[f'h{i}' for i in range(15)]);convert('gate',gate,6)
 m=masks();src0=np.asarray(Image.open(ref).convert('RGB'),int);blue=(src0[...,2]>src0[...,1]+25)&(src0[...,2]>src0[...,0]+40);wm=np.zeros((H,W),bool);wm[1:126,1:31]=blue[:2000,:480].reshape(125,16,30,16).mean((1,3))>.25;wood0=(src0[...,1]>src0[...,0])&(src0[...,2]<80);wscore=wood0[:2000,:480].reshape(125,16,30,16).mean((1,3))
 for yy in range(60,126):
  xs=np.flatnonzero(wm[yy,12:31])+12
  if len(xs):
   for xx in range(int(xs.min()),32):
    if xx==31 or wscore[yy-1,xx-1]<.2 or yy<86:wm[yy,xx]=True
 m['water']=wm
 p=np.full((H,W),'.',dtype='<U1')
 for name,ch in [('water','W'),('path','P'),('grass','G'),('cliff','R'),('dock','D'),('stairs','S')]:p[m[name]]=ch
 # The cliff opening south of the northern terraces remains source lawn/path.
 p[23:26,21:26]='P';p[27,24:27]='_'
 p[44:46,21]='P';p[46,21]='_'
 p[88:92,20:23]='P'
 p[104:110,18:24]='P'
 p[117:120,12:18]='P'
 p[66:70,12:]='W';p[66:70,18:21]='D'
 p[6:12,1:7]='.';p[103:109,17:24]='.'
 # Forest measured from the source colors, then fitted as complete 2x3 crowns / 2x2 ground footprints.
 src=np.asarray(Image.open(ref).convert('RGB'),int);woods=(src[...,1]>src[...,0])&(src[...,2]<80)
 score=np.zeros((H,W));score[1:126,1:31]=woods[:2000,:480].reshape(125,16,30,16).mean((1,3));score[:,0]=score[:,-1]=1;score[:2]=1;score[-2:]=1
 forest=(score>.35)&(p=='.');reserved=np.zeros((H,W),bool);reserved[5:12,1:7]=True;reserved[103:111,17:25]=True;reserved[:8,22:26]=True
 mc=native.MapCanvas(W,H);fore=native.MapCanvas(W,H);cells=np.full((H,W),ground.GRASS,np.int8);cells[p=='P']=ground.PATH;cells[p=='W']=ground.SEA
 solid=np.isin(p,list('RW'));beh=np.zeros((H,W),np.uint8);beh[p=='W']=21
 def put(c,x,y,foreground=False):
  mc.blit(c,x*16,y*16)
  if foreground:fore.blit(c,x*16,y*16)
 for y in range(H):
  for x in range(W):
   ch=p[y,x]
   if ch=='G':
    ns=''.join(str(int(0<=xx<W and 0<=yy<H and p[yy,xx]=='G')) for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]);put(a['grass-'+ns],x,y);beh[y,x]=2
   elif ch=='R':
    n=y>0 and p[y-1,x]=='R';s=y+1<H and p[y+1,x]=='R';w=x>0 and p[y,x-1]=='R';e=x+1<W and p[y,x+1]=='R';row=1 if n and s else (0 if not n else 2);col=1 if w and e else(0 if not w else 2);put(a['emerald-'+str((0x71 if row==1 and col==1 else (0x7c if row==2 and col==1 else 0x70+row*3+col)))],x,y)
   elif ch=='D':
    c=Canvas(16,16,pals[9]);c.px=a['boards'].px.copy()
    for side,yy,xx in [('n',y-1,x),('s',y+1,x),('w',y,x-1),('e',y,x+1)]:
     if 0<=yy<H and 0<=xx<W and p[yy,xx] in 'DS':continue
     if side=='n':c.px[:2,:]=1;c.px[2,:]=2
     elif side=='s':c.px[-2:,:]=1;c.px[-3,:]=2
     elif side=='w':c.px[:,:2]=1;c.px[:,2]=2
     else:c.px[:,-2:]=1;c.px[:,-3]=2
    put(c,x,y)
   elif ch=='_':
    mid=0xd5 if x==0 or p[y,x-1]!='_' else 0xd6 if x+1==W or p[y,x+1]!='_' else 0x87;put(a['emerald-'+str(mid)],x,y);solid[y,x]=True;beh[y,x]=59
   elif ch=='S':put(a['emerald-'+str(0xcf)],x,y);solid[y,x]=False
 mc.background_bank=mc.bank.copy();mc.background_idx=mc.idx.copy()
 positions=[];occupied=np.zeros((H,W),bool)
 for y in range(0,H-2,2):
  for x in range(0,W-1,2):
   root=forest[y+1:y+3,x:x+2];area=p[y:y+3,x:x+2];ok=(root.mean()>=.5) and np.all(area=='.') and not reserved[y:y+3,x:x+2].any()
   if not ok:continue
   assert not occupied[y+1:y+3,x:x+2].any();occupied[y+1:y+3,x:x+2]=True;positions.append((x,y));put(a['tree'],x,y,True);solid[y+1:y+3,x:x+2]=True;mc.above[y,x:x+2]=True
 # Center positioned around original facade; enlargement is solely native 112px accepted asset footprint.
 convert('sign',Image.open(old/'materials/sign.png').convert('RGBA'),5)
 for x,y in [(16,8),(22,15),(20,122)]:
  put(a['sign'],x,y-1,True);solid[y,x]=True;beh[y,x]=29;mc.above[y-1,x]=True
 put(a['center'],17,103,True);solid[104:109,17:24]=True;mc.above[103:105,17:24]=True;solid[108,20]=False;beh[108,20]=105
 put(a['gate'],1,6,True);solid[7:12,1:7]=True;mc.above[6:8,1:7]=True
 # Rails are above the player on BG1; land and dock retain their real collision below.
 for y in range(66,70):
  for x in range(W):put(a['rail-'+str(y-66)],x,y,True);mc.above[y,x]=True
 # Original railway support on the eastern water: continuous native silhouette.
 support=Canvas(32,64,pals[10]);support.px[0:52,5:27]=11;support.px[0:52,8:24]=12;support.px[0:52,9:12]=13;support.px[52:59,3:29]=8;support.px[59:64,6:26]=6
 put(support,24,70,True);solid[73:74,24:26]=True;beh[73,24:26]=0;mc.above[70:73,24:26]=True
 # Original water boulders stay separate from the trees and walkway.
 for x,y in [(26,70),(26,73),(26,76),(25,79),(25,82),(27,82),(26,88),(27,91),(25,93),(25,96)]:
  if np.all(p[y:y+2,x:x+2]=='W'):
   put(a['coastal-rock'],x,y,True);solid[y:y+2,x:x+2]=True;beh[y:y+2,x:x+2]=0
 # The Union Cave opening is a native Emerald mouth within the southern face.
 for i,mid in enumerate([0xa6,0xa7]):put(a['emerald-'+str(mid)],13+i,116,True)
 solid[116,13:15]=False;beh[116,13:15]=97
 # Native boundary collision; north opening is Violet, south original rocky boundary.
 solid[:,0]=True;solid[:,-1]=True;solid[0]=True;solid[0,23:25]=False;solid[-1]=True
 mc.fore_bank=fore.bank;mc.fore_idx=fore.idx
 class Primary(packing.Primary):
  def __init__(self,*args):
   super().__init__(*args);self.lookup={}
   for tid in range(93,len(self.tiles)):self._index(tid,self.tiles[tid])
  def find(self,bank,arr):
   hit=self.lookup.get(arr.tobytes())
   if hit is None:return 0 if not arr.any() else None
   tid,hf,vf=hit;return tid|(hf<<10)|(vf<<11)
 primary=Primary(game,92,512);packer=packing.RoutePacker(pals,primary);ground_native.install(game,pals);grid=np.zeros((H,W),np.uint16)
 comp={'W':W,'H':H,'cells':cells,'solid':solid,'behavior':beh,'canvas':mc};report=layers.pack(comp,packer,pals,grid,S)
 assert max(packer.sec_tiles)<1008,('Door scratch VRAM exceeded',max(packer.sec_tiles))
 t=Tileset(game,'cherrygrove','cherrygrove');watermid=58
 for y,x in zip(*np.where(p=='W')):
  if (mc.fore_bank[y*16:(y+1)*16,x*16:(x+1)*16]>=0).any():
   mid=int(grid[y,x]&1023);top=packer.sec_blocks[mid][0][4:];grid[y,x]=packer.metatile(list(t.blocks[0][watermid][:4])+list(top),int(beh[y,x]))|0x1000|(0xc00 if beh[y,x]!=21 and solid[y,x] else 0)
  else:grid[y,x]=watermid|0x1000
 nt,nb=packing.write_route_tileset(game,'route32',packer,pals)
 folder=game/'data/layouts/JohtoRoute32';folder.mkdir(exist_ok=True);grid.astype('<u2').tofile(folder/'map.bin');border=grid[32:34,2:4].copy();border|=0xc00;border.tofile(folder/'border.bin')
 np.save(S/'solid.npy',solid);np.save(S/'plan.npy',p);(S/'blocks.txt').write_text('\n'.join(''.join(row) for row in p)+'\n')
 for name,c in a.items():Image.fromarray(c.to_rgba()).save(S/'materials'/f'{name}.png')
 (E/'assembly.json').write_text(json.dumps({'native_size':[W,H],'source_registration':[16,16,1,1],'whole_trees':positions,'illegal_tree_ground_overlaps':0,'tiles':nt,'metatiles':nb,'layers':report,'missing_endpoints':['full Violet City','Ruins of Alph','Union Cave interior'],'reference':'original HGSS Route32, not earlier Gen3 layout'},indent=2)+'\n')
 Tileset(game,'route32','cherrygrove').map_image(grid.ravel().tolist(),W).save(E/'native-map.png');preservation.record(game,S);print(nt,nb,len(positions))
if __name__=='__main__':main(Path(sys.argv[1]))
