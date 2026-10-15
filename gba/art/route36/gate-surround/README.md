# Route 36 gate tree surrounds

Approved G01a/G02 artwork from Johto gate review refinement-4, now integrated into Route 36 with separate tree layers. The building source PNGs are unchanged. Seven whole rear trees use the existing Cherrygrove/Route 36 tree asset and align with neighboring tree footprints. Northern trees draw behind the buildings; the six existing southern crowns draw over their bases. No cropped-tree substitutes or foliage painted into the building files.

## Reusable materials

`source/west-tree-background.png` and `east-tree-background.png` preserve independent RGBA background plates. `west-tree-foreground.png` and `east-tree-foreground.png` preserve the lower crowns. Their source sprite is `../source/materials/tree.png`; placement coordinates and validation are in `evidence/structure.json`. Use these layers with the building at its authored grid origin. Collision is authored separately; plates do not imply walkability.

## Native integration

Only the Route 36 layout and its paired tilesets change. All pixels outside the gate/tree areas are identical to engine baseline `162c41c8b5987973480f7a276e63a196dfc1bf07`. All other maps, events, scripts and warps remain unchanged. Native slots: 528 / 1,008; metatiles: 322; used palettes: 9 / 13. Porytiles compiles exact foreground/background pixels; original RGB888 palette spellings are retained where they encode the same RGB555 values.

The rear alleys, foundation strip and southern crown rows are blocked. The active Violet threshold stays at (75,20); National Park remains a closed frontage pending its interior. The remaining route passage widths and Alph barriers are preserved. The original route generator now refuses to overwrite these later layers.

## Checks and views

- `evidence/gate-close-ups.png`: decoded native map, with foreground/background trees.
- `evidence/native-overview.png`: complete native Route 36.
- `evidence/gameplay-close-ups.png`: actual ROM captures from the background emulator.
- `evidence/structure.json`: exact native/Porymap pixels, 412 nonoverlapping tree footprints, 689 reachable cells, 308-step tour, 15 approaches, four added gate collision probes, warp round trip and ordinary save/reload/Continue.
- `evidence/runtime.json`: complete emulator observations, linked to the built ROM hash.

No desktop emulator was opened. Onward destinations, NPCs and encounters retain their prior unfinished status.

## Reproduction

Use the existing porygon Python environment:

```sh
python tools/gba/maps/route36/gate_surround/build.py /path/to/engine --install
python tools/gba/maps/route36/gate_surround/check.py /path/to/engine
# Build generated files, then the ROM with the pinned ARM toolchain.
python tools/gba/maps/route36/gate_surround/runtime.py /path/to/engine /tmp/new-runtime-dir --toolchain /path/to/arm-toolchain
```

The original gate review previews remain preserved. This integration makes no changes to other regional maps. Game-derived gate/tree source credits remain Game Freak, Nintendo and The Pokémon Company, with extraction provenance in the Johto review and Route 36 packages.
