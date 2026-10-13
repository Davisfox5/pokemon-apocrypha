"""Pixel ownership masks for HGSS imports; terrain never belongs to a prop.
Source RGB stays intact until the existing native palette conversion.
"""
import numpy as np
from PIL import Image


def house(ref):
    # Two pixels farther west than the earlier crop recover the outer eave.
    a=np.array(ref.crop((158,528,238,624)).convert('RGBA'))
    r,g,b=[a[:,:,i].astype(int) for i in range(3)]
    material=((b>g+8)&(r>g+8))|((r>=g)&(g>b+16))
    mask=np.zeros((96,80),bool)
    for y in range(66):
        # Roof/ridge colors define the exact stepped silhouette, not a coarse
        # polygon crossing the eaves. Limit the search to the known building.
        left,right=(28,42) if y<8 else (max(0,28-(y-8)*2),min(69,42+(y-8)*2))
        xs=np.flatnonzero(material[y,left:right])+left
        if len(xs):mask[y,xs[0]:xs[-1]+1]=True
    mask[64:86,6:64]=True
    # Ground exposed below the door/eaves is mint; wall and door greens are
    # darker, and the blue window glass has B > G, so neither is erased.
    ground=(g>r+30)&(g>b+15)&(b>r+20)
    mask&=~ground
    a[:,:,3]=mask*255
    return a


def bridge_post(ref):
    a=np.array(ref.crop((576,544,592,576)).convert('RGBA'))
    r,g,b=[a[:,:,i].astype(int) for i in range(3)]
    mask=np.zeros((32,16),bool)
    mask[4:8,6:10]=True
    mask[7:24,1:15]=True
    mask[24:30,3:13]=True
    # The original metal/stone shades are neutral or cool. The adjacent brown
    # path, green grass and cyan water fail this ownership test.
    neutral=(g>=r)&(g-r<=32)&(np.abs(g-b)<=24)
    a[:,:,3]=(mask&neutral)*255
    return a


def sign_mask(c):
    mask=np.zeros(c.px.shape,bool)
    mask[3:6,6:10]=True
    mask[6:16,1:16]=True
    mask[16:21,6:10]=True
    c.px[~mask]=0


def mart_sign_mask(c):
    # Remove the Mart roof fragment above the board, the facade below its
    # left edge and the extraneous ground pixels around the base of the pole.
    c.px[:6,:8]=0;c.px[:5,8:12]=0
    pole=c.px[28:58,13:16].copy()
    c.px[28:,:]=0;c.px[28:58,13:16]=pole
    c.px[27,:8]=0


def islet(ref):
    a=np.array(ref.crop((736,432,800,512)).convert('RGBA'))
    r,g,b=[a[:,:,i].astype(int) for i in range(3)]
    water=(b>g+15)&(b>140)&(r<110)
    # Preserve every original turf/cliff/canopy pixel. Only surrounding water
    # is transparent so the engine supplies its own matching lake texture.
    a[:,:,3]=(~water)*255
    return a
