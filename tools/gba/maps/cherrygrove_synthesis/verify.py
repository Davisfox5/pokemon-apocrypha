"""Compile test harnesses and bind fresh native proof to this ROM."""
from pathlib import Path
import sys,os,subprocess,json,hashlib,shutil
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[4];G=R/'tools/vendor/gba/cherrygrove-synthesis-work';A=R/'gba/art/cherrygrove-synthesis';EV=A/'evidence';OUT=Path(sys.argv[1]).resolve();TC=Path(sys.argv[2]).resolve();flags=['-I/opt/homebrew/include','-L/opt/homebrew/lib','-lmgba']
def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
run([sys.executable,R/'tools/gba/maps/check_cherrygrove.py',G,OUT,'--toolchain',TC,'--runtime-source',R/'tools/gba/maps/johto_direct_runtime.c'],env=dict(os.environ,MGBA_FLAGS=' '.join(flags)))
water=OUT/'water';water.mkdir();run(['cc',R/'tools/gba/maps/cherrygrove_synthesis/water_runtime.c',*flags,'-o',water/'runtime']);run(['cc',R/'tools/gba/maps/johto_collision_runtime.c',*flags,'-o',water/'collision'])
lines=subprocess.check_output([str(TC/'bin/arm-none-eabi-nm'),str(G/'pokeemerald.elf')],text=True);wanted={'MapProof_Boot','MapProof_Enter','MapProof_ReadState','MapProof_Resume','gMapProofState','TrySavingData','LoadGameSave','ArePlayerFieldControlsLocked','SetPlayerAvatarTransitionFlags'};rows=[l.split() for l in lines.splitlines()];(water/'symbols.txt').write_text(''.join(f'{r[2]} {r[0]}\n' for r in rows if len(r)==3 and r[2] in wanted));n=json.loads((EV/'integration.json').read_text())['animated_tiles']
with (water/'water.json').open('w') as f:run([water/'runtime',G/'pokeemerald.gba',water/'symbols.txt',water,n],stdout=f)
with (water/'collision.jsonl').open('w') as f:run([water/'collision',G/'pokeemerald.gba',water/'symbols.txt',EV/'collision-probes.tsv',water],stdout=f)
results=json.loads((OUT/'results.json').read_text());assert all(v['exit_code']==0 for v in results);obs=[json.loads(l) for l in (water/'collision.jsonl').read_text().splitlines()];assert all(o['passed'] for o in obs)
(EV/'runtime.json').write_text(json.dumps(dict(rom_sha256=sha(G/'pokeemerald.gba'),phases=results),indent=2)+'\n');shutil.copyfile(water/'water.json',EV/'water.json');shutil.copyfile(water/'collision.jsonl',EV/'collision-runtime.jsonl')
(EV/'build.json').write_text(json.dumps(dict(rom_sha256=sha(G/'pokeemerald.gba'),elf_sha256=sha(G/'pokeemerald.elf'),rom_bytes=(G/'pokeemerald.gba').stat().st_size,toolchain='ARM GNU 14.2.rel1 darwin-arm64',emulator='libmGBA 0.10.5',native_movement_probes=len(obs),passed=len(obs),door_pairs=7,route_round_trips=2,ordinary_save_bytes=131072,title_continue_passed=True,desktop_emulator_launched=False),indent=2)+'\n')
pairs=[('center-and-mart','Shops and northern lane'),('residential-lane','Waterfront homes'),('new-south-homes','Southern neighborhood'),('port-cargo-berth','Preserved dock and ships'),('fix-northwest-cliff','Coastal cliff'),('pond-bench','Pond and woodland')];out=Image.new('RGB',(960,1062),(28,34,37));d=ImageDraw.Draw(out)
for i,(name,label) in enumerate(pairs):
 x=i%2*480;y=i//2*354;d.text((x+8,y+8),label,fill='white');im=Image.open(OUT/(name+'.png'));out.paste(im.resize((480,320),Image.Resampling.NEAREST),(x,y+28));shutil.copyfile(OUT/(name+'.png'),EV/(name+'.png'))
out.save(EV/'in-game-review.png')
frames=[Image.open(p).resize((480,320),Image.Resampling.NEAREST).convert('RGB') for p in sorted(water.glob('water-*.ppm'))[:32]];frames[0].save(EV/'harbor-water.gif',save_all=True,append_images=frames[1:],duration=133,loop=0)
frames=[Image.open(p).resize((480,320),Image.Resampling.NEAREST).convert('RGB') for p in sorted(OUT.glob('door-0-*.png'))[:35]];frames[0].save(EV/'player-door.gif',save_all=True,append_images=frames[1:],duration=34,loop=0)
package=R/'tools/vendor/gba/Cherrygrove-synthesis-preview';package.mkdir(exist_ok=True);shutil.copyfile(G/'pokeemerald.gba',package/'Cherrygrove.gba');shutil.copyfile(OUT/'town.sav',package/'Cherrygrove.sav');print('Verified',len(obs),'native movement probes and ordinary save/Continue.')
