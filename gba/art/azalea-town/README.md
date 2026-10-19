# Azalea Town — HGSS-based native exterior

A separate area on engine `codex/azalea-town` and hub `codex/azalea-evidence`.
Engine source `a322750485` (full identity in `evidence/build.json`).
Route33 map/layout/art/source is untouched; this work branches from engine
`eb15d8923401af86bb12670c6627c2bfba1e3d0a`.

## Visual review

- [Whole native map](evidence/native-map.png), [2×](evidence/native-map-2x.png)
- [Registered HGSS/native comparison](evidence/reference-comparison.png)
- [Kurt's house](evidence/Kurt-comparison.png), [service buildings](evidence/service-buildings-comparison.png)
- [Gym loop](evidence/Gym-loop-comparison.png), [Slowpoke Well](evidence/well-comparison.png)
- [House/forest](evidence/house-forest-comparison.png), [completed west gate](evidence/gate-comparison.png)
- [Original grid](evidence/reference-grid.png), [native grid](evidence/native-grid.png)
- [Native review](evidence/review.json), [cell ledger](evidence/cell-ledger.json), [shared pixel checks](evidence/shared-art-review.json)

## Reference, materials and adaptation

Original reference: https://archives.bulbagarden.net/media/upload/0/0f/Azalea_Town_HGSS.png
932×508. Source(0,0) registers to native(64,16); native64×33 cells /1024×528.
The left/top extension completes the clipped western gate and tree crowns; right
and bottom padding completes native boundary cells. This is an overview-based
reconstruction, not extracted original DS collision or height data.

The Gym's surrounding path loop, Kurt's northern spur, Center/Mart approaches,
ordinary house spur, nested well terraces, southern woodland and eastern route
approach follow the original arrangement. Specific grass/dirt/stone/forest/props
are recorded separately from native collision and behavior. No source characters,
quests or story gates are copied from the original overview.

The approved C06 Center, M01 Mart, selected G02 side gate, T01 trees, signs,
mailboxes, flowers and native ledges are reused from shared source at ddafe9de.
The mailbox uses the catalog's15-color native indexed export. Source masters are
locked by hashes; all visible canonical pixels compare exactly after ordinary
RGB5 hardware conversion. Native boulders and the tiny southern plateau texture
reuse retained adjacent-map art; the plateau uses the boulder stone palette.
Only Azalea-specific thatched houses, Gym, well, timber piles and the small stone
need local assets; source polygons and native palette cleanup are preserved.
Gym green signage remains opaque architectural art. The chimney stays gray.

All277 trees are complete32×48 masters. Roots occupy distinct2×2 cells; supported
canopy overlap is32px between rows. The row beside Kurt's woodpiles shifts16px
without overlapping roots or exposing a missing-tree corridor. Roofs draw above
walking space while the actual walls/bases block, preserving the street behind
the southeast roof. Dirt/grass edges and the well apron use a coherent native rim.

Approved service-building footprints differ from the original overview; their
placements and clear approaches are adapted to the native grid. Kurt's local
architecture shifts8px down/right to fit the existing native forest/roof grid.
The completed western gate needs extra canvas and shifts the nearby boulder.
Well terraces and partly obscured lower terrain are native-grid interpretations;
they are not advertised as decoded DS elevations. Door alignment and approach
reachability are checked independently of those art adaptations.

## Source and checks

Current source is `data/maps/JohtoAzaleaTown`, its layout, and the private
`azalea` tileset pair in the engine repository. Editable material/solid/behavior
ledgers, foreground/background layers and canonical masters are under `source/`.
The original native tree/building/scenery PNGs remain unchanged.

932 native glyphs,397 metatiles and13 BG palette banks; all remain within the GBA
limits. Porymap6.3.1 exports equal the decoded native output across2112 cells.
Source root footprints, native attributes, complete well rock masters, connected
approaches and shared master pixels are checked by `review.py`. Arm GNU14.2.1
build and actual headless movement/barrier/ledge/closed-door approach checks pass,
including ordinary save, cold reload and title Continue. A copied eb15d89234
Route33 save also loads and Continues without changing its original. See
[gameplay](evidence/gameplay-gallery.png), [runtime](evidence/runtime.json),
[build](evidence/build.json), [reproduction](evidence/reproduction.json) and
[prior-save compatibility](evidence/prior-save-compatibility.json).

The first-authoring tools are provenance, not an editor to replay over committed
maps: `assets.py`, `build.py ENGINE`, then `register.py ENGINE`. The build refuses
committed Azalea source. `--authoring-only` only permits untracked work-in-progress
on a private first-authoring checkout. Exact RGB palette covering uses Z3; Python
versions are recorded in `source/python-versions.json`. No nearest-tile replacement
is used. Hidden native backing is compacted only where the other layer completely
preserves the final grass/object silhouette; actual decoded RGB is verified.

## Remaining scope

This is the town **exterior** for owner visual review. Building interiors,
Slowpoke Well descent, Ilex Forest and Route33 connections remain closed pending
separate implementation/integration. No campaign actors, dialogue, encounters,
shop inventory or Gym mechanics were invented. Native ordinary-save and movement
proof qualify this exterior; they do not establish owner visual acceptance.

Original geography/game artwork: Game Freak / Nintendo / Creatures. Existing
project adaptations and the selected shared revisions are recorded by source
paths and hashes. No ROM, save or tool executable is part of this evidence.

## Individual house cleanup — 2026-10-18

Current native source: `76a8e5f16bdf7c610a1c58db067ec99b6b9696a3` on `codex/azalea-town`. Kurt’s house and the southeast house were repaired separately from their HGSS reference crops. Restored violet glazing and wooden door panels, removed stray cutout edges, restored the southeast roof vents and complete rounded chimney. Existing straw grain and each house’s proportions remain. No layout generator was replayed.

- [Kurt before/after](evidence/kurt-house-before-after.png)
- [Southeast house before/after](evidence/house-house-before-after.png)
- [Current whole map](evidence/native-map-2x.png)
- [House patch checks](evidence/house-cleanup.json)

The guarded direct patch is `tools/gba/maps/azalea_town/house_cleanup.py ENGINE`; it expects the original `a322750485` native inputs and original local masters, preserved in `source/house-cleanup/`. Run this only on that baseline, never over current native edits. Palette 2 consolidates two redundant dark outline shades to restore two violet glass shades; no additional palette bank. The Porymap export matches native decoding exactly. Pixel comparison verifies no changes outside the house regions; collision/elevation bits are unchanged. Headless gameplay, door approaches, save, cold reload and Continue pass. Interiors remain outside this exterior task.

### Kurt eave correction

Native source `8beab42d99def1e39eb37ba076e837d1be13da31` removes the remaining attached log-cutout fragments and smooths the straight right eave and its lower corner. The separate log pile and approved southeast house remain exact. The patch changes 123 foreground pixels in three cells, only the private primary tile PNG; collision and map/metatile IDs remain unchanged. Actual Porymap/native and headless gameplay/save/reload checks pass. [Before/after](evidence/kurt-edge-before-after.png). Reproducible guarded patch: `tools/gba/maps/azalea_town/kurt_edge_cleanup.py`, baseline `76a8e5f16b`; inputs preserved under `source/kurt-edge-cleanup/`.

### Kurt roof and left support restoration

Current engine `0c0d2cff899438dcf0663762c2b2675e8d6cea5c` restores the HGSS upper thatch envelope that the initial cutout mask truncated, and completes the column and stepped stone footing left of the door. Roof portions occluded by reference canopy continue the neighboring thatch plane; this interpretation is explicit rather than claimed extracted original hidden pixels. Existing clean right eave, door, windows, separate log pile and regular house are preserved. [Original/current comparison](evidence/kurt-structure-original-current.png). Thirteen cells change; collision/elevation remain exact. Neighboring canopy pixels retain identical visible RGB, with a few moved between hardware layers to keep native 8px palette boundaries valid. Porymap/native, headless walking, save, cold reload and Continue pass. Guarded direct patch: `tools/gba/maps/azalea_town/kurt_structure_cleanup.py`, baseline `8beab42d99`; prior master/input lock under `source/kurt-structure-cleanup/`.

### Superseding rejected upper-roof repair

Owner rejected the preceding roof extension because it retained a clipped boundary inside the thatch. Current engine `e365b1821260897eea1463485fdadea741658510` discards the upper-roof patch and rebuilds the full upper section, including its outer boundary, instead of overlaying straw pixels on the old outline. Clean HGSS thatch pixels supply each plane, canopy-colored source pixels are excluded, and the original dark central ridge remains structural. Hidden portions use nearest clean same-plane reference donors; no claim of decoded hidden texture. The completed left support, lower roof, door, window, ordinary house and separate logs are unchanged. [Current original/native comparison](evidence/kurt-roof-original-current.png). Native/Porymap and headless walking/save/reload pass; visual approval remains pending. Guarded native patch `tools/gba/maps/azalea_town/kurt_roof_rebuild.py` expects baseline `0c0d2cff89`; rejected master and input lock are retained under `source/kurt-roof-rebuild/`.

### Roof texture and crossed-ridge contrast

Current engine `d822306675e15abe67c85235d9faf8d6e676d449` preserves the accepted roof silhouette and cleans isolated single-pixel same-plane quantization speckles on both slopes. The central crossed timber now retains the original source-defined recessed/body/end-face value groups using the existing native charcoal palette (24/40/48); it no longer collapses into a uniform warm outline shade. No palette colors were changed. Native hardware layers separate gray logs from warm thatch; the hidden background beneath logs continues the corresponding roof plane. [Original/previous/current detail](evidence/kurt-texture-detail.png), [original/current full house](evidence/kurt-texture-original-current.png). Eight isolated speckles and 238 ridge pixels were corrected, with 246 visible RGB pixel changes total. Alpha/silhouette is exact, no visible changes outside the roof, and collision, regular house and separate log pile remain unchanged. Porymap/native match and headless walking, save, cold reload and Continue pass. Owner visual approval pending. Guarded `tools/gba/maps/azalea_town/kurt_roof_texture.py` expects baseline `e365b18212`; original inputs/master preserved in `source/kurt-roof-texture/`.

### Kurt’s ten-year property expansion — kiln proposal

Current engine `38200410b559a842e4b4c7ef17e5dc8e77164f9a` on `codex/azalea-town` adds an attached masonry kiln with a complete flue/chimney, curved shoulders and arched unlit firebox. The original timber-and-thatch house is retained pixel-for-pixel, with a short timber link joining the new structure. A broad rear stack shows **23 tightly packed cut log ends** rather than long side faces. Exactly two full trees at native origins (304,128) and (320,96) were removed; underlying rear-tree trunks were restored from intact shared masters. The remaining 275 tree footprints do not overlap. A narrow rounded path connects the original front approach and new side yard. The first lower-thatched-wing proposal is preserved under `source/kurt-extension/earlier-thatch-proposal/`; the owner requested this kiln design instead.

- [Current property](evidence/kurt-property-current.png)
- [Previous/current property](evidence/kurt-property-before-after.png)
- [Gameplay property](evidence/gameplay/Kurt-expanded-property.png)
- [Gameplay firewood yard](evidence/gameplay/Kurt-firewood-yard.png)
- [Native/source checks](evidence/kurt-extension.json)
- [Detached baseline reproduction](evidence/kurt-extension-reproduction.json)
- [Previous ordinary save compatibility](evidence/kurt-previous-save.json)

This is an owner-authorized exterior design proposal. There are no new interiors, dialogue, quests or kiln mechanics. Existing house entrance remains closed as before; the kiln mouth is scenery with collision, not a new warp. The regular house and all non-Kurt visible art are unchanged. Route33 remains untouched.

Editable masters are `kurt-kiln.png` and `kurt-firewood.png`. `kurt_extension_art.py` authors only the local proposed objects and a preview from preserved baseline layers. `kurt_extension.py ENGINE` is a guarded direct native patch against `d822306675`; it never replays the town generator. The original layout, placement ledger, masks, source layers and prior proposal are preserved under `source/kurt-extension/`. Reproduction on a detached baseline matches all 40 native Azalea files after palette line-ending normalization.

Native limits: 995/1008 usable glyph slots, 412 metatiles, 13 unchanged palette banks. The patch modifies 33 cells and changes collision in 16 cells for the two cleared trees, rear pile and kiln walls. Actual Porymap6.3.1/native RGB match, original house visible-pixel errors zero, no visible changes outside Kurt’s property. Headless walking verifies the side yard, kiln front/east walls, woodpile barrier and retained forest barrier; normal save, cold reload and ordinary Continue pass. An existing pre-expansion save is tested using a copy. Hosted CI is not claimed; owner visual acceptance remains pending.
