# Vanilla Story Ledger

**What this is.** Apocrypha replaces the vanilla HGSS story, but chapters were originally built *additively*: new scenes were injected while the vanilla story machinery stayed in place. A fresh save starts with all vanilla story flags clear, so every vanilla story actor, trigger, and dialogue branch is live unless something explicitly suppresses it. This ledger is the full audit of vanilla story content on every map reachable in Chapters 1–4, with a disposition for each item. It was produced by a ground-truth sweep of the decomp (event JSONs, `scr_seq` scripts, `gmm` text, and engine C code) — **not** from the chapter build docs, whose "removed/hidden" claims were found unreliable (e.g. Silver at Elm's window was documented as hidden but his flag was never set).

**Standing policy (applies to Ch5–8 too).** Every chapter build ends with a *subtractive pass* over its newly reachable maps:
- **REMOVE** — vanilla story actors/cutscenes that don't exist in Apocrypha (Silver-as-thief, Team Rocket, Elm's egg/errand, Lyra/Ethan).
- **RETHEME** — generic NPCs kept, lines rewritten to Apocrypha canon (chosen over removal to keep towns alive).
- **KEEP** — pure flavor/mechanics with no story conflict.
- **GATE** — content that belongs to a later chapter; physically block access.

**Suppression mechanism.** `scr_seq_0149.s` is `_std_init` and runs on **every map load** (`src/fieldmap.c:576`), before objects spawn — a `setflag` there is the canonical way to permanently hide a vanilla actor, and it applies to existing saves on the next map transition. Belt-and-suspenders: also stub the scene scripts that could re-show or re-trigger the content, since map-load inits and scene scripts re-run per load. For phone/engine systems, seed vanilla guard flags at the same place so untouched flag-ladders resolve to neutral branches.

Status legend: ✅ fixed this pass · 🕐 deferred (noted why) · ✔ verified already handled.

---

## 1. New Bark / Route 29 (T20*, R29*)

| Item | Where | Disposition | Status |
|---|---|---|---|
| **Silver at Elm's lab window** (`obj_T20_gsrivel`) — `FLAG_HIDE_NEW_BARK_RIVAL` was never set anywhere | `057_T20.json`, talk `scr_seq_T20_000` | REMOVE — setflag in 0149 + stub talk script | ✅ |
| Marill demo prop in town (`FLAG_HIDE_NEW_BARK_MARILL` never set) | `057_T20.json` | REMOVE — setflag in 0149 | ✅ |
| Lyra/Ethan + Marill in their bedroom (`FLAG_HIDE_NEW_BARK_FRIENDS_ROOM_FRIEND` never set) | `341_T20R0402.json` | REMOVE — setflag in 0149 | ✅ |
| Elm's lab places 3 vanilla starter balls every load | `scr_seq_0843_T20R0101.s` `_010` (`place_starter_balls_in_elms_lab`) | REMOVE call | ✅ |
| Starter-selection script (`choose_starter`, arms vanilla scene chain) | `scr_seq_T20R0101_012` | REMOVE — stub | ✅ |
| Elm-errand intercept (traps player leaving lab, Mr. Pokémon errand) | coord in `058_T20R0101.json` → `_011` | REMOVE — stub | ✅ |
| West-exit Pokégear gate (Elm cameo registers `PHONE_CONTACT_PROF__ELM`) | coord in `057_T20.json` → `scr_seq_T20_002` | REMOVE — stub (also kills Elm phone registration) | ✅ |
| Silver-theft aftermath scene (police, `name_rival`, Mystery Egg) | `scr_seq_T20R0101_002` (+`_014`, egg branches) | REMOVE — stub (dormant, excised for safety) | ✅ |
| R29 vanilla catching tutorial (`scr_seq_R29_001`) | dormant (var armed only by excised lab scene) | REMOVE — stub | ✅ |
| Elm's dialogue tree (starter pitch, errand, egg, Silver lore) | `msg_0543_T20R0101.gmm` + talk `_000` | RETHEME — prune to Pokédex/campus | ✅ |
| Lab aide visible with vanilla lines | `058_T20R0101.json` / `msg_0543` | RETHEME — campus researcher | ✅ |
| "Elm Pokémon Lab" / town signs, gswoman1 "tell your mom", friend's parent ("Lyra is upstairs…"), Elm family 2F, Elm fan (SW house), R29 signs | various T20* gmm | RETHEME | ✅ |
| Stale vanilla rows in rewired player-house gmm (`msg_0545_T20R0201`) | rows 5–141 (Elm favor, Pokégear repair, Mr. Pokémon) | RETHEME/blank dead rows | ✅ |
| Mom, town friend pairs, R29 friend+Marill, lab officer, trophies, Cameron, Tuscany, R29 gatehouse | — | KEEP / verified hidden | ✔ |

