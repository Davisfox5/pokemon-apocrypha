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
generators over layouts the owner has edited or accepted (an element-converted draft
is regenerated each round until then; see the playbook below). Follow the existing
source/branch rules.

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
4. **Clean pixels deliberately.** Preserve the map's wall/cap texture and shading
   vocabulary (on a Gen 4 conversion, the restyled Gen 3 set from the playbook below,
   not the original's own texture). Review the cap, front/side face and corner as a continuous
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
IDs on untouched maps, previous drafts and saves. Generators are provenance once
the owner has edited or accepted a map; never replay them over those layouts.
Keep changes local, use the installed tool workflow, and publish source/evidence
through the shared Git lanes.

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

## Element conversion playbook

Owner-praised on Blackthorn City (2026-10-22, engine PR #26, hub
`gba/art/blackthorn-city/README.md`). The first Blackthorn draft rendered HGSS 1:1,
needed about 1,900 tiles, and had to be split into sections with a streaming engine
hack. The owner's direction was to convert each element instead. The second build did
that, fit one ordinary map on CherrygrovePrimary plus one secondary, and needed only two
rounds of small notes. Adapt the steps below to each map; constants in the Blackthorn
tools are marked as Blackthorn's.

### Steps

1. **Ledger.** Decode the HGSS map (`hgss_render.py` reads land_data, textures, building
   models and permissions). Per 16x16 cell record material, structure (rock top, face and
   its downhill direction, ledge, water, open ground, prop), the cell's HGSS peak height
   and its permissions. Terrace level = peak height minus the town floor height. Doors,
   signs and warps come from the zone events (`hgss_events.py`).
2. **Pick Gen 3 counterparts per element.** Rock: FRLG's General mountain set (nine-slice,
   four inner corners, over-rock variants, cave mouth, ledge and ledge-into-cliff joins),
   recoloured to the HGSS rock ramp. Ground and water: Cherrygrove's own tiles chosen by
   8-neighbour configuration and texture phase. Grass-water edges: Route 30's pond rim
   (its lip is on the grass side), with every water pixel repainted from the receiving
   map's own water at its 32 px phase, its mirror images for sides Route 30 never shows,
   and straight-edge water tiles left as plain lake water. Where a shoreline meets a
   cliff, the rock quadrant's clear pixels take part in the rim (`rock_beyond`,
   `ground(shore=True)`), so the lip runs on to the rock. Center and Mart: the shared
   art, pixel exact.
3. **Autotile rock from terrace levels.** Each quadrant takes the nine-slice piece its two
   edges call for; a cell whose only lower neighbour is diagonal takes the whole
   inner-corner piece; a quadrant facing a lower terrace uses the over-rock variant;
   north-facing edges show as rims, the way FRLG draws the far side of a mountain.
4. **Layering, as FRLG does it.** Rock and props sit on the top layer over plain ground.
   Under a rock edge the bottom layer is the plainest 8x8 block of the ground beyond, so
   edge tiles don't multiply by the ground texture's phase; under an opaque quadrant the
   bottom is the rock top, so solid rock is one metatile. The packer sets the normal layer
   type on walkable cells with top-layer art (walk-behind) and covered on blocked cells.
5. **Props from scratch.** Draw each prop as a sprite at native resolution. For shape and
   proportion, render the game's own model through the map's field camera:
   `hgss_camera.py` reads the camera from pokeheartgold (map header `cameraType`, table
   `ov01_02206478` in `asm/overlay_01_021EABA8.s`; Blackthorn uses type 0, 48.7 degrees).
   Keep props inside their cell columns so a player beside them is not overlapped. Keep
   each sprite to one small ramp (15 colours or fewer) and mirror symmetric parts.
