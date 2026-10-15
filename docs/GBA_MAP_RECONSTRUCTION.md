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
