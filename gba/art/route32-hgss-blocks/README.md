# Route 32 — refined HGSS reconstruction

Expansion branch `codex/route32-hgss-blocks`, commit `fe8df8b4917f4143ae86ac461c3d970cb4db5f63`, [engine PR #8](https://github.com/Davisfox5/pokeemerald-expansion/pull/8). Revised after the owner rejected the first draft's visual finish. Visual acceptance remains with the owner.

## Review images

- [Before/after refinement overview](evidence/refinement-overview.png)
- [Eight element comparisons](evidence/detail-comparison.png)
- [Whole HGSS/native comparison](evidence/comparison.png)
- [North](evidence/comparison-1.png), [cliff terraces and stairs](evidence/comparison-2.png), [docks and shoreline](evidence/comparison-3.png), [Center and cave approach](evidence/comparison-4.png)
- [Native gameplay gallery](evidence/gameplay-gallery.png)
- [Whole native map](evidence/native-map.png)

## What changed

The first draft flattened the eastern stepped formation into one plateau, used interchangeable cliff corners, painted staircase middle pieces across oversized footprints, clipped coastal rocks, and left old deck cells as grass in the water. This pass corrects those concrete defects.

- Measured HGSS terrace levels restore the connected eastern shelves and three wall courses. Continuous rock masks handle outer corners, reentrant joins and higher-to-lower transitions. Emerald directional side/front pieces keep their native pixel geometry, with the accepted Cherrygrove warm stone ladder. Rock-top chunks come from the real HGSS reference, cleaned into a repeatable native surface.
- The northern stair is a complete east–west 32×48 assembly; the southern stair is north–south, 48×32. Emerald tread/end pieces, mirrored rails, actual landings and adjoining barriers replace the repeated gray panels.
- Boards now have continuous plank seams, restrained grain, joined arms and timber edge courses. Obsolete deck remnants become animated water. Rounded grass/stone banks replace rectangular bright shoreline strips.
- Coastal rocks use a complete source silhouette and native foam edge. The upper fence follows the HGSS 24px spacing. The two eastern rocky outcrops and the southern rock ridge are restored.
- Whole Cherrygrove trees use exclusive 2×2 ground footprints; only rear canopies may overlap. Ordinary spare lawn may be absorbed, never the traced path. No half-tree or random rock fillers are used.
- Ground uses literal accepted Cherrygrove textures and signed-distance path rims, rather than a nearest-ground-tile approximation.
- The shared Violet Center design is retained. The foreign 31-pixel strip on its right roof edge is removed; door pixels, palette and footprint are unchanged. Its forecourt joins the route path, and roof layering is corrected. This cleaned prefab is also in the shared building library; the original Violet PNG is preserved.
- The cave uses a complete native Emerald top/bottom arch and both existing entrance cells.

`source/refined-plan.npy`, `source/terrace-heights.npy`, `source/cell-ledger.csv` and `evidence/refinement.json` retain editable placement, drawn terrace levels, all 4,096 cell behaviors/collisions and the cleanup record. HGSS overview registration remains 16px source cells with a one-cell offset. Collision is explicitly interpreted from the reference, not claimed to be decoded DS collision data. Drawn terrace heights introduce no new mechanic.

## Validation and preservation

The local ROM builds. Porymap 6.3.1 opens and exports the actual project with zero differences from the independently decoded map. All foreground ownership/color pixels match the native result. Isolated Porytiles compilation verifies the local art, grass, rock-top and stair families with zero 5-bit RGB/alpha errors.

The final headless tour passes 256 observations: both complete walking branches, both directions on both staircases, directional ledges, grass movement, barriers, Center entry/return and both cave entrance cells. Fresh 128 KiB flash saving, cold reload and title Continue pass. The preserved first-draft Route 32 save also loads/continues on the refined ROM with identical native images to the new save. This last check covers the prior isolated Route 32 proof save, not unspecified campaign saves.

Other route/town layouts, Cherrygrove primary art, map IDs, route events and the cave test room are unchanged. Source history and `evidence/previous-7bae845/` preserve the rejected draft. Static graphics stay below the door-animation VRAM range. Source only is committed; no ROM, save or tool binary. No desktop game was opened.

## Concrete remaining work

Route 32 still needs wiring to the separately developed Violet City and an Alph destination. The small native cave entry room is a placeholder, not the full Union Cave map. Original trainers, encounters, items and event scripting remain separate campaign work. These limitations do not stand in for visual acceptance of the exterior.

## Editing and reproduction

Edit the committed expansion checkout directly in Porymap. The authoring scripts are provenance, not an editor to replay over owner changes; their source manifest guard refuses changed Route 32 files. `refine.py` is the owner-authorized cleanup pass and reads the original HGSS trace/reference plus the preserved initial plan.

For isolated reproduction from a clean `apocrypha` base `2722eaf7601ec02dc5a684fa8cdef9206c0dc377`:

```sh
python3 tools/gba/maps/route32_hgss_blocks/build.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/register.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/refine.py /path/to/engine
make -C /path/to/engine -j1 generated
make -C /path/to/engine -j8
python3 tools/gba/maps/route32_hgss_blocks/compile_assets.py /path/to/engine /path/to/porytiles-legacy
python3 tools/gba/maps/route32_hgss_blocks/runtime.py /path/to/engine /new/evidence-directory --toolchain /path/to/arm-toolchain
```

The headless Porymap project-core probe source is alongside those scripts. The original HGSS and shared asset source hashes remain in their provenance files. Pokémon source artwork: Nintendo, Game Freak, Creatures; HGSS overview hosted by Bulbagarden Archives. Native adaptation/cleanup: Apocrypha project.
