// Run through build.py --mechanics; does not override the production settings.
#include "global.h"
#include "test/battle.h"
#include "battle_util.h"
#include "field_move.h"
#include "metatile_behavior.h"
#include "constants/metatile_behaviors.h"

TEST("Apocrypha Fairy chart and retyped moves remain canonical")
{
    EXPECT_EQ(gSpeciesInfo[SPECIES_CLEFAIRY].types[0], TYPE_FAIRY);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].types[0], TYPE_FAIRY);
    EXPECT_EQ(GetMoveType(MOVE_CHARM), TYPE_FAIRY);
    EXPECT_EQ(GetTypeModifier(TYPE_DRAGON, TYPE_FAIRY), UQ_4_12(0.0));
    EXPECT_EQ(GetTypeModifier(TYPE_FAIRY, TYPE_DRAGON), UQ_4_12(2.0));
    EXPECT_EQ(GetTypeModifier(TYPE_POISON, TYPE_FAIRY), UQ_4_12(2.0));
    EXPECT_EQ(GetTypeModifier(TYPE_STEEL, TYPE_FAIRY), UQ_4_12(2.0));
    EXPECT_EQ(GetTypeModifier(TYPE_GHOST, TYPE_STEEL), UQ_4_12(1.0));
    EXPECT_EQ(GetTypeModifier(TYPE_DARK, TYPE_STEEL), UQ_4_12(1.0));
}

AI_SINGLE_BATTLE_TEST("Apocrypha opposing trainers deal Thief/Covet damage without stealing player items")
{
    enum Move move;
    PARAMETRIZE { move = MOVE_THIEF; }
    PARAMETRIZE { move = MOVE_COVET; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_HYPER_POTION); }
        OPPONENT(SPECIES_WOBBUFFET) { Moves(move); }
    } WHEN {
        TURN { EXPECT_MOVE(opponent, move); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, move, opponent);
        HP_BAR(player);
        NOT ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_ITEM_STEAL, player);
    } THEN {
        EXPECT_EQ(player->item, ITEM_HYPER_POTION);
        EXPECT_EQ(opponent->item, ITEM_NONE);
    }
}

WILD_BATTLE_TEST("Apocrypha catches award no experience")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Level(20); }
        OPPONENT(SPECIES_CATERPIE) { HP(1); }
    } WHEN {
        TURN { USE_ITEM(player, ITEM_ULTRA_BALL, WITH_RNG(RNG_BALLTHROW_SHAKE, 0)); }
    } SCENE {
        NOT EXPERIENCE_BAR(player);
    } THEN {
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP),
                  gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][20]);
    }
}

WILD_BATTLE_TEST("Apocrypha lower-level recipients earn more experience", s32 exp)
{
    u8 level;
    PARAMETRIZE { level = 10; }
    PARAMETRIZE { level = 20; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Level(level); }
        OPPONENT(SPECIES_CATERPIE) { Level(10); HP(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } SCENE {
        EXPERIENCE_BAR(player, captureGainedExp: &results[i].exp);
    } FINALLY {
        EXPECT_GT(results[0].exp, results[1].exp);
    }
}

WILD_BATTLE_TEST("Apocrypha held Exp Share divides rewards and excludes other inactive Pokemon", s32 activeExp)
{
    enum Item item;
    PARAMETRIZE { item = ITEM_NONE; }
    PARAMETRIZE { item = ITEM_EXP_SHARE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Level(40); }
        PLAYER(SPECIES_WOBBUFFET) { Level(40); Item(item); }
        PLAYER(SPECIES_WOBBUFFET) { Level(40); }
        OPPONENT(SPECIES_CATERPIE) { Level(10); HP(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } SCENE {
        EXPERIENCE_BAR(player, captureGainedExp: &results[i].activeExp);
    } THEN {
        u32 initial = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][40];
        u32 second = GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP);
        if (item == ITEM_EXP_SHARE)
            EXPECT_GT(second, initial);
        else
            EXPECT_EQ(second, initial);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][2], MON_DATA_EXP), initial);
    } FINALLY {
        EXPECT_GT(results[0].activeExp, results[1].activeExp);
    }
}