## 2. Cherrygrove / Route 30 / Route 31 (T21*, R30*, R31*)

| Item | Where | Disposition | Status |
|---|---|---|---|
| **Lyra + Marill ghost objects in Violet gatehouse** (always visible, sprite resolved every load) | `094_R31R0101.json`, hdr `_001`, scene `_000` (Vs. Recorder) | REMOVE — delete objects, drop sprite-resolve, stub scene | ✅ |
| **R30 battle-demo tableau** (2 kids + Rattata/Pidgey; hide flag only set by excised vanilla lab scene) | `031_R30.json`, `FLAG_HIDE_ROUTE_30_BATTLERS` | REMOVE — setflag in 0149 | ✅ |
| R30 Elm panic call + Mom call wiring | `scr_seq_0227_R30.s` `_001`/`_004` + hdr/coord | REMOVE — stub bodies | ✅ |
| R31 "Is that a Pokémon Egg?" sleeper | `msg_0378_R31` row 11 | RETHEME | ✅ |
| Guide Gent object + tour/map-card/road-rival scenes | T21 — hidden by on-load init; scenes unwired | verified handled | ✔ |
| Mr. Pokémon's house: Oak object deleted, egg/orb scripts stubbed; live script = Quick Claw | `139_R30R0201.json` | verified handled | ✔ |
| Dead text: Guide-Gent tour, in-house starter ceremony, Egg/Oak/Red-Scale, Lyra gate rows | `msg_0550_T21`, `msg_0554_T21R0401`, `msg_0377_R30R0201`, `msg_0379_R31R0101` | REMOVE (blank dead rows) | ✅ |
| Kenya/Spearow loan quest (R31), Apricorn house, Dark Cave R31 side, marts/centers | — | KEEP | ✔ |
| "Badges all over Johto" line (T21R0301) | `msg_0553_T21R0301` row 0 | RETHEME | ✅ |

## 3. Violet region (T22*, D15R*, D24R*, R32, D25R*, R33)

| Item | Where | Disposition | Status |
|---|---|---|---|
| **Elm Egg chain live**: map-entry Elm phone call reveals mart egg aide; taking Togepi Egg corrupts Ch2 scene state (forces OW=3) | `scr_seq_T22_000` (hdr OW==1), `scr_seq_T22FS0101_002`, aide obj | REMOVE — no-op `T22_000` + drop hdr row, stub egg script | ✅ |
| Kimono-girl scene at OW==3 quotes "Mr. Pokémon → Elm → you" | `scr_seq_T22_004`, `msg_0556_T22` rows 13–16 | RETHEME — keep scene, rewrite lines (supernatural thread stays) | ✅ |
| R32 SlowpokeTail salesman ($1,000,000, Rocket-poaching tie-in) | `msg_0380_R32` rows 14–16 | RETHEME | ✅ |
| R32 held-item tutor branches on `BADGE_ZEPHYR` (unearnable) + Egg flag | `scr_seq_0232_R32.s` | RETHEME — repoint checks | ✅ |
| Gym guide/statue `BADGE_ZEPHYR` checks (dead branch) | `scr_seq_0859_T22GYM0101.s` | RETHEME — repoint | ✅ |
| Dead text: Falkner gym rows, Sprout Tower Silver monologue | `msg_0558_T22GYM0101` 0–5, `msg_0056_D15R0103` 0–4 | REMOVE (blank) | ✅ |
| Unown "radio waves" research line | `msg_0073_D24R0102` row 7 | RETHEME | ✅ |
| Sprout Tower 3F Silver cutscene; Earl escort; Union Cave; Roar TM man; Frieda; Ruins Silph seeds | — | verified handled / KEEP | ✔ |

## 4. Azalea region (T23*, D26R*, D36R0101)

