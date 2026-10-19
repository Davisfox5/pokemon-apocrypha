# Cleaned Olivine asset source

Input native commit: `8eb23f6774fd937f3018d413f1fab5b6dc8d05c8`. Result: `506860f6a88ba96833f8bec256ebbda110b1113f`. Edit the current source on subsequent revisions; never replay this guarded pass or an original map generator over later owner edits.

HGSS reference: [original overview](../hgss-reference.png), [Bulbagarden origin](https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png). Reference geography is registered at +64,+16 without scaling the scene. Individual cleaned assets are resized into explicitly recorded native footprints; they are adaptations, not extracted DS texture data.

`edit-input-atlas.png` assembles the prior local cutouts for the image-edit pass. `edited-atlas.png` is the transparent image-tool result. It is **not** ready-made native artwork: the editor shifted cells, so `asset-import.json` records each actual source crop, native bounds and palette. `import_clean_assets.py` performs explicit registration, 1-bit alpha conversion and RGB5 assignment, and rebuilds the lighthouse's repeated trim/windows as native modules. The resulting editable native masters are in `masters/`. Existing shared service buildings/signs and the current timber crossings are preserved.

`clean_assets.py` begins with the verified current planes and applies only the reviewed local masters, receiving-ground restoration and constrained stone cleanup. It preserves collision, priority, all tree rows and geography. `receiving-surfaces.png` is complete authored ground; `background.png` includes invisible-background reuse for hardware packing. `compile_planes.py` now optionally stages all three districts before source mutation. `terrain_palettes.py` uses exact candidate covering, falling back to direct color assignment when a candidate set exceeds the native budget. No RGB substitution occurs in the palette packer.

From the hub, on the pinned input checkout only:

```sh
python3 tools/gba/maps/olivine_city/import_clean_assets.py
python3 tools/gba/maps/olivine_city/clean_assets.py ENGINE PORYTILES
QT_QPA_PLATFORM=offscreen PORYMAP_EXPORT ENGINE EXPORTS
python3 tools/gba/maps/olivine_city/review.py ENGINE EXPORTS asset-cleanup
python3 tools/gba/maps/olivine_city/audit_assets.py ENGINE
```

Build/runtime commands, hashes, comparisons and qualified limits are in [the evidence](../../evidence/asset-cleanup/README.md). The original game art belongs to its respective owners; this retains its provenance for the Apocrypha project. Visual acceptance remains pending.
