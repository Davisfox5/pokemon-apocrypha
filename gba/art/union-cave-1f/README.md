# Union Cave — original textures, embedded stairs and local join review

Current engine **`fc1017fecad147879de460fcb9727ff63862598b`**, branch `codex/union-cave-1f`,
[draft source PR #9](https://github.com/Davisfox5/pokeemerald-expansion/pull/9).
[B1F review](../union-cave-b1f/README.md) · [B2F review](../union-cave-b2f/README.md).

## Current visual review

- [HGSS / previous / corrected stair and cap details](evidence/stairs-cap-reference-comparison.png)
- [Whole original / native 1F](evidence/comparison.png), [native gameplay](evidence/gameplay-gallery.png)
- [Every wall-containing native cell](evidence/wall-cell-review.png)
- [Southern entrance before/after](evidence/south-entrance-before-after.png)
- Floor panels: [north](evidence/material-comparison-1.png), [middle](evidence/material-comparison-2.png), [south](evidence/material-comparison-3.png)
- Preserved earlier styles: [988e0287](evidence/previous-988e0287/native-map.png), [de6922a](evidence/previous-de6922a/native-map.png)

## Owner-directed corrections

The earlier separate floor stair squares duplicated stairs already embedded in
the original rock walls. **All eight extra floor markers are removed**, with
ordinary ground restored. The six wired entries now sit on the actual visible
stairwells; approach direction, return travel and adjacent blocked walls are
verified. No separate square marker substitutes for a stair.

| Actual native stair entry | Paired destination |
| --- | --- |
| 1F north `(4,5)` | B1F main `(32,35)` |
| 1F southern pocket `(8,57)` | B1F lower west `(3,48)` |
| B1F lower east `(30,46)` | B2F northwest `(3,5)` |

Map/layout IDs and paired warp indices/destinations remain stable. Six former
wall cells become the correct stair entrances; collision/elevation is unchanged
everywhere else. The two additional B1F embedded stairwells remain unwired and
blocked until their original destinations are built. Route32's two external door
cells and south-arrow return stay unchanged; Route33 exterior remains unwired.

The owner preferred the earlier textured HGSS wall/cap treatment over the later
broad simplified bands. The original textured native appearance is restored from
`de6922a`; its 14-shade wall ramp and ground/water detail are retained. Mixed
floor/water boundaries share the original wall shades through available native
palette banks 6–9. Local original-HGSS upper-tread and cap joins use bank10, with
24×16 reference patches covering the complete head of each stair entrance.
This keeps source texture and depth instead of flattening the rock cap.

The accepted southern light/rim arrangement and the small B1F actor-removal repair
are retained. The latter removes 29 stray native pixels in a corner where a raw
donor had overlapped the original trainer. Source donors are now checked across
their full bounds for remaining clothing, skin and black outlines. Original
foreground rock silhouettes/shadows remain complete; background ground and root
collision stay separate.

## Evidence and checks

- Local ROM build passed; actual Porymap 6.3.1 exports equal native decoding on
  every pixel of all three floors. No desktop game was opened.
- 5,792 native cells checked for collision/elevation, behaviors, opaque backgrounds,
  layer indices and tile budget. Only the six documented stair-entry collision
  cells change. [Physics scope](evidence/physics-preservation.json).
- Actual indexed wall/cap texture patterns outside explicit local edits are
  identical to the earlier native baseline. Shared ramps change colors at mixed
  boundaries while keeping texture. [All-floor audit](evidence/all-floors-audit.json),
  [wall review](evidence/wall-review.json).
- Porytiles round-trips 128 representative layered metatiles per floor with zero
  RGB/alpha errors. Static glyphs remain below 1008; palette banks stay within
  the GBA's supported 0–12 field range.
- **420 native observations** cover Route32, all three real stair pairs both ways,
  blocked outer walls, blocked unwired stairs, Surf/disembark, southern threshold
  and separate ordinary 128KiB save/cold reload/title Continue on every floor.
  [Exact source/ROM and phase results](evidence/all-floors-build.json).
- Focused review covers 20 corner/join regions and 2,109 basement wall cells,
  plus 18 fresh controlled camera positions. Camera placement is separate from
  traversal proof. Source/native sheets and gameplay are linked in each floor README.
- Reproduction in a clean preserved baseline matches all 126 owned source files,
  with palette line endings normalized. [Reproduction](evidence/reproducibility.json).
  Shared art, other maps, original saves and prior workbenches are preserved.

The original overviews are foreshortened/cropped DS scenes registered to native
16×16 squares; this is not decoded DS collision or a pixel-exact RGB import.
Original HGSS references/events and deliberate adaptations remain recorded under
`source/`. Native interior texture reuse and palette reduction remain explicit.
Visual acceptance remains with the owner; compilation/traversal success is separate.

## Editable source and reproducible provenance

Current native layouts, metatiles, glyphs, palettes and map.json are authoritative.
Edit them through the installed Porymap/native workflow. Preserve owner edits and
IDs. Existing generators are provenance and must not be replayed over committed
owner layouts. Native-edit locks block the historical packers.

The latest restoration was reproduced in an **isolated exact 988e0287 engine**,
with a second read-only checkout of **de6922a** as the earlier appearance reference:

```sh
python3 tools/gba/maps/union_cave/restore_reference_finish.py /isolated/engine /readonly/de6922a
python3 tools/gba/maps/union_cave/blend_reference_caps.py /isolated/engine
python3 tools/gba/maps/union_cave/patch_embedded_stair_heads.py /isolated/engine
make -C /isolated/engine -j1 generated
make -C /isolated/engine -j8
```

These guarded steps preserve paired warp IDs, use exact flip deduplication to free
local glyph slots without altering pixels, restore ground beneath removed markers,
and author only the actual stair/cap joins. They are isolated reproduction tools.
`previous-988e0287/`, `previous-ab04d979/` on B1F and older snapshots retain prior
source/evidence. `native-tile-snapshot.json` records final glyph data as a snapshot,
not a scene-repacking dictionary. `review_all.py` compares actual native output
and Porymap; `runtime_all.py` exercises walking/stairs/Surf/saves;
`basement_finish_review.py` supplies focused source/native views and fresh framing.

Source artwork: Nintendo / Game Freak / Creatures; original overviews hosted by
Bulbagarden Archives; original texture rip by Kuramapika1 via The Models Resource;
event data from pret/pokeheartgold. No ROMs, player saves or tool binaries committed.

## Concrete remaining scope

Route33 exterior and additional unpictured transit destinations remain unbuilt.
Two represented B1F stairwells remain unwired/blocked. Strength pushing, animated
water, campaign actors/items/encounters/Lapras and Surf badge/party activation are
pending. Proof Surf setup uses the existing engine state; it does not grant an HM
or claim campaign unlock coverage. Existing original terrain barriers remain.
