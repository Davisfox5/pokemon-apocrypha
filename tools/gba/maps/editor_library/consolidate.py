"""Assemble pinned native map sources in a NEW checkout; never edit owner checkout.
Run once on a clean 1643f58a48 checkout. Owner Route30 edits are handled separately.
"""
import argparse, json, subprocess, re, hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('repository',type=Path);p.add_argument('destination',type=Path);p.add_argument('--resume',action='store_true');a=p.parse_args();repo=a.repository;dst=a.destination
assert repo.resolve()!=dst.resolve()
def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
def read(rev,path):return git('show',rev+':'+path)
def obj(rev,path):return json.loads(read(rev,path))
def dump(path,v):(dst/path).write_text(json.dumps(v,indent=2)+'\n')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=dst,text=True).startswith('1643f58a48')
assert a.resume or not subprocess.check_output(['git','status','--porcelain'],cwd=dst).strip(),'Destination must be clean'
imports={'ca8781c07c':['CherrygroveRoute29Approach'],'4f01430776':['CherrygroveRoute30Approach'],'6a5fbb19cf':['JohtoRoute32','Route32PokemonCenter','Route32CenterUpstairs'],'eb15d89234':['JohtoRoute33','UnionCaveRoute32Entrance','UnionCaveB1F','UnionCaveB2F']}
layouts=json.loads((dst/'data/layouts/layouts.json').read_text());groups=json.loads((dst/'data/maps/map_groups.json').read_text());sections=json.loads((dst/'src/data/region_map/region_map_sections.json').read_text());manifest=[];native_files={};done=set()
def copytree(rev,prefix,newprefix=None):
 for f in git('ls-tree','-r','--name-only',rev,'--',prefix).decode().splitlines():
  to=(newprefix+f[len(prefix):]) if newprefix else f;target=dst/to;target.parent.mkdir(parents=True,exist_ok=True);data=read(rev,f);target.write_bytes(data);native_files[to]={'source':rev+':'+f,'sha256':hashlib.sha256(data).hexdigest()}
def declaration(rev,path,symbol):
 s=read(rev,path).decode();m=re.search(r'(?m)^const\s+[^;]*?\b'+re.escape(symbol)+r'\s*(?:\[.*?\])?\s*=.*?;',s,re.S)
 assert m,(path,symbol);return m[0]
def append_decl(path,text,symbol):
 f=dst/path;s=f.read_text()
 if re.search(r'\b'+re.escape(symbol)+r'\s*(?:\[.*?\])?\s*=',s):return
 f.write_text(s+'\n// Consolidated editor: pinned native declaration.\n'+text+'\n')
for rev,names in imports.items():
 source_layouts={l['id']:l for l in obj(rev,'data/layouts/layouts.json')['layouts']}
 for name in names:
  header=obj(rev,f'data/maps/{name}/map.json');l=dict(source_layouts[header['layout']]);copytree(rev,f'data/maps/{name}/');
  for path in [l['blockdata_filepath'],l['border_filepath']]:
   target=dst/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(read(rev,path));native_files[path]={'source':rev+':'+path,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
  for side in ['primary','secondary']:
   sym=l[side+'_tileset'];suffix=sym.removeprefix('gTileset_');td=declaration(rev,'src/data/tilesets/graphics.h','gTilesetTiles_'+suffix);folder=re.search(r'"(data/tilesets/[^/]+/[^/]+)/',td)[1];destfolder=folder;newsuffix=suffix
   source_files=git('ls-tree','-r','--name-only',rev,'--',folder).decode().splitlines()
   conflicts=[f for f in source_files if (dst/f).exists() and ((dst/f).read_bytes().replace(b'\r\n',b'\n') if f.endswith('.pal') else (dst/f).read_bytes())!=(read(rev,f).replace(b'\r\n',b'\n') if f.endswith('.pal') else read(rev,f))]
   # Shared primary artwork differs across review branches. Isolate the exact
   # donor primary instead of overwriting another map's graphics or IDs.
   if conflicts and side=='primary':
    assert name in ('CherrygroveRoute29Approach','CherrygroveRoute30Approach'),(name,conflicts[:3])
    tag='Route29' if '29' in name else 'Route30';newsuffix='Editor'+tag+'Primary';destfolder='data/tilesets/primary/editor_'+tag.lower();l[side+'_tileset']='gTileset_'+newsuffix
   key=(rev,folder,destfolder)
   if key not in done:
    copytree(rev,folder,destfolder);done.add(key)
    for file,prefixes in [('graphics.h',['gTilesetTiles_','gTilesetPalettes_']),('metatiles.h',['gMetatiles_','gMetatileAttributes_']),('headers.h',['gTileset_'])]:
     for prefix in prefixes:
      oldsym=prefix+suffix;newsym=prefix+newsuffix;d=declaration(rev,'src/data/tilesets/'+file,oldsym)
      if newsuffix!=suffix:
       for pre in ['gTilesetTiles_','gTilesetPalettes_','gMetatiles_','gMetatileAttributes_','gTileset_']:d=d.replace(pre+suffix,pre+newsuffix)
       d=d.replace(folder+'/',destfolder+'/')
      append_decl('src/data/tilesets/'+file,d,newsym)
  prior=next((i for i,v in enumerate(layouts['layouts']) if v['id']==l['id']),None)
  if prior is None:layouts['layouts'].append(l)
  else:layouts['layouts'][prior]=l
  # Append new maps; never shift existing map numbers in the base project.
  if not any(name in v for v in groups.values() if isinstance(v,list)):groups['gMapGroup_Cherrygrove'].append(name)
  inc=f'.include "data/maps/{name}/scripts.inc"';f=dst/'data/event_scripts.s';s=f.read_text()
  if (dst/f'data/maps/{name}/scripts.inc').exists() and inc not in s:f.write_text(s+'\n'+inc+'\n')
  secid=header['region_map_section']
  if not any(v['id']==secid for v in sections['map_sections']):sections['map_sections'].append(next(v for v in obj(rev,'src/data/region_map/region_map_sections.json')['map_sections'] if v['id']==secid))
  manifest.append({'map':name,'source':rev,'layout':l})
dump('data/layouts/layouts.json',layouts);dump('data/maps/map_groups.json',groups);dump('src/data/region_map/region_map_sections.json',sections)
f=dst/'include/regions.h';s=f.read_text()
if 'case MAPSEC_UNION_CAVE:' not in s:s=s.replace('case MAPSEC_DARK_CAVE:', 'case MAPSEC_UNION_CAVE: return REGION_JOHTO;\n    case MAPSEC_DARK_CAVE:');f.write_text(s)
f=dst/'src/field_door.c';s=f.read_text();donor=read('6a5fbb19cf','src/field_door.c').decode();entry=next(line for line in donor.splitlines() if '.tileset=&gTileset_Route32' in line)
if entry not in s:s=s.replace('static const struct DoorGraphics sDoorAnimGraphicsTable[] =','extern const struct Tileset gTileset_Route32;\nstatic const struct DoorGraphics sDoorAnimGraphicsTable[] =').replace('static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{','static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{\n'+entry);f.write_text(s)
dump('johto-editor-sources.json',{'base':'1643f58a48','imported_maps':manifest,'source_files':native_files,'owner_edits':'pending separate conflict review','status':'editor consolidation; not campaign release'})
print(json.dumps({'imported_maps':[v['map'] for v in manifest],'native_files':len(native_files)}))
