# Violet City — university campus and redesigned lecture hall

The owner approved the softened exterior and requested expanded housing, replacement of the two purple-roofed buildings with a university, and a teaching court. This campus revision is ready for visual review; Chapter 2 interiors and scenes remain incomplete. It builds on the accepted Route 30 engine source `aa8ea35e`. Native source lives in the expansion fork on `codex/violet-city`; the source commit is recorded in `evidence/preservation.json`.

## What is implemented

- A new 80 × 72 map, `VioletCity`, appended to the existing Cherrygrove map group without renumbering prior maps.
- HGSS-inspired core geography: northern Sprout Tower, lake with two bridge spans and a central stone landing, old gym, university, central streets, Center/Mart and homes.
- The eastern campus extension is a design proposal based on `DESIGN.md` Chapter 2: university, library and practice court. The old gym is labeled as the lecture hall/battle practicum. No new character roles or story events were invented.
- Accepted Cherrygrove green trees, houses, Center and Mart with subtle Violet-only silhouette finishing; the Route 30 freshwater family with a Violet-specific bank; original Emerald boundary rock. New city-specific tile pools leave the accepted shared tilesets unchanged.
- Six readable signs authored with Poryscript 3.6.1. The existing east gate leads into the city and returns to Route 31 through its unchanged eastern exit.
- A closed-door exterior for the other buildings. Approaches exist and collision is placed against the buildings; the interiors are not implemented yet.

The former `VioletCityEntrance` stub is preserved as reference. Only the two western destination fields of `VioletEastGate` change. Its room, eastern Route 31 exits, and all existing map/warp IDs are retained.

## Roof-only refinement — current

The square paving-like grid is replaced with short, staggered copper roof tiles, shaded lower lips and diagonal hip caps. Exactly 3,160 roof pixels change; every pixel outside the roof and the complete alpha silhouette remain unchanged. Windows, walls, canopy, trim, doors and map placement are preserved. Collision, elevation, behavior, layers, scripts, events and warps are unchanged.

Engine source: `a17d6182e8dbea23836c038d2af6b26aab6475df`. Native Porymap output matches the decoded map exactly. The local ROM build and background 488-step tour, hall probes, signs, ordinary save/cold reload/Continue pass. Current scenery capacity is **961 / 1,008 tiles**. No desktop emulator opened.

[Roof before/after](evidence/roof-comparison.png) · [Roof-only validation](evidence/roof-validation.json)

## Lecture hall architectural redesign

The owner clarified that the **building should be redesigned**, with the original gym's colors and accent elements retained. The prior trim-only renovation below is superseded.

The current hall is an original 144x112-pixel, 9x7-cell auditorium: rectangular lecture wings, a broad angular copper roof and a raised glazed clerestory. Warm copper-brown roof shades, orange structural ribs, cyan facade bands and a curved blue entrance canopy carry forward the original gym's identity. The palette uses its original RGB555 color family. The university book crest and former-gym sign retain the educational role.

The doorway stays at (31,41), with its approach at (31,42). The larger structure occupies (27,35) through (35,41); the sign moves one cell west to (26,42), clear of the new facade. Collision is updated for the wider building. All visual and collision changes are confined to the hall/sign area; existing warps, actors and surrounding map artwork are preserved. Porytiles now also compiles the new hall, with zero decoded pixel errors; Porymap matches the native decoder.

[Original color reference beside the new hall](evidence/hall-redesign-comparison.png) · [Revision checks](evidence/hall-redesign-validation.json)

Interiors and the lecture/practicum interactions remain unimplemented.

## Superseded trim-only gym renovation

Owner approved a restrained university renovation that pays homage to the original gym. `campus.renovate_gym` keeps the exact silhouette, curved roof, central roof ridge, projecting entrance hood and original warm roof shades. Cyan bands become campus slate blue, gray walls and entrance supports become cream stone, and a small open-book crest replaces the old canopy emblem. The existing sign now also reads **Former VIOLET GYM**. Its lecture hall and Roxanne battle-practicum roles are unchanged.

Native comparison confirms all 3,515 warm-colored upper-roof pixels and the alpha silhouette are unchanged. Exactly 3,153 displayed map pixels change, all inside this building's footprint. Collision, elevation, tile behavior, layer attributes, events and warps are unchanged. Porymap matches the independent native decoder exactly. Current scenery capacity is **995 / 1,008 tiles**.

