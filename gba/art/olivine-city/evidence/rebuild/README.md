# Independent-asset Olivine reconstruction — 2026-10-20

The owner rejected the overview-based initial pass. The replacement uses HGSS
for geography and architectural/material references; it reconstructs the actual
city from standalone architecture and reusable native terrain/prop modules.
The assembler never reads or samples the overview raster. The old original
`reference-ground.png` is retained historical input for the rejected pass only.

![Rebuilt native city](../native-map.png)

## Inspect the actual components and joins

- [Isolated native building/boat masters](isolated-native-assets.png): Gym,
  one residence master used three times, café, lighthouse, terminal and boat.
- [Terrain and prop modules](terrain-and-prop-modules.png): fan stone paving,
  lawn, sand, water, dock wood, cliff faces/caps, curbs, pickets, lamps, signs,
  parasols/tables, stairs, ramp and shore rocks.
- [Whole-city before/after](before-after.png). The full-size rejected image
  remains `before.png`; latest actual native image is `../native-map.png`.
- HGSS / rejected / rebuilt context sheets: [Gym](gym.png),
  [residences](residences.png), [café](cafe.png), [lighthouse](lighthouse.png),
  [terminal](ferry-terminal.png), [service-building/lamp joins](service-buildings-and-lamp.png),
  [festival gate](festival-gate.png), [stairs](upper-stairs.png),
  [ramp/coast](lighthouse-ramp-coast.png), [grove](northern-grove.png),
  [promenade](promenade.png).

Architecture original: image_gen, isolated transparent asset sheet, HGSS as
architectural reference only. The retained full sheet, alpha crops, target sizes,
hashes and module provenance are under `source/rebuilt/`. The generated image
is not a game-ready map. Individual masters are converted into coherent native
RGB5 families and encoded as ordinary Porymap tiles/metatiles. Terrain and props
are independently drawn native-size modules. Approved Center/Mart/tree masters
retain their provenance and exact visible colors; all screenshot conifers are
replaced by 144 whole shared trees with distinct roots.

The small residence/café glass needs explicit blue ramps; roof frequency alone
would remove it. Yellow/blue flags and brass lamp heads have an intentional
compatible family. Cliff caps, front faces and flat lawns stay distinct. The
Mart lamp and lighthouse sign were fitted to the receiving neighborhood. Mixed
canopy/roof quadrants split across background and foreground, with four unused
foliage entries carrying matching lawn; canonical tree indices remain unchanged.

## Geography, footprints and honest adaptations

Same 65×54 city grid and thirteen sections, map IDs63–75. No renumbering or new
campaign links. HGSS overview projection is interpreted, not extracted DS data.
Partial house/path/quay/pier squares are completed to whole native cells. In
particular the path/quay east edge completes to x640 and central pier to x448.
The upper stair is two native columns at x576–608, y304–336, with closed shoulders.

The original broad collision trace had open cliff squares and passable railings.
Source context inspection identifies the actual festival gate gap at x184–240;
other railing runs are solid. The new material/collision ledger has no open water
or cliff-face cells. Twenty-four collision cells differ from the rejected pass:
visible railing/cliff/stair corrections and two moved prop footprints. Each is
recorded in `collision-adaptations.json`, with before/after flags. Elevations,
section boundaries and all previous cities' native data remain unchanged.

## Native runtime and verification

Source: engine `81697bbe0f9582ca30567604c748f22d0166a458`, branch
`codex/olivine-goldenrod-playbook-20261019`,
[draft PR23](https://github.com/Davisfox5/pokeemerald-expansion/pull/23).
The independent existing remote Olivine/Ecruteak branch is preserved unchanged.
No merge or supersession of that branch is implied.

The atlas derives from actual native files: 1,270 glyphs, maximum buffered ring
376/1,008 slots, 10,670-byte cache. All13 global palette banks remain below the
reserved UI banks. Actual Porymap exports and independent decode agree across
all3,510 native cells. Current proof:134 BG captures /5,145,600 pixels, zero
errors, including walking, save/cold load and title Continue. Four real walking
clips show festival gate, promenade, lighthouse ramp and ferry pier. The game
save snapshot uses SaveMapView, matching the ordinary menu's native-view cache.

Two real load-path issues were corrected locally to this static exterior:
old saves' disposable viewport IDs must not restore obsolete collision over the
reconstructed source; and fast Return/Continue must not queue static tiles that
overwrite the streamed glyph cache after drawing. Player/save state and save
format remain intact. The normal camera seam guard is retained. Goldenrod return
and old Goldenrod save scenery still match exactly. A real previous Olivine save
loads, renders correctly, blocks the moved lamp and clears its former post area.

ROM SHA256: `20f7acf35a45e6dd611cc172b352369d49db5dd481cd0d902a5b6cf88cae1a77`.
Local production build passes. A clean detached source checkout passes source
hash/atlas checks; this is not a claim of a second fresh compilation. Guarded
baseline-worktree art/atlas reproduction matches all340 changed native/derived
files exactly. Runtime source fixes are checked separately by gameplay. Hosted
GitHub Actions remains disabled; no hosted CI success is claimed.

See parent `build.json`, `review.json`, `runtime.json`,
`gameplay-background-parity.json`, `source-manifest.json`, `fresh-checkout.json`,
`previous-city-parity.json` and `walking-film.json`. Here, see
`native-reproduction.json`, `prior-Olivine-save.json`, `material-traversal.json`
and `visual-review.json`. `rejected-baseline/` contains immutable first-pass
identities. `historical-gameplay/` is explicitly not current verification.

## Remaining scope

Owner visual review of this rebuilt pass is pending. Exterior art/traversal only:
no interiors, Lighthouse floors, Gym/service mechanics, NPCs, encounters,
operational ferry or route connections. Water/boats/flags are static. Rock,
water, lawn and paving use compact repeatable material cores. Future mutable
map tiles would require reconsidering this static exterior's saved-view policy.