AI_SINGLE_BATTLE_TEST("Apocrypha trainer reward includes classic bonus without delayed evolution bonus")
{
    GIVEN {
        PLAYER(SPECIES_METAPOD) { Level(20); Speed(100); }
        OPPONENT(SPECIES_CATERPIE) { Level(20); HP(1); Speed(1); Moves(MOVE_SPLASH); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } THEN {
        // Equal levels make Gen 5's level ratio exactly one. Round before bonus.
        u32 expected = (gSpeciesInfo[SPECIES_CATERPIE].expYield * 20 / 5) * 150 / 100 + 1;
        u32 initial = gExperienceTables[gSpeciesInfo[SPECIES_METAPOD].growthRate][20];
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), initial + expected);
    }
}

WILD_BATTLE_TEST("Apocrypha participants divide the defeated Pokemon experience")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Level(20); Speed(100); }
        PLAYER(SPECIES_WOBBUFFET) { Level(20); Speed(100); }
        OPPONENT(SPECIES_CATERPIE) { Level(20); HP(1); Speed(1); }
    } WHEN {
        TURN { SWITCH(player, 1); MOVE(opponent, MOVE_SPLASH); }
        TURN { MOVE(player, MOVE_SCRATCH); }
    } THEN {
        u32 expected = (gSpeciesInfo[SPECIES_CATERPIE].expYield * 20 / 5) / 2 + 1;
        u32 initial = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][20];
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), initial + expected);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_EXP), initial + expected);
    }
}

// M03a: P_UPDATED_STATS is pinned to GEN_5, so every selector gated on GEN_6 or
// later resolves to the B2W2 value. One species is sampled per affected family
// file; the Fairy/Mega exceptions are checked separately below.
TEST("Apocrypha Gen 1-5 base stats follow Black 2 / White 2")
{
    // Gen 1 selectors that Gen 6 or Gen 7 later raised.
    EXPECT_EQ(gSpeciesInfo[SPECIES_PIKACHU].baseDefense, 30);
    EXPECT_EQ(gSpeciesInfo[SPECIES_PIKACHU].baseSpDefense, 40);
    EXPECT_EQ(gSpeciesInfo[SPECIES_RAICHU].baseSpeed, 100);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM].baseSpDefense, 85);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BUTTERFREE].baseSpAttack, 80);
    EXPECT_EQ(gSpeciesInfo[SPECIES_WIGGLYTUFF].baseSpAttack, 75);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VICTREEBEL].baseSpDefense, 60);
    EXPECT_EQ(gSpeciesInfo[SPECIES_DUGTRIO].baseAttack, 80);
    EXPECT_EQ(gSpeciesInfo[SPECIES_FARFETCHD].baseAttack, 65);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ELECTRODE].baseSpeed, 140);
    EXPECT_EQ(gSpeciesInfo[SPECIES_EXEGGUTOR].baseSpDefense, 65);
    // Gen 2.
    EXPECT_EQ(gSpeciesInfo[SPECIES_AZUMARILL].baseSpAttack, 50);
    EXPECT_EQ(gSpeciesInfo[SPECIES_AMPHAROS].baseDefense, 75);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CORSOLA].baseHP, 55);
    EXPECT_EQ(gSpeciesInfo[SPECIES_MANTINE].baseHP, 65);
    // Gen 3.
    EXPECT_EQ(gSpeciesInfo[SPECIES_CHIMECHO].baseHP, 65);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VOLBEAT].baseDefense, 55);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ROSERADE].baseDefense, 55);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BEAUTIFLY].baseSpAttack, 90);
    // Gen 4. Cresselia was lowered after Gen 5, not raised.
    EXPECT_EQ(gSpeciesInfo[SPECIES_STARAPTOR].baseSpDefense, 50);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CRESSELIA].baseDefense, 120);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CRESSELIA].baseSpDefense, 130);
    // Gen 5.
    EXPECT_EQ(gSpeciesInfo[SPECIES_STOUTLAND].baseAttack, 100);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BEARTIC].baseAttack, 110);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CRYOGONAL].baseHP, 70);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CRYOGONAL].baseDefense, 30);
    EXPECT_EQ(gSpeciesInfo[SPECIES_KROOKODILE].baseDefense, 70);
}

