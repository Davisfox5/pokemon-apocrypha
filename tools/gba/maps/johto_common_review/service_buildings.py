"""Read-only Johto Center/Mart review: current native pixels and saved alternatives."""
from pathlib import Path
import sys,json,io,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset
A=ROOT/'gba/art';OUT=A/'johto-common-review/service-buildings'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'

def read(path):return Image.open(A/path).convert('RGBA')
def main(game):
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'assets').mkdir(exist_ok=True);(OUT/'contexts').mkdir(exist_ok=True)
 before=subprocess.check_output(['git','status','--porcelain'],cwd=game)
 def scene(name,tiles,width):
  grid=np.fromfile(game/f'data/layouts/{name}/map.bin','<u2');return Tileset(game,tiles,tiles).map_image(grid.tolist(),width).convert('RGBA')
 cg=scene('CherrygroveCity','cherrygrove',80);violet=scene('VioletCity','violet_city',80)
 approval=json.loads((A/'johto-mart/source/approval.json').read_text())
 for name,digest in approval['assets_sha256'].items():assert hashlib.sha256((A/'johto-mart/source'/name).read_bytes()).hexdigest()==digest
 rows=[];seen={}
 def add(id,title,asset,sources,status,usage,note,context=None):
  box=asset.getbbox();tight=asset.crop(box);digest=hashlib.sha256(tight.tobytes()+str(tight.size).encode()).hexdigest()
  if digest in seen:
   row=seen[digest];row['sources']+=sources;return row['id']
  row=dict(id=id,title=title,status=status,usage=usage,note=note,sources=sources,native_canvas=list(asset.size),visible_size=list(tight.size),rgba_sha256=digest,asset=f'assets/{id}.png')
  asset.save(OUT/row['asset'])
  if context is not None:row['context']=f'contexts/{id}.png';context.save(OUT/row['context'])
  rows.append(row);seen[digest]=row;return id
 def native_asset(path,mapim,origin):
  template=read(path);x,y=origin;a=mapim.crop((x*16,y*16,x*16+template.width,y*16+template.height));a.putalpha(template.getchannel('A'));return a
 c1=native_asset('cherrygrove-synthesis/refined/center.png',cg,(58,4));c2=native_asset('violet-city/source/materials/center.png',violet,(46,50))
 add('C01','Cherrygrove Center',c1,['cherrygrove-synthesis/refined/center.png','engine:CherrygroveCity [58,4]'],'Current','Cherrygrove City','HGSS form with centered doorway.',cg.crop((54*16,2*16,68*16,12*16)))
 add('C02','Violet Center',c2,['violet-city/source/materials/center.png','engine:VioletCity [46,50]'],'Current; recommended','Violet City','Same HGSS form, with softened exterior edges.',violet.crop((42*16,48*16,56*16,58*16)))
 m1=read('johto-mart/source/building.png');assert np.array_equal(np.array(m1)[np.array(m1)[:,:,3]>0,:3],np.array(violet.crop((19*16,35*16,19*16+112,35*16+96)))[np.array(m1)[:,:,3]>0,:3])
 add('M01','Shared Johto Mart',m1,['johto-mart/source/building.png','engine:VioletCity [19,35]'],'Approved and locked','Violet City; approved for Johto reuse','Original blue pavilion; single roof, small emblem, no lettering.',violet.crop((15*16,33*16,29*16,43*16)))
 m2=native_asset('cherrygrove-synthesis/refined/mart.png',cg,(50,6));sign=read('cherrygrove-synthesis/references/B/mart_sign.png');plate=Image.new('RGBA',(112,64));plate.alpha_composite(m2);s=cg.crop((54*16,7*16,54*16+sign.width,7*16+sign.height));s.putalpha(sign.getchannel('A'));plate.alpha_composite(s,(64,16))
 add('M02','Cherrygrove Mart',plate,['cherrygrove-synthesis/refined/mart.png','cherrygrove-synthesis/references/B/mart_sign.png','engine:CherrygroveCity [50,6]'],'Current older design','Cherrygrove City','HGSS shop and projecting sign; predates the approved M01 pavilion.',cg.crop((47*16,3*16,61*16,13*16)))
 current_ids=[r['id'] for r in rows]
 # Inventory meaningful saved native/source families, including palette variants.
 for kind,prefix in [('center','C'),('mart','M')]:
  index=3
  for folder in ['claude-cherrygrove/source','cherrygrove-synthesis/references/B','cherrygrove-synthesis/references/C','johto-v1/native','johto-v2/native','johto-v3/native','johto-v4/prepared','johto-restart/native','cherrygrove-art-study-v1/native']:
   path=folder+'/'+kind+'.png'
   if not (A/path).exists():continue
   title={'claude-cherrygrove/source':'Earlier HGSS adaptation','cherrygrove-synthesis/references/B':'Cherrygrove reference B','cherrygrove-synthesis/references/C':'Cherrygrove reference C','johto-v1/native':'Early Johto v1','johto-v2/native':'Johto v2','johto-v3/native':'Johto v3','johto-v4/prepared':'Johto v4 source cutout','johto-restart/native':'Johto restart','cherrygrove-art-study-v1/native':'Cherrygrove art study'}[folder]
   id=f'{prefix}{index:02}';actual=add(id,title,read(path),[path],'Earlier saved artwork','Cherrygrove development history','Reference only; not a new recommendation or approval.')
   if actual==id:index+=1
  if kind=='mart':
   for rev,title,status in [('007cab4c','First Violet shop','Superseded'),('8d65b407','Violet tiled-roof shop','Rejected roof and sign'),('3d5cda64','Early shared Mart','Superseded'),('1c8e61c3','Split-roof pavilion','Rejected depth and tower sign')]:
    path='gba/art/violet-city/source/materials/mart.png';raw=subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT);im=Image.open(io.BytesIO(raw)).convert('RGBA');id=f'M{index:02}';actual=add(id,title,im,[f'git:{rev}:{path}'],status,'Violet City development history','Historical reference only; M01 supersedes this design.')
    if actual==id:index+=1
 center_delta=int(np.any(np.array(c1)!=np.array(c2),axis=2).sum())
 manifest={'category':'Shared Johto service buildings','engine_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=game,text=True).strip(),'art_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'approval':{'Center':'Awaiting regional selection','Mart':'M01 already approved; preserve its design'},'coverage':{name:({'centers':['C01'],'marts':['M02']} if name=='Cherrygrove City' else {'centers':['C02'],'marts':['M01']} if name=='Violet City' else {'centers':[],'marts':[],'note':'No Center or Mart exterior in the scoped map sources.'}) for name in ['New Bark Town','Route 29','Cherrygrove City','Route 30','Route 31','Violet City','Route 36']},'method':'Current assets sampled from decoded engine maps with their source alpha; earlier source images are unchanged. Identical tight RGBA images deduplicated with all source aliases recorded. All presentation uses integer nearest-neighbor scaling. No engine files edited. Historical cutouts retain their existing defects.','current_center_pixel_difference':center_delta,'credit':'HGSS-derived assets: Game Freak, Nintendo, Creatures / The Pokemon Company. M01 original project artwork. See source package provenance for older adaptations.','items':rows}
 (OUT/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
 f=ImageFont.truetype(FONT,24);small=ImageFont.truetype(FONT,17);titlef=ImageFont.truetype(FONT,30)
 def draw_asset(board,row,box,scale):
  im=Image.open(OUT/row['asset']).convert('RGBA');im=im.crop(im.getbbox());im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
  x,y,w,h=box;assert im.width<=w and im.height<=h,(row['id'],im.size,box);board.paste(im,(x+(w-im.width)//2,y+h-im.height),im)
 def current_sheet(ids,title,footer,file):
  b=Image.new('RGB',(1000,820),(235,238,237));d=ImageDraw.Draw(b);d.text((24,20),title,font=titlef,fill=(24,36,38));d.text((24,62),'Existing artwork at 3x; map context at 2x',font=small,fill=(58,70,70))
  for i,id in enumerate(ids):
   row=next(r for r in rows if r['id']==id);x=24+i*492
   d.text((x,108),id+' / '+row['title'],font=f,fill=(24,36,38));d.text((x,143),row['status'],font=small,fill=(25,104,80) if id=='M01' else (58,70,70))
   draw_asset(b,row,(x,175,452,285),3)
   context=Image.open(OUT/row['context']).convert('RGB').resize((448,320),Image.Resampling.NEAREST);b.paste(context,(x,478))
  # Footer is separate so it cannot obscure the native scene pixels.
  c=Image.new('RGB',(1000,864),(235,238,237));c.paste(b,(0,0));ImageDraw.Draw(c).text((24,833),footer,font=small,fill=(58,70,70));c.save(OUT/file)
 current_sheet(['C01','C02'],'JOHTO / POKEMON CENTERS','Same HGSS family. Compare the roof edging and facade finish; choose either or request changes.','centers-current.png')
 current_sheet(['M01','M02'],'JOHTO / POKE MARTS','M01 is already approved. M02 shows the older shop still present in Cherrygrove.','marts-current.png')
 for prefix,label in [('C','Center'),('M','Mart')]:
  earlier=[r for r in rows if r['id'].startswith(prefix) and r['id'] not in current_ids];cols=3;cellw=340;cellh=310
  b=Image.new('RGB',(1020,100+((len(earlier)+2)//3)*cellh),(235,238,237));d=ImageDraw.Draw(b);d.text((20,16),f'JOHTO / EARLIER {label.upper()} ARTWORK',font=titlef,fill=(24,36,38));d.text((20,58),'Reference inventory at 2x. Earlier and rejected versions are not new recommendations.',font=small,fill=(58,70,70))
  for i,row in enumerate(earlier):
   x=i%cols*cellw;y=100+i//cols*cellh;d.text((x+14,y),row['id']+' / '+row['title'],font=small,fill=(24,36,38));draw_asset(b,row,(x+10,y+35,320,228),2);d.text((x+14,y+280),row['status'],font=small,fill=(80,85,85))
  b.save(OUT/f'{prefix.lower()}-earlier.png')
 assert subprocess.check_output(['git','status','--porcelain'],cwd=game)==before
 print(json.dumps({'items':len(rows),'center_difference':center_delta,'current':current_ids,'output':str(OUT)}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
