# Qualify 30-box persistence

**Progress (2026-09-10):** the [isolated page-store prototype](GBA_STORAGE_PROTOTYPE.md)
passes 900-record and interrupted-transaction tests. Its seven-page commit bound
does not yet meet unrestricted manual-saving behavior. Production remains at
14 boxes. The owner deferred this investigation on 2026-09-10; automatic checkpoints
are not approved. See the prototype document for deferred questions. Continue with
the classic-mechanics configuration audit; this storage requirement remains open.

The GBA toolchain and 14-box baseline pass. Keep the approved **30 boxes / 900
slots** and familiar PC interaction; do not silently lower the target. Read
[GBA_BASELINE.md](GBA_BASELINE.md) for measured evidence, then the relevant engine
save/storage files. No maps or new art are needed for this task.

## Required result

A documented storage design and executable prototype that preserves full supported
Pokemon records in all 900 slots, saves to the intended GBA save medium, reloads
across emulator restarts, and has a tested interrupted-write recovery strategy.
An emulator savestate is not a game save. Measure worst-case encoded size, maximum
resident RAM, temporary buffers, and save/load time rather than relying on an empty
PC or repeated identical Pokemon compressing well.

Current benchmark: 80-byte boxed records; 72,704 bytes for the naive 30-box storage
structure; only 35,712 bytes in the current storage save allocation. Naively
expanding resident storage also exceeds static EWRAM by 2,752 bytes. SaveBlock1,
SaveBlock2, and SaveBlock3 have distinct sector constraints, not one interchangeable
pool of free bytes. The legacy format occupies 128 KiB of flash with two save slots.

## Investigation order

1. Inventory stored fields and every direct PC-array access, including deposit,
   withdrawal, moves, release, naming/wallpaper, capture overflow, daycare, trade,
   fusion, and saveblock relocation. Preserve canonical data and current game
   requirements; disabled feature data is not automatically safe to delete.
2. Compare bounded lossless record packing with paged storage plus transactional
   updates/journaling on the existing flash medium. Consider cache/heap lifetimes
   and write wear. Explain atomicity, backups, and worst-case journal size. Do not
   assume generic compression always makes 900 distinct fully populated records fit.
3. Use a versioned, explicit save schema and stable identifiers. Establish behavior
   for foreign/older saves; never silently reinterpret, truncate, or reset them.
   Baseline test saves are disposable fixtures, not a released compatibility promise.
4. Implement the smallest nonvisual prototype that proves the chosen storage path.
   Keep PC menus recognizable. Test every slot, particularly box 30/slot 30, plus
   party-to-PC transfers, first/last boundaries, capacity-full handling, repeated
   saves, and multiple fresh-process reloads.
5. Interrupt writes at meaningful erase/program/commit boundaries and verify
   recovery to a valid complete transaction. Include damaged save/checksum cases.
   Document any changed recovery guarantees explicitly before calling it qualified.
6. Report measured ROM/RAM/flash usage, latency, pass/fail evidence, and the exact
   follow-up needed for production. Then integrate campaign state and the custom
   types against the established schema.

No platform reversal is authorized. If a hard requirement fails, investigate GBA
remedies and document reproducible evidence before the owner considers a fallback.
