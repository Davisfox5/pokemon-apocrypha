# Shared map source: one branch everyone edits

**Status (2026-10-12): branch created; the `apocrypha build` action is green on head `373e460` (run 38279735129).**
The current accepted Johto maps now exist as ordinary Git history on the owner's
expansion fork instead of only as patch files stacked on a private workbench.

| What | Where |
| --- | --- |
| Source branch | `Davisfox5/pokeemerald-expansion`, branch **`apocrypha`** |
| Base | upstream `expansion/1.17.0` (`e8bd1cd7`) + `gba/cherrygrove-baseline.patch` + `gba/johto-synthesis.patch` |
| Content | Cherrygrove B/C/E synthesis, Routes 29/30/31, expanded New Bark with the accepted laboratory, Dark Cave frontage, Violet entrance, interiors, cast graphics; 43 maps in `gMapGroup_Cherrygrove` |
| Verified | All 437 files of `gba/art/johto-synthesis/evidence/source-manifest.json` reproduce byte for byte on this branch (palette line endings normalized) |
| Mechanics | Production roster and mechanics (`gba/roster-profile.patch`, `gba/mechanics-profile.patch`) are merged in. Five files the town baseline had at an older revision (`items.h`, `tms_hms.h`, `global.h`, `trainer_hill.c`, Mauville Game Corner scripts) were taken from the production tree. The branch is now the single source: maps and mechanics together. `game/` stays pinned for the historical benchmark numbers only. |
| CI | `.github/workflows/apocrypha.yml` on that branch compiles the ROM on every push and PR (host tools, serial `generated`, parallel build). It prints the ROM hash and uploads nothing. Green on `373e460`. |

This replaces "apply three patches into a fresh `tools/vendor/gba/...` workbench"
for Johto map work. The patch files and generators stay in this repo as the
record of how the art was made; they are no longer the way the current source is
exchanged.

## Why

Every collaborator (owner, Claude, Codex, Grok) was reconstructing the same source
from patches whose base commit `f09ec1de` exists only on the owner's Mac. Each
revision shipped as a new standalone patch, so two agents could not work on
different maps at the same time without one of them re-rolling the other's patch.
On a branch, a change to New Bark and a change to Route 31 are two commits that
merge. Porymap, Poryscript, Porytiles and porygon all assume a Git checkout of the
decomp, not a patch stack.

## Setup (any machine, 10 minutes)

```sh
git clone --branch apocrypha https://github.com/Davisfox5/pokeemerald-expansion.git apocrypha-src
cd apocrypha-src
```

Build. The branch builds with the stock upstream toolchain packages, the same
ones CI uses; the pinned Arm GNU 14.2 toolchain from `tools/gba/portable.py`
also works (pass `TOOLCHAIN=...`).

```sh
# Debian/Ubuntu
sudo apt-get install -y build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi libpng-dev
# macOS
brew install make libpng pkgconf && python3 ../pokemon-apocrypha/tools/gba/setup.py   # Arm GNU 14.2 into tools/vendor/gba
make -j1 generated     # serial first: the upstream multi-output map rule races in parallel
make -j8               # -> pokeemerald.gba (ignored)
```

Open it in Porymap: File > Open Project > `apocrypha-src`. Porymap writes
`porymap.project.cfg` and `porymap.user.cfg` on first open. Commit
`porymap.project.cfg`; `porymap.user.cfg` is per machine and is ignored.

## Tools

