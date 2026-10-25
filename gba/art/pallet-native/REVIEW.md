# Native visual and spatial review

Coordinates below refer to the receiving native metatile grid. Original FRLG
material/traversal grids remain independent in each map's `source/` folder.
The spatial revision is deliberate; it is not represented as original collision
parity. Every map has reference/current numbered sheets and before/after images.

| Map / coordinates | Review and correction |
| --- | --- |
| Town, homes (5–12,7–12), (23–30,7–12) | Whole meshes use a consistent projection. No horizontal strip squeezing. Native roof/facade palette families preserve the gable, windows, sill and posts. Both homes share the same architecture. |
| Town, doors (7,12), (25,12), (25,23) | Visible 16×24 panels coincide with animated door metatiles and preserve the surrounding jamb pixels. Checked both entry and return. |
| Town, yards (4–13,13–15), (22–31,13–15) | Full two-cell gateways, separate flower strips and mailboxes. Paths meet the door baseline. Pickets retain whole post heads. |
| Town, paths (17–18,0–18), (4–31,16–18) | Ground surfaces are separate from foreground. Intersections and concave corners have a narrow grass/gravel seam. A wider east–west crossing serves the three building approaches. |
| Town, garden (5–13,21–27) | Flower beds, rear pickets and a walkable perimeter retain the southwest FRLG landmark. The memorial is approached from the south. |
| Town, lab (21–29,19–23) | Complete roof, skylights, machinery and facade. The forecourt leaves side clearance and a direct entrance path. |
| Town, inlet (10–20,30–35) | Rounded north corners and continuous stone lip. Pure water tiles animate together. The extended camera border carries the shoreline south; all off-map exits stay blocked. |
| Town, perimeter | Complete shared Cherrygrove trees. Two-by-two root beds do not overlap; crowns layer north to south. Shared canopy colors are protected during palette cleanup. |
| Red 1F, (2–15,3–11) | Kitchen, dining furniture, sofa, coffee table and plants have separate footprints. The quiet rug and floor retain their own surface identity. |
| Red 1F, staircase (13–15,2–4) | Full HGSS tread/side-wall patch toned to the room. Walkable approach and eastward stair behavior coincide with the visible landing at (15,3). |
| Red 2F, (2–13,3–10) | Bed, storage, desk/chair, console and plant are complete. The landing at (13,3) retains westward return behavior. Reviewed both directions in motion. |
| Oak home, (2–16,3–11) | Reading furniture and dining area have distinct circulation space. The second bookshelf no longer intersects the TV. Oak remains accessible at (12,10). |
| Lab, rear and front cabinets | Cabinet origins have a four-pixel separation. The final right-hand cabinet ends before the side wall. Planters moved away from cabinet bases into clear side spaces. |
| Lab, center (8–12,7–16) | Continuous circulation from exit mat to Blue, around both work zones. Research machine/table are complete rather than squeezed into unrelated furniture silhouettes. |
| Oak/Blue actual gameplay | The existing sprite definitions were excluded by an FRLG-only compile guard. Enabled only these two definitions for Emerald, retaining their graphics IDs and source art. Runtime now requires a valid graphics pointer, a visible active sprite, and all 15 original opaque palette colors before dialogue. |
| All room boundaries | Continuous plaster, lower wall trim, side/front caps and exit mats. No orphan marker tiles at former warps. Furniture palettes and floor palettes remain separate. |

Actual native decoding and Porymap output are compared pixel for pixel. Native
cell collision/elevation/behavior are compared with the separately authored
receiving ledger. Runtime records cover walking, all transitions, interactions,
blocked edges, Surf/dismount, animation, saves, cold reload and title Continue.
These checks support review; owner visual acceptance is still pending.
