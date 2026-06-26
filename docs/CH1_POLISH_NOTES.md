# Chapter 1 — Polish / Player-Experience Notes

Second pass: not "does it run" but "does it feel right to a first-time player who
knows the originals." Watching placement, facing, dialogue wording/pacing, and how
free-roam (walking, talking to NPCs) actually plays. Captured densely via the rig.

Legend: 🟥 broken · 🟧 wrong/confusing · 🟨 minor/cosmetic · 💡 idea · ✅ good

## Cold open (house 1F)
- 🟧 **Intro is the stock HGSS professor sequence** — orange screen, player sprite, "So, you…". Generic; says nothing about Apocrypha/Kalos/the move. (The text-on-black replacement is the deferred `oaks_speech.c` work.)
- ✅ Mom's house dialogue reads fine: "…Honey." → "We made it. Our new home!" → "All the way from Kalos… and" → "The movers…" → "Go on up and see your new room."
- 🟧 **Mom is never placed** — cold-open script `_000` only plays music + 4 messages + `setvar H,1`. She sits at her mid-room spawn (by the table), NOT by the door. So:
  - **Exit is ungated**: the player can walk straight to the door/stairs and leave for Cherrygrove before going upstairs or getting the Pokégear (breaks progression).
  - Mom is awkward to even talk to (a plant pot sits between the player at (5,9) and Mom).
  - During the convo Mom & player are just standing apart mid-room — no staging (e.g. Mom by the door welcoming them in, or turning to face the player).
- 💡 Wants: place Mom to gate the exit until the Pokégear (on/just inside the door, facing the room), or a soft gate ("go set up upstairs first!") on the door tile. Stage the convo so Mom faces the player.

- 🟨 "Wake up, sleepyhead" (msg 41) is a nice frame, but the player is shown **standing** in the room, not asleep/waking — the line implies a bed or a slumped-in-the-car pose we don't see.

## Upstairs 2F + PC
- ✅ PC Potion line fits: "The PC hums to life. There's a POTION tucked inside - left over from the move."
- 🟨 Order is slightly off: Potion is given, THEN "Booted up the PC and checked the Mailbox! / There is no Mail…" — reads backwards (you'd check the PC, then find the Potion).
- 🟨 Second object: **"It's a Wii! Wii is huge in Johto, too!"** — leftover stock-HGSS meme; clashes with Apocrypha's tone. Reword or cut.
- ⚠️ Couldn't drive the 2F live (rig can't fire the interior stairs warp) — content read from source; needs a human spot-check of placement.

## Pokégear handoff (`_007`)
- ✅ Good lines: "There you are! All settled in? Before you head out, let me set you up proper." → "Oh - and this came for you. Your very own Pokégear. Map, phone, radio, clock, all in one." → "There. A real Trainer now. Go see this new town of ours - I'll be right here if you need…"
- 🟧 **msg 45 names "your Trainer Card"** but `_apoc_give_pokegear` doesn't grant it — the Trainer Card/Save are deferred until naming (Scene 1). Menu after the handoff shows only Bag/Options/Pokégear. A first-time player hears "Trainer Card" and opens the menu to find it missing. Drop the Trainer-Card mention here (the player isn't even named yet).
- 🟨 `_007` moves Mom to the tile just north of the player; if the player came down at the stairs landing, Mom lands on/at the stairs — verify she's not standing on them.

## Scene 1 (Silver battle · Kestra · naming)
- ✅ **Player now watches the battle** from inside the crowd (camera fix holds); the Gold/Silver banter ("TYPHLOSION! Fire Blast" / "Alakazam. Psychic. End it." / "Same old Gold.") reads great.
- ✅ Gold **stays interactable** after the scene; his talk line is lovely: "So you're setting out at last… don't rush the road. It goes fast enough on its own. Enjoy every step of it."
- 🟨 **Kestra pops** from her crowd spot (SW of the player) to the tile due-north of the player for the first-meeting (move_person_facing teleport, on-camera). Have her step over instead.
- ⚠️ Couldn't 100% confirm from frames: (a) Kestra faces the player during the whole meeting, (b) Gold visibly present at the very end. Want a human eye.

