# Route33 — shared-asset correction of the seven marked sections

Current engine: `codex/route33-hgss` at
`6e4d438b705604ca6e2cfc5fb5172377afa52d8e`, [draft PR10](https://github.com/Davisfox5/pokeemerald-expansion/pull/10).
The owner rejected `89f88993`: tracing gaps again, insufficient seam review and
fills chosen without terrain context. That revision is history, not accepted art.
This edit starts from the preserved `214e38cf` native source and installs shared
assets locally. No initial map generator was replayed.

## Current visual evidence

- [Whole native map at2×](evidence/shared-native-map-2x.png) / [native1×](evidence/native-map.png)
- [Seven enlarged HGSS / rejected / current comparisons](evidence/shared-sections-comparison.png)
- Individual sections: [A](evidence/shared-sections/A.png), [B](evidence/shared-sections/B.png), [C](evidence/shared-sections/C.png), [D](evidence/shared-sections/D.png), [E](evidence/shared-sections/E.png), [F](evidence/shared-sections/F.png), [G](evidence/shared-sections/G.png)
- [Actual native gameplay](evidence/gameplay-gallery.png)
- [Actual Porymap/native comparison](evidence/comparison.png), [native grid](evidence/native-grid.png), [original grid](evidence/reference-grid.png)
- [Shared source masters](source/shared-masters/provenance.json), [native placement ledger](evidence/shared-asset-repair.json), [independent scope review](evidence/shared-asset-review.json)

## Shared assets, not fresh reconstructions

Source: the newer common library on `codex/violet-city`, hub
`9fd8c645a13ecc266ed4df82b64cefef20f3b8da`.
[R02 contextual masters](https://github.com/Davisfox5/pokemon-apocrypha/tree/9fd8c645a13ecc266ed4df82b64cefef20f3b8da/gba/art/johto-common/rocks/r02-context/source)
provide complete front and east/west faces and corners.
[R02 shared masks](https://github.com/Davisfox5/pokemon-apocrypha/tree/9fd8c645a13ecc266ed4df82b64cefef20f3b8da/gba/art/johto-common/rocks/r02-shared-rims/source/tiles)
provide the same minimal convex tips used by that family.
Common scenery L11/L12/L13 supply the ledges. Imported PNGs are byte-identical to
those sources, with hashes/paths recorded. No master is redrawn or recolored;
master RGB and silhouettes are retained with the explicitly selected shared tip masks in native output. Source clipping
uses native quadrants or the shared tip masks. This does not claim the other
thread's map proposal has been merged or that the owner accepted this placement.

T01/T03/T04 remain byte-identical to the latest common tree masters. All tree
positions, complete crowns, roots, Apricorns, boulders and other foreground pixels
outside the ledge are unchanged. Pink fruit is not a pink large tree. The small
flowers remain simplified; no new props or interactions are introduced.

## Contextual decisions by marked area

| Mark | Terrain role and receiving join |
| --- | --- |
| A | Continue the existing raised top to one complete shared south-facing front course behind the forest crowns. Remove the earlier fake padding skirt; do not stack front-face strips. |
| B | This is a **top cap**, not a visible rear wall. Continue the immediately adjacent native top/shoulder quadrants. A reflected front was tried in preview and discarded because it invented a dark beam. |
| C | Install complete L11/L12 masters rotated clockwise so the ledge's raised side is east. The cap stays part of the approved master; no pixels are improvised. |
| D | Join the vertical shared modules to the shared horizontal end/body modules. Retain both original one-way behaviors and collision registration. |
| E | Keep the four-pixel lawn separation from the northern mountain. Continue the adjacent native top cap, then use matching upper side quadrants and the shared convex-tip masks. No grass lip is painted onto bare raised stone. |
| F | Use west-facing side modules, a matching southwest convex return and the front course. Continue a side through the concave notch; never put an outside corner into an inside turn. |
| G | Continue the existing plateau to a complete shared wall footing, rather than ending with a flat stone skirt. Extend the footing eight pixels behind the full existing tree crowns. Block the footprint and the former under-canopy sea corridor; no tree is shifted or cropped. |

The southeast faces are reviewed as one connected receiving surface; isolated
swatch replacements would leave color/phase collars and broken corners. The
existing main plateau and northern mountain textures are retained. Native lawn
and plateau backing come from existing map tiles, not fresh HGSS screenshot cuts.
Every placement and reused backing is explicit in the repair script/ledger.

## Validation and reproducibility

HGSS geographic/material reference remains the original 528×463 overview,
[Johto Route33](https://archives.bulbagarden.net/media/upload/8/8b/Johto_Route_33_HGSS.png),
registered at origin0,0 to 16×16 squares and 8×8 quadrants. Collision is interpreted
from the overview/topology, not described as decoded DS collision.

- Actual Porymap6.3.1 export matches decoded native RGB across all986 cells.
- Independent source/native layer comparison finds zero changes outside the
  explicit repair bounds and connected southeast faces. Foreground outside the
  ledge is identical; behavior/elevation are identical. All backings are opaque.
- 111 changed cells plus neighbors: 279 cells /1116 quadrants in coordinate review
  sheets. All seven assembled comparisons and actual native gameplay close-ups
  were inspected. Source hashes and receiving module orientation are checked.
- Twelve cells gain collision relative to214e38cf: rows21–22, columns26–31.
  Six were already blocked in the rejected89f88993 draft; six more close the
  under-canopy corridor. No blocked cells open, and all water remains blocked.
- Shared artwork uses exact native colors, with zero RGB/alpha approximation.
  One spare bank contains stone/lawn; three previously unused palette2 indices
  receive exact ledge shades. All retained map/border palette uses are checked.
- Nine native files reproduce exactly from214e38cf with
  `shared_asset_repair.py ENGINE --install`, palette CRLF normalized. Native IDs
  of untouched cells/border are retained. Only unreferenced storage is reused;
  maximum glyph987 stays below reserved1008–1023; 414 metatiles allocated.
- Debian Arm GNU14.2.1 builds the ROM. Headless libmGBA0.10.5 passes27 observations:
  cave entry/return, both ledge directions and blocked returns, route walking,
  cliffs/forest/water/footing barriers, ordinary save, cold reload and title Continue.
  A/B camera captures place the camera inside blocked terrain for visual review;
  they are not walking claims. C–G frames use reachable ground.
- Old saves from the previous cloud workspace were unavailable, so historical
  prior-ROM compatibility evidence is retained separately, not claimed for this
  ROM. Current ordinary save checks pass; no save schema is changed.

Read-only checks: `review.py ENGINE PORYMAP_EXPORT`,
`review_shared_assets.py ENGINE BASELINE_ENGINE PORYMAP_EXPORT`,
`check_selected_assets.py`. Runtime: `runtime.py ENGINE NEW_OUTPUT --toolchain ARM_ROOT`.
Build/output identity is in `evidence/build.json`; scope and reproduction are in
`shared-asset-review.json` and `reproduction.json`. The old Porytiles representative
round-trip is historical; this direct native edit does not rerun that packer.

## Preserved history and remaining limits

`previous-89f88993` and Git history retain the rejected pass; `previous-214e38cf`
and older snapshots remain intact. Old marked-repair tools/images document those
attempts and must not be replayed over current native source. Current native
source is the editor authority; the guarded patcher is narrow provenance.

Azalea is unbuilt and the west endpoint remains closed. Apricorn harvest,
encounters, actors, sign dialogue and campaign triggers remain outside this pass.
Eastern inaccessible sea framing is static. Native full-tree spacing and the
half-metatile cap/footing projection remain explicit adaptations. No cave art,
warps, shared production tilesets, unrelated maps or saves were edited. CI and
owner visual acceptance are separate from the local checks; the PR remains draft.
