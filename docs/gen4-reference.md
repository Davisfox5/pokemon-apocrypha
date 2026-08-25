# Gen 4 asset reference (Platinum / HGSS)

Format budgets, NARC paths, and the tool chain for custom art in this hack.
This is the lookup sheet — the workflow itself is in the root
[README.md](../README.md), and the per-scene art wishlist is in
[ART_ASSETS_SPEC.md](ART_ASSETS_SPEC.md).

**Rule for this file:** no invented paths. Anything not verified is marked
`TODO(verify)` — fill it in from the actual NARC before relying on it.

## NARC paths

| Asset | Game | Path |
|---|---|---|
| Trainer battle front sprites | Platinum | `/poketool/trgra/trfgra` |
| Trainer battle front sprites | HGSS | `/a/0/5/8` |
| Trainer battle backsprites | HGSS | `/a/0/0/6` |
| Trainer battle backsprites | Platinum | `TODO(verify)` |
| VS mugshots | Platinum | `TODO(verify)` — but the **palette** comes from `/poketool/trgra/trfgra`, see below |
| Overworld sprites | HGSS | `/data/mmodel/mmodel.narc` (decomp: `files/data/mmodel/mmodel/mmodel_%08d.bin`, packed by index) |
| Overworld sprites | Platinum | `TODO(verify)` |
| Map models / textures | both | inserted via editor tools (DSPRE / SDSME / PDSMS), not hand-repacked here |

## Format budgets by asset class

### Trainer battle sprites (front)
- **80x80** pixels per frame, 4bpp indexed: **max 16 colors including
  transparent index 0**.
- All graphics dimensions must be a multiple of 8 (hardware tile size).
- Verified in HGSS `a/0/5/8` (129 classes): 97 classes are a single static
  frame; 23 classes (gym leaders etc.) have 3 frames; a handful (Red,
  rival, E4) have 4-12. Frame count is fixed by the class's cell data —
  match it when replacing.

### Trainer battle backsprites
- Multi-frame **animated strips of 80x80 frames** (the throw animation).
  Verified in HGSS `a/0/0/6` (17 classes): **12 classes have 8 frames,
  5 have 5 frames** — not "~5"; match the target class exactly.
- Same 4bpp / 16-color / index-0-transparent budget.

### HGSS trainer sprite NARC internals (verified against nitrogfx + vanilla data)
Each class = **5 consecutive NARC members**:
`NCGR` (tiles) / `NCLR` (palette) / `NCER` (cells) / `NANR` (anim timing) /
`NCGR` aux (200 tiles = 2 extra VRAM-streamed animation frames).
- Tile data is **plain tiled 4bpp — NOT scanned/encrypted** (the Gen 4
  PRNG scrambling applies elsewhere, e.g. DP Pokémon sprites; nitrogfx's
  scanned flag `charHeader[0x14]` is 0 here).
- NCGR pixel data at chunk+0x20, byte size at chunk+0x18. NCLR color data
  at chunk+0x18, byte size at chunk+0x10. (Offsets from nitrogfx
  `ReadNtrImage` / `ReadNtrPalette` — the naive "dataOffset field" read is
  8 bytes off and was the source of subtle corruption.)
- One NCER cell bank per animation frame, 6 OAM pieces each, char-name
  shift 1, and per-frame **char partitions** of 3200 bytes (= one 80x80
  frame). Animation banks shift their bounding box (the backsprite throw
  slides right) — compose/decompose must anchor to each bank's own
  minX/minY.
- OAM priority: lowest-index OAM wins on overlap (front class 102 has
  overlapping pieces; it round-trips render-identical, not byte-identical).

**Slot assignments (this hack):** class 23 (RIVAL) now carries **Kestra**
(all live class-23 trainer entries are her repurposed rival battles;
source art `assets/src/trainers/front/kestra_front*.png`). Silver's
late-game Champion battle (Ch8, spec-only) must NOT use class 23 — assign
him a different class when Ch8 is built.

**Scripted insertion (no DSPRE needed for these):**
`scripts/extract_trainer.py` decodes any class to a PNG frame strip;
`scripts/insert_trainer.py` splices a validated strip back in (tiles +
palette; cells/timing untouched). Round-trip is byte-identical for 145 of
146 vanilla classes (render-identical for all 146). All vanilla sprites are
pre-extracted in `artwork-library/heartgold-johto/trainers/battle-front/`
(named by class) and `battle-back/`.

