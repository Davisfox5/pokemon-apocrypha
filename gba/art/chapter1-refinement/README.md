# Chapter 1 scene refinement — September 30, 2026

This is an isolated revision of the September 29 Chapter 1 staging build. It is
not installed over the owner's current ROM or save. Review ROM:
`tools/vendor/gba/Chapter1-refinement-review-20260930/Apocrypha-Chapter1-refined.gba`.
SHA-256: `2c6ef6fba773d28475fba460833013d48b661eeeb74768baa6ec283595e09f56`.
The review folder has no save; select New Game. The owner's September 29
playthrough and staging saves were not used or modified.

## Scene corrections

- The Gold/Silver scene uses the engine's camera object to pan four tiles to the
  battle and back. The player turns toward Kestra before their first exchange.
- Scripted outdoor fades now use the day/night-safe `fadescreenswapbuffers`
  command, as the pinned expansion's DNS tutorial requires. The visible
  Gold-farewell fade/reposition was removed. Side-by-side actual mGBA frames
  are in `evidence/lighting-before-after.png`.
- After the Route 30 catch, Gold and Kestra reach the southern edge of that
  route. The player walks across its real map connection into Cherrygrove's
  north entrance; the tour auto-starts there. The rescue no longer warps the
  player to Gold's doorstep.
- Kestra exits north after the first meeting, skirts Gold rather than walking
  through him after the starter choice, and runs out of view before removal
  on the return. In New Bark she follows the walkable road toward Elm's
  institute; her off-camera destination is persisted for map reload.
- The first Mart stop was rerouted so the player, Kestra, and Gold finish in a
  horizontal line facing the speaker. All five stops retain the prior dialogue
  and distinct landmarks.

## Source and build

The isolated build is `tools/vendor/gba/chapter1-scene-refinement-work`, cloned
from `opening-house-work` at engine base
`f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`. Its only source differences
from the September 29 staging workbench are three `scripts.inc` files under
CherrygroveCity, CherrygroveRoute30Approach, and NewBarkTown. The exact three
files and their hashes are in `source-overlay/`. To reconstruct, start from the
pinned engine revision, copy `gba/art/chapter1-route/source-overlay/` into it,
then copy this refinement's `source-overlay/` over those files. All 379 base
overlay files and the three overrides were checked against the built workbench.
The route authoring script is `tools/gba/maps/build_chapter1_tour.py`; invoke it
with the isolated workbench path. Its route follows native map collision data.

Build command from the isolated workbench:

```sh
gmake -j8 TOOLCHAIN=/Users/davisfox/Documents/GitHub/the-omni-hack/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi
```

## Verification

- mGBA core: fresh New Game through Mom's handoff, ordinary in-game save, cold
  Continue, then ordinary button input and walking through the northbound
  Chapter 1 departure. No fixture warps were used in that full walk.
- All three starter choices and Kestra's type-advantage choices reached the
  departure with one party Pokémon, five Poké Balls, Pokédex, map card, and
  Gold's contact.
- At all five tour stops, runtime assertions checked player, Kestra, and Gold
  coordinates and facing. Native 240×160 frames for the camera, Route 30 exit,
  town entry, five tour stops, and Gold's farewell are in `evidence/`.
- The ROM compiles. The build emits the existing bedroom implicit/explicit
  `waitstate` warning and linker RWX warning; neither was introduced by these
  three scripts.

This revision fixes the reported blocking and transition faults. The opening
Gold/Silver exchange remains a scripted field performance rather than a
turn-based battle. Route 29 and New Bark art remain provisional.
