# GBA baseline qualification

Status (2026-09-10): **toolchain, upstream build, roster benchmark, and baseline
save tests passed**. Full Apocrypha capacity is not yet qualified: 30-box storage
requires a different save/RAM implementation. The [page-store prototype](GBA_STORAGE_PROTOTYPE.md) now has separate qualification
evidence and an unresolved transaction/checkpoint tradeoff. No new maps or artwork were produced.

## Reproduce the build

Apple Silicon macOS is the qualified host. From the repository root:

```sh
# Initialize only the production submodule, not every historical donor.
git submodule update --init game
brew install make libpng pkgconf
python3 tools/gba/setup.py
# On a clean upstream checkout, apply the tracked roster benchmark once:
python3 tools/gba/profile.py apply
python3 tools/gba/build.py
python3 tools/gba/measure.py
python3 tools/gba/build.py --qualification
# Install mGBA if needed for ordinary-ROM boot/cold-save checks:
brew install mgba
python3 tools/gba/smoke.py
```

`game/` is a Git submodule pinned to release `expansion/1.17.0`, commit
`e8bd1cd7b03fc032ea37e3ecd38b379b5d01a1e7`. The checked-in
[roster patch](../gba/roster-profile.patch) is applied locally; the submodule HEAD
remains upstream. Parent-repository patches preserve these edits for fresh clones.
Do not reset the submodule to discard work. `profile.py remove` reverses only this
patch when needed for an upstream comparison; it refuses non-applicable changes.
Future engine changes must likewise be tracked in reviewed patches or a deliberately
established source fork, never left only in a dirty submodule.

The build wrapper uses checksum-pinned **Arm GNU Toolchain 14.2.Rel1**, including
newlib, from ignored `tools/vendor/gba/`. It checks the upstream commit and passes
an explicit toolchain path; it does not edit shell startup files. Homebrew GCC
16.2 was installed during preflight but is **not** the qualified compiler: it
lacks the required embedded C library. GNU Make 4.4.1, libpng 1.6.58, pkgconf
2.5.1, Python 3.9.6, and Apple clang 21.0.0 were available during qualification.
Compiler archive URL/checksum are in [toolchain.json](../tools/gba/toolchain.json).
Host packages are version-recorded rather than reproducibly vendored.

mGBA 0.10.5 (Homebrew `0.10.5_2`) runs the ordinary-ROM checks. The upstream test
runner is separately bundled/pinned by the expansion checkout; its Mac source
revision is documented in `game/tools/mgba/README.md`. Homebrew currently marks
its mGBA formula deprecated because of Qt 5; this did not prevent qualification.
Map/art editors and Poryscript/Porytiles are deferred until their production phase.

Output: `game/pokeemerald.gba` (ignored). Root `make build` still runs the legacy
DS asset pipeline. Use the Python wrapper for GBA. A clean rebuild is
`python3 tools/gba/build.py clean` followed by `python3 tools/gba/build.py`.
Always rebuild after profile/source changes before running `smoke.py`, whose ELF
symbols and target-compiled struct offsets must match the ROM.

## Measured results

| Metric | Unmodified upstream | Roster benchmark | Hardware/address budget |
| --- | ---: | ---: | ---: |
| Linked ROM bytes | 26,752,568 | 19,552,960 | 33,554,432 |
| Static EWRAM bytes | 226,420 | 226,336 | 262,144 |
| Static IWRAM bytes | 28,392 | 28,392 | 32,768 |
| SaveBlock1 bytes | 15,568 | 15,484 | 15,872 allocated payload |
| SaveBlock2 bytes | 3,884 | 3,884 | 3,968 allocated payload |
| SaveBlock3 bytes | 4 | 4 | 1,624 distributed payload |
| PokemonStorage bytes | 34,144 | 34,144 | 35,712 allocated payload |
| PC capacity | 14 × 30 | 14 × 30 | 30 × 30 required |

The benchmark leaves **13.35 MiB of linked ROM space**, 35,808 bytes of static
EWRAM space, and 4,376 bytes of static IWRAM space. ROM files are padded, so linked
usage is the useful content budget; file sizes and hashes are recorded separately.
RAM figures include reserved buffers/heaps; they do not prove adequate runtime
heap or stack headroom in every scene. New regions/art, custom types, and future
configuration changes must be remeasured.

The [configuration manifest](../gba/configuration.json) records the profile:
Gen 1–5 families plus Sylveon, native forms/fusions and pre-Gen9 Mega forms of
retained families; no later regional forms or unapproved gimmick forms. Internal
species IDs remain unchanged. The benchmark still uses upstream battle defaults;
it is **not the final classic-mechanics configuration or an obtainability audit**.
Roster switches also affect save layout: SaveBlock1 shrank by 84 bytes. Do not
reuse player saves across configuration changes without an explicit migration.

## Verified behavior and limits

