# City production playbook — Goldenrod case study

Owner-established exemplar, 2026-10-19. The owner accepted Goldenrod's initial
native exterior, subsequent building and equipment passes, and the completed
boardwalk. Their instruction is to carry this quality and process into every
city. This document complements [the required reconstruction workflow](GBA_MAP_RECONSTRUCTION.md),
not a replacement for it. Native engine sources remain authoritative.

## What made the result work

Geography came from the actual HeartGold/SoulSilver map. Art was reconstructed
into real Gen 3 palettes, tiles, metatiles, foreground layers and map sections.
The finish came from repeatedly examining complete buildings and their neighbors,
then correcting local materials, silhouettes, occlusion and movement together.
An attractive overview was only the beginning: actual Porymap exports, decoded
native pixels and emulator views all had to agree. Owner feedback drove focused
revisions rather than broad regeneration.

Goldenrod's working source and evidence live in
[`gba/art/goldenrod-city`](../gba/art/goldenrod-city/README.md). Its native engine
is `Davisfox5/pokeemerald-expansion`, branch `codex/goldenrod-city`, final verified
commit `eb63c24cb7e28c7de1eddd7db0b693a6510b29d4`. The corresponding published
hub checkpoint is `5da5cda94a2cac01491c06c7ae9fec97bd67b055`.

## 1. Establish the original city before drawing

The retained reference is Bulbagarden's `Goldenrod_City_HGSS.png`, 1330×885.
Registration is 1:1, origin (0,0), onto an 84×56 metatile canvas (1344×896 pixels).
The last 14 columns and 11 rows are explicit edge adaptations. This is an overview
reference, not extracted DS collision or height data; occluded ground and projected
heights required interpretation and were recorded as such.

We located the Radio Tower peninsula, fountains, streets, station annex, curved
Magnet Train canopy and raised railway, Gym and Flower Shop, Game Corner,
department store and Bike Shop, Underground mouths, residential blocks and south
arch before considering extra decoration. Building footprints and street-facing
approaches were recorded independently of their roof silhouettes.

Maintain distinct editable layers: material/structure, foot collision, elevation
and foreground/roof coverage, tree roots, and feature/entrance metadata. A blue
square cannot establish water collision, and a blocked square cannot establish
whether its art should be a railing, cliff or tree. Keep a numbered grid and a
ledger, including interpretations. Inspect both the whole city and each square.

## 2. Fit the native hardware without sacrificing identity

Goldenrod uses 12 connected native Porymap sections. Dense architectural texture
would not fit a single conventional private tileset pair. Sections retain native
map, border, tile, metatile, palette and attribute files; a derived city-specific
viewport glyph cache preserves that detail in gameplay. The cache is an adapter
for actual native source, not a flat screenshot used as the map.

There are 13 background palette banks, with index 0 transparent and banks 13–15
reserved for UI. Coherent families cover wood/terrain, water, mint/teal, cream
station stone, gold roofs, residential roofs/windows, highrise stone/glazing,
paving, orange/red shops, purple/gold architecture, shared foliage, and the two
canonical Center families. Independent nearest-color assignment initially
created quadrant checker seams and wrong vent/window hues. Explicit family
selection repaired this; palette continuity is a design constraint.

Reuse exact glyphs and their horizontal/vertical flips. Reclaim only slots proved
unused by every unchanged live quadrant. Preserve existing IDs and references.
Do not spend the budget on texture variants before reserving complete silhouettes,
roof rims, corners, shore lips, tree roots and layer transitions. Goldenrod's final
largest private pair uses 904/1008 glyph slots. Its adapter has 8,468 global glyphs
and a 25,066-byte allocation. These numbers are local to Goldenrod, not assumptions
for another city. Choose simpler conventional tilesets when they suffice.

The renderer needed two real fixes: internal city transitions must not overwrite
cached VRAM with a secondary tileset reload, and heap reset must forget the cache
pointer before initializing the heap. Emulator background reconstruction must use
`sGpuRegBuffer` scroll shadows: hardware HOFS/VOFS registers are write-only.

## 3. Reuse approved assets, with receiving context kept separate

The approved 32×48 tree and 80×80 Violet Center were copied with immutable source
hashes. The established Pokémart must likewise be reused wherever appropriate.
Foreground transparency, terrain beneath, collision and roof coverage are separate
assets/decisions. Never paste an opaque lawn or pavement rectangle with a building.

Goldenrod initially used 46 complete shared trees. After southeast repairs it has
49. Each tree has a full crown and a distinct 2×2 root footprint. Partial source
conifers were removed, and their ground/fence was rebuilt from verified clean,
same-phase donors before complete native trees were placed. The final four stand
at x=1184,1216,1248,1280, y=848. A clipped brown remnant against the eastern cliff
was repaired with matching cliff texture rather than another foliage patch.

## 4. First native pass: finish the architecture and actual boundaries

Initial repairs removed clipped trunks, bad removal donors and roof damage.
Camera borders were made from complete ocean, lawn/tree, cliff and paving cores.
An off-map view must not expose blank aliases, chopped crowns or repeated props.
The northern fence, gate bypass and east cliff were checked as barriers.

