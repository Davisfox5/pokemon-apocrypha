"""Publish the counted groves and reconstructed receiving surfaces with evidence."""
from pathlib import Path
import sys,json,subprocess,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'gba/art/olivine-city'
S=BASE/'source/forest-refinement';E=BASE/'evidence/forest-refinement';G,R,P=map(Path,sys.argv[1:4])
PARENT='116ea8011c958d10bf5d61daf2d879cca9e8a184'
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
for p in E.glob('*-compiled/palettes/*.pal'):p.write_text(p.read_text())
old=np.array(Image.open(BASE/'evidence/terrain-reset/native-map.png').convert('RGB'));now=np.array(Image.open(E/'native-map.png').convert('RGB'))
allowed=np.array(Image.open(S/'scope-mask.png'))>0;changed=np.any(now!=old,2)
assert not (changed&~allowed).any(),'Visible edits outside the declared forest, local texture and receiving-surface scope.'
ref=Image.open(BASE/'source/hgss-reference.png').convert('RGB');registered=Image.new('RGB',(1152,896),'#223039');registered.paste(ref,(64,16))
before=Image.fromarray(old);after=Image.fromarray(now);uncovered=Image.open(E/'trees-hidden.png').convert('RGB');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
boxes=[('northwest-rows',(0,0,416,224)),('western-rows',(0,192,192,512)),('northern-shelves',(496,16,792,288)),('lighthouse-grove',(736,128,952,432)),('upper-coast',(864,208,1040,432)),('planted-coastal-shelf',(864,384,1008,624))]
for name,box in [('whole-map',(0,0,1152,896)),*boxes]:
 w,h=box[2]-box[0],box[3]-box[1];scale=1 if name=='whole-map' else 2
 sh=Image.new('RGB',(3*(w*scale+16)+16,h*scale+48),'#223039');d=ImageDraw.Draw(sh)
 for i,(caption,im) in enumerate([('HGSS reference',registered),('Before: 116ea801',before),('Counted groves / completed terrain',after)]):
  x=16+i*(w*scale+16);d.text((x,8),caption,font=font,fill='white');sh.paste(im.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,40))
 sh.save(E/(name+'-before-after.png'))
for name,box in boxes[2:]:
 w,h=box[2]-box[0],box[3]-box[1];sh=Image.new('RGB',(4*w+48,2*h+48),'#223039');d=ImageDraw.Draw(sh)
 for i,(caption,im) in enumerate([('Completed receiving surfaces; trees hidden',uncovered),('Actual decoded native composite',after)]):
  x=16+i*(w*2+16);d.text((x,8),caption,font=font,fill='white');sh.paste(im.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x,40))
 sh.save(E/(name+'-understory.png'))
