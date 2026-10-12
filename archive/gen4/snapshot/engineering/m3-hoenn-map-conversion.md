# M3 — Hoenn map conversion (Gen 3 → Gen 4 DS formats)

Status: **pipeline built and verified at the data level**; first full conversion
of the Hoenn overworld is generated and committed under `converted/hoenn/`.
Tooling lives in `tools/hoennconv/`. Everything here runs without the
proprietary toolchain (this is [source]-tier work per the M-roadmap).

## Continuity note — the in-submodule work lives on the owner's machine

Earlier sessions committed map/story work *inside the submodules* and
recorded the pins in this repo (`disasm/pokeheartgold @ 1256c28`,
`disasm/pokeemerald @ 27bcf06`). **Those commits are safe on the owner's
local machine** (confirmed by the owner), but were never pushed to a remote,
so remote sessions cannot fetch them (`pret/pokeheartgold` rejects the pins
with `not our ref`). The owner's local state also includes: the Sinnoh
matrix integrated and navigable from the HGSS base, and a first (still 2-D)
Hoenn integration.

Consequences for remote work: everything authored here must live in **this
repo** (tools + `converted/` artifacts), never as submodule commits; the
recorded pins are respected and left untouched. **Standing ask:** when back
at the machine, push the submodule commits to forks and repoint
`.gitmodules` so remote sessions can see the real integration state. Until
then, remote sessions read the submodules at upstream commits
(`pokeheartgold b843c93`, `pokeemerald` master) — close enough for format
work, blind to local integration.

## What exists now

### Tooling (`tools/hoennconv/`)

| module | job | ground truth |
|---|---|---|
| `narc.py` | NARC archive parse/build | byte-identical round-trip of the whole vanilla 19.5 MB land-data archive |
| `hgss_map.py` | HGSS land-data member (map chunk) parse/serialize | DSPRE `MapFile.cs` layout + byte-identical round-trip of all 676 vanilla members |
| `gba.py` | pokeemerald layouts / tilesets / metatile attributes / map.json; renders any metatile to RGBA | masks from `include/global.fieldmap.h`, tileset constants from `include/fieldmap.h` |
| `behavior_map.py` | Gen-3 `MB_*` behavior + collision bits → Gen-4 (type, collision) bytes | type values verified empirically (below) |
| `stitch.py` | global Hoenn canvas from map.json `connections` (BFS from Littleroot) | reproduces the GBA seam math |
| `events.py` | Gen-3 events → HGSS `zone_event` JSON schema | schema from `files/fielddata/eventdata/zone_event/*.json` |
| `convert.py` | driver: emits everything under `converted/hoenn/` | — |
| `verify.py` | the gate: vanilla round-trips + output integrity + behavior coverage | run after any change; currently **PASS** |

### HGSS formats, pinned down

Land-data member (`a/0/6/5`, one per 32×32-metatile chunk):
`u32 permSize, u32 buildingsSize, u32 modelSize, u32 bdhcSize`, then
HGSS-only BGS section (`u16 0x1234, u16 len, data` — background sound
plates), then 1024 permission cells (`u8 type, u8 collision` each), buildings
(48 B each), NSBMD model (`BMD0`), BDHC height table. The map matrix format
was already pinned in `tools/mapeditor/mapdata.py` (from `src/map_matrix.c`).

