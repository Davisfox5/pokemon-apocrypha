# Apocrypha — shared agent rules

## Start here; keep context small

- Production target: **GBA, Gen 3 2D presentation, pokeemerald-expansion**.
  The owner approved this on 2026-09-10. Do not reopen the platform choice.
- Resuming this work: read `docs/AGENT_HANDOFF.md` after the context index.
  It identifies the last verified build and next task; do not repeat settled choices.
- Read `docs/CONTEXT_INDEX.md`, then ONLY the document/section relevant to the task.
  Read `docs/FOUNDATION_DECISIONS.md` when changing foundation behavior; it is the
  authoritative technical decision record. Current user instructions take priority.
- Do not bulk-read DESIGN.md, archive/, disasm/, old chapter builds, or tool trees.
  Find headings/symbols with scoped `rg`, then read bounded ranges. Expand only
  when a specific dependency requires it. Do not initialize reference submodules
  or load sprite libraries merely to understand the project.
- `DESIGN.md` owns narrative canon. Read relevant sections, not the whole file.
  Legacy engine IDs and implementation notes inside it are historical only.
- DS documentation and source access are indexed in `archive/gen4/README.md`.
  Do not read that archive during ordinary GBA work. Old build pages are redirects.
- `.rgignore` excludes archived snapshots and donor source trees from default
  searches, not from Git. For an intentional lookup use `rg --no-ignore` against
  a specific historical file or donor directory, never the whole repository.
- Claude and Gemini follow this file through their root pointer files. Keep one
  shared rule set; do not maintain different policies per model.

## Required workflow for every map-building task

- All models and instances, including Codex, Claude, Grok and Gemini, must read
  and apply [the map reconstruction workflow](docs/GBA_MAP_RECONSTRUCTION.md)
  before building, rebuilding, extending or refining a map.
- Compare the original-game reference square by square with native Gen 3 tiles.
  Match **specific terrain materials and structure as well as traversal**;
  collision agreement alone does not establish a faithful map.
- This requirement supplements existing Grok rules and other applicable shared
  instructions. Preserve those rules; do not replace them with a per-model policy.
- Inspect actual native renders and headless gameplay, fix visual defects, and
  publish readable source/native comparisons. Functional tests do not establish
  owner visual acceptance.

## Required native visual cleanup — all maps and floors

Owner-established after the Union Cave refinement, 2026-10-15. Apply this to
outdoors and interiors, in addition to the reconstruction and existing Grok/tool
rules above. Use the [detailed cleanup method](docs/GBA_MAP_RECONSTRUCTION.md#native-visual-cleanup-and-final-review).

- Review each map/floor at the same standard. Inspect original/native grids,
  every wall/terrain boundary and corner, then actual headless gameplay frames.
  Keep coordinate-labelled review sheets and specific findings; traversal checks
  alone do not establish visual quality.
- During tile reuse or compression, match the material/structure silhouette and
  orientation. Preserve complete outlines, corners, roots and narrow barriers.
  Give edges, foreground features, doors and stairs priority over spare texture
  variants; retain compact ground/water/plateau texture families.
- Keep one wall/cap treatment across the map and inspect the cap, front/side faces
  and corners as one continuous surface. On a Gen 4 conversion that treatment is a
  Gen 3 rock set restyled with the original's colour ramp (see the conversion section
  below), not the original's own texture. Buildings are the exception: they are the
  original's own models and textures (see "Buildings and props" below). Repair joins
  locally. Retain texture detail during palette reduction.
- Put stair/door warps on their actual visible entrances. Remove superseded
  marker squares and restore their ground; inspect the first/last steps and
  the whole stair-to-wall join.
- Clean isolated pixel noise within the same material and shading plane. Keep
  deliberate creases and crisp silhouettes. Maintain consistent palette ramps
  across neighboring banks; inspect light/dark bands and seams after native
  palette reduction. Keep foreground art, ground beneath it and collision separate.
