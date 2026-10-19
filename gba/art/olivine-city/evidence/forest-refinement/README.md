# Olivine — counted groves and completed ground

Native source **`8eb23f6774fd937f3018d413f1fab5b6dc8d05c8`**, on [draft PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21). This supersedes the trees and affected receiving surfaces in `116ea801`; the improved hill layout was the starting constraint, not approval of its tree-shaped holes.

- [Actual native whole map](native-map.png) · [HGSS / before / after](whole-map-before-after.png)
- [Northern rows](northwest-rows-before-after.png) · [Western rows](western-rows-before-after.png) · [Lighthouse grove](lighthouse-grove-before-after.png)
- [Northern shelves](northern-shelves-before-after.png) · [Upper coast](upper-coast-before-after.png) · [Complete eastern planted shelf](planted-coastal-shelf-before-after.png)
- [Trees hidden: completed receiving surfaces](trees-hidden.png) · [Coastal shelf with/without foliage](planted-coastal-shelf-understory.png)
- [All 45 row counts](tree-rows.md) · [Reference grid](reference-grid.png) · [Native grid](native-grid.png)
- [Actual gameplay gallery](gameplay-gallery.png) · [Native audit](review.json) · [Build/runtime](build.json) · [Preservation manifest](preservation.json)

The narrow shared crowns and generic 32×32 placement have been replaced with an unscaled HGSS-derived broad crown, using eight shades from the existing Johto palette. Dense groves follow the reference's roughly 32×24 spacing. The assembly contains **237 complete trees**, including 24 explicit map-edge additions. Occluded lighthouse positions are completed on the established row grid.

The remaining tree-shaped grass holes were a terrain problem. The receiving surfaces were inspected without foliage, northern courses were completed with caps, and the eastern shore was reconstructed as the continuous planted shelf visible in HGSS. Its outer rock face had been omitted from the earlier trace. Sand remains in the pocket north of that shelf. Two land rocks were reseated, and the local houses now use the same roof/timber palette. Rock interior glyphs retain original texture while accounting for neighboring joins.

Both timber openings retain their exact foreground pixels and movement axes. Shared Center/Mart/sign art, building geometry, Harbor source, other maps and all IDs remain unchanged. **39 headless observations**, ordinary save/cold Continue, 4,032 cell checks and actual Porymap/native pixel parity pass. ROM SHA-256: `f4238572c716d63af671aece82065bc4007151b4efe978e86d9ea483c3ad80e6`. No ROM or player save is checked in.

The trees-hidden view shows the complete receiving plane before invisible-background tile packing; the native composite is independently decoded and checked. HGSS hidden elevations/collision remain interpretations. Interiors, Routes 39/40 and shipping are unwired; water is static and district changes fade. The owner liked the groves and improved depth; acceptance of this completed revision remains pending.
