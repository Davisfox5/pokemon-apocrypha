# Route 30 native rebuild — review proposal

Engine source: [`codex/route30-rebuild`, `17281b47`](https://github.com/Davisfox5/pokeemerald-expansion/commit/17281b47f0f6d9a04f0668c1aef8800a85bae6d2), based on `apocrypha@2722eaf`. [Engine PR #2](https://github.com/Davisfox5/pokeemerald-expansion/pull/2).

[Whole-map comparison](evidence/comparison.png) · [Revised map](evidence/proposal.png) · [Full tree footprints](evidence/footprint-review.png) · [Blocked terrain overlay](evidence/blocked-terrain.png) · [Native gameplay frames](evidence/gameplay/).

This pass corrects tree alignment and original access restrictions, rather than adding density. The accepted native tree owns a complete 32×48 pixel / 2×3 tile footprint. New instances have no overlapping footprint or opaque pixels, and avoid preserved connection artwork, cliffs, stairs, signs and buildings. Empty transparent corners do not make forest cells walkable. Native house art replaces the mismatched donor perspectives; copied partial tree fragments were removed. The 16-variant tall-grass family derives from the preserved HGSS egrass texture and was compiled and decoded through Porytiles.

## Evidence and limits

- Porymap 6.3.1 core project loader/renderer exported the actual checkout; Route 30 matches the native decode exactly. This is not a manual GUI edit/save test.
- Five surrounding maps render identically: Cherrygrove, Route 29, New Bark, Route 31, Violet entrance. The accepted lab and all map/event IDs are unchanged. Connection-visible secondary metatile IDs and palette banks were reserved.
- Native packing has zero scenery pixel differences. The tree audit records 169 new complete instances, zero overlaps, zero non-forest pixels and zero clipped instances. Protected connection art stays at its prior pixels.
- Headless libmGBA 0.10.5 tests actual directional input along the entire route, both connections in both directions, ten forest/cliff barriers, tall grass, the one-way ledge, signs, ordinary 128 KiB save, cold load and title Continue. Full observations are in `evidence/results.json`. No desktop game was opened.
- The 35×74 original terrain stencil is measured from the preserved HGSS overview and earlier reference measurements, **not recovered Gen 4 collision archives**. The accepted map's 86-row Cherrygrove approach and shared camera windows remain adaptations. Visual/original-map fidelity still requires owner review.
- Route 30's existing houses have no interior warps; this exterior pass does not add interiors, dialogue or roles. The new freshwater pond is static. No future-story shortcuts or ten-year town changes were introduced.
- ROM, save and tool binaries are not committed. Runtime fixtures use the engine's existing debug map proof entrance to position scenes, then test ordinary key inputs; they do not prove a campaign start sequence.

## Source and provenance

`source/layout.json` is the new editable blueprint; `source/hgss-navigation.json` is the reference measurement stencil. `source/baseline/` preserves the prior Route 30 native blockdata/tileset and the shared palette/tile decode inputs at `2722eaf`; the original remains in engine history. `source/materials/` contains editable native-scale material PNGs, and `source/porytiles-grass/` and `source/porytiles-native/` preserve compiler input/output.

Trees, gabled house and blue house are reused without resizing or recoloring from `gba/art/cherrygrove-synthesis/refined/`. Ground/path helpers and palette packing come from the existing native authoring libraries. HGSS reference: `gba/art/claude-routes/references/route30-hgss.png`; decoded texture: `gba/art/johto-cohesion/references/egrass.png`. Original Pokémon art/reference belongs to its original creators (Game Freak/Nintendo/The Pokémon Company); repository conversion work is recorded in its earlier source/provenance. No Nintendo archive was restored.

## Reproduce in an isolated review checkout

Do not replay a historical generator over an owner-edited layout. These new tools reproduce this specific authored proposal only; use an isolated checkout of the recorded engine base.

```sh
python3 tools/gba/maps/route30_rebuild/editor.py /path/to/engine-review
# porygon's MCP Python environment, with porygon importable:
python tools/gba/maps/route30_rebuild/apply.py /path/to/engine-review
make -C /path/to/engine-review -j1 generated
make -C /path/to/engine-review -j8
python3 tools/gba/maps/route30_rebuild/runtime.py /path/to/engine-review /path/to/evidence --toolchain /path/to/toolchain
```

The editor imports existing packing utilities but never calls the old map generators. It writes only Route 30's secondary tileset plus a proposed grid; porygon applies that grid. Porytiles legacy 2.0.0 compiled `source/porytiles-grass/` using `compile-primary -dual-layer -target-base-game=pokeemerald -transparency-color=0,0,0 -default-behavior=2`; native output is decoded and compared pixel-for-pixel before import into free bank 10. Bank 12 contains pond art. Other banks are preserved. Shared primary animated tiles 1–92 are reserved.