// Selectors gated on GEN_2 must stay on their post-Gen 1 branch: the special
// split is part of the Gen 5 data, not something GEN_5 should roll back.
TEST("Apocrypha Gen 5 stats do not revert Gen 1 special stats")
{
    EXPECT_EQ(gSpeciesInfo[SPECIES_CHARIZARD].baseSpAttack, 109);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BLASTOISE].baseSpDefense, 105);
    EXPECT_EQ(gSpeciesInfo[SPECIES_GENGAR].baseSpDefense, 75);
    EXPECT_EQ(gSpeciesInfo[SPECIES_EEVEE].baseSpAttack, 45);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VENOMOTH].baseSpAttack, 90);
}

// The approved exceptions: species that do not exist in Gen 5 keep the stats
// they actually shipped with.
TEST("Apocrypha Sylveon and retained Mega forms keep canonical later stats")
{
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseHP, 95);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseAttack, 65);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseDefense, 65);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseSpeed, 60);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseSpAttack, 110);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].baseSpDefense, 130);
    // Mega Alakazam is the only retained Mega whose stats the selector reached.
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM_MEGA].baseSpDefense, 105);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM_MEGA].baseSpAttack, 175);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM_MEGA].baseSpeed, 150);
    // Unaffected Megas still read their own entries, not the base form's.
    EXPECT_EQ(gSpeciesInfo[SPECIES_CHARIZARD_MEGA_Y].baseSpAttack, 159);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VENUSAUR_MEGA].baseSpDefense, 120);
}

// M03b: P_UPDATED_ABILITIES is pinned to GEN_5. Selectors gated on >= GEN_4 stay
// on their Gen 4/5 branch; selectors gated on GEN_6 or later fall back to the
// Black 2 / White 2 ability set unless the owner pinned an exception.
TEST("Apocrypha Gen 1-5 abilities follow Black 2 / White 2")
{
    // Later additions that Gen 5 removes.
    EXPECT_EQ(gSpeciesInfo[SPECIES_JIGGLYPUFF].abilities[1], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_GOTHITELLE].abilities[1], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_KECLEON].abilities[2], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_STARLY].abilities[2], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_DUSKNOIR].abilities[2], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_FERROTHORN].abilities[2], ABILITY_NONE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_PLUSLE].abilities[2], ABILITY_NONE);
    // Later swaps that Gen 5 reverses; the owner kept these Gen 5 versions.
    EXPECT_EQ(gSpeciesInfo[SPECIES_ZAPDOS].abilities[2], ABILITY_LIGHTNING_ROD);
    EXPECT_EQ(gSpeciesInfo[SPECIES_RAIKOU].abilities[2], ABILITY_VOLT_ABSORB);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ENTEI].abilities[2], ABILITY_FLASH_FIRE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SUICUNE].abilities[2], ABILITY_WATER_ABSORB);
    EXPECT_EQ(gSpeciesInfo[SPECIES_EMPOLEON].abilities[2], ABILITY_DEFIANT);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SHIFTRY].abilities[1], ABILITY_EARLY_BIRD);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SCOLIPEDE].abilities[2], ABILITY_QUICK_FEET);
    // Gen 4-era ability updates are part of the Gen 5 data and must survive.
    EXPECT_EQ(gSpeciesInfo[SPECIES_CLOYSTER].abilities[1], ABILITY_SKILL_LINK);
}

