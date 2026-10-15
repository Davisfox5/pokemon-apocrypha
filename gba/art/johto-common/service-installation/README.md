# Approved Johto service-building installation

Owner approved C06 as the shared Johto Center and reuse of the locked M01 Mart
in Cherrygrove on October 15, 2026. The standing regional reuse/transparency rule
is in `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, and `../approved-buildings.json`.

## Installed result

- Cherrygrove: exact C06 master at (59,5), existing door (61,9); exact M01 master
  at (49,4), existing door (51,9). Existing interiors, events and return warps stay.
- Violet: exact C06 master at (47,51), closed entrance (49,55). Approved M01 is
  pixel-identical at its existing placement. Its interior remains closed.
- All pixels outside these building/entrance areas are unchanged. Other Johto maps
  and their original shared tilesets are preserved.

[Cherrygrove close-up](evidence/cherrygrove-service-closeup.png) ·
[Violet Center](evidence/violet-center-closeup.png) ·
[Separate layers](evidence/separate-building-and-ground-layers.png)

## Transparency and context-aware terrain

Building RGBA masters have transparent exterior pixels. Native metatiles use
index zero for transparency on the foreground layer above separate ground tiles.
`placements/` exports the actual independent ground and building layers.

Old terrain-colored facade remnants were removed across the former building
footprints. The lower layer uses Cherrygrove's existing HGSS grass, dirt and shaded
edge strips with the same map-space texture phase. The road branches extend under
the entrances and join the surrounding road using rounded transition profiles.
Ground is never embedded into the reusable building master.

Emerald's current door animator uses flattened frames. The adapter samples the
actual destination ground for those frames and encodes every pixel exactly; it
does not import donor terrain or quantize a mixed ground/facade tile. Existing
house animations are remapped losslessly to the private city's palette labels.

## Native integration and evidence

Engine `6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf` on `codex/violet-city`, based on `5bea9770ed752a9e7d8c763b64f2adb1c73300a9`.
The Cherrygrove city uses a private native tileset pair to preserve all other maps.
Sea tile IDs 1–92, their pixels, palette and callback stay intact. Lossless palette
label alignment and reuse of hidden lower-layer pixels preserve visible colors.
Capacity: Cherrygrove 941/1008 tiles; Violet 974/1008.

- Local ROM compilation passed; SHA-256 in `evidence/build.json`.
- Porymap 6.3.1 offscreen render equals native export: zero differing pixels.
- Both masters equal their installed opaque pixels in both cities, with zero errors.
- Background mGBA checks passed: Center/Mart entry and return, wall collisions,
  roof overlap, cleared old sign ground, existing house entry/return, animated pond,
  Violet's closed entrances, ordinary save, cold reload and title Continue.
- Native captures and door motion were inspected. No desktop emulator was opened.
- No ROM or save is committed. Test-only entry points are inherited from the
  existing isolated preview build; broader campaign playability is not claimed.

[Validation](evidence/native-validation.json) ·
[Door encoding](evidence/door-validation.json) ·
[Center entry](evidence/runtime/center-entry.gif) ·
[Mart entry](evidence/runtime/mart-entry.gif)

## Reproduce

Use Python with NumPy/Pillow (the porygon environment was used). Run from the
source worktree; the engine is the separate `apocrypha-violet` checkout.

```sh
python tools/gba/maps/johto_service_buildings/build.py /path/to/engine
python tools/gba/maps/johto_service_buildings/doors.py /path/to/engine
```

The build adapter reads its pinned baseline and checks `generated-files.json`
before rewriting an existing installation. Reconcile later authored edits before
regeneration. The older Cherrygrove generator refuses this adopted installation.
Build with the established GBA toolchain, then run `runtime.py` with a fresh temp
output directory and `--toolchain PATH`; it uses libmGBA without a desktop window.
`verify.py ENGINE PORYMAP_EXPORT_DIR RUNTIME_DIR` checks/collects the evidence and
refreshes the authored-state guard. Do not include its temporary flash save in Git.