The south arch illustrates why color parity alone is insufficient. Its cap was
initially below the player. A local upper-layer mask duplicated the correct stone
without changing the static RGB image, leaving the roadway transparent and the
pillars solid. Both directions of walking beneath the arch and railway were then
recorded. Every such feature needs a sprite-aware review, not just a map export.

This first pass was owner-accepted at engine
`f439df15cc6f4c95df2846da353c9e4e2549fcd2`, hub
`3b550ae79ea719f65e267249dc3af2b1c015202c`.

## 5. Building-by-building second pass

The owner asked to isolate buildings, compare references, clean rough pixels and
reuse a well-designed module wherever compatible. We made 39 coordinate-labelled
HGSS / first-pass / revised context comparisons. Each context includes neighboring
ground and structures: a perfect isolated facade can still have a bad join.

We preserved roof rims, vents, door and window frames, side planes and deliberate
creases. Isolated low-contrast single-pixel noise was removed only within one
material/shading plane (the recorded conservative pass required at least seven
of nine neighbors and a channel difference at most 48). There was no blanket blur.
Gold roofs received a coherent repeating 6×5 material core under their original
rim/vent/side masks. The stacked northwest highrise required both roofs, not just
the upper 56 pixels. Compatible cleaned masters were reused without forcing
incompatible silhouettes to share a model.

Native palette fitting changed 126 background and 114 foreground pixels in this
pass; these were documented reductions, not described as lossless. Inspect after
conversion as well as before: a clean RGB master can become noisy in RGB5 or an
ill-chosen palette bank.

Engine `bb54d528df4f26d457b3b1c5f43bf4de41b3b50f`, hub
`19c905799ead42f1099797e2555212d573825fc8`. Context sheets and exact reproduction
records are under `evidence/refinement/`.

## 6. Center neighborhood and Radio Tower equipment redesign

The owner noticed that the Center obscured a house on its left and a lamp on its
right. Diagnosis mattered: the 80×80 PNG already had proper alpha (5,679 opaque,
721 transparent pixels). The error was an earlier 96×96 ground replacement at
(784,568)–(880,664), which erased its neighbors. Removing a background from the
already-transparent PNG alone would not have fixed the city.

We restored the local reference neighborhood, removed only the superseded HGSS
Center and reconstructed the missing paving from genuinely unobscured donors.
One candidate donor carried roof fragments and another a curb; visual inspection
caught the ghost lines and both were rejected. The unchanged canonical Center
moved eight pixels left, to (792,576). All 5,679 canonical native pixels remain
exact. The west house regained its full roof/facade and coherent violet-window
palette; the right lamp regained its full silhouette and correct foreground.
The lamp base is solid at (55,41); the Center approach (52,41) stays reachable.

For the tower, we authored one clean 24×30 transparent dish and reused it three
times, mirroring the rear-facing one. Old dish corners and deck underneath were
repaired. A straight three-pixel metal mast and foot replaced the rough seven-pixel
antenna. Unneeded opaque roof foreground was removed from equipment quadrants:
roof stays in the background and silver hardware has its own transparent layer.
Otherwise native palette selection can turn the dish into water/teal colors.

Only the recorded local regions changed; outside pixels, shared trees and Center
master were protected. Engine `fdaf387b1ef1b0704e4f6a2f4ac0c24444d900a7`, hub
`bcfb58b5458a36e3ccd625079dbb507bcf9e8a47`. See `evidence/center-radio/`.

## 7. Develop a ten-year addition as an actual map concept

The owner next requested a more advanced city, with concept art before native
production. An initial presentation board/diagram was unsuitable: the owner
wanted an actual reproducible overhead map. The corrected concept kept the city
scale, footprint and roads visible in one map image. Always show images inline
when presenting visual work.

Feedback retained the station improvements, rejected bikes, and required flower
beds to join the existing fencing structurally rather than float over posts.
The owner then proposed a Coney Island-like market/boardwalk northwest of the
black station-annex tower, with a Ferris wheel and Slateport market character.
Department-store expansion was explicitly withdrawn. The accepted concept was
retained before the owner authorized its native build. Do not treat these
Goldenrod-specific creative decisions as a license to add carnivals to other cities.

## 8. Translate the approved concept into native modules

The new deck occupies (352,96)–(624,240), with a south apron to y=256, gangway
(544,240)–(608,416), and landing (560,416)–(592,432). Two complete walkable metatile
columns, 35 and 36, connect it to the city. A water channel keeps it separate from
the Radio Tower peninsula. Rails have correctly oriented runs, corners and ends;
the gate has a real opening. Planks, fascia and piles form a coherent structure.

A topology check caught the old shoreline collision still closing the landing.
We opened only the authorized entrance, repaired source flag/ground remnants and
walked the real route. We did not mask the error with a teleport. Another walking
test accidentally routed through a prize counter; the test route was corrected
to the real aisle instead of opening the counter.

