# Required map reconstruction workflow

Owner-established rule, 2026-10-15. Applies to every model and instance building,
rebuilding, extending or refining maps. Read this before map work, together with
[shared source rules](GBA_SHARED_SOURCE.md), [production workflow](AGENT_WORKFLOW.md)
and any applicable existing Grok/model instructions. This adds to those rules;
it does not replace them or change the approved GBA pokeemerald-expansion target.
Current owner direction takes precedence.

## 1. Establish the original reference

For Johto reconstructions, use the actual HeartGold/SoulSilver map and available
original map/texture files as the geographic authority. A previous Gen 3 draft,
including another model's output, is comparison material, not the layout authority.
For other regions, identify the appropriate original game reference. Inspect
accepted neighboring maps and rejected drafts to retain accepted art and avoid
repeating known defects. Record reference origin, dimensions, grid registration,
source revision and any unavailable data.

Use available decoded original data when suitable; do not describe a screenshot
trace as extracted terrain or collision. Mark occluded or uncertain squares and
explain their interpretation from neighboring ground, terrain continuity and
known original barriers. Do not invent ground from a character's clothing or
turn a small foreground boulder into an entire cliff block.

## 2. Reconstruct square by square, with separate material and traversal layers

Register the original reference to native **16×16 Gen 3 metatile squares**. Record
scale, origin/offset, crop and any deliberate expansion; keep numbered reference
sheets. Do not assume all maps have the same size or reuse Route 32's offset.
Use 8×8 native tile quadrants where needed to resolve edges and mixed squares.

For every mapped square, record independently:

- **Material and structure:** ordinary lawn, tall grass, dirt/path, ledge and its
  direction/ground beneath, rock top, front/side face and corner, water/shore,
  dock/bridge, stairs and axis, building, tree, prop or other relevant feature.
  Separate background ground from foreground features and canopy occlusion.
- **Traversal:** foot collision, elevation, one-way movement, water access,
  stairs, doors, warps, connections and applicable original gates. An open square
  must remain open and an original barrier must remain closed unless the owner
  authorizes a change. Matching blocked/open status alone is insufficient:
  rock, trees and water are different materials even when all block walking.

Recreate each square using the correct native family, then inspect its joins
with neighboring squares. Preserve original topology: clearings, path widths,
terraces, ledges, tall-grass shapes, woodland boundaries, ponds, cliffs, bridges,
buildings and gate placement. Do not simplify to large approximate polygons or
let automated color guesses decide ambiguous terrain without scene review.

Maintain an editable material grid, traversal ledger and explicit adaptation
list. Separate deliberate owner-approved differences from unexplained errors.
For a new or expanded area without an original counterpart, apply the same grid,
material, footprint and validation discipline; label its design as a proposal
rather than claiming an exact original-game reconstruction.

### Loaded graphics and animation budget

For this pokeemerald-expansion target, each location may choose a primary/secondary tileset pair, but the current map still has only1024 loaded8×8 graphics slots. Keep static art below1008 when the normal16-tile door reserve is required. `field_door.c` uses the upper slots independently of tileset animation callbacks; NULL callbacks do not make those slots safe for static art. Verify actual decoded references and the reserve after packing. Deduplicate exact patterns/H/V flips and already-occluded background before sacrificing silhouettes or inventing terrain patches. Repack only the intended private map pair and prove unchanged visible art elsewhere.

## 3. Assemble coherent native art