6. **Pack and budget.** One secondary holds 496 tiles (16 kept for door animation) and
   512 metatiles; the shared Center and Mart alone cost about 180 tiles. Count tiles and
   learned colours per element before cutting (`budget.py`). Map palettes are 13 banks:
   the primary's six, the fixed Center and Mart banks, a junction bank and four learned
   banks of 15 colours. Draw props in colours a loaded bank already has where they fit:
   CherrygrovePrimary bank 2 is a wood ramp (bridge, stairs, posts), bank 0 has whites that
   sit with its grass (snow), the Center's bank 8 has a neutral grey ramp (stone). Keep each
   remaining colour family (rock, houses, Gym, water mixes) to 15 colours so one bank holds
   it, and avoid tiles that mix families (railing over water: put the railing on the top
   layer). After packing, compare each element's decoded colours with its art, not only the
   averages: a grey stone once came out brown and a Gym panel brown-red while totals looked fine.
7. **Install and verify every round**: `install_elements.py`, `make`,
   `check_elements.py` (installed decode equals the packer, traversal ledger, reachability
   on foot and by Surf, walk-behind layer types, shared pixels and palettes, budgets,
   preserved map ids, changed-file scope), `runtime_elements.py` (headless mGBA routes,
   VRAM-rebuilt BG layers equal the native image, BG1 coverage over the player in
   walk-behind spots, save, cold reload, Continue), `porymap.py` (fresh clone, export
   equals native, save is byte-identical), `review_elements.py` (HGSS vs native sheets).
8. **Review loop.** Look at zoomed crops yourself before sending anything. Show the owner
   whole-map and before/after crops inline. Answer each note with a targeted fix and
   re-run step 7.

### Traps already hit (check for these)

- Inner corners built from one quadrant of the inner-corner piece look cut out; place it whole.
- Stacked terraces built from over-ground pieces show striped seams; use over-rock pieces.
- Ledges that stop one cell short of a cliff leave a gap; join them with the join pieces.
- A prop wider than its cell column overlaps a player standing beside it.
- A boulder on a plateau raises its own cells into a mound; give it the plateau's level.
- A building on a one-row island makes the shoreline step around it; keep the island
  inside the building's outline.
- Texture crops can carry threshold or shadow rows (a door's dark bottom band); crop them.
- Regular texture repeats (scallop rows on thatch) read as lumpy; follow the form instead
  (straw strands down the slope, lumps on a stone).
- Screenshot sites may be blocked by the cloud environment's network policy; the game's
  own models through its own camera are the fallback reference.
- A borrowed rim tile keeps its source map's water: a shore strip of one repeated 8 px
  tile reads as water from somewhere else. Repaint it from the receiving map's water.
- Learning edge pieces from a map treats trees and paths as "same as me", so a few
  learned tiles carry lips from contexts that don't apply (a grey spur into the water).
  Tiles with few samples are suspect; prefer the configuration's well-sampled pieces.
- A nearest-match fallback can hand a dry grass/sand corner a pond piece, or a shore
  corner a piece with the wrong sides. Restrict the fallback to the same classes, and
  build missing grass corners from the straight edge of each wet side.
- `max(set(tiles), key=tiles.count)` breaks ties in hash order, which changes per run;
  sort first, and confirm two runs with different `PYTHONHASHSEED` match.
- A building drawn to fill its whole blocked footprint comes out stretched (the Gym first
  took eight rows). Take every building's height from the camera render, even where
  HGSS's collision runs deeper than the drawn building.
- Before copying a shared Center or Mart, check the owner's registry
  (`gba/art/johto-common/approved-buildings.json`) for the locked version and its hash;
  a branch cut from an older `main` can carry a superseded draft.

## Worked example

Blackthorn City (above) is the reference for converting a Gen 4 map element by element.
The Route 32 material pass is an example, not a universal map template:
[review and provenance](https://github.com/Davisfox5/pokemon-apocrypha/blob/94bb239d7ea0d470fc5e4ecc85f9630867a1fb3b/gba/art/route32-hgss-blocks/README.md).
It separates original-reference terrain types from walkability and checks actual
native output. Its exclusions and wider Center footprint are declared adaptations;
future maps must establish their own reference registration and exceptions.
