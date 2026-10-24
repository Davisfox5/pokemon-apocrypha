# Corrected terrain: original HGSS grid, heights, directions and joins

This revision replaces the first pass's projected-outline trace with the original
map data. Native source: `9e1c0466b9ff16b4b1cdc29d5d402567bd9c0553`,
[PR24](https://github.com/Davisfox5/pokeemerald-expansion/pull/24).
The first pass remains in Git and `before/`; its checks do not imply visual approval.

The paths previously inherited diagonal outlines from the overview camera.
Original road-mesh coordinates now determine square16px cells, with3px corner
rounding. Route38 is64×32 and Route39 is32×64, the original32×32 chunk composition.
Their actual junction has zero matrix-row offset; all three walking lanes work
both ways, including the original earth ramp into Route38. IDs53/54 and layout
IDs are unchanged. Other maps, tilesets and Ecruteak source retain their bytes.

Original height data also corrects the earlier reversed outer banks and the
flattened farm. Flat original height1–5 maps to native elevation1/3/5/7/9:

| Location | Original height | Native elevation |
| --- | ---: | ---: |
| Route38 main ground | 3 | 5 |
| Route38 southern banks | 5 | 9 |
| Route39 upper farm/main path | 4 | 7 |
| Lower farm paddock | 3 | 5 |
| Main southern valley | 2 | 3 |
| Below southern stair | 1 | 1 |
| Outer eastern bank | 5 | 9 |

The western forest follows its original stepped3/4 contours. The lower paddock
has a real grass ramp below the upper field; it is not one flat enclosure.
Stairs use the original three-cell axis: the farm stair spans two logical rows
and drops4→2; the southern stair spans one and drops2→1. The grass ramp drops4→3.
Original jump ledges remain removed and introduce no jumping behavior.

Wall footprints come from the original terrain mesh, including the lateral
courses and corner returns previously missing beneath the removed trees. A face's
original downhill normal chooses front/back/left/right art. The grass lip sits on
the higher side and the contact shadow on the lower side; front depth follows
the original rise. Shared approved R02/R04/R11/R12 rock textures and the original
Emerald stair material are reused. Continuous contours join rounded outer and
inner turns; there are3 connected rock formations on Route38 and2 on Route39,
with no tiny disconnected rock fragments. Caps at the grass ramp are intentional
ends joining its traversable opening, rather than missing corner pieces.

[Corrected Route38](route38-native.png) · [Route39](route39-native.png) ·
[Corner review](corner-review.png) · [Gameplay](gameplay-contact.png) ·
[Height plan38](route38-height-grid.png) · [Height plan39](route39-height-grid.png)

## Original-data evidence and limits

Only the four relevant original land-data members54–57 were decoded. The
`source/refinement/` directory retains their scoped BDHC files, extracted terrain
triangles/planes, original source/blob hashes and the apicula converter revision.
Original `pret/pokeheartgold` source is pinned to
`6988158691eb6178cff697cda0428045ddcba5fb`; the downloaded archive's Git blob was
verified against that commit. No full ROM, original archive or tool binary is
committed. Existing bounded map/NARC readers and apicula were reused.

BDHC planes use `y=-(nx*x+nz*z+d)/ny`. Original building Y coordinates independently
confirm the sign and scale. Per-cell ledgers separate original plane coverage,
native material and native collision/elevation. Undefined/inaccessible backing
is inferred from adjacent defined planes. The closed northeastern rock pocket's
walking-height plane continues underneath it; its native rim/top height is taken
from the surrounding original model. This is declared rather than counted as a
proved BDHC top surface.

42,507 Route38 and58,777 Route39 wall points had a distinct sampled height on
either side of the original normal. No reversed straight runs remained. Ten
cross-samples at the compound farm/east-bank corner cross three terrain planes;
that corner was reviewed from original triangle winding, native art and actual
gameplay rather than treating the24px diagnostic as a two-plane proof there.

This is still the requested terrain-only preview. Trees, houses, fences, tall
grass, props and characters are absent. City endpoints, encounters and campaign/
HM hooks are unwired. Native footprints are fitted to Gen3 cells; this is not a
claim of byte-identical original DS collision after foreground removal.

## Native verification

- 4096 cells decoded from actual native metatiles/palettes; pixels exactly match
 the reviewed RGB5 layers. No grass/jump/water behavior or open nonzero height seams.
- Actual Porymap6.3.1 Project/Layout exports agree with decoded native images.
- 770 real open-to-blocked boundary probes passed, covering sides and corners.
- All3 lanes of each stair and the junction, plus all9 grass-ramp lanes, passed
 in both directions. Removed jump ledges remain traversable ordinary ground.
- 358,080 RGB5 terrain pixels across10 actual gameplay frames agree with native
 pixels outside the player avatar. Full frames and results are retained.
- Ordinary131072-byte save/cold reload/title Continue passed. A copy of the old
 first-pass save also Continued at its existing position and allowed normal
 movement; the original save was preserved.

The private pair uses327 metatiles and496 allocated glyph slots, with three
palette banks used. Local ARM14.2 build passed; hosted CI and owner visual review
remain pending. Build identities and results are in `preservation.json`.

Reproduce the read-only audit with `refined_review.py ENGINE`; use
`refined_runtime.py ENGINE NEW_OUTPUT --toolchain TOOLCHAIN` for movement/save
checks and `--boundary-part 0` / `--boundary-part 1` for
both boundary halves. `legacy_save.py` checks an original flash-save copy.
`extract_geometry.py` reads the four original members and apicula glTFs.
`refine.py` and `install_refinement.py` are pinned correction provenance for
`fee08659`; they refuse a later HEAD. Edit current native sources thereafter.
