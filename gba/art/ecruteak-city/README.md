# Ecruteak City — court, fixture and stone-wall refinement

[Native source PR #19](https://github.com/Davisfox5/pokeemerald-expansion/pull/19).
Engine `c8a8267606411bd62a6274ed0e5f430b1b2f7e80`, stacked on Azalea
`d822306675e15abe67c85235d9faf8d6e676d449`. Exterior proposal for owner visual review;
local checks pass. The source PR remains draft pending hosted CI and visual acceptance.

## Current review

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
All 447 tree anchors and distinct 2×2 roots remain unchanged in this pass.

Temple uses 838 glyphs / 330 metatiles; city uses 960 / 415. Both use thirteen BG
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
c8f961 proof save also reloads/continues; its original file remains unchanged.
These checks support review; owner visual acceptance remains pending.

Records: [current audit](evidence/court-refinement/audit.json), [native review](evidence/review.json),
[build](evidence/build.json), [runtime](evidence/runtime.json), [copied prior-save test](evidence/court-refinement/prior-save-compatibility.json),
[preservation](evidence/preservation.json), [reproduction](evidence/reproduction.json), [hosted CI](evidence/hosted-ci.json).

## Editable source and preservation

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
fits without color changes. Run actual Porymap export + `review.py`, `court_review.py`,
a ROM build, `runtime.py`, then `publish.py` for verification. No nearest-tile art
replacement or invisible color loss is permitted.

Original geography/art: Game Freak / Nintendo / Creatures. Shared artwork origins
are recorded under `source/`. No ROMs, saves, credentials or tool binaries are committed.
