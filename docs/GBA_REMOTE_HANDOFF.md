# GBA source handoff for Claude and Grok

The remote repository is **Davisfox5/pokemon-apocrypha**. The Mac folder name
`the-omni-hack` is only a local name. Use branch **codex/gba-source-handoff**.
This branch publishes the GBA work previously available only in that Mac checkout.
Read AGENTS.md, CONTEXT_INDEX.md and AGENT_HANDOFF.md after this page.

## Start in a remote Linux session

Select this branch when attaching the GitHub repository. In an existing checkout:

```sh
git fetch origin codex/gba-source-handoff
git switch --create my-cherrygrove --track origin/codex/gba-source-handoff
```

Use your own unique branch if `my-cherrygrove` already exists. Do not switch away
from unsaved work. No Mac filesystem access, base ROM, Nintendo DS SDK, old DS
submodules, emulator virtual environment or private baseline repository is needed.

Install the host dependencies. On Debian/Ubuntu, as an authorized administrator:

```sh
apt-get update
apt-get install -y build-essential git ca-certificates xz-utils libpng-dev pkg-config python3 python3-venv libmgba-dev
python3 -m venv .venv
. .venv/bin/activate
pip install Pillow
```

For a fresh independent town with the existing cast available:

```sh
python3 tools/gba/portable.py --preset workbench --output tools/vendor/gba/my-cherrygrove --build
```

This downloads public upstream source and a checksum-pinned Arm GNU 14.2 toolchain
for Linux x86_64/aarch64 or Apple Silicon macOS. You can supply an existing complete
toolchain with `--toolchain /path/to/toolchain`. All outputs are ignored locally.
`--output` must be new; the helper refuses to replace existing work or `game/`.

The workbench contains the original technical town, working interiors/connections,
and registered character graphics. It does **not** contain the subsequent custom
or HGSS exterior reconstructions, and it does not place all custom characters for
you. Replace the exterior with your independent interpretation and author your own
placements. Character constants and native strips are already installed. Choose
`--preset town` if you want the same town without the additional character imports.
This is an isolated visual baseline with historical mechanics, not current campaign
mechanics. Avoid changing gameplay economy in this map task.

## Reproduce the existing custom preview for comparison

```sh
python3 tools/gba/portable.py --preset preview --output tools/vendor/gba/reference-preview --build
python3 tools/gba/maps/check_cherrygrove.py tools/vendor/gba/reference-preview tools/vendor/gba/reference-check --toolchain tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi --runtime-source tools/gba/maps/johto_restart_runtime.c
```

Use the `aarch64` toolchain directory on ARM Linux or `darwin-arm64` on Apple
Silicon. The setup JSON beside the output directory records the selected path.
The check creates an ordinary `town.sav`, native PNG captures and JSON results.
Choose a new check output directory for each run. `MGBA_FLAGS` may supply compiler
and linker flags for a nonstandard libmGBA installation; otherwise the checker
uses pkg-config, Homebrew when present, or standard system headers/libraries.

The old visual compilers have local clone-name and baseline-HEAD assumptions.
Do not run them as remote bootstrap commands. The new portable helper reconstructs
the engine directly from checked-in patches and public upstream. Rebuild native
art as part of your own implementation, or deliberately adapt a historical authoring
script when that is your task. Historical README commands remain evidence for their
original Mac workspace, not promises of remote portability.

## Production mechanics and source preservation

`game/` is a registered submodule pinned to public upstream
`e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7`. It is deliberately separate from previews.
To reconstruct the published production profile in an isolated directory:

```sh
python3 tools/gba/portable.py --preset production --output tools/vendor/gba/production-copy --build
```

The profile is the preserved roster plus mechanics patches, not a qualification of
all campaign systems. Never merge an entire preview blindly into production: the
preview patches include special starting locations and runtime proof entrypoints.

`gba/cherrygrove-baseline.patch` now contains the missing pre-art town snapshot as
a patch against public upstream. The later `gba/johto-restart.patch` applies directly
after it. Its historical local commit was f09ec1de; a remote checkout does not need
that Git object. The export retains the upstream compresSmol **source** needed to
build on each host. It does not depend on copied Mac executables. Patch hashes and
preset order are in `gba/source-handoff.json`.

Keep source changes in your own branch or a reproducible patch. Preserve existing
art and custom Gold/Silver/Kestra identities. Do not commit ROMs, saves, emulator
states, credentials, environments or downloaded tool binaries. Legacy tracked Mac
emulator environments/save states were removed from this handoff branch; their
history and the owner's existing workspace are untouched.

## Container recipe and validation

A Linux container recipe is included for repeatable host dependencies:

```sh
docker build -t apocrypha-gba -f tools/gba/Dockerfile.remote tools/gba
docker run --rm -v "$PWD:/workspace" apocrypha-gba python3 tools/gba/portable.py --preset preview --output tools/vendor/gba/container-preview --build
```

See `gba/evidence/source-handoff.json` for the actual fresh-source build and runtime
checks performed for this branch. Linux x86_64 and ARM use separately pinned
compiler archives. A checksum entry alone is not evidence of a test on that host.
Previous Mac preview measurements remain in `gba/art/johto-restart/evidence/`.
