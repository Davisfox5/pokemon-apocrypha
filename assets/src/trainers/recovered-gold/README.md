# Recovered custom adult Gold

Recovered on 2026-09-13 after the owner confirmed that Gold had been customized.
The missing artwork was recorded in Aseprite as `/private/tmp/adultgold_frame0.png`
and `/private/tmp/adultgold_grid.png`. Those PNGs were no longer present. Aseprite's
recovery sessions retained the edited document pixels and palettes.

The latest recovered sheet is
[gold_adult_ow_grid.png](../overworld/gold_adult_ow_grid.png), with an editable
[Aseprite copy](../overworld/gold_adult_ow_grid.aseprite) and
[enlarged preview](gold-preview.png). It is a 192×128 grid of twenty-four 32×32
overworld cells. The original palette, transparent index zero, canvas and cel
position are preserved. No redraw, recolor, resizing or GBA quantization was
applied to the source; the preview alone is enlarged with nearest-neighbor pixels.

The latest available backup is session `20260625-003641-36760`, document 8,
image revision 25. Three earlier documents are also recovered: the June 23
single-frame edit and the June 23/24 grid revisions. The original recovery
records were copied into `aseprite-backups/` before decoding, leaving the app's
files intact. `recovery.json` records input hashes, document origins and output
hashes. The temporary filenames explain why normal Gold/Ethan asset searches
did not find the custom work in the repository.

Reproduction: `python3 tools/artwork_library/recover_adult_gold.py`.
The decoder implements the indexed single-cel format checked against the local
Aseprite source (`app/crash/write_document.cpp` and `doc/*_io.cpp`). Decompressed
indices and palettes round-trip exactly. Aseprite itself loaded the restored PNG
and saved the editable copy; exporting that copy reproduced every RGBA pixel.
This recovers the latest backed-up canvas, not the original undo history.

This is existing owner-customized Gold artwork, distinct from the adult Silver
assets. It has not yet been registered or placed in the GBA map. Its 24-cell
direction/action layout must be classified before using the twelve-frame NPC
import profile. Preserve the recovered source when preparing that conversion.