// The owner-approved M03b exceptions, in both directions.
TEST("Apocrypha owner ability exceptions override the Gen 5 baseline")
{
    // Kept from present-day: the four weather setters and their families.
    EXPECT_EQ(gSpeciesInfo[SPECIES_TORKOAL].abilities[1], ABILITY_DROUGHT);
    EXPECT_EQ(gSpeciesInfo[SPECIES_PELIPPER].abilities[1], ABILITY_DRIZZLE);
    EXPECT_EQ(gSpeciesInfo[SPECIES_GIGALITH].abilities[1], ABILITY_SAND_STREAM);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VANILLUXE].abilities[1], ABILITY_SNOW_WARNING);
    EXPECT_EQ(gSpeciesInfo[SPECIES_WINGULL].abilities[1], ABILITY_HYDRATION);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ROGGENROLA].abilities[1], ABILITY_WEAK_ARMOR);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BOLDORE].abilities[1], ABILITY_WEAK_ARMOR);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VANILLITE].abilities[1], ABILITY_SNOW_CLOAK);
    EXPECT_EQ(gSpeciesInfo[SPECIES_VANILLISH].abilities[1], ABILITY_SNOW_CLOAK);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CUBCHOO].abilities[1], ABILITY_SLUSH_RUSH);
    EXPECT_EQ(gSpeciesInfo[SPECIES_BEARTIC].abilities[1], ABILITY_SLUSH_RUSH);
    // Kept from present-day: Neutralizing Gas and Sharpness.
    EXPECT_EQ(gSpeciesInfo[SPECIES_KOFFING].abilities[1], ABILITY_NEUTRALIZING_GAS);
    EXPECT_EQ(gSpeciesInfo[SPECIES_WEEZING].abilities[1], ABILITY_NEUTRALIZING_GAS);
    EXPECT_EQ(gSpeciesInfo[SPECIES_GALLADE].abilities[1], ABILITY_SHARPNESS);
    // Overridden away from the Gen 5 restoration.
    EXPECT_EQ(gSpeciesInfo[SPECIES_GENGAR].abilities[0], ABILITY_CURSED_BODY);
    EXPECT_EQ(gSpeciesInfo[SPECIES_LITWICK].abilities[2], ABILITY_INFILTRATOR);
    EXPECT_EQ(gSpeciesInfo[SPECIES_LAMPENT].abilities[2], ABILITY_INFILTRATOR);
    EXPECT_EQ(gSpeciesInfo[SPECIES_CHANDELURE].abilities[2], ABILITY_INFILTRATOR);
    // Mega Gengar keeps its own entry rather than the base form's pinned macro.
    EXPECT_EQ(gSpeciesInfo[SPECIES_GENGAR_MEGA].abilities[0], ABILITY_SHADOW_TAG);
}

// M03c: P_LVL_UP_LEARNSETS is GEN_6 (ORAS) and B_UPDATED_MOVE_DATA is GEN_5.
// Returns the FIRST level at which the species learns the move; some species
// learn the same move twice (Gardevoir learns Moonblast at 1 and again at 62).
static u32 ApocryphaLevelUpMoveLevel(enum Species species, enum Move move)
{
    const struct LevelUpMove *learnset = GetSpeciesLevelUpLearnset(species);
    u32 i;

    for (i = 0; learnset[i].move != LEVEL_UP_MOVE_END; i++)
    {
        if (learnset[i].move == move)
            return learnset[i].level;
    }
    return 0;
}

TEST("Apocrypha level-up learnsets are the ORAS set")
{
    // Levels that identify ORAS specifically: Marill learns Play Rough at 23
    // here and at 21 in the present-day games; Whimsicott's Moonblast is at 50
    // rather than level 1; Gardevoir's Draining Kiss is at 23 rather than 12.
    EXPECT_EQ(ApocryphaLevelUpMoveLevel(SPECIES_MARILL, MOVE_PLAY_ROUGH), 23);
    EXPECT_EQ(ApocryphaLevelUpMoveLevel(SPECIES_WHIMSICOTT, MOVE_MOONBLAST), 50);
    EXPECT_EQ(ApocryphaLevelUpMoveLevel(SPECIES_GARDEVOIR, MOVE_DRAINING_KISS), 23);
}

