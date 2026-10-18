"""Install only editor metadata after proving native asset compatibility."""
import argparse,json,hashlib,shutil,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('project',type=Path);a=p.parse_args()
m=json.loads((a.package/'manifest.json').read_text());errors=[]
for rel,expected in m['source_sha256'].items():
 f=a.project/rel
 if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=expected:errors.append(rel)
if errors:raise SystemExit('Refusing incompatible tiles/map: '+', '.join(errors[:8]))
backup=a.project/'.porymap-library-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
for name in ['prefabs.json','porymap.project.cfg']:
 f=a.project/name
 if f.exists():shutil.copy2(f,backup/name)
old=json.loads((a.project/'prefabs.json').read_text()) if (a.project/'prefabs.json').exists() else []
new=json.loads((a.package/'prefabs.json').read_text());keys={(v['name'],v['primary_tileset'],v['secondary_tileset']) for v in new}
merged=new+[v for v in old if (v['name'],v['primary_tileset'],v['secondary_tileset']) not in keys]
# Separate file avoids altering/replacing the owner's existing prefab collection.
dest=a.project/'johto-editor-prefabs.json';dest.write_text(json.dumps(merged,indent=2)+'\n')
print(json.dumps({'file':str(dest),'added':len(new),'existing_preserved':len(merged)-len(new),'backup':str(backup)},indent=2))
