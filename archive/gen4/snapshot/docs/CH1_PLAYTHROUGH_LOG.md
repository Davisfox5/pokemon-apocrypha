# Chapter 1 — Autonomous Playthrough Bug Log

Driven end-to-end via the py-desmume rig (RAM oracle + screenshots). Every beat was
reached and asserted on ground truth (scene var, map, tile) — not guessed from pixels.

Severity: 🟥 blocker (can't continue) · 🟧 major · 🟨 minor/cosmetic · ⬜ deferred-by-design

## Result: chapter is playable up to the **starter ceremony**, then hard-blocks.

| # | Scene | Finding | Sev | Status |
|---|-------|---------|-----|--------|
| 1 | O-1 Cold open | Completes; `HOUSE_1F`→1, player free in house | ✅ | OK |
| 2 | O-1b narration | Text-on-black "…/wake up" lines still not shown | ⬜ | deferred (oaks_speech.c) |
| 3 | O-2 Upstairs PC | Couldn't auto-verify: rig can't fire **interior stairs** warps (doors work, stairs don't). Script *reads* correct (Potion + var=2). | 🟨 | needs human spot-check |
| 4 | O-3 Pokégear `_007` | Fires (verified via scene-jump earlier) | ✅ | OK |
| 5 | SCENE 1 `_012` | **Completes**: `OW`→1 after ~281 presses; naming works; player ends facing Kestra's tile (dir N) | ✅ | OK |
| 6 | SCENE 1 camera | ~~`scrcmd_102` never pans~~ **FIXED**: the camera-pan command is a no-op here, so instead the player now **walks down into the crowd (544,396→554,400)** to watch the fight (recorded path, avoids every actor). Rig-verified: the player is among the crowd with Gold/Silver + onlooker lines on-screen. | 🟧→✅ | **FIXED + verified** |
| 7 | SCENE 1 crowd | **FIXED**: the whole battle crowd (`gsboy1/gsbigman/gsoldman1/gswoman1/gsmiddleman1`) is hidden during the naming fade (no visible pop). Only the permanent Cherrygrove guide NPC remains. | 🟨→✅ | **FIXED + verified** |
| 8 | SCENE 1 length | ~15 message boxes before the player can move; feels long | 🟨 | content note |
| 9 | S2-A Rescue `_013` | Kestra **visible** & searching (the invisible-Kestra fix worked); wild **RATTATA** appears; **catching demo battle runs** (Marill vs Rattata); `OW`→2 | ✅ | OK |
| 10 | S2-A demo hero | Catching demo renders **Marill + generic hero**, not Gold (engine-demo limitation) | ⬜ | by-design caveat |
| 11 | **Ceremony seam** | ~~`_013` warps + `end`s with no `releaseall` → permanent black screen~~ **FIXED**: removed the warp; Gold now walks the player + Kestra home (recorded collision-free choreography) with a Mart/Center tour stop, ducks inside (kids glance, then back to the door), returns, ceremony proceeds. Rig-verified end-to-end: rescue → walk → ceremony → `OW→3`, ends in `field` (no black screen), starter + gear granted. | 🟥→✅ | **FIXED + verified** |
| 12 | S2-B Ceremony | Now reached via the walk; `choose_starter` + Running Shoes + Map Card run; `OW→3`. | ✅ | OK |

### Notes
- "AAAAAAA" in the menu = the **player name the rig typed** by A-mashing the naming keyboard (7 ×'A'), *not* a bug. Useful side-effect: the rig clears `name_player` without a touch handler.
- Rig now navigates the town (greedy nav + warp-avoidance), reaches every coord trigger, and drives long dialogue / the catching battle automatically.

### Fix order
1. 🟥 **#11 ceremony seam** — replace the warp with the "Gold walks them home → house in/out beat → ceremony" sequence (per your direction). *In progress.*
2. 🟧 #6 Scene 1 battle camera.
3. 🟨 #7 hide onlookers, #3 stairs PC human-check.
