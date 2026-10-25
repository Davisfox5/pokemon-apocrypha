# Native visual review

Review scope: the 24×20 exterior, Red house 13×10 / 12×9, Oak house 13×10, laboratory 13×14; every numbered reference/native square, actual Porymap exports and headless gameplay. Final source and ROM identities are in preservation.json/build.json. Owner acceptance is pending.

| Area | Coordinates / checks | Result and correction |
|---|---|---|
| Whole exterior | x0–23/y0–19 | Original lawn/water/building/tree/fence materials tracked independently of traversal. FRLG layout retained; HGSS art changes and roof overhang declared. No screenshot collision claims. |
| Forest | x0–1, x22–23; north y0–1; south x2–5/x18–21 at y19 | Complete shared trees; distinct 2×2 roots, supported crown overlap, aligned repeated forest border. Southern crowns do not turn the open FRLG clearing into a forest. No random rock fill. |
| Lawn | All open squares; garden x4–10/y11–15 | Removed square light-lawn decals; retained accepted lawn grain with the original receiving rim and coherent light ramp. Ground is separate from canopy/foreground. |
| Homes | x5–9 and x14–18/y3–7; doors (6,7)/(15,7) | Converted original HGSS gables, walls/windows and mailboxes. Local door-width fit keeps full panels in actual warp columns. Closed/native animation pixels preserved. Roof overhang is explicit. |
| Laboratory exterior | x13–19/y9–13; door (16,13) | Complete cap, roof, chimney, wall and window outline. Model door fitted to the receiving entrance; no FRLG animation painted on HGSS art. |
| Shore | x7–10/y17–19; both top corners | Original receiving water/rock mask, HGSS water and coherent native lip. Foot cannot enter water; Surf movement and dismount checked. Southern geographic continuation remains unwired. |
| Flowers, fence, signs | x5–9/y11–14; x13–18/y16 | HGSS flowers keep leaves with their plain-lawn background removed. Coherent native fence grain/rails; signs sit at original event coordinates. No character-obscured donor patches. |
| Red house 1F | Whole map; x4–9/y3–6 table; stair x10/y2 | Full table/chairs/rug and wall joins. Fixed foreground carpet that covered the player's feet by restoring covered interior layers. Restored actual original black void cells below exit mat. |
| Red bedroom | Whole map; x8–10/y1–3 stairs | Bed, PC/desk, shelves and console use HGSS room models. Actual directional up-right/down-left stair behavior checked in both directions, including entering and leaving the visible landings. |
| Oak house | Whole map; table, plants, exit | Complete HGSS plant silhouettes including pots; retired Oak visible over carpet. Door return and save/Continue checked. Original bottom void restored. |
| Laboratory interior | Whole map; x0–4/x8–12/y7–9 shelves | Complete cabinet tops and front faces; repaired previously missing top course. Filled original left book-stack footprint (0,3–4), retained rear desk footprint, and aligned all receiving joins. Dedicated lab primary fits the original families without cross-material tile substitution. |
| Palette reduction | Every map, all native quadrants | Transparency excluded from foreground color budgets; shared source ramps stay consistent. Native art matches converted source at RGB555; ROM/VRAM/palettes checked independently. |
| Transitions and saves | All three building doors, both stair directions; every floor | Three actual native animation sequences inspected; no stale FRLG door art. Normal saves/cold reload/Continue checked in separate emulator processes. |

Remaining limits: static water; Route 1/21 and campaign acquisition/unlocks are unwired; dialogues and model-footprint adaptations are proposals for owner review. Existing shared maps, mechanics, IDs and saves are preserved. Passing checks is not visual acceptance.
