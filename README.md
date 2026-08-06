# the-omni-hack

A custom Gen 4 (Nintendo DS) ROM hack targeting Pokémon Platinum and
HeartGold/SoulSilver, with fully custom trainer sprites (battle + overworld)
and custom map assets. This repo holds **source art, conversion scripts, and
validation tooling — never ROMs** (blocked by `.gitignore` *and* a
pre-commit hook).

For the hack's story/design see [DESIGN.md](DESIGN.md) and
[ENGINEERING.md](ENGINEERING.md). This README covers the **asset pipeline**.

## Layout

```
assets/src/            full-resolution source art (tracked)
  trainers/front/      battle front sprites (and Platinum mugshot sources)
  trainers/back/       battle backsprite sheets (~5 frames of 80x80)
  trainers/overworld/  32x32-per-frame walk-cycle sheets
  maps/tiles/          map tile art
  maps/textures/       textures for 3D map models
assets/out/            converted, game-ready output (gitignored; `make build`)
scripts/               Python pipeline (Pillow) + bootstrap + git hooks
tools/                 first-party tooling; third-party binaries in tools/vendor/ (gitignored)
docs/gen4-reference.md NARC paths, format budgets, tool chain
```

## Setup

```sh
make setup        # runs scripts/bootstrap.sh
```

Bootstrap creates `.venv` with Pillow, installs the ROM-blocking pre-commit
hook, and **reports** (never silently installs): Java for Pokémon DS Map
Studio, melonDS/mGBA via Homebrew, and whether a Windows compatibility
layer (wine/Whisky/CrossOver/Parallels) is present for DSPRE/SDSME. It
downloads nothing that requires accepting a license — GUI tools you install
yourself (see [tools/vendor/README.md](tools/vendor/README.md)).

## Workflow

1. **Author** full-resolution art and drop it under `assets/src/...` as PNG.
   Backsprite and overworld **sheets are authored at final pixel size**
   (the pipeline won't guess frame layouts): backs as strips of 80x80
   frames, overworld as grids of 32x32 frames
   (`scripts/sheet.py slice|assemble` helps build them).
2. **Convert**: `make build` — mirrors `assets/src/` into `assets/out/`:
   - fronts → 80x80 nearest-neighbor, 16-color indexed, index 0 transparent
   - backs / overworld / tiles → 16-color indexed, dimensions kept
   - textures → padded to power-of-two, 16-color indexed
3. **Platinum front + VS mugshot** (manual, per trainer): both must share
   one palette because the mugshot pulls its palette from the front-sprite
   NARC (`/poketool/trgra/trfgra`):
   ```sh
   .venv/bin/python scripts/shared_palette.py front.png mugshot.png -o assets/out/trainers/front/
   ```
4. **Check**: `make validate` — per-file report of mode/size/color budgets,
   nonzero exit on any violation. `make clean` wipes `assets/out/`.
5. **Insert**:
   - **HGSS trainer battle sprites — scripted, native.** Check the target
     class's frame count, then splice the validated strip straight into the
     decomp's NARC and rebuild:
     ```sh
     .venv/bin/python scripts/extract_trainer.py disasm/pokeheartgold/files/a/0/5/8 -o ref --cls 12
     .venv/bin/python scripts/insert_trainer.py  disasm/pokeheartgold/files/a/0/5/8 my_sprite.png --cls 12 --in-place
     ```
     Round-trip verified byte-identical against every vanilla class. All
     vanilla sprites are pre-extracted for reference in
     `artwork-library/heartgold-johto/trainers/battle-front|back/`.
   - **Everything else (manual, GUI tools):** DSPRE (via wine —
     `tools/launch_dspre.sh`) or Pokémon DS Map Studio
     (models/`.nsbtx` — `tools/launch_pdsms.sh`), then the NARC goes back
     under the build tree and the ROM is rebuilt. Paths and budgets:
     [docs/gen4-reference.md](docs/gen4-reference.md).
6. **Test** in melonDS, or drive it with this repo's `tools/play.py` /
   `tools/cockpit.py` DeSmuME harness.

### Which steps are manual

| Step | Automated? |
|---|---|
| Resize/quantize/palette/validate PNGs | yes — `make build` / `make validate` |
| Front+mugshot shared palette | **manual** — run `shared_palette.py` per trainer pair |
| HGSS trainer battle sprite extraction/insertion | yes — `extract_trainer.py` / `insert_trainer.py` |
| Authoring 3D models (.nsbmd, <~100 tris) | **manual** — PDSMS |
| Other PNG → Nitro conversions + NARC insertion (OW sprites, tiles, textures) | **manual** — DSPRE / PDSMS / Tinke |
| ROM rebuild + emulator test | scripted elsewhere (`_omni_native_build.sh`), launch is manual |

## Scripts

Each is a standalone CLI; run with `-h` for full usage.

- `scripts/quantize.py` — downscale (nearest-neighbor) + quantize to an
  indexed palette, index 0 reserved for transparency.
- `scripts/shared_palette.py` — one 16-color palette across 2+ images,
  re-indexes each (the Platinum front/mugshot case).
- `scripts/validate.py` — enforce per-asset-class budgets; nonzero exit on
  failure.
- `scripts/sheet.py` — slice/assemble sprite sheets by frame grid.
- `scripts/texture_prep.py` — pad/scale textures to power-of-two + quantize.
- `scripts/extract_trainer.py` / `scripts/insert_trainer.py` — decode /
  splice HGSS trainer battle sprites directly in the decomp NARCs
  (shared codec in `scripts/nitro.py`).
