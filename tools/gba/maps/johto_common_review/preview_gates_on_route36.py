"""Read-only placement preview using Route 36's authored ground and tree layers.

Reconstruct hidden scenery through the existing generator in a temporary output
folder. Stop before native packing or engine writes. Replace only the union of
old/new gate silhouettes in the independently decoded current map.
"""
from pathlib import Path
import sys,json,tempfile,shutil,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent))
from route36 import build,trace
from tiles import Tileset
from claude_cherrygrove import ground
OUT=ROOT/'gba/art/johto-common-review/gates/refinement-4/map-preview'
SOURCE=ROOT/'gba/art/route36/source'
class Captured(Exception):pass

def main(game):
 OUT.mkdir(exist_ok=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip()
 status=subprocess.check_output(['git','status','--porcelain'],cwd=game)
 grid=np.fromfile(game/'data/layouts/JohtoRoute36/map.bin','<u2')
 baseline=np.array(Tileset(game,'johto_route36','johto_route36').map_image(grid.tolist(),82).convert('RGB'))
 captured={}
 original_blit=build.native.MapCanvas.blit
 def blit(self,c,px,py,flip=False):
  if c.pal.bank not in (9,10):original_blit(self,c,px,py,flip)
 def capture(comp,packer,pals,grid,source_dir,**kwargs):
  mc=comp['canvas'];rgba,_=ground.paint(comp['cells']);rgb=rgba[:,:,:3].copy()
  for bank in np.unique(mc.bank):
   if bank<0:continue
   mask=mc.bank==bank;rgb[mask]=np.array(pals[int(bank)].gba(),np.uint8)[mc.idx[mask]]
  captured['background']=rgb
  raise Captured()
 with tempfile.TemporaryDirectory(prefix='johto-gate-preview-') as tmp:
  source=Path(tmp)/'source';source.mkdir();evidence=Path(tmp)/'evidence';evidence.mkdir()
  for name in ('approved-front-gate.png','generated-files.json','hgss-reference.png'):shutil.copy2(SOURCE/name,source/name)
  build.S=source;build.E=evidence;build.OUT=Path(tmp);trace.S=source;trace.E=evidence
  build.native.MapCanvas.blit=blit;build.layers.pack=capture
  try:build.main(game)
  except Captured:pass
  finally:build.native.MapCanvas.blit=original_blit
 assert 'background' in captured
 revised=baseline.copy();allowed=np.zeros(baseline.shape[:2],bool);placements=[]
 gates=json.loads((SOURCE/'features.json').read_text())['gates']
 for gate in gates:
  name='G01a' if gate['name']=='Alph gate' else 'G02'
  asset=Image.open(OUT.parent/(name+'.png')).convert('RGBA')
  old=Image.open(SOURCE/'materials'/('gate-front.png' if name=='G01a' else 'gate-side.png')).convert('RGBA')
  if gate['flip']:asset=asset.transpose(Image.Transpose.FLIP_LEFT_RIGHT);old=old.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  a=np.array(asset);o=np.array(old);x,y=[n*16 for n in gate['at']];h,w=a.shape[:2]
  union=(a[:,:,3]>0)|(o[:,:,3]>0);opaque=a[:,:,3]>0
  part=revised[y:y+h,x:x+w];bg=captured['background'][y:y+h,x:x+w]
  part[union]=bg[union];part[opaque]=a[opaque,:3];allowed[y:y+h,x:x+w]|=union
  assert np.array_equal(part[opaque],a[opaque,:3])
  placements.append({'name':gate['name'],'asset':name,'at':gate['at'],'mirrored':gate['flip']})
 assert np.array_equal(revised[~allowed],baseline[~allowed])
 assert subprocess.check_output(['git','status','--porcelain'],cwd=game)==status
 Image.fromarray(revised).save(OUT/'route36-full.png')
 Image.fromarray(revised).resize((2624,1024),Image.Resampling.NEAREST).save(OUT/'route36-full-2x.png')
 board=Image.new('RGB',(1200,554),(235,238,237));draw=ImageDraw.Draw(board);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
 for i,(label,box) in enumerate([('National Park gate',(0,112,192,336)),('Violet gate',(1120,208,1312,432)),('Alph gate',(832,288,1024,512))]):
  draw.text((i*400+16,16),label,font=font,fill=(24,36,38));crop=Image.fromarray(revised).crop(box).resize((384,448),Image.Resampling.NEAREST);board.paste(crop,(i*400+8,56))
 draw.text((16,518),'Map placement preview / approved gate art at native scale',font=font,fill=(24,36,38));board.save(OUT/'gate-close-ups.png')
 report={'engine_revision':head,'preview_only':True,'engine_changed':False,'runtime_tested':False,'placements':placements,'outside_gate_silhouettes_changed_pixels':0,'approved_gate_pixel_errors':0,'changed_pixels':int(np.any(baseline!=revised,2).sum()),'background':'Reconstructed original Route 36 ground and trees, with gate drawing disabled before packing; existing decoded map preserved outside gate silhouettes','integration_follow_up':'Restored side foundation row requires collision and doorway checks when adopted in engine.'}
 (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
