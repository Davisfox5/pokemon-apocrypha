# Omni Hack — Artwork Reference Library

Every sprite and overworld art asset extracted from the four source games used by this hack,
in one folder, as ordinary PNGs. Built as a style/content reference for creating new custom
artwork (e.g. in Claude Design). ~9,900 PNGs, ~41 MB.

Regenerate any of it with the scripts in `tools/artwork_library/`
(`build_artwork_library.py` — straight copies; `extract_hg_owsprites.py` — HGSS BTX0
overworld sprites; `render_gen3_blocks.py` — Gen 3 metatile block sheets).

## Layout

| Folder | Contents |
|---|---|
| **`_contact-sheets/`** | **47 compact composite sheets — the ones to use in Claude Design.** Every category packed into ≤1024px grids (named `<game>_<category>_<nn>.png`), so they can be attached to a design prompt and read at full pixel detail. Animation strips are represented by their front-facing frame; the full frame strips and back/female sprites live in the per-game folders below. Rebuilt by `tools/artwork_library/make_contact_sheets.py`. |
| `heartgold-johto/` | The base game (HGSS engine). |
| `platinum-sinnoh/` | Sinnoh donor game (Gen 4). |
| `emerald-hoenn/` | Hoenn donor game (Gen 3). |
| `firered-kanto/` | Kanto donor game (Gen 3). |

### Per-game folders

- **`pokemon/`** — battle sprites. Gen 3: `<name>_front/back/icon.png`. Platinum:
  `<name>_male/female_front/back.png` + `<name>_icon.png`. HeartGold: `<natdex>_<name>_front/back.png`
  (+ `_female_*` where the species is dimorphic).
- **`pokemon-icons/`** (HG) — 544 party/menu icons, numbered by National Dex.
- **`trainers/`** — Gen 3: battle front pics (`back_*` = player back sprites). HG: the 76
  VS/preview mugshots, plus **`battle-front/`** (all 129 trainer-class battle sprites as
  frame strips, named from `trainer_class.h`) and **`battle-back/`** (all 17 backsprite
  throw-animation strips, 5 or 8 frames). Extracted by `scripts/extract_trainer.py`;
  re-insert customs with `scripts/insert_trainer.py`.
- **`overworld-people/`** (Gen 3) — walking NPC sprite strips.
- **`overworld-sprites/`** (HG) — all 847 overworld models as RGBA frame strips:
  `<mmodel-id>_<name>.png`, names from `include/constants/mmodel.h` (NPCs, the player,
  follower Pokémon, doors, rocks, props). 17 of the 864 mmodel slots are empty stubs, skipped.
- **`overworld-objects/`** — Gen 3: dolls, cushions, berry trees, misc props, OW Pokémon
  (prefixed by category). Platinum: signpost art.
- **`items/`** — item icons named by item (`leftovers.png`, `tm01.png`…). HG's were converted
  from NCGR/NCLR via nitrogfx using the icon table in `src/item.c`; unused/data-card entries skipped.
- **`doors/`** (Gen 3) — door animation strips per building type.
- **`tilesets/blocks/`** (Gen 3) — **the overworld blocks**: every tileset's 16×16 metatiles
  rendered with true palettes, 8 blocks per row, in map order. `primary_general_blocks.png` is
  the region-wide base set; `secondary_<map>_blocks.png` are the per-area sets (rendered
  against the `general` primary, as in-game). FireRed's `silph_co` borrows `condominiums`
  tiles (as in the game's tileset header).
- **`tilesets/tiles/`** (Gen 3) — the raw 8×8 tile sheets (un-paletted; prefer `blocks/`).

## Notes

- All indexed sprites had palette slot 0 made transparent, so they composite cleanly.
- HGSS overworld *maps* are 3-D (textured models), so there are no HG "block sheets" —
  the Gen 3 block sheets + `converted/hoenn` ground work are the block-art references.
  HG building exteriors exist as 3-D models only; their door/prop textures are in
  `overworld-sprites/`.
- HG trainer *battle* sprites live in unnamed NARC archives and are not extracted here;
  the `trainers/` mugshots cover trainer art.
