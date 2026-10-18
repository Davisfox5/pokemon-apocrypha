"""Read-only native Porymap shelf generator. Never renumber or edit map tiles."""
import argparse, json, re, struct, sys, hashlib, html, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from tiles import Tileset

def read(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('output',type=Path);p.add_argument('--maps',nargs='+');a=p.parse_args();g=a.project;o=a.output;o.mkdir(parents=True,exist_ok=True);(o/'previews').mkdir(exist_ok=True)
 graphics=(g/'src/data/tilesets/graphics.h').read_text();layouts=read(g/'data/layouts/layouts.json')['layouts'];allpref=[];records=[];files={};summary=[]
 configs=read(ROOT/'gba/art/johto-common/rollout/source/initial-inventory.json')
 configs={v['map']:v for v in configs}
 names=a.maps or list(configs)
 for name in names:
  ls=[v for v in layouts if v['name']==name+'_Layout']
  if not ls:continue
  l=ls[0];w,h=l['width'],l['height'];grid=np.fromfile(g/l['blockdata_filepath'],'<u2').reshape(h,w)
  dirs=[]
  for side in ['primary','secondary']:
   sym='gTilesetTiles_'+l[side+'_tileset'].removeprefix('gTileset_')
   mt=re.search(re.escape(sym)+r'\[\].*?"data/tilesets/'+side+r'/([^/]+)/tiles.png"',graphics,re.S)
   if not mt:raise ValueError(sym)
   dirs.append(mt[1])
  t=Tileset(g,dirs[1],dirs[0]);scene=t.map_image(grid.ravel().tolist(),w);scene.save(o/'previews'/f'{name}.png');rgb=np.array(scene)
  for f in [g/l['blockdata_filepath'],g/l['border_filepath']]+[z for side,d in zip(['primary','secondary'],dirs) for z in (g/'data/tilesets'/side/d).rglob('*') if z.is_file()]:files[str(f.relative_to(g))]=digest(f)
  occupied={};items=[];seen=set();count=0
  def add(cat,label,box,mask=None):
   nonlocal count
   x,y,bw,bh=map(int,box)
   if min(x,y)<0 or x+bw>w or y+bh>h or min(bw,bh)<1:return
   data=grid[y:y+bh,x:x+bw];key=(cat,bw,bh,data.tobytes())
   if key in seen:return
   seen.add(key);mets=[]
   for yy in range(bh):
    for xx in range(bw):
     if mask is not None and not mask[yy,xx]:continue
     val=int(data[yy,xx]);mid=val&1023
     mets.append(dict(x=xx,y=yy,metatile_id=mid,collision=(val>>10)&3,elevation=val>>12))
     occupied.setdefault(mid,cat)
   if not mets:return
   title=f'{cat} | {label}'
   if any(v['name']==title for v in items):title+=f' @ {x},{y}'
   entry=dict(name=title,width=bw,height=bh,primary_tileset=l['primary_tileset'],secondary_tileset=l['secondary_tileset'],metatiles=mets)
   items.append(entry);count+=1
   preview=f'{name}-{count:03}.png';im=scene.crop((x*16,y*16,(x+bw)*16,(y+bh)*16));im.save(o/'previews'/preview)
   records.append(dict(map=name,name=title,box=[x,y,bw,bh],preview='previews/'+preview,tiles=[m['metatile_id'] for m in mets],kind='object'))
  # Authored building footprints, not inferred rectangles around arbitrary pixels.
  if name=='CherrygroveRoute30Approach':
   st=read(ROOT/'gba/art/route30-hgss-blocks/source/structures.json')
   for b in st['houses']:add('01 Buildings',b['name'],[b['x'],b['y'],b['width'],b['height']])
   for b in st['stairs']:add('04 Stairs',b['name'],b['rect'])
   for i,b in enumerate(st['ledges']):add('05 Ledges',f'Joined run {i+1}',b)
   for b in st['signs']:add('03 Scenery',b['name'],[b['at'][0],b['at'][1]-1,1,2])

  if name=='VioletCity':
   for b in read(ROOT/'gba/art/violet-city/source/landmarks.json'):
    if b.get('box') and b.get('asset') not in ('mart','center'):add('01 Buildings',b['name'],b['box'])
   add('03 Scenery','Teaching court',[55,48,12,7])
   add('03 Scenery','Bridge deck and rails',[36,20,7,2])
   add('03 Scenery','Lily pads',[27,19,2,1])
   add('03 Scenery','Lake islet',[47,22,4,5])
  if name=='CherrygroveCity':
   integration=read(ROOT/'gba/art/cherrygrove-synthesis/evidence/integration.json')
   for m in integration['maps']:
    if m['name']==name:
     for b in m['buildings']:
      if b['style'] not in ('center','mart'):add('01 Buildings',b['name'],[b['x'],b['y'],b['width'],b['height']])
  if name=='CherrygroveCity':
   for label,box in [('Harbor ship',[22,14,3,7]),('Harbor skiff',[28,23,4,2]),('Dock horizontal span',[27,18,4,2]),('Dock vertical span',[25,16,2,2]),('Dock junction',[25,18,2,2])]:add('03 Scenery',label,box)
  if name=='CherrygroveRoute29Approach':
   spec=read(ROOT/'gba/art/johto-common/rocks/hgss-placement-audit/source/route29-hgss-blocks/structures.json')
   for i,box in enumerate(spec['ledges']):add('05 Ledges',f'Joined run {i+1}',box)
  if name in ('VioletCity','CherrygroveCity'):
   for key,b in read(ROOT/'gba/art/johto-common/approved-buildings.json')['buildings'].items():
    if 'master' not in b:continue
    art=Image.open(ROOT/b['master']);bw,bh=math.ceil(art.width/16),math.ceil(art.height/16)
    for loc in b['placements']:
     if loc['map']==name:add('01 Buildings',b['review_id']+' '+key.replace('_',' '),[*loc['origin'],bw,bh])
  if name=='NewBarkTown':
   for label,x,y,bw,bh in [('Laboratory',11,0,11,7),('Annex',26,4,6,5),('West home',11,13,5,5),('East home',22,15,5,5),('Staff home A',9,26,5,5),('Staff home B',23,26,5,5)]:add('01 Buildings',label,[x,y,bw,bh])
  if name=='JohtoRoute36':
   for b in read(ROOT/'gba/art/route36/source/features.json')['gates']:add('01 Buildings',b['name'],[*b['at'],7,8 if b['name']=='Alph gate' else 7])
  if name=='JohtoRoute31':add('01 Buildings','Gatehouse',[1,8,7,8])
  if name=='JohtoRoute31':
   for label,cat,box in [('East-west flight','04 Stairs',[33,16,2,2]),('South flight','04 Stairs',[37,28,3,2]),('Joined low ledge','05 Ledges',[7,18,14,1]),('Side wall','06 Rock walls',[33,7,2,3]),('Front wall and foot','06 Rock walls',[54,10,2,2])]:add(cat,label,box)
  if name=='CherrygroveRoute29Approach':add('01 Buildings','Gatehouse',[49,4,7,8])
  if name=='JohtoRoute32':
   for label,cat,box in [('Installed Center','01 Buildings',[17,104,7,5]),('North gate','01 Buildings',[1,6,6,7]),('North-south flight','04 Stairs',[6,86,3,3]),('East-west flight','04 Stairs',[9,59,3,3]),('Railway span','03 Scenery',[12,66,4,4]),('Pier deck','03 Scenery',[20,82,3,3]),('Green tree','02 Trees',[24,17,2,3]),('Rock front and cap','06 Rock walls',[20,33,3,2]),('Rock side and cap','06 Rock walls',[23,42,3,3])]:add(cat,label,box)
  # Reuse only complete tree exemplars; prefer isolated crowns over overlapping forests.
  treefile=ROOT/f'gba/art/johto-common/rollout/source/{name}-trees.json'
  if treefile.exists():
   tr=read(treefile)
   for aid in (('T01','T02') if name=='CherrygroveCity' else ('T01',)):
    master=np.array(Image.open(ROOT/f'gba/art/johto-common/trees/source/{aid}.png').convert('RGBA'));mask=master[:,:,3]>0;choices=[]
    for v in tr:
     x,y=v['x'],v['y']
     if v['asset']!=aid or x%16 or y%16 or x<0 or y<0 or x+32>w*16 or y+48>h*16:continue
     crop=rgb[y:y+48,x:x+32];score=float(np.all(crop==master[:,:,:3],axis=2)[mask].mean());choices.append((score,x,y))
    if choices:
     score,x,y=max(choices);add('02 Trees',('Green tree' if aid=='T01' else 'Pink tree - Cherrygrove only')+' / current ground',[x//16,y//16,2,3])
  if name=='JohtoRoute36':
   for i,(x,y) in enumerate(read(ROOT/'gba/art/route36/source/features.json')['stairs']):add('04 Stairs',f'East-west flight {i+1}',[x,y,2,3])
   for i,x in enumerate([2,7]):add('06 Rock walls',f'Front complete cap and face {i+1}',[x,3,2,2])
   add('06 Rock walls','Side complete grass rim',[14,8,2,3])
  # Complete current small-object footprints. Exclude damaged old installations.
  if g.name!='apocrypha-src':
   specs={v['id']:v for v in read(ROOT/'gba/art/johto-common/trees/catalog.json')['assets']}
   specs.update({v['id']:v for v in read(ROOT/'gba/art/johto-common/scenery/catalog.json')['assets']})
   for entry in read(ROOT/'gba/art/johto-common/rollout/evidence/small-objects.json'):
    if entry['map']!=name:continue
    for obj in entry['objects']:
     aid=obj['master'];spec=specs[aid];sz=spec['size'];x,y=obj['origin'];add('02 Trees' if aid.startswith('T') else '03 Scenery',spec['label']+' / '+obj['background'],[x//16,y//16,math.ceil((x%16+sz[0])/16),math.ceil((y%16+sz[1])/16)])
  # Installed scenery coordinates and canonical dimensions.
  cat={v['id']:v for v in read(ROOT/'gba/art/johto-common/scenery/catalog.json')['assets']}
  props=read(ROOT/'gba/art/johto-common/rollout/source/prop-placements.json').get(name,{})
  for aid,positions in props.items():
   spec=cat[aid];sz=spec.get('size')
   if not sz:
    im=Image.open(ROOT/'gba/art/johto-common/scenery'/spec['master']);sz=im.size
   x,y=positions[0];add('03 Scenery',aid+' '+spec.get('label',aid),[x//16,y//16,math.ceil((x%16+sz[0])/16),math.ceil((y%16+sz[1])/16)])
  # All in-use metatiles get a named, one-cell picker, grouped by object membership
  # then native behavior. No synthetic collision values, ID remapping or unused donors.
  midpos={}
  for y in range(h):
   for x in range(w):midpos.setdefault(int(grid[y,x])&1023,(x,y))
  bank=[]
  for mid,(x,y) in sorted(midpos.items()):
   attr=t.attrs[mid>=512][mid%512]&255
   category=occupied.get(mid)
   if not category:
    if attr==2:category='07 Tall grass'
    elif attr in (16,17,18,19,20,21,22,23,24,25,26,27):category='08 Water'
    elif 0x38<=attr<=0x3f:category='05 Ledges'
    elif attr in (0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69):category='09 Entrances'
    else:category='10 Ground and structural transitions'
    if category=='10 Ground and structural transitions':
     ar=np.array(t.render(mid)).astype(int);r,gg,b=ar[:,:,0],ar[:,:,1],ar[:,:,2]
     blue=((b>r+15)&(b>gg-25)).mean();green=((gg>r+20)&(gg>b+12)).mean();tan=((r>gg)&(gg>b+20)).mean()
     if blue>.55:category='08 Water and shoreline'
     elif green>.80:category='07 Grass and vegetation'
     elif tan>.80:category='06 Rock or path surface'
   val=int(grid[y,x]);label=f'{category} / tile {mid:03X}'
   entry=dict(name=label,width=1,height=1,primary_tileset=l['primary_tileset'],secondary_tileset=l['secondary_tileset'],metatiles=[dict(x=0,y=0,metatile_id=mid,collision=val>>10&3,elevation=val>>12)])
   bank.append(entry)
  items.sort(key=lambda v:v['name']);bank.sort(key=lambda v:v['name']);allpref+=items+bank
  summary.append(dict(map=name,objects=len(items),used_tiles=len(bank),tilesets=dirs))
  # One complete ID-labelled bank for quick lookup, grouped identically to the shelf.
  cols=12;im=Image.new('RGB',(cols*64,math.ceil(len(bank)/cols)*64+28),'#202630');d=ImageDraw.Draw(im);d.text((8,8),name,fill='white')
  for i,b in enumerate(bank):
   mid=b['metatiles'][0]['metatile_id'];x=i%cols*64;y=i//cols*64+28;im.paste(t.render(mid).resize((32,32),Image.Resampling.NEAREST),(x+8,y));d.text((x+8,y+34),f'{mid:03X}',fill='white')
  im.save(o/'previews'/f'{name}-bank.png')
 (o/'prefabs.json').write_text(json.dumps(allpref,indent=2)+'\n');(o/'manifest.json').write_text(json.dumps(dict(project=str(g),maps=summary,source_sha256=files,objects=records),indent=2)+'\n')
 cards=[]
 for r in records:cards.append(f'<article data-search="{html.escape(r["map"]+" "+r["name"])}"><h3>{html.escape(r["map"]+" · "+r["name"])}</h3><img src="{r["preview"]}"><p>Source cells {r["box"]}</p></article>')
 (o/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Johto Porymap library</title><style>body{background:#1d252e;color:#eef4f8;font:16px system-ui;margin:24px}input{padding:12px;width:60%}main{display:flex;flex-wrap:wrap;gap:16px}article{padding:16px;background:#303d49;max-width:420px}img{image-rendering:pixelated;max-width:100%;min-width:64px}h3{font-size:15px}</style><h1>Johto object shelf</h1><p>Native tiles and collision, restricted to the source tileset pair. Placement copies ground too; use a matching ground context. Door events are separate.</p><input placeholder="Filter by map, building, tree, stairs..." oninput="document.querySelectorAll(\'article\').forEach(e=>e.hidden=!e.dataset.search.toLowerCase().includes(this.value.toLowerCase()))"><main>'+''.join(cards)+'</main>')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