// The reason ORAS was chosen over Gen 5: at Gen 5 learnsets, 22 of the 23
// Fairy-typed species on this roster learn no Fairy attacking move at all, and
// the TM list has no Fairy move to teach them.
TEST("Apocrypha Fairy species can attack with their own type")
{
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_CLEFABLE, MOVE_DISARMING_VOICE), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_WIGGLYTUFF, MOVE_PLAY_ROUGH), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_AZUMARILL, MOVE_PLAY_ROUGH), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_GRANBULL, MOVE_PLAY_ROUGH), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_MAWILE, MOVE_PLAY_ROUGH), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_GARDEVOIR, MOVE_MOONBLAST), 0);
    EXPECT_NE(ApocryphaLevelUpMoveLevel(SPECIES_SYLVEON, MOVE_MOONBLAST), 0);
    // Togekiss has none of its own; it carries Fairy Wind up from Togetic.
    EXPECT_EQ(ApocryphaLevelUpMoveLevel(SPECIES_TOGETIC, MOVE_FAIRY_WIND), 14);
    // Owner-approved M03c exception: ORAS leaves Mr. Mime with no Fairy move.
    EXPECT_EQ(ApocryphaLevelUpMoveLevel(SPECIES_MR_MIME, MOVE_DAZZLING_GLEAM), 44);
}

TEST("Apocrypha move power, accuracy and PP follow Gen 5")
{
    // Gen 6 toned these down; Gen 5 restores the higher power.
    EXPECT_EQ(GetMovePower(MOVE_FLAMETHROWER), 95);
    EXPECT_EQ(GetMovePower(MOVE_SURF), 95);
    EXPECT_EQ(GetMovePower(MOVE_ICE_BEAM), 95);
    EXPECT_EQ(GetMovePower(MOVE_THUNDERBOLT), 95);
    EXPECT_EQ(GetMovePower(MOVE_HYDRO_PUMP), 120);
    EXPECT_EQ(GetMovePower(MOVE_BLIZZARD), 120);
    EXPECT_EQ(GetMovePower(MOVE_FIRE_BLAST), 120);
    // Restored PP and accuracy.
    EXPECT_EQ(GetMovePP(MOVE_SWORDS_DANCE), 30);
    EXPECT_EQ(GetMovePP(MOVE_GROWTH), 40);
    EXPECT_EQ(GetMoveAccuracy(MOVE_THUNDER_WAVE), 100);
    // Gen 5 also reverses later buffs; this is not a one-way power increase.
    EXPECT_EQ(GetMovePower(MOVE_VINE_WHIP), 35);
    // Blizzard's accuracy selector is gated on GEN_2 and must stay on 70.
    EXPECT_EQ(GetMoveAccuracy(MOVE_BLIZZARD), 70);
    // Fairy moves carry no move-data selector and must be untouched.
    EXPECT_EQ(GetMovePower(MOVE_MOONBLAST), 95);
    EXPECT_EQ(GetMovePower(MOVE_DAZZLING_GLEAM), 80);
    EXPECT_EQ(GetMovePower(MOVE_PLAY_ROUGH), 90);
}

// M03d: P_UPDATED_EXP_YIELDS is pinned to GEN_5. Selectors gated on GEN_6 or
// later fall back to the Black 2 / White 2 yield, roughly 10% below the
// present-day value for the ~190 roster species that changed.
TEST("Apocrypha species experience yields follow Gen 5")
{
    EXPECT_EQ(gSpeciesInfo[SPECIES_CLEFABLE].expYield, 213);
    EXPECT_EQ(gSpeciesInfo[SPECIES_NIDOKING].expYield, 223);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM].expYield, 221);
    // Resolved through the shared GENGAR_EXP_YIELD macro, not an inline selector.
    EXPECT_EQ(gSpeciesInfo[SPECIES_GENGAR].expYield, 225);
    // Species with no selector are untouched.
    EXPECT_EQ(gSpeciesInfo[SPECIES_BULBASAUR].expYield, 64);
    EXPECT_EQ(gSpeciesInfo[SPECIES_SYLVEON].expYield, 184);
    // Megas needed no pin: their selectors fall back to a real Gen 6 or Gen 7
    // value rather than a pre-Mega number, and none resolves to zero. Mega
    // Alakazam takes 266, its Gen 6 figure, since its Gen 7 yield rise came with
    // the Sp. Def change that M03a pinned separately for base stats only.
    EXPECT_EQ(gSpeciesInfo[SPECIES_VENUSAUR_MEGA].expYield, 281);
    EXPECT_EQ(gSpeciesInfo[SPECIES_ALAKAZAM_MEGA].expYield, 266);
}