- On a map built from a render or trace, confirm sprite/item-removal donors are
  unobscured across their full bounds.
  Inspect repaired corners for leftover clothing, skin, outlines and corrupted
  palette pixels; reconstruct the missing local terrain from clean context.
- Fit reused art to the receiving location: width, height, baseline, wall depth,
  shoulders, approach and adjacent corners. Rebuild the complete join when needed.
  An approved entrance or building still needs local seam/footprint inspection.
- Build from accepted shared art and Gen 3 pieces, with the original game as the
  reference for layout, shape and colour, and the original's own models and textures
  for buildings (see the conversion section below). Preserve tree footprints and
  complete canopies, coherent grass borders, cliff tops/faces, stair axis, shore lips
  and dock grain. Reuse the owner-locked shared Center and Mart listed in
  `gba/art/johto-common/approved-buildings.json`.
- Validate actual decoded native tiles/palettes/layers and Porymap output, plus
  relevant headless movement, gates, connections, water, doors/stairs and ordinary
  saves. Review all affected floors/maps and both sides of transitions. Record
  exact source/ROM identities, before/after evidence and concrete remaining limits.
- Keep owner-approved topology and traversal unless a change is authorized.
  Preserve owner work, IDs, prior drafts and saves. Once the owner has edited or
  accepted a map, edit its native sources directly; until then a converted map is
  regenerated from its tools each round (see the conversion section below).
  Adapt the technique to each map's own tilesets and hardware budget. Cave-specific
  art, palettes and generators stay local to Union Cave. Visual acceptance remains
  with the owner.

## Converting a Gen 4 map: convert elements, not pixels

Owner-praised method, Blackthorn City, 2026-10-22: it reached near-acceptance in a few
rounds of small notes. Its building, texture and ground work on Cianwood City and the
Blackthorn houses (2026-10-23) the owner called excellent; "Buildings and props" and
"Ground, sand and shore" below are the standard for every map. Use this section for
every HGSS-to-Gen 3 map. Where an older rule in this file or the linked docs reads
differently for a Gen 4 conversion, this section wins. Details, pitfalls and budgets
are in [the element conversion playbook](docs/GBA_MAP_RECONSTRUCTION.md#element-conversion-playbook);
the worked examples are `gba/art/blackthorn-city/README.md` (mountain town, tools in
`tools/gba/maps/blackthorn/`), `gba/art/cianwood-elements/README.md` (coastal town,
tools in `tools/gba/maps/cianwood_elements/`) and `gba/art/olivine-elements/README.md`
(port city on a derived primary, tools in `tools/gba/maps/olivine_elements/`); read the
script you need, not the tree.

- Do not paste a 1:1 HGSS render onto a Gen 3 grid. Keep HGSS's **layout** (decoded
  heights, permissions, events, cell by cell), but replace each **element** with the
  Gen 3 piece that does the same job: rock terraces, ground, water, ledges, props.
- Build a per-cell element ledger first: material, structure (rock top/face direction,
  ledge, shore), terrace level from HGSS heights, traversal from HGSS permissions.
- Rock: take a Gen 3 piece set with the same role (FRLG's General mountain set for
  Johto/Kanto rock) and restyle it with the HGSS colour ramp. One HGSS layer becomes one
  one-tile terrace. Autotile per 8x8 quadrant, place inner corners as whole pieces, use
  the over-rock variants on stacked terraces, join ledges into cliffs with FRLG's join
  pieces. When unsure, build two treatments side by side and measure both budgets.
- Props and buildings other than the shared Center and Mart: top-layer sprites inside
  their own cell columns, made as "Buildings and props" below says. Do not hand-draw a
  building the game has a model for.
- Depth: the player is two cells tall (feet, and head in the cell above). A walkable cell
  draws its art above the player (layer type normal, every tile on the top layer) only
  when the art's object has its base row further south: a roof or crown the player walks
  behind. Doors and every other base-row cell, and all blocked cells, draw below the
  player (covered). A cell HGSS blocks only because its taller 3D model stands there is
  open ground when the Gen 3 sprite misses it or reaches only its lower half with a
  roof's top edge (the player walks behind that edge). Check depth in the emulator from
  behind and in front of every building.
