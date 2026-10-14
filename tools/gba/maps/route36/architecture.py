"""Route 29 HGSS gate components, cleaned and reassembled for side entrances."""
import numpy as np
from PIL import Image,ImageDraw
from claude_routes import art
from claude_cherrygrove import banks

def create(pals,materials):
 raw=art.gate()
 # Exact source silhouette, retained at native scale. Ignore the surrounding
 # lawn and tree fragments; preserve the turquoise rain gutters and lower trim.
 Image.fromarray(raw).save(materials/'route29-gate-reference.png')
 front=np.zeros((128,112,4),np.uint8)
 # Original 144px bounding box: body between x24..120, y22..143.
 front[6:128]=raw[22:144,16:128]
 # Side variant: complete square hip roof retained, window frieze continues
 # across front while the west portal sits in the shaded side wall.
 side=front.copy()
 # Original southern doorway replaced with cream masonry and the same glass
 # band/awning vocabulary, repeated whole source sections (no resize).
 wall=(184,168,136,255);shadow=(104,88,64,255);light=(208,192,160,255)
 side[95:120,26:88]=wall;side[118:122,24:90]=shadow;side[116:118,26:88]=light
 # Recessed paired glazed bays use the existing source glazing strip.
 glazing=raw[91:98,36:104].copy()
 for x in [30,58]:
  side[98:105,x:x+24]=glazing[:7,:24];side[105:107,x:x+24]=shadow
  side[109:111,x:x+24]=light
 # Side passage starts exactly at the western movement cell x0,y7.
 # Strong lintel, recessed opening, shallow treads, two intact stone jambs.
 side[91:128,6:26]=shadow
 side[95:128,8:22]=(48,64,64,255)
 side[91:95,5:28]=light;side[95:122,24:28]=wall
 # East/west travel: riser lines run vertically across the side landing.
 side[122:128,28:]=0
 side[95:128,0:22]=(48,64,64,255)
 for x in range(0,12,4):
  side[108:128,x:x+2]=(176,176,152,255)
  side[108:128,x+2:x+4]=(104,112,104,255)
 side[95:108,0:5]=(56,80,72,255)
 # Teal side hood projects over the portal, based on the existing awning.
 side[85:90,2:28]=(48,160,152,255);side[89:92,2:28]=(24,120,112,255)
 bank=banks.Bank(9,'HGSS_ROUTE29_GATE_ARCHITECTURE','secondary')
 bank.add('gate-front',front).add('gate-side',side)
 assets=bank.build();pals[9]=bank.palette
 for name,c in assets.items():Image.fromarray(c.to_rgba()).save(materials/(name+'.png'))
 return assets