[Before/after gym detail](evidence/gym-comparison.png) · [Native checks](evidence/gym-validation.json) · [In-game lecture hall](evidence/gameplay/lecture-hall.png)

## October 13 university and housing revision

- Removed the two repeated purple-roofed school buildings. One original native university facade now has two classroom wings, a central clock tower, a broad entrance and a shared library/classroom sign. The library is planned inside this building, not deleted from the story.
- Cleared three bounded forest pockets for three additional accepted Johto houses: northwest, southwest garden and southeast garden. There are now five residences. Paths connect all new approaches to the town spine.
- Kept Falkner's old gym as the lecture hall and Roxanne's battle practicum, exactly as specified in DESIGN.md Chapter 2 scenes 2 and 4. Practice courts are also explicitly in the story.
- Rebuilt the outlined court east of the Center as a teaching space: red/blue court halves, Pokeball center, marked trainer positions, four spectator benches and an instructional sign. Scarlet/Violet's schoolyard informs the visual direction; these are original native pixel modules, not extracted screenshot pixels. Reference links and source dimensions are in `source/campus-design.json`.
- Kept the lake landing, complete lake water footprint, bridge cells and east gate warp unchanged. Collision now follows the new houses, university and bench footprints. All ten building approaches are reachable; no new open map edges exist.
- Porytiles compiles/decodes the tower and new university without pixel errors. Porymap render matches the independent decoder exactly. Native 488-step tour, house/university closed-door checks, court traversal/benches, six signs and ordinary save/cold load/Continue pass.

The buildings and court are **exteriors only**. University/library interiors, teaching interactions, Roxanne's challenge, student battles and Chapter 2 actors still need implementation. This pass introduces no teams, rewards or story flags.

[Campus verification](evidence/campus-validation.json) · [Current native playthrough gallery](evidence/gameplay-gallery.png)

## Previous October 13 edge refinement

- Replaced the lake's thin rectangular outline with repeating grass/bank/shallow-water courses and rounded 12-pixel corners. Water texture and palette remain native; no image scaling or blur is used.
- Rounded the stone landing corners over actual water backing, with a softer stone bevel. No grass is exposed inside the lake.
- Eased high-contrast outer building outlines into their existing palettes and clipped single-pixel convex corners. Facade detail, doorway anchors and ground contact shadows are retained.
- Lightly rounded street corners; the stone street remains clearly legible against grass.
- Replaced all six Violet blossom trees with the complete accepted green tree. **Pink/blossom trees are exclusive to Cherrygrove City**; this project-wide direction is now in AGENTS.md. This revision changes Violet artwork only, not historical route proposals or shared donor assets.
- All 5,760 cells retain their collision, elevation, behavior and foreground-layer attributes. Events, warps and connections are byte-identical to the preceding Violet revision. Porymap/native render equality and the headless tour/save checks pass again.

[Before/after detail comparison](evidence/edge-comparison.png) · [Revision checks](evidence/edge-refinement.json)

## Visuals

- [Porymap native overview](evidence/porymap-overview.png)
- [Actual headless gameplay gallery](evidence/gameplay-gallery.png)
- [Individual native captures](evidence/gameplay/)

The preview uses the engine's existing lighting. No desktop emulator was opened. This task did not replace the owner's currently open Route 30 Porymap project.

## Tools used and evidence