| Tool | Version to use | Who uses it | Notes |
| --- | --- | --- | --- |
| Porymap | 6.3.1 (released 12 Apr) | Owner first; agents through its scripting API or porygon's bridge | Edits `data/maps/*/map.json`, `data/layouts/`, tilesets, wild encounters, region map. Saving through its UI preserved map blocks, IDs, `build_target`, doors and connections in the September round-trip test. |
| Poryscript | 3.6.1 (released 31 May) | Agents, for new event scripts | Wired. `make tools` fetches the checksum-pinned binary into `tools/poryscript/`; any `data/maps/*/scripts.pory` or `data/scripts/*.pory` compiles to the `.inc` beside it during `make generated`. Commit both; CI fails on a stale `.inc`. Existing hand-written `scripts.inc` files keep working. |
| Porytiles | Homebrew `grunt-lucas/porytiles/porytiles` | Agents, for tilesets built from PNG art | Compatible with pokeemerald-expansion. The existing Johto tilesets were packed by this repo's `tools/gba/maps/*/build.py` compilers, which stay the reference for those banks; use Porytiles for new tilesets. |
| porygon | `gregthegreek/porygon`, Apache-2.0 | Claude Code (MCP server + plugin); any MCP client | Map wiring (`add_warp`, `get_connections`, `edit_connection`, `set_map_properties`, `add_bg_event`), byte-exact `map.bin` / `border.bin` / `metatile_attributes.bin` I/O, `map.json` and `scripts.inc` validation, build error parsing, live Porymap bridge. Targets pokeemerald and expansion forks. Install: clone, `cd mcp && uv sync`, then register the server or install the plugin from `.claude-plugin/`. Optional; nothing in the workflow depends on it. |
| mGBA / libmgba | 0.10.5 | Everyone | `tools/gba/maps/*/runtime.py` style headless checks need `libmgba-dev`; the owner plays in the desktop app. |
| Git + GitHub | | Everyone | PRs against `apocrypha`. CI must be green before review. |

## Working rules on the branch

Before map work, every model and instance must apply
[the required reconstruction workflow](GBA_MAP_RECONSTRUCTION.md), in addition to
existing Grok rules and the branch rules below.

1. **One map group area per PR.** Two agents on the same `map.json` or the same
   secondary tileset will conflict. Say in the PR title which maps you touched.
2. **Never renumber what you did not touch.** Porymap and Porytiles can repack a
   tileset; the diff must be confined to the tileset and maps you meant to change.
   `git diff --stat` before pushing. If `data/tilesets/primary/cherrygrove/`
   changed and you did not intend it, revert it.
3. **Keep owner-edited layouts.** The owner edits in Porymap and commits. A
   generator in `tools/gba/maps/` may never be replayed over a committed layout.
   The generators are provenance, not the editor.
4. **Preserve IDs.** Map IDs, layout IDs, warp ids and event ids are stable. Append
   new maps to `gMapGroup_Cherrygrove`; do not reorder.
5. **Evidence goes to this repo**, under `gba/art/<name>/evidence/`, with the
   expansion commit hash in `preservation.json`. The fork holds source only.
6. **No ROMs, saves, toolchains or emulator binaries** in either repo.
7. **Owner approval still means visual review.** Green CI proves it compiles. A map
   is accepted when the owner has walked it and said so.

## Agent lanes

| Agent | Takes |
| --- | --- |
| Owner | Visual direction, Porymap edits, playtesting, approval, merges to `apocrypha`. |
| Codex | Continues the Johto map rebuild on the branch (New Bark, Route 31, Violet). Its generators now install into a checkout of `apocrypha`, not a fresh workbench. |
| Claude | Chapter 1 scripts and events on the accepted maps, Porymap scripting API / porygon wiring, CI and tooling, docs. |
| Grok | Campaign identifiers (PR #5), flags/badges/travel data layer, region map and section data, encounter tables when the owner approves them. |

## Where the previous workflow still applies

- `tools/gba/portable.py` presets and `gba/source-handoff.json` still rebuild the
  historical workbenches for reproducing evidence or comparing an older revision.
- Production mechanics live in `game/` (pinned upstream + roster and mechanics
  patches) and `tools/gba/build.py`. That is unchanged.
- The owner's private workbenches under `tools/vendor/gba/` on the Mac are not
  replaced. The branch was built from the public patches, so it is equivalent to
  `johto-synthesis-work` at the state recorded in `gba/art/johto-synthesis/`.

## Next

1. Codex: point `tools/gba/maps/johto_synthesis/install.py` style installs at an
   `apocrypha` checkout and commit directly instead of preserving a patch.
2. Owner: set the GitHub repository description for `pokemon-apocrypha` (the
   API refuses settings writes from agent sessions).

## Shared building art

Copy approved Pokémon Centers and Pokémarts instead of rebuilding them per map. The owner selected Violet City’s Center as the canonical Center; see [the standing art note](GBA_SHARED_BUILDING_ART.md).
