# Johto scenery: transparent foreground review

[Open the interactive catalog](review.html): filter by category, switch between
checkerboard/grass/dirt/water, and compare original versus cleaned artwork.

**52 pieces collected; 29 have terrain pixels removed or separated.** This is
source-art cleanup for review. No native map, collision, jump behavior, item
placement, save or ROM has changed.

## Review by category

| Category | Contents | Review |
|---|---|---|
| Jump ledges | Current Emerald Route 30 ends/middle, Violet straight ledge, existing warm Route 29/31 palette | [Pieces](review/ledges-1.png), [remaining end](review/ledges-2.png) |
| Stairs | Native north/south step modules; current east/west flights | [Sheet](review/stairs-1.png) |
| Signs and props | Current signs, bridge post, railings, Cherrygrove bench/fence, restored HGSS mailboxes, wooden signpost and New Bark windmill | [Sheet 1](review/props-1.png), [sheet 2](review/props-2.png) |
| Flowers | Four route animation variants and current Cherrygrove/New Bark beds | [Sheet](review/plants-1.png) |
| Tall grass | All 16 neighbor combinations, preserving blade pixels and enclosed shading | [1](review/grass-1.png), [2](review/grass-2.png), [3](review/grass-3.png) |
| Water scenery | Violet lily pads; current Cherrygrove rock and reef | [Sheet](review/water-1.png) |
| Native objects | Item ball, Strength boulder, Rock Smash rock | [Intact objects](review/native-1.png) |

[Joined ledges, stairs and grass patch](review/joined-modules.png) show complete
assemblies. Isolated water objects are also shown on grass for mask inspection;
this is not a proposal to put foam-edged water rocks on land.

## Fence, mailbox and signpost revision

[Focused review](review/fence-mailbox-signpost.png) includes the GBA palette export.

- P08: inspection found no remaining grass RGB. The green-looking top edge was
  two inherited blue-green metal shades. They are now neutral gray; every fence
  pixel and the existing transparent gaps retain their positions.
- P09/P10: restored the original HGSS letterbox, including the red front, narrow
  dark slot, curved orange-red top and gray post. The old native prop palette had
  collapsed the red front into dark blue. Both canvas anchors use the same artwork.
  The RGBA master preserves all 24 original object colors. The separate 15-color
  indexed version merges nearby shade steps, retaining the red front and outline.
- P12: added the original HGSS wooden signpost, including its upper peg and full
  support post. Removed the donor path, lawn and ground shadow by traced bounds.

## What changed

- Removed the green contact strip from the warm ledge set; stone texture retained.
- Removed the exact cyan water fringe from Violet's two railings.
- Separated exterior-connected dark-green backing outside the original HGSS
  `egrass_u` plant silhouette. The complete shaded leaf body, enclosed shading and
  every brighter blade pixel are preserved, even where leaves share the ground RGB.
- Extracted current Cherrygrove and New Bark props directly from the pinned native
  engine, removing ground/water palette pixels. This avoids substituting older
  reference props. The Cherrygrove sign also had a gray donor-ground patch outside
  its frame; it is now transparent. The subsequent mailbox revision restores original HGSS color rather than retaining
  the flawed native palette conversion.
- Most ledges, flowers, lily pads and stair pieces already had correct alpha.
  The stairs' actual treads remain opaque. All native item/rock sprite pixels, palette-index assignments and
  frames remain unchanged; the catalog shows only the intact frame.

The two current ledge palettes are presented as existing map families, not invented
alternatives. No regional palette selection is implied by this cleanup. Unused
`ledge-0/1` draft exports are not offered. No standalone current lamps, bushes or
reeds were confirmed, so no historical substitute was introduced. Structural cliff
faces, path borders and shoreline transitions remain separate terrain work.

## Source and integration

`source/*.png` are transparent RGBA masters; `source/*.idx.png` are 4bpp
palette exports, exact except for the explicitly recorded mailbox shade merges. `inputs/` holds before-cleanup **evidence**, never selectable
placement masters. `catalog.json` records source files/hashes, native map crops,
frame geometry, neighbor directions, existing aliases and removed-pixel counts.
The native engine source is pinned to `6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf`.

Native maps still contain their existing art. When integrating these masters,
place destination ground below the foreground and keep event/behavior IDs,
collision, elevation, layer priority, water effects and animations intact. The
asset palettes fit individually; destination tile/palette capacity still requires
checking. Do not regenerate approved maps with their older generators.

Original art: Game Freak / Nintendo / Creatures. Existing project adaptations and
native pixels are retained except for the documented fence color repair and mailbox restoration.

## Reproduce and verify

```sh
python tools/gba/maps/johto_common/scenery.py --engine /path/to/pinned-engine
python tools/gba/maps/johto_common/scenery_gallery.py
python tools/gba/maps/johto_common/check_scenery.py
python tools/gba/maps/johto_common/check_trees.py
```

Requires Pillow and NumPy. Native extraction refuses a different engine commit or
tracked changes to its source maps/tilesets/sprites. Validation checks retained
source pixels, binary alpha, zeroed transparent pixels, exact indexed round trips,
complete native animation sheets and preservation of all non-backing grass colors.
The review sheets were inspected at nearest-neighbor magnification, including
joined ledge/stair runs and a 4x3 grass patch. No emulator was opened.
