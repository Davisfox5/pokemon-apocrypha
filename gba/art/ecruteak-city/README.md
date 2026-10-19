# Ecruteak City — refined HGSS exterior

[Native source PR #19](https://github.com/Davisfox5/pokeemerald-expansion/pull/19).
Source `c8f961fc5a84cce6f3c71c0db58b19f8e3a9dd29`, stacked on Azalea
`d822306675e15abe67c85235d9faf8d6e676d449`. Exterior proposal for owner visual review.
The PR remains draft pending hosted CI and visual acceptance; local checks pass.

## Review this refinement

- [First pass/current whole map](evidence/refinement/whole-map.png), [current native map](evidence/native-map.png)
- [HGSS rocks with canopies removed](evidence/refinement/rocks-without-canopies.png)
- [Original and recreated tree families](evidence/refinement/tree-masters.png)
- [Burned Tower](evidence/refinement/burned-tower.png), [Bell entrance and annex](evidence/refinement/bell-entrance.png)
- [Timber house](evidence/refinement/house-entry.png), [green house](evidence/refinement/house-green.png)
- [Northwest house](evidence/refinement/house-1.png), [northeast house](evidence/refinement/house-2.png), [southeast house](evidence/refinement/house-southeast.png)
- [Theater](evidence/refinement/dance-theater.png), [Gym](evidence/refinement/gym.png)
- [Center](evidence/refinement/center.png), [Mart](evidence/refinement/mart.png)
- [South torii](evidence/refinement/south-gate.png), [west gate](evidence/refinement/gate-1.png), [east gate](evidence/refinement/gate-2.png)
- [Actual gameplay](evidence/gameplay-gallery.png), [individual captures](evidence/gameplay/)
- [Reference grid](evidence/reference-grid.png), [native grid](evidence/native-grid.png)
- [Cell ledger](evidence/cell-ledger.json), [native checks](evidence/review.json), [material audit](evidence/refinement/native-material-audit.json)

## What changed

Burned Tower's terraces and the western outcrop now use complete approved R02-family
rock modules. All 48 placements match their masters after RGB5 conversion. Caps,
faces and corners remain whole; canopy-free review exposes the joins. The pond
boulder reuses existing Azalea art. The stairs retain their geometry with a coherent
shared stone ramp. Hidden HGSS faces are interpreted, not claimed as extracted data.

Recreated HGSS tiered conifers and the broad temple maple replace the first-pass
crowns. Green, amber and autumn variants preserve trunks and shading. All 447 tree
positions and distinct 2×2 roots remain; none are partial or overlap another root.
Explicit original masks and recolor provenance live under `source/refinement/`.

Each building has an original/first-pass/current comparison. Golden sliding-door
panels regain vertical timber grain; Bell entrance/annex glazing is violet and
Burned Tower glazing green. Roof grain, footings, masks and receiving ground were
refined locally. Fully opaque blocked wall quadrants use two native layers to retain
both gold timber and neutral framing exactly. The palette report records the few
close-shade consolidations needed for the fifteen-color hardware limit.

Center, Mart and shared gate masters remain unchanged. The Center moved 16 source
pixels east and the Mart 8 north; their courts, curb recesses and door approaches
were rebuilt together. Theater's notch and placard were cleaned. The obsolete rock
apron collision was removed; 26 collision edits are individually recorded.

## Reference and native scope

Original: [HGSS Ecruteak overview](https://archives.bulbagarden.net/media/upload/7/77/Ecruteak_City_HGSS.png),
1032×785. Original (0,0) registers to native (64,16), without geometric scaling.
The complete exterior occupies 72×52 native 16px squares. Outward padding completes
tree crowns and clipped side gates. This is an overview reconstruction, not extracted
DS collision, height data or hidden terrain. Material and traversal ledgers are separate.

Two rendering districts preserve room for landmark art: temple uses 845 glyphs /
339 metatiles; city uses 976 / 420. Each uses thirteen BG banks with sixteen glyph
slots reserved. The split at global row 27 (source y416) uses a short map fade.
Interiors, adjoining Routes 37/38/42, Bell Tower path, campaign actors, encounters,
shops and Gym mechanics remain unwired. Closed doors are tested as closed approaches.

## Validation and preservation

Actual Porymap 6.3.1 exports equal decoded native output for all 3,744 cells, with
zero visible authoring, collision or behavior errors. All visible master pixels
(488,020), complete tree frames and landmark approaches pass review. The full ROM
build passes. Headless libmGBA tests cover stairs, forest/fence/pond/post barriers,
both district transitions, adjusted doors and the corrected western apron. Ordinary
save, cold reload and title Continue pass. A copy of the first-pass save also loads
and continues on the refined ROM; its original file was left unchanged. See
[prior-save results](evidence/refinement/prior-save-compatibility.json).

Exact identities: [build](evidence/build.json), [runtime](evidence/runtime.json),
[preservation](evidence/preservation.json), [reproduction](evidence/reproduction.json).
Existing IDs and unrelated map art are preserved. Ecruteak uses group 80 IDs 51–52.
Original first-pass material remains in `source/refinement/baseline/` and Git history.

Committed native maps remain authoritative. `refine.py` is a guarded, one-time
refinement of the first-pass commit; `compile_refinement.py` encodes edited layers
without regenerating geography. Do not replay first-authoring generators over
committed layouts. Review actual Porymap exports, build the ROM, then run `runtime.py`
and `publish.py` for subsequent edits. Porytiles 2.0 uses exact palette covering and
the engine's stable 512 primary/secondary split.

Original geography/art: Game Freak / Nintendo / Creatures. Shared artwork provenance
is in `source/shared-provenance.json` and `source/refinement/shared-rock-provenance.json`.
No ROMs, saves, credentials or tool executables are committed.