| Item | Where | Disposition | Status |
|---|---|---|---|
| Well battles' in-battle identity (VS art, class banners, BGM) | `files/poketool/trainer/trainers.json` | verified already rethemed by the Ch3 data pass — all 8 well trainers are `TRAINERCLASS_SCIENTIST`, leader named "Lead", generic battle music (audit finding was stale) | ✔ |
| Live "You chased off Team Rocket" charcoal-man line (fires post-well+Cut) | `msg_0570_T23R0201` row 2 | RETHEME | ✅ |
| Kurt's dead tail-cutting rows ("cutting off SlowpokeTails for sale", "disbanded by Red") | `msg_0571_T23R0501` rows 0–1 | REMOVE (blank) | ✅ |
| Latent Celebi time-slip (Giovanni past + "Team Rocket's terrible design" text) | `scr_seq_0092_D36R0101.s` `_1F48`, `msg_0115` rows 66–67 | REMOVE — hard-stub branch, blank rows | ✅ |
| Survey-blocker repurpose, adult-Silver scene, Kestra west-exit trigger, Kurt-not-in-well, Farfetch'd quest, kimono dancer | — | verified handled / KEEP | ✔ |

## 5. Goldenrod / Route 34 (T25*, D23R*, D37R*, R34*)

| Item | Where | Disposition | Status |
|---|---|---|---|
| **Whitney's gym fully open** — init *clears* her hide flag; battle → Plain Badge + TM45; 4 gym trainers live | `scr_seq_0886_T25GYM0101.s` `_004`/`_000`, `133_T25GYM0101.json` | REMOVE — init always hides Whitney, trainers re-flagged hidden, guide + signs rethemed to "closed" | ✅ |
| **Radio-Card quiz receptionist live** (grants radio card; Whitney cameo) | `109_D23R0101.json`, `scr_seq_0029_D23R0101.s` | REMOVE — object re-flagged `FLAG_APOC_ALWAYS_HIDDEN` (no radio card in Ch4) | ✅ |
| Tower 2F stair guard says "something wrong with the Director" | `msg_0066_D23R0102` row 4 | RETHEME — keep as blocker, rewrite line | ✅ |
| 5F fake-Director + Petrel stacked on one tile (both visible if floor reached) | `FLAG_HIDE_RADIO_TOWER_5F_PETREL_REVEALED` | REMOVE — setflag in 0149 | ✅ |
| Underground Fashion-Case cutscene fires on first entry (shows hidden Lyra) | `scr_seq_0093_D37R0101.s` `_002` | REMOVE — stub to var-set only | ✅ |
| Photo studio "wear a Team Rocket uniform" | `scr_seq_0094_D37R0102.s` `_006`, `msg_0117` rows 30/37 | RETHEME — plain photo, lines rewritten | ✅ |
| "Whitney went flying by to get a Radio Card!" street line | `msg_0581_T25` row 28 | RETHEME | ✅ |
| Rooftop Whitney (phone-registration path) | `FLAG_UNK_26F` | REMOVE — setflag in 0149 (restore when gym reopens, Ch6+) | ✅ |
| Alphabet rap "…black pajamas is Team Rocket" | `msg_0602_T25R1203` row 7 | RETHEME | ✅ |
| Bill hidden but Eevee `give_mon` intact; family lines vanilla | `scr_seq_0892_T25R0401.s` | RETHEME family lines; Eevee script neutralized | ✅ |
| Basement-Key kid vanilla line | `msg_0117` row 27 | RETHEME | ✅ |
| **Day-Care interior: full vanilla Lyra/Ethan visit cutscene** fired on first entry (friend + Marill visible, walk-and-talk scene; found during implementation, missed by the audit) | `scr_seq_0238_R34R0101.s` `_001`, `302_R34R0101.json` | REMOVE — scene stubbed to var-advance only, both actors re-flagged `FLAG_APOC_ALWAYS_HIDDEN`, phone registration cut | ✅ |
| Rocket takeover crowd/trainers/dept-store lines/coord triggers; train station gating; flower-shop girl | — | verified dead/handled | ✔ |

## 6. Saffron (T11*) — Ch4 endpoint

