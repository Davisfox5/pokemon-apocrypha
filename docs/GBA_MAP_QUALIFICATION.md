# Maps beyond Hoenn: engine qualification

Status: **runtime feasibility passed; complete map-production workflow not yet qualified.**
Tested 2026-09-13 against the pinned expansion/1.17.0 source plus the current
Apocrypha mechanics snapshot. Production `game/` was neither edited nor built.

## Owner priority

The owner requires map feasibility beyond Hoenn before campaign development
continues. Story has bones through approximately eight or nine chapters and a
gym leader list exists. Pokémon placement, trainer teams, and the level curve
have not been designed by the owner. Existing battle documents must not be
treated as approval of those decisions.

This task authorizes disposable technical maps only. It does not start full
region production, invent new canon, or reopen the deferred 30-box save design.

## What the working ROM proves

One Emerald ROM contains five appended map groups with Hoenn, Johto, Kanto,
Sinnoh and Unova region identities. They do not replace existing campaign maps.

| Fixture | Group / map | Layout | Result |
| --- | --- | --- | --- |
| Hoenn | 75 / 0 | 24 × 20, Emerald | New-game entry, NPC dialogue and scripted warp pass |
| Johto | 76 / 0 | 24 × 20, Emerald | Movement, solid-tile collision and east connection pass |
| Kanto | 77 / 0 | 24 × 20, native FRLG | Pallet layout and Kanto art render in the Emerald ROM |
| Sinnoh | 78 / 0 | 24 × 20, Emerald | Entry from Johto and return connection pass |
| Unova | 79 / 0 | 80 × 80, Emerald | Large layout loads and runs |

All five maps pass ordinary flash save and cold reload in separate emulator
processes. The check verifies region, group, map, player coordinates, layout
format, dimensions and map section after reload. Ten write/read processes pass
with no emulator error output. Screenshots were inspected for Kanto art,
field/NPC rendering and the loaded large-map fixture.

Hoenn, Johto, Sinnoh and Unova are deliberately plain technical yards using
existing Emerald art. Their names and region tags do **not** constitute recreated
regional geography or finished regional visual styles. Kanto is the concrete
non-Hoenn asset/layout import proof: existing Pallet Town blocks and native
General/Pallet FRLG tilesets, with fresh test events instead of donor story scripts.

- [Kanto rendered in the Emerald ROM](../gba/evidence/maps/kanto-runtime.png)
- [NPC interaction](../gba/evidence/maps/npc-dialogue.png)
- [Unova fixture after cold reload](../gba/evidence/maps/unova-cold-reload.png)
- [Machine-readable results and provenance](../gba/evidence/map-qualification.json)

## Required integration found by the test

The stock map generator filters maps by their region: an Emerald build admits
Hoenn, and a FireRed build admits Kanto. Its layout generation has corresponding
format filters. Adding a new region name alone therefore does not work.

The isolated patch introduces optional `build_target` metadata for maps and
layouts. `build_target: emerald` permits the test maps while preserving the
original behavior when that property is absent. It also includes just two Kanto
tilesets outside their FireRed-only compile gate, adds fixture map sections and
explicit region lookup cases, and installs isolated test entry points.

The existing field runtime already selects primary tile/metatile/palette counts
and metatile attribute format using each layout's `isFrlg` flag. The native Kanto
test exercised that existing support. Kanto tile animation callbacks are disabled
in this fixture; static art rendering is the verified result.

The complete, approximately 30 KB [qualification patch](../gba/map-qualification.patch)
is preserved outside the disposable checkout. **Do not apply it wholesale to
production:** it changes the starting map, skips the truck sequence and includes
debug entry points. Production integration should extract the map-builder and
asset support separately after the remaining workflow checks.

## Measured limits and remaining work