// M04: 100 TMs, twenty per region, each stocked with generic moves that the
// region's own generation introduced, capped at 85 power. Signature high-power
// moves are deliberately absent; they belong to the regional tutors.
// TMs remain single-use (I_REUSABLE_TMS is FALSE).
TEST("Apocrypha TM list is the curated per-region set")
{
    EXPECT_EQ(NUM_TECHNICAL_MACHINES, 100);
    EXPECT_EQ(NUM_ALL_MACHINES, 111); // 100 TMs + 11 HMs
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_GIGA_DRAIN), MOVE_GIGA_DRAIN);      // Johto
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_THUNDER_PUNCH), MOVE_THUNDER_PUNCH); // Kanto
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_BRICK_BREAK), MOVE_BRICK_BREAK);    // Hoenn
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_IRON_HEAD), MOVE_IRON_HEAD);        // Sinnoh
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_SCALD), MOVE_SCALD);                // Unova
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_ROOST), ITEM_TM_ROOST);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_HM_SURF), MOVE_SURF);
    // Single-use: importance 0 means the item is consumed on use.
    EXPECT_EQ((u32)gItemsInfo[ITEM_TM_SCALD].importance, 0);
}

// Every offensive Fairy move is Gen 6 or later, so no region could stock one.
// The three Fairy TMs close the list at 98-100 and Johto, Kanto and Hoenn carry
// nineteen each to pay for them. Without these the list had no Fairy move at all,
// and no TM could have one under the origin rule.
TEST("Apocrypha stocks Fairy TMs outside the regional sets")
{
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_DAZZLING_GLEAM), MOVE_DAZZLING_GLEAM);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_DISARMING_VOICE), MOVE_DISARMING_VOICE);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_DRAINING_KISS), MOVE_DRAINING_KISS);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_DAZZLING_GLEAM), ITEM_TM_DAZZLING_GLEAM);
    // They are the last three, so the regional blocks stay contiguous before them.
    EXPECT_EQ(GetItemTMHMIndex(ITEM_TM_DAZZLING_GLEAM), 98);
    EXPECT_EQ(GetItemTMHMIndex(ITEM_TM_DRAINING_KISS), 100);
}

// The rebalancing pass: Dragon had one attacking TM and Psychic two, while Normal
// carried twelve, eight of them near-duplicates. These are the moves that moved.
TEST("Apocrypha TM rebalance filled the thin types and cut the duplicates")
{
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_DRAGON_BREATH), MOVE_DRAGON_BREATH); // Johto
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_DRAGON_CLAW), MOVE_DRAGON_CLAW);     // Hoenn
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_PSYBEAM), MOVE_PSYBEAM);             // Kanto
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_TM_ENERGY_BALL), MOVE_ENERGY_BALL);     // Sinnoh
    // Dropped: two Normal near-duplicates, an evasion move, and four weak entries.
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_FRUSTRATION), ITEM_NONE);  // Return mirrored
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_SECRET_POWER), ITEM_NONE); // Facade duplicate
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_DOUBLE_TEAM), ITEM_NONE);  // evasion stalling
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_SWIFT), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_SAFEGUARD), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_TORMENT), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_GRASS_KNOT), ITEM_NONE);   // weight-variable
}

// No TM may teach a signature move. These are reserved for the regional tutors,
// which are gated behind rare cross-region items and unlock late.
TEST("Apocrypha signature moves are not obtainable from TMs")
{
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_THUNDERBOLT), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_ICE_BEAM), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_FLAMETHROWER), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_FIRE_BLAST), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_BLIZZARD), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_THUNDER), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_EARTHQUAKE), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_HYPER_BEAM), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_GIGA_IMPACT), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_OVERHEAT), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_DRACO_METEOR), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_BLAST_BURN), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_HYDRO_CANNON), ITEM_NONE);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_FRENZY_PLANT), ITEM_NONE);
}