- Reuse accepted vocabulary (Cherrygrove ground, sea, sandbar shore and trees, Route 30 pond rim,
  the owner-locked Center and Mart listed in `gba/art/johto-common/approved-buildings.json`)
  and colours the loaded palettes already hold (the primary's banks), so tiles and
  palettes stay inside one tileset pair. Every pixel must decode to its exact 5-bit
  colour: give each building a bank of its own, put small props in a ramp already loaded,
  and check every element's decoded colours after packing. Measure per-element tile and
  colour cost (`budget.py`) before cutting anything, and cut where it cannot be seen
  (shared tiles, hidden tiles, overlays moved under objects) before cutting detail.
- When a town's buildings will not fit one secondary even after that (Olivine: 860 tiles
  against 496), give the map a primary of its own derived from CherrygrovePrimary rather
  than splitting the town or cutting buildings: keep tile 0, the sea tiles the map draws
  (Olivine: the 16 open-sea tiles) and every Cherrygrove tile the map draws at their own
  indices, give the primary its own animation callback that plays Cherrygrove's sea frames
  into those sea tiles only, keep banks 0, 1 and 3 (filling only slots no Cherrygrove tile
  draws) and learn the rest (Olivine's `pack.py`). Palettes then bind before tiles do:
  share one neutral ramp across ground surfaces (deck, quay, fences, paving, sea rocks) and
  draw small props in a building's palette.
- Objects have no background. Draw everything that stands (trees, fences, props,
  buildings) in painter's order by the row its foot stands on, by its own opaque pixels, so
  whatever stands behind shows round it; never delete one object's pixels to make room for
  another. Where two palette families meet in one 8x8 tile, one takes the top layer and
  the bottom layer there is the picture with that family left out (what stands behind it,
  whole, over plain ground), so those tiles repeat wherever the art behind repeats
  (Olivine's `elements.split`).
- Johto trees are Cherrygrove's tree (HGSS's own `tree01_re` at 1:1, 32x48 with trunk and
  shadow): trunk in the lower row of HGSS's 2x2 tree block, crown rising into the row
  above, in front of the tree or ledge behind it. HGSS's top-down render flattens trees
  into wide, flat-sided blobs; do not cut trees from it.
- A borrowed edge piece brings its source map's texture and colours with it. Repaint its
  water or ground with the receiving map's own texture at that map's phase, recolour its
  stray pixels into the receiving bank, mirror pieces for sides the source never shows,
  and run a shoreline on under a cliff's clear pixels so it meets the rock instead of
  stopping short.
- Every round: compose, pack, install, build, audit (decode, traversal, reachability,
  walk-behind, palettes, budgets, ids, file scope), headless mGBA with VRAM parity,
  Porymap round trip, then look at the images yourself and show the owner
  before/after crops inline. Answer review notes with targeted fixes, not rebuilds.
  When a reinstall restores base files, use `git restore --source=BASE --worktree`
  (`git checkout BASE -- file` stages the old copy, and a later commit takes it), and
  read `git show --stat` before every push.
- Regenerating the map from its tools each round is the method while the map is still
  the agent's draft. Check `git log` on its layout and tileset first: once any commit is
  an owner edit, or the owner has accepted the map, stop regenerating and edit the
  native files. Keep generators deterministic (no hash-order tie-breaks), so a rerun
  reproduces the installed map exactly.

### Buildings and props

The owner-locked C06 Center is the reference: every other building must look like the
same game standing beside it. Worked code: `sprites.py` and `hgss_camera.py` in
`tools/gba/maps/cianwood_elements/` and `tools/gba/maps/blackthorn/`.

1. **Render the model, do not draw it.** Take the building's own HGSS model and its door
   model (the door's offset from the building in HGSS's placements) with their own
   textures, and render them at C06's angle (owner, 2026-10-23): orthographic, 38
   degrees, 16 px per tile up the screen, squeezed across so the visible model fills its
   footprint (`hgss_camera.view`; the fit is Cianwood's `evidence/elements/c06-angle.png`).
   HGSS's own field camera (48.7 degrees) is only a reference for HGSS's look; it makes
   houses steep beside the Center. Cut textures out at alpha 200, and leave out the ground
   shadow quad (`h_kage`) and faces lying on the ground (painted shadows). The sprite's
   bottom edge is the bottom of the building's base (door) row.
2. **One bank per building.** 14 colours plus C06's outline colour round the silhouette.
   Fit them with weighted k-means seeded farthest-first, so small accents (a door's wood,
   a knob, a poster) keep their own colour; buildings built on one model share one
   palette. When a building has more colour families than 14 slots hold (a Gym's wood,
   bands, hall, beams, emblem and glass), pick the 14 by family from its render's own
   colour clusters. When a fit flattens a surface's shading (a roof gone one brown), give
   that surface its own ramp: its own k-means shade farthest from the palette joins and
   the colour whose loss costs least goes. The packer seeds each building's palette into
   a bank of its own before fitting anything else.
3. **Draw back the detail reduction loses.** Fine texture lines (roof plank seams, door
   planks) vanish at sprite size and 14 colours. Find where they fall with a marker render
   (the texture's line rows or columns recoloured, rendered at 4x) and draw them one pixel
   wide, one step darker on that surface's ramp; plank gaps on the darkest shade take the
   outline colour. A regular texture lattice (glass panes) is laid back from the texture
   itself on an 8 px lattice that steps with the slope, so the plane repeats every two
   tiles.
4. **Lift dull DS textures.** A texture that reads grey on the GBA (Blackthorn's straw) has
   its pixels lifted by a fixed per-channel gain before the palette fit, toward the Gen 3
   colour the owner has seen and liked. Never rank pixels onto a ramp by brightness; that
   flattens the pattern.
5. **Keep tiles shared.** Mirror symmetric roofs on an 8 px axis. Fold a tile into a more
   common one that differs only by a one-pixel edge shift or a render speck, and never
   fold away a drawn line. Every copy of a building shares its tiles; in a blocked cell
   the rock's top-layer overlay drops to the bottom layer under an object or boulder, so
   the object keeps those tiles (except an 8x8 tile where the sea shows through).
6. **Props and plants at Gen 3 quality.** Rocks and stones come from HGSS's own textures,
   resampled into a Gen 3 ramp, best one already loaded (Cianwood's stones use the
   cliffs' ramp). Plants are drawn by hand the Gen 3 way: dark outline, lit blade edges,
   a short ramp, never flat blocks or single-colour shapes. Snap ground details to the
   8 px grid so every copy shares its tiles.
7. **Check against the source.** Put each finished sprite beside HGSS's model at the same
   angle, unquantized, at 5x: every colour family and every visible line of the model
   must be in the sprite. Show the owner the sprite in place, before and after.

### Ground, sand and shore

Owner, Cianwood, 2026-10-23: flat sand read as boring, flat plants as "Atari level", and
square inner water corners as unfinished.

- Sand is Gen 3 sand: a 16 px cell of base colour with scattered light grains, each with
  a shade pixel, and a few darker grains, plus one-tile decals (a second scatter, a
  ripple, a shell, pebbles) in about half the open cells, picked by a fixed hash. Keep the
  eye-catching decals two cells apart, and keep decals out of cells beside an edge or
  under an object.
- Grass meets sand on rounded corners (a blurred cell mask, so straight runs stay on the
  cell edge) and the sand side carries the transition: alternating grass and rim pixels,
  then a dithered rim row.
- A shoreline's inner corners curve into the land with the same radius as its outer
  corners, every band (wet sand, foam, sea) keeping its distance from the curved sea
  edge. The curve starts in the edge cells beside the corner; one drawn inside a single
  cell reads square. Wet sand runs as one even band along the tide line.

## Kanto towns: HGSS's Kanto, the Olivine way

Owner, Celadon, 2026-10-26. Two rounds were turned down: FireRed's map with the changes
painted on ("pretty terrible"), then HGSS's plan drawn in FireRed's own pieces ("a slightly
updated version of the FRLG maps"; its palette and features "horribly, horribly boring").
The owner then chose HGSS's own look, made the way Olivine was. A Kanto town is converted
from HGSS as a Johto one is: follow "Converting a Gen 4 map" above (element ledger from
HGSS's map data, HGSS's ground textures at 1:1 on the Gen 3 grid, every building rendered
from its own HGSS model at C06's angle). The worked example is
`gba/art/celadon-elements/README.md` (tools in `tools/gba/maps/celadon_elements/`).
Saffron (`gba/art/saffron-kanto/README.md`, FireRed's map) stays as accepted; its rules
below on new maps, rooms, combined buildings and lines still apply.

- Kanto's own colours: HGSS's Kanto textures (Celadon's map texture set) give the streets
  their paving and brick. Grass, trees and flowers come from the games' own tilesets
  (below), not from resampled or recoloured HGSS crowns.
- Its ground at 1:1: each HGSS texture repeats at its own size in the world's phase (one
  16 px quadrant where an edge runs over it), joins drawn the Gen 3 way (Celadon's lawn edge:
  HGSS's tama_fuch bands on the lawn side, the cell mask blurred so corners round).
- The story's changes are HGSS's own models where the game has one, retextured where the
  story asks (the Gym's roof glazed with its own window glass as the Botanical Gardens, its
  emblem replaced by a leaf; the Olivine parasol bench recoloured as a rainbow market stall),
  placed on HGSS's lots. Change only what ten years and the story change, each change
  answering the owner's brief or a DESIGN.md line.
- A town with many buildings gets a tileset pair wholly its own (no borrowed primary): seed
  every palette bank with a job before the exact fit (`celadon_elements/pack.bank_seeds`), snap
  the ground's textures onto shared ramps, and spend tiles where they show (one prop in all
  its colours rather than a variant per colour; a mirrored building with a `keep` box over
  what differs). The traps are in the reconstruction workflow.
- Make a new Emerald-format map beside FireRed's (its own name, `gMapGroup_Kanto`,
  FireRed's MAPSEC, `REGION_KANTO`, `build_target` emerald); never edit the `_Frlg` maps.
- An interior Kanto needs is FireRed's room, or a room built from FireRed's rooms cell by
  cell with other rooms' objects laid on by their own pixels, packed into its own
  secondary on `gTileset_Building` (`saffron/interiors.py`, `celadon_elements/interiors.py`).
  Exit mats keep `MB_SOUTH_ARROW_WARP`; other FireRed behaviours become `MB_NORMAL` until
  their scripts exist (their numbers mean other things in Emerald: FireRed's Gym pads would warp).
- Two buildings combined must read as one: one roof line, one facade, one crest, the
  difference carried by details (Saffron: each school's door curtain). Two halves under a
  shared roof is the failure the owner named. A wing must change the silhouette of what it
  joins, built onto it, not set beside it.
- Where a line (a track, a bridge) meets a building, the building takes it in: build the
  meeting in the building's own pieces and carry the line's lines on into it (Saffron's
  station). A line that stops against a wall reads as dumped there.
- A piece another region also has (the Magnet Train's deck) may take its form from that
  town's native art (kept as a source file with its branch and commit), but Kanto's is its
  own: recolour it in the Kanto town's palette. Check open PRs for towns other agents built
  before saying one does not exist.
- Doors to unbuilt interiors and gates to unbuilt routes are solid.

Owner, Celadon rounds 5 and 6, 2026-10-26. Buildings drawn from scratch read as "something out
of a game for the SNES"; flat elevations as "very 2D"; invented trees and flat flowers as
custom; hard ground joins and English signs as tacky. These rules hold for every town:

- **No text on buildings.** No English lettering on any building, awning, marquee or canopy
  (no shop names, no "HOTEL", no "CAFE"); a building's name belongs in its sign event. The one
  exception the owner allowed: Japanese lettering where HGSS's own building carries it
  (Celadon's Dept Store banners, タマムシ / デパート). Symbols are fine (a Poke Ball, a seven).
- **The HGSS model is the base, always.** Every building starts as its own HGSS model brought
  down to Gen 3 (`celadon_elements/hgss_gen3.py`): rendered at 45 degrees, unsqueezed, at the
  scale its role asks, with the Gen 3 finish (`gen3_art.gen3_finish`: shade under eaves, lit
  upper and left edges). The story changes it slightly, on its own textures or the converted
  art (a door, a colourway, repainted banners); never redraw a building that HGSS has. A town's
  houses are that town's own HGSS houses, not another region's.
- **Pitch.** Hand-drawn props (market stalls) are drawn at the buildings' 45 degrees, their
  tops visible (`custom_art.stall3d`).
- **Nature from the games.** Flowers are cut from the games' tilesets with their ground keyed
  out (`celadon_elements/nature.py`; Gen 3's flowers, recoloured petal ramps for more colours).
  Trees are the repo's own cut-outs, whole crowns on clear backgrounds (`nature.TREE_ART`:
  Cherrygrove's, the Johto restart crown, Sandgem's cone, Floccesy's great trees). Never key a
  tree out of a tileset by its grass colours: every leaf sharing a grass colour goes and the
  neighbouring cells' shadows stay, so crowns arrive holed and boxed (owner, Celadon,
  2026-10-27). Forests stand in staggered rows two cells apart, drawn by foot so each crown
  overlaps only the trunks behind it; no tree covers a prop or stands in front of a building.
  A park may mix regions. Never invent a tree or recolour one into a new kind.
- **Smooth joins.** Grass meets every other ground (dirt, paving, brick, a cycleway, a pond's
  coping) through FireRed's path edge pieces, quadrant by quadrant (`nature.grass_edges`).
  Flowers stand on whole grass cells, never cut by an edge.
- **Neighbours.** Houses stand wall to wall in rows, not each in its own yard, a cell back
  from the road they face.
- **Bridges from the games.** A bridge is a Gen 3 bridge taken from its tileset (Celadon's
  are Route 104's boardwalk, `borrowed.boardwalk`, its middle row repeated for a wider
  street), with the water shaded under its south edge.
- **Layering.** No standing object's pixels may cover another's (a lamp on a stall, a bench
  under a lamp, a sign over a marquee) except trees behind a building or behind each other;
  flowers stand only on cells nothing stands over. Run the overlap check
  (`celadon_elements/concept.overlaps`) and clear every pair before showing the owner.

## Planning a new town: the change plot

Owner, Celadon, 2026-10-25: plan every new or remade town this way, and show the owner the
plot before building anything. Worked example: `gba/art/celadon-elements/README.md`.

1. **Story brief.** Read only the town's own lines: DESIGN.md (grep the town name), its
   chapter's `CHAPTERn_SCENES_SPEC.md` section and retheme stubs, and its rows in the
   region's `*_ITEMS.md` and `*_BATTLES.md`. Note every building, character, sign text and
   service the story needs there.
2. **Other agents' work.** Search open and closed PRs and branches in the hub and the
   engine for the town before planning (Saffron's Magnet Train deck came from Codex's
   Goldenrod).
3. **Decode HGSS's map.** Decode HGSS's version from pokeheartgold
   (`celadon_elements/hgss_source.py`: header id and area bank from `src/data/map_headers.h`,
   events from `zone_event/NNN_ZONE.json`): it is the base, Game Freak's own ten-years-later
   revision of the town, and its textures and models are what the town is drawn with.
4. **Ledger.** List HGSS's elements (streets, lots, lawns, water, woods, each building) and
   the Gen 3 element each becomes (Celadon's README has the table), the story's changes on top.
5. **Source art.** For each new building or prop, find the HGSS model it can be rendered
   from and render it at C06's angle (Celadon: the parasol bench as market stalls, the Gym's
   own window glass for the Gardens' roof); list HGSS's other bm_field models first
   (`celadon_elements` README: lamps, banners, planters, flower shops).
6. **Change list.** Number each change and tie it to a DESIGN.md line, a scene spec line or
   an HGSS letter. Say where every displaced door, interior and warp goes so none goes
   dead. End with what is out of this pass (dialogue, unbuilt interiors and gates).
7. **Plot.** One image: HGSS's town area with its zones, the story's numbered changes on
   it, paths (a bike lane, a canal) as lines. Save it as the town's `evidence/plan.png`.
8. **Owner's call.** Send the plot and the list. Build only after the owner approves; a
   revised plan gets a revised plot.

## Ownership and autonomy

- Owner: story, creative direction, visual review, playtesting, approval/revisions.
- Agents: map/asset design and production, coding, gameplay within approved canon,
  tooling, integration, testing, visual inspection, and all revision labor.
- Do not hand routine drawing, pixel cleanup, palette editing, frame assembly,
  collision painting, map placement, import/export, or editor operation to the owner.
  Automate or perform it. Make routine reversible technical choices independently.
- Use existing tools, source formats, scripts, and narrow adapters first. Build a
  new editor only when a demonstrated recurring problem justifies it.
- Do not invent canon or silently change character roles. Label creative proposals.
- Follow `docs/AGENT_WORKFLOW.md` for the relevant production/validation work.

## Non-negotiable scope

- Five playable regions: Johto, Kanto, Hoenn, Sinnoh, Unova; twenty sanctioned
  badges; original regional identity with substantial changes roughly a decade on.
- Classic Pokemon party, battle flow, menus, and PC interaction. Explicit exceptions:
  canonical Fairy typing throughout; late-game Mega Evolution; Shadow in Wes's
  gym; Terra confined to the designated final gym leader.
- Terra and Shadow are additional custom types alongside the standard types.
  They are assigned before battle, not activated through mid-battle transformations.
  Terra is not Terastallization; Shadow is not merely a status condition. Do not
  expand their gym-specific scope or invent matchups/typing assignments.
- Canonical species: Gen 1-5 plus documented picks, currently Sylveon. Use existing
  suitable sprites/data. No generated Pokemon redesigns or blanket later-gen roster.
- **30 PC boxes / 900 slots**, familiar PC interaction, ordinary persistent saves.
  This is an approved target; implementation and save fit still require verification.
- Preserve engine flags needed for functioning systems. Replace original campaign
  triggers deliberately; never indiscriminately wipe or reuse flags/variables.
- Preserve independent optional-event state and stable IDs. No silent save resets.

## Current implementation phase

The GBA toolchain, upstream/roster builds, and baseline save tests pass; see
`docs/GBA_BASELINE.md` for commands and limits. The owner deferred the unresolved
30-box save/autosave architecture on 2026-09-10; do not treat the isolated prototype's
limits as universal GBA limits or resume that investigation without a relevant task.
See `docs/GBA_STORAGE_PROTOTYPE.md` for evidence and the deferred questions.
Automatic checkpoints and an emulator dependency are not approved. Production still
has 14 boxes; the 30-box requirement remains open, not waived or qualified.
The configuration audit is in `docs/GBA_MECHANICS_AUDIT.md`: twenty-five settings
are pinned, including the owner-approved Gen 4–5 per-move physical/special split.
The Gen 5 experience package (rules and yields), Gen 5 species base stats with
canonical Sylveon/Mega exceptions, Gen 5 ability sets with eighteen owner-chosen
exceptions, ORAS level-up learnsets and Gen 5 move data are approved, applied and
verified. The open decisions are the TM/HM list, Hidden Ability access, move flags
and breeding.
Three gaps stay open and must not be assumed away: how the player obtains a Hidden
Ability; move tutors, still Emerald's 30 and expandable only through map script
data; and breeding/inheritance rules, all still at inherited Gen 9 defaults.
The move economy is tiered by owner design: TMs are the generic toolkit and
signature moves belong to origin-locked regional tutors. Read
`docs/MOVE_ECONOMY.md` before touching TMs, tutors or move distribution. The TM list is settled at 100 single-use TMs, **rebalanced on 2026-09-13** across the eighteen types: Johto, Kanto and Hoenn carry nineteen each so that three Fairy TMs can close the list, since every offensive Fairy move is Gen 6 or later and no region could stock one. Dragon went from one attacking TM to three and Normal from ten to seven. The HM list is now **11**: the vanilla
eight plus Defog, Rock Climb and Whirlpool, which cover every field move the five
regions need as originally built. Whirlpool was built from nothing, modelled on
Waterfall. That expansion renumbered every item id from 690 up; no player save
exists, so nothing was invalidated, but item ids should now be treated as frozen.
**The tutor economy is 150 moves, every one assigned to a region** -- 89 historical TM moves, 12 vanilla Emerald tutor moves and the 49 Tier 2 signature moves; see `docs/TUTOR_ROSTERS.md`. Regions were assigned on identity (landmark, gym, species, type character), not introducing generation, which had left Kanto with 44 and Hoenn and Unova with 8 each. The split is Johto 31, Kanto 28, Hoenn 30, Sinnoh 35, Unova 26. `gTutorMoves[]` holds exactly these 150. That is the data layer only: every move is teachable, none is obtainable, because no tutor is placed, priced or scheduled. No TM or HM is placed either. No tileset assigns `MB_WHIRLPOOL`, and
the HM badge gates are vanilla placeholders against an eight-badge assumption. Egg-move data itself is reviewed and settled:
it has no generation switch and nothing egg-exclusive on this roster is unbalanced. Any change to moves, TMs or learnsets must
re-run the Fairy-coverage check; that trap has already been hit once.
Read that concise audit before changing gameplay settings; do not globally change
GEN_LATEST or treat inherited settings as approved. Independent nonvisual work may
proceed; persistent-state integration still requires a qualified save design.
The owner has explicitly authorized isolated Cherrygrove map/art production and
independent Claude/Grok interpretations. Follow docs/GBA_REMOTE_HANDOFF.md for
remote setup. Broader campaign production remains subject to its scoped requests.
Production source is `game/`, a pinned submodule plus the tracked roster and mechanics patches
in `gba/`.
**Shared map source is the `apocrypha` branch of `Davisfox5/pokeemerald-expansion`**
(current accepted Johto maps as Git history; see `docs/GBA_SHARED_SOURCE.md`). Map and
script work goes there as commits and PRs, not as new standalone patches. Porymap opens
that checkout directly. Preserve local changes and track new engine edits in patches or an
explicit source fork; never leave their only copy in a dirty submodule.
The root `make build` is still a legacy DS asset command, not a GBA ROM build.
Do not report a proposed dependency or configuration as installed or tested.

## Preserve work and report evidence

- Keep DS source trees, tools, original assets, and dirty/untracked work intact.
  They are reference/fallback material, not the production target. Use a separate
  path for GBA production; do not overwrite a donor submodule.
- A platform fallback requires a documented hard blocker, attempted GBA remedies,
  and an explicit owner decision. Never switch automatically or develop two targets.
- Record pinned revisions, configuration, relevant checks, and measured capacity.
  Distinguish estimates, source inspection, compilation, runtime tests, and approval.
- Inspect visual work yourself before owner review once that work is in scope.
  An image passing validation does not prove successful in-game integration.
- Never commit ROMs, player saves, credentials, virtual environments, or vendored
  tool binaries. Keep source assets, provenance/credits, and reproducible tooling.
