# Original references and HGSS palette proposal

Owner requested the original HGSS route, Emerald stair context and a recolored
Emerald rock preview. This package is a visual proposal; no engine assets,
ROM, map geometry or collision were changed.

- Original HGSS Route 31: `../../hgss-connections/references/route31-hgss.png`.
  Existing Bulbagarden reference render of Nintendo / Game Freak / Creatures art.
- `emerald-route112-original.png`: original Emerald Route 112, decoded from its
  native layout and General/Lavaridge tilesets. Map scenery only; event objects
  are not included in these Emerald decodes.
- `emerald-mossdeep-original.png`: original Emerald Mossdeep City scenery.
- `emerald-stairs-context.png`: 2x crops of Route 112 and the exact Mossdeep donor.
  Both use general metatiles 0x0af/0x0cf; native placements are asserted.
- `emerald-rock-hgss-palette-comparison.png`: current route at left; proposed
  palette at right. Gray stairs, ground, tile indices and geometry are unchanged.
- `route31-hgss-palette-preview.png`: full current route with the proposed palette.

Five colors are sampled from the original HGSS cliff and substituted only in
the in-memory Route 31/30 rock palette. No source image is repainted or resized
to create game artwork. Comparison panels use nearest-neighbor enlargement.
The preview is a static native decode, not a compiled ROM or emulator capture.
See `provenance.json` for exact samples, source hash and checks.

Reproduce from the worktree root with the existing ignored donor and current
Johto engine workbench:

```sh
python3 tools/gba/maps/johto_synthesis/reference_review.py
```
