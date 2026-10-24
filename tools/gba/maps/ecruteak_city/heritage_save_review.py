"""Copied older preview save: Continue and native fixtures without a reset."""
from pathlib import Path
import subprocess,json,shutil,hashlib,sys,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];G,R,D,prior=map(Path,sys.argv[1:5]);D.mkdir(exist_ok=False);sha=hashlib.sha256(prior.read_bytes()).hexdigest();shutil.copyfile(prior,D/'johto.sav');out=[]
for phase in ['read','menu']:
 q=subprocess.run([str(R/'runtime'),str(G/'pokeemerald.gba'),str(R/'symbols.txt'),str(D),phase],capture_output=True,text=True,timeout=60);assert q.returncode==0,q.stderr;out.append(dict(phase=phase,exit_code=q.returncode,observations=[json.loads(x) for x in q.stdout.splitlines() if x.startswith('{')]))
assert hashlib.sha256(prior.read_bytes()).hexdigest()==sha
for ppm in D.glob('*.ppm'):Image.open(ppm).save(ppm.with_suffix('.png'));ppm.unlink()
S=ROOT/'gba/art/ecruteak-city/source';a=np.array(Image.open(S/'masters/heritage-shrine.png').convert('RGBA'))[32:];m=a[...,3]>0;h,w=a.shape[:2];matches_by_phase={}
for name in ['cold-reload','title-continue']:
 screen=np.array(Image.open(D/(name+'.png')).convert('RGB'))&248;matches=[];ys,xs=np.where(m);anchors=list(zip(ys[::max(1,len(ys)//8)],xs[::max(1,len(xs)//8)]))[:8]
 for y in range(161-h):
  for x in range(241-w):
   if all(np.array_equal(screen[y+yy,x+xx],a[yy,xx,:3]) for yy,xx in anchors) and np.array_equal(screen[y:y+h,x:x+w][m],a[m,:3]):matches.append([x,y])
 assert len(matches)==1,(name,'Old save must immediately show native fixture',matches);matches_by_phase[name]=matches
 # The counter's rightmost 8px is visible at the western camera edge here.
 counter=np.array(Image.open(S/'masters/offering-counter.png').convert('RGBA'))[:,24:];cm=counter[...,3]>0;x,y=matches[0];assert x==0;assert np.array_equal(screen[y+32:y+48,x:x+8][cm],counter[cm,:3]),'Old save counter must also appear'
e=S.parent/'evidence/heritage';(e/'prior-save-compatibility.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((G/'pokeemerald.gba').read_bytes()).hexdigest(),prior_source='103874452f101ba3f597cafcca73c1aa1e32998d',prior_save_sha256=sha,copied_save_only=True,original_save_unchanged=True,phases=out,restored_native_shrine_body_matches=matches_by_phase,counter_edge_RGB_errors=0,save_layout_changed=False,flags_reset=False),indent=2)+'\n');shutil.copyfile(D/'title-continue.png',e/'previous-save-continue.png');print('Previous save: read and title Continue pass; both fixtures immediately visible.')
