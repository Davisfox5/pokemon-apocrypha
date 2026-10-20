# Ecruteak City — ten-year heritage architecture

[Native source PR #19](https://github.com/Davisfox5/pokeemerald-expansion/pull/19).
Engine `2d7689a9c420e1af075d6c29c0d069d1aaa04fe3`, stacked on Azalea `d822306675e15abe67c85235d9faf8d6e676d449`.
The simplified concept was approved for native implementation; this finished
native revision remains available for owner visual review. PRs remain draft
while hosted CI is unreported.

## Current native architecture

- All 489 remaining trees use the approved green tree's exact silhouette and
  foliage geometry. Amber and autumn variants change colors only. Eleven trees
  tucked behind the tower roofs use the receiving roof's dark ramp on their
  bottom eight pixels; geometry and texture shade ordering are retained.
- Burned Tower retains its ruin and existing Route 32 stonework. Repeating timber
  scaffold courses and a readable restoration notice identify active rebuilding.
  The bounded worksite pockets behind the scaffold remain closed to walking.
- The central court has a compact traditional shrine, an unattended offering
  counter and a heritage notice. No flowers, statues or new characters are added.
- Four complete trees east of the pond are cleared for a small shrine court,
  paired red lanterns and a stone approach from the south bank. Water and shore
  geometry remain intact. The archive gains a traditional hanging scroll.
- All seventeen lantern placements use one sharp red master. The southern arch
  sits on an eight-pixel visual offset, centered between the forest shoulders;
  its two native walking lanes remain clear and both post flanks remain sealed.

[Full native map](evidence/native-map.png) ·
[Real gameplay gallery](evidence/gameplay-gallery.png) ·
[Central fixtures in-game](evidence/gameplay/heritage-overview.png) ·
[Pond shrine](evidence/gameplay/pond-shrine.png)

Focused native comparisons: [restoration](evidence/heritage/restoration.png),
[pond](evidence/heritage/pond-shrine.png),
[heritage court](evidence/heritage/heritage-court.png),
[lanterns](evidence/heritage/lanterns.png),
[arch](evidence/heritage/centered-arch.png),
[tree geometry](evidence/heritage/tree-geometry.png).

## Interactions and movement

Ten public readings cover the restoration project, archive, Bell approach,
central shrine, heritage notice, offering counter, pond shrine/notice, Will's
Gym and the Dance Theater. The counter has no seller or transaction; inspection
explains that its wrapped offerings should remain there. Both counter columns
are tested, and shrine inspection can be repeated. Every dialogue returns control.
Lanterns and scaffold timbers are ordinary solid scenery.

The two larger central fixtures use standard native inanimate object graphics,
with their solid bodies in the map grid. They are architecture, not NPCs. Two
appended graphics IDs and one palette tag preserve every earlier ID. The game
frame matches all 2,920 visible opaque fixture pixels exactly in RGB5.

The prior coordinate-trigger district transfer could land on blocked house/tree
cells. It is replaced by 53 paired native directional warps between matching
clear edge tiles. North/south travel is tested at every pair; sideways walking
stays in the current district. Four northern tree-root approaches stay blocked.
Existing older preview saves restore only the two appended static fixtures on
return to field. Continue shows both immediately without a reset; menu return
and repeated Continue retain exactly one of each.

## Verification

- Full local ROM build; actual Porymap backgrounds and decoded native RGB match.
  The full overview adds the exact committed native static-object graphics.
- All 3,744 native cells checked for collision, behavior and layer attributes;
  all 1,314 public walkable cells are connected; complete distinct tree roots.
- All 559 reachable open-to-solid boundaries exercised with real game input;
  all 53 district pairs crossed both ways; signs, posts, stairs, water edges,
  fixture bodies and ordinary save/reload/Continue pass.
- Temple: 952 glyphs; city: 996 glyphs; thirteen scenery banks each. Native
  object graphics preserve the central fixtures within the tile budget.
- [Native geometry/layers/interactions](evidence/heritage/review.json),
  [boundary gameplay](evidence/heritage/boundary-runtime.json),
  [all crossings](evidence/heritage/crossing-runtime.json),
  [exact fixture pixels](evidence/heritage/native-object-pixels.json),
  [older-save compatibility](evidence/heritage/prior-save-compatibility.json).

Existing building interiors, adjoining routes, commerce and story actors remain
unwired. District travel retains a short fade. The supplied player is the normal
preview avatar; this work places no story characters.

## Editable source and one-time patch

Committed native map/tileset/object sources remain authoritative. Do not replay
first-authoring generators. The heritage patch is pinned to clean engine
`103874452f101ba3f597cafcca73c1aa1e32998d`; it preserves that source, masters and
prior renders under `source/heritage/baseline/`. Its provenance sequence is:
`heritage.py`, `heritage_fixtures.py`, `heritage_backing.py`,
`heritage_shadows.py`, `heritage_arch.py`, `heritage_pack.py`,
`heritage_hidden.py`, `heritage_objects.py`, `heritage_finish.py`,
`heritage_crossings.py`, `heritage_resume.py`, then `heritage_compile.py`.
The verified exact covers are retained in `source/heritage/`; the packer validates
them against actual patches. Hidden-glyph reuse changes no visible RGBA or
foreground priority. Asset origins are recorded separately from original donors.
Earlier comparisons below retain their historical source identities.

## Approved landmark corrections

The tree overlapping the fence east of Burned Tower is removed, revealing the
complete existing fence posts. The Bell entrance no longer includes source leaf
fragments in its foreground roof mask. Its original dark ridge outline and gold
annex rail remain; a small leaf-occluded timber edge is recovered from the same
vertical grain eight pixels below. Complete trees remain behind the building,
and every other tree/building placement is unchanged.

- [Fence: HGSS / approved / corrected](evidence/landmark-finish/fence.png)
- [Entrance: HGSS / approved / corrected](evidence/landmark-finish/entrance.png)
- [Exact native layers and preservation audit](evidence/landmark-finish/review.json)
- [Current native map](evidence/native-map.png), [in-game views](evidence/gameplay-gallery.png)

At that historical correction, collision, behavior and gates were unchanged. The owner
approved the area with these two remaining corrections; the final correction
images are available for review.

## Approved tree-spacing review

The complete trees now sit closer to Burned Tower and the Bell Tower entrance.
The west/east gateways meet their surrounding forest, and both southern torii
flanks are filled. Side gateways remain closed; the torii center stays open in
both directions. Native collision and a flood-fill check rule out a route around
the barriers. All approved master artwork and building placements are preserved.
This is the owner's requested placement refinement of the HGSS interpretation.

- [Whole-map before/after](evidence/tree-closure/whole-map.png)
- [Burned grove](evidence/tree-closure/burned-grove.png), [Bell grove](evidence/tree-closure/bell-grove.png)
- [West gate](evidence/tree-closure/west-gate.png), [east gate](evidence/tree-closure/east-gate.png), [southern torii](evidence/tree-closure/southern-torii.png)
- [Collision and preservation proof](evidence/tree-closure/review.json), [visual findings](evidence/tree-closure/visual-review.json), [layer-priority audit](evidence/tree-closure/layer-priority.json)
- [Current native map](evidence/native-map.png), [actual gameplay](evidence/gameplay-gallery.png)

## Previous approved court review

Every sheet shows the original HGSS reference, previous c8f961 source and current
**decoded native map**. Coordinates identify native 16px cells.

- [Whole map](evidence/court-refinement/whole-map.png), [current native map](evidence/native-map.png)
- [Northwest court](evidence/court-refinement/northwest-court.png), [northeast court](evidence/court-refinement/northeast-court.png)
- [West house and lantern](evidence/court-refinement/west-house-court.png)
- [Gym](evidence/court-refinement/gym-court.png), [southwest house](evidence/court-refinement/southwest-house-court.png), [southeast house](evidence/court-refinement/southeast-court.png)
- [Center approach](evidence/court-refinement/center-court.png), [Mart approach](evidence/court-refinement/mart-court.png), [Theater approach](evidence/court-refinement/theater-court.png)
- [Central plot](evidence/court-refinement/central-plot.png)
- [Burned Tower](evidence/court-refinement/burned-tower.png), [wall courses without canopies](evidence/court-refinement/tower-without-canopies.png), [temple](evidence/court-refinement/temple.png)
- [West gateway lanterns](evidence/court-refinement/west-gateway-lanterns.png), [east gateway lanterns](evidence/court-refinement/east-gateway-lanterns.png)
- [Actual native gameplay](evidence/gameplay-gallery.png), [individual frames](evidence/gameplay/)
- [Reference grid](evidence/reference-grid.png), [native grid](evidence/native-grid.png), [cell/material ledger](evidence/cell-ledger.json)

## Corrections

All ten receiving courts now have one continuous shaded moss-paver rim. The rim
turns around both shoulders and the head of each recessed approach; it is no
longer a cut through an unrelated rectangular border. The lower house approaches
return to their main facade axes. The southeast plain-front house keeps the
straight rim shown in HGSS, without an invented entrance recess. Recess depth follows each building baseline.
The Center and Mart keep their earlier grid-aligned placements and unchanged shared
masters; their receiving courts have been checked against their actual door centers.

Five complete house-front lanterns and both four-lantern gateway rows are restored
from explicit HGSS masks. Heads, lights, stems and bases remain complete, with
foreground ground kept separate. Three previously open base cells are now blocked;
all other collision/elevation and behavior entries remain unchanged. The tower's
fence posts have complete masks and continuous wood shading.

The Gym now retains cyan glazing, violet bands, warm orange trim and the distinct
horizontal shading on its central roof spine. Its source sign fragment is removed
from the wall mask and the occluded wall repaired from the unobscured symmetric
side; a complete separate sign remains. Burned Tower's orange window timber is
restored beside its green glazing and charred roof. House roof ridges regain gold
shading; existing roof grain, timber panels and violet glazing remain distinct.
The Theater and temple annex regain their gold ridge accents. The Theater has
one complete freestanding sign; its clipped source-board fragment is removed
and the covered wall repaired by symmetry. Three close blue/edge shades were
consolidated to reserve the gold ramp, recorded in
[source finishing notes](source/court-refinement/finish-report.json). Native RGB5
colors approximate the source palette; the overview does not provide hidden pixels.

Burned Tower's two stone courses and the western shelf now use the **Route 32
stone vocabulary**: original Emerald directional side/front pixels in the accepted
Cherrygrove ramp. Complete corner masters join the original native 8px quadrants;
half-side donors are not treated as whole corners. Flat receiving earth remains
separate from the faces. All 46 placements are audited where visible. This
supersedes the previous R02 wall arrangement, preserved in the baseline and history.
[Route32 donor provenance](source/court-refinement/route32-provenance.json).

**The central earth plot is also empty in HGSS, with just a sign.** No building was
omitted there. It stays open; no new monument or campaign feature is invented.

## Native scope and validation

Original: [HGSS Ecruteak overview](https://archives.bulbagarden.net/media/upload/7/77/Ecruteak_City_HGSS.png),
1032×785. Original (0,0) registers at native (64,16), without geometric scaling.
The map occupies 72×52 16px squares with outward padding for complete trees/gates.
This is a source-image reconstruction, not decoded DS collision or hidden terrain.
There are 493 complete trees after removing the fence overlap. The preceding
spacing pass added 47 and shifted 64 at the gate shoulders.
Their distinct 2×2 root footprints do not overlap.

Temple uses 910 glyphs / 333 metatiles; city uses 988 / 422. Both use thirteen BG
banks and reserve sixteen glyph slots. The split at global row 27 uses a short
map fade. Interiors, Bell Tower path, neighboring Routes 37/38/42, campaign actors,
encounters, shops and Gym mechanics remain unwired. Closed entrances are tested as
closed approaches.

The full ROM builds. Actual Porymap 6.3.1 exports equal decoded native output across
all 3,744 cells, with zero visible authoring, collision or behavior mismatches.
Visible master pixels, all complete trees, receiving approaches and directional
wall placements pass. Headless libmGBA checks cover stairs, barriers, restored
lantern bases, the open central plot, adjusted courts and both district transitions.
Ordinary save, cold reload and title Continue pass. A **copy** of the preceding
d5405cdc proof save also reloads/continues; its original file remains unchanged.
These checks support review; owner visual acceptance remains pending.

Records: [current landmark audit](evidence/landmark-finish/review.json), [native review](evidence/review.json),
[build](evidence/build.json), [runtime](evidence/runtime.json), [copied prior-save test](evidence/landmark-finish/prior-save-compatibility.json),
[preservation](evidence/preservation.json), [reproduction](evidence/reproduction.json), [hosted CI](evidence/hosted-ci.json).

The previous court sheets retain the approved c8a826 result as history. The tree
sheets compare that exact baseline to the current decoded native map.

## Editable source and preservation

`landmark_finish.py` applies only the fence rectangle and two Bell roof-mask joins
to clean d5405cdc native source. Its immutable baseline, original master and donor
coordinates are retained in `source/landmark-finish/`. `landmark_review.py` decodes
both native layers, transparency and attributes, verifies unchanged collision and
all placements except the one removed tree, and compares only the three local
rectangles. Previous tree-spacing and court evidence stays historical.

`tree_closure.py` is a narrow one-time patch requiring clean c8a826 native source.
Its baseline and placement ledger are in `source/tree-closure/`. `tree_cover.py`
solves exact thirteen-bank color covers, allowing layer repacking at blocked
joins. `tree_layers.py` independently checks every cover against actual patches
and preserves visible RGB. Open foreground masks and all exposed normal-layer
foreground edges retain their masks and colors; the native layer audit checks all 26 such edge cells.
The tree masters are neither recolored nor resized.

Current committed native maps are authoritative. IDs stay at group 80, 51–52;
shared masters and unrelated map art are untouched. Before-state art, layers,
ledgers and native render are in `source/court-refinement/baseline/`. Previous
R02/tree material evidence remains under `evidence/refinement/` as historical work.

`court_cleanup.py` is a one-time local patch requiring **clean c8f961 native source**.
It refuses other heads and uncommitted native edits. `court_finish.py` applies
the subsequent southeast-rim/sign/ridge corrections to clean d7a478 native source;
it preserves the background architecture under overlapping canopies. Do not replay first-authoring
town generators over committed maps. `compile_refinement.py` encodes edited private
layers with Porytiles 2.0, exact palette covering and the engine's 512-tile split.
The exact cover uses OR-Tools CP-SAT 9.10.4067 (`python3 -m pip install ortools==9.10.4067`);
legacy first-authoring uses Z3. Cached banks are reused only if every current patch
fits without color changes. Run actual Porymap export + `review.py`, `tree_review.py`,
a ROM build, `runtime.py`, then `publish.py` for verification. No nearest-tile art
replacement or invisible color loss is permitted.

Original geography/art: Game Freak / Nintendo / Creatures. Shared artwork origins
are recorded under `source/`. No ROMs, saves, credentials or tool binaries are committed.
