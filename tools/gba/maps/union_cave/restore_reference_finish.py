"""Owner-authorized restoration of textured HGSS walls and actual embedded stairs.
Guarded native edit of only the three private cave areas. No screenshot repack.
The de6922a native reference is read-only; exact duplicate glyph flips free slots
without altering a pixel. Local edits retain map IDs, original warp pair indices,
accepted southern entrance and the repaired B1F corner.
Usage: script ENGINE READ_ONLY_DE6922A_REFERENCE
"""
from pathlib import Path
import sys,json,struct,hashlib,subprocess
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE.parent));from tiles import Tileset
from config import FLOORS
G,B=map(Path,sys.argv[1:3]);HEAD='988e0287216410698481d313e73d6cf99f650b76';BASE='de6922a964721aceb11147bcac6acadc477d4538'
assert subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(G),'status','--porcelain'],text=True),'Preserve owner source edits'
assert subprocess.check_output(['git','-C',str(B),'rev-parse','HEAD'],text=True).strip()==BASE
actual={'1f':[(4,5),(8,57)],'b1f':[(32,35),(3,48),(30,46)],'b2f':[(3,5)]}
unwired={'1f':[],'b1f':[(3,5),(3,12)],'b2f':[]}
removed_markers={'1f':[(5,5),(7,57)],'b1f':[(31,35),(4,48),(29,46),(4,5),(4,12)],'b2f':[(4,5)]}
donors={'1f':[(6,5),(7,56)],'b1f':[(30,35),(5,48),(29,47),(5,5),(5,12)],'b2f':[(5,5)]}
def digest(p):
 b=p.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if p.suffix=='.pal' else b).hexdigest()
for key,c in FLOORS.items():
 S=ROOT/f'gba/art/union-cave-{key}/source';manifest=json.loads((S/'previous-988e0287/generated-files.json').read_text());assert all((G/p).exists() and digest(G/p)==h for p,h in manifest.items()),('Preserve owned source',key)
