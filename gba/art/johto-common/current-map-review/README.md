# Current Johto map review — source reconciliation

Owner correction, 2026-10-17: the shared-art rollout did not constitute an HGSS
tile-by-tile review, and its seven-map inventory included outdated versions.
The completed Route 36 is preserved. The remaining maps require review against
their original references, current authored layouts, and approved shared assets.

## Verified source inventory

Remote branch heads were fetched on October 17. Exact commits, layout dimensions,
and layout hashes are in [source-inventory.json](source-inventory.json).
These are separate source branches, **not a merged or fully reviewed game**.

| Map | Current review source | Special handling |
| --- | --- | --- |
| New Bark | `8d5efde191` | 36×53, including northern forest expansion and latest housing/mailbox changes |
| Route 29 | `6f7661e9ee` | Later HGSS reconstruction, supersedes the older rollout layout |
| Cherrygrove | `698db52a18` | Retain approved B/C/E town and shared service buildings |
| Route 30 | `aa8ea35eea` plus local edits | 34 uncommitted changed map cells in `apocrypha-src`; preserve and review these too |
| Route 31 | `698db52a18` | Review old terrain and receiving gate orientation against HGSS |
| Violet | `698db52a18` | Preserve approved custom architecture and city expansion |
| Route 32 | `7049fd5d8b` | Compare later `48cefd3d` cleanup separately; its PR11 is closed without merge |
| Route 33 | `eb15d89234` | Newer concurrent R02 terrain review; intentionally tree-free. The earlier image in this snapshot is superseded |
| Union Cave 1F | `fc1017feca` | Actual 34×60 floor; not the former entrance stub |
| Union Cave B1F | `fc1017feca` | Include basement wall, stair and water review |
| Union Cave B2F | `fc1017feca` | Include basement wall, stair and water review |
| Route 36 | `5b80e625d1` | Completed and owner-approved; preserve |

Connecting gates, doors, route adapters and cave thresholds belong to their
parent-map review. Existing interiors are not automatically approved by this
exterior inventory. This reconciliation itself did not alter native maps. Subsequent rock-face edits and verification are recorded in `../rocks/regional-rollout/README.md`.

## Preserve the ten-year changes

HGSS is the reference for terrain structure, materials and retained geography.
It is not an instruction to restore every map to its historical state. Maintain
an adaptation entry for each approved difference and its affected area before
changing that area. Current explicit preservation requirements:

- **New Bark:** accepted original laboratory design, expanded campus and housing,
  later house arrangement, mailbox placement, paths and forest expansion.
- **Cherrygrove:** approved expanded B/C/E town, harbor, dock and shipyard, mixed
  housing and colors, shared Center/Mart, and exclusive pink large trees.
- **Violet:** university replacing the two former buildings, repurposed gym as
  the lecture hall, approved architecture/roof/perspective, additional housing,
  teaching arena, and shared Mart/Center. Do not restore the original gym or
  remove the campus to match the historical screenshot.
- **Route 29:** retained coastal ridge, lookout and town adapters; these are
  documented intentional departures from the HGSS lower forest.
- **Route 30:** approved complete-tree footprint adaptations and Cherrygrove
  connector; account for the local 34-cell edit before any installation.
- **Route 32:** documented complete-tree and wider shared Center adaptations.
- **Route 36:** approved owner-marked three-level terrain, walls, stairs,
  gate placements and complete backgroundless trees are the accepted result.

This list is a starting register, not an exhaustive claim about narrative canon.
Consult each area's current source notes and relevant DESIGN.md section before
changing an unexplained difference. Do not invent additional time-lapse changes.

## Review status

Source reconciliation is recorded. The full native/HGSS cell review and fixes
remain pending. Prior rollout before/after sheets and passing traversal tests
do not establish HGSS visual fidelity or owner acceptance. Each area's next
review must identify individual cells and contextual joins, preserve intentional
adaptations, inspect actual native output, and verify affected movement/warps.
