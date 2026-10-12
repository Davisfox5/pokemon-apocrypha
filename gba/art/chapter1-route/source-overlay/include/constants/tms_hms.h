#ifndef GUARD_CONSTANTS_TMS_HMS_H
#define GUARD_CONSTANTS_TMS_HMS_H

// Apocrypha M04: 100 TMs and 11 HMs.
//
// TMs are the generic toolkit: each region stocks only moves its own generation
// introduced, capped at 85 power, and the signature high-power moves are excluded
// and belong to the regional move tutors instead. Regions run in story order.
// Johto, Kanto and Hoenn carry nineteen each rather than twenty, because the three
// Fairy TMs close the list: every offensive Fairy move is Gen 6 or later, so under
// the origin rule no region could stock one. (Charm, Sweet Kiss and Moonlight are
// Gen 2 moves retyped to Fairy and so are Johto-eligible, but all three are status
// moves and none was ever a TM.)
//
// HMs cover traversal and sit outside the TM power cap. The five regions as
// originally built need eleven field moves between them, so there are eleven HMs.
// Defog and Rock Climb are Sinnoh's; Whirlpool is Johto's and was built from
// nothing, modelled on Waterfall.
//
// A block comment placed *inside* either backslash-continued macro truncates it
// silently and produces errors in unrelated files. Keep comments outside.
#define FOREACH_TM(F) \
    /* Johto */ \
    F(PROTECT) \
    F(RETURN) \
    F(HIDDEN_POWER) \
    F(SLEEP_TALK) \
    F(ENDURE) \
    F(ATTRACT) \
    F(RAIN_DANCE) \
    F(SUNNY_DAY) \
    F(SANDSTORM) \
    F(THIEF) \
    F(ICY_WIND) \
    F(SHADOW_BALL) \
    F(GIGA_DRAIN) \
    F(CRUNCH) \
    F(STEEL_WING) \
    F(ANCIENT_POWER) \
    F(ENCORE) \
    F(FALSE_SWIPE) \
    F(DRAGON_BREATH) \
    /* Kanto */ \
    F(TOXIC) \
    F(REST) \
    F(REFLECT) \
    F(LIGHT_SCREEN) \
    F(THUNDER_WAVE) \
    F(SWORDS_DANCE) \
    F(AGILITY) \
    F(BODY_SLAM) \
    F(DIG) \
    F(ROCK_SLIDE) \
    F(THUNDER_PUNCH) \
    F(ICE_PUNCH) \
    F(FIRE_PUNCH) \
    F(LOW_KICK) \
    F(SEISMIC_TOSS) \
    F(CONFUSE_RAY) \
    F(SCREECH) \
    F(COUNTER) \
    F(PSYBEAM) \
    /* Hoenn */ \
    F(FACADE) \
    F(ROCK_TOMB) \
    F(AERIAL_ACE) \
    F(BRICK_BREAK) \
    F(KNOCK_OFF) \
    F(SHOCK_WAVE) \
    F(TAUNT) \
    F(WATER_PULSE) \
    F(SIGNAL_BEAM) \
    F(MUD_SHOT) \
    F(CALM_MIND) \
    F(BULK_UP) \
    F(HAIL) \
    F(IRON_DEFENSE) \
    F(WILL_O_WISP) \
    F(BULLET_SEED) \
    F(MAGICAL_LEAF) \
    F(AIR_CUTTER) \
    F(DRAGON_CLAW) \
    /* Sinnoh */ \
    F(ZEN_HEADBUTT) \
    F(PAYBACK) \
    F(STEALTH_ROCK) \
    F(CHARGE_BEAM) \
    F(POISON_JAB) \
    F(SHADOW_CLAW) \
    F(NASTY_PLOT) \
    F(SEED_BOMB) \
    F(IRON_HEAD) \
    F(DARK_PULSE) \
    F(U_TURN) \
    F(DRAIN_PUNCH) \
    F(ROOST) \
    F(AIR_SLASH) \
    F(TRICK_ROOM) \
    F(NIGHT_SLASH) \
    F(FLASH_CANNON) \
    F(X_SCISSOR) \
    F(AVALANCHE) \
    F(ENERGY_BALL) \
    /* Unova */ \
    F(ROUND) \
    F(BULLDOZE) \
    F(WORK_UP) \
    F(RETALIATE) \
    F(INCINERATE) \
    F(HONE_CLAWS) \
    F(SMACK_DOWN) \
    F(SCALD) \
    F(ACROBATICS) \
    F(PSYSHOCK) \
    F(LOW_SWEEP) \
    F(VENOSHOCK) \
    F(SNARL) \
    F(HEX) \
    F(STRUGGLE_BUG) \
    F(DRAGON_TAIL) \
    F(ELECTROWEB) \
    F(FLAME_CHARGE) \
    F(VOLT_SWITCH) \
    F(DRILL_RUN) \
    /* Fairy -- belongs to no region's past, so it belongs to none of their sets */ \
    F(DAZZLING_GLEAM) \
    F(DISARMING_VOICE) \
    F(DRAINING_KISS)

#define FOREACH_HM(F) \
    F(CUT) \
    F(FLY) \
    F(SURF) \
    F(STRENGTH) \
    F(FLASH) \
    F(ROCK_SMASH) \
    F(WATERFALL) \
    F(DIVE) \
    F(DEFOG) \
    F(ROCK_CLIMB) \
    F(WHIRLPOOL)

#define FOREACH_TMHM(F) \
    FOREACH_TM(F) \
    FOREACH_HM(F)

#endif
