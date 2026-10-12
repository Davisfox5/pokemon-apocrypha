"""Keep old cross-region preview return paths separate from the real Johto roads."""
from compose import *
import json,shutil,re
G=Path(sys.argv[1]).resolve()
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
layouts=read(G/'data/layouts/layouts.json');source_layouts=read(SOURCE/'data/layouts/layouts.json')['layouts'];groups=read(G/'data/maps/map_groups.json')
for n,region in [(29,'FloccesyTown'),(30,'SandgemTown')]:
 old=f'CherrygroveRoute{n}Approach';new=f'CherrygroveRegionalPreview{n}';id_=f'CHERRYGROVE_REGIONAL_PREVIEW_{n}'
 m=read(SOURCE/'data/maps'/old/'map.json');m.update(id='MAP_'+id_,name=new,layout='LAYOUT_'+id_)
 write(G/'data/maps'/new/'map.json',m)
 script=(SOURCE/'data/maps'/old/'scripts.inc').read_text().replace(old,new);(G/'data/maps'/new/'scripts.inc').write_text(script)
 # Replace any local script labels as well as the map header.
 m=read(G/'data/maps'/new/'map.json');m=json.loads(json.dumps(m).replace(old,new));write(G/'data/maps'/new/'map.json',m)
 l=dict(next(l for l in source_layouts if l['name']==old+'_Layout'));l.update(id='LAYOUT_'+id_,name=new+'_Layout')
 for key in ('blockdata_filepath','border_filepath'):
  before=l[key];l[key]=before.replace(old,new);p=G/l[key];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/before,p)
 if not any(v['id']==l['id'] for v in layouts['layouts']):layouts['layouts'].append(l)
 if new not in groups['gMapGroup_Cherrygrove']:groups['gMapGroup_Cherrygrove'].append(new)
 p=G/'data/maps'/region/'map.json';m=read(p)
 for w in m['warp_events']:
  if w['dest_map']==f'MAP_CHERRYGROVE_ROUTE{n}_APPROACH':w['dest_map']='MAP_'+id_
 write(p,m)
 p=G/'data/event_scripts.s';s=p.read_text();line=f'.include "data/maps/{new}/scripts.inc"'
 if line not in s:s+='\n'+line+'\n'
 p.write_text(s)
write(G/'data/layouts/layouts.json',layouts);write(G/'data/maps/map_groups.json',groups)
p=G/'src/apocrypha_map_proof.c';s=p.read_text();names=groups['gMapGroup_Cherrygrove'];ids=[read(G/'data/maps'/n/'map.json')['id'] for n in names];s=re.sub(r'const u16 sMapProofMaps\[\] = \{[^}]*\};','const u16 sMapProofMaps[] = {'+', '.join(ids)+'};',s);p.write_text(s)
(OUT/'evidence/map-ids.json').write_text(json.dumps(dict(enumerate(names)),indent=2)+'\n')
