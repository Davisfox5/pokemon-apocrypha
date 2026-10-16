# Route33 — original-reference correction

Current engine source: `codex/route33-hgss`,
`214e38cfb94309965e0cc58d09460e58737e00a6`, [draft PR10](https://github.com/Davisfox5/pokeemerald-expansion/pull/10).
HGSS is the geographic/material authority. The owner rejected a broad terrain
revision; it was reverted at `515d80c7`. The original mountain contours, wall/cap
textures, footprints and traversal are restored. No extra cliff caps, extended
walls, new tree rows or procedural shoreline are retained.

## Current visuals

- [Whole native map](evidence/native-map.png)
- [Original HGSS / restored map / bounded current correction](evidence/restored-reference-comparison.png)
- [Focused before/current review](evidence/reference-correction-closeups.png)
- [Actual Porymap/native comparison](evidence/comparison.png)
- [Native gameplay](evidence/gameplay-gallery.png)
- [HGSS numbered grid](evidence/reference-grid.png) / [native grid](evidence/native-grid.png)

## Tile and object work

Use the [actual HGSS overview](https://archives.bulbagarden.net/media/upload/8/8b/Johto_Route_33_HGSS.png),
528×463px, origin (0,0) at 16px native squares with 8px quadrants. Native 34×29 includes
16px eastern framing and one bottom padding pixel. Material and traversal ledgers
are independent. Overview interpretation is not claimed as decoded DS collision.

Current changes are bounded: gray residue in the visible original cave opening
is black; actual original HGSS foam/sea pixels replace the hard coastal join in
x504:512. Mountain geometry, texture phase, original cap/faces and elevation are
unchanged. `reference-scope.json` compares decoded native background pixels with
the restored original: zero changes outside the two named regions, zero collision
or elevation changes across 986 cells, every backing opaque, warp opening black,
and all water cells blocked. This is a scope proof alongside the HGSS visual review.

Foreground uses owner-approved masters from hub commit
`3d593788873f5e3446e2d032764bc1b43c1ffcbc`: T01 large trees, T03/T04 Apricorns,
and L11/L12/L13 horizontal ledges. Their RGBA files are copied unchanged, with
hashes and origin pinned in `source/transparent-objects/`. The original full tree
checker passed in a clean checkout of that commit; the local selected-master
checker verifies installed inputs. Terrain is beneath the objects. The 197-pixel
mint ground oval is absent from T01. Apricorn anchors are fitted to their native
root cells; interaction and collision IDs remain unchanged. The existing vertical
Emerald ledge remains, with the complete local corner join.

The two large land boulders are extracted from this route's actual HGSS source,
with adjacent tree/trunk and lawn removed. They are separate RGBA foregrounds;
no matching large land-boulder master was in the supplied scenery catalog.
Source RGB/alpha masters remain intact. The two Apricorn masters have 19 combined
native shades; the route's 15-color shared bank merges nearby shades during native
conversion. No master was recolored. No new harvest behavior is introduced.

## Verification and native editing

Actual Porymap 6.3.1 export equals decoded native RGB for 986 cells. Behavior/collision
match the separate ledger. Porytiles representative layered round-trip reports
zero native RGB/alpha errors. Native glyph maximum 987 stays below reserved 1008–1023.
There are 414 allocated metatiles; superseded private entries are not a new asset catalog.

Arm GNU 14.2 builds the 32 MiB ROM. Headless libmGBA 0.10.5 checks 25 observations:
real cave travel both ways, main-route walking, directional ledges and blocked
returns, forest/cliff/fruit footprints, grass, water boundary and ordinary 128 KiB
save/cold reload/title Continue. The water-only negative probe uses controlled
placement and is not a reachable shoreline travel claim. A copied prior 224ee13c
route save also loads/Continues; its original is unchanged. Exact identities and
proof are in build.json/runtime.json/prior-route33-save.json/preservation.json.

All 11 current repair files reproduce from the exact 224ee13c native baseline with
`match_reference_cells.py`; palette line endings are normalized. The original
broad revision is rejected and is not the authoring path. Native source remains
the editor authority. Never replay old build/register generators over owner maps.
The matching tool guards baseline files, composes local native layers and reuses
freed glyphs; it does not rerun the original map generator. Original snapshots,
full reference renders and Git history remain preserved.

Useful read/check commands under tools/gba/maps/route33_hgss:
`check_selected_assets.py`, `review.py ENGINE PORYMAP_EXPORT`,
`check_art.py ENGINE PORYTILES`, `check_reference_scope.py ENGINE BASELINE_NATIVE`,
`runtime.py ENGINE NEW_OUTPUT --toolchain ARM_ROOT`, and
`publish.py ENGINE RUNTIME_OUTPUT`.

## Limits

Azalea is unbuilt and the west endpoint is closed. Encounters, actors, sign
dialogue and campaign triggers remain outside this map-art pass. Apricorn harvest
is unwired; small flowers remain simplified. Eastern inaccessible sea framing is
static. Shared Gen3 tree/ledge shapes and finite native palette conversion are
explicit adaptations. CI is separate from local checks; owner visual acceptance
remains pending.
