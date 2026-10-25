"""Native inanimate fixtures, analogous to Emerald's truck/town-map objects.
Only the central shrine/counter use OBJ graphics; collision stays in map cells.
Two appended graphics IDs and one appended palette tag preserve all prior IDs.
"""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];G=Path(sys.argv[1]);S=ROOT/'gba/art/ecruteak-city/source';E=S.parent/'evidence';r=json.loads((E/'assembly.json').read_text());assert 'object_placements' not in r
bg=np.array(Image.open(S/'background.png'));fg=np.array(Image.open(S/'foreground.png'));oldbg=np.array(Image.open(S/'heritage/baseline/background.png'));oldfg=np.array(Image.open(S/'heritage/baseline/foreground.png'));obj=[];keep=[]
for p in r['placements']:
 if (p['name'],p['x'],p['y']) not in [('heritage-shrine',544,464),('offering-counter',520,528)]:keep.append(p);continue
 a=Image.open(S/'masters'/(p['name']+'.png'));w,h=a.size;x,y=p['x'],p['y'];bg[y:y+h,x:x+w]=oldbg[y:y+h,x:x+w];fg[y:y+h,x:x+w]=oldfg[y:y+h,x:x+w];obj.append(p)
r['placements']=keep;r['object_placements']=obj
pal=sorted(set(map(tuple,np.array(Image.open(S/'masters/house.png'))[np.array(Image.open(S/'masters/house.png'))[...,3]>0,:3])));palette=[(0,0,0)]+pal
folder=G/'graphics/object_events/pics/ecruteak';folder.mkdir(exist_ok=True);pp=G/'graphics/object_events/palettes/ecruteak_heritage.pal';pp.write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in palette)+'\n')
for name,size,pad in [('heritage-shrine',(64,64),(8,0)),('offering-counter',(32,16),(0,0))]:
 a=Image.new('RGBA',size);src=Image.open(S/'masters'/(name+'.png'));a.paste(src,pad);v=np.array(a);idx=np.zeros(v.shape[:2],np.uint8)
 for i,c in enumerate(palette[1:],1):idx[(v[...,3]>0)&np.all(v[...,:3]==c,2)]=i
 assert np.array_equal(idx>0,v[...,3]>0);im=Image.fromarray(idx,'P');im.putpalette([n for c in palette for n in c]+[0]*(768-48));im.save(folder/(name+'.png'),bits=4,transparency=0)
 for p in obj:
  if p['name']==name:p.update(graphics_path=str((folder/(name+'.png')).relative_to(G)),native_padding=list(pad),native_size=list(size))
def append(path,text):
 p=G/path;s=p.read_text();assert 'ECRUTEAK_HERITAGE' not in s and 'EcruteakHeritage' not in s; p.write_text(s+'\n'+text)
