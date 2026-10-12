#!/usr/bin/env python3
"""Build eight scale-comparison assets above the qualified custom-cast preview.

Native Aseprite reduction is prepared separately; this importer is lossless. A manifest fixes source identity,
frame order, a shared anchor, IDs and explicit map-event assignments.
"""
import argparse, hashlib, json, re, struct, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'gba/art/regional-scale-v1'
p=argparse.ArgumentParser();p.add_argument('game',type=Path);a=p.parse_args();game=a.game.resolve()
assert game==ROOT/'tools/vendor/gba/regional-scale-v1-game', 'Use the isolated NPC preview.'
assert subprocess.check_output(['git','-C',str(game),'rev-parse','HEAD'],text=True).strip()=='f09ec1de2e6754e9f9a8e02281d3d773efcfa65e'
spec=json.loads((ART/'import.json').read_text())
assert spec['profile']=='hgss-human-12-frame-v1'
native=ART/'native';native.mkdir(parents=True,exist_ok=True)
evidence=ART/'evidence';evidence.mkdir(exist_ok=True)
def write(path,text):
    path=game/path;path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text()!=text:path.write_text(text)
def replace(path,old,new):
    text=(game/path).read_text()
    if new in text:return
    assert text.count(old)==1,(path,old)
    write(path,text.replace(old,new))
def section(path,body):
    start='// BEGIN REGIONAL COMPARISON IMPORT';end='// END REGIONAL COMPARISON IMPORT'
    text=(game/path).read_text();block=start+'\n'+body+'\n'+end
    if start in text:text=re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _:block,text,flags=re.S)
    else:text+='\n'+block+'\n'
    write(path,text)
assets=[];gfx=[];pics=[];infos=[];constants=[];externs=[];pointers=[];pals=[]
for s in spec['assets']:
    name=s['name'];is_cast=name in ['Gold','Silver','Kestra'];symbol=('Johto' if is_cast else 'Regional')+name
    folder='johto' if is_cast else 'regional'
    source=ART/'prepared'/s['source']
    im=Image.open(source).convert('RGBA')
    assert im.size==(32,384),(source,im.size)
    assert {v[3] for v in im.getdata()}<={0,255},'Unexpected partial alpha'
    colors=sorted({v[:3] for v in im.getdata() if v[3]});assert len(colors)<=15
    assert all(((v>>3)<<3 | (v>>3)>>2)==v for rgb in colors for v in rgb), 'Source is not lossless RGB555'
    palette=[(0,0,0)]+colors+[(0,0,0)]*(15-len(colors));lookup={c:i+1 for i,c in enumerate(colors)}
    atlas=Image.new('P',im.size);atlas.putpalette([v for c in palette for v in c]+[0]*720)
    expected=Image.new('RGBA',im.size)
    bounds=[]
    for i in range(12):
        frame=im.crop((0,i*32,32,i*32+32));bounds.append(frame.getbbox())
        dx,dy=spec['translation'];assert frame.getbbox()[3]+dy<=32
        shifted=Image.new('RGBA',(32,32));shifted.paste(frame,(dx,dy))
        expected.paste(shifted,(0,i*32))
        indexed=Image.new('P',(32,32));indexed.putdata([lookup[v[:3]] if v[3] else 0 for v in shifted.getdata()]);atlas.paste(indexed,(0,i*32))
    atlas.info['transparency']=0;atlas.save(native/(name.lower()+'.png'),transparency=0)
    # Compare alpha and visible pixels, ignoring unobservable RGB under alpha zero.
    decoded=atlas.convert('RGBA')
    assert all(x[3]==y[3] and (not x[3] or x[:3]==y[:3]) for x,y in zip(decoded.getdata(),expected.getdata()))
    tiles=[list(atlas.crop((x,y,x+8,y+8)).getdata()) for y in range(0,384,8) for x in range(0,32,8)]
    packed=bytes(t[i]|t[i+1]<<4 for t in tiles for i in range(0,64,2))
    assert bytes(v for b in packed for v in (b&15,b>>4))==bytes(v for t in tiles for v in t)
    (native/(name.lower()+'.4bpp')).write_bytes(packed)
    paltext='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in palette)+'\n'
    (native/(name.lower()+'.pal')).write_text(paltext)
    (native/(name.lower()+'.gbapal')).write_bytes(struct.pack('<16H',*[sum((c[j]>>3)<<(5*j) for j in range(3)) for c in palette]))
    dest=game/'graphics/object_events/pics/people'/folder;dest.mkdir(exist_ok=True)
    atlas.save(dest/(name.lower()+'.png'),transparency=0)
    write('graphics/object_events/palettes/'+folder+'_'+name.lower()+'.pal',paltext)
    assets.append(dict(**s,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_bounds=bounds,opaque_colors=len(colors),bytes_4bpp=len(packed),exact_pixel_roundtrip=True,translation=spec['translation']))
    if is_cast: continue
    gfx += [f'const u32 gObjectEventPic_{symbol}[] = INCGFX_U32("graphics/object_events/pics/people/regional/{name.lower()}.png", ".4bpp", "-mwidth 4 -mheight 4");',f'const u16 gObjectEventPal_{symbol}[] = INCGFX_U16("graphics/object_events/palettes/regional_{name.lower()}.pal", ".gbapal");']
    pics += [f'static const struct SpriteFrameImage sPicTable_{symbol}[] = {{\n    overworld_ascending_frames(gObjectEventPic_{symbol}, 4, 4),\n}};']
    infos += [f'''const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_{symbol} = {{
    .tileTag = TAG_NONE, .paletteTag = OBJ_EVENT_PAL_TAG_REGIONAL_{name.upper()},
    .reflectionPaletteTag = OBJ_EVENT_PAL_TAG_NONE,
    .size = 512, .width = 32, .height = 32, .paletteSlot = PALSLOT_NPC_1,
    .shadowSize = SHADOW_SIZE_M, .inanimate = FALSE, .compressed = FALSE,
    .tracks = TRACKS_FOOT, .oam = &gObjectEventBaseOam_32x32,
    .subspriteTables = sOamTables_32x32, .anims = sAnimTable_JohtoCast,
    .images = sPicTable_{symbol},
}};''']
    constants += [f'#define OBJ_EVENT_GFX_REGIONAL_{name.upper()} {s["graphics_id"]}',f'#define OBJ_EVENT_PAL_TAG_REGIONAL_{name.upper()} 0x{s["palette_tag"]:04X}']
    externs += [f'extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_{symbol};']
    pointers += [f'    [OBJ_EVENT_GFX_REGIONAL_{name.upper()}] = &gObjectEventGraphicsInfo_{symbol},']
    pals += [f'    {{gObjectEventPal_{symbol}, OBJ_EVENT_PAL_TAG_REGIONAL_{name.upper()}}},']


