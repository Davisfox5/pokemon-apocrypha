"""Append stable route registrations and exterior review interactions; no campaign actors or rewards."""
from pathlib import Path
import os,json,subprocess
G=Path(os.environ.get('ROUTES_ENGINE','/workspace/routes3839-complete'))
assert not subprocess.check_output(['git','-C',str(G),'ls-files','data/maps/JohtoRoute38/map.json'],text=True).strip(), 'Do not replay initial map integration over committed native maps.'
p=G/'src/data/region_map/region_map_sections.json';d=json.loads(p.read_text())
for n,x,y in [(38,4,5),(39,3,6)]:
 if not any(s['id']==f'MAPSEC_JOHTO_ROUTE{n}' for s in d['map_sections']):d['map_sections'].append(dict(id=f'MAPSEC_JOHTO_ROUTE{n}',name=f'ROUTE {n}',x=x,y=y,width=1,height=1))
p.write_text(json.dumps(d,indent=2)+'\n')
p=G/'data/event_scripts.s';s=p.read_text()
for n in [38,39]:
 line=f'.include "data/maps/JohtoRoute{n}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
p.write_text(s)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();s=s.replace('MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT};','MAP_JOHTO_ECRUTEAK_TEMPLE_DISTRICT, MAP_JOHTO_ROUTE38, MAP_JOHTO_ROUTE39};');p.write_text(s)
for n in [38,39]:
 p=G/f'data/maps/JohtoRoute{n}/map.json';d=json.loads(p.read_text());d['region_map_section']=f'MAPSEC_JOHTO_ROUTE{n}';d['music']='MUS_ROUTE119';p.write_text(json.dumps(d,indent=2)+'\n')
# Farm entrances are labelled exterior inspections; interiors need a separate original reconstruction.
p=G/'data/maps/JohtoRoute39/map.json';d=json.loads(p.read_text());p2=p.parent/'scripts.inc';s=p2.read_text()
for x,label,title in [(9,'Farmhouse','MOOMOO FARM'),(4,'Stable','MOOMOO FARM STABLE')]:
 name='JohtoRoute39_'+label
 if not any(e['script']==name for e in d['bg_events']):d['bg_events'].append(dict(type='sign',x=x,y=4,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_NORTH',script=name))
 if name+'::' not in s:s+=f'\n{name}::\n    msgbox {name}_Text, MSGBOX_SIGN\n    end\n\n{name}_Text:\n    .string "{title}$"\n'
p.write_text(json.dumps(d,indent=2)+'\n');p2.write_text(s)
