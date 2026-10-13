# Violet City — native exterior and edge refinement

The owner broadly accepted the exterior direction on October 13 and requested softer edges and removal of pink trees. This revision is ready for visual review; Chapter 2 interiors and scenes remain incomplete. It builds on the accepted Route 30 engine source `aa8ea35e`. Native source lives in the expansion fork on `codex/violet-city`; the source commit is recorded in `evidence/preservation.json`.

## What is implemented

- A new 80 × 72 map, `VioletCity`, appended to the existing Cherrygrove map group without renumbering prior maps.
- HGSS-inspired core geography: northern Sprout Tower, lake with two bridge spans and a central stone landing, old gym, academy, central streets, Center/Mart and homes.
- The eastern campus extension is a design proposal based on `DESIGN.md` Chapter 2: university, library and practice court. The old gym is labeled as the lecture hall/battle practicum. No new character roles or story events were invented.
- Accepted Cherrygrove green trees, houses, Center and Mart with subtle Violet-only silhouette finishing; the Route 30 freshwater family with a Violet-specific bank; original Emerald boundary rock. New city-specific tile pools leave the accepted shared tilesets unchanged.
- Five readable signs authored with Poryscript 3.6.1. The existing east gate leads into the city and returns to Route 31 through its unchanged eastern exit.
- A closed-door exterior for the other buildings. Approaches exist and collision is placed against the buildings; the interiors are not implemented yet.

The former `VioletCityEntrance` stub is preserved as reference. Only the two western destination fields of `VioletEastGate` change. Its room, eastern Route 31 exits, and all existing map/warp IDs are retained.

## October 13 edge refinement

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

- **Porytiles 2.0.0 legacy compiler:** compiled 147 landmark metatiles; decoded output was compared with the RGB555-normalized source and imported with zero RGB/alpha errors. Editable layer sheets and native compiled files are in `source/porytiles-*`.
- **Poryscript 3.6.1:** signs compiled to committed `.inc`, with both source and generated script preserved.
- **porygon 0.1.1:** checked binary Blockdata encode/decode and MCP read/validation. `evidence/porygon.json` reports no script errors. Its single unused-label warning is for the map-script header, which the engine references through map metadata.
- **Porymap 6.3.1:** original loader and renderer executed offscreen; exported 1280 × 1152 pixels exactly match the independent native decoder. This is renderer evidence, not a desktop editor save round-trip. The test host's bundled giflib required a C++ `bool` compatibility correction for the current macOS SDK, confined to the temporary probe build.
- **Cloud build:** the preceding exterior passed the production job on `cb814b0ac9`. The [edge-refinement run](https://github.com/Davisfox5/pokeemerald-expansion/actions/runs/38420889025) targets `4d086afa28` and was in_progress when this evidence was saved; its latest captured status is in `evidence/ci.json`. The current revision already passes the local native build and runtime checks below.
- **ROM build:** host tools, serial generated data, then Arm GNU 14.2 parallel build passed. Existing linker warnings remain. ROM hash is recorded in `evidence/build.json`; no ROM is committed.
- **Headless libmGBA 0.10.5:** 355 ordinary walking steps visit all eight landmark approaches; gate travel in both directions, bridge/island collision, closed doors and all five signs pass. A 128 KiB ordinary save passes cold reload and title-screen Continue. Fixtures only place the player for isolated probes; the tour itself uses directional inputs.
- **Preservation:** Route 30, Route 31, Cherrygrove, New Bark, and their protected graphics/layout files remain byte-identical to the base. No open walkable map edges lead into unbuilt areas.

## Reference and art provenance

Core geography and landmark silhouettes were surveyed from [Violet City HGSS on Bulbagarden Archives](https://archives.bulbagarden.net/wiki/File:Violet_City_HGSS.png). The page credits **Gabo 2oo / Gabo 200**, using tiles by **Newtiteuf and rene_lucario**, emulator captures and other material. It is a community composite substantially derived from the game, **not decoded original HGSS collision or object data**. It is retained as a reference with this attribution, not represented as agent-authored art. Underlying Pokémon art belongs to its respective rights holders; no new reuse license is claimed.

Tower/school masks are explicit traced polygons. Colors are adapted to GBA RGB555 banks; repeating interior roof courses fit native tile constraints while preserving the outer profiles. School architecture supplies the proposed library wing. Trees and service buildings retain the accepted Cherrygrove asset provenance in `gba/art/cherrygrove-synthesis/`. Freshwater comes from `gba/art/route30-hgss-blocks/`. These changes are native adaptations, not a pixel-exact recreation of the DS town.

The exterior uses **1,001 of 1,008 scenery tile slots**, with 7 remaining; future exterior detail must reuse or simplify modules. Interior maps have separate tile banks.

## Next work

1. Refine the campus architecture and bridge/platform detailing after reviewing this exterior proposal.
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
