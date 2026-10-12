"""Install map/event metadata without renumbering the accepted town or previews."""
from compose import *
import json,shutil,re
G=Path(sys.argv[1]).resolve();OLD=OUT/'references/native-base'
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
groups=read(G/'data/maps/map_groups.json');oldgroup=read(OLD/'data/maps/map_groups.json')['gMapGroup_Cherrygrove'];added=[]
for name in oldgroup[11:]:
 if name not in groups['gMapGroup_Cherrygrove']:groups['gMapGroup_Cherrygrove'].append(name)
 added.append(name);dest=G/'data/maps'/name;dest.mkdir(exist_ok=True)
 for f in ('map.json','scripts.inc'):shutil.copyfile(OLD/'data/maps'/name/f,dest/f)
write(G/'data/maps/map_groups.json',groups)
layouts=read(G/'data/layouts/layouts.json');ols=read(OLD/'data/layouts/layouts.json')['layouts']
for name in added:
 m=read(G/'data/maps'/name/'map.json');src=next(l for l in ols if l['id']==m['layout'])
 if not any(l['id']==src['id'] for l in layouts['layouts']):layouts['layouts'].append(src)
 if name not in ('NewBarkTown','JohtoRoute31','VioletCityEntrance'):
  for key in ('blockdata_filepath','border_filepath'):
   p=G/src[key];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/src[key],p)
# Existing map and layout IDs are stable. Only route dimensions/secondaries change.
for n,w,h,ts in [('CherrygroveRoute29Approach',98,48,'Cla udeRoute29'.replace(' ','')),('CherrygroveRoute30Approach',35,86,'ClaudeRoute30')]:
 l=next(l for l in layouts['layouts'] if l['name']==n+'_Layout');l.update(width=w,height=h,secondary_tileset='gTileset_'+ts)
 m=read(OLD/'data/maps'/n/'map.json')
 if '29' in n:
  for event in m['bg_events']+m['object_events']+m['coord_events']+m['warp_events']:event['y']+=2
  # The original west sign occupied the preserved entrance woodland. Place it
  # at the first open route clearing; the Potion flag and coordinates persist.
  m['bg_events']=[e for e in m['bg_events'] if e.get('script')!='CherrygroveRoute29Approach_WestSign']
  m['connections'][0]['offset']=0;m['connections'][1]['offset']=6
 else:m['connections'][0]['offset']=-35
 write(G/'data/maps'/n/'map.json',m);shutil.copyfile(OLD/'data/maps'/n/'scripts.inc',G/'data/maps'/n/'scripts.inc')
write(G/'data/layouts/layouts.json',layouts)
# Cave sign is a freestanding field prop one tile south of its old position.
p=G/'data/maps/JohtoRoute31/map.json';m=read(p)
for event in m['bg_events']:
 if event.get('script')=='JohtoRoute31_Cave':event['x']=51;event['y']=14
write(p,m)
for name,direction,value in [('CherrygroveCity','up',35),('NewBarkTown','left',-6)]:
 p=G/'data/maps'/name/'map.json';m=read(p)
 for c in m['connections']:
  if c['direction']==direction:c['offset']=value
 write(p,m)
scripts=G/'data/event_scripts.s';s=scripts.read_text()
for n in added:
 line=f'.include "data/maps/{n}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
scripts.write_text(s)
# Register only the five new secondary tilesets; preserve town/other regions.
routes.register_tilesets(G,['claude_route29','claude_route30','new_bark','route31','violet_entrance'])
# Append missing region sections, leaving every existing numeric section stable.
p=G/'src/data/region_map/region_map_sections.json';d=read(p);oldsecs=read(OLD/'src/data/region_map/region_map_sections.json')['map_sections']
ids={'MAPSEC_JOHTO_ROUTE_29','MAPSEC_JOHTO_ROUTE_30','MAPSEC_NEW_BARK_TOWN','MAPSEC_JOHTO_ROUTE_31','MAPSEC_VIOLET_CITY','MAPSEC_DARK_CAVE'}
for sec in oldsecs:
 if sec['id'] in ids and not any(v['id']==sec['id'] for v in d['map_sections']):d['map_sections'].append(sec)
write(p,d)
p=G/'include/regions.h';s=p.read_text();anchor='    case MAPSEC_CHERRYGROVE_CITY: return REGION_JOHTO;\n'
for id_ in sorted(ids):
 if 'case '+id_+':' not in s:s=s.replace(anchor,anchor+f'    case {id_}: return REGION_JOHTO;\n')
p.write_text(s)
# Preserve the already authored encounter tables and hidden item state.
routes.write_encounters(G)
p=G/'include/constants/flags.h';s=p.read_text();line='#define FLAG_HIDDEN_ITEM_APOC_ROUTE29_POTION FLAG_UNUSED_0x264 // Existing Route 29 hidden Potion'
if line not in s:s=s.replace('#endif',line+'\n#endif')
p.write_text(s)
p=G/'src/field_control_avatar.c';s=p.read_text();anchor='static bool32 ShouldDisableRandomEncounters(void)\n{\n'
if 'Apocrypha: no wild battles' not in s:s=s.replace(anchor,anchor+'    if (CalculatePlayerPartyCount() == 0) // Apocrypha: no wild battles before the first Pokemon\n        return TRUE;\n\n')
p.write_text(s)
# MapProof follows stable actual IDs, including existing regional previews.
p=G/'src/apocrypha_map_proof.c';s=p.read_text();names=groups['gMapGroup_Cherrygrove'];ids=[read(G/'data/maps'/n/'map.json')['id'] for n in names]
s=re.sub(r'const u16 sMapProofMaps\[\] = \{[^}]*\};','const u16 sMapProofMaps[] = {'+', '.join(ids)+'};',s);p.write_text(s)
(OUT/'evidence/map-ids.json').write_text(json.dumps(dict(enumerate(names)),indent=2)+'\n')
print('Installed stable map IDs:',len(names))
