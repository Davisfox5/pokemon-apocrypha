# Chapter 1 isolated GBA source overlay

The latest scene blocking revision is documented in
`../chapter1-staging/README.md`. Its separate review ROM is
`tools/vendor/gba/Chapter1-staging-review-20260929/Apocrypha-Chapter1-staging.gba`
(SHA-256 `20b363e2f7c8b5831e80f328a7521e6cf163a871c41762c0a57c5d7bbd687d81`). This supersedes the earlier scenes review build; both
older ROMs and the owner's active playable save remain unchanged.

`source-overlay/` contains all 379 modified/new engine source files relative to
pinned engine base `f09ec1de2e6754e9f9a8e02281d3d773efcfa65e`, with
SHA-256 hashes in `source-overlay/SHA256.json`. The live isolated source is
`tools/vendor/gba/opening-house-work`. The overlay contains no ROM, save, or
build output. The continuous tour route generator and headless runtime probes
are under `tools/gba/maps/`.

Build from the isolated engine directory with
`gmake -j8 TOOLCHAIN=/Users/davisfox/Documents/GitHub/the-omni-hack/tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi`.
Native visual evidence, full-scene walkthrough checks, remaining art and
battle limits are in `../chapter1-staging/README.md`.
