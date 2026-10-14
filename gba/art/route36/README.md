# Route 36 — native western connection from Violet

Revised exterior after owner rejection of the sparse first draft; awaiting visual review. Reconstructs the [HGSS Route 36 overview](https://bulbapedia.bulbagarden.net/wiki/File:Johto_Route_36_HGSS.png) using the existing Johto art family. It is an 82×32 native map with a working Violet west-gate room and round-trip travel. The approved Violet buildings, including the locked Mart, remain pixel-identical.

## Layout and artwork — refined October 14

The old broad rectangle stencil has been replaced by a per-cell HGSS survey. All **2,624 native cells** have a record in [block-ledger.json](source/block-ledger.json), with their source pixel box, sampled terrain, authored interpretation, native block ID, collision and tree footprint. [Survey blocks](evidence/survey-blocks.png), [readable terrain rows](source/survey-blocks.txt), and [relative heights](source/elevation-survey.json) are separate from artwork.

- **398 whole trees**, versus 343 in the rejected draft. Forest bands, the northwestern island, central divider and southern boundary follow the source more closely. Tree footprints do not overlap; complete crowns can naturally overlap their northern neighbor. Existing Cherrygrove tree pixels are retained. Interior forest shadow uses the existing tree-shadow color, with no cropped crown fillers.
- **702 reachable cells**, versus 888. The central neck is one movement cell, the Route 35 grass lane is two, the plateau's southern dirt strip is two, and the eastern dirt approach is three. These widths are collision assertions. The path continues beneath the southern canopy row rather than becoming grass there.
- Route 35 moves west into its HGSS grass corridor. The upper western tree column moves inward to narrow the passage. The original signs, flowering eastern verge and Apricorn silhouette remain.
- Both side gatehouses now use **Route 29's detailed HGSS gate components**, replacing the flat Violet prototype. Roof ribs, hip faces, eaves, window frieze and turquoise trim come from that source. The side entrance and paired lower bays are native adaptations; the south gate retains the original front-facing entrance. East/west gate stairs now have vertical riser lines.
- Cliff faces use native Emerald general **0x73 / 0x75 / 0x7c / 0x7b** with the HGSS earth palette. They face away from the high terrace. Cliffs continue into the southern forest and render behind the tree crowns instead of ending against a bare gap.
- **West flight climbs east; east flight descends east.** The former identical rotated tread strips are replaced by a cleaned HGSS 16×48 side-flight silhouette and its opposite, with neutral stone treads. These are adapted HGSS side stairs, not claimed to be an original Emerald horizontal stair placement. Adjacent wall tiles block crossing.

The source is 1295×470 pixels; the native map remains 82×32 (1312×512). Geometry is inferred from the raster, not recovered DS collision data. Whole crowns, full gatehouses replacing edge-clipped buildings, integer-cell boundaries and the final padding rows are explicit native adaptations. The west/east gates keep their working doorway coordinates. The renderer does not rescale the gate components or tree sprites.

Relative height is represented by directional artwork and solid cliff boundaries, using the existing ordinary outdoor movement level. No new movement mechanic, story barrier, Sudowoodo event or actor role is introduced.

## Playable scope

The west threshold at Violet (5,30) now uses a directional warp into `VioletWestGate`, which reuses the existing 15×6 gate-room layout. Its other exit reaches Route 36 (75,20). Walking farther into the east/west arrow threshold triggers the transition. Return directions are verified in the emulator.

Only that one Violet cell changes collision/behavior, and one warp is appended; its old east warp keeps index zero. City art, all other collision cells, scripts, existing map IDs, and prior maps remain unchanged. New map IDs are appended: Route 36 = 44, west gate = 45 in group 80. The route's region-map section is appended through the authoritative JSON source, not by editing generated headers.

National Park, Routes 35/37 and Alph are approach frontages only; their destination maps and gate interiors are not connected. Route 36 has no trainers, encounter table, item rewards, Sudowoodo encounter or story scripts yet. These are separate production scopes. The earlier Chapter 2 canon continues south via Route 32; this map does not alter that story progression.

## Evidence

- [Before / revised route](evidence/revision-comparison.png)
- [Full native route](evidence/native-overview.png)
- [Original HGSS / native comparison](evidence/source-comparison.png)
- [Background gameplay captures](evidence/gameplay-gallery.png)
- [Gate interior](evidence/gate-interior.png)
- [Reachability and preservation checks](evidence/structure.json)
- [Porymap comparison](evidence/porymap.json), [porygon](evidence/porygon.json), [Porytiles grass round trip](evidence/porytiles.json)
- [Background playthrough and ordinary save/reload/Continue](evidence/runtime.json)

The 258-step route tour uses ordinary movement after entering through the gate. Additional probes cover both stairs, walls, tall grass, signs, pending edges and the complete return trip. Porymap's own offscreen render equals the independent native render, including the unchanged Violet exterior. The preceding build passed the 661-step Violet regression; this refinement changes only Route 36 tiles/layout, preserves all Violet art/physics/events byte-for-byte against that build, and repeats the real west-gate round trip. Camera-edge captures also verify the continuous forest border at the two unfinished exits. No desktop emulator or visible Porymap window was opened.

## Editing and reproduction

Engine source is on `codex/violet-city` in `Davisfox5/pokeemerald-expansion`; exact revision is recorded in `evidence/preservation.json`. Parent source revision begins at `6e50c9ad`; engine baseline is `ac6e1ee42257ba3551452a9f193b8d9c3a3fd1e3`.

```sh
python tools/gba/maps/route36/trace.py
python tools/gba/maps/route36/build.py /path/to/engine
python tools/gba/maps/route36/check.py /path/to/engine
python tools/gba/maps/route36/porytiles_check.py /path/to/engine
python tools/gba/maps/route36/porygon_check.py /path/to/engine
python tools/gba/maps/route36/runtime.py /path/to/engine /tmp/route36-runtime --toolchain /path/to/arm-toolchain
```

Use the porygon virtual environment for the Python commands. Build the ROM with the project's pinned ARM toolchain before running the emulator checks. `source/generated-files.json` guards against overwriting subsequent edits. The earlier Violet generator intentionally rejects the new west-gate changes; do not bypass its guard or regenerate the city over this connection.

The source overview is a game-derived reference credited to Game Freak/Nintendo/The Pokémon Company, retrieved from Bulbagarden Archives. Reused Johto art retains its provenance in the Cherrygrove synthesis and Route 30 packages. Gate component provenance is `claude_routes/art.py::gate()` and `gba/art/claude-routes/references/route29-hgss.png`; the side-facing adaptation is in `architecture.py`. Rock/stair provenance and native conversions are in `terrain.py`. No ROM, save, tool binary or donor source tree is committed.

## Visual review and limits

Native Porymap output and the independent decoder match pixel for pixel. Background gameplay captures are from the built ROM, including both stair crossings and the real gate; they retain the engine's ordinary time-of-day palette. The map overview shows base tileset colors. No desktop emulator is opened. This is the revised exterior for owner review, not an assertion of visual approval. The four onward destinations, encounters and story content remain outside this revision.