- Both ordinary ROMs built and executed 600 headless mGBA frames. This is a boot
  smoke check, not a visual review or a complete playthrough.
- Four upstream save-structure compatibility tests passed on unmodified upstream.
- An upstream normal-save/reload test preserved party, PC boundary entries, and
  a story variable. The roster profile additionally passed the tracked test that
  fills **all 420 existing PC slots**, saves, destroys live PC/party state, reloads,
  and checks the entire storage digest, party data, and story variable.
- Roster tests verify Sylveon, Clefairy's Fairy typing, and Gen5 species data.
- Two **fresh emulator processes** exercised the ordinary roster ROM's new-game,
  normal-save, and normal-load engine functions. Only a 128 KiB flash file crossed
  between them; the saved story value survived. No emulator savestate was used.
  This bypasses menu navigation and does not claim manual save-menu validation.
- No 30-box build, power-interruption recovery test, five-region travel test,
  Terra/Shadow battle implementation, or 20-badge UI test has passed yet.

The unmodified asset build emitted libpng `bKGD: invalid index` metadata warnings
and one linker RWX LOAD-segment warning. Builds completed successfully; counts
are recorded in evidence. Do not claim warning-free builds.

Compact evidence: [upstream build](../gba/evidence/upstream-build.json),
[upstream ABI sizes](../gba/evidence/upstream-capacity.json),
[roster build/tests](../gba/evidence/roster-build.json),
[roster ABI sizes](../gba/evidence/roster-capacity.json),
[cold-save/boot checks](../gba/evidence/roster-smoke.json).
Local full logs and the unmodified comparison ROM/ELF are ignored under
`tools/vendor/gba/evidence/`; rerun the commands instead of relying on those files
being present in another clone. Test code lives in `tools/gba/`; `--qualification`
temporarily copies its test into the upstream test directory and removes that
copy afterward. The wrapper relinks test filters to avoid stale or empty test runs.

## Capacity constraints and next implementation order

Owner update (2026-09-10): storage/autosave architecture is deferred, not resolved.
Item 2's [configuration audit](GBA_MECHANICS_AUDIT.md) now records eighteen
applied scope corrections; the final rules-era decision remains open. Independent identifier planning may
follow, but save-dependent integration still awaits storage qualification. See
[GBA_STORAGE_PROTOTYPE.md](GBA_STORAGE_PROTOTYPE.md) for the deferred requirements.

1. **30-box save and RAM design remains a production prerequisite.** Each boxed Pokemon is 80 bytes.
   The current 30-box structure would require 72,704 bytes, exceeding the PC
   payload allocation by 36,992 bytes. It would also add 38,560 bytes of resident
   RAM, exceeding the roster benchmark's static EWRAM headroom by 2,752 bytes.
   The existing flash format has two rotating 14-sector save slots and four
   auxiliary sectors within 128 KiB. A bigger box constant is insufficient.
   Evaluate a compact representation and/or paged storage with an atomic journal;
   retain all supported Pokemon data and prove worst-case fit/recovery. Generic
   compression estimates, bigger emulator-only save files, or dropping the backup
   copy without a recovery design are not qualification. See [storage brief](GBA_STORAGE_QUALIFICATION.md).
2. **Lock the remaining battle/configuration settings.** Audit classic Gen3 defaults
   explicitly, retaining Fairy data and Mega scope. Add Terra/Shadow type identities,
   type-chart/UI support and gym-specific per-Pokemon assignments once matchups
   are specified. Existing Terastallization is not their implementation.
3. **Establish campaign state and world identifiers.** Current counts are 2,400
   flag bits (including occupied/system/trainer flags), 256 persistent 16-bit vars,
   and eight badges. Add stable region/chapter/20-badge state and shared gates
   after the save format is settled. Changing trainer-count limits can shift
   system flags; preserve identifiers rather than assuming constants are stable.
4. **Validate map constraints before authoring.** Warp events use byte group/map
   IDs, but saved `WarpData` uses signed bytes and there are reserved sentinel
   values. Do not infer 65,536 freely usable maps. Allocate multiple small groups
   and validate identifiers through save/warp/travel paths. Current map loading
   requires `(width + 15) * (height + 14) <= 10240`; map event counts are bytes,
   and only 16 object events are active at once, including the player. These are
   local constraints, not a limit of 16 events across the whole game. Map-grid
   metatile indices use ten bits with an undefined sentinel. Five-region map
   screens, location names, Fly/heal destinations and badge displays need integration.

Primary source locations: `game/include/save.h`, `game/src/save.c`,
`game/include/pokemon_storage_system.h`, `game/src/load_save.c`,
`game/include/global.h`, `game/include/constants/flags.h`,
`game/include/constants/vars.h`, `game/include/global.fieldmap.h`,
`game/include/fieldmap.h`, `game/src/fieldmap.c`, and `game/src/data/types_info.h`.
Read only the files relevant to the next task. These findings establish engineering
work within GBA; they do not justify automatically switching platforms.