append('include/constants/event_objects.h','// ECRUTEAK_HERITAGE: static architecture, no characters.\n#define OBJ_EVENT_GFX_ECRUTEAK_SHRINE 1037\n#define OBJ_EVENT_GFX_ECRUTEAK_COUNTER 1038\n#define OBJ_EVENT_GFX_ECRUTEAK_FIRST 1037\n#define OBJ_EVENT_GFX_ECRUTEAK_END 1039\n#define OBJ_EVENT_PAL_TAG_ECRUTEAK_HERITAGE 0x118D\n')
append('src/data/object_events/object_event_graphics.h','const u32 gObjectEventPic_EcruteakHeritageShrine[] = INCGFX_U32("graphics/object_events/pics/ecruteak/heritage-shrine.png", ".4bpp");\nconst u32 gObjectEventPic_EcruteakHeritageCounter[] = INCGFX_U32("graphics/object_events/pics/ecruteak/offering-counter.png", ".4bpp");\nconst u16 gObjectEventPal_EcruteakHeritage[] = INCGFX_U16("graphics/object_events/palettes/ecruteak_heritage.pal", ".gbapal");\n')
append('src/data/object_events/object_event_pic_tables.h','static const struct SpriteFrameImage sPicTable_EcruteakHeritageShrine[] = { obj_frame_tiles(gObjectEventPic_EcruteakHeritageShrine) };\nstatic const struct SpriteFrameImage sPicTable_EcruteakHeritageCounter[] = { obj_frame_tiles(gObjectEventPic_EcruteakHeritageCounter) };\n')
append('src/data/object_events/object_event_graphics_info.h','\n'.join('const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_EcruteakHeritage'+n+' = {\n .tileTag=TAG_NONE, .paletteTag=OBJ_EVENT_PAL_TAG_ECRUTEAK_HERITAGE,\n .reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE, .size='+str(w*h//2)+', .width='+str(w)+', .height='+str(h)+',\n .paletteSlot=PALSLOT_NPC_1, .shadowSize=SHADOW_SIZE_S, .inanimate=TRUE,\n .compressed=FALSE, .tracks=TRACKS_NONE, .oam=&gObjectEventBaseOam_'+str(w)+'x'+str(h)+',\n .subspriteTables=NULL, .anims=sAnimTable_Inanimate, .images=sPicTable_EcruteakHeritage'+n+',\n .affineAnims=gDummySpriteAffineAnimTable,\n};' for n,w,h in [('Shrine',64,64),('Counter',32,16)])+'\n')
p=G/'src/data/object_events/object_event_graphics_info_pointers.h';s=p.read_text();s='extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_EcruteakHeritageShrine;\nextern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_EcruteakHeritageCounter;\n'+s;s=s.replace('gObjectEventGraphicsInfoPointers[OBJ_EVENT_GFX_REGIONAL_END] = {','gObjectEventGraphicsInfoPointers[OBJ_EVENT_GFX_ECRUTEAK_END] = {\n    [OBJ_EVENT_GFX_ECRUTEAK_SHRINE] = &gObjectEventGraphicsInfo_EcruteakHeritageShrine,\n    [OBJ_EVENT_GFX_ECRUTEAK_COUNTER] = &gObjectEventGraphicsInfo_EcruteakHeritageCounter,');p.write_text(s)
p=G/'src/event_object_movement.c';s=p.read_text();s=s.replace('static const struct SpritePalette sObjectEventSpritePalettes[] = {','static const struct SpritePalette sObjectEventSpritePalettes[] = {\n    {gObjectEventPal_EcruteakHeritage, OBJ_EVENT_PAL_TAG_ECRUTEAK_HERITAGE},');s=s.replace('    if (graphicsId >= NUM_OBJ_EVENT_GFX)','    if (graphicsId >= OBJ_EVENT_GFX_ECRUTEAK_FIRST && graphicsId < OBJ_EVENT_GFX_ECRUTEAK_END)\n        return gObjectEventGraphicsInfoPointers[graphicsId];\n\n    if (graphicsId >= NUM_OBJ_EVENT_GFX)',1);s+='\n_Static_assert(OBJ_EVENT_GFX_ECRUTEAK_FIRST == OBJ_EVENT_GFX_REGIONAL_END, "Heritage IDs must append");\n_Static_assert(OBJ_EVENT_GFX_ECRUTEAK_END < OBJ_EVENT_MON, "Heritage IDs overlap follower IDs");\n';p.write_text(s)
p=G/'data/maps/JohtoEcruteakCity/map.json';d=json.loads(p.read_text());assert d['object_events']==[]
for i,(gfx,x,y,key) in enumerate([('SHRINE',35,5,'WaysideShrine'),('COUNTER',33,6,'OfferingCounter')],1):d['object_events'].append(dict(local_id='LOCALID_ECRUTEAK_HERITAGE_'+gfx,graphics_id='OBJ_EVENT_GFX_ECRUTEAK_'+gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='JohtoEcruteakCity_Heritage_'+key,flag='0'))
for e in d['bg_events']:
 if e['script'].endswith('_WaysideShrine'):e['y']=5
p.write_text(json.dumps(d,indent=2)+'\n')
solid=np.load(S/'solid.npy');solid[32,35]=True;np.save(S/'solid.npy',solid);mat=np.load(S/'material-grid.npy');mat[32,35]='B';np.save(S/'material-grid.npy',mat)
p=S/'heritage/interactions.json';e=json.loads(p.read_text())
for i in e:
 if i['name']=='WaysideShrine':i['y']=5
for i in e:i['approach']=dict(map=i['map'],x=i['x'],y=i['y']+1,facing='UP')
p.write_text(json.dumps(e,indent=2)+'\n');(E/'assembly.json').write_text(json.dumps(r,indent=2)+'\n')
for n,a in [('background',bg),('foreground',fg)]:Image.fromarray(a).save(S/(n+'.png'))
(S/'heritage/native-objects.json').write_text(json.dumps(dict(objects=obj,graphics_IDs=[1037,1038],palette_tag='0x118D',collision='Native map bodies plus native inanimate object footing; no NPCs or persistent flags.',pixel_conversion='Exact indexed conversion of the existing RGB5 house palette; no color loss.'),indent=2)+'\n')
print('Registered two native inanimate fixtures; prior IDs preserved.')
