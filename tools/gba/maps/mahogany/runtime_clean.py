"""Exercise the current clean native revision, using the existing mGBA harness.

Includes every new entrance/return, ledges, signs, roof/wall occlusion,
Cherrygrove regression, ordinary flash write, fresh-process load and Continue.
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import runtime_convert as R

ROOT=HERE.parents[3]
CITY=R.CITY

def setup():
    old=R.STEPS;new=[];i=0
    # These four triples formerly proved an unfinished door was blocked. They
    # are replaced below by actual walking entry/return checks, not discarded.
    doors={(11,24),(16,15),(25,15),(12,6)}
    while i<len(old):
        s=old[i]
        if s[0]=='go' and s[1]==CITY and tuple(s[2:4]) in doors and i+2<len(old) and old[i+1]==('north',1,None) and old[i+2][0]=='at':
            i+=3;continue
        new.append(s);i+=1
    additions=[]
    for name,mid,(x,y),(ix,iy) in [('souvenir-shop',46,(16,14),(3,7)),('east-house',47,(25,14),(3,8)),('gym-lobby',48,(11,23),(5,9)),('route43-gate',49,(12,5),(3,8))]:
        additions += [('go',CITY,x,y+1),('north',1,None),('wait',400),('map',mid,name+'-entry'),('shot',name+'-interior'),
                      ('east',0 if mid==48 else 2,None),('north',5 if mid==48 else 3,None),('at',mid,5,4 if mid==48 or mid==46 else 5),('shot',name+'-interior-room'),
                      ('go',mid,ix,iy-1),('south',2,None),('wait',400),('at',CITY,x,y+1),('shot',name+'-return')]
    # Second visible gate entrance must also return at its own matching cell.
    additions += [('go',CITY,13,6),('north',1,None),('wait',400),('map',49,'gate-right-entry'),
                  ('go',49,4,7),('south',2,None),('wait',400),('at',CITY,13,6),('shot','gate-right-return')]
    R.STEPS=new+additions
    original_body=R.body
    def body():
        s=original_body()
        for name,x,y in [('center',22,23),('shop',16,14),('house',25,14),('gym',11,23)]:
            s+=f'\n go({CITY},{x},{y+1}); for(int t=0;t<90;t++){{frames(1,t<20?UP:0);char tag[80];sprintf(tag,"anim-{name}-%03d",t);screenshot(out,tag);}} frames(300,0);'
        return s
    R.body=body
    native=ROOT/'gba/art/mahogany-town/evidence/clean/native.png'
    R.expected=lambda:R.padded(np.array(Image.open(native).convert('RGB')).astype(np.int32)>>3,R.BORDER)
    original=R.check_frames
    def check_frames(out,game,phases):
        # The existing comparison assumes an outdoor camera. Interior screenshots
        # are separately inspected and exported through Porymap.
        frames=original(out,game,phases)
        assert not any(f['mismatched_map_layer_pixels'] for f in frames), 'Native background parity failed'
        return frames
    R.check_frames=check_frames

if __name__=='__main__':
    setup()
    R.main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
