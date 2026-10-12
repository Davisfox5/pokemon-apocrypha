# 30-box storage prototype: results and decision

Status (2026-09-10): **an isolated paged backend passes native fault tests and an
actual-Pokemon GBA emulator test**. It is not the production PC/save implementation.
The playable benchmark still has 14 boxes. No existing saves or DS work were changed.

## Deferred by owner (2026-09-10)

The owner asked to record the save/autosave question and move on. This prototype's
seven-page transaction bound and measured latency do not prove universal GBA
limitations. Neither automatic checkpoints nor emulator-assisted saving is adopted.

On return, compare ROM-only save-layout/packing alternatives with emulator-assisted
checkpoints. The requested autosave behavior, if implemented, is a rotating set
of separate automatic saves, with the last manual save preserved until explicitly
replaced, and sub-second autosaves. Retention count and supported devices are not
settled. File backups and full emulator save states are different mechanisms;
copying a file alone does not eliminate in-game flash-write latency. Qualify
consistent world/party/PC restoration, interruption time, completed persistence,
manual-save protection, compatibility and recovery before promising that behavior.

Continue with the classic-mechanics configuration audit. The 30-box requirement
remains unresolved and must be revisited before production save integration or a
claim that the complete baseline is qualified. Leave production saves unchanged.

## What is implemented

[store.c](../tools/gba/storage/store.c) implements a fixed-size, versioned,
copy-on-write page store on **32 × 4 KiB = 128 KiB flash**. It copies every supplied
byte; it neither compresses Pokemon nor discards names, trainer identities, IVs,
EVs, ribbons, or other fields. A 4 KiB read cache avoids keeping the PC resident
in RAM. ARM-measured backend workspace is **4,236 bytes**, plus caller data and
stack. This does not include the rest of the game's RAM or a finished PC UI cache.

| Allocation | Sectors | Bytes |
| --- | ---: | ---: |
| Alternating committed root records | 2 | 8,192 |
| Current snapshot pages | 23 | 94,208 |
| Unreferenced pages available to a transaction | 7 | 28,672 |
| Total physical flash | 32 | 131,072 |

900 unchanged-format boxed records need 72,000 bytes. The current roster baseline's
SaveBlocks 1/2/3 plus a naive 30-box storage structure total **92,076 bytes**, leaving
2,132 bytes within this prototype snapshot capacity. This is a size comparison,
not an implemented serialization of those SaveBlocks. The prototype's fixture uses
opaque snapshot space around the Pokemon records.

**The separate legacy Hall of Fame, Trainer Hill and recorded-battle sectors are
not included in that 92,076-byte total.** This prototype uses their physical space;
production must explicitly budget required auxiliary features instead of silently
dropping them. Five-region state growth also needs a measured reserve.

## Transaction protocol and recovery

1. Validate the current root's page checksums and reject invalid/oversized requests
   before writing anything.
2. Erase the inactive root. The active root and all pages it references remain intact.
3. Write changed logical pages to free physical pages, reading back each CRC.
4. Write and verify a new root containing the schema/layout version, generation,
   page mappings, and CRCs. Program its commit marker last.
5. Mount the newest complete valid root. If a write reports failure after mutation,
   remount before further operations; the commit may actually have landed.

This guarantees **old-or-new complete transactions within the tested transaction
bound**, rather than accepting a mixture of pages. It does not retain two complete
independent copies of all data. Corruption of a page shared by both roots is
reported as corrupt and cannot necessarily be repaired. A corrupt private new page
or root can only fall back when the older root's complete referenced data is intact.
Fixed alternating root sectors are also a write-wear hotspot; hardware endurance
and root rotation need qualification before production checkpoint frequency is set.

Only a blank device can be formatted. Unknown valid prototype versions are refused;
legacy/unrecognized contents are never reformatted automatically. There is no
legacy-save migration or released compatibility promise yet. The ordinary game's
new-game/continue/menu paths are not connected to this backend.

## Evidence

Reproduce from the repository root after the existing GBA toolchain setup:

```sh
python3 tools/gba/storage/run.py --gba
```

This builds native tests with AddressSanitizer and UndefinedBehaviorSanitizer,
compiles the backend with the pinned ARM compiler, and temporarily injects a
qualification test into the upstream runner. Temporary source copies are removed
afterward. It writes [compact evidence](../gba/evidence/storage-prototype.json);
full logs/binaries stay ignored in `tools/vendor/gba/storage-evidence/`.

Checks passed:

- All **900 × 80-byte records**, including records crossing page boundaries, are
  recovered byte-for-byte in native tests with varied high-entropy payloads.
