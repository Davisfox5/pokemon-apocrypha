# Cherrygrove artwork-to-native study — September 30

Converted the reviewed five-town revision-3 Cherrygrove artwork into an isolated playable GBA map. Source: `tools/vendor/gba/cherrygrove-art-study-work`. Separate ROM/save package: `tools/vendor/gba/Cherrygrove-art-study-20260930.zip`. Continue starts in the town at (40,21). The matching save is fresh test data; existing owner saves were not used or replaced. No active Porymap project, main game source, campaign build or desktop emulator changed.

## Artwork and conversion

The 1619x972 reference is preserved as `reference.png`. Its town composition is adapted into an 800x480 native artwork area, with eight columns and six rows of camera scenery around it (66x42 map). Buildings and boats were extracted directly from the reference, resized and reduced to GBA colors. The five houses reuse one facade to preserve consistent door/roof artwork. A separately generated complete tree avoids clipped source crowns; `tree-source.png` and `tree-prompt.txt` preserve it. Grass and water use repeated patches, the western shoreline is traced from the image, and dock, pond, garden, bench and Mart sign retain their positions. Existing Emerald interiors and cast are retained.

Final conversion: 990 static 8x8 tile patterns of 1008 allocated, 342 metatiles, palette banks 0-12 with 15 opaque colors each. Sixteen hardware tile slots are reserved for animated doors. Eleven complex palette junctions were reduced to two banks. Native encoding/decoding matches the quantized assembled scene pixel-for-pixel; this does not mean the concept image is pixel-identical. Terrain texture, color range, shoreline granularity, tree spacing and small prop details differ at native resolution. Water is static in this study. Collision blocks buildings, crowns, boats, reef and pond; open ground, pier and island are walkable. Existing route approaches connect through native directional warps, while retaining their art and onward Sandgem/Floccesy links.

## Verified evidence

Compilation passed. Static checks cover all 2772 cells and 364 reachable walking cells: seven door approaches, island, both exits, all NPC route cells, covered scenery layers and camera margins. Headless mGBA passes all seven building entry/return pairs, both route round trips, island access/water blocking, 224 representative movement probes, ordinary Save, cold reload and title-screen Continue. The movement probes test whether each representative neighbor permits or blocks movement; they do not require an exact one-cell displacement after a held input. Twelve NPCs each occupied both ends of their walking route over 720 observations. Full dialogue, every interior service and surfing have not been requalified in this study. No desktop emulator was opened.

`evidence/in-game-review.png` contains six actual engine captures at integer scale; `walking.gif` records native NPC movement. `town-overview.png` and `artwork-area.png` decode the native tiles. `reference-comparison.png` pairs the reviewed image with that decoded map. Build identity and runtime/static records are in evidence.

## Source and preservation

Compiler: `tools/gba/maps/build_cherrygrove_art_study.py`; connections: `connect_cherrygrove_art_study.py`; doors: `cherrygrove_art_study_doors.py`; engine proof: `cherrygrove_art_study_runtime.c` and its generated probe header. Compiler writes only the isolated study. Do not rerun these over later owner edits without a fresh snapshot.

`source-overlay/` preserves all sixty changed engine source assets. `gba/cherrygrove-art-study.patch` is incremental against the local johto-restart-game preview at conversion time, not pristine upstream. Forward and reverse patch checks pass in an isolated baseline. `evidence/source-base.json` records exact original hashes for touched files; `preservation.json` lists modifications. All non-target maps remain identical; the two route approaches have only their native return wiring/cells adapted. Reference architectural designs belong to Nintendo, Game Freak and Creatures; generated tree and converted assets were authored for this project.