- **Porytiles 2.0.0 legacy compiler:** compiled 345 landmark metatiles; decoded output was compared with the RGB555-normalized source and imported with zero RGB/alpha errors. Editable layer sheets and native compiled files are in `source/porytiles-*`.
- **Poryscript 3.6.1:** signs compiled to committed `.inc`, with both source and generated script preserved.
- **porygon 0.1.1:** checked binary Blockdata encode/decode and MCP read/validation. `evidence/porygon.json` reports no script errors. Its single unused-label warning is for the map-script header, which the engine references through map metadata.
- **Porymap 6.3.1:** original loader and renderer executed offscreen; exported 1280 × 1152 pixels exactly match the independent native decoder. This is renderer evidence, not a desktop editor save round-trip. The test host's bundled giflib required a C++ `bool` compatibility correction for the current macOS SDK, confined to the temporary probe build.
- **Prior cloud build:** [lecture-hall redesign](https://github.com/Davisfox5/pokeemerald-expansion/actions/runs/38446877103) targets `b652df9490` and was in_progress when recorded. Current local native build, Porymap and background runtime checks pass; cloud snapshot is in `evidence/ci.json`.
- **ROM build:** host tools, serial generated data, then Arm GNU 14.2 parallel build passed. Existing linker warnings remain. ROM hash is recorded in `evidence/build.json`; no ROM is committed.
- **Headless libmGBA 0.10.5:** 488 ordinary walking steps visit all ten landmark approaches; gate travel in both directions, bridge/island collision, closed doors and all six signs pass. A 128 KiB ordinary save passes cold reload and title-screen Continue. Fixtures only place the player for isolated probes; the tour itself uses directional inputs.
- **Preservation:** Route 30, Route 31, Cherrygrove, New Bark, and their protected graphics/layout files remain byte-identical to the base. No open walkable map edges lead into unbuilt areas.

## Reference and art provenance

Core geography and landmark silhouettes were surveyed from [Violet City HGSS on Bulbagarden Archives](https://archives.bulbagarden.net/wiki/File:Violet_City_HGSS.png). The page credits **Gabo 2oo / Gabo 200**, using tiles by **Newtiteuf and rene_lucario**, emulator captures and other material. It is a community composite substantially derived from the game, **not decoded original HGSS collision or object data**. It is retained as a reference with this attribution, not represented as agent-authored art. Underlying Pokémon art belongs to its respective rights holders; no new reuse license is claimed.

Tower/school masks are explicit traced polygons. Colors are adapted to GBA RGB555 banks; repeating interior roof courses fit native tile constraints while preserving the outer profiles. The earlier school masks remain reference material; the current university and court are original modular native art in `tools/gba/maps/violet_city/campus.py`. Trees and service buildings retain the accepted Cherrygrove asset provenance in `gba/art/cherrygrove-synthesis/`. Freshwater comes from `gba/art/route30-hgss-blocks/`. These changes are native adaptations, not a pixel-exact recreation of the DS town.

The exterior uses **961 of 1,008 scenery tile slots**, with 47 remaining; future exterior detail must reuse or simplify modules. Interior maps have separate tile banks.

## Next work

1. Owner review of the university, additional homes and teaching court.
2. Build actual Sprout Tower, lecture/practicum, library, service and residential interiors with reciprocal doors.
3. Implement the existing Chapter 2 scene specifications, actors and lessons; trainer teams and rewards remain separate approved design work.
4. Connect Routes 32/36 when those areas exist. Current boundaries deliberately stay closed.

Water is currently static, and the court has no battles or actors. No trainers, encounters, new flags, rewards, badges or persistent-state mechanics were added. The Center and Mart have no new service interiors in this proposal. Do not infer those features from their exterior art.

## Reproduction and editing

Use Porymap to edit the committed native map. The generator is provenance for this new-map proposal; it checks `source/generated-files.json` and refuses to overwrite any subsequent owner edits. Do not bypass that check. Its common layer helper now accepts an optional composite palette bank; the Route 30 default stays 7, while Violet uses otherwise unused bank 1 to preserve landmark colors.

With an isolated expansion checkout at the stated base, installed tool versions above, and numpy/Pillow/porygon available:

```sh
make -C /path/to/expansion tools
python tools/gba/maps/violet_city/build.py /path/to/expansion
python tools/gba/maps/violet_city/check.py /path/to/expansion
python tools/gba/maps/violet_city/porygon_check.py /path/to/expansion
make -C /path/to/expansion -j1 generated
make -C /path/to/expansion -j8
python tools/gba/maps/violet_city/runtime.py /path/to/expansion /fresh/output --toolchain /path/to/arm-toolchain
```

On macOS, pass `MGBA_FLAGS='-I/opt/homebrew/opt/mgba/include -L/opt/homebrew/opt/mgba/lib -lmgba'` to the runtime check. Source assets and evidence are committed here; engine maps, scripts and tilesets are committed directly in the expansion fork.
