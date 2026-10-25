"""Compile the two complete route layers with Porytiles, preserving exact RGB555 pixels."""
from pathlib import Path
import os,sys,json,struct,subprocess,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];TOOLS=ROOT/'tools/gba/maps';sys.path[:0]=[str(TOOLS/'route31_catalog'),str(TOOLS)]
spec=importlib.util.spec_from_file_location('pairpack',TOOLS/'route30_catalog/pair_pack.py');PP=importlib.util.module_from_spec(spec);spec.loader.exec_module(PP)
from tiles import Tileset
from claude_cherrygrove import ground as Gr
import assemble as A
G=Path(os.environ.get('ROUTES_ENGINE','/workspace/routes3839-complete'));ART=ROOT/'gba/art/routes3839-complete';S=ART/'source';E=ART/'evidence';BANK='routes3839_complete';PT='/workspace/deps/porytiles/porytiles-linux-amd64/porytiles-legacy'
assert not subprocess.check_output(['git','-C',str(G),'ls-files',f'data/tilesets/primary/{BANK}'],text=True).strip(), 'Committed native sources are authoritative; do not replay this provenance compiler.'
jobs={};plans={};specs={};attrs=[];pairs=[];ids={};grids={}
for n in [38,39]:
 z=np.load(S/f'route{n}/layers.npz');h,w=z['above'].shape;t=json.loads((S/f'route{n}/traversal.json').read_text());yy,xx=np.mgrid[:h*16,:w*16]
 plain=[tex[yy%32,xx%32].astype(np.uint8) for tex in [Gr.textures()[Gr.GRASS],A.road_texture(G)]]
 sp=dict(name=str(n),W=w,H=h,ground=z['ground'],flat=z['flat'],top=z['top'],above=z['above'],placed={},plains=plain);specs[n]=sp
 plans[n]=PP.plan_cells(sp,jobs);grid=np.zeros((h,w),np.uint16)
 for y in range(h):
  for x in range(w):
   q=plans[n][x,y];attr=t[y][x]['behavior_id']|(0 if sp['above'][y,x] else 0x1000);key=(tuple(q),attr)
   if key not in ids:
    ids[key]=len(ids);layers=[np.zeros((16,16,4),np.uint8) for _ in range(2)]
    for qi,(b,u) in enumerate(q):
     sl=np.s_[qi//2*8:qi//2*8+8,qi%2*8:qi%2*8+8]
     for li,k in enumerate([b,u]):
      if k is None:continue
      v=jobs[k]['k5'];mask=v[...,0]>=0;layers[li][sl][mask,:3]=(v[mask]<<3).astype(np.uint8);layers[li][sl][mask,3]=255
    pairs.append(layers);attrs.append(attr)
   grid[y,x]=ids[key]|(t[y][x]['collision']<<10)|(t[y][x]['elevation']<<12)
 grids[n]=grid
assert len(pairs)<=1024,len(pairs)
inp=S/'porytiles';out=E/'compiled';inp.mkdir(exist_ok=True);out.mkdir(exist_ok=True);rows=(len(pairs)+7)//8;ims=[Image.new('RGBA',(128,rows*16)) for _ in range(3)]
for i,(b,u) in enumerate(pairs):
 xy=(i%8*16,i//8*16);li=0 if attrs[i]&0x1000 else 1;ims[li].paste(Image.fromarray(b),xy);ims[li+1].paste(Image.fromarray(u),xy)
for name,im in zip(['bottom','middle','top'],ims):im.save(inp/f'{name}.png')
cmd=[PT,'compile-primary','-dual-layer','-tiles-primary-override=1008','-tiles-total-override=1024','-metatiles-primary-override=1024','-pals-primary-override=13','-o',str(out),str(inp),str(G/'include/constants/metatile_behaviors.h')]
print('Compiling',len(pairs),'metatiles',len(jobs),'quadrant jobs',flush=True)
r=subprocess.run(cmd,capture_output=True,text=True);(E/'porytiles.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-5000:]
im=Image.open(out/'tiles.png');blocks=(out/'metatiles.bin').read_bytes()[:len(pairs)*16];att=struct.pack('<%dH'%len(attrs),*attrs)
for sec in [False,True]:
 side='secondary' if sec else 'primary';sym='Routes3839Complete'+('' if sec else 'Primary');d=G/f'data/tilesets/{side}/{BANK}';(d/'palettes').mkdir(parents=True,exist_ok=True);start=512 if sec else 0
 sh=Image.new('P',(128,256));sh.putpalette(im.getpalette())
 for i in range(512):
  tid=start+i
  if tid//16*8<im.height:sh.paste(im.crop((tid%16*8,tid//16*8,tid%16*8+8,tid//16*8+8)),(i%16*8,i//16*8))
 sh.save(d/'tiles.png',bits=4)
 for i in range(16):
  p=out/'palettes'/f'{i:02}.pal';(d/'palettes'/f'{i:02}.pal').write_text(p.read_text() if p.exists() else 'JASC-PAL\n0100\n16\n'+'0 0 0\n'*16)
 (d/'metatiles.bin').write_bytes(blocks[start*16:(start+512)*16] or bytes(16));(d/'metatile_attributes.bin').write_bytes(att[start*2:(start+512)*2] or bytes(2))
 PP.register(G,sym,BANK,primary=not sec)
L=json.loads((G/'data/layouts/layouts.json').read_text());M=json.loads((G/'data/maps/map_groups.json').read_text())
for n,grid in grids.items():
 name=f'JohtoRoute{n}';lid=f'LAYOUT_JOHTO_ROUTE{n}';h,w=grid.shape;folder=G/f'data/layouts/{name}';folder.mkdir(exist_ok=True);grid.astype('<u2').tofile(folder/'map.bin');((grid[-4:-2,2:4]&1023)|0xc00).astype('<u2').tofile(folder/'border.bin')
 layout=dict(id=lid,name=f'{name}_Layout',width=w,height=h,primary_tileset='gTileset_Routes3839CompletePrimary',secondary_tileset='gTileset_Routes3839Complete',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin')
 if not any(l['id']==lid for l in L['layouts']):L['layouts'].append(layout)
 else:L['layouts']=[layout if l['id']==lid else l for l in L['layouts']]
 group=M['gMapGroup_Cherrygrove']
 if name not in group:group.append(name)
 d=G/f'data/maps/{name}';d.mkdir(exist_ok=True)
 signs=json.loads((S/f'route{n}/events.json').read_text())['signs'];bgs=[];scripts=[f'{name}_MapScripts::\n    .byte 0\n']
 for i,e in enumerate(s for s in signs if s['bg_type']==1):
  x,y=e['cell'];label=f'{name}_Sign{i}';bgs.append(dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=label))
  msg='MOOMOO FARM' if n==39 and x==14 else f'ROUTE {n}'
  scripts.append(f'{label}::\n    msgbox {label}_Text, MSGBOX_SIGN\n    end\n\n{label}_Text:\n    .string "{msg}$"\n')
 con=[dict(direction='left' if n==38 else 'right',offset=0,map=f'MAP_JOHTO_ROUTE{39 if n==38 else 38}')]
 base=json.loads((G/'data/maps/JohtoRoute31/map.json').read_text());base.update(id=f'MAP_JOHTO_ROUTE{n}',name=name,layout=lid,music='MUS_ROUTE110',region='REGION_JOHTO',region_map_section=f'MAPSEC_JOHTO_ROUTE_{n}',connections=con,object_events=[],warp_events=[],coord_events=[],bg_events=bgs)
 (d/'map.json').write_text(json.dumps(base,indent=2)+'\n');(d/'scripts.inc').write_text('\n'.join(scripts))
 t=Tileset(G,BANK,BANK);native=t.map_image(grid.ravel().tolist(),w);native.save(E/f'route{n}/native.png')
 want=np.array(Image.open(E/f'route{n}/composed.png'));actual=np.array(native);assert np.array_equal(actual>>3,want>>3),(n,int(((actual>>3)!=(want>>3)).any(-1).sum()))
(G/'data/layouts/layouts.json').write_text(json.dumps(L,indent=2)+'\n');(G/'data/maps/map_groups.json').write_text(json.dumps(M,indent=2)+'\n')
(E/'packing.json').write_text(json.dumps(dict(metatiles=len(pairs),allocated_glyphs=im.height//8*16,palettes_used=sorted(set(map(int,np.frombuffer(blocks,'<u2')>>12))),command=cmd,exact_rgb555_match=True),indent=2)+'\n');print('Installed exact native routes.',flush=True)
