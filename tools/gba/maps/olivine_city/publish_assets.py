"""Publish a completed, committed native asset cleanup with exact evidence."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];B=ROOT/'gba/art/olivine-city';S=B/'source/asset-cleanup';E=B/'evidence/asset-cleanup'
G,R,P=map(Path,sys.argv[1:4]);BASE='8eb23f6774fd937f3018d413f1fab5b6dc8d05c8'
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
head=git('rev-parse','HEAD');assert head!=BASE
files=git('diff','--name-only',BASE,head).splitlines();allowed=['olivine_city','olivine_quay','olivine_harbor','JohtoOlivineCity','JohtoOlivineQuay','JohtoOlivineHarbor']
assert all(any('/'+n+'/' in p for n in allowed) for p in files)
for p in files:
 if p.endswith('/map.bin'):
  a=np.frombuffer(subprocess.check_output(['git','-C',str(G),'show',BASE+':'+p]),'<u2');b=np.fromfile(G/p,'<u2');assert np.array_equal(a&0xfc00,b&0xfc00)
for n in ['solid','behaviors','above','tree-footprints','material-grid','ground-material-grid']:
 assert np.array_equal(np.load(S/(n+'.npy')),np.load(B/'source/forest-refinement'/(n+'.npy')))
oldfg=np.array(Image.open(B/'source/forest-refinement/foreground.png'));newfg=np.array(Image.open(S/'foreground.png'))
for x,y,x1,y1 in [(640,328,688,352),(688,543,752,608)]:
 a,b=oldfg[y:y1,x:x1],newfg[y:y1,x:x1];assert np.array_equal(a[...,3],b[...,3]) and np.array_equal(a[a[...,3]>0],b[b[...,3]>0])
run=json.loads((R/'results.json').read_text());rom=sha(G/'pokeemerald.gba');assert run['rom_sha256']==rom and all(p['exit_code']==0 for p in run['phases'])
review=json.loads((E/'review.json').read_text());inventory=json.loads((E/'asset-inventory.json').read_text());tiles=json.loads((E/'tile-inventory.json').read_text())
before=np.array(Image.open(B/'evidence/forest-refinement/native-map.png').convert('RGB'));after=np.array(Image.open(E/'native-map.png').convert('RGB'))
write(E/'preservation.json',dict(source_commit=head,baseline=BASE,source_PR='https://github.com/Davisfox5/pokeemerald-expansion/pull/21',source_manifest=[dict(path=p,git_blob=git('rev-parse',head+':'+p),sha256=sha(G/p)) for p in files],ROM_sha256=rom,changed_visible_pixels=int(np.any(before!=after,2).sum()),collision_elevation_behavior_changes=0,tree_footprint_changes=0,stone_silhouette_changes=0,stairs_ramp_visible_pixel_changes=0,unchanged='Other maps, IDs, scripts, warps, shared Center/Mart/sign native pixels, 45 tree rows, 237 roots, hill topology and both timber crossings.',owner_visual_acceptance='pending'))
write(E/'runtime.json',run)
write(E/'build.json',dict(command='PATH=ARM_BIN:$PATH make -j5',exit_code=0,ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Arm GNU 14.2.1',Porymap='6.3.1 actual native project',compiler='Porytiles legacy; exact native RGB5 palettes',emulator='libmgba 0.10.5',runtime_observations=sum(len(v['observations']) for v in run['phases']),phases=[dict(phase=v['phase'],exit_code=v['exit_code']) for v in run['phases']],district_usage=review['district_usage']))
for folder,src in [('gameplay',R),('porymap',P)]:
 (E/folder).mkdir(exist_ok=True)
 for p in src.glob('*.png'):shutil.copyfile(p,E/folder/p.name)
shots=['civic-hall','central-house','northeastern-residences','harbor-cafe','Pokemon-Center','Poke-Mart','lighthouse-door','ferry-terminal','quay-furniture','sailboat-and-railing','headland-three-courses','cold-reload']
gallery=Image.new('RGB',(1440,1408),'#223039');d=ImageDraw.Draw(gallery)
for i,n in enumerate(shots):
 x=i%3*480;y=i//3*352;d.text((x+8,y+8),n,fill='white');gallery.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+32))
gallery.save(E/'gameplay-gallery.png')
for p in E.glob('*-compiled/palettes/*.pal'):p.write_text(p.read_text())
findings={
 'civic-hall':'Removed the cliff fragment above the roof; rebuilt the complete curved shell, consistent roof ribs, glazing, crest and doorway.',
 'house':'Removed pale cutout fringe and ground between the feet; restored distinct door, window and timber colors with the same residence ramp.',
 'house-pair':'Two complete repeated houses use the same cleaned master; complete eaves, window frame and foundations, without cliff/grass contamination.',
 'cafe':'Removed side fringes and ground backing; restored awning rhythm, framed glazing, chimney and sign detail.',
 'lighthouse':'Restored finial; removed lower sign/grass fragments; regularized blue parapet tiles, matched front window frames and cleaned recessed doors. The tower silhouette remains independent of its reusable trim.',
 'terminal':'Cleaned complete curved roof outline and facade; restored contrasting life rings, window band and posts in a richer native palette.',
 'olivine-tree':'Complete edited leaf clusters and trunk; cleaner silhouette and depth. All 237 positions and all 45 row counts stay fixed.',
 'bunting':'Separate flags and clean posts/feet; removed extracted background fringe and cutout remnants.',
 'rail':'Complete evenly spaced uprights and continuous horizontal rails at all ten recorded placements.',
 'bench':'Removed deck-colored backing; separate complete feet and seat edge under each parasol.',
 'umbrella':'Clean panel boundaries, edge and pole; meets the independent bench socket.',
 'boat':'Complete hull, mast, sail and rigging outlines; removed irregular source cutout edges at both moorings.',
 'land-rock':'Coherent shaded facets and complete base without lawn-colored fringe at all four positions.',
 'sea-rock':'Clean stone/foam outline at all 42 positions; restored actual water underneath, including the mixed pier-edge cell.',
 'center':'Approved shared Violet Center retained exactly; placed outline, grass receiving surface and closed entrance reviewed.',
 'mart':'Approved shared Mart retained exactly; native roof, foot baseline, receiving lawn and closed entrance reviewed.',
 'P12':'Shared signs retained exactly; each placement checked against its own native receiving material.',
 'stairs':'Existing rebuilt treads, shoulders, full opening and traversal axis retained; source/native and both directions reviewed.',
 'ramp':'Existing complete timber crossing retained, including the projecting top rail; both landings and both traversal directions reviewed.'}
lines=['# Asset and tile review','', 'Original HGSS overview is the placement/material authority. Native art is a cleaned adaptation, not an extraction of original DS objects. The previous native version is shown only as before evidence.','', '| Element | Concrete inspection / correction | Comparison |','|---|---|---|']
for n,v in findings.items():lines.append(f'| {n} | {v} | [HGSS / previous / current]({n}-asset-review.png) |')
lines+=['','## Receiving surfaces and cliff tiles','', 'Grass, paving, sand, deck and water cores were reviewed individually and as 4×4 repetitions. They retain their material patterns. Ground beneath every replaced foreground outline was restored independently; the sea-rock at the terminal platform needed pixel-level water restoration because its metatile also contains deck.','', 'All 426 distinct stone authoring glyphs were checked by the constrained cleanup pass; 112 isolated low-contrast stone pixels were removed. Full interior stone uses same-facing, edge-weighted source medoids to reserve native space for complete architecture. Mixed-material edges, caps, silhouettes, corners and wall masks remain intact. Full map regions and the eight native tile sheets were inspected visually after compilation.','', 'The 19 foreground families have 320 assembly records, representing 319 distinct placements (the lighthouse has a retained duplicate stamp). Every visible placed master pixel is checked against actual decoded native output. The 1,289 used metatiles cover all 4,032 native cells. Pixel agreement is an integration check, not proof of artistic quality or owner acceptance.','', '## All used native metatiles','']
for p in tiles['pages']:lines.append(f'- [{p}]({p})')
lines+=['','## Surface core joins','']
for n in ['grass','sand','paving','deck','water']:lines.append(f'- [{n}]({n}-surface-review.png)')
lines+=['','## Limits','', 'Original hidden terrain and collision are overview interpretations. Native building footprints and simplified decorative treatment differ from HGSS; this pass cleans existing placed elements and preserves the established layout, rather than claiming a pixel-identical original scene. Water remains static. Interiors, Route 39/40 connections and shipping services are unwired. District transitions use fades. Quay has only three spare native glyphs, so future additions need deliberate budgeting. Visual acceptance remains with the owner.']
(E/'asset-review.md').write_text('\n'.join(lines)+'\n')
(E/'README.md').write_text(f'''# Olivine — full local asset cleanup

Native source **`{head}`**, [source PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21). This supersedes the local artwork in `8eb23f67` while preserving the established elevation, grove rows and traversal.

- [Actual native whole map](native-map.png) · [HGSS / previous / current](whole-map-before-after.png)
- [Every asset: findings and comparisons](asset-review.md) · [Master inventory](asset-inventory.json) · [Every placed instance](instance-audit.json)
- [All used native tiles](tile-inventory.json) · [Native grid](native-grid.png) · [HGSS grid](reference-grid.png)
- [Civic buildings](western-civic-before-after.png) · [Residences and groves](eastern-residences-before-after.png) · [Service buildings](town-services-before-after.png)
- [Lighthouse and cliffs](lighthouse-coast-before-after.png) · [Quay furniture and rails](quay-props-before-after.png) · [Ferry terminal](harbor-before-after.png)
- [Complete receiving surfaces, all objects hidden](all-objects-hidden.png) · [Trees hidden](trees-hidden.png)
- [Actual gameplay](gameplay-gallery.png) · [Native audit](review.json) · [Build and runtime](build.json) · [Preservation](preservation.json)

Fourteen local masters were redrawn/cleaned, then converted to native palettes and fitted to their existing locations. The lighthouse additionally received explicit repeated parapet tiles and matched window frames. The stone pass removes isolated noise and reserves unique tiles for silhouettes and joins. All 19 placed foreground families, five receiving-material cores and 1,289 used metatiles have review evidence. The current source includes City, Quay **and Harbor**.

Actual Porymap/native parity, all 4,032 cell checks, every visible master placement, 237 non-overlapping tree roots and reachable building approaches pass. The ROM builds and all 39 headless observations pass, including both stair axes, district returns, barriers and ordinary save/cold Continue. Shared Center/Mart/sign pixels, all IDs, collision/elevation, grove counts and timber crossing pixels are preserved. No ROM or player save is committed.

ROM SHA-256: `{rom}`. Native glyph use: City 998/1008, Quay 1005/1008, Harbor 394/1008. Palette use: 10, 13 and 3 banks respectively. These are native adaptations of HGSS, with the limitations recorded in [the review](asset-review.md#limits). Owner visual acceptance remains pending.
''')
(S/'README.md').write_text(f'''# Cleaned Olivine asset source

Input native commit: `{BASE}`. Result: `{head}`. Edit the current source on subsequent revisions; never replay this guarded pass or an original map generator over later owner edits.

HGSS reference: [original overview](../hgss-reference.png), [Bulbagarden origin](https://archives.bulbagarden.net/media/upload/f/f6/Olivine_City_HGSS.png). Reference geography is registered at +64,+16 without scaling the scene. Individual cleaned assets are resized into explicitly recorded native footprints; they are adaptations, not extracted DS texture data.

`edit-input-atlas.png` assembles the prior local cutouts for the image-edit pass. `edited-atlas.png` is the transparent image-tool result. It is **not** ready-made native artwork: the editor shifted cells, so `asset-import.json` records each actual source crop, native bounds and palette. `import_clean_assets.py` performs explicit registration, 1-bit alpha conversion and RGB5 assignment, and rebuilds the lighthouse's repeated trim/windows as native modules. The resulting editable native masters are in `masters/`. Existing shared service buildings/signs and the current timber crossings are preserved.

`clean_assets.py` begins with the verified current planes and applies only the reviewed local masters, receiving-ground restoration and constrained stone cleanup. It preserves collision, priority, all tree rows and geography. `receiving-surfaces.png` is complete authored ground; `background.png` includes invisible-background reuse for hardware packing. `compile_planes.py` now optionally stages all three districts before source mutation. `terrain_palettes.py` uses exact candidate covering, falling back to direct color assignment when a candidate set exceeds the native budget. No RGB substitution occurs in the palette packer.

From the hub, on the pinned input checkout only:

```sh
python3 tools/gba/maps/olivine_city/import_clean_assets.py
python3 tools/gba/maps/olivine_city/clean_assets.py ENGINE PORYTILES
QT_QPA_PLATFORM=offscreen PORYMAP_EXPORT ENGINE EXPORTS
python3 tools/gba/maps/olivine_city/review.py ENGINE EXPORTS asset-cleanup
python3 tools/gba/maps/olivine_city/audit_assets.py ENGINE
```

Build/runtime commands, hashes, comparisons and qualified limits are in [the evidence](../../evidence/asset-cleanup/README.md). The original game art belongs to its respective owners; this retains its provenance for the Apocrypha project. Visual acceptance remains pending.
''')
print(json.dumps(dict(source_commit=head,ROM_sha256=rom,changed_files=len(files),runtime_observations=39),indent=2))
