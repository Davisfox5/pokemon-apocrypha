#!/usr/bin/env python3
"""Install the faithful Cherrygrove layout, walking cast and reserved-tile animation."""
from pathlib import Path
import json,struct,re,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[3];G=ROOT/'tools/vendor/gba/johto-v4-game';A=ROOT/'gba/art/johto-v4'
layout=json.loads((A/'layout.json').read_text());scene=np.load(A/'native/scene.npz');solid=scene['solid'];W=layout['width'];H=layout['height']
def read(p):return json.loads((G/p).read_text())
def write(p,v):(G/p).write_text(json.dumps(v,indent=2)+'\n')
p='data/maps/CherrygroveCity/map.json';m=read(p)
routes=[('WATERFRONT',29,18,'UD',1),('COMMUTER',35,7,'LR',1),('JOHTO_BOY',41,19,'LR',1),('JOHTO_GIRL',59,13,'LR',1),('CAST_GOLD',39,15,'SQ',1),('CAST_SILVER',49,19,'SQ',1),('CAST_KESTRA',37,18,'LR',2),('COMPARE_HOENN',47,10,'LR',1),('COMPARE_KANTO',58,15,'SQ',1),('COMPARE_JOHTO',39,10,'SQ',1),('COMPARE_SINNOH',31,18,'SQ',1),('COMPARE_UNOVA',52,22,'LR',1)]
manifest=[]
for key,x,y,mode,n in routes:
 o=next(o for o in m['object_events'] if o['local_id']=='LOCALID_'+key);o.update(x=x,y=y,movement_type='MOVEMENT_TYPE_'+{'UD':'WALK_UP_AND_DOWN','LR':'WALK_LEFT_AND_RIGHT','SQ':'WALK_SEQUENCE_UP_RIGHT_DOWN_LEFT'}[mode],movement_range_x=n if mode!='UD' else 0,movement_range_y=n if mode!='LR' else 0)
 positions=[(x,y),(x,y-1),(x+1,y-1),(x+1,y)] if mode=='SQ' else [(xx,y) for xx in range(x-n,x+1)] if mode=='LR' else [(x,yy) for yy in range(y-n,y+1)]
 for xx,yy in positions:assert not solid[yy,xx],(key,'blocked',xx,yy)
 manifest.append(dict(name=key,graphics=o['graphics_id'],start=[x,y],mode=mode,positions=positions))
for b in layout['buildings']:m['warp_events'][b['warp']].update(zip(['x','y'],b['door']))
# Stable historical warp 3 is retained off the walkable surface. No ID renumbering.
m['warp_events'][3].update(x=1,y=4)
m['bg_events']=[dict(type='sign',x=41,y=12,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script='CherrygroveCity_TownSign')];write(p,m)
(A/'residents.json').write_text(json.dumps(manifest,indent=2)+'\n')
l=read('data/layouts/layouts.json')
for row in l['layouts']:
 if row['id'] in ['LAYOUT_CHERRYGROVE_CITY','LAYOUT_CHERRYGROVE_ROUTE29_APPROACH']:row['height']=H
write('data/layouts/layouts.json',l)
grid=np.frombuffer((G/'data/layouts/CherrygroveCity/map.bin').read_bytes(),dtype='<u2').reshape(H,W)
# Continue the same native forest/road patterns across both actual map connections.
forest=grid[28:30,40:42];road=grid[18:20,50:52].copy()
for name,w,h in [('CherrygroveRoute29Approach',16,H),('CherrygroveRoute30Approach',W,12)]:
 out=np.tile(forest,((h+1)//2,(w+1)//2))[:h,:w].copy()
 if w==16:
  # Identical rows for the first eight columns prevent any seam at the east edge.
  for x in range(12):out[:,x]=grid[:,62+x%2]
  out[14:17,:12]=np.tile(grid[14:17,62:64],(1,6))
 else:
  for y in range(4,h):out[y]=grid[y%2]
  out[4:h,35:38]=grid[0,35:38]
 (G/f'data/layouts/{name}/map.bin').write_bytes(out.astype('<u2').tobytes())
for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach']:
 (G/f'data/layouts/{name}/border.bin').write_bytes(forest.astype('<u2').tobytes())
p=G/'src/new_game.c';s=p.read_text();s=re.sub(r'(MAP_NUM\(MAP_CHERRYGROVE_CITY\), WARP_ID_NONE, )\d+, \d+',r'\g<1>39, 16',s);p.write_text(s)
p=G/'src/data/tilesets/headers.h';s=p.read_text();s=re.sub(r'(const struct Tileset gTileset_CherrygrovePrimary = .*?\.callback = )\w+',r'\g<1>InitTilesetAnim_JohtoV4',s);p.write_text(s)
p=G/'include/tilesets.h';s=p.read_text();decl='extern const struct Tileset gTileset_CherrygrovePrimary;\nvoid InitTilesetAnim_JohtoV4(void);';s=s.replace(decl+'\n','');s=s.replace('#define GUARD_tilesets_H','#define GUARD_tilesets_H\n'+decl);p.write_text(s)
folder=G/'graphics/tilesets/johto_v4';folder.mkdir(parents=True,exist_ok=True)
for f in (A/'native/water').glob('*.4bpp'):shutil.copyfile(f,folder/('water'+f.name))
p=G/'src/tileset_anims.c';s=p.read_text().split('// BEGIN JOHTO V4 SEA')[0].rstrip()+'\n\n// BEGIN JOHTO V4 SEA\n'
for i in range(32):s+=f'static const u16 sJohtoV4Sea{i:02}[] = INCBIN_U16("graphics/tilesets/johto_v4/water{i:02}.4bpp");\n'
s+='static const u16 *const sJohtoV4Sea[] = {'+', '.join(f'sJohtoV4Sea{i:02}' for i in range(32))+'};\n'
s+='''static void TilesetAnim_JohtoV4(u16 timer)
{
    if (timer % 8 == 0)
        AppendTilesetAnimToBuffer(sJohtoV4Sea[(timer / 8) % 32], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(1)), 16 * TILE_SIZE_4BPP);
}
void InitTilesetAnim_JohtoV4(void)
{
    sPrimaryTilesetAnimCounter = 0;
    sPrimaryTilesetAnimCounterMax = 256;
    sPrimaryTilesetAnimCallback = TilesetAnim_JohtoV4;
}
''';p.write_text(s)
# Remove the now-false reference to boats; preserve established story dialogue.
p=G/'data/maps/CherrygroveCity/scripts.inc';s=p.read_text().replace('These boats do not go far anymore.\\nNow they mostly just... sit.','I never get tired of watching\\nthe waves roll in.')
flavor={'HOENN':'I came here from HOENN.\\nThe sea makes me feel at home.','KANTO':'KANTO is just beyond the mountains.\\nI took the scenic route.','JOHTO':'Flowers, fresh air, and the sea.\\nThat is CHERRYGROVE for you!','SINNOH':'It is much warmer here than SINNOH.\\nI can leave my scarf in my bag!','UNOVA':'UNOVA has some very busy cities.\\nI like the quiet here.'}
for label,body in flavor.items():s=s.replace(f'"{label}$"',f'"{body}$"')
p.write_text(s)
print('Installed five active doors, two native approaches, twelve walking residents and sea animation.')
