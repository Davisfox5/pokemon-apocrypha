# Separate Johto editing project — staged, not handed over

Project: `/Users/davisfox/Documents/GitHub/apocrypha-johto-editor`.
Branch: `codex/johto-editor-consolidation`.
Original checkout and running editor remain untouched.

- Latest selected outdoor sources consolidated: New Bark, Cherrygrove, Violet,
  Routes 29, 30, 31, 32, 33, and 36. Three current Union Cave floors copied without
  artwork changes so their existing data remains represented.
- Native Porymap exports match decoded pixels on all 12 maps/floors. All nine
  outdoor maps match their pinned previews apart from 47 exact owner edits.
- Prior 34 owner Route30 edits were already integrated. Five remaining dirt/grass
  overlaps are pending an explicit choice. The full 86-edit original is preserved.
- Existing map numbers preserved. Route29/30 primary banks isolated to avoid
  cross-map changes. No ROM/runtime validation of this combined project yet.
- The intermediate shelf inventory was moved to `/tmp/johto-consolidation-shelf-draft`;
  it predates owner edits and must be regenerated before installation.
- Full selector/foreground cleanup is still outstanding. This step resolves map
  source versions safely; it does not claim all old assets are already cleaned.

`verify_consolidation.py` checks decoder/native equality and source/owner pixels.
`consolidate.py` builds the isolated project from pinned commits; `carry_owner_edits.py`
rejects overlaps and requires exact native art/attributes before carrying a cell.
