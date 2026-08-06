# tools/

Two kinds of things live here:

- **First-party tooling** (tracked): the emulator harness (`play.py`,
  `cockpit.py`, `emu_*.py`), the live map editor (`mapeditor/`), the
  Hoenn/Sinnoh region-port converters (`hoennconv/`, `regionport/`), the
  artwork reference library (`artwork_library/`), and launch wrappers for
  external GUI tools (`launch_pdsms.sh`, `launch_dspre.sh`).
- **Third-party binaries and jars** (gitignored): these go in
  [`vendor/`](vendor/README.md). Binary blobs (`*.jar`, `*.exe`, `*.dll`,
  `*.zip`) are ignored anywhere under `tools/` so they can never be
  committed by accident.

For the asset conversion pipeline itself (quantize/validate/sheet/texture
scripts), see [`../scripts/`](../scripts/) and the root `Makefile`.
