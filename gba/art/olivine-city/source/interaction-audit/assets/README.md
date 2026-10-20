# Interaction asset provenance

`bunting-original.png`: newly generated standalone transparent illustration for
this owner-authorized redesign, using the image generation tool. Brief: seven
maritime pennants in navy, sea blue, ivory and brass, mixed triangle/swallowtail/
rounded forms with simple sun, wave and anchor motifs. Not an HGSS extraction.
`bunting-native.png`: crop to nontransparent bounds, resize to124×24, threshold
alpha at128 and fit existing native palette6. One master reused at all three
strings; ground repairs and support lamps remain separate.

`parasol-canopy.png`: isolated from the existing HGSS-based native background at
x136..199, y544..575. The closed cloth outline determines each row's alpha span.
One native64×32 master reused for all three parasols. Original colors are retained;
poles below the canopy and physical tables are not part of the cloth master.

Implementation/provenance patch: `tools/gba/maps/olivine_city/city_interactions.py`.
The source masks, footprints and receiving repairs are independently recorded one
folder up. Native 4bpp tiles/metatiles and layer attributes live in engine PR23.
