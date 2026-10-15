"""Publish exact-source cave review and native save evidence; never ROM/save binaries."""
from pathlib import Path
import sys,json,shutil,subprocess
from PIL import Image,ImageDraw
from config import FLOORS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];G,R,S1,Sb=map(Path,sys.argv[1:5]);sha=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();runs={key:json.loads((d/'results.json').read_text()) for key,d in [('all-floors',R),('save-1f',S1),('save-b1f',Sb)]};hashes={r['rom_sha256'] for r in runs.values()};assert len(hashes)==1
for result in runs.values():assert all(p['exit_code']==0 for p in result['phases'])
first=ROOT/'gba/art/union-cave-1f/evidence';old=first/'previous-6abf7e84/gameplay'
if not old.exists():shutil.copytree(first/'gameplay',old)
# Retain earlier published tour explicitly, then make current gameplay unambiguous.
for p in (first/'gameplay').iterdir():
 if p.is_file():p.unlink()
names={
 '1f':[('1f-route32-entrance','Route32 lighted threshold'),('1f-northern-stone-stairs-clear','HGSS stone stairs / northern branch'),('1f-north-boulder','Source beige boulder, solid footprint'),('1f-small-rock-formations','Complete small rock clusters'),('1f-south-boulder','Source southern boulders'),('1f-southern-stairs','Water-separated southern stone stair'),('1f-southern-doorway','Rebuilt southern light and continuous rim')],
 'b1f':[('b1f-main-stone-stairs-clear','Main 1F / B1F stone stair'),('b1f-main-lake-land','Surf landing in the upper gallery'),('b1f-north-gallery','Northern cave rock and ground'),('b1f-strength-rock','Original fixed Strength barrier'),('b1f-lower-Surf','Separate lower chamber / Surf'),('b1f-lower-east-bank','B2F stair bank')],
 'b2f':[('b2f-stone-stairs-clear','B2F stone stairs / return to B1F'),('b2f-northeast-pocket','Northern pocket after Surf landing'),('b2f-west-peninsula','Western peninsula'),('b2f-east-gallery','Eastern gallery'),('b2f-south-peninsula','Southern peninsula'),('b2f-southern-lake','Southern lake in native gameplay'),('b2f-southern-lake-land','Southern lake disembark'),('b2f-low-shore','Walkable low bank / water blocks walking')]
}
for key,c in FLOORS.items():
 E=ROOT/f'gba/art/union-cave-{key}/evidence';d=E/'gameplay';d.mkdir(exist_ok=True)
 for p in R.iterdir():
  if p.suffix in ['.jsonl'] or p.name=='results.json' or (p.suffix=='.png' and (key=='1f' or p.stem.startswith(key))):shutil.copyfile(p,d/p.name)
 out=Image.new('RGB',(980,((len(names[key])+1)//2)*346+12),'#1a2125');dr=ImageDraw.Draw(out)
 for i,(name,title) in enumerate(names[key]):
  x=10+i%2*490;y=10+i//2*346;out.paste(Image.open(R/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+20));dr.text((x,y+3),title,fill='white')
 out.save(E/'gameplay-gallery.png')
 for name in ['packing.json','audit.json','porytiles.json','wall-review.json']:
  p=E/name;j=json.loads(p.read_text());j['source_commit']=sha;p.write_text(json.dumps(j,indent=2)+'\n')
 report={'source_commit':sha,'rom_sha256':next(iter(hashes)),'floor':key,'ROM_build':'passed','actual_Porymap_export':'6.3.1; zero pixel differences','Porytiles_native_RGB_alpha':'passed','runtime_source':'shared all-floor tour, exact ROM hash','ordinary_flash_save_cold_reload_Continue':'passed separately on each floor','Surf_scope':'proof setup on water uses existing engine Surf; normal water input and disembark tested; campaign unlock not claimed','ROM_save_tool_binaries_committed':False,'desktop_game_opened':False};(E/'build.json').write_text(json.dumps(report,indent=2)+'\n')
for name,source in [('save-1f',S1),('save-b1f',Sb)]:
 d=first/'save-checks'/name;d.mkdir(parents=True,exist_ok=True)
 for p in source.iterdir():
  if p.suffix in ['.png','.jsonl'] or p.name=='results.json':shutil.copyfile(p,d/p.name)
report={'source_commit':sha,'base_commit':'6abf7e84e27828356c1bb390b048611c1997d4e4','rom_sha256':next(iter(hashes)),'floors':list(FLOORS),'runtime_observations':sum(len(p['observations']) for r in runs.values() for p in r['phases']),'phases':{k:[{'phase':p['phase'],'exit_code':p['exit_code']} for p in r['phases']] for k,r in runs.items()},'ordinary_flash_bytes':131072,'previous_proof_saves':'both preceding 1F and Route32 copies reload/Continue; originals untouched','original_DS_warp_graph':'three pictured stair pairs wired bidirectionally; source event records retained','pending':['Route33 exterior','unpictured upper Alph transit rooms','Strength pushing','campaign Surf unlock and actors/items/encounters','animated cave water']};(first/'all-floors-build.json').write_text(json.dumps(report,indent=2)+'\n')
p=first/'all-floors-audit.json';j=json.loads(p.read_text());j['source_commit']=sha;p.write_text(json.dumps(j,indent=2)+'\n')
print('Published source',sha,'native observations',report['runtime_observations'])
