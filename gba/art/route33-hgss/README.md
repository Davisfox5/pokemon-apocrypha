# Route33 — original-reference correction

Current engine source: `codex/route33-hgss`,
`89f8899335cd5182e534d8a5c4f9e5e21bb57615`, [draft PR10](https://github.com/Davisfox5/pokeemerald-expansion/pull/10).
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

The seven owner-marked sections are repaired locally. A restores rock footing behind
northwest crowns; B/E restore clipped original rear edges; F restores the original
rounded wall corner. C/D align and join the native Emerald ledge arms. G fills the
missing southeast rock footing while retaining every original tree position.
A/G use existing native plateau texture where HGSS foliage occludes the reference.
B/E/F restore actual connected original-source rock pixels. Main mountain textures
remain intact. Six cells (row21, columns26–31) gain rock collision; none are opened.
No elevation changes or native background/foreground pixel changes outside the
seven reviewed bounds and their connected ledge corridor occur.

See [all seven original / before / corrected sections](evidence/marked-sections-comparison.png)
and [scope proof](evidence/marked-review.json). Older restored-reference and
reference-correction images document the preceding 214e38cf pass, not this revision.

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

Actual Porymap 6.3.1 export equals decoded native RGB for all 986 cells.
Porytiles representative layered round-trip reports zero RGB/alpha errors.
Native glyph maximum992 remains below reserved1008–1023; 455 metatiles allocated.
Arm GNU14.2 builds the ROM. Headless libmGBA0.10.5 passes 29 observations,
including cave travel both ways, both directional ledges, blocked forest/rock/water,
and ordinary save, cold reload and title Continue. A copied prior save also loads
and Continues without modifying the original. A/B close-ups use controlled cameras
inside blocked terrain and are visual evidence only; C–G frames use reachable land.

The seven changed native files reproduce exactly from baseline214e38cf with
`repair_marked_sections.py` (palette line endings normalized). This guarded local
patcher does not replay the original layout generator. Prior source and evidence
snapshots are preserved under previous-214e38cf; older rejected revisions remain
historical. Native source is the editor authority.

Checks: `review.py ENGINE PORYMAP_EXPORT`, `review_marked_sections.py ENGINE BASELINE_NATIVE`,
`check_art.py ENGINE PORYTILES`, `check_selected_assets.py`, and
`runtime.py ENGINE NEW_OUTPUT --toolchain ARM_ROOT`.

## Limits

Azalea is unbuilt and the west endpoint is closed. Encounters, actors, sign
dialogue and campaign triggers remain outside this map-art pass. Apricorn harvest
is unwired; small flowers remain simplified. Eastern inaccessible sea framing is
static. Shared Gen3 tree/ledge shapes and finite native palette conversion are
explicit adaptations. CI is separate from local checks; owner visual acceptance
remains pending.