Gen-4 type-byte values **verified against vanilla chunks** (rendered Route
29/40/41 and matched the real maps): `0x02` encounter grass, `0x15` open sea
(surfable), `0x21` sand, `0x10` still water, `0x00` plain. Values taken from
community tables but **not yet verified in-game**: ledges `0x38–0x3B`, ice
`0x20`, waterfall `0x13`, door/stair warps `0x69/0x6D`. Collision byte:
`0x00` passable / `0x80` blocked (vanilla also carries low-bit values whose
meaning is undecoded; we don't emit them).

### Generated output (`converted/hoenn/`)

- 49 overworld maps stitched to an 800×383-metatile canvas (Littleroot to
  Ever Grande, visually verified against the real Hoenn layout —
  `preview/overworld.png`).
- **25×12 map matrix** (`matrix/hoenn_overworld.bin`, engine format) with 190
  real chunks + 1 shared void chunk; per-cell header slots point at the
  owning map (slot = index into `manifest.json` `maps[]`).
- **191 land-data chunks** (`land_data/*.bin` + packed `land_data.narc`,
  openable in DSPRE/Tinke): converted movement permissions; empty
  buildings/BGS; model+BDHC are structural donors from the simplest vanilla
  flat chunk until the model stage exists.
- **Zone events** for all 49 maps in HGSS JSON schema, matrix-global
  coordinates: warps (dest kept as Gen-3 map id placeholder), objects
  (sprites mapped to HGSS archetypes, movement mapped to the verified
  stand/wander/pace values), triggers, signs/hidden items. Gen-3 script
  labels ride along in `scriptId` as strings — greppable intent, pending real
  scr_seq authoring.
- 13 composed metatile atlases (`tilesets/*.png`) — texture source material
  for the model stage.
- `manifest.json` — placements, chunk table, proposed `MAP_HOENN_*` header
  names, 140 interior warp targets pending, 399 notes (mostly sprite
  fallbacks to archetypes; also the Verdanturf/Route116 seam, below).

## Known issues / decisions

- **Verdanturf↔Route 116 seam:** vanilla Gen-3 connection offsets are
  globally inconsistent by 2 rows there (the GBA never renders the whole
  world at once so it never mattered). First-placed wins for now; needs a
  2-row nudge decision at integration.
- **Ocean currents (Routes 132–134):** Gen 4 has no current mechanic;
  converted as open sea. Route design implication tracked here.
- **Dive:** dive spots convert as sea; the mechanic itself is M4 territory.
- **Secret bases:** converted as scenery (hack design drops Gen-3 secret
  bases).

## Buildings: why the ground "rises with the roof", and the way out

Field report from the owner's local integration: Hoenn is in-game but 2-D,
and extruding buildings drags the background ground up with the roof.

That happens because in the Gen-3 art the roof-edge tiles *contain* the
ground pixels behind them — the GBA fakes depth by baking grass into the
roof tile. HGSS's architecture never does this: the ground chunk model is
bare terrain, and every building is a **separate NSBMD** (there are 340 of
them in `files/fielddata/build_model/bm_field.narc`) placed by the 48-byte
entries in each chunk. So buildings must not be raised out of the ground
texture; they must be cut out of it and re-added as placed models.

Two useful facts make that mechanical rather than per-pixel art surgery:

1. **The Gen-3 layer split is the building/background separation.** Each
   metatile is two 4-tile planes; roof pixels live in layer B with
   palette-0 transparency, the grass behind them in layer A. Rendering
   layer B alone yields the building art with clean transparent edges — no
   hand-editing of each tile to remove background.
2. **Vanilla models are named and countable.** `bm_field_catalog.json` maps
   every model id to its internal names (`en_pc` = Pokémon Center,
   `en_fs` = mart, `en_gym`, house variants...) and how often vanilla
   places it — the donor list for retexturing.

Tooling added (`tools/hoennconv/buildings.py`, `bm_catalog.py`), artifacts
under `converted/hoenn/buildings/`:

- **111 building footprints** auto-detected across 34 overworld maps
  (door-warp-seeded flood over solid, non-green metatiles; window-capped;
  per-town `review.png` overlays; `overrides.json` accepts
  `{"MAP_X": {"add": [[x,y,w,h]...], "drop": [i...]}}` corrections —
  Lavaridge/Fortree are the known override cases, cliff- and tree-hugging
  towns).
- Per building: `*_full.png` (GBA look), `*_struct.png` (layer B only —
  background-free building art), `*_base.png` (layer A only — what belongs
  in the ground texture under the model).
- `buildings.json`: local + matrix-global footprints per building.
- `bm_field_catalog.json`: the 340 vanilla models with names + placement
  counts.

**Strategy decision (owner review of the Littleroot pilot):** retexturing
vanilla models is DROPPED as the primary path. The palette-swapped donor
walls read as Johto-with-different-colors, not Hoenn — the aesthetic lives
in the art, and no recolor of foreign art matches it. The plan of record is
now **strategy A: the Gen-3 art itself becomes the textures on simple 3-D
geometry** (box + roof prism per building), which is also how vanilla HGSS
buildings work (pixel-art textures on boxes). The `bldg_*_clean.png`
cutouts (background-free, full roof including the walk-behind ridge row)
are the texture sources; `littleroot_mock_topdown.png` shows the target.
The palette-swap tooling (`nsbtx.py`, models 340/341) stays as a fallback
and for future texture edits, but no more donor retextures are planned.

Detection note: Gen-3 walk-behind roof rows (passable, art in layer B) made
the solid-cell flood stop one row short of the roof line everywhere; fixed
by extending footprints upward over draw-over rows, and clean cutouts key
out the surrounding ground's exact colors.

## Reconciliation with tools/regionport (merged from main, 2026-07-11)

The parallel conversation's `tools/regionport/` suite is the **canonical
pipeline**: it is emulator-verified (Sinnoh + Hoenn traversable in the ROM,
Slateport buildings standing in 3-D) and includes a real NSBMD writer.
Where the two toolchains overlap, regionport supersedes hoennconv
(chunk/matrix generation, ground models, building extraction). Still unique
to hoennconv and current: the byte-round-trip verify gate (`verify.py`),
the zone_event JSON conversion for all 49 Hoenn maps, the behavior->type
mapping doc, and `preview_render.py` (added to regionport) — a software
renderer that draws a town with the exact `_fold_model` geometry and
`_mask_art` textures, for previewing without a ROM build.

**Strategy decision (owner, 2026-07-11): SETTLED — fold-billboards for
buildings.** The A/B render comparison (littleroot_A_vs_B.png) confirmed
donor models read as Johto architecture; Hoenn keeps its own art. Donor
Gen-4 models remain in play for non-building objects. See ENGINEERING.md
Region Port Status for the edge fixes that landed with the decision.

## Next steps, in order

1. **Terrain models:** generate real per-chunk NSBMD (flat textured planes
   UV-mapped from the tileset atlases would already boot) + real BDHC heights
   from Gen-3 elevation data. This is the big remaining format job.
2. **Interiors:** 140 warp-target maps (houses, gyms, caves) — same pipeline,
   one single-chunk matrix each.
3. **Integration into the HGSS tree:** append matrix + chunks to the NARCs,
   add `MAP_HOENN_*` headers to `src/data/map_headers.h`/`maps.h`, land the
   zone_event JSONs, assign real header ids (replaces the manifest's slot
   indices).
4. **In-game verification** of the UNVERIFIED type bytes (ledges, ice,
   waterfall, warp panels) — needs the owner's toolchain (build blocker).
5. **Sinnoh (M3 sibling):** pokeplatinum is the same engine generation; its
   map data should port mostly by renumbering, not conversion — separate
   assessment doc when started.
