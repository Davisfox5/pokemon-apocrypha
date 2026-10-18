"""Registered HGSS / previous / current native review, with per-cell coverage.

Source overview registration is image-derived, not decoded DS collision data.
The terrain authoring tool is regional_rocks.py; this file never edits the engine.
"""
from pathlib import Path
import sys, json, csv, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tools/gba/maps'))
from johto_common.regional_rocks import load, P, STONE
A = ROOT/'gba/art/johto-common/rocks/hgss-placement-audit'
S = A/'source'
V = A/'review'
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)
refs = {
 'CherrygroveRoute29Approach': (ROOT/'gba/art/claude-routes/references/route29-hgss.png', (4,5), (0,32), (98,34)),
 'CherrygroveRoute30Approach': (ROOT/'gba/art/route30-hgss-blocks/source/hgss-reference.png', (6,4), (0,0), (35,74)),
 'JohtoRoute31': (ROOT/'gba/art/hgss-connections/references/route31-hgss.png', (0,0), (0,0), (63,30)),
 'JohtoRoute32': (S/'route32-hgss-blocks/hgss-reference.png', (0,0), (16,16), (30,125)),
}
configs = json.loads((P/'source/inputs.json').read_text())
summary = []
for c in configs:
 n = c['map']; old = Image.open(S/(n+'-previous.png')).convert('RGB')
 current = Image.open(P/'review'/(n+'-native.png')).convert('RGB')
 t,g,l,b,e,attrs,original = load(c, Path(c['baseline']))
 now = np.asarray(current); before = np.asarray(old)
 diff = np.any(now != before, 2)
 cells = diff.reshape(g.shape[0],16,g.shape[1],16).any((1,3))
 scope = np.zeros(g.shape, bool)
 material = np.full(g.shape, 'outside rock audit', dtype=object)
 if n == 'CherrygroveRoute29Approach':
  structure = json.loads((S/'route29-hgss-blocks/structures.json').read_text())
  for typ in ['walls','ledges']:
   for x,y,w,h in structure[typ]:scope[y:y+h,x:x+w]=True;material[y:y+h,x:x+w]=typ
  scope[30:33,10:98]=True;material[30:33,10:98]='approved coast adaptation'
 elif n == 'CherrygroveRoute30Approach':
  plan=np.load(ROOT/'gba/art/route30-hgss-blocks/source/plan.npy')
  for symbol,label in [('#','retained cliff'),('R','removed forest rock filler'),('_','hop ledge'),('S','stairs and shoulders')]:
   scope[plan==symbol]=True;material[plan==symbol]=label
  rock=(b==8)&(original[:,:,0]>original[:,:,1]);q=rock.reshape(g.shape[0],16,g.shape[1],16).any((1,3));scope|=q
  material[q&(material=='outside rock audit')]='rock behind foreground / adapter'
 elif n == 'JohtoRoute31':
  scope[3:30,33:35]=True;material[3:30,33:35]='divider and stair shoulders'
  scope[28:30,35:]=True;material[28:30,35:]='southern face / route connector'
  scope[:14,44:]=True;material[:14,44:]='stepped mountain, tops, arch and foreground'
  low=(attrs&255)==59;scope|=low;material[low]='hop ledge'
 elif n == 'JohtoRoute32':
  plan=np.load(P/'source/route32/refined-plan.npy');scope=plan=='R';material[scope]='rock top or registered face'
 else:
  scope[7:10,:38]=True;material[7:10,:38]='approved expanded coastal ridge'
 with (A/(n+'-cells.csv')).open('w') as f:
  writer=csv.writer(f);writer.writerow(['x','y','material','changed_from_previous','collision_elevation','behavior','reference_note'])
  for y,x in np.argwhere(scope):
   note='registered overview; occlusion is not an exact-match claim'
   if n=='CherrygroveCity' or 'adaptation' in material[y,x]:note='approved adaptation; no 1:1 HGSS placement claim'
   if n=='CherrygroveRoute30Approach' and y>=74:note='approved 12-row Cherrygrove adapter'
   writer.writerow([x,y,material[y,x],bool(cells[y,x]),int(g[y,x]>>10),int(attrs[y,x]),note])
 residual = None
 if n in ['CherrygroveRoute29Approach','CherrygroveRoute30Approach','JohtoRoute31']:
  legacy=(b==8)&(original[:,:,0]>original[:,:,1]);residual=int((legacy&np.all(now==original[:,:,:3],2)).sum())
  assert residual==0,(n,residual)
  gray=(b==8)&(original[:,:,0]==original[:,:,1])&(original[:,:,1]==original[:,:,2])
  assert np.array_equal(now[gray],original[gray,:3]),(n,'stair tread pixels changed')
 registered = Image.new('RGB', current.size, '#354148')
 pages=[]
 if n in refs:
  path,origin,offset,size=refs[n];source=Image.open(path).convert('RGB')
  registered.paste(source.crop((origin[0],origin[1],origin[0]+size[0]*16,origin[1]+size[1]*16)),offset)
  # Full source/native grids: every square in the registered range is visible.
  tilew=35 if n=='CherrygroveRoute30Approach' else 32
  tileh=16
  for y in range(0,g.shape[0],tileh):
   for x in range(0,g.shape[1],tilew):
    if not scope[y:y+tileh,x:x+tilew].any():continue
    w=min(tilew,g.shape[1]-x);h=min(tileh,g.shape[0]-y)
    panel_width=max(w*16+20,270)
    board=Image.new('RGB',(3*panel_width,h*16+48),'#172329');d=ImageDraw.Draw(board)
    for i,(im,title) in enumerate([(registered,'HGSS registered'),(old,'Previous native'),(current,'Corrected native')]):
     ox=i*panel_width+10;d.text((ox,5),f'{title}: x{x}-{x+w-1}, y{y}-{y+h-1}',font=font,fill='white')
     piece=im.crop((x*16,y*16,(x+w)*16,(y+h)*16));board.paste(piece,(ox,28))
     for xx in range(w+1):d.line((ox+xx*16,28,ox+xx*16,28+h*16),fill=(76,100,102),width=1)
     for yy in range(h+1):d.line((ox,28+yy*16,ox+w*16,28+yy*16),fill=(76,100,102),width=1)
    name=f'{n}-x{x:02}-y{y:03}.png';board.save(V/name);pages.append(name)
  registered.save(V/(n+'-registered-reference.png'))
  refinfo=dict(file=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),origin=origin,native_pixel_offset=offset,source_cells=size)
 else:refinfo=dict(note='Approved expanded Cherrygrove composition; original HGSS is not a coordinate-equivalent map')
 summary.append(dict(map=n,changed_cells_from_previous=int(cells.sum()),scope_cells=int(scope.sum()),unchanged_legacy_colored_rock_pixels=residual,reference=refinfo,pages=pages,visual_review='separate findings receipt required'))
(A/'coverage.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['pages','reference']} for r in summary],indent=2))