- **1,408 injected interruptions plus two successful controls** span two successive
  generations, including old-root reclamation. Cuts cover each 64-byte data-program
  boundary, each 1 KiB partial-erase boundary, every root-metadata byte, and each
  bit of the final commit marker. Recovery validates the whole snapshot as old or
  new. These are simulated fault boundaries, not exhaustive electrical fault tests.
- Oversized and duplicate-page transactions are refused without changing flash;
  bounds errors, write/readback corruption, missing commit acknowledgments, corrupt
  roots, corrupt shared pages, and unsupported versions are exercised.
- Five independent native processes perform format/write, read, update, and two
  subsequent reads of the same 128 KiB file. No RAM state or emulator savestate is
  shared. This is a backend file test, distinct from the GBA emulator test below.
- A GBA test ROM creates **900 actual Bulbasaur/Sylveon records** with distinct
  trainer IDs, personalities, initialized names, levels and IVs. It verifies all
  bytes, updates the first/last records and another page, destroys backend state,
  remounts, and re-verifies all 900 records using the actual 1 Mbit flash driver.
  This test does not perform a cold emulator-process restart of the new backend.
- The GBA test measures approximately **9 seconds for initial full formatting**
  and **2 seconds for a three-page commit**, at roughly one-second timer resolution.
  These are emulated-time prototype measurements, not physical cartridge latency.
  The flash adapter currently performs redundant erases and is not optimized.
- The isolated ARM object size and compiler stack-usage report are in the evidence.
  Stack reports are per function; callback and nested call usage must be added.

The test runner and normal flash driver originally both used timer 2, producing
false timeout counts. The qualification test temporarily assigns flash to unused
timer 3 and restores the driver afterward; the production timer configuration was
not changed. A one-page read cache also avoids recalculating a whole page's CRC for
every individual record read. The native interruption suite was rerun against that
cache implementation.

## Why this is not yet a drop-in solution

The maximum atomic transaction changes **seven logical pages**, including all
world/party/PC metadata being saved—not seven boxes. An eighth page is rejected
before any erase/program operation. A large PC rearrangement, many changes between
manual saves, or a broad SaveBlock rewrite can exceed this bound. Splitting such a
save into several commits would expose intermediate game states on power loss.
The prototype deliberately does not do that.

Two full raw snapshots of the current proposed 30-box state would already require
184,152 bytes before root records or auxiliary features. Compression or a new
semantic packing scheme might improve this, but no worst-case lossless packing
bound has been established. This is **not** a proof that all 128 KiB solutions are
impossible, and it is not a reason to switch platforms automatically.

Two paths remain:

- **Paged storage with explicit whole-game checkpoint semantics.** Checkpoint before
  the bounded transaction capacity is exhausted, particularly before/within PC
  sessions. The PC controls can remain familiar, but quitting without manually saving
  would no longer undo changes already checkpointed. Transactions must include party,
  held items, inventory, world state and PC changes together; PC-only autosaves risk
  duplication or loss. Individual operations, auxiliary-data allocation, latency,
  and wear still need integration tests. This behavior change needs an owner decision.
- **Preserve unrestricted classic manual-save rollback.** Continue bounded packing/
  save-layout research, including all auxiliary features and worst-case distinct
  records. Do not quietly reduce boxes, strip data, accept a save that can fail when
  full, use emulator-only larger flash, or weaken recovery while calling it complete.

The recommendation to prototype pages was useful: it demonstrated a concrete
capacity/transaction tradeoff. Adoption of automatic checkpoints has **not** been
approved. Keep the production save path unchanged until that choice is resolved.

## Integration inventory

[Storage access inventory](../gba/evidence/storage-access-inventory.json) lists
scoped source references at the current pin. It is an integration checklist, not
proof that every pointer alias has been audited.

- `pokemon_storage_system.c`: navigation loops mostly use the box-count constant,
  but direct array writes and borrowed mutable pointers need explicit dirty-page
  ownership. A one-page cache cannot silently invalidate a pointer retained by UI code.
- `chooseboxmon.c`: determines PC membership using a contiguous address range;
  paged storage requires an explicit origin/slot identity.
- `lottery_corner.c`, `script_pokemon_util.c`, and `debug.c`: whole-PC scans and
  direct record writes must use checked accessors rather than a resident array.
- Summary, ribbons, Pokenav and menu helpers borrow pointers returned by
  `GetBoxedMonPtr`; their lifetimes must be traced and converted to copies/pinned
  handles where required.
- `party_menu.c`: fusion records are also in PokemonStorage and must be included.
- `load_save.c`/`main.c`: storage relocation currently copies the entire storage
  block through the heap. Save pointers and relocation cannot retain that assumption.
- Deposits, withdrawals, moves, release, party swaps, held-item operations, capture
  overflow, daycare and trade interactions still need end-to-end tests. Existing
  prototype tests do not establish their correctness in a 30-box PC interface.
