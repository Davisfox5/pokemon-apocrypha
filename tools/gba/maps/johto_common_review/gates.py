"""Read-only gate inventory: extract existing pixels; never regenerate game art."""
from pathlib import Path
import argparse,base64,hashlib,io,json,subprocess,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
from claude_routes import art
P=ROOT/'gba/art';OUT=P/'johto-common-review/gates';OUT.mkdir(parents=True,exist_ok=True)

def read(p):return Image.open(P/p).convert('RGBA')
def native(game,name,secondary,width,primary='cherrygrove'):
 a=np.fromfile(game/f'data/layouts/{name}/map.bin','<u2')
 return Tileset(game,secondary,primary).map_image(a.tolist(),width).convert('RGBA')
def masked(im,box,mask):
 a=im.crop(box).copy();assert a.size==mask.size;a.putalpha(mask.getchannel('A'));return a

def main():
 ap=argparse.ArgumentParser();ap.add_argument('engine',type=Path);ap.add_argument('visual',type=Path);args=ap.parse_args();G=args.engine
 route29=native(G,'CherrygroveRoute29Approach','claude_route29',98)
 route31=native(G,'JohtoRoute31','route31',63)
 violet=native(G,'VioletCity','violet_city',80,'violet_city')
 route36=native(G,'JohtoRoute36','johto_route36',82,'johto_route36')
 rows=[]
 def item(id,family,title,orientation,status,usage,note,asset,scene,source,archive=False):
  box=asset.getbbox();assert box;asset=asset.crop(box)
  assert asset.width<=144 and asset.height<=144
  plate=Image.new('RGBA',(144,144));plate.alpha_composite(asset,((144-asset.width)//2,132-asset.height))
  plate.save(OUT/(id+'-asset.png'));scene.convert('RGB').save(OUT/(id+'-context.png'))
  def uri(im):
   b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
  rows.append(dict(id=id,family=family,title=title,orientation=orientation,status=status,usage=usage,note=note,source=source,archive=archive,visible_pixels=list(asset.size),asset=uri(plate),context=uri(scene),asset_file=id+'-asset.png',context_file=id+'-context.png',sha256=hashlib.sha256(asset.tobytes()).hexdigest()))
 def context(im,x,y):
  # Uniform 224x192 source pixels; edge padding is transparent, not invented terrain.
  b=Image.new('RGBA',(224,192));box=(x,y,x+224,y+192);crop=im.crop(box);b.alpha_composite(crop);return b
 item('G01a','G01','HGSS front gate / Route 36','North–south','Front artwork accepted','Route 36 → Ruins of Alph','Full teal hip roof, projecting front canopy and stair entrance. Regional standard not yet selected.',read('route36/source/materials/gate-front.png'),context(route36,51*16,20*16),['route36/source/materials/gate-front.png','route36/evidence/native-overview.png'])
 raw=Image.fromarray(art.gate())
 for id,label,path,status in [('G01b','HGSS front gate / Claude Route 29','claude-routes/route29-overview.png','Earlier build'),('G01c','HGSS front gate / Route 29 slices','apoc-route29/route29-overview.png','Alternate Route 29 build')]:
  im=read(path);offset=2 if id=='G01c' else 0;asset=masked(im,(48*16,(1+offset)*16,57*16,(10+offset)*16),raw)
  item(id,'G01',label,'North–south',status,'Route 29 → Route 46','Same HGSS donor, different native palette and source cleanup. Compare windows, trim and stair tones.',asset,context(im,46*16,0),[path,'tools/gba/maps/claude_routes/art.py::gate'])
 item('G02','G02','HGSS side gate / Route 36','East–west','Latest correction; awaiting review','Route 36 → National Park and Violet','Actual side-facing HGSS architecture; east gate uses a mirrored copy. Window band has no front doorway.',read('route36/source/materials/gate-side.png'),context(route36,0,6*16),['route36/source/materials/gate-side.png','route36/evidence/native-overview.png'])
 item('G03','G03','Geometric side gate / Violet','East–west','Present in the Violet build','Violet west gate → Route 36','Earlier simplified roof and repeated wall modules. The two sides of the same connection currently use G03 and G02.',read('violet-city/source/preserved-west-gate.png'),context(violet,0,23*16),['violet-city/source/preserved-west-gate.png','violet-city/evidence/native-overview.png'])
 mask=read('cherrygrove-synthesis/refined/gable.png');asset=masked(route31,(32,176,112,256),mask)
 item('G04a','G04','Red gable used as a gate','Front entrance','Present in the route build','Route 29 → Route 46; Route 31 → Violet','Cherrygrove house shell serving as a gate. Front entrance does not depict east–west passage.',asset,context(route31,0,7*16),['cherrygrove-synthesis/refined/gable.png','engine:JohtoRoute31 [2,11]'])
 item('G04b','G04','Red gable / earlier palette','Front entrance','Earlier build','Earlier Route 29 and Route 31 revisions','Same house family; older wall and door colors.',read('johto-native-refinement/native/gate.png'),context(read('johto-native-refinement/route31-overview.png'),0,7*16),['johto-native-refinement/native/gate.png','johto-native-refinement/route31-overview.png'])
 h=read('violet-city/source/materials/house.png');asset=masked(violet,(73*16,51*16,73*16+80,51*16+96),h)
 item('G05','G05','Violet purple gable used as a gate','Front entrance','Present in the Violet build','Violet east gate → Route 31','Violet house shell used for the gate. Shows a local house identity, not a matching regional gatehouse.',asset,context(violet,66*16,48*16),['violet-city/source/materials/house.png','engine:VioletCity [73,51]'])
 item('G06','G06','Clipped HGSS side gate','East–west silhouette','Superseded','Earlier Route 31 → Violet','Source crop is cut off on the west and retains ground near the side entrance.',read('johto-polish/native/gate-gba.png'),context(read('johto-polish/route31-overview.png'),0,7*16),['johto-polish/native/gate-gba.png','johto-polish/route31-overview.png'],True)
 def historical(ref,path):return Image.open(io.BytesIO(subprocess.check_output(['git','show',ref+':gba/art/'+path],cwd=ROOT))).convert('RGBA')
 rejected=historical('3cf4a9b','route36/source/materials/gate-side.png')
 oldmap=historical('3cf4a9b','route36/evidence/native-overview.png')
 item('G07','G07','Assembled side-door gate','Intended east–west','Rejected','Previous Route 36 revision','Frontal body with added side door and extra glazed bays; shown only to identify the rejected design.',rejected,context(oldmap,0,5*16),['git:3cf4a9b:gba/art/route36/source/materials/gate-side.png'],True)
 oldmap=historical('a8a17dae','route36/evidence/native-overview.png')
 item('G08','G08','Simple front gate','North–south','Superseded','First Route 36 Alph frontage','Flat roof planes and a minimal front doorway, before the accepted G01a rebuild.',read('route36/source/materials/alph_gate.png'),context(oldmap,52*16,20*16),['route36/source/materials/alph_gate.png','git:a8a17dae:gba/art/route36/evidence/native-overview.png'],True)
 manifest={'category':'Gatehouse exteriors','approval':'Unselected; review only','engine_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),'art_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'credit':'HGSS-derived art: Game Freak, Nintendo, Creatures / The Pokemon Company. Existing project adaptations only.','coverage':{'New Bark Town':'No gatehouse exterior found','Route 29':['G01b','G01c','G04a','G04b'],'Cherrygrove City':'No gatehouse exterior found','Route 30':'No gatehouse exterior found','Route 31':['G04a','G04b','G06'],'Violet City':['G03','G05'],'Route 36':['G01a','G02','G07','G08']},'method':'Existing native pixels only. Identical uses deduplicated; meaningful palette variants retained. Isolated assets use existing source alpha. Contexts are map-render crops, not new gameplay screenshots. No game files changed.','items':[{k:v for k,v in r.items() if k not in ('asset','context')} for r in rows]}
 (OUT/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
 template=(Path(__file__).parent/'gates.html').read_text();html=template.replace('__GATE_DATA__',json.dumps(rows,separators=(',',':')))
 args.visual.parent.mkdir(parents=True,exist_ok=True);args.visual.write_text(html);assert len(html.encode())<1_000_000
 # A static fallback sheet uses the same unscaled source art at exactly 2x.
 font='/System/Library/Fonts/Supplemental/Arial.ttf';f=ImageFont.truetype(font,20);small=ImageFont.truetype(font,15)
 primary=[r for r in rows if r['id'] in ['G01a','G02','G03','G04a','G05']]
 board=Image.new('RGB',(1056,3*420+92),(238,240,239));d=ImageDraw.Draw(board);d.text((24,20),'JOHTO / GATEHOUSE REVIEW',font=f,fill=(25,36,38));d.text((24,52),'Existing artwork at 2x • no selection applied • variants and earlier builds in the interactive sheet',font=small,fill=(55,65,65))
 for i,r in enumerate(primary):
  x=24+(i%3)*352;y=100+(i//3)*420;d.text((x,y),r['id']+' / '+r['orientation'],font=f,fill=(25,36,38))
  im=Image.open(OUT/r['asset_file']).resize((288,288),Image.Resampling.NEAREST);board.paste(im,(x+16,y+62),im)
  label={'G01a':'Route 36 front gate','G02':'Route 36 side gate','G03':'Violet west gate','G04a':'Route 29 / 31 red gable','G05':'Violet east purple gable'}[r['id']]
  d.text((x,y+358),label,font=small,fill=(25,36,38))
 board=board.crop((0,0,1056,950));board.save(OUT/'gatehouses-overview.png')
 print(json.dumps({'variants':len(rows),'families':len(set(r['family'] for r in rows)),'fragment_bytes':len(html.encode()),'output':str(args.visual)}))
if __name__=='__main__':main()
