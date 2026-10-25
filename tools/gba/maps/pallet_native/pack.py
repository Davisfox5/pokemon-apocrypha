"""Compile only the five authorized Pallet replacements through Porytiles.
Palette coalescing is global per map: identical colors stay identical at seams.
No nearest-tile substitution. Every material mask and pixel silhouette is kept.
"""
from pathlib import Path
import sys,json,struct,math,shutil,subprocess,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/gba/maps/pallet_rebuild'))
from native import Bank,words,numbered
A=ROOT/'gba/art/pallet-native';S=A/'source';EV=A/'evidence';PACK=S/'porytiles';PACK.mkdir(exist_ok=True)
E=Path(sys.argv[1]);PT=Path(sys.argv[2])
SPECS=[('ApocPalletTown','palletoutdoor','pallettown'),('ApocPalletRedHouse1F','palletindoor','palletredhouse'),('ApocPalletRedHouse2F','palletbedroomprimary','palletbedroom'),('ApocPalletOakHouse','palletoakprimary','palletoakhouse'),('ApocPalletLab','palletlabprimary','palletlab')]

def plan(sets):
 sets=set(s for s in sets if s)
 maximal=[s for s in sets if not any(s<t for t in sets)]
 pals=[]
 for cs in sorted(maximal,key=lambda s:(-len(s),sorted(s))):
  fits=[(len(p|cs),i) for i,p in enumerate(pals) if len(p|cs)<=15]
  if fits:pals[min(fits)[1]]|=cs
  else:pals.append(set(cs))
 return pals

def prepare(name):
 images=[Image.open(S/name/(n+'.png')).convert('RGBA') for n in ('ground','foreground')]
 arrays=[np.array(im) for im in images];hist=collections.Counter(tuple(map(int,c[:3])) for a in arrays for c in a.reshape(-1,4) if c[3])
 sets=[]
 for im in images:
  for y in range(0,im.height,8):
   for x in range(0,im.width,8):sets.append(frozenset(c[:3] for c in im.crop((x,y,x+8,y+8)).getdata() if c[3]))
 pals=plan(sets);initial=len(pals);remap={c:c for c in hist};steps=[]
 protected=set()
 if name=='ApocPalletTown':
  # Shared canopy colors and every water phase stay exact.
  for p in [ROOT/'gba/art/route31-catalog/source/local-art/cherrygrove-tree-with-shadow.png',S/'assets/hgss-water.png']:
   protected.update(tuple(int(k)&248 for k in c[:3]) for c in Image.open(p).convert('RGBA').getdata() if c[3])
 while len(pals)>12:
  cols=sorted(hist);a=np.array(cols,dtype=float);dist=((a[:,None]-a[None,:])**2*np.array([.8,1,.8])).sum(-1);np.fill_diagonal(dist,np.inf)
  cost=dist*np.array([math.sqrt(hist[c]) for c in cols])[:,None]
  for i,c in enumerate(cols):
   if c in protected:cost[i]=np.inf
  i,j=np.unravel_index(np.argmin(cost),cost.shape);src,dst=cols[i],cols[j]
  assert np.isfinite(cost[i,j]) and dist[i,j]<=1600,(name,'palette merge too large',src,dst,dist[i,j])
  hist[dst]+=hist.pop(src);sets=[frozenset(dst if c==src else c for c in st) for st in sets]
  remap={c:(dst if v==src else v) for c,v in remap.items()};steps.append(dict(source=src,target=dst,distance=float(dist[i,j])));pals=plan(sets)
  assert len(steps)<500
 out=[]
 for layer,a in zip(('ground','foreground'),arrays):
  rgb=a[...,:3].copy()
  for c,v in remap.items():
   if c!=v:a[...,:3][(rgb==c).all(-1)]=v
  a[...,3]=np.where(a[...,3],255,0);im=Image.fromarray(a);im.save(S/name/(layer+'-native.png'));out.append(im)
 # Most common palettes first to make the six primary banks useful.
 pals.sort(key=lambda p:(-sum(hist[c] for c in p),sorted(p)))
 (S/name/'palette-adaptation.json').write_text(json.dumps(dict(initial_banks=initial,final_banks=len(pals),global_color_merges=steps,protected_canopy_and_water=name=='ApocPalletTown'),indent=2)+'\n')
 return out,pals

