# Chapter 1 scenes: review evidence

`evidence/scene-sequence.png` shows fifteen native 240×160 headless mGBA captures
from the final isolated ROM. Individual PNGs preserve each capture. The
playable review ROM is
`../../../tools/vendor/gba/Chapter1-scenes-review-20260929/Apocrypha-Chapter1-scenes.gba`
(SHA-256 `c51f1307e19747e1b1920405b262e711cd386e6fb3ea07bcc8d3e395dfc9f67f`). It is separate from the owner's current save.

The headless walkthrough began with a fresh New Game, used an ordinary save at
the house handoff, then walked and pressed buttons through the Chapter 1 exit
without warping or repositioning the player. Test source:
`../../../tools/gba/maps/chapter_continuous_runtime.c` and
`../../../tools/gba/maps/opening_house_revision_runtime.c`. The individual
scene and persistence checks are listed in `../chapter1-route/README.md`.
