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
| Overworld sprites | HGSS | `TODO(verify)` |
| Overworld sprites | Platinum | `TODO(verify)` |
| Map models / textures | both | inserted via editor tools (DSPRE / SDSME / PDSMS), not hand-repacked here |

## Format budgets by asset class

### Trainer battle sprites (front)
- **80x80** pixels, exactly.
- 4bpp indexed: **max 16 colors including transparent index 0**.
- All graphics dimensions must be a multiple of 8 (hardware tile size).

### Trainer battle backsprites
- Multi-frame **animated sheets, ~5 frames** of 80x80 (HGSS plays the
  throw animation from these).
- Same 4bpp / 16-color / index-0-transparent budget.

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
- Sprite insertion order of operations: validated indexed PNG →
  DSPRE/Tinke converts to the Nitro format and repacks the NARC → NARC
  dropped back under the build's `files/` tree → rebuild
  (`_omni_native_build.sh` packs `files/` as-is; see ART_ASSETS_SPEC.md §0).
- When replacing a Platinum front sprite, re-insert the mugshot (or at
  least re-check it) — they share the palette entry you just changed.