| Item | Where | Disposition | Status |
|---|---|---|---|
| **All of Kanto open** — Routes 5/6/7/8 gatehouses have no blockers | `348_R05R0301.json`, `346_R06R0201.json`, `445_R07R0101.json`, `347_R08R0201.json` | GATE — blocker script in each gatehouse (walk-back, "routes closed" notice) until Ch5 flag | ✅ |
| **Sabrina's gym fully live** (Marsh Badge + TM48 + "Champion" speech to a 1-badge player) | `scr_seq_0829_T11GYM0101.s`, `366_T11GYM0101.json` | GATE — Sabrina hidden, trainers re-flagged, sign rethemed | ✅ |
| Station guard: "Power Plant broken, train can't run" (contradicts arriving by train) | `msg_0535_T11R0601` row 0 | RETHEME | ✅ |
| Mr. Psychic gives TM29 freely; Silph guard gives Up-Grade | `T11R0501`, `T11R0701` | GATE — gifts deferred behind Ch5 flag, flavor lines kept | ✅ |
| "Team Rocket wanted Silph Co." street line | `msg_0529_T11` row 6 | RETHEME | ✅ |
| Silph elevator open to Rotom room | `359_T11R0701.json` warp | 🕐 deferred — low harm (inert Rotoms); gate properly in Ch5 build | 🕐 |
| Cameron photographer (Saffron), Copycat quest, Karate King | — | KEEP (benign vanilla flavor) | ✔ |
| Fighting Dojo rematch leaders, Lt. Surge, Steven | — | verified self-gated | ✔ |

## 7. Global systems (engine)

| Item | Where | Disposition | Status |
|---|---|---|---|
| **Vanilla guard flags never seeded** — Elm/Mom phone ladders and NPC branches fall into earliest vanilla-story branch | `scr_seq_0149.s` | RETHEME — seed `FLAG_GOT_ELMS_PANIC_CALL`, `FLAG_GAVE_RIVAL_NAME_TO_OFFICER`, `FLAG_GOT_PICK_UP_EGG_CALL_FROM_ELM`, `FLAG_GOT_EGG_FROM_ELMS_ASSISTANT`, `FLAG_SYS_HATCHED_TOGEPI_EGG`, `FLAG_GOT_EVERSTONE_FROM_ELM`, `FLAG_TALKED_TO_MOM_AFTER_NAMING_RIVAL` | ✅ |
| Elm callable via Pokégear (theft/egg/"Team Rocket returned" call ladder) | registration at `scr_seq_0842_T20.s:558` | REMOVE — registration dies with the west-exit scene stub | ✅ |
| Mom's phonebook entry points at `MAP_NEW_BARK_PLAYER_HOUSE_1F` | `files/tel/pmtel_book.json` | no change needed — that map *is* the rewired Cherrygrove player house, so the engine's "home" reference is already consistent | ✔ |
| Route 34 Day-Care registers Lyra + Ethan as contacts (they'd randomly call) | `scr_seq_0238_R34R0101.s:55,59` | REMOVE | ✅ |
| Marill "email from your friend" seeded into PC at new game | `src/overlay_36.c:210-235` | REMOVE | ✅ |
| Gym-leader phone registrations (Falkner/Whitney/Bugsy) | per-gym scripts | 🕐 inert pre-endgame (needs 16 badges); handle per chapter | 🕐 |
| Roamers, Rocket-takeover radio/music, radio card gating, special call slots, badge UI | — | verified safe for Ch1–4 | ✔ |

---

## Known debt surfaced by this pass (not vanilla leftovers — missing Apocrypha content)

- **Ch1 Pokédex hand-off scene is unimplemented.** Nothing in the repo calls `give_pokedex` or sets `FLAG_GOT_POKEDEX`; CHAPTER1_BUILD.md Increment 5 (Elm's lab coord scene) never landed. Elm's talk tree is now wired and ready for it (pre-dex greeting / post-dex line both exist), but the scene itself must be built.
- **Mom's savings offer** (Cherrygrove house) is gated on `VAR_SCENE_ELMS_LAB >= 4`, which nothing can set anymore — re-gate on `FLAG_GOT_POKEDEX` when the Pokédex scene lands.

**Future chapters:** when Ch5+ opens new maps (Kanto proper, Ecruteak, upper Radio Tower, deep Silph), run this same audit on the newly reachable band *before* calling the chapter done: objects (`event_*.h`/zone JSONs, trace every `eventFlag` to an actual setflag), scene scripts/triggers (hdr tables + coord events at fresh var values), gmm text (grep Rocket/Silver/Elm/Lyra/badge-givers), and cross-map systems (phone registrations, radio, rematches, gift items). Also revisit the 🕐 items above.
