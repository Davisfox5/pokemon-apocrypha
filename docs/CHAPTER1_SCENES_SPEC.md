# Chapter 1 — Scene Spec (single source of truth)

This is the **authoritative desired end-state** for every Chapter 1 scene. I implement
toward this and test against it; you tick the checklists. When something's wrong, change
the spec line (or drop a screenshot/save-state) rather than re-describing in prose — the
spec is what prevents me from silently overwriting an earlier-agreed behavior.

**Status key:** ✅ verified in-game · 🔧 implemented, unverified · ❌ known-broken · ⬜ not built
**Coords:** global world tiles, `(x, z)`; z increases **south**. Dir: 0=N,1=S,2=W,3=E.
**Engine rules that bite us (keep in mind for every scene):**
- Scene/coord scripts re-check **every frame** while `var==value` → always bump the gating var before the script ends, or it re-fires forever.
- `hide_person` deletes the object **and sets** its eventFlag; `show_person` won't recreate it while the flag is set → reveal order is **`clearflag` → `show_person`**.
- To place a *hidden* actor: `move_person` (sets spawn default) **before** `show_person`. To move a *live* actor: `move_person_facing`. A just-`show_person`'d object isn't active the same tick — don't `move_person_facing` it immediately.
- **Never** `move_person_facing obj_player` — it teleports onto an unloaded chunk = black "Mystery Zone". Position the player by branch-walk, camera-focus (`scrcmd_102`/`103`), or a same-map `warp`.
- Every movement-table label needs `.balign 4, 0` above it or `wait_movement` hangs.
- Field `fade_screen` darkens the message box too → **no readable text on a black screen** from a field script (needs `oaks_speech` C work).

---

## RAM test hooks (how each scene is auto-verified)
`tools/emu_ram.py`: `var(emu, id)`, `loc(emu)` → `{mapId,x,z,dir}`.
- `VAR_SCENE_PLAYERS_HOUSE_1F = 0x4106` — opening progression.
- `VAR_SCENE_CHERRYGROVE_CITY_OW = 0x4073` — Cherrygrove scene progression.
- `MAP_PLAYER_HOUSE_1F = 63`, `MAP_PLAYER_HOUSE_2F = 64`, `MAP_CHERRYGROVE = 67`.

---

## OPENING

### O-1 · Cold open (house 1F)  — `scr_seq_T20R0201_000`, fires on new game (`HOUSE_1F`==0)
**Intent:** start black → narration "…" / "Honey, wake up" / "our new home" on black → brighten to the house → Mom's Kalos lines → "go upstairs and set up your PC." Player + Mom by the door.
**End state:** `HOUSE_1F` var = 1; player free in house (map 63); Mom on door tile (3,10).
- [ ] 🔧 Screen **starts black and fades up** — no house "flash", no fade-to-black. *(field-only kills the flash; true start-black needs the oaks_speech C path)*
- [ ] ❌ The "…" / "wake up" / "our new home" lines appear **as readable text on the black screen** *(BLOCKED: needs `oaks_speech.c` narration states — see O-1b)*
- [ ] 🔧 After brighten: Mom's "Kalos / new region / fresh start" + "go upstairs, set up your PC" play, visible.
- [ ] 🔧 Mom stands **on the door tile (3,10)**, facing into the room.
- [ ] 🔧 Player cannot leave town until the Pokégear hand-off (Mom on door blocks the exit).
- [ ] auto: `var(HOUSE_1F)==1` and `loc().mapId==63` after the scene.

### O-1b · (BLOCKED) text-on-black narration — requires C work in `src/oaks_speech.c`
Add narration states using `OakSpeech_PrintAndFadeCenteredFullScreenText` (white-on-black, kind=0) before the field hand-off, and leave the screen black so the house fades up clean. Needs new MainState enum values + message strings in a msg NARC + overlay rebuild. **Deferred until you greenlight the intro C edit.**

### O-2 · Upstairs 2F + PC Potion — `scr_seq_T20R0202_000`
- [ ] 🔧 First PC use gives a **Potion** (once; flag-guarded).
- [ ] 🔧 Using the PC sets `HOUSE_1F` var = 2 (arms the return Pokégear scene).

### O-3 · Return downstairs: Pokégear hand-off ("scene two") — `scr_seq_T20R0201_007`, fires `HOUSE_1F`==2
- [ ] 🔧 Mom moves to the tile just **north of the player**, both facing each other (player faces north).
- [ ] 🔧 Gives Bag + Options + **Pokégear** (Trainer Card / Save deferred to naming).
- [ ] 🔧 Safety net: talking to Mom gives the Pokégear if it was somehow missed.
- [ ] 🔧 Sets `HOUSE_1F` var = 4; player free; Mom no longer blocks the door.

---

## SCENE 1 · Silver in Cherrygrove — `scr_seq_T21_012`, coord fires `CHERRYGROVE_OW`==0

