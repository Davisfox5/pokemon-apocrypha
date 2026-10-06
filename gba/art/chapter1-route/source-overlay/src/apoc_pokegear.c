// Modern Pokégear presentation: Gen 5 polish, distinct device/app layout. Campaign services are kept behind
// explicit card/event gates; no fabricated contacts or rematches are unlocked.
#include "global.h"
#include "apoc_pokegear.h"
#include "apoc_pokegear_services.h"
#include "regions.h"
#include "pokemon.h"
#include "item.h"
#include "bg.h"
#include "main.h"
#include "gpu_regs.h"
#include "window.h"
#include "menu.h"
#include "text.h"
#include "palette.h"
#include "sprite.h"
#include "task.h"
#include "overworld.h"
#include "event_data.h"
#include "rtc.h"
#include "string_util.h"
#include "region_map.h"
#include "sound.h"
#include "trig.h"
#include "constants/vars.h"
#include "constants/flags.h"
#include "constants/songs.h"
#include "constants/rgb.h"
enum
{
    GEAR_CLOCK, GEAR_RADIO, GEAR_MAP, GEAR_PHONE, GEAR_SETTINGS, GEAR_COUNT
};
static const u8 sShell[] = INCBIN_U8("graphics/apoc_pokegear/shell.bin");
static const u8 sRadio[] = INCBIN_U8("graphics/apoc_pokegear/radio.bin");
static const u16 sPalette[] = INCGFX_U16("graphics/apoc_pokegear/shell.pal", ".gbapal");
static const u8 sAtlas1[] = INCBIN_U8("graphics/apoc_pokegear/atlas1.bin");
static const u16 sAtlasPal1[] = INCGFX_U16("graphics/apoc_pokegear/atlas1.pal", ".gbapal");
static const u8 sAtlas2[] = INCBIN_U8("graphics/apoc_pokegear/atlas2.bin");
static const u16 sAtlasPal2[] = INCGFX_U16("graphics/apoc_pokegear/atlas2.pal", ".gbapal");
static const u8 sAtlas3[] = INCBIN_U8("graphics/apoc_pokegear/atlas3.bin");
static const u16 sAtlasPal3[] = INCGFX_U16("graphics/apoc_pokegear/atlas3.pal", ".gbapal");
static const u8 sAtlas4[] = INCBIN_U8("graphics/apoc_pokegear/atlas4.bin");
static const u16 sAtlasPal4[] = INCGFX_U16("graphics/apoc_pokegear/atlas4.pal", ".gbapal");
static const u8 sAtlas5[] = INCBIN_U8("graphics/apoc_pokegear/atlas5.bin");
static const u16 sAtlasPal5[] = INCGFX_U16("graphics/apoc_pokegear/atlas5.pal", ".gbapal");
static const u8 sWorldAtlas[] = INCBIN_U8("graphics/apoc_pokegear/world.bin");
static const u16 sWorldPal[] = INCGFX_U16("graphics/apoc_pokegear/world.pal", ".gbapal");
static const u8 *const sAtlases[] = {sAtlas1,sAtlas2,sAtlas3,sAtlas4,sAtlas5};
static const u16 *const sAtlasPals[] = {sAtlasPal1,sAtlasPal2,sAtlasPal3,sAtlasPal4,sAtlasPal5};
// Cursor origins, not player-position claims. This composite artwork does not
// provide calibrated coordinates for every field map in the five regions.
static const u8 sHomePins[][2] = {{104,64},{104,64},{104,64},{104,64},{104,64}};
static const u8 *const sRegions[] = {COMPOUND_STRING("KANTO"),COMPOUND_STRING("JOHTO"),COMPOUND_STRING("HOENN"),COMPOUND_STRING("SINNOH"),COMPOUND_STRING("UNOVA")};
static const struct BgTemplate sBg[] =
{
    {
        .bg=0,.charBaseIndex=0,.mapBaseIndex=31,.priority=0
    }
};
static const struct WindowTemplate sWindows[] =
{
    {
        .bg=0,.width=30,.height=20,.paletteNum=0,.baseBlock=1
    }
    , {.bg=0,.tilemapLeft=2,.tilemapTop=4,.width=26,.height=14,.paletteNum=1,.baseBlock=601}
    , DUMMY_WIN_TEMPLATE
};
static EWRAM_DATA u8 sApp, sTheme, sPreset, sFrequency, sCall, s24Hour;
static EWRAM_DATA u16 sFrame, sMusic;
static EWRAM_DATA u8 sMapRegion, sMapX, sMapY, sZoom, sNoteMode, sNoteFull;
static EWRAM_DATA u8 sPhoneRow, sPhoneHistory, sRadioText, sQuizChoice, sQuizResult;
static EWRAM_DATA u16 sLastRadioSong;
static EWRAM_DATA volatile u16 sPendingKeys;
static EWRAM_DATA u16 sPreviousHeldKeys;
static EWRAM_DATA u8 sTime[32];
static const u8 *const sWeekdays[] =
{
    COMPOUND_STRING("SUNDAY"),COMPOUND_STRING("MONDAY"),COMPOUND_STRING("TUESDAY"),COMPOUND_STRING("WEDNESDAY"),COMPOUND_STRING("THURSDAY"),COMPOUND_STRING("FRIDAY"),COMPOUND_STRING("SATURDAY")
};
static const u8 *const sTitles[] =
{
    COMPOUND_STRING("CLOCK"),COMPOUND_STRING("RADIO"),COMPOUND_STRING("MAP"),COMPOUND_STRING("PHONE"),COMPOUND_STRING("STYLE")
};
static const u8 *const sStyles[] =
{
    COMPOUND_STRING("CYAN"), COMPOUND_STRING("ROSE"),
    COMPOUND_STRING("RED"), COMPOUND_STRING("AMBER"),
    COMPOUND_STRING("WHITE"), COMPOUND_STRING("GREEN")
};
// Dark recessed display, restrained accent colors and crisp pale text.
static const u16 sThemeColors[][3] =
{
    {RGB(1,2,2), RGB(2,3,3), RGB(0,24,25)},
    {RGB(3,1,2), RGB(5,2,4), RGB(29,8,18)},
    {RGB(2,1,1), RGB(4,2,2), RGB(29,5,8)},
    {RGB(2,2,1), RGB(4,3,2), RGB(29,20,3)},
    {RGB(1,2,2), RGB(2,3,3), RGB(29,30,30)},
    {RGB(1,2,1), RGB(2,4,3), RGB(2,25,13)},
};
static void Render(void);
static void Rect(u8 color,u16 x,u16 y,u16 w,u16 h)
{
    FillWindowPixelRect(0,PIXEL_FILL(color),x,y,w,h);
}
static void Print(const u8 *text,u16 x,u16 y,u8 color)
{
    const u8 colors[]=
    {
        0,color,0
    };
    AddTextPrinterParameterized4(0,FONT_SMALL,x,y,0,0,colors,TEXT_SKIP_DRAW,text);
}
static void Number(unsigned n,u16 x,u16 y)
{
    u8 str[12];
    ConvertIntToDecimalStringN(str,n,STR_CONV_MODE_LEFT_ALIGN,3);
    Print(str,x,y,3);
}
static void Store(void)
{
    VarSet(VAR_APOC_GEAR_SETTINGS,sApp|(sTheme<<3)|(s24Hour<<6));
    VarSet(VAR_APOC_GEAR_TUNING,sFrequency|(sPreset<<8));
}
static u8 Preset(u8 i)
{
    u16 p=VarGet(i<2?VAR_APOC_GEAR_PRESETS_01:VAR_APOC_GEAR_PRESETS_23);
    return i&1?p>>8:p&255;
}
static void SavePreset(void)
{
    u16 v=VarGet(sPreset<2?VAR_APOC_GEAR_PRESETS_01:VAR_APOC_GEAR_PRESETS_23);
    if(sPreset&1)v=(v&255)|(sFrequency<<8);
    else v=(v&0xFF00)|sFrequency;
    VarSet(sPreset<2?VAR_APOC_GEAR_PRESETS_01:VAR_APOC_GEAR_PRESETS_23,v);
}
static s8 Station(void)
{
    switch(sFrequency)
    {
        case 16:return 0;
        case 48:return 1;
        case 80:return 2;
        case 112:return 3;
        default:return -1;
    }
}
static void Tune(void)
{
    s8 st=Station();
    RtcCalcLocalTime();
    if(st==1)
    {
        static const u16 songs[] = {MUS_RG_ROUTE1, MUS_ROUTE110, MUS_ROUTE120, MUS_ROUTE113, MUS_ROUTE104, MUS_ROUTE119, MUS_LITTLEROOT};
        u16 song = songs[GetDayOfWeek()%7];
        if (sLastRadioSong != song) PlayBGM(song);
        sLastRadioSong = song;
    }
    else { PlayBGM(sMusic); sLastRadioSong = 0; }
}
// Large HGSS digital readout; crisp native pixels, no scaled GBA font.
static void Digit(u8 n,u16 x,u16 y)
{
    static const u8 seg[]=
    {
        0x3F,6,0x5B,0x4F,0x66,0x6D,0x7D,7,0x7F,0x6F
    };
    u8 a=seg[n];
    if(a&1)Rect(3,x+3,y,15,3);
    if(a&2)Rect(3,x+18,y+3,3,15);
    if(a&4)Rect(3,x+18,y+21,3,15);
    if(a&8)Rect(3,x+3,y+36,15,3);
    if(a&16)Rect(3,x,y+21,3,15);
    if(a&32)Rect(3,x,y+3,3,15);
    if(a&64)Rect(3,x+3,y+18,15,3);
}
static void DrawClock(void)
{
    Print(COMPOUND_STRING("CLOCK"),105,33,2);
    unsigned hour=gLocalTime.hours;
    if(!s24Hour)hour=hour%12?hour%12:12;
    Digit(hour/10,47,48);
    Digit(hour%10,74,48);
    Rect(3,103,60,3,3);
    Rect(3,103,74,3,3);
    Digit(gLocalTime.minutes/10,116,48);
    Digit(gLocalTime.minutes%10,143,48);
    Print(s24Hour?COMPOUND_STRING("24h"):gLocalTime.hours>=12?COMPOUND_STRING("PM"):COMPOUND_STRING("AM"),174,73,3);
    Print(sWeekdays[GetDayOfWeek()%7],88,94,2);
    Print(COMPOUND_STRING("A: 12 / 24 hour"),72,115,2);
}
static void DrawRadio(void)
{
    s8 station=Station();
    static const u8 *const names[]=
    {
        COMPOUND_STRING("POKéMON TALK"),COMPOUND_STRING("POKéMON MUSIC"),COMPOUND_STRING("VARIETY CHANNEL"),COMPOUND_STRING("BUENA'S PASSWORD")
    };
    unsigned angle=sFrequency*2;
    int x=120+(Sin(angle,30)),y=78-(Cos(angle,30));
    Rect(2,x-2,y-2,5,5);
    Rect(4,x-1,y-1,3,3);
    for(u8 i=0;i<4;i++)
    {
        unsigned x=i&1?204:20,y=i<2?47:97;
        Number(i+1,x+7,y+4);
        if(i==sPreset)
        {
            Rect(12,x-5,y-10,26,1);
            Rect(12,x-5,y+19,26,1);
        }
    }
    Rect(4,49,28,142,12);
    Print(station<0?COMPOUND_STRING("NO SIGNAL"):names[station],53,28,2);
    Print(COMPOUND_STRING("A: tune  START: store"),53,117,2);
    if(station==1) Print(COMPOUND_STRING("DAILY MIX"),92,74,2);
    else if(station>=0) Print(COMPOUND_STRING("ON AIR"),99,74,13);
    Print(COMPOUND_STRING("SELECT: broadcast"),64,104,2);
}
static void RadioPage(void)
{
    static const u8 *const tips[][3] = {
        {COMPOUND_STRING("MOVE CLINIC"),COMPOUND_STRING("Each move has its own category:"),COMPOUND_STRING("physical, special, or status.")},
        {COMPOUND_STRING("TYPE CLINIC"),COMPOUND_STRING("Fairy is part of the type chart."),COMPOUND_STRING("Dragon moves cannot hit Fairy.")},
        {COMPOUND_STRING("TRAINER TOOLKIT"),COMPOUND_STRING("TMs are used once. Choose the"),COMPOUND_STRING("recipient before teaching a move.")},
        {COMPOUND_STRING("FIELD NOTES"),COMPOUND_STRING("Map notes can mark a place to"),COMPOUND_STRING("revisit. They stay in your save.")}
    };
    static const u8 *const passwords[] = {COMPOUND_STRING("PIKACHU"),COMPOUND_STRING("EEVEE"),COMPOUND_STRING("MARILL"),COMPOUND_STRING("TOGEPI")};
    unsigned st = Station();
    if (st == 0)
    {
        Print(COMPOUND_STRING("POKéMON TALK / LIVE REPORT"),18,37,3);
        if (gSaveBlock1Ptr->outbreakPokemonSpecies != SPECIES_NONE && gSaveBlock1Ptr->outbreakDaysLeft)
        {
            const struct MapHeader *map = Overworld_GetMapHeaderByGroupAndId(gSaveBlock1Ptr->outbreakLocationMapGroup,gSaveBlock1Ptr->outbreakLocationMapNum);
            u8 name[48];
            Print(COMPOUND_STRING("An active outbreak was reported:"),18,58,2);
            Print(GetSpeciesName(gSaveBlock1Ptr->outbreakPokemonSpecies),18,75,13);
            GetMapNameGeneric(name,map->regionMapSectionId);Print(name,18,92,2);
        }
        else
        {
            Print(COMPOUND_STRING("No active outbreak reports."),18,61,2);
            Print(COMPOUND_STRING("This feed follows local reports"),18,80,2);
            Print(COMPOUND_STRING("as they become available."),18,96,2);
        }
    }
    else if (st == 1)
    {
        Print(COMPOUND_STRING("POKéMON MUSIC / DAILY MIX"),18,37,3);
        Print(sWeekdays[GetDayOfWeek()%7],18,61,13);
        Print(COMPOUND_STRING("A different track each day."),18,81,2);
        Print(COMPOUND_STRING("Listening now. No encounter boost."),18,97,2);
    }
    else if (st == 2)
    {
        unsigned i = (gLocalTime.days + gLocalTime.hours/6)%4;
        Print(COMPOUND_STRING("VARIETY / TRAINER CHANNEL"),18,37,3);
        Print(tips[i][0],18,59,13);Print(tips[i][1],18,78,2);Print(tips[i][2],18,94,2);
    }
    else if (st == 3)
    {
        struct ApocGearState *state = &gSaveBlock3Ptr->apocGear;
        unsigned password = (gLocalTime.days + GetDayOfWeek())%4;
        Print(COMPOUND_STRING("BUENA'S PASSWORD / DAILY"),18,37,3);
        Print(COMPOUND_STRING("Today's password:"),18,54,2);
        Print(passwords[password],137,54,13);
        Print(COMPOUND_STRING("Repeat it:"),18,75,2);Print(passwords[sQuizChoice],94,75,3);
        if (state->passwordDay == gLocalTime.days && state->passwordSolved)
            Print(COMPOUND_STRING("Today's entry is complete."),18,96,13);
        else Print(sQuizResult?COMPOUND_STRING("Try again. Listen carefully!"):COMPOUND_STRING("Left/right: choose   A: answer"),18,96,2);
    }
    Print(COMPOUND_STRING("B / SELECT: tuner"),65,115,2);
}
static void MapPixel(u8 *dest,unsigned x,unsigned y,u8 color)
{
    unsigned at = (y/8*26+x/8)*32+(y%8)*4+(x%8)/2;
    if (x&1) dest[at]=(dest[at]&15)|(color<<4);
    else dest[at]=(dest[at]&240)|color;
}
static void DrawMap(void)
{
    u8 name[48];
    if (!(gSaveBlock3Ptr->apocGear.cards&1))
    {
        GetMapNameGeneric(name,gMapHeader.regionMapSectionId);Print(name,35,39,2);
        Print(COMPOUND_STRING("MAP CARD"),80,67,3);
        Print(COMPOUND_STRING("Regional atlas: not installed."),24,90,2);
        Print(COMPOUND_STRING("Your location is shown above."),24,109,2);
        return;
    }
    bool8 world = sMapRegion == 6;
    Print(world?COMPOUND_STRING("WORLD"):sRegions[sMapRegion-1],16,25,3);
    Print(world?COMPOUND_STRING("A zoom / START detail"):sNoteMode?COMPOUND_STRING("NOTE: A cycle, B done"):COMPOUND_STRING("A zoom / SELECT note"),92,25,2);
    u8 *dest=(u8 *)GetWindowAttribute(1,WINDOW_TILE_DATA);
    const u8 *atlas=world?sWorldAtlas:sAtlases[sMapRegion-1];
    int left=world&&sZoom?(int)sMapX*2-104:0;
    int top=sZoom?(world?(int)sMapY*2-56:(int)sMapY-56):0;
    if(left<0)left=0;if(left>208)left=208;
    if(top<0)top=0;if(top>(world?144:16))top=world?144:16;
    FillWindowPixelBuffer(1,PIXEL_FILL(1));
    for(unsigned y=0;y<112;y++)for(unsigned x=0;x<208;x++)
    {
        unsigned ax,ay;
        if(!sZoom){if(x<13||x>=195)continue;ax=(x-13)*(world?416:208)/182;ay=y*(world?256:128)/112;}
        else{ax=x+left;ay=y+top;}
        unsigned at=ay*(world?208:104)+ax/2;u8 color=atlas[at];
        MapPixel(dest,x,y,ax&1?color>>4:color&15);
    }
    // Markers are drawn on the atlas, never used as warps or travel gates.
    for(unsigned i=0;i<APGEAR_NOTES;i++)
    {
        const struct ApocGearNote *n=&gSaveBlock3Ptr->apocGear.notes[i];
        if(world || !n->icon || n->region!=sMapRegion)continue;
        int x=sZoom?n->x:13+n->x*182/208,y=sZoom?n->y-top:n->y*112/128;
        if(x>=2&&x<206&&y>=2&&y<110)
        {
            FillWindowPixelRect(1,PIXEL_FILL(14),x-2,y-2,5,5);
            if(n->icon==1)FillWindowPixelRect(1,PIXEL_FILL(15),x-1,y-1,3,3);
            if(n->icon==2){FillWindowPixelRect(1,PIXEL_FILL(15),x-2,y,5,1);FillWindowPixelRect(1,PIXEL_FILL(15),x,y-2,1,5);}
            if(n->icon==3){FillWindowPixelRect(1,PIXEL_FILL(15),x-2,y-2,5,1);FillWindowPixelRect(1,PIXEL_FILL(15),x-2,y+2,5,1);}
            if(n->icon==4){FillWindowPixelRect(1,PIXEL_FILL(15),x-1,y-2,3,1);FillWindowPixelRect(1,PIXEL_FILL(15),x-1,y+2,3,1);FillWindowPixelRect(1,PIXEL_FILL(15),x-2,y-1,1,3);FillWindowPixelRect(1,PIXEL_FILL(15),x+2,y-1,1,3);}
        }
    }
    int x=sZoom?(world?sMapX*2-left:sMapX):13+sMapX*182/208;
    int y=sZoom?(world?sMapY*2-top:sMapY-top):sMapY*112/128;
    if(x<3)x=3;if(x>204)x=204;
    if(y>=3&&y<109){FillWindowPixelRect(1,PIXEL_FILL(0),x-3,y-3,7,7);FillWindowPixelRect(1,PIXEL_FILL(15),x-2,y-2,5,5);FillWindowPixelRect(1,PIXEL_FILL(0),x-1,y-1,3,3);}
    LoadPalette(world?sWorldPal:sAtlasPals[sMapRegion-1],16,32);
    GetMapNameGeneric(name,gMapHeader.regionMapSectionId);
    Print(COMPOUND_STRING("HERE:"),16,147,3);
    Print(name,55,147,2);
}
static const u8 *ContactName(u8 contact)
{
    // Chapter scripts register these stable ids only after the encounter.
    if (contact == 0) return COMPOUND_STRING("MOM");
    if (contact == 1) return COMPOUND_STRING("GOLD");
    if (contact == 2) return COMPOUND_STRING("PROF. ELM");
    return COMPOUND_STRING("REGISTERED CONTACT");
}
static unsigned ContactCount(void)
{
    unsigned count=0;
    for(unsigned i=0;i<APGEAR_CONTACTS;i++)if(gSaveBlock3Ptr->apocGear.contacts[i]&APGEAR_REGISTERED)count++;
    return count;
}
static u8 SelectedContact(void)
{
    unsigned row=0;
    for(unsigned i=0;i<APGEAR_CONTACTS;i++)
    {
        u8 id=gSaveBlock3Ptr->apocGear.order[i];
        if(gSaveBlock3Ptr->apocGear.contacts[id]&APGEAR_REGISTERED)
            if(row++==sPhoneRow)return id;
    }
    return 0;
}
static void DrawPhone(void)
{
    struct ApocGearState *state=&gSaveBlock3Ptr->apocGear;
    u8 id=SelectedContact();
    if(sCall)
    {
        Rect(3,15,33,210,23);Rect(1,16,34,208,21);
        Print(ContactName(id),24,37,2);Print(COMPOUND_STRING("CONNECTED"),126,37,13);
        if(id==0)
        {
            if(GetCurrentRegion()!=REGION_JOHTO)
            {
                Print(COMPOUND_STRING("Hi, honey! You're a long way"),18,62,2);
                Print(COMPOUND_STRING("from home. Keep in touch, and"),18,78,2);
                Print(COMPOUND_STRING("take care of yourself."),18,94,2);
            }
            else
            {
                Print(COMPOUND_STRING("Hi, honey! Still surrounded"),18,62,2);
                Print(COMPOUND_STRING("by boxes here. Take your time"),18,78,2);
                Print(COMPOUND_STRING("exploring. I'll be right here."),18,94,2);
            }
        }
        else if(id==1)
        {
            if(VarGet(VAR_APOC_CHAPTER_STAGE)<5)
            {
                Print(COMPOUND_STRING("Gold: Take Route 29 to New Bark."),18,62,2);
                Print(COMPOUND_STRING("Elm will give you a Pokédex."),18,78,2);
                Print(COMPOUND_STRING("I'll be tending my garden."),18,94,2);
            }
            else
            {
                Print(COMPOUND_STRING("Gold: Nice work at Elm's."),18,62,2);
                Print(COMPOUND_STRING("Come see me before you leave"),18,78,2);
                Print(COMPOUND_STRING("Cherrygrove for Violet City."),18,94,2);
            }
        }
        else if(id==2)
        {
            Print(COMPOUND_STRING("Elm: Your Pokédex records"),18,62,2);
            Print(COMPOUND_STRING("each Pokémon you encounter."),18,78,2);
            Print(COMPOUND_STRING("I look forward to your reports!"),18,94,2);
        }
        else Print(COMPOUND_STRING("No authored call episode yet."),18,78,2);
        Print(state->callbackSteps?COMPOUND_STRING("Callback requested / B hang up"):state->gifts[id]?COMPOUND_STRING("SELECT gift / B hang up"):ApocGear_RematchReady(id)?COMPOUND_STRING("Rematch ready / B hang up"):COMPOUND_STRING("B hang up / START callback"),30,115,3);
    }
    else if(sPhoneHistory)
    {
        Print(COMPOUND_STRING("RECENT CALLS"),18,34,3);
        if(!state->historyCount)Print(COMPOUND_STRING("No calls yet."),18,64,2);
        for(unsigned i=sPhoneRow/4*4;i<state->historyCount&&i<sPhoneRow/4*4+4;i++)
        {
            unsigned y=50+(i%4)*15;
            if(i==sPhoneRow){Rect(3,16,y,208,14);Rect(1,17,y+1,206,12);}
            Print(ContactName(state->history[i].contact),20,y,2);
            Print(state->history[i].kind==2?COMPOUND_STRING("MISSED"):state->history[i].kind?COMPOUND_STRING("INCOMING"):COMPOUND_STRING("OUTGOING"),130,y,3);
        }
        Print(COMPOUND_STRING("Up/down / A redial / SELECT back"),15,115,2);
    }
    else
    {
        unsigned row=0,start=sPhoneRow/3*3;
        Print(state->queue!=255?COMPOUND_STRING("INCOMING CALL / A ANSWER"):COMPOUND_STRING("PHONE / CONTACTS"),18,33,3);
        for(unsigned i=0;i<APGEAR_CONTACTS;i++)
        {
            u8 contact=state->order[i];u8 flags=state->contacts[contact];
            if(!(flags&APGEAR_REGISTERED))continue;
            if(row>=start&&row<start+3)
            {
                unsigned y=51+(row-start)*19;
                if(row==sPhoneRow){Rect(3,16,y-1,208,18);Rect(1,17,y,206,16);}
                Print(ContactName(contact),25,y,2);
                if(flags&APGEAR_FAVORITE)Print(COMPOUND_STRING("STAR"),153,y,12);
                if(flags&APGEAR_MISSED)Print(COMPOUND_STRING("MISSED"),145,y,14);
            }
            row++;
        }
        Print(COMPOUND_STRING("A call / START star / SELECT log"),17,115,2);
    }
}
static void DrawSettings(void)
{
    Print(COMPOUND_STRING("BACKGROUND STYLE"),62,36,2);
    for(u8 i=0;i<6;i++)
    {
        unsigned x=26+(i%3)*72,y=60+(i/3)*29;
        Rect(i==sTheme?3:7,x,y,64,23);
        Rect(1,x+1,y+1,62,21);
        Print(sStyles[i],x+8,y+4,i==sTheme?3:2);
    }
    Print(COMPOUND_STRING("D-pad: choose    A: apply"),45,115,2);
}
static void Render(void)
{
    RtcCalcLocalTime();
    CopyToWindowPixelBuffer(0,sApp==GEAR_RADIO&&!sRadioText?sRadio:sShell,sizeof(sShell),0);
    LoadPalette(sPalette,0,sizeof(sPalette));
    LoadPalette(&sThemeColors[sTheme][0],5,2);
    LoadPalette(&sThemeColors[sTheme][1],1,2);
    LoadPalette(&sThemeColors[sTheme][2],3,2);
    FormatDecimalTimeWithoutSeconds(sTime,gLocalTime.hours,gLocalTime.minutes,TRUE);
    Print(sTime,24,9,13);
    Print(COMPOUND_STRING("POKéGEAR"),100,9,2);
    Print(COMPOUND_STRING("L/R"),200,9,3);
    // The map gets the whole display below the device header.
    if(sApp==GEAR_MAP)
    {
        Rect(1,0,128,240,32);
    }
    else
    {
        u8 x = 28 + 46 * sApp;
        Rect(12,x-2,131,5,2);
        Rect(3,x-14,151,28,1);
    }
    if(gSaveBlock3Ptr->apocGear.queue!=255)Rect(12,180,136,4,4);
    switch(sApp)
    {
        case GEAR_CLOCK:DrawClock();
        break;
        case GEAR_RADIO:if(sRadioText)RadioPage();else DrawRadio();
        break;
        case GEAR_MAP:DrawMap();
        break;
        case GEAR_PHONE:DrawPhone();
        break;
        case GEAR_SETTINGS:DrawSettings();
        break;
    }
    if(gSaveBlock3Ptr->apocGear.reserved[0])
    {
        Rect(1,12,33,216,94);
        Print(COMPOUND_STRING("POKéGEAR DATA RECOVERED"),18,39,14);
        Print(COMPOUND_STRING("Damaged gear data was cleared."),18,61,2);
        Print(COMPOUND_STRING("Your game progress is intact."),18,79,2);
        Print(COMPOUND_STRING("A: continue"),79,108,3);
    }
    PutWindowTilemap(0);
    CopyWindowToVram(0,COPYWIN_FULL);
    if(!gSaveBlock3Ptr->apocGear.reserved[0]&&sApp==GEAR_MAP&&(gSaveBlock3Ptr->apocGear.cards&1)){PutWindowTilemap(1);CopyWindowToVram(1,COPYWIN_FULL);}
}
static void VBlank(void)
{
    // A full text/page redraw can span VBlanks. Preserve physical press edges
    // during that work so short presses are processed once by the app.
    u16 held = (~REG_KEYINPUT) & KEYS_MASK;
    sPendingKeys |= held & ~sPreviousHeldKeys;
    sPreviousHeldKeys = held;
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}
static void Main(void)
{
    u16 ime = REG_IME;
    REG_IME = 0;
    u16 keys = sPendingKeys;
    sPendingKeys = 0;
    REG_IME = ime;
    bool8 dirty=FALSE;
    if(gSaveBlock3Ptr->apocGear.reserved[0])
    {
        if(keys&A_BUTTON){gSaveBlock3Ptr->apocGear.reserved[0]=0;ApocGear_Seal();Render();}
        return;
    }
    if(keys&B_BUTTON)
    {
        if(sRadioText){sRadioText=0;Render();return;}
        if(sNoteMode){sNoteMode=0;Render();return;}
        if(sPhoneHistory){sPhoneHistory=0;sPhoneRow=0;Render();return;}
        if(sCall)
        {
            sCall=0;
            dirty=TRUE;
            keys &= ~A_BUTTON;
        }
        else
        {
            if(sApp==GEAR_PHONE && gSaveBlock3Ptr->apocGear.queue!=255)
            {
                u8 missed=gSaveBlock3Ptr->apocGear.queue;
                gSaveBlock3Ptr->apocGear.contacts[missed]|=APGEAR_MISSED;
                ApocGear_RecordCall(missed,2);
            }
            Store();
            PlayBGM(sMusic);
            FreeAllWindowBuffers();
            SetMainCallback2(CB2_ReturnToFieldWithOpenMenu);
            return;
        }
    }
    if(!sCall&&(keys&(L_BUTTON|R_BUTTON)))
    {
        sApp=(sApp+(keys&R_BUTTON?1:GEAR_COUNT-1))%GEAR_COUNT;
        sRadioText=sPhoneHistory=sNoteMode=0;
        Store();
        if(sApp==GEAR_RADIO)Tune();else PlayBGM(sMusic);
        PlaySE(SE_SELECT);
        dirty=TRUE;
    }
    if(sApp==GEAR_CLOCK&&(keys&A_BUTTON))
    {
        s24Hour^=1;
        Store();
        dirty=TRUE;
    }
    if(sApp==GEAR_PHONE)
    {
        struct ApocGearState *state=&gSaveBlock3Ptr->apocGear;
        if(keys&SELECT_BUTTON){if(sCall){ApocGear_ClaimGift(SelectedContact());PlaySE(SE_SELECT);}else {sPhoneHistory^=1;sPhoneRow=0;}dirty=TRUE;}
        if(!sCall&&!sPhoneHistory)
        {
            unsigned count=ContactCount();
            if(count>1&&(keys&(DPAD_LEFT|DPAD_RIGHT)))
            {
                unsigned current=0,next=0,row=0,target=(sPhoneRow+(keys&DPAD_RIGHT?1:count-1))%count;
                for(unsigned i=0;i<APGEAR_CONTACTS;i++){if(state->contacts[state->order[i]]&APGEAR_REGISTERED){if(row==sPhoneRow)current=i;if(row==target)next=i;row++;}}
                u8 id=state->order[current];state->order[current]=state->order[next];state->order[next]=id;sPhoneRow=target;ApocGear_Seal();dirty=TRUE;
            }
            if(count&&(keys&DPAD_DOWN)){sPhoneRow=(sPhoneRow+1)%count;dirty=TRUE;}
            if(count&&(keys&DPAD_UP)){sPhoneRow=(sPhoneRow+count-1)%count;dirty=TRUE;}
            if(keys&START_BUTTON){state->contacts[SelectedContact()]^=APGEAR_FAVORITE;ApocGear_Seal();dirty=TRUE;}
            if(keys&A_BUTTON)
            {
                if(state->queue!=255)
                {
                    u8 incoming=state->queue;unsigned row=0;
                    for(unsigned i=0;i<APGEAR_CONTACTS;i++){u8 id=state->order[i];if(state->contacts[id]&APGEAR_REGISTERED){if(id==incoming){sPhoneRow=row;break;}row++;}}
                    ApocGear_RecordCall(incoming,1);
                }
                else ApocGear_RecordCall(SelectedContact(),0);
                sCall=1;PlaySE(SE_SELECT);dirty=TRUE;
            }
        }
        else if(sPhoneHistory)
        {
            unsigned count=state->historyCount;
            if(count&&(keys&DPAD_DOWN)){sPhoneRow=(sPhoneRow+1)%count;dirty=TRUE;}
            if(count&&(keys&DPAD_UP)){sPhoneRow=(sPhoneRow+count-1)%count;dirty=TRUE;}
            if(count&&(keys&A_BUTTON))
            {
                u8 target=state->history[sPhoneRow].contact;unsigned row=0;
                for(unsigned i=0;i<APGEAR_CONTACTS;i++){u8 id=state->order[i];if(state->contacts[id]&APGEAR_REGISTERED){if(id==target){sPhoneRow=row;break;}row++;}}
                ApocGear_RecordCall(target,0);sPhoneHistory=0;sCall=1;dirty=TRUE;
            }
        }
        else if(sCall)
        {
            if(keys&START_BUTTON){state->callbackSteps=10;ApocGear_Seal();PlaySE(SE_SELECT);dirty=TRUE;}
            if(keys&A_BUTTON){sCall=0;dirty=TRUE;}
        }
    }
    if(sApp==GEAR_MAP&&(gSaveBlock3Ptr->apocGear.cards&1))
    {
        if(keys&START_BUTTON)
        {
            sMapRegion=sMapRegion==6?1:sMapRegion+1;
            sMapX=sMapRegion==6?104:sHomePins[sMapRegion-1][0];
            sMapY=sMapRegion==6?64:sHomePins[sMapRegion-1][1];
            sZoom=sNoteMode=0;
            dirty=TRUE;
        }
        if(keys&DPAD_LEFT){sMapX=sMapX>=4?sMapX-4:0;dirty=TRUE;}
        if(keys&DPAD_RIGHT){sMapX=sMapX<=203?sMapX+4:207;dirty=TRUE;}
        if(keys&DPAD_UP){sMapY=sMapY>=4?sMapY-4:0;dirty=TRUE;}
        if(keys&DPAD_DOWN){sMapY=sMapY<=123?sMapY+4:127;dirty=TRUE;}
        if((keys&SELECT_BUTTON)&&sMapRegion!=6){sNoteMode^=1;dirty=TRUE;}
        if(keys&A_BUTTON)
        {
            if(sNoteMode&&sMapRegion!=6)sNoteFull=!ApocGear_SetNote(sMapRegion,sMapX,sMapY,(ApocGear_GetNote(sMapRegion,sMapX,sMapY)+1)%5);
            else sZoom^=1;
            dirty=TRUE;
        }
    }
    if(sApp==GEAR_SETTINGS)
    {
        if(keys&DPAD_RIGHT)
        {
            sTheme=(sTheme+1)%6;
            dirty=TRUE;
        }
        if(keys&DPAD_LEFT)
        {
            sTheme=(sTheme+5)%6;
            dirty=TRUE;
        }
        if(keys&(DPAD_UP|DPAD_DOWN))
        {
            sTheme=(sTheme+3)%6;
            dirty=TRUE;
        }
        if(dirty||(keys&A_BUTTON))Store();
    }
    if(sApp==GEAR_RADIO)
    {
        if((keys&SELECT_BUTTON)&&Station()>=0){sRadioText^=1;dirty=TRUE;}
        if(sRadioText)
        {
            if(Station()==3)
            {
                if(keys&DPAD_RIGHT){sQuizChoice=(sQuizChoice+1)%4;sQuizResult=0;dirty=TRUE;}
                if(keys&DPAD_LEFT){sQuizChoice=(sQuizChoice+3)%4;sQuizResult=0;dirty=TRUE;}
                if(keys&A_BUTTON)
                {
                    RtcCalcLocalTime();sQuizResult=1;
                    if(sQuizChoice==(gLocalTime.days+GetDayOfWeek())%4){gSaveBlock3Ptr->apocGear.passwordDay=gLocalTime.days;gSaveBlock3Ptr->apocGear.passwordSolved=1;ApocGear_Seal();sQuizResult=0;PlaySE(SE_SELECT);}
                    dirty=TRUE;
                }
            }
            keys &= ~(DPAD_LEFT|DPAD_RIGHT|DPAD_UP|DPAD_DOWN|A_BUTTON|START_BUTTON);
        }
        if(keys&DPAD_LEFT)
        {
            sFrequency=(sFrequency+127)%128;
            dirty=TRUE;
        }
        if(keys&DPAD_RIGHT)
        {
            sFrequency=(sFrequency+1)%128;
            dirty=TRUE;
        }
        if(keys&DPAD_DOWN)
        {
            sPreset=(sPreset+1)%4;
            dirty=TRUE;
        }
        if(keys&DPAD_UP)
        {
            sPreset=(sPreset+3)%4;
            dirty=TRUE;
        }
        if(keys&A_BUTTON)
        {
            sFrequency=Preset(sPreset);
            dirty=TRUE;
        }
        if(keys&START_BUTTON)
        {
            SavePreset();
            PlaySE(SE_SELECT);
            dirty=TRUE;
        }
        if(dirty)
        {
            Store();
            Tune();
        }
    }
    if(++sFrame%60==0)dirty=TRUE;
    if(dirty)Render();
    BuildOamBuffer();
    UpdatePaletteFade();
    DoScheduledBgTilemapCopiesToVram();
}
static void Init(void)
{
    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT,0);
    ResetSpriteData();
    FreeAllSpritePalettes();
    ResetTasks();
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0,sBg,1);
    InitWindows(sWindows);
    DeactivateAllTextPrinters();
    ClearScheduledBgCopiesToVram();
    SetGpuReg(REG_OFFSET_BG0HOFS,0);
    SetGpuReg(REG_OFFSET_BG0VOFS,0);
    ResetPaletteFade();
    Render();
    ShowBg(0);
    sPendingKeys = 0;
    sPreviousHeldKeys = (~REG_KEYINPUT) & KEYS_MASK;
    SetVBlankCallback(VBlank);
    SetMainCallback2(Main);
}
void ApocPokegear_Open(void)
{
    u16 settings;
    if(VarGet(VAR_APOC_GEAR_INITIALIZED)!=0x5047)
    {
        VarSet(VAR_APOC_GEAR_SETTINGS,0);
        VarSet(VAR_APOC_GEAR_TUNING,16);
        VarSet(VAR_APOC_GEAR_PRESETS_01,16|(48<<8));
        VarSet(VAR_APOC_GEAR_PRESETS_23,80|(112<<8));
        VarSet(VAR_APOC_GEAR_INITIALIZED,0x5047);
    }
    settings=VarGet(VAR_APOC_GEAR_SETTINGS);
    sApp=(settings&7)%GEAR_COUNT;
    sTheme=((settings>>3)&7)%6;
    s24Hour=(settings>>6)&1;
    sFrequency=VarGet(VAR_APOC_GEAR_TUNING)&127;
    sPreset=(VarGet(VAR_APOC_GEAR_TUNING)>>8)&3;
    ApocGear_EnsureState();
    sMapRegion=6; // The supplied world artwork is the Map Card's landing view.
    sMapX=104;sMapY=64;
    sZoom=sNoteMode=sNoteFull=sPhoneRow=sPhoneHistory=sRadioText=sQuizChoice=sQuizResult=0;
    sLastRadioSong=0;
    sCall=0;
    sFrame=0;
    sMusic=GetCurrentMapMusic();
    if(sApp==GEAR_RADIO)Tune();
    SetMainCallback2(Init);
}
