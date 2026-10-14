"""Protect owner edits; authoring scripts are source provenance, not a map editor."""
import hashlib,json
from pathlib import Path
OWNED=['data/layouts/JohtoRoute32','data/layouts/UnionCaveRoute32Entrance','data/tilesets/secondary/route32']+[f'data/maps/{n}' for n in ['JohtoRoute32','Route32PokemonCenter','Route32CenterUpstairs','UnionCaveRoute32Entrance']]
def digest(path):
 b=path.read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if path.suffix=='.pal' else b).hexdigest()
def check(game,source):
 manifest=source/'generated-files.json'
 if not (game/'data/maps/JohtoRoute32/map.json').exists():return
 if not manifest.exists():raise SystemExit('Existing Route32 has no matching source manifest; preserve owner edits.')
 changed=[p for p,h in json.loads(manifest.read_text()).items() if not(game/p).exists() or digest(game/p)!=h]
 if changed:raise SystemExit('Preserving edits since this reconstruction: '+', '.join(changed))
def record(game,source):
 files={str(p.relative_to(game)):digest(p) for d in OWNED for p in (game/d).rglob('*') if p.is_file() and p.suffix in ['.bin','.png','.pal','.json','.inc']}
 (source/'generated-files.json').write_text(json.dumps(files,indent=2)+'\n')
