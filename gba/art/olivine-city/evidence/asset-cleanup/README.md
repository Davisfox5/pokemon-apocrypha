# Olivine — full local asset cleanup

Native source **`506860f6a88ba96833f8bec256ebbda110b1113f`**, [source PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21). This supersedes the local artwork in `8eb23f67` while preserving the established elevation, grove rows and traversal.

- [Actual native whole map](native-map.png) · [HGSS / previous / current](whole-map-before-after.png)
- [Every asset: findings and comparisons](asset-review.md) · [Master inventory](asset-inventory.json) · [Every placed instance](instance-audit.json)
- [All used native tiles](tile-inventory.json) · [Native grid](native-grid.png) · [HGSS grid](reference-grid.png)
- [Civic buildings](western-civic-before-after.png) · [Residences and groves](eastern-residences-before-after.png) · [Service buildings](town-services-before-after.png)
- [Lighthouse and cliffs](lighthouse-coast-before-after.png) · [Quay furniture and rails](quay-props-before-after.png) · [Ferry terminal](harbor-before-after.png)
- [Complete receiving surfaces, all objects hidden](all-objects-hidden.png) · [Trees hidden](trees-hidden.png)
- [Actual gameplay](gameplay-gallery.png) · [Native audit](review.json) · [Build and runtime](build.json) · [Preservation](preservation.json)

Fourteen local masters were redrawn/cleaned, then converted to native palettes and fitted to their existing locations. The lighthouse additionally received explicit repeated parapet tiles and matched window frames. The stone pass removes isolated noise and reserves unique tiles for silhouettes and joins. All 19 placed foreground families, five receiving-material cores and 1,289 used metatiles have review evidence. The current source includes City, Quay **and Harbor**.

Actual Porymap/native parity, all 4,032 cell checks, every visible master placement, 237 non-overlapping tree roots and reachable building approaches pass. The ROM builds and all 39 headless observations pass, including both stair axes, district returns, barriers and ordinary save/cold Continue. Shared Center/Mart/sign pixels, all IDs, collision/elevation, grove counts and timber crossing pixels are preserved. No ROM or player save is committed.

ROM SHA-256: `acb792f3cce96f8e2083fd67f1c3bd5bbd1af91f72c57903cbcbae2aa1a05b92`. Native glyph use: City 998/1008, Quay 1005/1008, Harbor 394/1008. Palette use: 10, 13 and 3 banks respectively. These are native adaptations of HGSS, with the limitations recorded in [the review](asset-review.md#limits). Owner visual acceptance remains pending.

[Hosted status](hosted-ci.json): no PR-triggered workflow run was returned; the qualified results above are local checks, and the PR remains draft.
