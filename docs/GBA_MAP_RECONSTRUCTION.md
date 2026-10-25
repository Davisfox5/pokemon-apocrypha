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
   bottom is the rock top, so solid rock is one metatile. Depth follows each object's base
   row (`pack.above_player`): the player is two cells tall, so a walkable cell draws its art
   above the player (normal layer type, every tile on the top layer) only when its object's
   base lies further south (walk-behind); doors and other base-row cells and every blocked
   cell draw below the player (covered).
5. **Props and buildings.** Each is a sprite at native resolution. HGSS's field camera
   (`hgss_camera.py` reads it from pokeheartgold: map header `cameraType`, table
   `ov01_02206478` in `asm/overlay_01_021EABA8.s`; type 0 is 48.7 degrees) shows HGSS's
   own look, but the Gen 3 reference is the accepted C06 Center: HGSS's own Center model
   rendered orthographic at 38 degrees, 16 px per tile up the screen, reproduces C06's
   silhouette (`hgss_camera.view`, Cianwood's `evidence/elements/c06-angle.png`). Render
   every building at that angle with its own textures, squeezed across to its footprint,
   so roof pitch and doors match the Center (Cianwood's `sprites.py`). Keep props inside
   their cell columns so a player beside them is not overlapped. Keep each sprite to one
   small ramp (15 colours or fewer) and mirror symmetric parts.
6. **Pack and budget.** One secondary holds 496 tiles (16 kept for door animation) and
   512 metatiles; the shared Center and Mart alone cost about 180 tiles. Count tiles and
   learned colours per element before cutting (`budget.py`). Map palettes are 13 banks:
   the primary's six and seven of the secondary's. Blackthorn spends them on fixed Center
   and Mart banks, a junction bank and four learned banks; Cianwood (no Mart) splits the
   locked C06 Center's 21 colours exactly over two banks first, gives each building's
   palette a free bank whole, then fits every other tile into all seven with those colours
   pre-filled (`pack.exact_banks`). Draw props in colours a loaded bank already has where they fit:
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
- A door is walkable but sits on its building's base row. "Walkable plus top-layer art means
  above the player" hid the player's head under the Mart and Center fronts; decide by the
  object's base row instead, and test standing in front of every building.
- On a walk-behind row, opaque tiles left on the bottom layer draw under the player while
  their neighbours draw over it; put every tile of that row on the top layer.
- Before copying a shared Center or Mart, check the owner's registry
  (`gba/art/johto-common/approved-buildings.json`) for the locked version and its hash;
  a branch cut from an older `main` can carry a superseded draft.
- A walkable surf strip drawn as a synthetic foam band reads machine-made. Use the
  accepted beach's own shore cells instead: Cherrygrove's sandbar gives an edge cell per
  side and an outer corner per diagonal; key each strip cell by which side or diagonal
  holds land, join two land sides on the diagonal, and give its sea pixels the map's sea
  at its phase (Cianwood, `elements.shore`).
- A "clean" texture block can sit in a shadow (Cherrygrove's sand beside the dock showed
  dark dashes every 32 px). Use the plain metatile itself, and dump the source pixels
  before trusting a crop.
- HGSS's small blocked bumps (the `etc_a` stones) read as slopes: they turned into short
  cliff faces and one-cell terraces. Label them by material as props, and give their
  cells the height of the ground round them.
- HGSS blocks every cell its taller 3D building covers in perspective. A blocked cell the
  Gen 3 sprite does not reach is an invisible wall; open it and record the adaptation.
- Flat ground details (stones, tufts, decals) always draw below the player, whatever row
  their art reaches; snap them to the 8 px grid so every copy shares the same tiles.
- Greedy bank packing can leave tiles inexact with slots to spare (84 colours in 105
  slots still failed). Pack only the maximal colour sets, largest first, and take turns
  between bank-choice rules (fewest new colours, most shared); pull a lone prop's accent
  colours onto ones a neighbouring sprite already uses.
- The packer also splits a building's palette over banks when it packs the building's
  tile subsets one by one, leaving the props no room. Seed each building's whole palette
  into a bank of its own first, and draw small props in a ramp that is already loaded
  (Cianwood's stones in the cliffs' ramp).
- HGSS's field camera is steeper than C06 (48.7 against 38 degrees), so houses rendered
  through it look steep beside the Center. Render buildings at C06's angle.
- A rendered texture is sheared and resampled, so a glass roof comes out different on every
  tile. Lay one pane of the model's own texture back over the plane on an 8 px lattice that
  steps with the slope; the plane then repeats every two tiles.
- Median-cut palettes drop small accents (a door's orange); quantize each palette group
  with k-means seeded farthest-first. Texture alpha is soft: cut it at 200, and leave out
  the ground shadow quad (`h_kage`) and faces lying on the ground (painted shadows), or they
  render as black blobs and hooks.
- A bottom tile under fully opaque top-layer art is never seen but still costs a tile if it
  carries ground; point it at any primary tile.
- An object over the rock's top-layer overlay makes top tiles that mix rock and object, so a
  house against a cliff shares none of its tiles with its copies. Where no player reaches
  (the cell and the one below blocked), drop the overlay to the bottom layer first.
- An inner shore corner rounded inside its own cell gets a waterline radius of about 6 px
  and reads square. Measure depth from a curved sea edge whose curve starts in the two edge
  cells beside the corner (Cianwood: 10 px, the sandbar's outer corners about 12).
- A borrowed shore piece can carry colours from its source's secondary bank (Cherrygrove's
  sandbar has light-green pixels on its tide line). Map them into the receiving bank, or
  every shore tile needs secondary colours.
- A taller sprite pokes into a row HGSS blocks for its model and can wall off a pocket of
  open cells. Open a blocked cell where only the roof's top edge reaches its lower half;
  the player walks behind that edge.
- Folding near-duplicate tiles by colour distance draws seams (a beam's edge column copied
  into a stripe). Fold a tile only where every changed pixel takes a colour its own
  neighbour already had, a one-pixel edge shift.
- Decals picked by hash cluster (four shells in a column). Keep the eye-catching ones two
  cells apart, and keep decals out of cells under objects, whose edge tiles pick them up.
- A 14-colour fit over a whole building keeps the colours that cover the most and drops a
  surface's shading: the Cianwood Gym's roof shells came out one flat brown. Give such a
  surface its own ramp (its k-means shade farthest from the palette joins and the colour
  whose loss costs least goes) and draw back its fine lines (roof seams, door planks) from
  a marker render of their texture rows. For a building with many colour families (the
  Blackthorn Gym: wood, purple, greys, beams, reds, glass) pick the 14 by family from the
  render's colour clusters.
- Tile folding erases one-pixel lines (a seam pixel's neighbours all hold the surface
  colour). Pass drawn detail to the fold as pixels it may not change.
- A DS texture can be duller than Gen 3 art wants (Blackthorn's straw reads grey on the
  GBA). Lift that texture's pixels by a fixed gain before the palette fit; ranking them by
  brightness onto a ramp flattens the pattern.
- Any blocked cell draws below the player, so under an object or boulder a rock overlay can
  move to the bottom layer and the object keeps its shared tiles; skip an 8x8 tile where
  the sea shows through, whose bank lacks the rock's colours.
- `git checkout BASE -- file` stages the base copy; a reinstall that uses it and a later
  commit of only the map's own files commits those base copies too. Restore base files
  with `git restore --source=BASE --worktree`, and read `git show --stat` before pushing.
- A port city outgrows one secondary (Olivine: about 860 tiles). A derived primary
  (`olivine_elements/pack.py`) gives about 990: keep CherrygrovePrimary's tile 0, the
  open-sea tiles the map draws (1-16) and every tile the map draws at their own indices,
  and its banks 0, 1, 3. CherrygrovePrimary's callback rewrites tiles 1-92 every 16 frames,
  so a derived primary that keeps it can use none of slots 17-92 (Olivine draws none of
  the shore tiles there); give it its own callback that plays the same frames into 1-16
  only (`InitTilesetAnim_OlivinePrimary`, 76 slots freed). The VRAM-parity check then
  proves the sea still animates and nothing past it is overwritten.
- After that, palettes bind first: 13 banks for the Center (2), the Mart (1), five
  buildings and every surface. Map neutral surfaces (deck, quay, fences, paving, sea rocks)
  onto one shared ramp, draw props in a building's palette (benches in the Lighthouse's,
  yachts in the Gym's woods and whites), and seed a small prop group (the flag lines) into
  the Center's half-empty bank.
- A tile mixing a building with a tree, fence or rock has no bank. Deleting the other's
  pixels there (the building "keeps" the tile) draws ground-coloured boxes round the
  building: grass squares in the treetops round the Lighthouse's lantern, gaps where the
  fences meet the Center, the Mart and the flag poles. Put one family on the top layer and
  draw the bottom layer there as the picture with that family left out: the art behind,
  whole, over plain ground. Drawing the bottom as only what shows round the top layer
  makes every such tile unique (Olivine came to 920 tiles that way, 871 drawn whole).
- A corner quadrant that drops onto lower rock on one side and onto grass on the other
  took the grass beyond for both: a strip of grass between two terraces, like a hole in
  the ledge. Paint its clear pixels nearer the rock side as the lower rock's top on the
  overlay and keep the bottom one plain ground; a bottom mixing two grounds (sea and deck)
  needs two banks.
- A 2x2 prop between two levels (a boulder) took each cell's level from its own
  neighbours, so the rock beside it drew a ledge into the boulder. Give the whole prop one
  terrace, from the open ground round it.
- A prop standing on the map's edge with most of it past the edge (HGSS's north-gate flag
  line, over Route 39) shows only stubs on a Gen 3 map, and its stubs share tiles with
  whatever stands beside them. Leave it out.
- HGSS models tree crowns as terrain a level above their trunks, so a tree cell's height
  is not its terrace. Plant trees from their trunk pixels (the brown core of `tree01_un`)
  on HGSS's 2x2 grid and take the terrace from the ground under the trunk.
- Fences are thin in the top-down render; their faces show in the lifted render
  (`hgss-ground-materials.npz`). A blocked floor cell without fence faces is plain ground.
- C06's width is the building's HGSS blocked footprint, not the placement's footprint
  (which counts the shadow quad): Olivine's houses are four cells, not five. Props keep
  their true size.
- A 3D-lit tower (the Lighthouse) is not symmetric in colour; mirror the frame round it
  and keep the tower's own two sides. A barrel roof's stripes curve, so making each row
  repeat wipes them out; mirror about the door instead.

### Kanto towns

Saffron (`gba/art/saffron-kanto/README.md`) first edited FireRed's map, then (owner,
2026-10-24) tried HGSS's plan with buildings rendered from HGSS's models, which the owner
turned down; the third round is FireRed's map again with new buildings cut from Gen 3 map
art (`saffron/parts.py`). Traps hit there:

- A cut part keeps the ground it was cut from. Flood-fill the ground colours from the
  part's edges to transparent (`parts.clear_from_edges`), then look at the part on grass
  as well as on paving: Rustboro's lamp carried pale paving speckles and a grey cast shadow
  that only showed once a lawn went under it.
- A roof widened by repeating columns needs its period: the Battle Palace's roof repeats
  every 8 px, so widening it by whole 8 px bays keeps the tiles shared.
- Thirteen banks hold about 195 colours, and a whole city repacked from pixels fills them.
  What made Saffron fit, in order: snapping each part's colours to a colour FireRed already
  draws within 2.5 5-bit steps, merging colours one step apart in every channel, and an
  annealed exact fit over maximal colour sets with seed restarts (a greedy fit left 740 tile
  uses unplaced). Green spaces from FireRed's own grass, flowers and trees cost no colours.
- A lawn edge drawn on both cells keeps each cell's colours in its own family: the grass
  rim in a grass colour, the kerb in the paving's own darkest and lightest colours, so no
  tile mixes the two.
- After a repack the Center's door metatile drew from banks 10 and 11, not FireRed's 3;
  the sliding door then played in the wrong colours. Index the door frames into the
  metatile's banks and name them in the door's palette list (`install.move_door`).
- A part's colours can all pass the palette fit and still clash: Emerald's deep-blue Battle
  Tower glass under FireRed's purple and teal Silph crown read as a second building. Judge
  a combined part at 1x beside its neighbours, not only by its seams.
- A taller building's roof reaches the row FireRed kept behind the old one: Silph's back
  row still held FireRed's railings and its old city sign, showing above the roof and
  blocking the street behind it. Clear the new roof's back row too.
- A sliding door plays its frames in its own tiles' banks. Once a repack fills every slot,
  the door's bank can lose a frame-only colour, so give the packer the frames' colours with
  the door tiles (`pack.door_frame_colours`).
- With every bank full, a new part's colours cannot simply be snapped to the map's nearest:
  they land in many banks and leave hundreds of tile uses unplaced (Saffron's deck: 580).
  One bank's colours fit (the deck in the station's, which the owner chose as Kanto's own);
  so did the part in few of its own colours (Goldenrod's six). Lines that fall on the cell
  grid help either way.
- A lawn rectangle drawn by eye ran one column into a house and one cell into a tree's
  crown poking up from the row below. Check every lawn cell's FireRed picture holds only
  paving and grass colours before painting it.
- Trees in pairs filled whole walkways though each alone cost two steps at most. Measure
  routes with all trees in, against all trees out, not one at a time.
- A building's foot row can overhang a cell by a pixel or two; such a cell stays
  walkable and draws below the player, so test the solid front one row higher.
- FireRed rooms: a decoder that draws a bottom-layer pixel of colour 0 in its tile's bank
  colour 0 is wrong. On hardware a normal-layer metatile's bottom sits on BG2 over BG3,
  which `DrawMetatile` fills with tile 0x14 in bank 3 (`0x3014`); decode with `frlg.under`.
  Packing a room from its pixels with every bottom pixel opaque sidesteps it.

## Worked example

Blackthorn City (above) is the reference for converting a Gen 4 map element by element,
and Cianwood City (`gba/art/cianwood-elements/README.md`) the reference for a coastal one.
The Route 32 material pass is an example, not a universal map template:
[review and provenance](https://github.com/Davisfox5/pokemon-apocrypha/blob/94bb239d7ea0d470fc5e4ecc85f9630867a1fb3b/gba/art/route32-hgss-blocks/README.md).
It separates original-reference terrain types from walkability and checks actual
native output. Its exclusions and wider Center footprint are declared adaptations;
future maps must establish their own reference registration and exceptions.
