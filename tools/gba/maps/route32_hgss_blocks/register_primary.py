"""Register a route-local copy of Cherrygrove; never rewrites an existing tileset header."""
from pathlib import Path
import sys,json
G=Path(sys.argv[1]);tag='// Route32 reviewed-grid local primary\n'
entries={
'graphics.h':'const u32 gTilesetTiles_Route32Primary[] = INCGFX_U32("data/tilesets/primary/route32/tiles.png", ".4bpp.fastSmol");\nconst u16 gTilesetPalettes_Route32Primary[][16] = {\n'+''.join(f'INCGFX_U16("data/tilesets/primary/route32/palettes/{i:02}.pal", ".gbapal"),\n' for i in range(16))+'};\n',
'metatiles.h':'const u16 gMetatiles_Route32Primary[] = INCBIN_U16("data/tilesets/primary/route32/metatiles.bin");\nconst u16 gMetatileAttributes_Route32Primary[] = INCBIN_U16("data/tilesets/primary/route32/metatile_attributes.bin");\n',
'headers.h':'const struct Tileset gTileset_Route32Primary = { .isCompressed = TRUE, .isSecondary = FALSE, .tiles = gTilesetTiles_Route32Primary, .palettes = gTilesetPalettes_Route32Primary, .metatiles = gMetatiles_Route32Primary, .metatileAttributes = gMetatileAttributes_Route32Primary, .callback = InitTilesetAnim_CherrygrovePrimary };\n'
}
for name,entry in entries.items():
 p=G/'src/data/tilesets'/name;s=p.read_text()
 if tag not in s:p.write_text(s+'\n'+tag+entry)
 else:assert entry in s,('Preserving changed registration',name)
f=G/'data/layouts/layouts.json';j=json.loads(f.read_text())
for l in j['layouts']:
 if l['id']=='LAYOUT_JOHTO_ROUTE32':l['primary_tileset']='gTileset_Route32Primary'
s=json.dumps(j,indent=2)+'\n'
if f.read_text()!=s:f.write_text(s)