| Area | Evidence and implication |
| --- | --- |
| ROM | Linker reports 19,609,168 bytes of 33,554,432; 13,945,264 bytes remain. This is a small fixture's headroom, not a five-region capacity estimate. |
| RAM | EWRAM 226,736 / 262,144 bytes; IWRAM 28,392 / 32,768 bytes in the proof build. |
| Loaded map size | Engine buffer holds 10,240 cells including connection padding. The 80 × 80 fixture uses `(80 + 15) × (80 + 14) = 8,930` cells. Larger worlds need multiple connected maps. |
| Map IDs | Existing groups are retained; five groups append to the original 75. Save warp fields include signed 8-bit group/map values and negative sentinels. Use conservative 0–127 allocations until a complete ID audit; do not claim 65,536 usable maps. |
| Per-map graphics | Current definitions allow 1,024 tiles, 1,024 metatile entries and 13 map palettes, with different primary/secondary splits for Emerald and FRLG. These are per-loaded-map budgets, not an entire-world tileset budget. |
| Regional navigation UI | `GetRegionForSectionId` and town-map/Fly selection are still largely Hoenn/Kanto-specific. Fixture region cases are implemented; actual Johto/Sinnoh/Unova town-map graphics, location lookup, destinations and travel behavior are not. |
| Regional assets | Johto/Sinnoh/Unova GBA-style art, architecture, animation, interiors and geographic reconstruction remain to be produced and budgeted. DS maps have not been imported or qualified. |
| Editor | Official Porymap 6.3.1 was downloaded and opened the isolated source project. Its initial configuration selected `pokeruby`; correcting and validating configuration was not completed. Do not treat this as an editor round-trip pass. Mixed Emerald/FRLG tile splits and attribute widths must be configured or normalized before editing native Kanto data. |
| Saves | Normal save functions and cold location restoration pass on the current storage architecture. Save-menu button flow, compatibility with older saves after changing IDs, full campaign state and 30 PC boxes are outside this test. |

Relevant inspected source in the pinned checkout: `tools/mapjson/mapjson.cpp`,
`src/fieldmap.c`, `include/fieldmap.h`, `include/regions.h`, `src/region_map.c`,
and the save warp structures. Official editor reference:
[Porymap settings](https://huderlem.github.io/porymap/manual/settings-and-options.html)
and [6.3.1 release](https://github.com/huderlem/porymap/releases/tag/6.3.1).

The next map qualification should validate one representative location in the
intended GBA visual style through source editing, tile import, build, movement,
interior/exit and reload. Settle the editor handling of mixed formats first, then
implement regional town-map/Fly support and estimate the full region asset and
map-ID budget. Team composition and level balancing remain downstream of these
map questions.

## Reproduction and isolation

Evidence records the upstream commit, mechanics diff hash, independent baseline
snapshot commit, ROM/ELF hashes, source hashes and observations. The independent
checkout is `tools/vendor/gba/map-proof-game`; its baseline snapshot commit is
`4a06e98a3c1643b2d491f19a06b80ea07634d548`. This includes the mechanics state at
the start of qualification, which is identified separately from the upstream pin.
ROMs, emulator binaries, flash saves, editor binaries and disposable checkouts
stay under ignored `tools/vendor/`; none are committed artifacts.

To reproduce source preparation from that local baseline, use a new independent
clone (not a linked worktree or production submodule) and run the fixture generator
once. A separately cloned baseline was used to compare generated changes with
the exact tested patch. The generator is intentionally not idempotent.

```sh
git clone --shared tools/vendor/gba/map-proof-game tools/vendor/gba/map-proof-fresh
python3 tools/gba/maps/prepare.py tools/vendor/gba/map-proof-fresh
gmake -C tools/vendor/gba/map-proof-fresh -j8 TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
python3 tools/gba/maps/check_runtime.py tools/vendor/gba/map-proof-fresh tools/vendor/gba/map-proof-fresh-results --toolchain "$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
```

The runtime runner requires the installed Homebrew mGBA library (tested 0.10.5)
and a C compiler. It creates a new output directory and refuses production
`game/`. It invokes test-only engine entry points for setup and normal save/load
functions; directional and A-button input exercise collision, NPC dialogue,
scripted warping and connected-map walking. It uses ordinary 128 KiB flash files,
not emulator save states. It is an instrumented runtime test, not a manual full
playthrough or hardware test.
