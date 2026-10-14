# Route 36 — native western connection from Violet

First exterior draft, ready for owner visual review. Reconstructs the [HGSS Route 36 overview](https://bulbapedia.bulbagarden.net/wiki/File:Johto_Route_36_HGSS.png) using the existing Johto art family. It is an 82×32 native map with a working Violet west-gate room and round-trip travel. The approved Violet buildings, including the locked Mart, remain pixel-identical.

## Layout and artwork

- Broad flower-lined eastern approach from Violet; southern gate frontage toward Alph.
- Central wooded passage and diagonal northern branch toward Route 37.
- Western raised grass terrace, continuous cliff sides and two east/west stair crossings.
- Western gate frontage toward National Park and southern lane toward Route 35.
- Complete accepted Cherrygrove green tree sprites, original ground texture library, Route 30's detailed HGSS-derived grass edge family and existing Emerald-derived rock/treads.
- Violet's teal gate modules are reused, with a central-passage variant for the southern gate. No residential house is substituted for it.
- Four readable route signs authored with Poryscript. The Apricorn silhouette is scenery only; harvesting is not implemented.

The reference is 1295×470 pixels. The native draft expands to 1312×512 to fit whole 16px blocks, complete tree sprites and bounded approaches. Geometry is surveyed from the raster reference, not recovered DS collision data. Canopy footprints and small forest adjustments are explicitly native adaptations. The original Sudowoodo character/event is not instantiated: the current story contains no Route 36 event specification. No new narrative gate or actor role is invented.

Stair artwork comes from the existing route-family Emerald general metatiles (0xAF/0xCF), quarter-turned for east/west movement. These are adapted existing treads, not claimed to be a recovered original Emerald east/west placement. They do not apply elevation changes or a special diagonal movement behavior. Both traversal directions and adjacent wall blocking are checked.

## Playable scope

The west threshold at Violet (5,30) now uses a directional warp into `VioletWestGate`, which reuses the existing 15×6 gate-room layout. Its other exit reaches Route 36 (75,20). Walking farther into the east/west arrow threshold triggers the transition. Return directions are verified in the emulator.

Only that one Violet cell changes collision/behavior, and one warp is appended; its old east warp keeps index zero. City art, all other collision cells, scripts, existing map IDs, and prior maps remain unchanged. New map IDs are appended: Route 36 = 44, west gate = 45 in group 80. The route's region-map section is appended through the authoritative JSON source, not by editing generated headers.

National Park, Routes 35/37 and Alph are approach frontages only; their destination maps and gate interiors are not connected. Route 36 has no trainers, encounter table, item rewards, Sudowoodo encounter or story scripts yet. These are separate production scopes. The earlier Chapter 2 canon continues south via Route 32; this map does not alter that story progression.

## Evidence

- [Full native route](evidence/native-overview.png)
- [Original HGSS / native comparison](evidence/source-comparison.png)
- [Background gameplay captures](evidence/gameplay-gallery.png)
- [Gate interior](evidence/gate-interior.png)
- [Reachability and preservation checks](evidence/structure.json)
- [Porymap comparison](evidence/porymap.json), [porygon](evidence/porygon.json), [Porytiles grass round trip](evidence/porytiles.json)
- [Background playthrough and ordinary save/reload/Continue](evidence/runtime.json)

The 254-step route tour uses ordinary movement after entering through the gate. Additional probes cover both stairs, walls, tall grass, signs, pending edges and the complete return trip. Porymap's own offscreen render equals the independent native render, including the unchanged Violet exterior. The updated Violet regression harness also passes its 661-step city tour and ordinary save/reload/Continue with the new west gate. No desktop emulator or visible Porymap window was opened.

## Editing and reproduction

Engine source is on `codex/violet-city` in `Davisfox5/pokeemerald-expansion`; exact revision is recorded in `evidence/preservation.json`. Parent source revision begins at `6e50c9ad`; engine baseline is `ac6e1ee42257ba3551452a9f193b8d9c3a3fd1e3`.

```sh
python tools/gba/maps/route36/build.py /path/to/engine
python tools/gba/maps/route36/check.py /path/to/engine
python tools/gba/maps/route36/porytiles_check.py /path/to/engine
python tools/gba/maps/route36/porygon_check.py /path/to/engine
python tools/gba/maps/route36/runtime.py /path/to/engine /tmp/route36-runtime --toolchain /path/to/arm-toolchain
```

Use the porygon virtual environment for the Python commands. Build the ROM with the project's pinned ARM toolchain before running the emulator checks. `source/generated-files.json` guards against overwriting subsequent edits. The earlier Violet generator intentionally rejects the new west-gate changes; do not bypass its guard or regenerate the city over this connection.

The source overview is a game-derived reference credited to Game Freak/Nintendo/The Pokémon Company, retrieved from Bulbagarden Archives. Reused Johto art retains its provenance in the Cherrygrove synthesis and Route 30 packages. Local original gate adaptations are in the generator. No ROM, save, tool binary or donor source tree is committed.
