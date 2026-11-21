# Johto element standards

Owner-approved 2026-11-20/21 after the PR #39 review. Every Johto map uses these. A map
that draws one of these elements differently gets fixed when it next goes through G3.
Always follow AGENTS.md "Never draw over what is already there": change only the element,
keep canopies, props, shadows and neighbouring ground, and diff old vs new before review.

| Element | Standard | Source |
| --- | --- | --- |
| Trees | Cherrygrove's tree | accepted map: CherrygroveCity (#39) |
| Low ridges (forest, grassland) | thin one-tile dirt ridge, square corners (Routes 36/31) | accepted map: JohtoRoute36 |
| Mountain cliffs | big tan rock faces (Routes 32, 42-46; Route 31 mountain) | accepted maps |
| Stairs | Route 32 kit: `tools/gba/maps/johto_stairs.py` | locked 2026-11-20 |
| Tall grass | hand-drawn G3 tile, rounded patch corners, wavy 1-2 px side/bottom edge, blade tips on top; carved edge pixels are plain grass ground only, never path/sand colours; the grass fills only the old grass outline, so path borders and margins in the same cells stay | `tools/gba/maps/standards/johto_tall_grass.py`, `gba/art/johto-common/standards/tall_grass_tile.png` |
| Ponds and small pools | the map's light HGSS water inside Emerald's pond border set (rim, shadow band top/left, 2 px lip on the land below) | `tools/gba/maps/standards/johto_pond.py` |
| Sea, rivers off the map edge | unchanged (deep blue sea); no pond border | |
| Large lakes (Lake of Rage) | case by case: border likely, water texture decided per map | ask the owner |
| Ground grass, dirt paths, ledges | the common version already on most maps | survey boards |

Mockups the owner approved: `/mnt/project-files/standards/picks/tall_grass_soft.png` and
`pond_borders.png` (project files).

## Applying them

Both tools return `(old, new, cells)` pixel images of a map from an engine checkout. Only
pixels inside the element's cells change. Feed `new` to the map's own packer (for example
`route32_native/pack.py`) so the tiles and palettes are rebuilt within budget, then run
`map_gate.py` and check the diff before review.

```sh
EMERALD_ENGINE=path/to/vanilla-capable/checkout python3 tools/gba/maps/standards/johto_pond.py
python3 tools/gba/maps/standards/johto_tall_grass.py   # writes the 16x16 tile
```

`johto_pond.ponds()` treats a water body as a pond when it does not touch the map edge and
has at most 400 cells. Check its pick on every map; harbours and big lakes need a decision.

The tall-grass rustle field effect (`graphics/field_effects/pics/tall_grass.png` on the
fork) still shows Emerald's grass and must be redrawn to match the new tile.

## Rollout list (from the 2026-11-20 survey of open PRs)

Tall grass: CherrygroveRoute29Approach, CherrygroveRoute30Approach, JohtoRoute31, JohtoRoute32,
JohtoRoute33, JohtoRoute36, JohtoRoute38, JohtoRoute39, Route42, Route43, Route44, Route45,
Route46. Kanto maps (KantoRoute7, KantoSaffronCity) wait for the Kanto kit.

Ponds: CherrygroveCity, CherrygroveRoute30Approach, JohtoRoute31, VioletCity,
JohtoEcruteakTempleDistrict, Route42, Route43, Route44, Route45, BlackthornCity.
Case by case: JohtoRoute32 (sea vs inland water), LakeOfRage, OlivineCity and CianwoodCity
(harbour water), KantoCeladonCity (Kanto).
