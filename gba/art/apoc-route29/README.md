# Route 29 from HGSS slices, as a Porymap tileset

October 12, 2026. A rebuild of Route 29 (Cherrygrove to New Bark) done the way the
shared-source workflow expects: the HGSS vocabulary sliced at Gen 3 metatile size into
one secondary tileset, a layout Porymap can open and edit, and a PR on the `apocrypha`
branch of `Davisfox5/pokeemerald-expansion`. This is a review proposal. The accepted
route is untouched on that branch until the owner says otherwise.

## Review

- [Whole route at native scale](route29-overview.png)
- [The tileset Porymap will show](tileset-sheet.png) (secondary half, ids 0x200 and up)
- [Build report](build-report.json): 332 tiles of the 512 budget, 161 metatiles, six palette banks

## What was sliced from HGSS

Every piece comes off the 1:1 Route 29 render on its own 16 px cell grid, so each one is
already a Gen 3 metatile:

| Piece | Cells on the render | Result |
| --- | --- | --- |
| Tall grass | nine-slice at (17..18, 15..17) | 16 neighbour variants, each over all four lawn phases |
| Ledges and walls | (15..18, 14), (13, 16..18), (28, 14), (52, 18) | one-way ledge, wall, wall top, three corners |
| Route 46 gate | (48..56, 1..9) | 9 x 9 building, roof ridge drawn over the player |
| Apricorn tree | (20..22, 9..11) | 3 x 3, solid |
| Orange flowers | (45, 10) | one cell, passable, placed wherever the render has them |
| Light lawn patch | (22, 12) | the upper lawn's lighter rectangle |
| Route sign | (87, 14) | with the existing `CherrygroveRoute29Approach_EastSign` event |

Lawn, sand path and the forest come from the primary tileset Cherrygrove already uses, so
the route reads as the same world as the town. The forest is the six-row band the accepted
route and its seam columns already use, on a global row phase, so blocks join the seam.

## What changed from HGSS

- Blossom trees at the west end, the town's own blossom tree, scattered with a density that
  fades from Cherrygrove toward the first ledge (design bible, Chapter 1 world design).
- The sea ridge, lookout, railing, benches and hidden Potion from the accepted route are
  carried over unchanged (rows 29 to 47), as is the Cherrygrove seam window (columns 0 to 9).

## Not verified

- No emulator run. The layout, collision and events were not walked. Collision and
  elevation follow the HGSS plan (trees, walls, gate and sign solid; ledges one-way;
  tall grass encounters) and the carried-over regions keep their accepted values.
- Porymap was not opened on it here (no desktop). The files are the standard Emerald
  layout format and `gbagfx` accepts the tiles and palettes.

## Source and reproduction

Generator: `tools/gba/maps/apoc_route29/build.py ENGINE_DIRECTORY`. It reads the accepted
layout from the branch commit named in `BASE_REV` for the carried-over regions, writes the
tileset to `data/tilesets/secondary/apoc_route29/`, the layout blockdata, `layouts.json`
and the three tileset registration headers, and renders the images in this folder.
