# Pokemon Apocrypha — Chapter 1 Implementation Design

**Maps:** Cherrygrove City (T21), Player House (T20R0201), Gold's House (T21R0401, formerly the Guide-Gent house), Route 29 (R29), New Bark Town (T20), Elm's Lab 1F (T20R0101).
**Badges:** 0. **Tone:** Classic Pokemon — warm, personal, safe, full of possibility. This chapter deliberately evokes the GSC opening before the story darkens.
**Status of this doc:** This is the single buildable spec. It reconciles the already-built-and-approved Scene 1 cutscene, fixes the mis-built Scene 2, and specifies everything still to build. All dialogue here is HG-charset-safe (curly apostrophes U+2019, no em dashes, no straight apostrophes; `\r` = wait-for-button/clear, `\n` = second line of box, `\f` = scroll within box).

---

## 1. Overview & how Chapter 1 seeds the whole-game arc

Chapter 1 is the "high-water mark of belief." The whole game's spine is **hero-worship → principled dissent**: Silver is the universally-adored Champion-redeemed-villain, and over five regions that image cracks. Chapter 1 must plant that worship as deeply and uncritically as possible so its later collapse has somewhere to fall from.

Three load-bearing things Chapter 1 establishes:

1. **Silver as untouchable idol.** The player never speaks to him. He wins a friendly battle, ribs his old rival Gold, and flies off over the town without so much as a glance at the kids. He is an *image*, not yet a character — exactly the mythology the late game will interrogate.
2. **Gold as mentor, not quest-giver.** Gold gives tools and encouragement, never a mission. He is the warm, grounded counterweight to Silver's distant glamour — and the person whose quiet contentment ("everything I need is right here") will later read as the wiser choice.
3. **The friend-rival, Kestra, as the future first voice of doubt.** She is introduced as the *loudest, most uncritical* Silver-worshipper in the game. Her impulsiveness (bolts to Violet before Gold finishes) and competitiveness (always takes the type-advantage counter-starter) are set here and scale into the Chapter 2 rival battle, the Chapter 4 Goldenrod "stay sensible" beat, and the late-game pivot where her gut feeling — "this doesn't add up about Silver" — becomes the narrative's questioning voice. The believer breaking faith first means more than a skeptic being right.