// Traversing all five regions as they were originally built needs eleven field
// moves against eight HM slots. Defog and Rock Climb are Sinnoh's; they are HMs
// rather than TMs so they cost no region a TM slot. Field moves key on the move
// and not the HM item, so the ids need not be contiguous with HM01-HM08 -- but
// they are, because every item from 690 up was shifted by two.
TEST("Apocrypha ships eleven HMs including Defog, Rock Climb and Whirlpool")
{
    EXPECT_EQ(NUM_HIDDEN_MACHINES, 11);
    EXPECT_EQ(NUM_ALL_MACHINES, 111);
    EXPECT_EQ(NUM_TECHNICAL_MACHINES, 100);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_HM_DEFOG), MOVE_DEFOG);
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_HM_ROCK_CLIMB), MOVE_ROCK_CLIMB);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_DEFOG), ITEM_HM_DEFOG);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_ROCK_CLIMB), ITEM_HM_ROCK_CLIMB);
    // HMs are not consumed and cannot be tossed.
    EXPECT_EQ((u32)gItemsInfo[ITEM_HM_DEFOG].importance, 1);
    EXPECT_EQ((u32)gItemsInfo[ITEM_HM_ROCK_CLIMB].importance, 1);
    // The renumbering must not have collided the HM block with the charms.
    EXPECT_EQ(ITEM_HM09, ITEM_HM08 + 1);
    EXPECT_EQ(ITEM_HM10, ITEM_HM08 + 2);
    EXPECT_EQ(ITEM_OVAL_CHARM, ITEM_HM11 + 1);
    // Both field moves must actually be reachable, not compiled out.
    EXPECT(gFieldMoveInfo[FIELD_MOVE_DEFOG].unlockType != CANT_UNLOCK);
    EXPECT(gFieldMoveInfo[FIELD_MOVE_ROCK_CLIMB].unlockType != CANT_UNLOCK);
    EXPECT_EQ((u32)gFieldMoveInfo[FIELD_MOVE_DEFOG].moveID, MOVE_DEFOG);
    EXPECT_EQ((u32)gFieldMoveInfo[FIELD_MOVE_ROCK_CLIMB].moveID, MOVE_ROCK_CLIMB);
}

// Whirlpool had no engine support at all: no metatile behavior, no FieldMove
// entry, no field effect. It is built here because Johto's whirlpools gate Whirl
// Islands and the Route 41 crossing, and the alternative -- re-cutting them as
// dive sites -- would mean producing new underwater maps.
TEST("Apocrypha Whirlpool is a working field move")
{
    EXPECT_EQ(GetItemTMHMMoveId(ITEM_HM_WHIRLPOOL), MOVE_WHIRLPOOL);
    EXPECT_EQ(GetTMHMItemIdFromMoveId(MOVE_WHIRLPOOL), ITEM_HM_WHIRLPOOL);
    EXPECT_EQ((u32)gItemsInfo[ITEM_HM_WHIRLPOOL].importance, 1);
    EXPECT_EQ((u32)gFieldMoveInfo[FIELD_MOVE_WHIRLPOOL].moveID, MOVE_WHIRLPOOL);
    EXPECT(gFieldMoveInfo[FIELD_MOVE_WHIRLPOOL].unlockType != CANT_UNLOCK);
    EXPECT(gFieldMoveInfo[FIELD_MOVE_WHIRLPOOL].fieldMoveFunc != NULL);
    // The tile must exist, be surfable, and be recognised only as itself.
    EXPECT(MetatileBehavior_IsWhirlpool(MB_WHIRLPOOL));
    EXPECT(!MetatileBehavior_IsWhirlpool(MB_WATERFALL));
    EXPECT(!MetatileBehavior_IsWhirlpool(MB_DEEP_WATER));
    EXPECT(MetatileBehavior_IsSurfableWaterOrUnderwater(MB_WHIRLPOOL));
    // A whirlpool must not be treated as a waterfall, which is north-only.
    EXPECT(!MetatileBehavior_IsWaterfall(MB_WHIRLPOOL));
}