def sheet(pairs,path,outdoor,pals,primary):
 path.mkdir(exist_ok=True);size=(128,max(16,math.ceil(len(pairs)/8)*16));ims=[Image.new('RGBA',size) for _ in range(3)]
 for i,(bg,fg,_) in enumerate(pairs):
  xy=(i%8*16,i//8*16);ims[1 if outdoor else 0].paste(bg,xy);ims[2 if outdoor else 1].paste(fg,xy)
 for n,im in zip(('bottom','middle','top'),ims):im.save(path/(n+'.png'))
 d=path/'palette-overrides';d.mkdir(exist_ok=True)
 for p in d.glob('*.pal'):p.unlink()
 for i in range(6) if primary else range(6,len(pals)):
  colors=sorted(pals[i]) if i<len(pals) else [];lines=['-']+['%d %d %d'%c for c in colors]+['-']*(15-len(colors))
  (d/f'{i:02}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(lines)+'\n')

def compile(path,primary=None):
 out=path.with_name(path.name+'-compiled');out.mkdir(exist_ok=True)
 cmd=[str(PT),'compile-secondary' if primary else 'compile-primary','-dual-layer','-o',str(out),str(path)]
 if primary:cmd.append(str(primary))
 cmd.append(str(E/'include/constants/metatile_behaviors.h'));r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 for pal in (out/'palettes').glob('*.pal'):pal.write_bytes(pal.read_bytes().replace(b'\r\n',b'\n'))
 return out

def install(out,folder,pairs):
 d=E/'data/tilesets'/folder;(d/'palettes').mkdir(exist_ok=True,parents=True)
 at=words(out/'metatile_attributes.bin')
 for i,(_,_,beh) in enumerate(pairs):at[i]=(at[i]&0xf000)|beh
 (out/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(at),*at))
 for n in ('tiles.png','metatiles.bin','metatile_attributes.bin'):shutil.copyfile(out/n,d/n)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(d/'palettes'/p.name).write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 return Image.open(out/'tiles.png').width*Image.open(out/'tiles.png').height//64

def colors(pair):
 sets=[]
 for im in pair[:2]:
  for y in (0,8):
   for x in (0,8):
    s={v[:3] for v in im.crop((x,y,x+8,y+8)).getdata() if v[3]}
    if s:sets.append(s)
 return sets

layouts=json.loads((E/'data/layouts/layouts.json').read_text());report=[]
selected=sys.argv[3] if len(sys.argv)>3 else None
if selected:
 assert selected in [n for n,p,s in SPECS]
 report=[r for r in json.loads((EV/'pack.json').read_text()) if r['map']!=selected]
for name,pr,se in SPECS:
 if selected and name!=selected:continue
 (g,f),pals=prepare(name);w,h=g.width//16,g.height//16;outdoor=name==SPECS[0][0]
 cells=json.loads((S/name/'cells.json').read_text());pairs=[];unique={};indices=[]
 for c in cells:
  x,y=c['x'],c['y'];box=(x*16,y*16,x*16+16,y*16+16);bg,fg=g.crop(box),f.crop(box);beh=c['behavior'];key=bg.tobytes(),fg.tobytes(),beh
  if key not in unique:unique[key]=len(pairs);pairs.append((bg,fg,beh))
  indices.append(unique[key])
 # Off-map border: canopy by default. South extension is handled by its own native border table.
 borders=[]
 for y in range(2):
  for x in range(2):
   bg,fg=(g.crop((x*16,(y+2)*16,x*16+16,(y+3)*16)),f.crop((x*16,(y+2)*16,x*16+16,(y+3)*16))) if outdoor else (Image.new('RGBA',(16,16),(40,56,64,255)),Image.new('RGBA',(16,16)))
   pair=(bg,fg,0);key=bg.tobytes(),fg.tobytes(),0
   if key not in unique:unique[key]=len(pairs);pairs.append(pair)
   borders.append(unique[key])
 # Dark interior border color is already part of the shell palette.
 pri=[];sec=[];mapping={}
 for i,pair in enumerate(pairs):
  fits=all(any(st<=pal for pal in pals[:6]) for st in colors(pair))
  if fits and len(pri)<250:mapping[i]=len(pri);pri.append(pair)
  else:mapping[i]=512+len(sec);sec.append(pair)
 assert pri and len(sec)<=512
 pp=PACK/pr;sp=PACK/se;sheet(pri,pp,outdoor,pals,True);po=compile(pp);pn=install(po,'primary/'+pr,pri)
 assert pn<=512,(name,pn,'primary tiles')
 sheet(sec,sp,outdoor,pals,False);so=compile(sp,pp);sn=install(so,'secondary/'+se,sec)
 assert sn<=496,(name,sn,'secondary tiles')
 grid=[(c['elevation']<<12)|(c['collision']<<10)|mapping[i] for c,i in zip(cells,indices)]
 d=E/'data/layouts'/name;(d/'map.bin').write_bytes(struct.pack('<'+'H'*len(grid),*grid));(d/'border.bin').write_bytes(struct.pack('<4H',*[mapping[i] for i in borders]))
 l=next(l for l in layouts['layouts'] if l['name']==name+'_Layout');l['width']=w;l['height']=h
 meta=(S/name/'map.json').read_text();mp=E/f'data/maps/{name}/map.json'
 if mp.read_text()!=meta:mp.write_text(meta)
 b=Bank(E,'primary/'+pr,'secondary/'+se,False);im=b.map(grid,w);expected=g.copy();expected.alpha_composite(f)
 # Palette zero uses the global backdrop, only transparent pixels differ outside authored maps.
 assert np.array_equal(np.array(im),np.array(expected.convert('RGB'))),(name,'native conversion mismatch')
 im.save(EV/(name+'-native.png'));numbered(im,2).save(EV/(name+'-native-grid.png'))
 (S/name/'native-grid.json').write_text(json.dumps(dict(width=w,height=h,entries=grid),indent=1)+'\n')
 report.append(dict(map=name,width=w,height=h,cells=w*h,primary_tiles=pn,secondary_tiles=sn,primary_metatiles=len(pri),secondary_metatiles=len(sec),palettes=len(pals),native_pixels_equal=True))
 print(report[-1],flush=True)
lp=E/'data/layouts/layouts.json';lt=json.dumps(layouts,indent=2)+'\n'
if lp.read_text()!=lt:lp.write_text(lt)
report.sort(key=lambda r:[n for n,p,s in SPECS].index(r['map']))
(EV/'pack.json').write_text(json.dumps(report,indent=2)+'\n')