## CONTINUITY (cross-scene — a first-time player WILL notice)
- 🟧 **Gold has no Pokémon?!** Rescue msg 40: "Nothing on me to battle with, either… I hope this works!" — but Gold just **beat the Champion with his Typhlosion** in Scene 1. He shouldn't be weaponless or nervous about a wild Rattata. Either he uses Typhlosion (and the line changes), or Scene 1 needs to explain why he's not carrying his team now.
- 🟧 **Who actually catches the Rattata?** The dialogue says **Gold** does it ("…I hope this works! …Gotcha. It actually worked."), but the engine `catching_tutorial` hands control to the **player** with a borrowed **Marill**, rendered as the *other-gender hero* sprite — not Gold. The shown action contradicts the words. (Known caveat — needs a decision: live with the engine demo + reword, or build a custom "Gold throws the ball" cutscene.)

## Rescue + walk-home + ceremony
- ✅ Rescue staging reads right: player center, Kestra (pink) NE searching, Gold rushes in from the south, Rattata in the grass. Dialogue is strong ("There you are, slowpoke!… THERE'S one!").
- 🟨 **Catching tutorial is long & forced** — the full engine guided demo (Marill vs Rattata) runs ~150 A-presses before the story resumes. For a returning player who knows how to catch, it's a slog; and it's framed as Gold's catch but the player drives it.
- ✅ Walk-home works: all three traverse town; tour stop fires ("That's the Poké Mart - it keeps you stocked…").
- 🟨 **Tour-stop framing**: the group halts next to a *house*; the blue-roofed Mart is off in the upper-right. Reads a little vague about which building is "the Mart." Could stop closer / have Gold gesture at it.
- ✅ House in/out beat works (Gold ducks in on "Wait right here," returns on "Ok, here we go").
- ✅ Starter selection presents normally (Chikorita/Cyndaquil/Totodile in Poké Balls); starter then follows the player; Running Shoes + Map Card granted; Kestra & Gold exit; player left with their starter.

---

## ✅ FIXED THIS PASS (verified via rig)
- **Gold catches the Rattata himself** — replaced the player/Marill catching-tutorial with a Gold-throws-the-ball cutscene (face → throw SE → it struggles → caught fanfare). No wrong-gender hero, no ~150-press tutorial (scene is ~160 presses shorter), and his lines are reworded confident ("Stand back… let me show you how this is done." / "...And - gotcha. Still got the touch.") — fixes the "no Pokémon / nervous" continuity.
- **Door is gated** — Mom steps onto the front door at the end of the cold open and blocks BOTH the direct path and the (4,10) bypass; the player can't leave for Cherrygrove at H=1. She moves off at the Pokégear hand-off.
- **Mom faces the player** during the cold-open conversation (was: back turned).
- **Pokégear line fixed** — Mom no longer claims "your Trainer Card and the save… all in your menu now" (those are deferred to naming); now just Bag + options.
- **"It's a Wii" replaced** with a tone-appropriate moved-in flavor line.

# PRIORITIZED SUMMARY (for a first-time player who knows the originals)

### Clear fixes I can just make
1. 🟧 **Mom doesn't gate the exit / isn't staged.** Place her to block the door until the Pokégear (or a soft "go upstairs first!" gate), and stage the cold-open convo so she faces the player (and isn't behind a plant).
2. 🟧 **Pokégear names the "Trainer Card"** the player can't open yet (deferred to naming). Cut the Trainer-Card mention from Mom's line.
3. 🟧 **Gold's continuity:** rescue line "Nothing on me to battle with… I hope this works!" contradicts him beating the Champion with Typhlosion ~2 minutes earlier. Reword (e.g. he *won't* sic a champion's Typhlosion on a baby Rattata, or lends the kids the ball).
4. 🟨 **"It's a Wii! Wii is huge in Johto"** — stock-HGSS meme; reword to fit Apocrypha.
5. 🟨 **2F PC order** — give the Potion *after* the "checked the Mailbox / no Mail" beat.
6. 🟨 **Kestra teleport-pop** in Scene 1 — have her step over to the player instead of snapping north.
7. 🟨 **Tour-stop framing** — halt nearer the Mart/Center or have Gold face them.

### Needs your call (design / bigger work)
8. 🟧 **Stock professor intro** ("So, you…") still plays — generic, says nothing about Apocrypha. The text-on-black cold open (oaks_speech.c) replaces it. Greenlight?
9. 🟧 **Catching demo = Gold or the player?** Engine demo is player-driven with a Marill rendered as the *wrong-gender hero*, but the script says Gold catches it. Live with engine demo + reword, OR build a custom "Gold throws the ball" cutscene (C work)?
10. 🟨 **Forced full catching tutorial length** — keep, or shorten/skip for pace?

### Minor / cosmetic
- "Wake up, sleepyhead" while the player stands (no bed/waking pose).
