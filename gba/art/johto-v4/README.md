# Cherrygrove: HGSS exterior reconstruction

Owner request, 2026-09-14: stress-test world production by bringing Cherrygrove
as close as practical to its Johto appearance, with a clean, functioning exterior
and a moving cast from the five playable regions.

[Playable preview and matching save](../../../tools/vendor/gba/Cherrygrove-HGSS-preview.zip)
 · [In-game walking tour](evidence/walking-tour.gif)
 · [Native screenshots](evidence/in-game-tour.png)
 · [Full native-tile map](evidence/town-overview.png)

Extract the ROM and save together, keep their matching filenames, and choose
**Continue**. The player starts on the residential lane at (39,16). D-pad moves,
A talks/enters interactions, B closes text, and Start opens the ordinary menu.
This package has its own preview save; keep previous preview saves with their
respective ROMs because exterior coordinates have changed.

## What changed

The reference is [HeartGold/SoulSilver Cherrygrove City](https://archives.bulbagarden.net/wiki/File:Cherrygrove_City_HGSS.png),
with the original three houses, Mart, Center, western bay, rocky offshore islands,
small sandbar, northern cliff, northeast pond and southern flower gardens.
The fourth exterior house, invented park, docks and boats from earlier proposals
are removed from this reconstruction. The dormant fourth-house interior and warp
index remain reserved; no existing map IDs or other warp indices were renumbered.

Buildings use masked native pixels from the reference. Grass, paths, sand,
flowers, fences, water, rocks, cliff faces and single-crown trees use the local
HGSS area-2 textures. This replaces the previous generated building proposal for
this requested closer-copy comparison; its assets and playable builds remain
available. This is a GBA tile adaptation, not a pixel-identical recreation of the
DS 3D renderer. Building silhouettes, beach curves and terrain are fitted to
16-pixel movement cells, with extra forest at map boundaries. Interiors remain
the working rooms from the earlier town preview.

Every placed object is composed over the actual scenery beneath it. Native GBA
layers put canopies in front and walkable surfaces behind characters. The sea
has a 32-phase scrolling texture loop in sixteen dedicated tiles. Five exterior
doors have native three-frame animations derived from their own facade pixels;
the last sixteen hardware tiles remain reserved for door animation.

Twelve residents walk around the town: custom Gold, Silver and Kestra; Hoenn,
Kanto, Johto, Sinnoh and Unova visitors; and four Johto citizens. The approved
smaller custom/regional artwork is unchanged from the scale preview. The earlier
citizens retain their existing art. Visitor labels are replaced with short
regional travel remarks, explicitly preview flavor rather than new story canon.
Gold/Silver/Kestra retain their temporary name-only dialogue and established roles.

## Sources and editing

- [Texture provenance](provenance.json): read-only `a/0/4/4`, member 2, with explicit
  palette aliases. Original designs/art belong to Game Freak / Nintendo / Creatures.
- Reference image: `gba/art/johto-v1/references/cherrygrove-hgss.png`.
- Transparent, editable building cutouts: `prepared/*.png` and `*.aseprite`.
- [Geometry and building anchors](layout.json), [walking routes](residents.json).
- Character provenance and frame preparation remain in
  [regional-scale-v1](../regional-scale-v1/README.md) and
  [johto-npc-v1](../johto-npc-v1/README.md).

The map compiler converts source textures into indexed RGB555 palettes and
8×8 tiles, deduplicates flipped tiles, and shares invisible background pixels
only where foreground pixels cover them. It does not blur or approximate terrain
grain. When three palette families meet in one tile, it fits that seam to two
banks; the measured average RGB-channel difference from the authored composite
is recorded in [integration.json](evidence/integration.json).

## Verification

The compiled ROM was run through mGBA 0.10.5. See
[runtime-results.json](evidence/runtime-results.json),
[movement.json](evidence/movement.json), [water.json](evidence/water.json), and
[structure.json](evidence/structure.json).

- Five entrances and exits, bedroom stairs, Route 29 and Route 30 crossings and
  returns, beach collision, shop interaction, save, fresh-process reload and
  ordinary title-menu Continue pass.
- 7,200 engine frames across five camera positions verify all twelve residents'
  routes, collision, directional artwork in actual OBJ VRAM, and distinct active
  palettes. Eight custom/regional conversations verify stop, face-player south
  idle pixels and resumed walking.
- A separate 512-frame test sees all 32 sea phases while static tile memory stays
  unchanged. Native screenshots, door sequences and movement captures were
  visually inspected. Final captures use a fixed midday emulator clock; normal
  game time-of-day tinting remains active.
- 789 static/reserved-sea tiles of 1,008 available before door space; 327 native
  metatiles of 1,024 available. The ROM is padded to 32 MiB as before. Exact
  linked size, build hashes and package readback are in [build.json](evidence/build.json).
- Regeneration produces an identical engine patch; forward and reverse patch
  checks pass. No production `game/`, donor archive or prior preview was replaced.

This is the completed exterior production/visual-review pass, with the existing
preview interiors and route stubs. It is not a completed regional campaign,
Surf encounter design, or story placement approval. Those are separate work.

## Reproduce or continue

Start from town baseline `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e` in a separate
checkout, and apply these root patches in order:

1. `gba/johto-art-v3.patch`
2. `gba/johto-npc-v1.patch`
3. `gba/johto-cast-v1.patch`
4. `gba/regional-scale-v1.patch`
5. [gba/johto-v4.patch](../../johto-v4.patch)

All engine assets, including raw water and door frames, are in the patches. ROMs,
saves, tool binaries and build caches stay under ignored `tools/vendor/gba/`.
The current isolated checkout is `tools/vendor/gba/johto-v4-game`.

To regenerate source above the first four patches, use the preserved `sources/`
textures, run `tools/artwork_library/prepare_johto_v4.lua` in Aseprite with
`--script-param root="$PWD"`, then:

```sh
python3 tools/gba/maps/compile_johto_v4.py tools/vendor/gba/johto-v4-game
python3 tools/gba/maps/integrate_johto_v4.py
python3 tools/gba/maps/compile_johto_doors.py
python3 tools/gba/maps/validate_johto_v4.py
gmake -C tools/vendor/gba/johto-v4-game -j8 \
  TOOLCHAIN="$PWD/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi"
```

The texture extractor is optional: `tools/gba/maps/extract_johto_terrain.py`
recreates the preserved PNGs from the local donor. Production work should not
need to re-open DS archives merely to use these prepared sources.

Runtime commands:

```sh
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/johto-v4-game \
  tools/vendor/gba/johto-v4-fresh-run \
  --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi \
  --runtime-source tools/gba/maps/johto_v4_runtime.c
python3 tools/gba/maps/check_johto_v4_movement.py
python3 tools/gba/maps/preserve_johto_v4.py
```

Use a new output directory for the save/Continue harness. The water probe is
`tools/gba/maps/johto_v4_water_runtime.c`, using the same local mGBA compile flags
and the movement harness's symbols file. The source compiler intentionally
asserts the isolated checkout path to protect production and prior previews.