**Mechanical progression (the chapter's teaching arc):** see Silver → choose starter → first wild encounters (Route 29) → Pokedex (Elm) → catching tutorial + 5 Poke Balls (Gold) → mother's savings offer → depart north.

---

## 2. The friend-rival: KESTRA (committed)

- **Name:** Kestra. (A kestrel: a small, fast, restless falcon — "always a step ahead in action." Apocrypha-original, collides with no canon name and no other Apocrypha NPC, e.g. Ren the Violet foil.)
- **Gender/sprite:** Female, **SPRITE_GSGIRL2** (the GS-era Johto girl). Fixed female so her identity is stable across five regions regardless of the player's chosen gender, and so she never visually collides with SPRITE_HERO or SPRITE_HEROINE. *Fallback:* if SPRITE_GSGIRL2 collides with a placed NPC in a zone, use SPRITE_GSGIRL1. **Never** SPRITE_GSRIVEL — that is Silver.
- **Speaker prefix in dialogue:** `KESTRA:` (consistent across all maps). The vanilla rival self-intro line `msg_0550_T21_00015` ("You saw my name...") is Silver-rival flavor and must NOT be reused for her.

**Voice (one consistent register for all writers):** a kid running on pure enthusiasm — short bursty sentences, thinks out loud, answers her own questions, declares plans as if already done, gives the player friendly titles ("partner," "slowpoke," "champ-in-training"). She is competitive *with* the player, never *against* — her teasing is affectionate, never mean. She narrates the moment so narration boxes aren't needed. Verbal tics: (1) doubles a word for emphasis ("That. Is. SILVER."); (2) "Okay, new plan, we are SO going to..."; (3) the friendly title. **Critical for the long arc:** the same bursty cadence must later curdle into unease without becoming a different person — her late-game doubt is this voice pointed inward.

---

## 3. Gold's house decision + Cherrygrove geography/flow

**Gold's house = MAP_CHERRYGROVE_GUIDE_GENT_HOUSE (068_T21R0401, overworld warp 3 at 558,401).**

Why: In the built Scene 1, Gold stands at (557,403) — literally one tile from that house's door (558,401). It is the house he is standing outside of. It already holds the three starter-ball objects from the mis-build, so reuse minimizes new mapping.

**The Guide-Gent is deceased — removed from the world.** No overworld tour NPC, no Southeast-House relocation. **Gold inherits the onboarding tour**, delivered begrudgingly: a trimmed pass over the Poke Mart, Pokemon Center, and the map / running-shoes basics for the neighbor kids about to leave — he didn't sign up to be a tour guide, but he does it because he cares. Reassign the onboarding content (`scr_seq_T21_001` / `_002`, the old `obj_T21_gsoldman1` running-shoes/Pokegear tour) to Gold — fold it into a short, optional begrudging-tour talk on `obj_T21_gold` (or a one-time coord near the Mart/Center). **Remove** both the overworld `obj_T21_gsoldman1` and the interior `obj_T21R0401_gsoldman1` (the interior slot is reused by Gold — see Scene 2 Part B).

**Cherrygrove layout (from 064_T21.json warps):** Pokecenter (564,391), Pokemart (555,391), **Player House (547,399)**, **Gold's House (558,401)**, **Southeast House (567,405)**. Gold battles Silver at (557,403). The town's tall-grass route mouth is at the **north edge** (the existing `scr_seq_T21_002` coord band sits at x547,z385,w4,h1).

**Geography of the chapter loop:** Cherrygrove → (north) Route 29 → New Bark Town (Elm) → back south to Cherrygrove (Scene 4) → north again toward Violet. *Confirm the exact Cherrygrove↔Route 29 connection tile before wiring Scene 2/3 triggers (see Open Questions); the spec assumes the north-edge grass at ~x547,z385 is that mouth.*

**Scene-state variable, cleanly re-sequenced** (`VAR_SCENE_CHERRYGROVE_CITY_OW`, 0x4073). The legacy values (1/2 Guide-Gent map-card, 3/4 road-rival) belong to retired vanilla content; detach those legacy flows from this var. New canonical sequence:

| Value | Meaning |
|---|---|
| 0 | Fresh start; arms Scene 1 coord trigger |
| 1 | Silver gone; arms Scene 2 grass-block trigger |
| 2 | Starter chosen; free to head north to Route 29 |
| 3 | Returned from New Bark with Pokedex; arms Scene 4 farewell |
| 4 | Farewell + catching tutorial done; north exit fully open |

**New flags to allocate** (reuse free `FLAG_UNK_*` in the hide range): `FLAG_HIDE_CHERRYGROVE_FRIEND` (Kestra in town — use free 0x19A), `FLAG_HIDE_CHERRYGROVE_SILVER` (0x19E), `FLAG_HIDE_CHERRYGROVE_GOLD` (0x19F), `FLAG_APOC_R29_INTRO_DONE` (0x1A0), `FLAG_APOC_CATCH_TUT_DONE` (0x1A3), and define-only: `FLAG_APOC_MOM_GOODBYE_DONE`. Add a custom var `VAR_APOC_FRIEND_STARTER` (allocate a free 0x40xx) to persist Kestra's counter-starter species for later rival battles. **Reuse:** `FLAG_GOT_STARTER` (0x6A), `FLAG_GOT_POKEDEX` (0x6B), `FLAG_HIDE_ROUTE_29_FRIEND` (0x1A4), `FLAG_HIDE_ROUTE_29_MARILL` (0x1A5), `FLAG_HIDE_NEW_BARK_FRIEND` (0x1A2), `FLAG_HIDE_ELMS_LAB_ELM` (0x191), `FLAG_HIDE_ELMS_LAB_FRIEND` (0x1A6), `FLAG_SYS_MOMS_SAVINGS` (0x986).

**Hide-flag correction (built bug):** `scr_seq_T21_012` currently does `setflag FLAG_HIDE_CHERRYGROVE_RIVAL` while hiding `obj_T21_gsrivel` — but gsrivel is **Silver**. Retarget: Silver's hide → `FLAG_HIDE_CHERRYGROVE_SILVER`; `FLAG_HIDE_CHERRYGROVE_RIVAL` (0x19C) becomes Kestra's overworld hide flag. (A grep confirms 0x19C is only otherwise referenced by the retired `scr_seq_T21_003` road-rival flow.)

---

## 4. The four scenes

### SCENE 1 — Silver in Cherrygrove (reconcile + extend the built `scr_seq_T21_012`)

**Decision:** KEEP the approved battle-flavor, the Gold/Silver dialogue (msgs 26-32), and the Murkrow fly-off (`apoc_fly_away`, opcode 853) essentially verbatim. Only three narrative changes: (a) give Gold a non-player sprite; (b) add Kestra on-screen and give her the starstruck lines so awe is *voiced, not narrated*; (c) fix the Silver/Kestra hide-flag mix-up.

**Beat-by-beat staging:**
1. Player exits the Player House (warp at 547,399) into the plaza. Kestra is pre-placed a couple tiles off the exit path (e.g. 553,401) facing the battle; Gold (557,403), Silver (556,403), and the hidden Murkrow (556,403) are pre-placed mid-conversation to the east.
2. Coord trigger `_EV_scr_seq_T21_012` fires (var==0). `lockall`; `hide_person obj_T21_silverbird` (already built).
3. **Kestra recognition line** (NEW msg 33) — she whisper-shouts who that is.
4. Player auto-faces east (`_apoc_face_e`, built).
5. Gold's command (msg 26, kept).
6. Player edges closer to watch "from a distance" (`_apoc_approach`, built); optionally a 1-2 step parallel lean for Kestra.
7. Silver's command (msg 27, kept).
8. **Kestra reaction to the finish** (NEW msg 34) — awe that Silver took Gold apart.
9. Silver/Gold exchange (msgs 28-31, kept): Silver ribs rusty Gold; Gold content, no ego; Silver invites him back; Gold declines, happy in the quiet town.
10. **Kestra reaction** (NEW msg 35) — barely able to stand still.
11. Silver's exit (msg 32, kept).
12. `hide_person obj_T21_gsrivel` + `setflag FLAG_HIDE_CHERRYGROVE_SILVER`; `show_person obj_T21_silverbird`; `apoc_fly_away obj_T21_silverbird, SPECIES_MURKROW`. Silver lifts off and flies over town. He never looks at or speaks to the kids.
13. **Kestra aspirational button** (NEW msg 36) as the Murkrow disappears.
14. `setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 1`; `releaseall`. Kestra stays visible on the map (she runs to the grass in Scene 2).

**Full dialogue** (insert into `msg_0550_T21.gmm`; keep 26-32 as-is):

```
msg_0550_T21_00033 (KESTRA, recognition):
KESTRA: Wait. Wait wait wait.\rThat is GOLD’s house.\rAnd the one he’s battling -\rThat. Is. SILVER!\rThe CHAMPION is standing in our town!\r

msg_0550_T21_00026 (GOLD, KEEP):
GOLD: TYPHLOSION! Fire Blast, now!\r

msg_0550_T21_00027 (SILVER, KEEP):
SILVER: Alakazam. Psychic.\rEnd it.\r

msg_0550_T21_00034 (KESTRA, after the finish):
KESTRA: ...He didn’t even raise his\nvoice.\rGOLD is the strongest Trainer who\never lived, and Silver just -\rTook him apart.\r

msg_0550_T21_00028..00031 (SILVER/GOLD exchange, KEEP all four)

msg_0550_T21_00035 (KESTRA, hushed):
KESTRA: They’re just... talking.\nLike it’s nothing.\rTwo of the strongest people alive,\nright in front of us.\r

msg_0550_T21_00032 (SILVER exit, KEEP):
SILVER: ...Heh. Same old Gold.\rTake care of yourself.\rI’ve got a region waiting on me.\r

msg_0550_T21_00036 (KESTRA, as Murkrow lifts off — the button):
KESTRA: ...Did you SEE that?\rHe just - FLEW off. Like the whole\nsky belongs to him.\r{STRVAR_1 3, 0, 0}... one day that’s\ngoing to be us. I mean it.\rCome on. We are not standing in the\ngrass forever!\r
```

**Mechanics:** Reuse `scr_seq_T21_012` wholesale; insert four `npc_msg` calls (33 at beat 3, 34 at beat 8, 35 at beat 10, 36 at beat 13). Change line 894 `hide_person obj_T21_gsrivel` to pair with `setflag FLAG_HIDE_CHERRYGROVE_SILVER` (NOT `_RIVAL`). Change line 897 from `setvar ... 10` to `setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 1`. Keep `apoc_fly_away`. The buffer for `{STRVAR_1 3, 0, 0}` (player name) requires a `buffer_players_name 0` before msg 36.

**Map / NPC changes (064_T21.json):**
- `obj_T21_gold`: `spriteId SPRITE_HERO` → **`SPRITE_GSMIDDLEMAN1`** (NOTE: SPRITE_HERO_2 is player-only and CRASHES as an NPC; use a real NPC sprite) (HGSS's "other protagonist," reads as a real trainer who isn't the player; closest in-engine fit absent a custom adult-Gold sprite). Add `eventFlag FLAG_HIDE_CHERRYGROVE_GOLD` (shown for Scenes 1 & 4). Keep position (557,403), scriptId `_EV_scr_seq_T21_011 + 1` (his Scene-4 talk line).
- `obj_T21_gsrivel` (Silver): keep SPRITE_GSRIVEL, change `eventFlag` to `FLAG_HIDE_CHERRYGROVE_SILVER`.
- **ADD `obj_T21_friend`** (Kestra): SPRITE_GSGIRL2, position ~(553,401), facing east, `movement 0` (stationary), `scriptId 0` (no overworld talk during cutscene), `eventFlag FLAG_HIDE_CHERRYGROVE_RIVAL` (her hide flag). Add `obj_T21_friend = 8` to `event_T21.h` and bump `obj_T21_silverbird` accordingly (or append friend as index 8, silverbird stays 7 — append friend last to avoid renumbering: make friend index 8).
- Ensure ambient NPCs (gsboy1, gswoman1, gsbigman, Cameron) are clear of the `_apoc_approach` auto-walk tiles around (553-557, 401-403). They already are.

---

### SCENE 2 — The grass block + Gold's house starter ceremony

Two parts: a NEW overworld "Gold stops you" script (`scr_seq_T21_013`) and a fully REDESIGNED interior ceremony (`scr_seq_T21R0401_002`).

#### Part A — Overworld: Gold stops the kids (NEW `scr_seq_T21_013`)

**Beats:**
1. Player heads for the north-edge tall grass. Kestra is a step ahead (in character).
2. Coord trigger fires (var==1); `lockall`.
3. **Kestra** at the grass, eager (msg 37).
4. **Gold** hurries over and physically stops them (`move_person_facing`/`apply_movement` Gold beside the kids), msg 38 ("you can't go in there with no Pokemon").
5. **Kestra** deflates then rebounds (msg 39).
6. **Gold** beckons them to his house (msg 40).
7. Gold walks to his door (558,401) and `hide_person`; warp the player into MAP_CHERRYGROVE_GUIDE_GENT_HOUSE (anchor 3). `setflag FLAG_HIDE_CHERRYGROVE_FRIEND` (Kestra is escorted in; the interior has its own friend object).
8. Var stays 1 (the interior completes Scene 2).

**Dialogue** (append to `msg_0550_T21.gmm`):

```
msg_0550_T21_00037 (KESTRA, at the grass):
KESTRA: Okay - tall grass, wild\nPokemon, real adventure.\rWe just walk right in and -\r

msg_0550_T21_00038 (GOLD, stopping them):
GOLD: Whoa, whoa. Hold it right\nthere, you two.\rYou can’t go wandering into that\ngrass with no Pokemon of your own.\rA wild one out there won’t care how\nexcited you are.\r

msg_0550_T21_00039 (KESTRA, deflating):
KESTRA: ...Oh. Right. We don’t\nactually HAVE any Pokemon yet.\r

msg_0550_T21_00040 (GOLD, warm, beckoning):
GOLD: Heh. I remember that feeling.\rTell you what - come with me. Both\nof you. My house is right here.\rI’ve got something for a couple of\nTrainers just starting out.\r
```

**Mechanics:** New `scr_seq_T21_013` (add `scrdef scr_seq_T21_013` to `scr_seq_0850_T21.s` and `#define _EV_scr_seq_T21_013 13` to `event_T21.h`). Body: `scrcmd_609`; `lockall`; `npc_msg 37`; `apply_movement obj_T21_gold` toward the kids; `wait_movement`; `npc_msg 38`; `npc_msg 39`; `npc_msg 40`; `closemsg`; `apply_movement obj_T21_gold` into door + `hide_person obj_T21_gold`; `setflag FLAG_HIDE_CHERRYGROVE_FRIEND`; warp player to MAP_CHERRYGROVE_GUIDE_GENT_HOUSE anchor 3; `end` (var held at 1). NEW coord entry in 064_T21.json: gate on `VAR_SCENE_CHERRYGROVE_CITY_OW == 1`, a 1-tile band across the grass mouth (reuse geometry near x547,z385,w4,h1), scriptId `_EV_scr_seq_T21_013 + 1`. **Note:** the legacy coord at x547,z385 currently points to `_EV_scr_seq_T21_002` gated val=1 — repoint it to the new Scene-2 script and detach the Guide-Gent map-card flow to its own gating.

#### Part B — Interior: the starter ceremony (REDESIGN `scr_seq_T21R0401_002`)

**Beats:**
1. Player enters; Gold stands behind three Poke Balls with his **Typhlosion resting nearby** (the same partner that battled Silver outside); Kestra beside the player, vibrating with impatience.
2. **Gold** intro (msg 00000, replaced): these are the three Elm let him choose from years ago; player picks first.
3. **Kestra** protests good-naturedly (msg 00003).
4. Player interacts with a ball → `choose_starter` (offers all three; confirm one).
5. On confirm: `FLAG_GOT_STARTER` set; follower-mon setup preserved; species stored via `set_starter_choice`.
6. **Gold** reacts warmly (msg 00004).
7. **Kestra** grabs the **type-advantage counter** (Chikorita→player ⇒ Kestra Cyndaquil; Cyndaquil→player ⇒ Kestra Totodile; Totodile→player ⇒ Kestra Chikorita), declaring it the smart pick (msg 00005). Her species stored in `VAR_APOC_FRIEND_STARTER`.
8. **Gold** sends them both to Elm for a Pokedex (msg 00006).
9. **Kestra** bolts for the door first (msg 00007), `apply_movement` to door + `hide_person`.
10. `releaseall`; `setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 2`.

**Dialogue** (rewrite `msg_0554_T21R0401.gmm`; keep 00001 item-get and 00002 re-entry guard):

```
msg_0554_T21R0401_00000 (GOLD intro, REPLACES Guide-Gent text):
GOLD: Years back, Professor Elm let me\npick my first partner from three.\rI never could bring myself to part\nwith the other two.\fGo on, {STRVAR_1 3, 0, 0}. You choose\nfirst.\rCyndaquil. Totodile. Chikorita.\rWhichever one feels right.\r

msg_0554_T21R0401_00003 (KESTRA, impatient):
KESTRA: Hey - why does {STRVAR_1 3, 0, 0}\nget to pick first?\r...Fine. Fine. Go ahead.\rJust leave me a good one, partner.\r

msg_0554_T21R0401_00001 (item-get, KEEP):
{STRVAR_1 3, 0, 0} received the\n{STRVAR_1 0, 1, 0}!

msg_0554_T21R0401_00004 (GOLD reacts):
GOLD: Good choice. Take care of it,\nand it’ll take care of you.\r

msg_0554_T21R0401_00005 (KESTRA grabs the counter; {STRVAR_1 0,1,0} = her species name):
KESTRA: Then I’m taking THIS one.\rType advantage, right out of the gate.\nNothing personal.\r{STRVAR_1 0, 1, 0}? You’re mine.\rDon’t come crying when I beat you\nwith it, partner.\r

msg_0554_T21R0401_00006 (GOLD sends them to Elm):
GOLD: Ha! There it is. You two are\ngoing to push each other a long way.\rNow - if you’re serious about this,\ngo see Professor Elm in New Bark Town.\rHe’ll set you each up with a Pokedex.\rNo real journey starts without one.\r

msg_0554_T21R0401_00007 (KESTRA bolts):
KESTRA: New Bark, got it!\rLast one there’s a SLOWPOKE!\r

msg_0554_T21R0401_00002 (re-entry guard, KEEP):
You’ve already chosen your\npartner. Take good care of it!\r
```

**Mechanics (rewrite of `scr_seq_T21R0401_002`):**
```
play_se SEQ_SE_DP_SELECT
lockall
goto_if_set FLAG_GOT_STARTER, _already
buffer_players_name 0
npc_msg 00000
npc_msg 00003
choose_starter
setflag FLAG_GOT_STARTER
scrcmd_605 3, 2            ; (follower setup, preserved from build)
toggle_following_pokemon_movement 0
scrcmd_608
wait 10, VAR_SPECIAL_RESULT
toggle_following_pokemon_movement 1
get_partymon_species 0, VAR_TEMP_x4001
set_starter_choice VAR_TEMP_x4001
buffer_mon_species_name 1, 0
npc_msg 00001
play_fanfare SEQ_ME_POKEGET
wait_fanfare
npc_msg 00004
; --- counter-pick: compute Kestra's species into VAR_APOC_FRIEND_STARTER ---
compare VAR_TEMP_x4001, SPECIES_CHIKORITA
goto_if_eq _friend_cynda
compare VAR_TEMP_x4001, SPECIES_CYNDAQUIL
goto_if_eq _friend_toto
setvar VAR_APOC_FRIEND_STARTER, SPECIES_CHIKORITA   ; player took Totodile
goto _friend_named
_friend_cynda: setvar VAR_APOC_FRIEND_STARTER, SPECIES_CYNDAQUIL
goto _friend_named
_friend_toto:  setvar VAR_APOC_FRIEND_STARTER, SPECIES_TOTODILE
_friend_named:
buffer_species_name 1, VAR_APOC_FRIEND_STARTER, 0, 0   ; names her starter for msg 00005
npc_msg 00005
hide_person obj_T21R0401_ball-of-player-pick   ; (or hide all three balls after pick)
hide_person obj_T21R0401_ball-of-friend-pick
npc_msg 00006
apply_movement obj_T21R0401_friend, _to_door
wait_movement
hide_person obj_T21R0401_friend
npc_msg 00007                                   ; (or before the movement, designer choice)
closemsg
releaseall
setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 2
end
_already:
npc_msg 00002
closemsg
releaseall
end
```
*Note on `buffer_species_name`:* signature is `buffer_species_name slot, species, arg2, arg3` and accepts a species id/var directly — this cleanly names Kestra's starter without the broken Platinum `buffer_dppt_friend_starter_species_name` (which always returns Turtwig in HGSS). `VAR_APOC_FRIEND_STARTER` also feeds later rival battles, mirroring how `get_starter_choice` already drives the retired road-rival branch.

**Map / NPC changes (068_T21R0401.json + event_T21R0401.h):**
- Replace `obj_T21R0401_gsoldman1` with **`obj_T21R0401_gold`** (**SPRITE_GSMIDDLEMAN1** — NOT SPRITE_HERO_2, which is player-only and crashes as an NPC; see §3 Scene 1) at ~(4,3) facing down, scriptId 0 (he speaks via the ball script / cutscene). Keep its index slot.
- **ADD `obj_T21R0401_typhlosion`** (Gold's partner) resting in the room during the ceremony — a static overworld-Pokemon object near Gold (~(3,3)), `movement 0`, scriptId 0 (optional flavor talk). Needs the Typhlosion follower/overworld sprite; if unavailable in-engine, flag for an asset pass or fall back to a placed `SPECIES_TYPHLOSION` follower-style object.
- **ADD `obj_T21R0401_friend`** (Kestra, SPRITE_GSGIRL2) at ~(5,5) facing left/up, scriptId 0.
- Keep `ball1/ball2/ball3` (SPRITE_MONSTARBALL) — all three route to `_EV_scr_seq_T21R0401_002 + 1` (interacting with any ball opens `choose_starter`). They become pedestal props; hide the taken ones after selection.
- Update `event_T21R0401.h` object indices accordingly.

**Guide-Gent removed (deceased):** Do not relocate him — remove the interior `obj_T21R0401_gsoldman1` (slot reused by Gold) and the overworld `obj_T21_gsoldman1`. His onboarding scripts (`scr_seq_T21_001/002`, msgs 0-12, 16) are **reassigned to Gold** as the begrudging tour (see §3). The Southeast House (069_T21R0501) keeps its existing residents; nothing new is added there.

---

### SCENE 3 — Route 29, first wild encounters, and Elm's Pokedex

Two sub-scenes: 3A on Route 29, 3B in Elm's Lab.

#### Scene 3A — Route 29 (first wild encounters)

**Beats:**
1. After Scene 2, player + Kestra leave Cherrygrove north into Route 29. Keep vanilla R29 encounter tables (low-level Pidgey/Sentret/Rattata, lv2-3 — short and safe).
2. Kestra walks the route as a companion NPC. A first-time-only coord trigger near the first grass patch fires a SHORT moment: she goads the player to test their starter, then peels off ("race you"). No forced battle — the player learns by walking into grass naturally.
3. She re-appears at the New Bark edge to walk in together (hide on R29 after the line, re-show at New Bark via flag).

**IMPORTANT:** Do NOT use the vanilla R29 `catching_tutorial` here — that tutorial belongs to Gold in Scene 4. Hide/remove the vanilla R29 tutorial NPCs (`obj_R29_var_2` = Elm's aide, `obj_R29_tsure_poke_static_marill`) at chapter start so the vanilla tutorial cannot fire. Repurpose `obj_R29_var_2`'s slot, or add a fresh Kestra object, using SPRITE_GSGIRL2 and a hide flag (reuse `FLAG_HIDE_ROUTE_29_FRIEND`).

**Dialogue** (new lines in the Route 29 msg file):
```
msg_apoc_r29_00 (KESTRA, first grass, once):
KESTRA: There it is. Tall grass.\rThis is the part Gold warned us about,\nhuh?\r...Forget warned. This is the part I’ve\nbeen waiting my whole life for.\rCome on - let’s see what that starter\nof yours can do!\r

msg_apoc_r29_01 (KESTRA, before peeling off):
KESTRA: First one to New Bark wins.\rLoser carries the bragging rights of\nthe loser. Which is none!\r
```

**Mechanics:** New coord trigger in the R29 overworld zone_event gated on `FLAG_GOT_STARTER` set AND `FLAG_APOC_R29_INTRO_DONE` unset; scriptId → new R29 sub-script. Body: `lockall`; `apply_movement` Kestra to face player; `npc_msg apoc_r29_00`; `npc_msg apoc_r29_01`; `apply_movement` Kestra north; `hide_person` + `setflag FLAG_HIDE_ROUTE_29_FRIEND`; `setflag FLAG_APOC_R29_INTRO_DONE`; `releaseall`. Re-point Cherrygrove's north warp ↔ Route 29's south warp and Route 29's north warp ↔ New Bark (verify exact map connection — Open Questions).

#### Scene 3B — Elm's Lab (Pokedex + Gold/Silver reminiscence)

**Beats:**
1. Player + Kestra arrive in New Bark (T20). The only meaningful destination is Elm's Lab (warp to MAP_NEW_BARK_ELMS_LAB_1F / 058_T20R0101). Optional flavor NPC: "Professor Elm is expecting you."
2. Enter the lab. Elm (`obj_T20R0101_doctor`, SPRITE_DOCTOR, gated by `FLAG_HIDE_ELMS_LAB_ELM` — cleared for this visit) stands center. Kestra walks in beside the player (reuse the lab's `var_1` friend object, set to SPRITE_GSGIRL2, `FLAG_HIDE_ELMS_LAB_FRIEND`).
3. Coord trigger just inside the door fires the one-time Pokedex scene: Elm greets warmly (Gold called ahead), gives EACH a Pokedex, brief orientation, then reminisces about Gold AND Silver — the "redemption" framing stated as universally-believed fact.
4. `give_pokedex`; `setflag FLAG_GOT_POKEDEX`; fanfare. (One engine give for the player; Elm's line covers Kestra's copy narratively.)
5. Elm finishes; nothing else to do. Kestra says they should head back and tell Gold. `setvar VAR_SCENE_ELMS_LAB, <done>`; exit. Walking back south transitions to Scene 4 (set `VAR_SCENE_CHERRYGROVE_CITY_OW, 3` on entering Cherrygrove from the north, gated on `FLAG_GOT_POKEDEX`).

**Dialogue** (new lines in Elm Lab 1F msg file — the T20R0101 file, NOT the wife's T20R0102):
```
msg_apoc_elm_00 (ELM, greeting):
ELM: Ah - you must be the two from\nCherrygrove.\rGold rang ahead about you. Said a pair\nof his neighbors had finally caught\nthe bug.\rHe was right to send you. A Trainer\nwithout a Pokedex is a Trainer walking\nwith their eyes closed.\r

msg_apoc_elm_01 (ELM, hands the Pokedex):
ELM: Here. One for each of you.\rIt records every Pokemon you meet and\nevery Pokemon you catch.\rThe more pages you fill, the more of\nthis world you’ll understand.\fThat’s the whole idea of it.\r

msg_apoc_elm_02 (system, after give_pokedex):
{STRVAR_1 3, 0, 0} received the\nPokedex from Professor Elm!\r

msg_apoc_elm_03 (ELM, orientation):
ELM: Check it whenever you see a\nPokemon you don’t know.\rIt fills its own pages. All you have to\ndo is go and look.\r

msg_apoc_elm_04 (ELM, reminiscence):
ELM: You know, the two of you remind me\nof someone.\rTwo more, actually.\rGold started out from a town just like\nyours. Walked into this lab not much\nolder than you are now.\rAnd the other one... well. You know him\nas the Champion.\r

msg_apoc_elm_05 (ELM, the redemption framing as fact):
ELM: Silver was a difficult boy back\nthen. Sharp edges. A chip on his\nshoulder the size of Mt. Silver.\rBut people change. He turned all that\nfire into something the whole world\ncould lean on.\rChampion. Protector. Proof that no one\nis only the worst day of their life.\fI’ve never been prouder of two\nstudents.\r

msg_apoc_elm_06 (ELM, send-off):
ELM: Go on, then. Your road’s waiting.\rAnd do an old professor a favor -\nfill those pages.\r

msg_apoc_elm_friend_00 (KESTRA, leaving the lab):
KESTRA: Did you hear that? The Champion\nstarted right here.\rSame lab. Same professor. Same dinky\nlittle Pokedex.\rThat’s gonna be us. I can feel it.\fCome on - let’s go tell Gold we’re\nofficially Trainers!\r
```

**Mechanics (Elm Lab 1F script — verify exact .s filename for T20R0101):** Add a coord-trigger sub-script gated on `VAR_SCENE_ELMS_LAB` with top guard `goto_if_set FLAG_GOT_POKEDEX, _skip`. Body: `lockall`; `apply_movement` Elm to greet; `npc_msg apoc_elm_00`; `closemsg`; `npc_msg apoc_elm_01`; `give_pokedex`; `setflag FLAG_GOT_POKEDEX`; `play_fanfare SEQ_ME_ITEM`; `wait_fanfare`; `buffer_players_name 0`; `npc_msg apoc_elm_02`; `npc_msg apoc_elm_03..06`; `closemsg`; `setvar VAR_SCENE_ELMS_LAB, <done>`; `releaseall`. At chapter-reaches-New-Bark init: `clearflag FLAG_HIDE_ELMS_LAB_ELM`, keep `FLAG_HIDE_ELMS_LAB_OFFICER` set (this is a calm visit, not the GSC Mr. Pokemon crisis), `clearflag FLAG_HIDE_ELMS_LAB_FRIEND`. Optional: register Elm to Pokegear if a `PHONE_CONTACT_ELM` constant exists; else skip.

**Map / NPC changes:** New Bark (057_T20): hide the GSC-opening crisis NPCs; redress flavor as a **busy research hub** (visiting-scholar NPCs, lab props/microscopes, a line or two about grants and Elm's institute) rather than a sleepy village; `obj_T20_var_1` → Kestra sprite. Elm Lab 1F (058_T20R0101): Elm present, Officer/aide absent; the lab reads as a serious **research institute**, but only Elm + the Pokedex beat are interactable — the deeper facility is **gated for a later return visit** (pass-through this chapter). Keep Chapter 1 clean: no Silph / visiting-corporate-lab presence here.

---

### SCENE 4 — Cherrygrove farewell + catching tutorial + mother

Three sub-scenes: 4A (Kestra bolts), 4B (Gold's catching tutorial + 5 balls + advice), 4C (mother's goodbye).

#### Scene 4A — Kestra bolts north (NEW `scr_seq_T21_014`)

**Beats:**
1. Player returns to Cherrygrove from the north (now arriving via Route 29). Gold waits outside (re-show `obj_T21_gold` via `clearflag FLAG_HIDE_CHERRYGROVE_GOLD`). New coord trigger near the north entrance fires, gated on `VAR_SCENE_CHERRYGROVE_CITY_OW == 3` (set on arrival, requires `FLAG_GOT_POKEDEX`).
2. Kestra (re-shown for this beat via `clearflag FLAG_HIDE_CHERRYGROVE_RIVAL`) interrupts before Gold can finish — announces Violet City and BOLTS north off-screen. `apply_movement` north + `play_se` run + `hide_person` + `setflag FLAG_HIDE_CHERRYGROVE_RIVAL`. (Her characterization beat: a step ahead in action if not thought.)
3. Gold reacts wryly, then turns to the player for the quieter moment — notices the player stayed to listen.
4. Chain directly into Scene 4B.

**Dialogue** (append to `msg_0550_T21.gmm`):
```
msg_0550_T21_00041 (GOLD, opening, gets cut off):
GOLD: There you two are. Pokedexes and\neverything. Look at you.\rNow, before you set off, there’s a\nthing or two I want to-\r

msg_0550_T21_00042 (KESTRA, interrupting, already leaving):
KESTRA: -Violet City! That’s where the\ngym is, right? And the school?\rNo time to waste, then. First badge\nisn’t gonna win itself.\rSee you on the road, slowpoke! Try to\nkeep up!\r

msg_0550_T21_00043 (GOLD, watching her go, dry):
GOLD: ...And there she goes.\rHalf a step ahead of her own brain.\nAlways was.\r

msg_0550_T21_00044 (GOLD, turning to player, warmer):
GOLD: But not you. You stuck around to\nhear the rest.\rThat’ll take you farther than running\never will.\rCome here a second. There’s one thing\nevery Trainer ought to learn before\nthe road takes them.\fLet me show you how it’s done.\r
```

#### Scene 4B — Catching tutorial + 5 Poke Balls + advice (continue `scr_seq_T21_014`)

**Mechanic choice (committed for ship): Option A — Gold COACHES a hands-on practice catch via the proven `catching_tutorial` scrcmd (opcode 251).** That engine routine is the GSC/HGSS player-controlled demo: it hands the player a temporary lv5 Marill vs a wild lv2 Rattata, gives 20 demo balls, and the player throws — it's a sandbox (nothing added to the real party/bag). To honor the design's "Gold walks the player through it step by step," frame it as Gold *coaching*: he narrates each step around the `catching_tutorial` call. The player's real first balls come from Gold's `giveitem` afterward; their first real catch happens on the road. (Option B — a custom "Gold auto-catches" cutscene scrcmd à la `apoc_fly_away` — is higher-fidelity to the literal wording but needs ARM9/C work; flagged as a later upgrade.)

**Beats:** Gold sets up (weaken, then throw) → `catching_tutorial` → Gold congratulates → explains real balls aren't free and hands **5 Poke Balls** (`giveitem ITEM_POKE_BALL, 5`) → sincere advice (go to Violet's school/university; don't rush, enjoy the journey) → steps aside; north exit opens; `setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 4`.

**Dialogue** (append to `msg_0550_T21.gmm`):
```
msg_0550_T21_00045 (GOLD, pre-tutorial):
GOLD: Catching’s simple once you’ve\ndone it once.\rFirst you wear the wild one down. A\nfainted Pokemon can’t be caught, but a\ntired one comes quietly.\rThen - when it’s weak enough - you\nthrow the Ball.\fGo on. I’ll talk you through it.\r

(engine: catching_tutorial)

msg_0550_T21_00046 (GOLD, post-catch):
GOLD: There you go. First catch.\rFeels good, doesn’t it? That little\nclick when the Ball goes still.\rYou never quite stop chasing that\nfeeling. Trust me.\r

msg_0550_T21_00047 (GOLD, hands the balls):
GOLD: Here. Take these to get you\nstarted.\rThe Marts sell more, but a good Trainer\nnever lets their pack run empty.\r

msg_0550_T21_00048 (system):
{STRVAR_1 3, 0, 0} received\n5 Poke Balls from Gold!\r

msg_0550_T21_00049 (GOLD, advice — Violet):
GOLD: Head for Violet City. There’s a\nschool there now - a whole university,\nif you can believe it.\rTypes, items, battling. They’ll teach\nyou everything I’d only fumble trying\nto explain.\r

msg_0550_T21_00050 (GOLD, the heart of it — extends the built msg 00025):
GOLD: But take it from someone who’s\nbeen there - don’t rush the road.\rIt goes fast enough on its own.\rEnjoy every step of it.\fNow go say goodbye to your mother\nbefore you leave. She’d never forgive\nme if you skipped that.\r
```

**Mechanics (chained from 4A in `scr_seq_T21_014`):** `npc_msg 45`; `closemsg`; `catching_tutorial`; `npc_msg 46`; `closemsg`; `npc_msg 47`; `giveitem ITEM_POKE_BALL, 5`; `play_fanfare SEQ_ME_ITEM`; `wait_fanfare`; `buffer_players_name 0`; `npc_msg 48`; `npc_msg 49`; `npc_msg 50`; `closemsg`; `setflag FLAG_APOC_CATCH_TUT_DONE`; `setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 4`; `releaseall`; `end`. Add `scrdef scr_seq_T21_014` + `#define _EV_scr_seq_T21_014 14`. The built `msg_0550_T21_00025` (Gold's "setting out / don't rush" line on his `scr_seq_T21_011` talk script) can stay as his post-tutorial idle line, or be superseded by msg 50.

#### Scene 4C — Mother's goodbye + savings (reuse existing player-house logic)

**Beats:**
1. Player enters the Player House (060_T20R0201) after the tutorial. Mom (`obj_T20R0201_gsmama`, SPRITE_GSMAMA) initiates a warm farewell.
2. **Reuse the existing yes/no savings logic** at `scr_seq_T20R0201_005` (lines 169-194: `getmenuchoice` → `setflag/clearflag FLAG_SYS_MOMS_SAVINGS`). Re-skin the prompt as a heartfelt send-off, gated first-time on `FLAG_APOC_MOM_GOODBYE_DONE`; subsequent talks fall through to the existing bank menu (lines 196+) for ongoing deposits/withdrawals.
3. Short loving send-off; player exits and heads north. Chapter 1 ends.

**Dialogue** (add to `msg_0545_T20R0201.gmm`):
```
msg_apoc_mom_00 (MOM, goodbye + savings offer):
MOM: So today’s the day. My little\nTrainer, off to see the world.\rGold told me he set you straight on the\nimportant things. Good.\rOh - before you go. Let me do what\nmothers do.\rWhile you’re away, I can look after your\nmoney for you.\fEvery time you win a battle, I’ll tuck\na little aside. Safe and sound, waiting\nfor when you come home.\rShould I hold onto your prize money\nfor you?\r
[YES -> msg_apoc_mom_01a]  [NO -> msg_apoc_mom_01b]

msg_apoc_mom_01a (MOM, YES — setflag FLAG_SYS_MOMS_SAVINGS):
MOM: Then it’s settled. I’ll keep it\nsafe, and spend a little on nice things\nfor you when I see a bargain.\rCall me anytime. I love hearing your\nvoice.\r

msg_apoc_mom_01b (MOM, NO — clearflag FLAG_SYS_MOMS_SAVINGS):
MOM: All right, all right. You’re a big\nTrainer now. You’ll manage your own\ncoin.\rJust don’t spend it all on Poke Balls\nand vending machines, hmm?\r

msg_apoc_mom_02 (MOM, final send-off, both paths):
MOM: There’s a whole world out there,\nand it’s yours to walk.\rBe kind. Be brave. And every now and\nthen... come home and tell me about it.\fNow go on. Your friend’s probably\nhalfway to Violet already.\r
```

**Mechanics:** In the player-house script, on Mom-talk: `goto_if_set FLAG_APOC_MOM_GOODBYE_DONE, _existing_bank_menu`; else `npc_msg apoc_mom_00`; `getmenuchoice`; YES → `npc_msg apoc_mom_01a` + `setflag FLAG_SYS_MOMS_SAVINGS`; NO → `npc_msg apoc_mom_01b` + `clearflag FLAG_SYS_MOMS_SAVINGS`; `npc_msg apoc_mom_02`; `setflag FLAG_APOC_MOM_GOODBYE_DONE`; `releaseall`. No new engine code — `FLAG_SYS_MOMS_SAVINGS` + `bank_transaction`/`check_bank_balance` already implement the GSC savings system. **Note:** the Player House warp header still reads `MAP_NEW_BARK_PLAYER_HOUSE_1F` in 064_T21.json (vanilla naming, rewired to Cherrygrove); the interior's return warp targets `MAP_CHERRYGROVE` anchor 2. Leave the names; they work.

---

## 5. Consolidated WORLD-OVERHAUL CHECKLIST (per map)

### Cherrygrove City (064_T21.json, scr_seq_0850_T21.s, event_T21.h, msg_0550_T21.gmm)
- [ ] `obj_T21_gold`: SPRITE_HERO → **SPRITE_GSMIDDLEMAN1** (NOT HERO_2 — crashes as an NPC); add `eventFlag FLAG_HIDE_CHERRYGROVE_GOLD`.
- [ ] `obj_T21_gsrivel` (Silver): `eventFlag` → `FLAG_HIDE_CHERRYGROVE_SILVER`.
- [ ] **ADD `obj_T21_friend`** (Kestra, SPRITE_GSGIRL2, ~553,401, scriptId 0, `eventFlag FLAG_HIDE_CHERRYGROVE_RIVAL`); add to event_T21.h.
- [ ] Scene 1 (`scr_seq_T21_012`): insert msgs 33-36; fix line 894 hide-flag to `FLAG_HIDE_CHERRYGROVE_SILVER`; change line 897 setvar 10 → 1; add `buffer_players_name 0` before msg 36.
- [ ] **ADD `scr_seq_T21_013`** (Scene 2A grass-block) + scrdef + `_EV_..._013`; new/repointed coord at grass mouth gated var==1; msgs 37-40.
- [ ] **ADD `scr_seq_T21_014`** (Scene 4A+4B farewell/catch chain) + scrdef + `_EV_..._014`; new coord at north entrance gated var==3 + `FLAG_GOT_POKEDEX`; msgs 41-50.
- [ ] On arrival from New Bark, set `VAR_SCENE_CHERRYGROVE_CITY_OW, 3` (entry script or coord on the north warp).
- [ ] **Remove overworld Guide-Gent `obj_T21_gsoldman1` (deceased)**; reassign his onboarding (`scr_seq_T21_001/002`) to Gold as a short begrudging tour on `obj_T21_gold`.
- [ ] Detach legacy Guide-Gent map-card (`scr_seq_T21_002`) and road-rival (`scr_seq_T21_003`) from this scene var; repoint the x547,z385 coord to `_EV_scr_seq_T21_013`.
- [ ] Add free flags to flags.h: `FLAG_HIDE_CHERRYGROVE_FRIEND` (0x19A), `FLAG_HIDE_CHERRYGROVE_SILVER` (0x19E), `FLAG_HIDE_CHERRYGROVE_GOLD` (0x19F), `FLAG_APOC_R29_INTRO_DONE` (0x1A0), `FLAG_APOC_CATCH_TUT_DONE` (0x1A3); var `VAR_APOC_FRIEND_STARTER`; define `FLAG_APOC_MOM_GOODBYE_DONE`.

### Player House (060_T20R0201.json, scr_seq_0845_T20R0201.s, msg_0545_T20R0201.gmm)
- [ ] Verify Mom `obj_T20R0201_gsmama` visible.
- [ ] Add first-time goodbye branch using existing `FLAG_SYS_MOMS_SAVINGS` yes/no; gate on `FLAG_APOC_MOM_GOODBYE_DONE`; add msgs apoc_mom_00/01a/01b/02.
- [ ] Confirm return warp → MAP_CHERRYGROVE anchor 2.

### Gold's House (068_T21R0401.json, scr_seq_0855_T21R0401.s, event_T21R0401.h, msg_0554_T21R0401.gmm)
- [ ] Replace `obj_T21R0401_gsoldman1` with **`obj_T21R0401_gold`** (**SPRITE_GSMIDDLEMAN1**, NOT HERO_2, ~4,3 down, scriptId 0).
- [ ] **ADD `obj_T21R0401_typhlosion`** (Gold's partner, static, ~3,3, scriptId 0) — present in the room during the ceremony (needs Typhlosion follower/overworld sprite; flag for asset pass if unavailable).
- [ ] **ADD `obj_T21R0401_friend`** (Kestra, SPRITE_GSGIRL2, ~5,5, scriptId 0).
- [ ] Keep three balls as props routing to `_002`; hide after pick.
- [ ] Rewrite `scr_seq_T21R0401_002` per Scene 2 Part B (intro, protest, choose_starter, counter-pick logic via `VAR_APOC_FRIEND_STARTER` + `buffer_species_name`, Elm directive, bolt, setvar 2).
- [ ] Rewrite msgs 00000/00003-00007 (keep 00001 item-get, 00002 guard).
- [ ] Remove the Guide-Gent entirely (deceased); his tour is reassigned to Gold (see §3).

### Southeast House (069_T21R0501.json)
- [ ] No change — the Guide-Gent is deceased (not relocated here). Keep existing residents.

### Route 29 (030_R29.json + its scr_seq, event_R29.h)
- [ ] Repoint Kestra companion object to SPRITE_GSGIRL2 (reuse `obj_R29_var_2` slot or add fresh); `eventFlag FLAG_HIDE_ROUTE_29_FRIEND`.
- [ ] Hide/remove vanilla catching-tutorial NPCs (`obj_R29_var_2` aide role, `obj_R29_tsure_poke_static_marill`) so vanilla tutorial cannot fire.
- [ ] Add Scene 3A coord trigger + sub-script (gated `FLAG_GOT_STARTER` set, `FLAG_APOC_R29_INTRO_DONE` unset); msgs apoc_r29_00/01.
- [ ] Verify/repoint warps: Cherrygrove north ↔ R29 south; R29 north ↔ New Bark. Keep vanilla wild tables (short/safe).

### New Bark Town (057_T20.json) + Elm's Lab 1F (058_T20R0101 + its scr_seq + msg)
- [ ] New Bark: `obj_T20_var_1` → SPRITE_GSGIRL2 (Kestra); hide GSC-crisis NPCs; keep flavor.
- [ ] Elm Lab: show Elm (`clearflag FLAG_HIDE_ELMS_LAB_ELM`), keep Officer hidden, show Kestra (`FLAG_HIDE_ELMS_LAB_FRIEND`).
- [ ] Add Scene 3B coord-trigger sub-script: greet, `give_pokedex`, `setflag FLAG_GOT_POKEDEX`, reminiscence; msgs apoc_elm_00-06 + apoc_elm_friend_00.
- [ ] Ensure only the lab and the route exits are meaningful (no other content).

### Reconciliation of the already-built Scene 1
Scene 1 is approved and stays substantially intact. The only edits to it are: Gold sprite (SPRITE_GSMIDDLEMAN1), four new Kestra lines, the Silver hide-flag fix, the setvar value (10→1), and one `buffer_players_name` before msg 36. The Murkrow `apoc_fly_away` cutscene is untouched.

---

## 6. ORDERED IMPLEMENTATION PLAN (testable increments)

**Increment 0 — Flags/vars/headers (no behavior change).** Add the new flags, `VAR_APOC_FRIEND_STARTER`, and the `_EV_scr_seq_T21_013/014` defines + scrdef lines. Build to confirm it still compiles. *Test: game boots.*

**Increment 1 — Scene 1 reconcile.** Apply the Gold sprite swap, add `obj_T21_friend`, insert msgs 33-36, fix Silver hide flag, change setvar to 1. *Test: step out of house → battle plays with Kestra reacting → Silver flies off → Kestra stays visible → var==1.*

**Increment 2 — Scene 2A grass block.** Build `scr_seq_T21_013` + coord; Gold stops the kids and warps the player into Gold's house. *Test: walk to north grass with var==1 → Gold intercepts → player ends up inside Gold's house.*

**Increment 3 — Scene 2B starter ceremony.** Swap interior objects to Gold + Kestra, rewrite `scr_seq_T21R0401_002` + msgs, counter-pick logic. *Test: pick each of the three starters in turn; confirm Kestra always names/takes the correct type-advantage counter; `VAR_APOC_FRIEND_STARTER` set; var==2; starter follows player out.*

**Increment 4 — Route 29 traversal.** Kestra sprite + intro coord; disable vanilla tutorial NPCs; verify warps. *Test: leave Cherrygrove north → Kestra goads + peels off once → ordinary wild encounter works → reach New Bark.*

**Increment 5 — Elm's Lab Pokedex.** Show Elm/Kestra, add the coord cutscene, `give_pokedex`. *Test: enter lab → Pokedex granted once → reminiscence plays → `FLAG_GOT_POKEDEX` set → re-entry skips cutscene.*

**Increment 6 — Return + Scene 4A/4B.** Set var==3 on arrival; build `scr_seq_T21_014`; Kestra bolts; `catching_tutorial`; 5 balls; advice; var==4. *Test: walk back into Cherrygrove from north → Kestra interrupts and runs → Gold runs the catching tutorial → receive 5 Poke Balls → advice plays.*

**Increment 7 — Scene 4C mother.** First-time goodbye branch + savings yes/no. *Test: talk to Mom → savings prompt (both branches set/clear flag correctly) → send-off → subsequent talk falls through to bank menu.*

**Increment 8 — Full playthrough + polish.** End-to-end run; charset audit (curly apostrophes only, no em dashes/straight quotes, `\r`/`\n`/`\f` correct); confirm no orphaned legacy flows fire; confirm the Guide-Gent is fully removed and Gold's begrudging tour works; Typhlosion present in Gold's house; optional Scene 1 fly-off SE/BGM sting.

---

## 7. OPEN REFINEMENT QUESTIONS (genuine creative forks)

1. **Kestra's sprite** — commit to SPRITE_GSGIRL2 (recommended), or do you want a custom adult-distinct/child sprite inserted now that the project supports new assets?
2. **Gold's sprite** — resolved to **SPRITE_GSMIDDLEMAN1** (HGSS's other-protagonist NPC; SPRITE_HERO_2 crashes as an NPC). It reads as a real trainer who isn't the player, but it isn't a distinct adult Gold. Ship with GSMIDDLEMAN1, or invest in a custom adult-Gold overworld sprite?
3. **Catching tutorial fidelity** — ship Option A (Gold *coaches* the proven player-controlled `catching_tutorial`), or build Option B (custom scrcmd where Gold literally auto-catches as a pure cutscene)?
4. **Cherrygrove ↔ Route 29 connection** — confirm the exact north-edge warp/connection tile so the Scene 2 grass-block and Scene 4A north-entrance triggers sit on the real path (the spec assumes the x547,z385 grass mouth).
5. **Scene 1 fly-off audio** — add a Champion/idol musical sting or flying SE on Silver's takeoff (the build has rival intro/outro music available), or keep it ambient/silent?

---

## 8. Chapter 1 World Detail — NPCs, Dialogue & Placement

All coordinates and object IDs below are **read from the real map files** (`064_T21.json` Cherrygrove, `030_R29.json` Route 29, `057_T20.json` New Bark). Dialogue is HG-charset-safe (curly apostrophes `’`, `Poké`/`Pokémon`/`Pokégear` with accents, ` - ` for dashes, `\r`/`\n`/`\f`).

### 8.0 Geography correction — resolves Open Question #4

The map coordinates contradict §3's assumption that Route 29 lies *north* of Cherrygrove. Object X-ranges place the towns on an **east–west axis**: Cherrygrove (x≈520–575) → **Route 29** (x≈581–666) → New Bark (x≈676–703). These are **shared global world coordinates** — the three maps form one contiguous, non-overlapping, ascending X-band, so the east–west ordering is geometric fact, not inference. This matches vanilla HGSS, where Route 29 is the east–west connector and **Route 30 (north of Cherrygrove) leads to Violet**.

**Corrected chapter loop:** Cherrygrove → **(EAST) Route 29** → New Bark (Pokédex) → back to Cherrygrove → **(NORTH) Route 30/31** → Violet.

Implications for the already-specced triggers:
- The Scene-2 grass block (heading to New Bark/Elm) belongs at Cherrygrove's **east edge** (the Route 29 mouth, ≈ x573–575, z≈396–400), **not** the north coord `(547,385)`.
- The north coord `(547,385)` is the **Scene-4 departure toward Violet** (Route 30), which is correct for the chapter's *ending*.
- **Build action (resolved):** move the Scene-2 grass-block coord to Cherrygrove's east edge (the Route 29 mouth) and keep `(547,385)` for the Scene-4 Violet departure. (The legacy `_EV_scr_seq_T21_002` coord currently sits at `(547,385)`.)

### 8.1 Gold's begrudging tour (replaces the deceased Guide-Gent)

**When it fires:** at the **end of the Scene 2 starter ceremony**, inside Gold's house (`068_T21R0401`), after Gold sends them to Elm (`msg 00006`) and before Kestra bolts. Giving the Running Shoes here (rather than Scene 4) means the player can run on Route 29. The joke is that Gold flatly **refuses to do a walking tour** — they're locals — so he just grumbles the basics and hands over the gear.

**New dialogue** (append to `msg_0554_T21R0401.gmm`; existing Scene-2 msgs 00000–00007 stay):

```
msg_0554_T21R0401_00008 (GOLD, begrudging tour):
GOLD: And before the two of you go\ntearing off -\rNo, I’m not walking you around town.\nYou were both born here. You know\nwhere the Mart is.\fThe Mart sells what keeps you upright\nout there. The Center patches your\nPokémon up, free, every time.\rThat’s the tour. Riveting, I know.\r

msg_0554_T21R0401_00009 (GOLD, hands the gear):
GOLD: Here. Running Shoes - so I don’t\nhave to watch you amble off at a crawl.\rAnd a Map Card for your Pokégear, so\n“I got lost” stops being an excuse.\rLook after your feet. The road’s long.\r

msg_0554_T21R0401_00010 (system, items):
{STRVAR_1 3, 0, 0} received the\nRunning Shoes and the Map Card!\r

msg_0554_T21R0401_00011 (KESTRA, reacting then bolting — supersedes the plain 00007 bolt):
KESTRA: Gooold, we KNOW where the Mart\nis -\r...New shoes, though. Okay. Okay, that’s\nactually kind of great.\rRace you, partner! Last one to New Bark’s\na SLOWPOKE!\r
```

**Mechanics (extend the Scene 2B script after `npc_msg 00006`):**
```
npc_msg 00008
npc_msg 00009
setflag FLAG_SYS_RUNNING_SHOES          ; reuse the vanilla tour's Running-Shoes grant
load_map_card / pokegear_mapcard op     ; reuse the op behind the old tour msgs 10-11
play_fanfare SEQ_ME_ITEM
wait_fanfare
buffer_players_name 0
npc_msg 00010
npc_msg 00011                            ; (or keep 00007 if you prefer the shorter bolt)
apply_movement obj_T21R0401_friend, _to_door
wait_movement
hide_person obj_T21R0401_friend
...continue existing Scene 2B tail (releaseall; setvar VAR_SCENE_CHERRYGROVE_CITY_OW, 2; end)
```
The Running-Shoes flag and Pokégear Map-Card op already exist in the vanilla Guide-Gent tour (`scr_seq_T21_001/002`, old msgs 6–7 and 10–12) — lift those grant ops rather than authoring new ones.

### 8.2 Cherrygrove NPC roster (reuse existing objects; new lines)

Remove `obj_T21_gsoldman1` (Guide-Gent, deceased, at 566,396). Re-voice the surviving flavor objects:

| Object (sprite) | Coord | Script | New role & line (gist) |
|---|---|---|---|
| `obj_T21_gsboy1` (GSBOY1) | 554,399 | `_007` | **Silver fanboy kid.** "Did you SEE him? The CHAMPION, right here! I'm gonna fly off just like that someday. You watch." |
| `obj_T21_gswoman1` (GSWOMAN1) | 561,407 *(waterfront)* | `_008` | **By the idle boats.** "These boats don't go far anymore. Used to be you could ride the coast clear to Olivine. Now they mostly just... sit." (future-travel hook) |
| `obj_T21_gsbigman` (GSBIGMAN) | 530,406 | `_004` | **Neighbor who looks after Gold.** "Champion or not, Silver still drops in to lose to Gold now and then. Does the old man good. Don't tell Gold I said he won." (understated reverence + the friendship) |
| `obj_T21_gsmiddleman1` "Cameron" (GSMIDDLEMAN1) | 562,402 | `_009` | **Research-hub commuter.** "Half the kids here ride to New Bark for the labs now. Not Gold. He came to Cherrygrove to get *away* from all that humming." (seeds New Bark = hub + Gold's reason) |

**Signs (bgs):**
```
sign _EV_scr_seq_T21_005 (556,401, beside Gold's house) — understated reverence:
There’s no plaque here. Just a quiet\nhouse, a worn-out battle ring in the\nyard, and a man who’s done enough.\r

sign _EV_scr_seq_T21_006 (554,396) — the grove:
CHERRYGROVE CITY\n“Where the cherry trees and the sea\nlook after their own.”\r
```

### 8.3 New Bark NPC roster (research-hub redress; pass-through)

New Bark is the player's **destination for the Pokédex only** — not their home (the player's house/mother are in Cherrygrove). Hide the vanilla "this is your hometown" furniture; re-voice the rest as a busy institute town.

**Hide (set their hide flags at chapter init):**
- `obj_T20_gsrivel` (vanilla Silver-rival, 682,391) — Silver does not appear here.
- `obj_T20_gsmama` (mom, 695,396) — the player's mother is in Cherrygrove. Repurpose the `MAP_NEW_BARK_PLAYER_HOUSE_1F` warp as a researcher's residence or lock it.
- `obj_T20_tsure_poke_static_marill` + `obj_T20_tsure_poke_static_marill_2` (Marill demo props) — no vanilla catching tutorial here.
- `obj_T20_var_1_2` (second demo friend, 694,400) — unused.

**Repurpose for hub flavor (keep; new lines):**

| Object (sprite) | Coord | Script | New role & line (gist) |
|---|---|---|---|
| `obj_T20_doctor` (DOCTOR) | 703,384 | — | **Harried researcher.** "Can't stop - grant review in an hour. You're here for Professor Elm? Everyone is, lately." |
| `obj_T20_gswoman1` (GSWOMAN1) | 683,399 | `_001` | **Lab local, proud.** "New Bark was three houses and a windmill when I was small. The Professor put this town on the map. Literally - cartographers come now." |
| `obj_T20_gsbigman` (GSBIGMAN) | 685,408 | `_015` | **Old-timer who knew Gold.** "Gold grew up two doors down. Left the week they broke ground on the third lab. Said he wanted somewhere the loudest thing was the sea." |
| `obj_T20_gsmiddleman1` "Cameron" (GSMIDDLEMAN1) | 695,403 | `_017` | **Visiting scholar (kept clean — from Violet).** "I came up from the university in Violet to shadow Professor Elm. Best fieldwork in Johto, bar none." |
| `obj_T20_var_1` (→ GSGIRL2) | 688,392 | `_004` | **Kestra**, arrived ahead of you (companion; see §8.4). |

- **Elm's Lab:** 1F is the interactable institute floor (Elm + Pokédex beat). **2F** (`MAP_NEW_BARK_ELMS_LAB_2F`, warp at 688,392) is the **research wing — gated** this chapter (the "deeper facility opens later" beat). Keep `FLAG_HIDE_*` on 2F researchers until the return visit.
- **Chapter stays clean:** the visiting scholar is from Violet, *not* Saffron/Silph. No corporate-lab presence in New Bark.

### 8.4 Route 29 — Kestra companion + flavor

- **Kestra companion:** reuse `obj_R29_var_2` (660–661,400, east/New-Bark side) → `SPRITE_GSGIRL2`, hide `FLAG_HIDE_ROUTE_29_FRIEND`. The companion beat (goad → peel off → reunite at New Bark) fires off the existing east-edge coord `_EV_scr_seq_R29_001` at `(666,396)`. Dialogue already specced in §3 Scene 3A (msgs `apoc_r29_00/01`).
- **Disable the vanilla tutorial:** hide `obj_R29_tsure_poke_static_marill` (660,400) so the GSC Marill tutorial cannot fire (the catching demo belongs to Gold in Scene 4).
- **Flavor NPCs** (keep vanilla placements, light Apocrypha touches optional): `gsman1` (600,395), `gswoman2` (608,404), `gsboy2` (626,410), `gsbigman` (622,392), `gswoman2_2` (629,405). One can mention the washed-out path / sea air to seed the "world has changed" tone gently.
- **Optional nooks you aren't ready for:** the two `std_field_cut` trees at (629,401) and (619,405) gate small side patches — HM Cut isn't available, so they teach "come back later" exactly like Dark Cave in Ch.2.
- **Apricorn tree** (596,392, `obj_R29_bonguri`, Red apricorn) — harmless flavor now; Kurt's ball-craft pays it off in Ch.3.

### 8.5 Tile-level scenery & placement (confirmed scenery items)

These are **map-tile / object-placement tasks**, grounded in the real coordinate space. Tile-art items that need new tileset graphics are flagged **[asset]**.

**Cherrygrove (064_T21) — full aesthetic redesign ("10 years on"):**

*Decisions: cinematic graded palette (game-wide pilot), modest/lived-in growth, all four feature sets.*

- **Cinematic color grade [asset — palette]:** re-author the Cherrygrove tileset palettes per the game-wide grade (DESIGN.md *Visual Identity & Art Direction*): shadows → cool teal, highlights → warm amber, midtones rich-but-desaturated (no flat GSC primaries). Cherrygrove's local accent is **cherry-blossom pink**. Author the day/night palette variants to deepen the grade, not fight it. **This palette set is the template the other Johto tilesets adopt** — so get it right here first.
- **Matured cherry grove + blossom park [asset — tiles]:** reskin tree tiles to flowering cherry, densest framing **Gold's house (558,401)** and the central lanes (x≈554–562, z≈399–403). Add a small **park pocket** with petal-strewn ground tiles and a bench in the open area NW of the Mart/Center (≈ 548–553, 393–398). Needs: cherry-blossom tree tile + fallen-petal ground tile + bench prop.
- **Weathered fishing waterfront:** the south edge is already sea (vanilla tour msg 5; `gswoman1` at 561,407, `gsbigman` at 530,406 stand on the southern strip). Add a **sand strip** (z≈406–409), a **worn wooden pier** extending into the water ≈ (560–564, 407–410), **2–3 beached/idle boat objects**, and **drying-net props**. Non-boardable (no warp); `gswoman1`'s line (§8.2) explains the trade faded. Needs: pier + net tiles; boat objects (check whether S.S.-network content already defines reusable boat objects).
- **A few new homes (modest growth):** add **1–2 new house models** west of the player's house (≈ 540–545, 401–405), filling the lane. Keep cost low — facades by default, or make **one enterable** with a flavor resident: a recent transplant who "moved here for the quiet, like Gold did." (New roster line; reinforces the §8.2 theme.)
- **Coastal lookout / overlook:** a scenic point at the SE water's edge near the Southeast house (≈ 566–569, 406–409): a **railing tile + bench** overlooking the sea toward Route 29's matching sea-view ridge (Route 29 block below). Pure mood, with a quiet "this is where Gold sits" implication.
- **Understated Gold reverence:** no statue. The sign at (556,401) (§8.2), a **worn battle-ring tile** in Gold's yard (≈ 556–558, 404), and the neighbor `gsbigman` carry it.
- **Weathering pass:** age the existing building textures (Center/Mart/houses) within the grade — a decade of sea air. Detail, not reconstruction.

**Cherrygrove asset checklist:** graded palette set (+ day/night variants) · cherry-blossom tree tile · fallen-petal ground tile · pier tile · drying-net prop · 1–2 house models (or facades) · railing/overlook tile · bench prop · worn-battle-ring tile.

**Route 29 (030_R29) — coastal grade + "Gold's town fades to the research town":**
- **Cinematic grade [asset — palette]:** apply the Johto warm-amber/teal grade to the Route 29 outdoor tileset (template lifted from Cherrygrove). Day/night is **automatic** — HGSS runs time-of-day palette/encounter swaps (night table in [JOHTO_BATTLES.md](JOHTO_BATTLES.md)); just confirm the zone uses the graded outdoor palette set.
- **West→east visual gradient:** near the Cherrygrove (west) end, let **a few cherry trees spill onto the route** (continuity with the grove), fading to ordinary graded Johto woodland as you move east toward New Bark — a quiet visual handoff from "Gold's town" to "the research town." Reskin only the westmost 2–3 tree tiles.
- **Sea-view ridge [asset — tiles]:** a small elevation/lookout on the south side ≈ (640–650, 404–408), overlooking the water back toward Cherrygrove — the matching bookend to Cherrygrove's coastal lookout. Railing + bench. Cut only if tile budget is tight.
- **Lived-in detail:** age the path/fence tiles so the route reads as well-trodden, not pristine. Keep the apricorn tree (596,392) and the two Cut-tree nooks (629,401 / 619,405) as-is.

**New Bark (057_T20) — research-institute campus, graded:**
- **Cinematic grade [asset — palette]:** Johto warm-amber base, but New Bark's **local accent runs cooler and cleaner** (lab teal / off-white) than Cherrygrove's blossom pink — same regional grade, distinct town character (institute vs. refuge).
- **Campus redress [asset-light — props/tiles]:** lab props (microscopes, equipment crates, antenna/dish, tidy signage, paved paths) around Elm's Lab exterior (≈ 684–700, 384–400) and the repurposed houses; reads as a working campus, not a sleepy village. **Optional single facade:** a small **research-annex building** (non-enterable) to sell the institute's scale without real growth.
- **Layout stays put:** the existing two-floor lab + surrounding houses already support the institute read once the residential furniture is hidden (mom / player-house, §8.3). **Elm's Lab 2F = the gated research wing** (opens on the later return visit).
- **Deliberate contrast with Cherrygrove:** clean lines, brighter/cooler light, busy NPCs — the opposite of Cherrygrove's warm quiet, which is exactly why Gold left it (§8.3 old-timer line).

---

## 9. Opening Overhaul — the Cold Open (NEW DIRECTION)

**Premise change:** the player is **not** a Cherrygrove native. They are a **transplant from Kalos** who has just moved to Cherrygrove with their mother. The standard HGSS new-game flow (the Oak lecture / control-info screen) is **cut entirely** and replaced with a cinematic cold open. Kestra is therefore a **stranger** the player meets for the first time at the Silver/Gold battle (see Scene 1 rewrite, §9.4).

### 9.1 Engine changes (biggest piece — C-level, needs a dedicated pass)

- **Cut Oak's intro.** The lecture lives in `src/oaks_speech.c`; the new-game entry runs through `src/application/main_menu/main_menu.c` → `src/save.c` / `src/field_system.c`. New game must **skip the Oak sequence** and warp the player straight into the Cherrygrove house interior with the cold-open script armed. (Keep the name-entry step; just drop Oak's framing around it.)
- **Set the new-game start location** to the Cherrygrove player-house 1F (`MAP_NEW_BARK_PLAYER_HOUSE_1F` = `060_T20R0201`), player + mom pre-placed, screen starting **black**.
- **Naming is cut from the intro.** Keep **only** the boy/girl **gender select** (it lives in Oak's-speech states 61–70); cut the lecture, the Pokémon showcase, and both naming screens. The player's **name is entered later**, during the **Kestra first-meeting** (she asks who you are → a naming-screen call from the field script). So the only pre-game choice is appearance. (An intro message before the gender pick can be added later.)
- This is the one genuinely hard, code-level item. **Investigate before editing**; do it as its own increment. Everything below (9.2–9.4) is field-script / map / message work that can proceed independently once the start warp lands in the house.

### 9.2 Cold-open sequence (field script on the house 1F map)

Beats: black screen → a couple of `...` boxes → Mom's "wake up" → "we're here, our new home" → **gradual brighten** (`fade_screen` in) revealing player + mom by the front door amid moving boxes → Mom's dialogue → player goes upstairs (sees room, sets up PC w/ Potion) → returns → Mom has moved, gives the **menu rundown + Pokégear** → free to move.

**Draft dialogue** (HG-charset; to add to `msg_0545_T20R0201.gmm`):
```
(black screen) ...\r
(black screen) ......\r
MOM: ...Honey. Hey - we’re here.\rWake up, sleepyhead.\r
MOM: We made it. Our new home!\rI still can’t believe we actually\ndid it.\r
(fade in to the house interior)
MOM: All the way from Kalos... and now\nthis is home.\rA whole new region. A fresh start,\nfor both of us.\rThe movers got everything here in one\npiece. More or less.\r
MOM: Go on up and see your new room -\nI had them set your things up first.\rYour PC should be ready. Get it\nsorted while I unpack down here.\r
(player visits 2F, takes the Potion from the PC, returns)
MOM: There you are. Settling in?\rOh - this came for you.\fYour very own Pokégear. Map, phone,\nradio, clock, all in one.\rCall me anytime. I mean it.\r
(give Pokégear + the field-menu rundown; player is now free)
```
- **Pokégear reconciliation:** Mom gives the **Pokégear** here (replacing the old Guide-Gent/Oak hand-off). Gold's begrudging tour (§8.1 / `scr_seq_T21R0401_002`) then gives the **Map Card** that loads onto it + Running Shoes — order is now consistent (Pokégear first from Mom, Map Card later from Gold).
- The **menu rundown** is Mom's job now; Gold's "tour" is just Mart/Center flavor, no menu tutorial.
- Town name: Mom must **not** say "Cherrygrove." The reveal lands naturally from Kestra at the battle (§9.4) or a sign.

### 9.3 House interior — swap an existing room model + object dressing (DECIDED)

Full custom-3D was ruled out: interiors are prebuilt NSBMD models (`bm_room.narc` → `bm_room_*.bin`) with **no model source/build pipeline** in the repo, so a bespoke model needs an external GUI 3D tool — out of scope for code. **Decision: reuse a better-fitting *existing* interior model and dress it with objects.** All code-doable, no GUI tooling.

- **Swap the model:** point the player-house 1F (and 2F) map at a roomier/nicer existing interior model than the vanilla New Bark protagonist house, so it doesn't read as the default home. (Find the map→model index wiring first.)
- **Object dressing (the "just moved in" feel):** place **moving-box sprites**, scattered **furniture objects**, the **PC** (with a Potion via a standard item event), and **Mom**'s positions/scripts.
- **2F:** the player's room (bed + PC). Use an existing upstairs model; dress similarly.
- This is the achievable "significant custom" without 3D modeling. If a truly bespoke room is wanted later, that's the DSPRE / DS Map Studio path (you driving, me folding the model into `bm_room`).

### 9.4 Scene 1 fixes (DONE this pass — built & compiling)

- **#1 Gold persisted:** Scene 1 now `hide_person obj_T21_gold` + `setflag FLAG_HIDE_CHERRYGROVE_GOLD` after the fly-off (Gold heads inside; the interior Gold runs the ceremony).
- **#2 No onlookers:** `gsboy1` (555,405) and `gsbigman` (557,405) repositioned as **static onlookers facing the battle**; with Kestra (553,401) that's a small watching crowd.
- **#3/#4 Kestra dialogue:** msgs 33–36 rewritten — no battle play-by-play, and reframed as a **first meeting** ("I don't know you, and I know everybody round here... welcome to the neighborhood, stranger"); the player's name is no longer used (she doesn't know it yet).
- **#6 Murkrow persisted:** `obj_T21_silverbird` eventFlag → `FLAG_HIDE_CHERRYGROVE_SILVER` and `hide_person` after `apoc_fly_away`, so it stays gone after leaving/re-entering.

### 9.5 Still open / next increment

- **#7 Scene 2A + retire legacy flows:** add the grass-block (the player can't head north without a Pokémon — but it's no longer the dead Guide-Gent; Gold or a sign stops them and points to Gold's house), and **detach/neutralize `scr_seq_T21_001/002/003`** (the dead Guide-Gent tour + road-rival) so they never fire. Also confirm overworld Kestra's presence/path between Scene 1 and the ceremony.
- **Reconcile the starter ceremony** with the new premise: the player is a Kalos transplant, so Gold giving the Johto starters needs an in-fiction reason (Gold takes a shine to the new kid; or Elm/Gold arrange it) — tighten the framing.
- **Apply §9.1** (the engine intro cut) as its own focused increment.

---

## 10. Scene 2 — REWRITTEN (committed; supersedes the §7 grass-block warp & the §8 in-house ceremony)

The starter no longer comes from a grass-block → warp → in-house ceremony. New flow is a multi-map cutscene: **town → north route rescue → town tour → outdoor ceremony at Gold's house**. It characterizes Gold as a humble, socially-awkward retiree who'd rather garden than play Champion, and pays off Kestra's pushiness. Spans **Cherrygrove (T21)**, the **north route (R30)**, and **Gold's house (T21R0401)**.

**Naming dependency:** the dialogue uses the player's name, so naming must already have happened — i.e., during the **Scene 1 Kestra first-meeting** (§9.1 / to build). Until naming is wired, the name STRVAR shows the default.

### Beat sequence (with committed dialogue)

1. **Kestra bolts north.** After Scene 1, Kestra gets excited and runs off to the route north of town to look for Pokémon. The player follows.
2. **The rescue (on the route).** The player finds Kestra alone, cornered by a wild Pokémon.
3. **Gold steps in — emergency catch.** Gold has no Pokémon on him (his are home), so he has no choice but to catch the wild one. *Gold: "I hope this works!"* (Cutscene catch, not the interactive tutorial — Gold throws, it's caught, Kestra's safe.)
4. **Gold:** "Phew, that was close! You kids can't just run off into tall grass like that. What to do with you two... *Sigh* Alright, come with me. I guess it's my job to show you the ropes now that the old man's gone."
5. **Town tour.** Gold walks the player + Kestra around town (Mart, Center, etc.), ending **outside his house**.
6. **Gold:** "Alright, uh, that's it. You should, uh, go play at home now... or something."
7. **Kestra:** "Aren't you going to give us our own very first Pokémon now?!"
8. **Gold:** "Uh..."
9. **Kestra:** "Come onnnn! That's what Champions doooo, right? Right, {PLAYER}?!"
10. **Gold:** "Well, uh, I mean I suppose so..."
11. **Kestra:** "Yaaaay! My HERO!"
12. **Gold:** "Uh, ok, wait right here." → *goes inside, ~1-second pause, comes back out.*
13. **Gold:** "Ok, here we go. These three Pokémon are very special to me. You can each pick one, but you have to promise to take really good care of them, ok?"
14. **Kestra:** "Yaaaay! {PLAYER}, you go first!"
15. **Player chooses** (outdoor `choose_starter`); **Kestra takes the type-disadvantaged counter** (Chikorita→she takes Cyndaquil, etc. — logic already built in §8/`scr_seq_T21R0401_002`, to be relocated outdoors).
16. **Kestra runs off toward New Bark:** "Smell ya later!"
17. **Gold:** "You should probably go keep an eye on her... Welp, Typhlosion and I have some gardening to do. Good luck out there." → *goes into his house.*
18. **Repeat-interaction flavor (inside Gold's house):** Gold is found talking to his Typhlosion about flowers, trees, and berries from the series, and wondering where he put his old squirt bottle.

### Implementation increments

| # | Piece | Map(s) | Notes / risk |
|---|-------|--------|--------------|
| A | Kestra bolts north; player follows onto the route | T21 → R30 | Rework `scr_seq_T21_013` (drop the grass-block warp); Kestra runs to the route exit + transition |
| B | Route rescue + Gold emergency-catch cutscene | R30 (untouched so far) | Need a wild-mon confrontation + a **scripted Gold catch** (SE + ball throw; simpler than interactive `catching_tutorial`). New objects/script on R30 |
| C | Gold's lament + **town tour** | T21 | Walking choreography (can adapt the retired Guide-Gent tour movements, or simplify/fade). Movement tables need `.balign` (freeze gotcha) |
| D | **Outdoor ceremony** at Gold's house | T21 | Move `choose_starter` + counter-pick + "promise to care" dialogue outdoors; reuse the built counter-pick logic |
| E | Kestra → New Bark ("Smell ya later"); Gold → house | T21 | Kestra departs east; Gold hides into house |
| F | Gold + Typhlosion gardening flavor (repeat talk) | T21R0401 | Replaces the in-house ceremony; Gold's idle dialogue about flowers/berries/squirt bottle |

**Supersedes:** the §7 `scr_seq_T21_013` grass-block→warp, and the §8 in-house ceremony (`scr_seq_T21R0401_002` choosing moves outdoors; the house interior becomes the gardening-flavor scene). The §8 counter-pick logic and dialogue are reused, relocated.

**Player's own catching tutorial:** in this flow *Gold* catches (cutscene); the player still hasn't caught one themselves. Decide whether the rescue suffices as the catching intro or the player gets a hands-on tutorial later (was Scene 4). **Open.**

### 10b. Refinements (committed — supersede the first-cut staging)

**Location: the rescue is on ROUTE 30 (R30), in the tall grass.** R30 is the route north of Cherrygrove (confirmed: it shares Cherrygrove's x-range and sits above it; the player enters R30 at the **south**, z≈388–390). The Cherrygrove-edge staging (the first cut) is replaced: the player walks north out of town onto R30 and finds Kestra in the grass.

**Revised rescue beat sequence (R30):**
1. **Kestra is in the tall grass, looking around** — searching, calm, in no danger. (A "look around" idle movement.)
2. **Trigger:** the player either **talks to Kestra** OR **steps into the tall grass** → forced interaction, the two **face each other**.
3. **Kestra (friendly, fast):** a real **first-meeting / get-to-know-you** exchange — she's searching for Pokémon, talking a mile a minute, mostly at the player.
4. **A wild mon appears:** *"There's one! Let's get him!"*
5. **Gold arrives:** *"Don't go after wild Pokémon on your own!"* — but **too late**: the mon has noticed them and wants to fight.
6. Continue: Gold's **scripted catch** ("I hope this works!"), his lament, then warp back to Cherrygrove for the **tour + outdoor ceremony** (Script 2, unchanged).

**FREEZE LESSON (important):** the first cut froze right before Gold appeared because it called `move_person_facing` on Gold **while he was still hidden**. **You cannot apply position/movement opcodes to a hidden person** — `show_person` first, *then* move. In the rebuild, **pre-place all actors** (Kestra, the wild mon, Gold) on the R30 map (hidden via flags) and reveal them with `show_person`; never `move_person`/`apply_movement` a hidden object. `move_person`/`move_person_facing` are teleports (opcodes 338/339).

### 10c. Scene 1 polish (committed — separate pass)

- **More spectators** gathered around the Silver/Gold battle, each with **real dialogue about the battle** (reactions to the moves, awe at the Champion, etc.).
- **Kestra must face the player** while talking to him (currently she doesn't).
- **Player framing:** the player must not be left facing away from the battle. They should **always end on the tile just below Kestra**, then **turn to face her** as they converse (right now, if they step right first they can end up facing down).
- **Expand the Kestra conversation** into a genuine **first-meeting / get-to-know-you** — they've never met; mostly Kestra talking at a million miles an hour.