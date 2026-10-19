# Goldenrod exterior refinement

Native engine `bb54d528df4f26d457b3b1c5f43bf4de41b3b50f`. First pass accepted by owner; this refinement awaits visual review.

[Updated whole map](../native-map.png) · [Southeast before/after](trees-before-after.png) · [Actual southeast gameplay](../gameplay/southeast-native-trees.png)

All 39 building contexts were compared with the registered HGSS reference. Cleanup removes isolated low-contrast noise while retaining outlines, vents, window frames and deliberate seams. Repeated highrise gold roof planes use one tidy material master with receiving rims, vents and side masks preserved. Residential building geometry remains the accepted first pass. The canonical Center is unchanged.

Four complete native trees replace the clipped southeast row and lone placement. The ground/fence strip uses an unobscured same-phase native donor; a remaining tree fragment against the cliff is replaced with continuous cliff texture. The city now has 49 complete shared trees, without overlapping roots.

Native sources and existing palette banks were edited directly; no first-authoring replay. Palette fitting affected 126 lower-layer and 114 upper-layer pixels; these are recorded reductions within the existing hardware banks, not new colors or blurred edges. Decoded native/Porymap and 75 actual game BG comparisons have zero mismatches. Movement, ordinary save, cold reload, Continue and refreshed walking clips pass.

[Reproduction](reproduction.json) · [Coordinate findings](review.json) · [Building sheets 1](building-review-1.png) · [2](building-review-2.png) · [3](building-review-3.png)

Individual sheets show HGSS / accepted first pass / revised native art at matching scale. Context crops intentionally retain touching buildings and ground for join review; they are not transparent replacement sprites.

| Building | Comparison |
| --- | --- |
| Radio Tower · (168, 128, 320, 400) | [HGSS / before / after](building-00.png) |
| Station annex · (608, 248, 736, 416) | [HGSS / before / after](building-01.png) |
| Magnet Train station · (728, 280, 864, 416) | [HGSS / before / after](building-02.png) |
| North gate · (896, 0, 976, 128) | [HGSS / before / after](building-03.png) |
| Goldenrod Gym · (992, 144, 1112, 232) | [HGSS / before / after](building-04.png) |
| Flower Shop · (1112, 48, 1192, 208) | [HGSS / before / after](building-05.png) |
| Northeast highrise · (1192, 48, 1272, 192) | [HGSS / before / after](building-06.png) |
| North house west · (1184, 128, 1240, 224) | [HGSS / before / after](building-07.png) |
| North house east · (1240, 128, 1304, 208) | [HGSS / before / after](building-08.png) |
| North orange house · (1192, 184, 1248, 248) | [HGSS / before / after](building-09.png) |
| Northwest highrise · (632, 128, 712, 296) | [HGSS / before / after](building-10.png) |
| Underground north · (728, 168, 800, 232) | [HGSS / before / after](building-11.png) |
| Name Rater · (792, 152, 864, 232) | [HGSS / before / after](building-12.png) |
| Game Corner · (760, 472, 872, 560) | [HGSS / before / after](building-13.png) |
| West apartment north · (632, 472, 696, 552) | [HGSS / before / after](building-14.png) |
| West apartment east · (696, 472, 760, 552) | [HGSS / before / after](building-15.png) |
| West orange house · (632, 544, 696, 632) | [HGSS / before / after](building-16.png) |
| Bill family house · (728, 576, 792, 664) | [HGSS / before / after](building-17.png) |
| Underground south · (728, 648, 792, 728) | [HGSS / before / after](building-18.png) |
| Southwest house · (584, 648, 648, 736) | [HGSS / before / after](building-19.png) |
| Southwest tower · (600, 680, 680, 776) | [HGSS / before / after](building-20.png) |
| Southwest tower south · (648, 728, 728, 832) | [HGSS / before / after](building-21.png) |
| South house west · (728, 736, 792, 816) | [HGSS / before / after](building-22.png) |
| South house east · (792, 736, 856, 816) | [HGSS / before / after](building-23.png) |
| Department Store · (992, 480, 1080, 656) | [HGSS / before / after](building-24.png) |
| Department annex · (1080, 584, 1160, 680) | [HGSS / before / after](building-25.png) |
| Bike Shop · (1080, 640, 1160, 728) | [HGSS / before / after](building-26.png) |
| East apartments · (1112, 464, 1184, 544) | [HGSS / before / after](building-27.png) |
| East orange house · (1144, 520, 1216, 584) | [HGSS / before / after](building-28.png) |
| East railway highrise · (1176, 376, 1256, 496) | [HGSS / before / after](building-29.png) |
| East tower upper · (1224, 496, 1304, 600) | [HGSS / before / after](building-30.png) |
| East house · (1240, 584, 1304, 664) | [HGSS / before / after](building-31.png) |
| East tower middle · (1224, 632, 1304, 712) | [HGSS / before / after](building-32.png) |
| East tower lower · (1224, 696, 1304, 784) | [HGSS / before / after](building-33.png) |
| Southeast house · (1224, 752, 1304, 832) | [HGSS / before / after](building-34.png) |
| Southeast tower · (1144, 728, 1224, 832) | [HGSS / before / after](building-35.png) |
| Southeast apartments upper · (1016, 704, 1080, 776) | [HGSS / before / after](building-36.png) |
| Southeast apartments lower · (1016, 744, 1080, 816) | [HGSS / before / after](building-37.png) |
| approved Violet Pokemon Center · (789, 574, 873, 656) | [HGSS / before / after](building-38.png) |
