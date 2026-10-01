"""Adapt original game Town Maps into a native atlas; retain regional geography.
Source screenshots: Bulbagarden Archives, files named in manifest. Copyright
Nintendo/Creatures/Game Freak; archive contributors credited in provenance.
"""
from pathlib import Path
from PIL import Image, ImageChops
import json,hashlib
root=Path(__file__).resolve().parents[3]
art=root/'gba/art/pokegear-services';out=root/'tools/vendor/gba/opening-house-work/graphics/apoc_pokegear'
files=['Kanto_Pallet_Town_Map.png','Johto_Cherrygrove_City_Map.png','Hoenn_Littleroot_Town_Map.png','Sinnoh_Sandgem_Town_Map.png','Unova_Floccesy_Town_Map.png']
manifest=[]
for r,n in enumerate(files,1):
 p=art/'references'/n;src=Image.open(p);src.seek(0);a=src.convert('RGB');src.seek(1);b=src.convert('RGB');box=ImageChops.difference(a,b).getbbox()
 # Preserve aspect ratio and letterbox rather than stretch the map.
 w,h=a.size;scale=min(208/w,128/h);nw,nh=round(w*scale),round(h*scale);left=(208-nw)//2;top=(128-nh)//2
 bg=b.getpixel((0,h-1));im=Image.new('RGB',(208,128),bg);im.paste(b.resize((nw,nh),Image.Resampling.NEAREST),(left,top))
 im=im.quantize(colors=14,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 vals=list(im.getdata());(out/f'atlas{r}.bin').write_bytes(bytes(x|(y<<4) for x,y in zip(vals[::2],vals[1::2])))
 pal=im.getpalette()[:42]+[0,0,0,248,248,248];colors=[pal[i:i+3] for i in range(0,48,3)];(out/f'atlas{r}.pal').write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
 im.save(art/f'atlas-{r}.png')
 x=round((box[0]+box[2])/2*scale)+left;y=round((box[1]+box[3])/2*scale)+top
 m=hashlib.md5(n.encode()).hexdigest();manifest.append(dict(region=r,file=n,source=f'https://archives.bulbagarden.net/media/upload/{m[0]}/{m[:2]}/{n}',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),location=[x,y],adaptation='second animation frame, aspect preserved, 16-color native atlas'))
(art/'map-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print([(m['region'],m['location']) for m in manifest])