**Intent:** the player walks out, watches Champion Silver beat Gold in a friendly battle, meets Kestra (the loud Silver-worshipper) for the first time, is **named**, and Kestra runs off north.
**Actors:** Gold (557,403, stays), Silver `gsrivel` (556,403), Murkrow `silverbird`, Kestra `friend` (spawn 553,401), crowd `gsboy1`/`gsbigman`.
**End state:** `CHERRYGROVE_OW` = 1; Silver+Murkrow gone; **Gold stays visible/interactable**; Kestra gone (ran north); player named.

- [ ] 🔧 The player **reliably sees the Gold/Silver battle** (camera focuses on it; `scrcmd_102 556,403`).
- [ ] ❌→🔧 The player ends **on the tile directly south of Kestra**, facing her. *(now: Kestra is moved to the tile just north of the player off-camera; verify the player isn't left in a weird spot)*
- [ ] 🔧 **Kestra faces the player** when she talks to him.
- [ ] 🔧 Crowd (2 onlookers) react to the battle with real lines.
- [ ] 🔧 Player turns to Kestra **the instant Silver flies off** (before her first line to him), not at the "manners" line.
- [ ] 🔧 The **naming screen** appears during her first-meeting line, and the field returns cleanly after (no black screen).
- [ ] 🔧 Get-to-know-you dialogue (mostly Kestra, fast), using the entered name.
- [ ] 🔧 **Kestra runs off north**; **Gold remains standing and interactable** (his _011 "setting out" line). *(was: Gold wrongly warped away)*
- [ ] auto: after the scene `var(CHERRYGROVE_OW)==1`, `loc().mapId==67`, and the run didn't freeze (var advanced, screen not stuck-black).

---

## SCENE 2 · North-grass rescue + starter ceremony

### S2-A · Rescue — `scr_seq_T21_013`, coord fires `CHERRYGROVE_OW`==1 (north grass)
**Intent:** find Kestra calmly searching the grass → she excitedly spots a wild mon → Gold rushes in a beat too late → a real catching demo. The kids have no Pokémon, so Gold handles it.
**Actors:** Kestra `friend` (→548,385), wild Rattata `wildmon` (549,385), Gold (→548,387).
**End state:** wild mon caught/gone; `CHERRYGROVE_OW` = 2; warp to (557,404) for the ceremony.

- [ ] ❌→🔧 **Kestra is visible**, searching the grass. *(fix: `move_person` before `show_person`)*
- [ ] 🔧 The wild Rattata appears (ideally emerging, not popping in place).
- [ ] ❌→🔧 **Gold is visible** when he rushes in. *(fix: he's live in town; hide→set→show recreates him at the grass robustly)*
- [x] 🔧 A real **catching demo battle** occurs (`catching_tutorial`). *(RESOLVED 2026-07-05: scene lives on Route 30 as `scr_seq_R30_012`; the engine demo runs rebadged as Gold, who has NO Pokémon — TUTORIAL|SAFARI staging in `BattleSetup_New_Tutorial` gives a mon-less battle (no send-out, no enemy turn), the TUTORIAL bit forces the catch (4 shakes in `ov12_02247228`), the single Poké Ball throw is auto-injected in `BattleControllerPlayer_SelectionScreenInput` (no menu/finger), and subscript 275 + `SafariThrowBall` re-skin it as a plain Poké Ball. Name row `msg_0375_R30_00022` = "Gold"; backsprite stays the opposite-gender hero, consistent with Gold's SPRITE_HEROINE overworld placeholder.)*
- [ ] auto: `var(CHERRYGROVE_OW)` goes 1→2; the rescue didn't freeze.

### S2-B · Outdoor starter ceremony — `scr_seq_T21_014`, coord fires `CHERRYGROVE_OW`==2 at (557,404)
**Intent:** Gold's begrudging "tour", Kestra badgers him into giving starters, the player picks, Kestra grabs the type-advantage counter and runs off; Gold gives Running Shoes + Map Card.
**End state:** `FLAG_GOT_STARTER`; Running Shoes + Map Card; `CHERRYGROVE_OW` = 3.
- [ ] 🔧 Both kids + Gold are placed correctly (during the black, before fade-in).
- [ ] 🔧 `choose_starter`; Kestra takes the type-advantage counter (`VAR_APOC_FRIEND_STARTER`).
- [ ] 🔧 Gold gives **Running Shoes + Map Card** (live grant path).
- [ ] auto: `flag(GOT_STARTER)` set; `var(CHERRYGROVE_OW)==3`.

---

## House aesthetics
- [ ] 🔧 1F interior swapped to a different existing room model (gof_02). *(verify: collision unchanged, but if the visible door/walls don't line up you'll see walk-through-wall weirdness — one-byte revert if so)*
- [ ] ⬜ "Just moved in" boxes — **no usable box sprites exist in-engine**; needs new assets or a custom-dressed room model.

---

## Deferred / needs-decision (not silently dropped)
- **O-1b** text-on-black narration → `oaks_speech.c` C edit (your greenlight).
- **S2-A** catch fidelity → engine demo (have now) vs custom "Gold catches" cutscene (C).
- **House boxes** → new sprite/model assets.
- Scenes 3–4 (Route 29/New Bark/Elm Pokédex; catching tutorial + Mom goodbye) → not built.