Reuse accepted Cherrygrove ground, trees, architecture, terrain and palette
vocabulary wherever suitable. Follow the [shared building-art rule](https://github.com/Davisfox5/pokemon-apocrypha/blob/94bb239d7ea0d470fc5e4ecc85f9630867a1fb3b/docs/GBA_SHARED_BUILDING_ART.md):
copy the approved Violet Pokémon Center and established Pokémart instead of
redrawing them for every map. Author only missing local assets, using original
textures as references and cleaning silhouettes, masks, palette reduction and
native pixel edges deliberately.

Trees have real footprints. Keep roots/trunks in distinct occupied spaces;
allow canopy overlap only where the art supports it. Avoid partial/half trees:
use nearby open space to complete and align trees without obstructing original
paths or opening gaps in barriers. Do not substitute random rock for missing
foliage. Keep background grass, foreground canopy, transparency and layer order
correct at every join.

Inspect cliff tops, front/side walls and corners as coherent terrain planes;
avoid repeated wall blocks across flat tops. Align dirt/grass boundaries,
shorelines, tall-grass edges, shadows, dock grain and deck joins. Stairs must
face and traverse the correct axis. Where the owner requests Emerald placeholder
stairs, ledges, rock walls or cuttable trees, use the corresponding native assets
and retain identifiable placements for later replacement.

Use Porymap/native source formats in the production checkout. Preserve owner
edits, IDs and shared tilesets; do not repack unrelated maps or replay provenance
generators over committed layouts. Follow the existing source/branch rules.

### Native visual cleanup and final review

Required addition, owner-established after the Union Cave finish, 2026-10-15.
Apply the same finish to every affected map and floor, including outdoors.
[Immutable Union Cave example and provenance](https://github.com/Davisfox5/pokemon-apocrypha/blob/013771b80b22774a9458b8b3bb38e0bbb1c0ebe1/gba/art/union-cave-1f/README.md).
Its art/compiler is local to those maps; transfer the following technique.

1. **Inspect the whole shape and its native squares.** Create coordinate-labelled
   original/current/before views. Review straight runs, concave/convex turns,
   narrow barriers, wall tops, front/side faces, water banks, props and transitions.
   Keep the material/structure ledger separate from collision. Original overview
   projections and occluded areas require explicit interpretation.
   For sprite/item removal, verify that the entire donor patch is unobscured.
   Compare source and native repairs for leftover clothing, skin or black outlines.
   Reconstruct occluded corners from the surrounding terrain and clean modules.
2. **Reserve coherent features before spending the tile budget on variations.**
   Keep complete foreground silhouettes, corners, shore outlines, door/step heads
   and roots. Reserve small reusable texture cores for ordinary ground, raised
   tops, grass, water and other local materials. Retain visual texture during
   palette/tile reduction instead of collapsing a surface to a flat fill.
3. **Constrain reuse to compatible geometry.** When an asset pipeline substitutes
   tiles, require matching material masks, structure orientation and layer role.
   Match edge shading and adjacent surface planes as well as overall RGB error.
   An independent nearest-color tile match can chop a wall, fill a corner with
   floor or remove a barrier. Check actual final native entries and pixels.
   Existing directly authored maps can use equivalent manual/native tile checks;
   they do not need a new screenshot packer.
4. **Clean pixels deliberately.** Preserve the original texture and wall/cap
   shading vocabulary. Review the cap, front/side face and corner as a continuous
   surface; local cleanup must retain its detail and depth. Use the available
   native palette budget to align mixed-material ramps without flattening the
   original texture into uniform or repeated shade bands.
   Remove isolated resampling speckle within one
   material/shading plane. Preserve deliberate high-contrast creases and clean
   outlines; avoid blending background grass/floor/water into foreground art.
   Coordinate palette ramps where materials cross banks, so the same wall or
   shoreline does not change hue every quadrant. Keep opaque backgrounds,
   transparent foreground masks, canopy layering and contact shadows correct.
5. **Adapt each receiving join.** Measure the local baseline, opening width,
   rim/wall depth, shoulders, facing, path approach and collision footprint before
   reusing art. Rebuild the complete join and inspect neighboring cells. Union
   Cave's southern light required a four-pixel baseline adaptation; the northern
   corner turned downward and could not be pasted into a straight southern rim.
   Reusable art remains shared; placement and local joins are reviewed separately.
   Align warps to the actual stairs/doorways. Remove superseded marker squares,
   restore the local ground, and inspect the first/last treads and the entire
   connection to the surrounding rock. Stair/door art and warp registration must
   describe the same entrance, including directional approaches and return travel.
6. **Check outdoor specifics.** Align tree footprints and complete canopies with
   supported overlap; preserve original blocked corridors and approved clearings.
   Match grass/dirt/ledge/rock/water types square by square. Inspect tall-grass
   boundaries, coast corners, dock planks and grain, stair axis, building doors,
   gatehouse bypass gaps, foreground clipping and connections in both directions.
   Retain accepted Cherrygrove art and the approved shared Center/Mart assets.
7. **Review the real output and record findings.** Export actual Porymap views;
   inspect decoded native art plus headless gameplay frames at 1x and enlarged
   with nearest-neighbor scaling. Review every affected floor/map and transition.
   Record reviewed coordinates, defects/corrections, uncertain cells, deliberate
   adaptations and remaining approximation. Functional checks support the work;
   the owner provides visual acceptance. Use source/ROM hashes to reuse relevant
   existing proof for unchanged code/art; run new checks after meaningful changes.

Preserve current editable native source, owner modifications, palette/metatile
IDs on untouched maps, previous drafts and saves. Generators are provenance;
never replay them over committed owner layouts. Keep changes local, use the
installed tool workflow, and publish source/evidence through the shared Git lanes.

## 4. Validate actual output, then inspect it visually

Compare the original material grid against **decoded native map entries, tile
art, palettes and behaviors**, alongside the independent traversal comparison.
An authoring label saying “grass” does not prove that the rendered tile is grass.
Inspect mixed squares, edges and transitions at native gameplay scale. Report
which cells were checked, excluded due to occlusion, uncertain or intentionally
adapted. Do not count excluded cells as matches or claim invisible original
collision/event behavior from an overview image.

Open/export the project with actual Porymap and build the ROM. Inspect decoded
native tiles and background/headless emulator frames for corrupted colors,
broken masks/edges, wrong ground, tree layering, cliff planes, stair direction,
dock joins and transition seams. Do not open a desktop game on the owner's
computer. Exercise relevant open and blocked paths, one-way ledges, stairs,
doors, warps, connections and ordinary flash save/cold reload/Continue; preserve
original saves and use copies for compatibility checks. Explicitly report
unwired connections or unavailable campaign interactions.

Fix visual defects before presenting the map. Passing compilation, collision
or traversal tests is **not visual acceptance**. Acceptance remains with the owner.

## 5. Publish reviewable evidence and editable source

Show readable whole-map original/native comparisons, focused material/grid
comparisons and actual native gameplay frames for the affected area. Preserve
before/after evidence and make image links work. Record the exact engine commit,
reference provenance, tool versions, reproducible commands, audit scope,
intentional adaptations and concrete remaining limitations.

Commit and push editable maps/assets/scripts to the shared engine source branch
under the existing PR rules; evidence and narrow reproducible provenance belong
in the hub. Preserve earlier drafts, owner edits, saves and workbenches. Never
commit ROMs, saves, credentials or tool binaries. Keep checks, proposals and owner
acceptance distinct.

## Worked example

The Route 32 material pass is an example, not a universal map template:
[review and provenance](https://github.com/Davisfox5/pokemon-apocrypha/blob/94bb239d7ea0d470fc5e4ecc85f9630867a1fb3b/gba/art/route32-hgss-blocks/README.md).
It separates original-reference terrain types from walkability and checks actual
native output. Its exclusions and wider Center footprint are declared adaptations;
future maps must establish their own reference registration and exceptions.
