> **Rejected by owner; superseded by [R02 revised sample](../r02-refined/README.md).**
> Retained only as historical evidence. Do not reuse its screenshot repairs.

# R02 side-cliff pilot

Start with [original / rebuilt / on-map comparison](review/comparison.png).
All three panels show a 192x128-pixel area at exactly 3x nearest-neighbor scale.

- Left: unchanged original HGSS Route 36 crop (R02).
- Middle: rebuilt rock and stairs on independent destination ground; trees and
  tall grass are omitted here so the joins are visible.
- Right: that section in the current Route 36 map, decoded from compiled GBA tiles.
  This is an offline native map preview, **not an emulator screenshot**.

[Transparent 16x16 modules](review/modules.png) |
[Full route with the pilot](review/route36-preview.png) |
[Previous map crop](review/map-before.png) |
[Evidence](evidence.json)

## What changed

The west face now follows the narrower, rounded HGSS silhouette and earth colors.
The repeating face is traced from the actual R02 map. Where the donor tree hid its
left margin, exposed rock from the same row reconstructs that margin; every repaired
pixel is recorded. Two repeat modules and four stair-surround modules retain the
stair opening's upper and lower projecting lips. Four additional cells hold the
previously reviewed neutral-stone S04 treads, at their original source anchor.
The transparent masters contain no grass or dirt. Ground remains independent.

The rock shares a 15-color palette selected from actual source shades. Palette
reduction changes 110 source pixels; it does not alter the opaque silhouette.
Source foreground PNGs and exact indexed exports are included. This uses existing
project pixel tools and Porytiles; no generated replacement artwork is involved.

## Scope and verification

This first pilot covers only the west side face and its stair opening: eight map
cells at x=14, y=18..25. Plateau corners, other directions and cave mouths remain
future work after visual review. No entire cliff family is claimed complete.
The wider route image retains the old art outside the small pilot area.

- 43 metatiles, 144 tile slots and 5 palette banks for the full comparison crop.
- Porytiles compilation passes; decoded output has zero RGB555 pixel differences.
- Every master has binary transparency and an exact <=15-color indexed export.
- Pixels outside the pilot are unchanged. Approved tree source is reused intact.
- Engine source, collision, elevation, doors, warps and events are untouched.
- No emulator opened; runtime placement/priority has not been tested or installed.

Engine snapshot: `6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf`.
Original game artwork: Game Freak / Nintendo / Creatures.

## Reproduce

```sh
python tools/gba/maps/johto_common/r02_pilot.py --engine /path/to/apocrypha-violet
```

Requires the existing Pillow/NumPy environment and `porytiles-legacy` on PATH.
Only this pilot review directory is written. The engine must be at the pinned clean
revision. `native/preview-map.bin` is an isolated review crop, not installable map
block data: no collision/elevation or destination metatile numbering is assigned.
