# Union Cave — stone stairs, smooth rock shading and fitted thresholds

Native source **`988e0287216410698481d313e73d6cf99f650b76`**, branch `codex/union-cave-1f`,
[draft engine PR #9](https://github.com/Davisfox5/pokeemerald-expansion/pull/9).
This corrects the preceding `de6922a` pass across 1F, B1F and B2F.
[B1F review](../union-cave-b1f/README.md) · [B2F review](../union-cave-b2f/README.md).

## Visual review

- [Southern entrance: previous / replaced / actual gameplay](evidence/south-entrance-before-after.png)
- [Entrances, stairs and rocks: HGSS / de6922a / corrected native](evidence/entrances-rocks-before-after.png)
- [Whole original / native 1F](evidence/comparison.png), [native gameplay](evidence/gameplay-gallery.png)
- Source/native panels: [north](evidence/material-comparison-1.png), [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- [Every wall cell, source / native, with coordinates](evidence/wall-cell-review.png)
- [Original HGSS stone-step texture and native up/down assets](evidence/stone-stairs-reference.png)
- Preserved passes: [de6922a](evidence/previous-de6922a/comparison.png), [6abf7e84](evidence/previous-6abf7e84/comparison.png)

## Corrections and material checks

Rock and wall shading receives bounded cleanup within the same material. This
removes isolated resampling noise without blurring floor into wall, cutting rock
silhouettes or changing their base footprints. Beige formations remain boulders.
Complete teal rock heads retain their separate native foreground layer.

The previous independent RGB tile substitution could replace part of a wall with
an incompatible piece. Native packing now requires the **same exact 8×8 material
mask** for every substitution: floor, wall, water and void outlines cannot be
exchanged. Spare glyphs cover the largest remaining shading/border errors. Shared
wall palette ramps prevent palette changes across ground/water banks. Compact
floor, water and plateau texture families are reserved instead of flattening them.
Interior shading still uses a finite 1,008-tile dictionary; this is not a claim of
pixel-exact source RGB or extracted original DS collision.

The approved northern light/threshold treatment remains pixel-identical in its
48×32 protected region. A literal copy to the southern warp row was rejected:
the southern rock rim has a different baseline, and the northern west corner
turns downward. The replacement fits the approved light **four pixels higher**
than that literal translation, replaces the full rim and straight shoulders,
and omits that corner. Local open floor stays open; there is one continuous rim
rather than a stacked border or hanging pillar. The southern exterior is still
unwired and remains blocked beyond its threshold.

All eight stair markers now use native stone treads derived from **the actual
HGSS Union Cave `d_level01.png` texture**, with ascending/descending variants.
No Emerald wooden ladder artwork remains in the current assets. The existing
native warp behavior 97 remains appropriate for instant cave floor transitions.
[Texture provenance and checksums](source/hgss-textures/provenance.json) credit
Nintendo / Game Freak / Creatures and the Kuramapika1 texture rip hosted by The
Models Resource. The overview references remain hosted by Bulbagarden Archives;
original event records come from pret/pokeheartgold.

| Native stair pair | Return destination |
| --- | --- |
| 1F north `(5,5)` | B1F main `(31,35)` |
| 1F water-separated south `(7,57)` | B1F lower west `(4,48)` |
| B1F lower east `(29,46)` | B2F northwest `(4,5)` |

The two other B1F markers still reference unpictured Alph rooms. Route32's two
external entry cells, return warp and IDs remain unchanged. The accepted 34×60
first floor, 36×52 B1F and 40×47 B2F registrations remain; these projected overview
images are not decoded DS collision. [Original registration](source/warp-registration.json)
and [event records](source/hgss-events.json) preserve the distinction.

## Verification

- Local ROM build passed. Actual Porymap 6.3.1 exports match native decoding on
  all three floors with zero pixel differences; no desktop game was opened.
- All 5,792 collision/elevation entries are byte-identical to `de6922a`.
  [Preservation](evidence/physics-preservation.json) and [native audit](evidence/all-floors-audit.json).
- Every actual background quadrant is checked against its tile bytes and material
  silhouette; wall cells have coordinate-labelled source/native review sheets.
  [Wall review](evidence/wall-review.json).
- Layered Porytiles imports round-trip 128 representative metatiles per floor
  with zero RGB/alpha errors. Foreground RGB, opaque backgrounds and tile budget pass.
- Native walking, Route32 entry/return, all three stair pairs in both directions,
  controlled existing-engine Surf/disembark, the southern threshold/barrier, and
  separate ordinary 128KiB saves/cold reload/title Continue on all floors pass.
  [Exact source, ROM hash and phase results](evidence/all-floors-build.json).
- Copies of three preceding proof saves reload/Continue; originals are untouched.
  [Compatibility scope](evidence/previous-save-compatibility.json). These are
  development proof saves, not arbitrary campaign-save qualification.
- Repeated authorized packing is byte-identical across 117 native asset/layout
  files. [Reproducibility](evidence/reproducibility.json). Shared art, Route32,
  existing map IDs and warp definitions remain unchanged. CI status is separate
  from the local build and owner visual acceptance.

## Concrete remaining scope

The pictured floor sections and their three internal stair pairs are built.
Original warp records also name upper Alph transit rooms **outside these overview
images**; those rooms and their destinations are not invented here. Two B1F stair
markers remain unwired for that work. Route33 exterior is also pending. The fixed
Strength boulder preserves its barrier; pushing is not implemented/qualified here.
Water art is static. Campaign actors, items, encounters, Lapras and Surf badge/party
activation remain separate work. Surf proof setup initializes the existing engine
state on water; it does not grant a campaign HM or change progression gates.

## Focused basement review after owner approval of the entrance

Both B1F and B2F received a separate close-up review of wall returns, concave and
convex corners, low shore lips, lake rims, rock/shore overlaps, sprite-removal
sites and stair approaches. The review found a remaining B1F trainer-outline
fragment at cells `(23,16)` / `(23,17)`. Two unique native glyphs were cleaned
within their existing face/base shading plane: **29 visible pixels**, with no
layout, collision, palette, metatile IDs or footprint change. B2F required no
additional art edits. First-floor artwork remains unchanged.

[B1F focused review and repair](../union-cave-b1f/README.md) ·
[B2F focused review](../union-cave-b2f/README.md).
Both include original / preceding / current corner sheets and fresh gameplay
camera views. Controlled framing is separate from the full traversal proof.
Native material/physics checks, Porymap equality and appropriate runtime/save
checks were rerun after the B1F asset edit. Visual acceptance remains with owner.

## Editable source and isolated reproduction

Edit current native layouts/assets directly. Preserve owner edits, IDs, previous
source/evidence and saves. The finish uses direct native glyph edits, with no
repacking. `source/native-edit-lock.json` on B1F blocks replay of the packer or
pixel-preparation generator over the final native artwork.

To reproduce the current small repair, use an **isolated, unchanged engine checkout
at ab04d9792ea5c36233a3ef2ff0c410b46b6658b6** and this hub branch:

```sh
python3 tools/gba/maps/union_cave/fix_b1f_junction.py /path/to/isolated-engine
make -C /path/to/isolated-engine -j8
python3 tools/gba/maps/union_cave/runtime_all.py /path/to/isolated-engine /new/runtime-output --toolchain /path/to/arm-toolchain
```

The patch verifies exact source identity, clean ownership fingerprints and unique
uses of both glyphs. Its output was reproduced in an isolated baseline worktree
and matches all 117 final native files (palette line endings normalized).
`previous-ab04d979/` preserves the prior editable B1F source. Earlier de6922a and
6abf snapshots remain. The packed ab04d979 baseline's separate provenance is
[pinned here](https://github.com/Davisfox5/pokemon-apocrypha/blob/c30f2a3beafd583b6c2458ca3e9cc238fa21afe7/gba/art/union-cave-1f/README.md).

`refine.py ENGINE FLOOR --check-only` checks owned source without writing. Keep
native finish edits authoritative; do not run historical trace/register/build
scripts on the final project. `basement_finish_review.py` generates fresh corner
sheets and controlled headless camera views without editing the engine, followed
by an ordinary save/cold reload/Continue. Existing build/proof source and ROM
identities remain recorded. No ROMs, saves or tool binaries are committed.