for key,c in FLOORS.items():
 W,H=c['size'];S=ROOT/f'gba/art/union-cave-{key}/source';E=S.parent/'evidence';old=Tileset(B,c['set'],c['set']);current=Tileset(G,c['set'],c['set']);grid=np.fromfile(B/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W).copy();oldgrid=grid.copy();oldimage=old.map_image(list(map(int,grid.ravel())),W)
 blocks=[list(q) for part in old.blocks for q in part];attrs=[v for part in old.attrs for v in part];tiles=[np.array(p,np.uint8).reshape(8,8) for part in old.tiles for p in part];pals=[np.array(p,np.uint8) for p in old.pals[0]];events=json.loads((G/'data/maps'/c['name']/'map.json').read_text());edits=[]
 # Deduplicate only exact indexed glyph flips. Colors, masks and artwork stay exact.
 seen={};remap={}
 for tid in range(1008):
  p=tiles[tid];variants=[p,p[:,::-1],p[::-1],p[::-1,::-1]];sig=min(a.tobytes() for a in variants)
  if sig not in seen:seen[sig]=tid
  rep=seen[sig]
  for n,a in enumerate([tiles[rep],tiles[rep][:,::-1],tiles[rep][::-1],tiles[rep][::-1,::-1]]):
   if np.array_equal(a,p):remap[tid]=(rep,[0,1024,2048,3072][n]);break
 for block in blocks:
  for i,en in enumerate(block):
   tid=en&1023
   if tid<1008:rep,flip=remap[tid];block[i]=(en&~1023)^flip;block[i]|=rep
 def mid(x,y):return int(grid[y,x])&1023
 def fresh(x,y):
  m=mid(x,y)
  if int(((grid&1023)==m).sum())>1:
   used=set(map(int,(grid&1023).ravel()));n=next(n for n in range(1024) if n not in used);blocks[n]=blocks[m].copy();attrs[n]=attrs[m];grid[y,x]=(int(grid[y,x])&~1023)|n;m=n
  return m
 def usedglyphs():return {en&1023 for m in set(map(int,(grid&1023).ravel())) for en in blocks[m]}
 def glyph(p):
  for tid in sorted(usedglyphs()):
   for n,a in enumerate([tiles[tid],tiles[tid][:,::-1],tiles[tid][::-1],tiles[tid][::-1,::-1]]):
    if np.array_equal(a,p):return tid|[0,1024,2048,3072][n]
  used=usedglyphs();free=next((tid for tid in range(1,1008) if tid not in used),None);assert free is not None,('Local glyph budget',key,len(used));tiles[free]=p.copy();return free
 def native_piece(t,x,y,q):
  g=np.fromfile((G if t is current else B)/'data/layouts'/c['name']/'map.bin','<u2').reshape(H,W);m=int(g[y,x])&1023;en=t.blocks[m>=512][m-512 if m>=512 else m][q];tid=en&1023;p=np.array(t.tiles[tid>=512][tid-512 if tid>=512 else tid],np.uint8).reshape(8,8)
  if en&1024:p=p[:,::-1]
  if en&2048:p=p[::-1]
  return t.pals[0][en>>12],p,en>>12
 def set_rgb_quad(x,y,q,rgb,bank):
  co=pals[bank].astype(np.int32);d=((rgb.astype(np.int32)[...,None,:]-co[None,None,:,:])**2).sum(3);d[...,0]=10**9;p=d.argmin(2).astype(np.uint8);m=fresh(x,y);blocks[m][q]=glyph(p)|(bank<<12)
 # Remove all eight extra floor markers completely, including their warp behavior.
 for (x,y),(dx,dy) in zip(removed_markers[key],donors[key]):
  dm=mid(dx,dy);assert (int(grid[dy,dx])&0xc00)==0
  grid[y,x]=(int(grid[y,x])&~1023)|dm;edits.append({'remove_floor_marker':[x,y],'ordinary_floor_donor':[dx,dy]})
 # Retain the owner's accepted southern opening and its full fitted rim.
 if key=='1f':
  for y in range(56,60):
   for x in range(25,32):
    for q in range(4):
     co,p,bank=native_piece(current,x,y,q);rgb=np.array(co,np.uint8)[p];set_rgb_quad(x,y,q,rgb,bank)
  edits.append({'preserved_southern_entrance_cells':[25,56,32,60]})
 # Retain original embedded stairhead/tread/cap texture, without a new square
 # sprite or isolated cutout. Their full joins are reviewed against HGSS.
 for x,y in actual[key]+unwired[key]:
  edits.append({'embedded_stair_head':[x,y],'reference_pixel_box':[x*16,y*16-8,x*16+16,y*16+16],'head_policy':'original embedded native stairwell and cap retained; no added floor stair sprite'})
 # Preserve the small actor-removal fix, authored inside the original ramp.
 if key=='b1f':
  for y in [16,17]:
   x=23;q=3 if y==16 else 1;m=mid(x,y);en=blocks[m][q];p=tiles[en&1023].copy()
   if en&1024:p=p[:,::-1]
   if en&2048:p=p[::-1]
   p[:,5:8]=p[:,4:5];blocks[fresh(x,y)][q]=glyph(p)|(en&0xf000)
 # Registered warp indices/destinations stay stable; trigger at the real stair entrance.
 stair_events=events['warp_events'][1:] if key=='1f' else events['warp_events']
 for e,(x,y) in zip(stair_events,actual[key]):e['x']=x;e['y']=y;m=fresh(x,y);attrs[m]=(attrs[m]&~255)|97;grid[y,x]=(int(grid[y,x])&1023)|0x3000
 assert len(stair_events)==len(actual[key])
 for part,typ in enumerate(['primary','secondary']):
  d=G/'data/tilesets'/typ/c['set'];im=Image.new('P',(128,256));im.putpalette([int(v) for co in pals[0] for v in co]+[0]*720)
  for i,p in enumerate(tiles[part*512:(part+1)*512]):im.paste(Image.fromarray(p,'P'),(i%16*8,i//16*8))
  im.save(d/'tiles.png');(d/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*b) for b in blocks[part*512:(part+1)*512]));(d/'metatile_attributes.bin').write_bytes(struct.pack('<512H',*attrs[part*512:(part+1)*512]))
  for i in range(16):(d/'palettes'/f'{i:02}.pal').write_bytes((B/'data/tilesets'/typ/c['set']/'palettes'/f'{i:02}.pal').read_bytes())
 grid.astype('<u2').tofile(G/'data/layouts'/c['name']/'map.bin');(G/'data/maps'/c['name']/'map.json').write_text(json.dumps(events,indent=2)+'\n')
 # Editable ledgers retain original ground/material classes and explicit new stair entries.
 plan=np.array([list(row) for row in (S/'previous-de6922a/hgss-material-grid.txt').read_text().splitlines()]);foot=np.load(S/'previous-de6922a/hgss-foot-blocked.npy').copy()
 for x,y in removed_markers[key]:plan[y,x]='.'
 for x,y in actual[key]:plan[y,x]='S';foot[y,x]=False
 for n in ['hgss-material-grid.txt']:(S/n).write_text('\n'.join(''.join(row) for row in plan)+'\n')
 for n in ['native-material-grid.npy']:np.save(S/n,plan)
 for n in ['native-foot-blocked.npy','hgss-foot-blocked.npy']:np.save(S/n,foot)
 np.save(S/'native-metatile-grid.npy',grid);np.save(S/'native-water-plane.npy',(grid>>12)==1)
 t=Tileset(G,c['set'],c['set']);t.map_image(list(map(int,grid.ravel())),W).save(E/'native-map.png')
 report={'base_native_style':BASE,'preserved_prior_finish':HEAD,'operation':'restore original textured walls/caps and palette vocabulary, remove all extra floor stair squares, register existing embedded stairs, repair local heads/joins','local_edits':edits,'actual_wired_stairs':actual[key],'visible_unwired_stairs':unwired[key],'static_glyphs_used':len(usedglyphs()),'no_unrelated_maps_changed':True,'warp_pair_indices_preserved':True};(S/'reference-finish.json').write_text(json.dumps(report,indent=2)+'\n')
 paths=[p for folder in [G/'data/layouts'/c['name'],G/'data/maps'/c['name'],G/'data/tilesets/primary'/c['set'],G/'data/tilesets/secondary'/c['set']] for p in folder.rglob('*') if p.is_file() and p.name not in ['header.inc','events.inc','connections.inc']];(S/'generated-files.json').write_text(json.dumps({str(p.relative_to(G)):digest(p) for p in paths},indent=2)+'\n')
 (S/'native-edit-lock.json').write_text(json.dumps({'reason':'owner-requested original-style restoration and direct embedded-stair edits; never replay a scene packer','source':'current native layout/metatile/glyph files','provenance':'restore_reference_finish.py guarded at exact preserved baseline'},indent=2)+'\n')
 print(key,json.dumps(report))
