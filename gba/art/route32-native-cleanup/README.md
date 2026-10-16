# Route 32 — native visual cleanup

Engine branch `claude/route32-native-cleanup` on `Davisfox5/pokeemerald-expansion`, commit
**`48cefd3da180d21329a346407c9be4d0339fa3a0`**, built on Codex's Route 32 reconstruction
`7049fd5d8b95b3f357056ff53b8b2b3a3e848d74` ([PR #8](https://github.com/Davisfox5/pokeemerald-expansion/pull/8),
[its review](../route32-hgss-blocks/README.md)). This applies the
[required native visual cleanup](../../../docs/GBA_MAP_RECONSTRUCTION.md#native-visual-cleanup-and-final-review)
demonstrated on Union Cave (`fc1017fe`) to the outdoor map: close-up review of every square
against the HGSS reference, local repairs only, original textures and the accepted Cherrygrove
art preserved. Visual acceptance remains with the owner.

## Review sheets

- [Whole map: original / before / after](evidence/whole-map-original-before-after.png)
- 16-row strips at 2x, coordinate-labelled: [0–15](evidence/strip-000.png), [16–31](evidence/strip-016.png),
  [32–47](evidence/strip-032.png), [48–63](evidence/strip-048.png), [64–79](evidence/strip-064.png),
  [80–95](evidence/strip-080.png), [96–111](evidence/strip-096.png), [112–127](evidence/strip-112.png)
- Repairs, original / before / after at 5–6x: [gate shadow](evidence/detail-gate-shadow.png),
  [cave mouth](evidence/detail-cave-mouth.png), [rock column end](evidence/detail-rock-column-end.png),
  [north-south stairs](evidence/detail-north-south-stairs.png), [pier / fishing-arm junction](evidence/detail-pier-arm-junction.png),
  [upper dock](evidence/detail-upper-dock.png), [lower pier](evidence/detail-lower-pier.png),
  [west coast pillar](evidence/detail-west-pillar.png), [Magnet Train pylon](evidence/detail-pylon.png),
  [railway posts](evidence/detail-railway-posts.png), [flowers](evidence/detail-flowers.png)
- [Native gameplay frames](evidence/gameplay/) from the headless tour (see Validation), including
  `pylon-close`, `pylon-base`, `west-pillar-close`, `railway-posts-underpass`, `ns-stairs-lower-tread`,
  `rock-column-end`, `pier-arm-junction`, `flowers-and-gate`
- [Actual Porymap 6.3.1 export](evidence/porymap-export-JohtoRoute32.png) and [parity record](evidence/porymap.json)
- [Every changed cell, collision/elevation changes](evidence/cell-diff.json), [edit log with every glyph, metatile and cell](source/edit-log.json)

## Method

All 128 rows were compared with the HGSS overview registered at 16 px squares (native = source + 1,1,
the registration Codex recorded) in labelled strips, then the suspect areas at 4–10x, then the
decoded native glyphs themselves. Material/structure was judged separately from walkability. The
macro layout, material classes, tree footprints, Cherrygrove ground/tree/rock art, the accepted
Emerald placeholder stairs, the shared Violet Center and the wider-Center adaptation were found
sound and left alone. The defects were all local, and every repair is a scripted edit of the
committed source that Porymap could make by hand (`tools/gba/maps/route32_native_cleanup/cleanup.py`,
refusing to run on anything but the recorded `7049fd5d` baseline). No generator was replayed.

## Defects found and repaired

| Where (native cells) | Finding | Repair |
| --- | --- | --- |
| Gate shadow row 12, x=2/4/6 | Black HGSS trunk arcs baked into the gate-shadow glyphs; HGSS has none under the gate | 22 arc pixels cleared; the pillar outline column is kept |
| Cave mouth (13,117) | Three isolated cream pixels in the left jamb face | Cleaned to the surrounding face shade |
| Rock column end (24,64) | Lawn glyph sat under the rounded rock end in open water (green corner) | Water glyph beneath the rock corner |
| North-south stairs (6–8,89) | Flight was two tread rows plus a bare sand square, reading as a leftover marker | Third tread row; (9,89) becomes a plain face so the right wall continues |
| Long pier (17–19,73–76) | Planks turned horizontal through the fishing-arm junction | Vertical grain continues; the arm keeps horizontal grain, as in HGSS |
| West coast pillar (10,70–77) | Face alternated between rounded lobes and recesses; HGSS is one straight wall | Continuous right-facing wall; the four lobes at (11,70/75/76/77) are water again |
| Dock shores | Lips present only on some deck edges (none along the upper dock, the pier's east side or the arm's top) | 45 water squares carry the lip on exactly their deck/pillar edges; existing lips elsewhere untouched; one right+bottom corner piece mirrored from the left+bottom piece |
| Magnet Train pylon (24–25,70–75) | Flat two-tone teal rectangle with a gray slab, standing on surfable water | Redrawn from the HGSS pixels: shaft, collar, orange band, base and foam ring; rows 70–74 blocked, row 75 surfable with the foam on the covered layer |
| Railway x=8 and x=16 | HGSS bridge support posts missing | Posts added to the top layer of the four rail rows; underpass walking unchanged |
| Lawn (15–18,6), (15–16,7), (14,8) | HGSS flower clusters missing | Petals quantised to the Center bank on the covered layer over the existing lawn |

Palette work: the pylon shaft uses the railway bank (teal/gray ramp), its band row the Center bank
(orange, gray, white), chosen per 8×8 quadrant by lowest colour error; nothing else changed bank.
Budget: 62 previously unreferenced static glyph slots and 28 blank primary catalogue entries were
used; 27 static glyphs and 357 primary metatile entries remain free. No existing glyph or metatile
was renumbered or recycled, so Codex's grid and material audits still address the same IDs.

## Traversal

92 layout cells change. Collision/elevation changes are exactly 12 and are listed in
[cell-diff.json](evidence/cell-diff.json): the ten pylon-body squares (24–25,70–74) are blocked like
the original structure (they were surfable water carrying the pylon art), and the four former rock
lobes (11,70/75/76/77) are surfable water as in HGSS. No land traversal, warp, door, ledge, stair or
connection changes. Map, layout, tileset and warp IDs are unchanged.

## Validation

- Local ROM build passed: `pokeemerald.gba` sha256
  `a43d277aba7b3c17b3a539473442d5e39649ba2fa11d06ae1094c0f338ffe2f4` (commit `48cefd3d`).
- Actual Porymap 6.3.1 (built from source, Qt 6) project-core export of `JohtoRoute32` equals the
  decoded native layout on every pixel; `Route32PokemonCenter` and `UnionCaveRoute32Entrance` export
  unchanged.
- Headless mGBA (libmgba 0.10.2) runs Codex's Route 32 tour unchanged plus eight close-up frames:
  both ground branches, both railway underpasses, both stair flights in both directions, the restored
  floor below the cave boulder, fixed HGSS forest/stair/boulder barriers, one-way ledges, grass steps,
  Center entry/return, both cave entrance cells, and
  ordinary 128 KiB flash save, cold reload and title-screen Continue: 270 write-phase
  observations plus the read and menu phases, all passing ([results](evidence/gameplay/results.json)). No owner save is read or modified.
- The eight close-up frames place the camera with the tour's teleport helper (two stand on water); they
  show rendering, not traversal. Traversal proof is the walked tour itself.
- Source hashes after the edit are recorded in [edit-log.json](source/edit-log.json); the baseline
  hashes in [baseline-hashes.json](source/baseline-hashes.json).

## Reproduction

```sh
git clone --branch claude/route32-native-cleanup https://github.com/Davisfox5/pokeemerald-expansion.git engine
# or, from the 7049fd5d baseline:
python3 tools/gba/maps/route32_native_cleanup/cleanup.py /path/to/engine
python3 tools/gba/maps/route32_native_cleanup/review.py /path/to/engine        # sheets + cell-diff
make -C /path/to/engine -j4 tools && make -C /path/to/engine -j1 generated && make -C /path/to/engine -j4
python3 tools/gba/maps/route32_native_cleanup/runtime.py /path/to/engine OUT --toolchain /usr
python3 tools/gba/maps/route32_native_cleanup/porymap_check.py /path/to/engine /path/to/porymap-probe EXPORT
```

`porymap_probe.cpp` is Codex's headless export harness, linked against a Porymap 6.3.1 source build.
Original art: Nintendo / Game Freak / Creatures; HGSS overview via Bulbagarden Archives (the copy in
`../route32-hgss-blocks/source/hgss-reference.png`). No ROMs, saves or tool binaries are committed.

## Findings left as they are (owner decision)

- **Thin ridge at (24,23–27).** HGSS shows a narrow raised strip separating the lawn at x=21–23 from
  the pocket at x=25–27 (see [strip 16–31](evidence/strip-016.png)). Codex's reviewed cell grid treats
  those squares as open lawn and the native map has no barrier there. Restoring it would change land
  traversal (a detour through the tall grass), so it is reported, not changed.
- **Route sign at (15,8).** HGSS places the sign post one square further east (16,8–9). Moving it
  would move a blocked square; left in place.
- **Shore lips elsewhere.** Only deck and pillar shores were re-lipped. Rock-faced and tall-grass
  shores keep Codex's treatment (some have lips built into the rock pieces, some have none); a
  consistent HGSS-style lip along every bank would be a separate, map-wide pass.
- **Cave forecourt registration.** The forecourt, its ledges and the cave mouth sit one square east
  of the registered overview; Codex documented the portal move as a deliberate adaptation and the
  foot grid was audited against it, so it is left.
- **Emerald placeholder stairs** (both flights) and the Center-forecourt sign remain the approved
  placeholders. The east-west flight's small rock stumps at (9,61) and (10,62) read as rock; HGSS
  has a straight narrow face there.
- The pylon body is now blocked and the pillar lobes are water. Both match HGSS, both are
  Surf-only cells, and both are listed above as the only traversal changes in case the owner prefers
  Codex's values.

Violet City, the Alph destination and the full Union Cave remain external wiring, as before.