The Ferris wheel became a 128×144 transparent native master, at (432,48), with
eight upright cabins, spokes, teal supports and a manually restored star hub.
Existing bank 11 was used; alpha holes stay clear. Its support cells are solid,
while the approach is open. The rear deck moved north one metatile to y=96 so a
player at (29,7) sees the complete wheel in the ordinary 160-pixel viewport.
It is explicitly static scenery, not an implemented ride.

Three separate 48×48 market stalls sit at (368,128), (416,176), (544,160).
Awnings are foreground, wood is background and counters are solid. Their approaches
remain accessible. Native-size deck, rails, lamps, bench, kiosk and planters use
small coherent palettes rather than attaching ground rectangles to each prop.

The station board is 64×24 at (768,376). Its real door is world (47,26), left of
the plaque, not under the apparent canopy center. A 16×32 ticket terminal has a
solid base and clear approach. A broadcast sign and fountain-side bench respect
actual clearances. Low 32×32 flower beds at (144,568), (336,568) replace specific
rail segments, align their caps with posts and preserve fountain/lamp space.
The earlier wider/lower form intruded into water and duplicated the fence.
South retaining beds replace the full old fence and legs with full masonry walls;
clean border donors prevent fragments repeating beyond the map.

Only four proven-unused entries in foliage bank 10 were extended. Tree indices
1–11 were unchanged. All twelve private copies remain coherent. Native glyph
reuse kept existing section dimensions and IDs, avoiding save migration.
Six read-only sign interactions describe stalls, wheel, broadcast and terminal.
There are no hidden inventory changes, ride systems, shops or campaign flags.

## 9. Validate appearance, playability, preservation and reproducibility

Use independent checks, each with a clear claim:

1. Decode committed native tiles/palettes/attributes and compare the full image
   against the intended layered art. Export through actual Porymap too; all three
   must agree. Inspect full-scale and enlarged details, not only difference counts.
2. Check every building context, mixed-material square, terrain edge, border,
   roof/facade join, tree root and canopy. Use before/after and reference sheets.
3. Walk actual emulator routes in both directions across section boundaries,
   under foreground structures, up to doors, along water and against barriers.
   Test changes at the normal camera position. Inspect player occlusion and UI.
4. Save ordinarily, cold reload and Continue. Retain a prior proof save and load it
   against the new build. Exercise the new city, an earlier city and re-entry to
   detect renderer/cache lifecycle regressions. Keep stable map IDs.
5. Prove preserved pixels and protected masters remain exact outside authorized
   regions. Record file hashes and source/ROM identity. Derive runtime atlas only
   from native source; enforce a build-time stale-atlas guard.
6. Reproduce narrow patches from immutable baseline checkpoints and verify a clean
   checkout. Never replay first-authoring generators over committed maps.

Final Goldenrod verification: all 4,704 cells match actual Porymap; 91 background
captures / 3,494,400 pixels have zero errors. Six dialogue views are separately
reviewed, not falsely included in unobscured-background parity. Five walking GIFs
show seams, railway, arch, boardwalk arrival and market. All 49 tree contexts,
canonical Center and tower equipment remain protected. Local build and ordinary
save/cold-reload/prior-save checks pass. Final ROM SHA-256:
`3c7e08e044312dce6af766fc44a58bd00216b806b3c50fbfe240fe2ecb4e5324`.
Hosted Actions were disabled by GitHub; local verification is recorded, and this
must not be represented as a successful hosted CI run.

## Reusable sequence for the next city

1. Read AGENTS, handoff, reconstruction rules and this case study. Identify the
   accepted engine/hub baseline and protect pending work in dedicated branches.
2. Retain the actual original map, register its grid and inventory every landmark,
   terrain family, approach and occluded region. Record uncertainty honestly.
3. Inspect shared masters and native hardware budget. Choose map sections and
   coherent palette families; reserve complete structural art first.
4. Author material, ground, transparent foreground and traversal independently.
   Reuse approved buildings and full native trees; fit their actual neighbors.
5. Build real native source and inspect actual decoded/Porymap renders. Review
   each building individually with context, then all terrain joins and corners.
6. Polish local noise and texture planes, repeat compatible clean modules, and
   inspect palette conversion. Repair donors and background independently.
7. Build and walk the map at player scale; verify borders, layers, entrances,
   section transitions, prior cities and ordinary save persistence.
8. Present the actual city inline with readable evidence and concrete limitations.
   Owner visual acceptance is distinct from automated success.
9. For later creative changes, show a reproducible map concept, incorporate owner
   choices, then make narrow native edits with protected-region proofs. Recheck
   the neighborhood around every asset, not only the asset itself.

Use `tools/gba/maps/goldenrod_city/` as worked examples, not a universal generator.
`author.py` and `register.py` are first-authoring only. Local revision helpers
refuse unexpected baselines. `stream.py` derives the adapter from native files;
`review.py`, `runtime.py`, `verify_frames.py`, `film.py` and the Porymap exporter
provide distinct evidence. The next city needs its own reference registration,
geography, budgets, borders and review ledger. Preserve those distinctions.
