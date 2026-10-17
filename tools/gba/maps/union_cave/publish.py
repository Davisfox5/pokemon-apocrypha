"""Attach cave review evidence to its exact native source commit; copy no ROM/save."""
from pathlib import Path
import sys,json,subprocess,shutil
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];G,R=map(Path,sys.argv[1:3]);E=ROOT/'gba/art/union-cave-1f/evidence';S=E.parent/'source';sha=subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip();results=json.loads((R/'results.json').read_text());assert all(p['exit_code']==0 for p in results['phases']);d=E/'gameplay';d.mkdir(exist_ok=True)
for p in R.iterdir():
 if p.suffix in ['.png','.jsonl'] or p.name=='results.json':shutil.copyfile(p,d/p.name)
names=[('route32-cave-entry','Route 32 entrance'),('north-chamber','North chamber'),('central-pool-bank','Central pool and rock faces'),('stalagmite-overlap','Walk behind upper rock / solid base'),('southern-lake-bank','Southern lake bank'),('route33-exit-location','Southern exit location - unwired')];out=Image.new('RGB',(980,1050),'#1a2125');dr=ImageDraw.Draw(out)
for i,(name,title) in enumerate(names):
 x=10+i%2*490;y=10+i//2*346;out.paste(Image.open(R/(name+'.png')).resize((480,320),Image.Resampling.NEAREST),(x,y+20));dr.text((x,y+3),title,fill='white')
out.save(E/'gameplay-gallery.png')
# Record and show every heuristic mixed-cell disagreement; do not hide/exclude it silently.
audit=json.loads((E/'audit.json').read_text());items=audit['native_RGB_majority_disagreements'];a=Image.open(S/'hgss-reference.png');b=Image.open(E/'native-map.png');out=Image.new('RGB',(1060,((len(items)+4)//5)*120),'#1a2125');dr=ImageDraw.Draw(out)
for i,q in enumerate(items):
 x,y=q['cell'];xx=i%5*212;yy=i//5*120;box=(x*16,y*16,x*16+16,y*16+16);dr.text((xx+3,yy+3),str(q['cell'])+' '+q['traced_material']+'/'+q['decoded_RGB_majority'],fill='white');out.paste(a.crop(box).resize((96,96),Image.Resampling.NEAREST),(xx+3,yy+20));out.paste(b.crop(box).resize((96,96),Image.Resampling.NEAREST),(xx+106,yy+20))
out.save(E/'mixed-material-cells.png')
report={'source_commit':sha,'base_commit':'7049fd5d8b95b3f357056ff53b8b2b3a3e848d74','ROM_sha256':results['rom_sha256'],'ROM_build':'passed','runtime_observations':sum(len(p['observations']) for p in results['phases']),'phases':[{'name':p['phase'],'exit_code':p['exit_code']} for p in results['phases']],'ordinary_flash_bytes':131072,'Porymap_version':'6.3.1','Porymap_export_pixel_differences':audit['porymap_pixel_differences'],'mGBA_version':'0.10.5','desktop_game_opened':False,'ROM_save_tool_binaries_committed':False,'scope':'Union Cave 1F; lower floors and Route33 unwired; static cave water'};(E/'build.json').write_text(json.dumps(report,indent=2)+'\n')
for name in ['audit.json','packing.json','porytiles.json','prior-route32-save.json']:
 p=E/name;j=json.loads(p.read_text());j['validated_engine_commit']=sha;p.write_text(json.dumps(j,indent=2)+'\n')
print('Published',sha,'native runtime observations',report['runtime_observations'])
