# M3 — Hoenn map conversion (Gen 3 → Gen 4 DS formats)

Status: **pipeline built and verified at the data level**; first full conversion
of the Hoenn overworld is generated and committed under `converted/hoenn/`.
Tooling lives in `tools/hoennconv/`. Everything here runs without the
proprietary toolchain (this is [source]-tier work per the M-roadmap).

## Continuity note — prior session's work was unrecoverable

Earlier sessions committed map work *inside the submodules* and recorded the
pins in this repo (e.g. `disasm/pokeheartgold @ 1256c28`, `disasm/pokeemerald
@ 27bcf06`). Those commits were never pushed to any remote this environment
can reach — `pret/pokeheartgold` rejects the pins (`not our ref`) and no
accessible fork carries them — so every "(submodule)" commit in this repo's
history references history that only existed in expired session containers.
The Hoenn conversion work from the previous conversation is therefore lost to
this environment and has been **rebuilt from scratch, entirely inside this
repo**, so it cannot be lost the same way again.

**Action for the design owner:** if a local clone still has those submodule
commits, push them to forks and repoint `.gitmodules`; ALL prior in-submodule
story/chapter work (Ch1–Ch4 scripts, scenes) is otherwise dangling. Until
then, work here targets upstream pins: `pokeheartgold b843c93` (the pin
ENGINEERING.md verified against), `pokeemerald 83df84e` (master at time of
writing).

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
