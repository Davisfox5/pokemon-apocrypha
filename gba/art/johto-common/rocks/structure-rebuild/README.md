# Routes 31 and 32 — complete rock structure rebuild

2026-10-17. Owner rejected the placement correction pass and requested removal and reconstruction of both maps' rock structures. This is that replacement, pending visual acceptance.

## What changed

The former rock pixels are cleared. Editable HGSS contour lists construct complete solid plateaus, continuous side planes and single front drops. A complete shared R02 face is adapted to the measured course height; it is not repeated vertically within a drop. Grass-topped wall runs use the shared grass fringe once at the top. Foreground trees, stair treads, railway and cave mouths are independently composited. Ground or water replaces the removed portions of the old structures.

- Route 31: rebuilt three connected mountain levels, pond divider and southern wall; 347 art cells changed. Seven old blocked cells on the cleared western mountain margin become ordinary ground.
- Route 32: rebuilt eighteen solid terrain sections and seven grass-topped wall runs; 1,029 art cells changed. Thirty-two collision/behavior cells follow the reconstructed outlines, including clearing superseded rock and blocking new rock. Source comparison caught the northeast massif starting too far south; its upper contour was corrected to source y560/592/608.
- Warps, event positions, buildings and map connections are unchanged. Existing stairs retain their travel axis and reserved traversal cells. Cave interiors, other route branches and ten-year town adaptations are untouched.

## Evidence

`review/*-native.png` are decoded native output and equal actual Porymap 6.3.1 exports pixel for pixel. Nine coordinate-labelled source/native grid sheets cover all altered rock sections. `evidence/*-cells.csv` records every changed cell's collision/elevation and behavior. `evidence/*-collision.json` lists each intentional change; no other gameplay cells changed. Both ROM builds and headless movement/stair/door/connection/save/cold-reload/ordinary-Continue runs pass. Reviewed gameplay frames and exact ROM/source identities are under `evidence/`. No desktop game was opened.

Source branches are pushed: Route 31 `1643f58a48` (PR14), Route 32 `6a5fbb19cf` (PR17). They remain separate review branches and are not merged into a campaign checkout.

## Source and native adaptation

`source/structures.json` is the new geometry authority. It replaces the preceding rectangle-over-old-mask treatment. Route 31's mountain uses the HGSS contour translated -8px horizontally to retain the approved cave threshold; its pond/divider retain approved native positions. Route 32 uses +16,+16px registration and continues source-edge rock through its native border. Source is traced overview imagery, not decoded DS geometry or collision.

The top texture comes from an unobscured HGSS Route31 32px patch at (944,32), mapped to each native rock palette. Route 31 uses that 32px texture and both shared front variants; Route 32 uses a compact 16px core and one front/side variant to preserve complete geometry within hardware capacity. Route 31 has 171 spare graphics; Route 32 has six. Layouts follow native square footprints, so silhouettes are still native adaptations, not pixel-identical DS projections. Existing non-rock tree density and path outlines are outside this rebuild.

## Reproduction

Use immutable baseline commits and selected file lists in `source/inputs.json` to materialize `/tmp/rock-rebuild-baselines/JohtoRoute31` and `JohtoRoute32`. Work only in disposable matching engine checkouts, setting `engine` in the local input configuration as needed. Run `tools/gba/maps/johto_common/rock_structures.py --install`, then `rock_structure_collision.py`. Installation rejects a changed baseline; never replay it over owner edits. Build with the pinned ARM toolchain, export using the existing actual-Porymap helper, and run `rock_structure_review.py`. Use the existing `regional_runtime_cities.py` and `regional_runtime_r32.py` wrappers for background gameplay checks. All pixel allocation is lossless after the explicit source palette conversion; no nearest-neighbor glyph substitution is used.