for file,body in [('object_event_graphics.h',gfx),('object_event_pic_tables.h',pics),('object_event_graphics_info.h',infos)]:section('src/data/object_events/'+file,'\n'.join(body))
constants += ['#define OBJ_EVENT_GFX_REGIONAL_FIRST 1032','#define OBJ_EVENT_GFX_REGIONAL_END 1037',
              '_Static_assert(OBJ_EVENT_GFX_VAR_F < OBJ_EVENT_GFX_REGIONAL_FIRST, "Johto graphics overlap dynamic IDs");',
              '_Static_assert(OBJ_EVENT_GFX_REGIONAL_END < OBJ_EVENT_MON, "Johto graphics overlap follower IDs");']
# Header is included by assembler too: C assertions belong in the movement unit.
section('include/constants/event_objects.h','\n'.join(constants[:-2]))
path='src/data/object_events/object_event_graphics_info_pointers.h'
replace(path,'const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[OBJ_EVENT_GFX_CAST_END] = {',
    '\n'.join(externs)+'\nconst struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[OBJ_EVENT_GFX_REGIONAL_END] = {\n'+'\n'.join(pointers))
replace('src/event_object_movement.c','static const struct SpritePalette sObjectEventSpritePalettes[] = {',
        'static const struct SpritePalette sObjectEventSpritePalettes[] = {\n'+'\n'.join(pals))
replace('src/event_object_movement.c','    if (graphicsId >= NUM_OBJ_EVENT_GFX)',
        '    if (graphicsId >= OBJ_EVENT_GFX_REGIONAL_FIRST && graphicsId < OBJ_EVENT_GFX_REGIONAL_END)\n        return gObjectEventGraphicsInfoPointers[graphicsId];\n\n    if (graphicsId >= NUM_OBJ_EVENT_GFX)')
section('src/event_object_movement.c','\n'.join(constants[-2:]))

maps={}
for placement in spec['placements']:
    name=placement['map'];path=f'data/maps/{name}/map.json'
    if name not in maps:maps[name]=json.loads((game/path).read_text())
    m=maps[name];local=placement.get('existing_local_id',placement.get('local_id'))
    existing=[e for e in m['object_events'] if e['local_id']==local]
    if 'existing_local_id' in placement:assert len(existing)==1,local
    if existing:event=existing[0]
    else:
        label=name+'_'+local.removeprefix('LOCALID_').title().replace('_','')
        event=dict(local_id=local,elevation=3,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=label,flag='0');m['object_events'].append(event)
    if 'text' in placement:
        label=event['script']
        body=f'{label}::\n    lock\n    faceplayer\n    msgbox {label}_Text, MSGBOX_DEFAULT\n    release\n    end\n\n{label}_Text::\n    .string "{placement["text"]}$"\n'
        scripts=game/f'data/maps/{name}/scripts.inc'
        if label+'::' not in scripts.read_text():scripts.write_text(scripts.read_text()+'\n'+body)
    event['graphics_id']=('OBJ_EVENT_GFX_JOHTO_' if placement['asset'] in ['Gold','Silver','Kestra'] else 'OBJ_EVENT_GFX_REGIONAL_')+placement['asset'].upper()
    event['movement_type']='MOVEMENT_TYPE_'+placement['movement']
    event['movement_range_x'],event['movement_range_y']=placement.get('range',[0,0])
    if 'position' in placement:event['x'],event['y']=placement['position']
for m in maps.values():
    for e in m['object_events']:
        if e['local_id']=='LOCALID_JOHTO_BOY':e['x'],e['y']=43,15
        if e['local_id']=='LOCALID_JOHTO_GIRL':e['x'],e['y']=58,15
        if e['local_id']=='LOCALID_COMMUTER':e['x'],e['y']=40,12
for name,m in maps.items():write(f'data/maps/{name}/map.json',json.dumps(m,indent=2)+'\n')

report=dict(profile=spec['profile'],assets=assets,directions=spec['directions'],placements=spec['placements'],
    original_enum_and_dynamic_ids_unchanged=True,independent_east_frames=True,source_frame_size=[32,32])
(evidence/'import.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'assets':len(spec['assets']),'frames':len(spec['assets'])*12,'exact_pixels':True,'map_events':sum(len(m['object_events']) for m in maps.values())}))