### Platinum VS mugshot palette trap
The VS mugshot does **not** take its palette from `field_encountereffect` —
it pulls the palette from the front-sprite NARC (`/poketool/trgra/trfgra`).
**Front sprite and mugshot must be indexed against one shared 16-color
palette** or one of them will render wrong in-game. That is what
`scripts/shared_palette.py` is for.

### Overworld sprites
- **32x32 per frame**, sheets of directional walk cycles.
- **Max 15 non-transparent colors** (+ transparent index 0).
- Slice/assemble sheets with `scripts/sheet.py` (row-major grid).

### HGSS overworld NPC internals (verified against vanilla mmodel members)
- Overworlds are **billboarded textures**: one BTX0 (NSBTX) file per model
  in `files/data/mmodel/mmodel/mmodel_%08d.bin`; `mmodel.mk` repacks the
  directory into `mmodel.narc` by filename order, so appending
  `mmodel_00000864.bin` (vanilla ends at 863) adds a model.
- NPC walkers: **16 texture dict entries sharing 12 unique 512-byte
  32x32 4bpp frames** + one 16-color palette (color 0 transparent). The
  TEX0 header offsets at +0x0E/+0x34 point directly at NNS resource dicts.
- Three ID spaces: event JSONs use `SPRITE_*` (`constants/sprites.h`),
  mapped to `MMODEL_*` (= NARC index, `constants/mmodel.h`) by the table
  in `asm/overlay_01_sprite_data.s` (ends at a `0xFFFF` sentinel — append
  rows before it; copy the donor's third param, `0x000 | (0 << 10)` for
  GS-style walkers).
- Scripted extract/insert: `scripts/extract_ow.py` / `scripts/insert_ow.py`
  (round-trip byte-identical on vanilla members). Strips hold the unique
  frames in ascending data-offset order.

**Slot assignments (this hack):** `MMODEL_KESTRA` = 864 /
`SPRITE_KESTRA` = 1051 — Kestra's overworld (GIRL2 base, palette+pixel
edit matching battle sprite v11). All 8 of her placements (T22 x3, T23,
R30 x2, T25, D15R0102) point at it; vanilla GSGIRL2 NPCs are untouched.

### Map assets
- Houses, trees, props are **3D geometry (`.nsbmd`)**, not sprites.
- Textures are **`.nsbtx`**: power-of-two dimensions, typically **32x32 or
  64x64**, palettized (`scripts/texture_prep.py` makes a PNG legal first).
- Keep buildings **under ~100 triangles**.

## Tool chain

| Stage | Tool | Runs on macOS? |
|---|---|---|
| Downscale / palette / validate PNGs | `scripts/*.py` (Pillow) | yes — native |
| Author map geometry + .nsbtx | Pokémon DS Map Studio (PDSMS) | yes — Java 8+ (`tools/launch_pdsms.sh`) |
| Insert trainer sprites, edit headers/events | DSPRE | wine/GPTK only (`tools/launch_dspre.sh`, prefix `~/.wine_dspre`) |
| Alternative map/NARC editor | SDSME | wine only (Windows .NET) |
| NARC unpack/repack, format preview | Tinke | wine/mono |
| NCLR/NCGR/NSCR/NCER pixel work | NitroPaint | wine |
| Inspect existing NSBMD/NSBTX | apicula | yes — native CLI |
| Test in emulator | melonDS (DS), DeSmuME (this repo's `tools/play.py` harness) | yes |

mGBA is GBA-only — useful for viewing Gen 3 source material, not for DS
testing.

Third-party binaries live in `~/toolchains/` (what the launch scripts
expect) or `tools/vendor/` (gitignored) — see
[tools/vendor/README.md](../tools/vendor/README.md).

## Insertion notes

- ROMs are never stored in this repo; `.gitignore` and the pre-commit hook
  both block `*.nds`/`*.gba`/`*.sav`/`*.srm`.
- HGSS trainer battle sprite insertion is fully scripted:
  `insert_trainer.py` writes straight into `disasm/pokeheartgold/files/a/0/5/8`
  (or `a/0/0/6`) → rebuild (`_omni_native_build.sh` packs `files/` as-is).
- Other asset kinds (overworld sprites, tiles, models) still go through
  GUI tools: DSPRE/Tinke convert + repack the NARC → NARC dropped back
  under `files/` → rebuild (see ART_ASSETS_SPEC.md §0).
- When replacing a Platinum front sprite, re-insert the mugshot (or at
  least re-check it) — they share the palette entry you just changed.
