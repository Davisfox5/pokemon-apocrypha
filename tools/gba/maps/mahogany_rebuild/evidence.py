"""Assemble review sheets from immutable references and actual native/game output.

This does not author map pixels. Run after check.py, runtime.py and porymap.py.
The optional last argument is the rejected preview, used only as labelled history.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
from build import ART,SRC,EV,N,O

FONT=ImageFont.truetype('DejaVuSans.ttf',16)
SMALL=ImageFont.truetype('DejaVuSans.ttf',12)
BG=(26,31,35)

def sheet(items,path,cols=2,scale=1):
    w=max(i.width for _,i in items)*scale;h=max(i.height for _,i in items)*scale
    out=Image.new('RGB',(cols*(w+24)+24,((len(items)+cols-1)//cols)*(h+56)+24),BG);d=ImageDraw.Draw(out)
    for j,(label,im) in enumerate(items):
        x=24+j%cols*(w+24);y=24+j//cols*(h+56)
        d.text((x,y),label,font=FONT,fill='white');out.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(x,y+28))
    out.save(path)

def grid(im,box):
    x0,y0,x1,y1=box;out=im.crop(tuple(i*16 for i in box)).resize(((x1-x0)*32,(y1-y0)*32),Image.Resampling.NEAREST)
    result=Image.new('RGB',(out.width+30,out.height+24),BG);result.paste(out,(30,24));d=ImageDraw.Draw(result)
    for x in range(x0,x1):
        xx=(x-x0)*32+30;d.line((xx,24,xx,result.height),fill=(65,73,75));d.text((xx+3,4),str(x),font=SMALL,fill='white')
    for y in range(y0,y1):
        yy=(y-y0)*32+24;d.line((30,yy,result.width,yy),fill=(65,73,75));d.text((2,yy+8),str(y),font=SMALL,fill='white')
    return result

def main(game,runtime,rejected=None):
    original=Image.new('RGB',(N*16,N*16),(70,72,73));original.paste(Image.open(ART/'reference/original-hgss.png').convert('RGB'),(O*16,O*16))
    native=Image.open(EV/'native.png').convert('RGB')
    sheet([('Original HGSS reference - offset (2,2)',original),('Fresh compiled Gen 3 map',native)],EV/'original-native.png')
    sheet([('Receiving ground before structures',Image.open(SRC/'receiving-ground.png')),('Fresh compiled Gen 3 map',native)],EV/'receiving-native.png')
    sheet([('Editable RGB composition',Image.open(EV/'fresh-composition.png')),('Actual compiled tiles and palettes',native)],EV/'source-native.png')
    sheet([('Original reference - native coordinates',grid(original,(0,0,N,N))),('Compiled native - same coordinates',grid(native,(0,0,N,N)))],EV/'original-native-grid.png')
    focus=EV/'focus';focus.mkdir(exist_ok=True)
    boxes={'north-gate-forest':(10,0,29,12),'west-ledge-corners':(1,11,19,19),'houses-antenna':(16,11,35,20),'gym-join':(4,18,19,29),'center-join':(20,18,32,30),'southern-roots-rock':(0,27,36,34)}
    for name,box in boxes.items():
        sheet([(f'Original - native cells {box}',grid(original,box)),('Compiled native - same cells',grid(native,box))],focus/(name+'.png'))
    dest=EV/'runtime';dest.mkdir(exist_ok=True)
    for f in runtime.glob('*.png'):
        if f.name.startswith(('bg-','door-frame-')):continue
        shutil.copy2(f,dest/f.name)
    shutil.copy2(runtime/'results.json',dest/'results.json')
    shots=['town-square','gym-front','gate','behind-center-roof','center-interior','title-continue']
    sheet([(s,Image.open(dest/(s+'.png'))) for s in shots],EV/'gameplay.png',cols=3,scale=2)
    frames=[0,8,16,24,32,40,48,56,64]
    for n in frames:shutil.copy2(runtime/f'door-frame-{n:03}.png',dest/f'door-frame-{n:03}.png')
    sheet([(f'Door frame {n}',Image.open(runtime/f'door-frame-{n:03}.png')) for n in frames],EV/'door-animation.png',cols=3,scale=2)
    if rejected:
        im=Image.open(rejected).convert('RGB');shutil.copy2(rejected,EV/'rejected-previous.png')
        sheet([('Previous draft - rejected by owner',im),('Fresh rebuild - owner review pending',native)],EV/'rejected-current.png')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    git=lambda *a:subprocess.check_output(['git','-C',str(game),*a],text=True).strip()
    manifest=dict(engine_repository='Davisfox5/pokeemerald-expansion',engine_base=git('rev-parse','origin/apocrypha'),engine_local_commit=git('rev-parse','HEAD'),engine_tree=git('rev-parse','HEAD^{tree}'),rom_sha256=sha(game/'pokeemerald.gba'),native_sha256=sha(EV/'native.png'),tools=dict(porytiles='2.0.0 legacy CLI',porymap='6.3.1 (139eda9)',poryscript='3.6.1',mgba='0.10.5',arm_gcc='14.2.1'),assets={str(p.relative_to(ART)):sha(p) for p in (SRC/'approved-center.png',SRC/'approved-gym.png',SRC/'gym-native.png',SRC/'layers.npz',SRC/'receiving-ground.png')},approval='Proposal; owner visual acceptance pending')
    (EV/'identity.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve() if len(sys.argv)>3 else None)
