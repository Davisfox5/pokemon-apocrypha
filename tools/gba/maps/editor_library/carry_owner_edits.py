"""Carry only reviewed non-overlapping owner cells to a separate native project.
The five conflicting dirt/grass cells deliberately remain untouched pending reply.
"""
import sys,json,hashlib,struct
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from tiles import Tileset
owner=Path(sys.argv[1]);dest=Path(sys.argv[2]);audit=Path(sys.argv[3]);report=Path(sys.argv[4]);assert owner.resolve()!=dest.resolve()
a=json.loads(audit.read_text());old=Tileset(owner,'claude_route30','cherrygrove');new=Tileset(dest,'claude_route30','editor_route30');path='data/layouts/CherrygroveRoute30Approach/map.bin';saved=np.fromfile(owner/path,'<u2');grid=np.fromfile(dest/path,'<u2');before=grid.copy();lookup={}
for part in range(2):
 for off in range(len(new.blocks[part])):
  mid=part*512+off;lookup.setdefault((new.render(mid).tobytes(),new.attrs[part][off]),[]).append(mid)
applied=[];pending=[];added=[]
for v in a['cells']:
 i=v['y']*35+v['x'];assert int(saved[i])==v['saved_word'],'Owner changed again';assert int(grid[i])==v['newer_word'],'Destination changed again'
 if v['overlaps_newer_art'] or v['overlaps_newer_movement']:pending.append(v);continue
 mid=int(saved[i]&1023);key=(old.render(mid).tobytes(),old.attrs[mid>=512][mid%512]);matches=lookup.get(key,[])
 if not matches:
  # Reuse the exact original entries only if they still decode identically in
  # the receiving banks. Never approximate terrain, palette, or attributes.
  assert len(new.blocks[1])<512,'No metatile capacity for preserved owner art'
  extra=512+len(new.blocks[1]);new.blocks[1].append(old.blocks[mid>=512][mid%512]);new.attrs[1].append(old.attrs[mid>=512][mid%512])
  assert new.render(extra).tobytes()==key[0],(v,'Owner graphics need explicit migration')
  matches=[extra];lookup[key]=matches;added.append({'old_id':mid,'new_id':extra})
 picked=mid if mid in matches else matches[0];grid[i]=(int(saved[i])&~1023)|picked;applied.append(dict(v,native_id=picked))
folder=dest/'data/tilesets/secondary/claude_route30'
(folder/'metatiles.bin').write_bytes(b''.join(struct.pack('<8H',*v) for v in new.blocks[1]))
(folder/'metatile_attributes.bin').write_bytes(struct.pack('<'+'H'*len(new.attrs[1]),*new.attrs[1]))
grid.tofile(dest/path);report.write_text(json.dumps({'added_exact_native_tiles':added,'applied':applied,'pending':pending,'before_sha256':hashlib.sha256(before.tobytes()).hexdigest(),'after_sha256':hashlib.sha256(grid.tobytes()).hexdigest()},indent=2)+'\n');print(len(applied),'applied;',len(pending),'pending')
