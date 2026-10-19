"""Complete rock surfaces occluded by HGSS trees, before placing any foliage.

These are receiving surfaces, not tree-shaped masks. Each repair spans a whole
ledge/face between visible reference anchors. Real terrace levels and the two
timber openings remain outside these repairs.
"""
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt

def rebuild(bg,rock,wall,art,reference):
 h,w=wall.shape;Y,X=np.indices((h,w));sx,sy=X-64,Y-16
 scope=np.zeros_like(wall);ledger=[];original=rock.copy()
 grass=art['grass'][sy%16,sx%16];sand=art['sand'][sy%16,sx%16]
 def area(box):
  x0,y0,x1,y1=box;return (sx>=x0)&(sx<x1)&(sy>=y0)&(sy<y1)
 def surface(name,box,donor,cut=None,reference_donor=False):
  m=area(box)
  if cut:
   mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([(x+64,y+16) for x,y in cut],fill=255);m&=np.array(mask)>0
  x0,y0,x1,y1=box;dx,dy,dr,db=donor
  tile=original[dy+16:db+16,dx+64:dr+64].copy()
  if reference_donor:
   palette=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.int32)
   v=reference[dy:db,dx:dr].astype(np.int32);tile[...,:3]=palette[np.argmin(((v[:,:,None]-palette)**2).sum(3),2)];tile[...,3]=255
  missing=tile[...,3]==0
  assert missing.mean()<.2,(name,'donor is not an internal face')
  if missing.any():
   _,near=distance_transform_edt(missing,return_indices=True);tile[missing]=tile[near[0][missing],near[1][missing]]
  q=tile[(sy[m]-y0)%(db-dy),(sx[m]-x0)%(dr-dx)]
  # An unobscured internal face donor is opaque across its full rectangle.
  assert np.all(q[...,3]==255),(name,'donor has an opening')
  rock[m]=q;wall[m]=True;bg[m]=q;scope[m]=True
  ledger.append(dict(name=name,box=list(box),texture_donor=list(donor),donor_kind='unobscured HGSS face converted directly to RGB5' if reference_donor else 'existing native same-facing stone',outline=cut,material='same-facing stone',authority='straight continuation between HGSS-visible face anchors; original tree silhouette discarded'))
 def lawn(name,box,material):
  m=area(box);wall[m]=False;rock[m]=0;receiving=sand if material=='sand' else art['water'][sy%32,sx%32] if material=='water' else grass;bg[m]=receiving[m];scope[m]=True
  ledger.append(dict(name=name,box=list(box),material=material,authority='complete connected receiving shelf; not a crown-shaped replacement'))
 def capped_front(name,box,donor):
  x0,y0,x1,y1=box;dx,dy,dr,db=donor;zone=area(box)
  palette=np.array([(88,56,32),(112,72,40),(136,88,48),(152,104,56),(176,128,72),(192,152,96),(216,184,120)],np.int32)
  tile=reference[dy:db,dx:dr].astype(np.int32);warm=(tile[...,0]>tile[...,1]+4)&(tile[...,0]>tile[...,2]+4)
  warm[8:]=True
  tex=palette[np.argmin(((tile[:,:,None]-palette)**2).sum(3),2)].astype(np.uint8)
  yy,xx=sy[zone]-y0,sx[zone]-x0;inside=warm[yy%(db-dy),xx%(dr-dx)]
  # The face returns through a small rounded tip, rather than ending as an
  # uncapped vertical cut. The source's top lip still governs its turf contact.
  inset=np.maximum(0,4-np.minimum(yy,y1-y0-1-yy));inside&=(xx>=inset)&(xx<x1-x0-inset)
  q=np.zeros((int(zone.sum()),4),np.uint8);q[inside,:3]=tex[yy[inside]%(db-dy),xx[inside]%(dr-dx)];q[inside,3]=255
  wall[zone]=inside;rock[zone]=q;bg[zone]=grass[zone];bg[zone]=np.where(inside[:,None],q,bg[zone]);scope[zone]=True
  ledger.append(dict(name=name,box=list(box),texture_donor=list(donor),material='stone front with turf lip and rounded end returns',authority='HGSS unobscured same-facing course, rebuilt across original canopy occlusion',geometric_scaling=False))
 # Reconstruct the complete receiving surfaces, not isolated circular bites.
 # Use complete rectangular courses between reference anchors; turn endpoints
 # are bounded by the original visible side faces.
 surface('north high lip behind first lower row',(528,80,560,96),(704,584,736,600))
 lawn('residential shelf top',(512,144,624,152),'grass')
 capped_front('continuous capped residential upper face',(512,152,624,176),(560,152,592,176))
 capped_front('continuous capped residential lower face',(512,176,624,200),(560,176,592,200))
 # East coast: two small turf shelves between complete retaining faces. Clear
 # the entire former occluded area before drawing the landings and their faces.
 lawn('upper coastal landing',(840,240,904,280),'grass')
 lawn('lower coastal landing',(840,280,928,336),'grass')
 surface('high east face behind both coastal shelves',(824,256,840,384),(832,480,848,512))
 surface('rounded upper end of high east face',(824,248,840,264),(832,480,848,512),[(824,256),(827,252),(832,250),(836,252),(839,256),(839,263),(824,263)])
 capped_front('upper landing capped front',(848,280,904,304),(704,576,736,600))
 surface('outer three-course face completion',(904,280,936,304),(976,280,1008,304))
 surface('lower outer landing east face',(928,304,936,344),(888,336,896,352))
 surface('lower outer landing front',(864,328,928,352),(704,584,736,608),[(864,328),(927,328),(927,347),(923,351),(864,351)])
 surface('inner landing front',(840,336,864,352),(704,584,736,600))
 # Fresh reference inspection reveals a COMPLETE planted shelf, x848..888,
 # with a sand pocket north of it. The previous trace lost its outer face and
 # inset the shore by about 24px; extracting tree silhouettes cannot repair it.
 lawn('retire complete former lower coast assembly',(832,384,904,576),'water')
 surface('continuous high eastern face',(832,384,848,576),(832,400,848,416),reference_donor=True)
 lawn('northern sand pocket',(848,384,888,416),'sand')
 lawn('complete planted coastal shelf',(848,416,888,552),'grass')
 surface('planted shelf rounded east return',(888,416,904,568),(888,424,904,448),[(888,416),(899,416),(903,420),(903,559),(899,567),(888,567)],reference_donor=True)
 surface('planted shelf full south cap and face',(848,552,888,568),(856,552,888,568),reference_donor=True)
 surface('planted shelf rounded shore toe',(848,568,904,576),(856,568,888,576),[(848,568),(899,568),(899,571),(895,575),(848,575)],reference_donor=True)
 return scope,ledger
