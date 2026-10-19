#!/usr/bin/env python3
"""Survey the actual HGSS Route 29 image on its own 16px grid."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/route29-hgss-blocks';S=OUT/'source';E=OUT/'evidence';W,H=98,34
COLORS={'P':[(224,200,128),(224,200,136),(216,184,128),(216,184,136),(184,168,128),(216,168,128),(216,168,136),(152,144,112)],'.':[(104,208,160),(104,200,160),(96,200,152),(96,192,144),(88,184,144),(88,176,136),(72,168,136),(104,216,160),(112,208,160)],'G':[(56,152,88),(40,136,80),(64,168,112),(32,112,80),(80,192,120),(32,120,88)],'T':[(64,56,40),(64,64,40),(72,72,48),(80,88,40),(88,104,32),(88,112,32),(96,120,32),(112,144,32),(120,152,32),(136,168,40)]}
FEATURES={'gate':{'x':50,'y':5,'width':5,'height':7,'door_front':[52,12],'reference_box_px':[804,44,74,121]},'houses':[],'divider_trees':[],'apricorns':[[21,13]],'signs':[{'at':[6,16]},{'at':[87,16]}],'flower_boxes':[[45,12,5,2],[43,25,3,1],[72,15,2,1],[88,15,2,1]],'ledges':[[15,16,4,1],[22,16,7,1],[14,20,5,1],[22,20,9,1],[31,24,5,1],[49,20,3,1],[53,24,4,1],[59,24,4,1],[68,24,10,1]],'walls':[[28,12,1,4],[13,18,1,3],[52,20,1,5],[77,18,1,7]]}
def trace():
 im=np.asarray(Image.open(S/'hgss-reference.png').convert('RGB'))[5:549,4:1572];scores={}
 for k,colors in COLORS.items():scores[k]=(((im.astype(np.int32)[...,None,:]-np.asarray(colors))**2).sum(3).min(2)<=144).reshape(H,16,W,16).mean((1,3))
 p=np.full((H,W),'T',dtype='<U1');confidence=np.zeros(p.shape)
 for y in range(H):
  for x in range(W):
   v={k:float(a[y,x]) for k,a in scores.items()}
   ch='P' if v['P']>.22 else 'G' if v['G']>.18 else 'T' if v['T']>.16 else '.' if v['.']>.12 else 'T';p[y,x]=ch;confidence[y,x]=v[ch]
 def rect(box,ch):x,y,w,h=box;p[y-2:y-2+h,x:x+w]=ch
 for box in FEATURES['ledges']:rect(box,'_')
 for box in FEATURES['walls']:rect(box,'#')
 g=FEATURES['gate'];rect([g['x'],g['y'],g['width'],g['height']],'H');x,y=g['door_front'];p[y-2,x]='.'
 for x,y in FEATURES['apricorns']:p[y-2,x]='A'
 for q in FEATURES['signs']:x,y=q['at'];p[y-2,x]='!'
 # Paths stop naturally at the HGSS borders; adapters are authored separately.
 (S/'blocks.txt').write_text('\n'.join(''.join(row) for row in p)+'\n');(S/'structures.json').write_text(json.dumps(FEATURES,indent=2)+'\n')
 ledger=[{'x':x,'source_y':y,'native_y':y+2,'type':str(p[y,x]),'reference_box':[4+x*16,5+y*16,16,16],'fraction':round(float(confidence[y,x]),3)} for y in range(H) for x in range(W)];(S/'block-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 grid=Image.fromarray(im);d=ImageDraw.Draw(grid)
 for x in range(W):d.line((x*16,0,x*16,H*16),fill=(180,180,180))
 for y in range(H):d.line((0,y*16,W*16,y*16),fill=(180,180,180))
 grid.save(E/'reference-grid.png');print('Surveyed',W*H,'source cells')
if __name__=='__main__':trace()