rows=json.loads((S/'tree-rows.json').read_text());padding=sum(len(r['padding_centers_x']) for r in rows);total=sum(r['native_total'] for r in rows)
lines=['# Tree-row audit','', 'HGSS overview positions, registered at +64,+16. Counts include crowns inferred behind the lighthouse on the established row grid; this is not extracted DS object data. Map-edge completion is listed separately. Native centers are rounded to the glyph grid without rescaling crowns.','', '| Row | Reference / completed row | Padding | Total | Source apex y |','|---|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {r['name']} | {r['reference_count']} | {len(r['padding_centers_x'])} | {r['native_total']} | {r['source_apex_y']} |")
lines+=['',f'{total} complete native crowns: {total-padding} reference-aligned / inferred row positions, {padding} perimeter additions. Every row count is checked against the compiled assembly; no collision-based tree dropping.']
(E/'tree-rows.md').write_text('\n'.join(lines)+'\n')
run=json.loads((R/'results.json').read_text());rom=sha(G/'pokeemerald.gba');assert run['rom_sha256']==rom and all(p['exit_code']==0 for p in run['phases']);write(E/'runtime.json',run)
for dirname,src in [('gameplay',R),('porymap',P)]:
 (E/dirname).mkdir(exist_ok=True)
 for p in src.glob('*.png'):shutil.copyfile(p,E/dirname/p.name)
shots=['northwest-forest-rows','western-retaining-wall','northeastern-residences','stair-courtyard-grove','coastal-planted-shelf','headland-eastern-turn','east-stair-head','lighthouse-ramp-west','cold-reload']
gallery=Image.new('RGB',(1440,1056),'#223039');d=ImageDraw.Draw(gallery)
for i,n in enumerate(shots):
 x,y=i%3*480,i//3*352;d.text((x+8,y+8),n,font=font,fill='white');gallery.paste(Image.open(R/(n+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+32))
gallery.save(E/'gameplay-gallery.png')
head=git('rev-parse','HEAD');assert head!=PARENT;files=git('diff','--name-only',PARENT,head).splitlines()
assert all(any('/'+n+'/' in p for n in ['olivine_city','olivine_quay','JohtoOlivineCity','JohtoOlivineQuay']) for p in files)
manifest=[]
for p in files:
 raw=subprocess.check_output(['git','-C',str(G),'show',head+':'+p]);manifest.append(dict(path=p,git_blob=git('rev-parse',head+':'+p),sha256=hashlib.sha256(raw).hexdigest()))
oldfg=np.array(Image.open(BASE/'source/terrain-reset/foreground.png'));newfg=np.array(Image.open(S/'foreground.png'))
for x0,y0,x1,y1 in [(640,328,688,352),(688,543,752,608)]:
 a,b=oldfg[y0:y1,x0:x1],newfg[y0:y1,x0:x1]
 assert np.array_equal(a[...,3],b[...,3]) and np.array_equal(a[a[...,3]>0],b[b[...,3]>0])
review=json.loads((E/'review.json').read_text());observations=sum(len(p['observations']) for p in run['phases']);texture=json.loads((S/'texture-joins.json').read_text())
write(E/'preservation.json',dict(source_commit=head,baseline=PARENT,source_PR='https://github.com/Davisfox5/pokeemerald-expansion/pull/21',source_manifest=manifest,ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,changed_visible_pixels=int(changed.sum()),outside_declared_scope_pixel_changes=0,stair_and_ramp_foreground_pixel_changes=0,unchanged='Harbor source; other maps; map/layout/event/warp IDs and registries; shared Center/Mart/sign art; building geometry; timber stair/ramp pixels and traversal axes.',local_changes='237 broad native crowns and explicit rows; completed occluded receiving surfaces and coastal shelf; two reseated land rocks; local house palette aligned with the two residences; same-face interior texture joins.',owner_visual_acceptance='Groves and elevation direction received positive feedback; full revised terrain review remains pending.'))
write(E/'build.json',dict(exit_code=0,command='PATH=ARM_BIN:$PATH make -j5',ROM_sha256=rom,ROM_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='Arm GNU 14.2.1',compiler='Porytiles legacy, 13 exact RGB5 BG palettes',Porymap='6.3.1 actual project exports',mGBA='0.10.5 headless',runtime_observations=observations,phases=[dict(phase=p['phase'],exit_code=p['exit_code']) for p in run['phases']],district_usage=review['district_usage']))
write(E/'visual-review.json',dict(owner_request='Keep the good groves and improved depth; eliminate cookie-cutter grass holes and reliance on the rejected terrain design.',reviewed_regions=[dict(name=n,native_crop=list(b)) for n,b in boxes],tree_rows=len(rows),trees=total,perimeter_trees=padding,method='Explicit HGSS row counts; unscaled broad native crown. Inspect full receiving surfaces with foliage removed. Reconstruct the eastern planted shelf from fresh reference crops, including its previously omitted outer face; complete northern courses and caps. Same-facing interior glyph selection includes neighboring joins.',texture_join_report=texture,limits=['HGSS visible geography and inferred hidden surfaces, not extracted DS elevation/collision.','Trees-hidden sheet is the complete authoring receiving plane before invisible-background packing; actual native composites separately pass Porymap parity.','Interiors, Routes39/40 and shipping remain unwired; water is static and districts use ordinary fades.','Visual acceptance belongs to the owner.']))
(E/'README.md').write_text(f'''# Olivine — counted groves and completed ground

Native source **`{head}`**, on [draft PR #21](https://github.com/Davisfox5/pokeemerald-expansion/pull/21). This supersedes the trees and affected receiving surfaces in `116ea801`; the improved hill layout was the starting constraint, not approval of its tree-shaped holes.

- [Actual native whole map](native-map.png) · [HGSS / before / after](whole-map-before-after.png)
- [Northern rows](northwest-rows-before-after.png) · [Western rows](western-rows-before-after.png) · [Lighthouse grove](lighthouse-grove-before-after.png)
- [Northern shelves](northern-shelves-before-after.png) · [Upper coast](upper-coast-before-after.png) · [Complete eastern planted shelf](planted-coastal-shelf-before-after.png)
- [Trees hidden: completed receiving surfaces](trees-hidden.png) · [Coastal shelf with/without foliage](planted-coastal-shelf-understory.png)
- [All {len(rows)} row counts](tree-rows.md) · [Reference grid](reference-grid.png) · [Native grid](native-grid.png)
- [Actual gameplay gallery](gameplay-gallery.png) · [Native audit](review.json) · [Build/runtime](build.json) · [Preservation manifest](preservation.json)

The narrow shared crowns and generic 32×32 placement have been replaced with an unscaled HGSS-derived broad crown, using eight shades from the existing Johto palette. Dense groves follow the reference's roughly 32×24 spacing. The assembly contains **{total} complete trees**, including {padding} explicit map-edge additions. Occluded lighthouse positions are completed on the established row grid.

The remaining tree-shaped grass holes were a terrain problem. The receiving surfaces were inspected without foliage, northern courses were completed with caps, and the eastern shore was reconstructed as the continuous planted shelf visible in HGSS. Its outer rock face had been omitted from the earlier trace. Sand remains in the pocket north of that shelf. Two land rocks were reseated, and the local houses now use the same roof/timber palette. Rock interior glyphs retain original texture while accounting for neighboring joins.

Both timber openings retain their exact foreground pixels and movement axes. Shared Center/Mart/sign art, building geometry, Harbor source, other maps and all IDs remain unchanged. **{observations} headless observations**, ordinary save/cold Continue, 4,032 cell checks and actual Porymap/native pixel parity pass. ROM SHA-256: `{rom}`. No ROM or player save is checked in.

The trees-hidden view shows the complete receiving plane before invisible-background tile packing; the native composite is independently decoded and checked. HGSS hidden elevations/collision remain interpretations. Interiors, Routes 39/40 and shipping are unwired; water is static and district changes fade. The owner liked the groves and improved depth; acceptance of this completed revision remains pending.
''')
(S/'README.md').write_text(f'''# Forest and receiving-surface authoring record

Immutable input: native `{PARENT}`. Result: `{head}`. Do not replay an original map generator or this guarded authoring script over later owner changes.

`refine_forest.py` narrowly updates current native planes. `tree-rows.json` records each observed/inferred row and perimeter addition. `masters/olivine-tree.png` is an unscaled explicit silhouette from the [original HGSS overview](../hgss-reference.png), not a resized shared tree; `tree-provenance.json` records its donor and native palette. The local house master uses the existing residence palette with unchanged geometry.

`forest_understory.py` reconstructs complete receiving surfaces between visible reference anchors. `understory-reconstruction.json` records every affected course, shelf and donor. `receiving-surfaces.png` retains the finished ground before invisible-pixel packing; `rock-layer.png` and `wall-mask.png` retain stone independently of trees. `forest_textures.py` reuses same-facing glyphs with a source-tone and edge-join objective; no averaging or silhouette simplification. `texture-joins.json` records the measured changes.

`compile_planes.py` stages both City/Quay banks before mutating native source. `terrain_palettes.py` performs exact bank covering. Actual decoded pixels, Porymap, cell/collision checks, row/complete-root checks, gameplay and ordinary save/Continue are in [the review](../../evidence/forest-refinement/README.md). These authoring files do not establish owner visual acceptance.
''')
print(json.dumps(dict(source_commit=head,ROM_sha256=rom,changed_visible_pixels=int(changed.sum()),outside_scope=0,trees=total,rows=len(rows),runtime_observations=observations),indent=2))