// Every move that was a TM or HM in a Gen 1-5 mainline game and is not one of our
// 111 machines is now teachable by tutor, assigned to the region of its
// introducing generation. This is the data layer only: extraTutors makes a move
// teachable and puts it in gTutorMoves[], but where a tutor stands and what it
// charges is world design that has not happened yet.
TEST("Apocrypha restores the historical TM moves as tutor moves")
{
    // Roar was a TM in nine of the eleven games, including vanilla Emerald, and
    // had no delivery route at all before this.
    EXPECT(CanLearnTeachableMove(SPECIES_ARCANINE, MOVE_ROAR));
    EXPECT(CanLearnTeachableMove(SPECIES_GYARADOS, MOVE_ROAR));
    // Widest reach on the restored list.
    EXPECT(CanLearnTeachableMove(SPECIES_WEAVILE, MOVE_FLING));
    // Water was the thinnest attacking type among the TMs; Brine backs it up.
    EXPECT(CanLearnTeachableMove(SPECIES_LAPRAS, MOVE_BRINE));
    // Gen 3 and Gen 4 staples that were TMs in five straight games.
    EXPECT(CanLearnTeachableMove(SPECIES_ALAKAZAM, MOVE_SKILL_SWAP));
    EXPECT(CanLearnTeachableMove(SPECIES_STEELIX, MOVE_GYRO_BALL));
    // Kept on the owner's call as early-game moves, not cut.
    EXPECT(CanLearnTeachableMove(SPECIES_PIDGEOT, MOVE_DOUBLE_TEAM));
    EXPECT(CanLearnTeachableMove(SPECIES_SWAMPERT, MOVE_SECRET_POWER));
}

// Tier 2: the signature moves that were never TMs. These are the reason the tutor
// economy exists -- bought with rare goods, often from another region, and opening
// late. Every one is teachable; none is obtainable, because no tutor is placed.
TEST("Apocrypha signature moves are teachable by tutor and never by TM")
{
    static const u16 signatureMoves[] = {
        MOVE_DRACO_METEOR, MOVE_SACRED_FIRE, MOVE_OUTRAGE, MOVE_CROSS_CHOP,
        MOVE_BLAST_BURN, MOVE_HYDRO_CANNON, MOVE_FRENZY_PLANT, MOVE_METEOR_MASH,
        MOVE_CLOSE_COMBAT, MOVE_AURA_SPHERE, MOVE_LEAF_STORM, MOVE_FLARE_BLITZ,
        MOVE_SACRED_SWORD, MOVE_FOUL_PLAY, MOVE_HURRICANE, MOVE_EARTH_POWER,
    };
    for (u32 i = 0; i < ARRAY_COUNT(signatureMoves); i++)
        EXPECT_EQ(GetTMHMItemIdFromMoveId(signatureMoves[i]), ITEM_NONE);

    // Each must actually reach the species it belongs to.
    EXPECT(CanLearnTeachableMove(SPECIES_DRAGONITE, MOVE_DRACO_METEOR));
    EXPECT(CanLearnTeachableMove(SPECIES_HO_OH, MOVE_SACRED_FIRE));
    EXPECT(CanLearnTeachableMove(SPECIES_BLAZIKEN, MOVE_BLAST_BURN));
    EXPECT(CanLearnTeachableMove(SPECIES_SWAMPERT, MOVE_HYDRO_CANNON));
    EXPECT(CanLearnTeachableMove(SPECIES_SCEPTILE, MOVE_FRENZY_PLANT));
    EXPECT(CanLearnTeachableMove(SPECIES_METAGROSS, MOVE_METEOR_MASH));
    EXPECT(CanLearnTeachableMove(SPECIES_LUCARIO, MOVE_AURA_SPHERE));
}
