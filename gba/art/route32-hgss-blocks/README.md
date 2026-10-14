# Route 32 — HGSS exterior reconstruction

Source: expansion branch `codex/route32-hgss-blocks`, commit `7bae845d9f6b6eca806444bee5b220f17f6da342`, [engine PR #8](https://github.com/Davisfox5/pokeemerald-expansion/pull/8). This is a visual-review draft, not owner acceptance or a completed connected campaign area.

The original HGSS Route 32 overview is the layout authority. `source/trace.json` records the measured polygons; `source/cell-ledger.csv` records all 4,096 native cells, source sampling coordinates, metatile, behavior and walking collision. Registration uses native 16px cells with a one-cell border offset. The reference is a rendered DS overview, so collision is interpreted explicitly rather than claimed to be decoded HGSS collision data. Existing Gen 3 route plans were not used for placement.

## Visuals

- [Complete same-scale comparison](evidence/comparison.png)
- [North](evidence/comparison-1.png), [terraces and grass](evidence/comparison-2.png), [railway and docks](evidence/comparison-3.png), [Center and cave approach](evidence/comparison-4.png)
- [Whole native map](evidence/native-map.png)
- [Native gameplay gallery](evidence/gameplay-gallery.png)

Complete Cherrygrove tree footprints and ground are reused. Plateau shapes follow the HGSS trace; Emerald's native cliff edges, stairs, directional ledges and cave mouth supply the local terrain. The broad plateau fill is cleaned with the same native soil colors. Tall grass reuses the accepted real-HGSS TEX0 family. Rails occupy the overhead hardware layer, while the western lane and fishing dock retain their separate walking surfaces below.

The Center is an **exact copy of the finished Violet City asset**, including silhouette and alpha, from hub `1c8e61c317a870910ef099af7851144549480b12` / engine `9037554c61833a5f8f7da175d45420b4797bafde`. See [the standing shared-building rule](../../../docs/GBA_SHARED_BUILDING_ART.md). No new Center or Mart redraw was made; this HGSS route contains no Mart.

## Verification

The native ROM built. Porymap 6.3.1 opened and exported all three relevant layouts; its Route 32 export matches the independent decoded native map with zero pixel differences. Porytiles legacy 2.0.0 compiled the local gate/rail/dock/boulder art plus reused grass into 80 metatiles with zero native 5-bit RGB or alpha errors. This isolated compiler verification does not repack any existing engine primary bank or map IDs.

The final headless mGBA tour passed 254 normal-input observations: northern-to-southern walking, both land and fishing-dock branches, passage below the railway, tall-grass movement, downhill ledge/uphill blocking, terrain barriers, Center/cave entry and return. Ordinary 128 KiB flash saving, cold reload and title-screen Continue all passed. The initial placement and separate barrier probes use the existing map-proof fixture; walking tour segments use ordinary directional inputs. No desktop game was opened.

`evidence/preservation.json` verifies that Cherrygrove, Routes 29–31, New Bark, the existing Violet entrance and their tilesets are unchanged. Native secondary tiles stay below the door-animation scratch range; only supported palette banks are used. ROMs, saves and tool binaries are excluded.

## Remaining concrete work

The newer Violet City is on a separate unmerged source branch. Route 32's north exit is not wired into it yet. The clipped HGSS Alph gate is preserved, but Alph's destination/interior is not built. The Union Cave doorway leads to a small native Emerald entry test room, not a reconstructed Union Cave interior. Original route NPCs, trainer battles, items, encounters and event scripting are not supplied by this exterior-only revision.

## Reproduction and editing

Open the expansion source checkout directly in Porymap. Edit committed source there and preserve its IDs. The authoring scripts below are provenance, not an editor to replay over owner changes. Their manifest guard refuses altered Route 32 source.

For isolated reproduction from a clean `apocrypha` base (commit `2722eaf7601ec02dc5a684fa8cdef9206c0dc377`), from the hub:

```sh
python3 tools/gba/maps/route32_hgss_blocks/build.py /path/to/engine
python3 tools/gba/maps/route32_hgss_blocks/register.py /path/to/engine
make -C /path/to/engine -j1 generated
make -C /path/to/engine -j8
python3 tools/gba/maps/route32_hgss_blocks/compile_assets.py /path/to/engine /path/to/porytiles-legacy
python3 tools/gba/maps/route32_hgss_blocks/runtime.py /path/to/engine /new/evidence-directory --toolchain /path/to/arm-toolchain
```

The headless Porymap export source is `tools/gba/maps/route32_hgss_blocks/porymap_probe.cpp`; it links against a Porymap 6.3.1 build. It opens/renders the actual project core without simulating desktop UI work.

Reference credit: Pokémon HGSS art © Nintendo, Game Freak, Creatures; the original overview is hosted by Bulbagarden Archives, with URL/digest recorded in `gba/art/violet-route-references/provenance.json`. Native adaptations and cleanup: Apocrypha project. Preserve the original references and earlier workbenches.
