# Coordinate review — 2026-10-24

All boxes use native cells (exclusive right/bottom); subtract (2,2) to reach
the original geography. Original and native numbered sheets, actual compiled
tiles/palettes, Porymap exports and native-scale mGBA frames were inspected.
The whole boundary was scanned, with the following joins examined enlarged.
This records agent review; owner visual acceptance remains pending.

| Review area | Specific finding and correction | Final evidence |
|---|---|---|
| North gate/forest (10,0)–(29,12) | Completed all canopy tips using apron; kept separate roots and original forest width. New compact gate retains the doorway columns and stepped approach. Its destination remains blocked/unwired. | [Grid](evidence/focus/north-gate-forest.png), [game](evidence/runtime/gate.png) |
| West ledges/corners (1,11)–(19,19) | Preserved flower patch, narrow west barrier, vertical turn and south-facing ledge. Initial palette allocation washed out brown ledge faces; a mixed grass/rock/path bank restores the complete face and cap. | [Grid](evidence/focus/west-ledge-corners.png), [game](evidence/runtime/west-lawn.png) |
| Houses/antenna (16,11)–(35,20) | Replaced tall model renders with shared compact native houses at the original door columns. Restored dirt beneath the smaller antenna tree; checked door baseline, path shoulders, east cliff and foreground roots. | [Grid](evidence/focus/houses-antenna.png), [game](evidence/runtime/shop-front.png) |
| Gym/grass (4,18)–(19,29) | Source master contained an opaque lawn and neighbor fragment. Traced the complete silhouette, removed those pixels, restored continuous receiving grass/dirt, fitted the front baseline and retained the brown roof/blue facade identity. Door is blocked and interior unbuilt. | [Grid](evidence/focus/gym-join.png), [game](evidence/runtime/gym-front.png) |
| Center/east cliff (20,18)–(32,30) | Preserved locked C06 opaque pixels. Reconstructed the complete lawn beneath the shorter building, kept east rock plane and full trees, opened the roof overhang rows and blocked the actual body. Warp and new three-frame animation use the visible single door column. | [Grid](evidence/focus/center-join.png), [roof](evidence/runtime/behind-center-roof.png), [animation](evidence/door-animation.png) |
| South roots/rock (0,27)–(36,34) | Removing old tree mesh exposed thin grass stripes on the plateau. Restored stone top first, joined root lawn pockets, then placed complete shared trees. North-facing lip has high ground to the south; no inverted wall or repeated front-face blocks across flat top. | [Grid](evidence/focus/southern-roots-rock.png), [game](evidence/runtime/south-groves.png) |
| Both Center floors | Inspected shared floor/wall edges, entrance mat, staircase landings and return exit. Both Porymap exports match decoded native and both sides of stair/door transitions pass. | [Ground floor](evidence/porymap/MahoganyPokemonCenter-export.png), [upstairs](evidence/porymap/MahoganyCenterUpstairs-export.png), [game](evidence/runtime/center-upstairs.png) |

The original reference is a binary-derived orthographic projection, not an
original-game screenshot. Roof height and tree silhouettes differ intentionally
when replaced with shared native art. Fully occluded original ground is inferred
from material continuity and recorded receiving repairs. The new gate,
watchtowers, antenna tree and adapted Gym remain design proposals. No claim is
made that their individual pixels match the original game.

Every native metatile is checked against its editable layer atlas and actual
engine decode. That proves the tested pixels are the shipped native pixels;
it does not automate artistic judgment. The material ledger contains original
materials even when hidden by foreground art, while traversal is audited
independently with the thirteen declared changes. Remaining unbuilt destinations
and gameplay limits are listed in the README.
