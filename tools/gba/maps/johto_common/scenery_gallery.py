"""Create a portable, category-filtered review of the cleaned scenery pack."""
from pathlib import Path
import json,base64,io,html
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'gba/art/johto-common/scenery'

def data(im):
    b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def main():
    records=json.loads((P/'catalog.json').read_text())['assets'];cards=[]
    for r in records:
        ims=[]
        for folder in ['inputs','source']:
            im=Image.open(P/f'{folder}/{r["id"]}.png').convert('RGBA')
            if r.get('preview_box'):im=im.crop(tuple(r['preview_box']))
            scale=max(1,min(5,240//im.width,200//im.height))
            ims.append(f'<img class="{folder}" src="{data(im)}" width="{int(im.width*scale)}" height="{int(im.height*scale)}" alt="{html.escape(r["label"])}">')
        status=f'{r["removed_background_pixels"]} terrain pixels separated' if r['removed_background_pixels'] else 'Already transparent / unchanged'
        if r.get('review_state'):status='New HGSS model conversion / transparent'
        cards.append(f'<article data-cat="{r["category"]}"><h2>{r["id"]} · {html.escape(r["label"])}</h2><div class="swatch">'+''.join(ims)+f'</div><p>{status}</p></article>')
    grass=data(Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct/grass-source.png'))
    dirt=data(Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct/path-source.png'))
    water=data(Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/B/sea-frame-0.png').crop((0,0,32,32)))
    content='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Johto scenery review</title><style>
*{box-sizing:border-box}body{margin:0;background:#17212b;color:#ecf0ef;font:16px system-ui,sans-serif}header{padding:24px 32px;background:#202e3b;position:sticky;top:0;z-index:2;border-bottom:1px solid #465463}h1{font-size:26px;margin:0 0 8px}header p{margin:6px 0;color:#c7d2da;max-width:920px}nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}button,select{padding:8px 12px;border:1px solid #617382;border-radius:6px;background:#2a3c4a;color:white;font:inherit;cursor:pointer}button[aria-pressed=true]{background:#d4e9cc;color:#17212b;border-color:#d4e9cc}label{display:flex;align-items:center;gap:8px}main{padding:24px 32px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}article{padding:16px;background:#24323f;border-radius:8px;border:1px solid #425160}h2{font-size:15px;min-height:36px;margin:0 0 12px}article p{font-size:13px;color:#c2d0d9;margin:12px 0 0}.swatch{height:220px;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#394854 0% 25%,#273643 0% 50%) 0/24px 24px;image-rendering:pixelated}.swatch img{image-rendering:pixelated;max-width:100%;object-fit:contain}.inputs{display:none}.original .inputs{display:block}.original .source{display:none}body[data-bg=grass] .swatch{background-image:url(GRASS);background-size:128px}body[data-bg=dirt] .swatch{background-image:url(DIRT);background-size:128px}body[data-bg=water] .swatch{background-image:url(WATER);background-size:128px}footer{padding:24px 32px;color:#b8c5cf}
</style><body data-bg="clear"><header><h1>Johto scenery · background cleanup</h1><p>ASSET_COUNT scenery pieces. Choose a category and background. Native objects show the intact frame; their full animation sheets are preserved.</p><p>Artwork review only. Maps, collision, jumps and interactions have not been changed. Water effects stay in the water category.</p><nav id="cats">CATEGORIES</nav><nav><label>Background <select id="background"><option value="clear">Checkerboard</option><option value="grass">Grass</option><option value="dirt">Dirt</option><option value="water">Water</option></select></label><button id="original" aria-pressed="false">Show original</button><span id="count"></span></nav></header><main>CARDS</main><footer>Original art: Game Freak / Nintendo / Creatures. Existing project adaptations retained. No old tree designs or unused scenery alternatives added.</footer><script>
const cards=[...document.querySelectorAll('article')];document.querySelectorAll('#cats button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#cats button').forEach(x=>x.setAttribute('aria-pressed',x===b));cards.forEach(c=>c.hidden=b.dataset.cat!=='all'&&c.dataset.cat!==b.dataset.cat);document.querySelector('#count').textContent=cards.filter(c=>!c.hidden).length+' pieces';});document.querySelector('#background').onchange=e=>document.body.dataset.bg=e.target.value;document.querySelector('#original').onclick=e=>{const on=document.body.classList.toggle('original');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'Show cleaned':'Show original'};document.querySelector('#count').textContent=cards.length+' pieces';
</script></body></html>'''
    cats=[('all','All'),('ledges','Ledges'),('stairs','Stairs'),('props','Signs & props'),('plants','Flowers'),('grass','Tall grass'),('water','Water scenery'),('native','Item & rock sprites')]
    buttons=''.join(f'<button data-cat="{c}" aria-pressed="{str(c=="all").lower()}">{t}</button>' for c,t in cats)
    for key,value in [('ASSET_COUNT',str(len(records))),('GRASS',grass),('DIRT',dirt),('WATER',water),('CATEGORIES',buttons),('CARDS',''.join(cards))]:content=content.replace(key,value)
    (P/'review.html').write_text(content)
    # Joined strips and one complete grass patch expose seams, not just cutouts.
    def asset(k):return Image.open(P/f'source/{k}.png').convert('RGBA')
    def join(keys):
        ims=[asset(k) for k in keys];out=Image.new('RGBA',(sum(i.width for i in ims),max(i.height for i in ims)))
        x=0
        for im in ims:out.alpha_composite(im,(x,0));x+=im.width
        return out
    patch=Image.new('RGBA',(64,48))
    for y in range(3):
        for x in range(4):
            bits=(y>0)*8+(y<2)*4+(x>0)*2+(x<3)
            patch.alpha_composite(asset('G'+str(bits).zfill(2)),(x*16,y*16))
    demos=[('Emerald ledge: complete ends + repeated middle',join(['L01','L02','L02','L03'])),('Warm Johto ledge: complete ends + repeated middle',join(['L11','L12','L12','L13'])),('North/south stairs: complete width',join(['S01','S02','S03'])),('Tall grass: a complete 4 x 3 tile patch',patch)]
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    sheet=Image.new('RGB',(1000,860),'#202833');d=ImageDraw.Draw(sheet);d.text((20,14),'JOHTO / JOINED MODULES — source-art preview',font=font,fill='white')
    textures=[None,Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct/grass-source.png').convert('RGBA'),Image.open(ROOT/'gba/art/cherrygrove-synthesis/references/HGSS-direct/path-source.png').convert('RGBA')]
    for row,(title,im) in enumerate(demos):
        y=54+row*198;d.text((20,y),title,font=font,fill='white')
        for col,tex in enumerate(textures):
            bg=Image.new('RGBA',(96,52),(49,62,73,255));pix=bg.load()
            for yy in range(52):
                for xx in range(96):
                    if (xx//4+yy//4)%2:pix[xx,yy]=(65,78,89,255)
            if tex:
                for yy in range(0,52,tex.height):
                    for xx in range(0,96,tex.width):bg.paste(tex,(xx,yy))
            bg.alpha_composite(im,((96-im.width)//2,(52-im.height)//2));sheet.paste(bg.resize((288,156),Image.Resampling.NEAREST),(20+col*328,y+28))
    sheet.save(P/'review/joined-modules.png')
    # Focused revision sheet includes the actual 15-color mailbox export.
    sheet=Image.new('RGB',(1040,700),'#202833');d=ImageDraw.Draw(sheet)
    d.text((20,14),'JOHTO / FENCE, MAILBOX & SIGNPOST',font=font,fill='white')
    d.text((20,45),'Original source          Transparent                 On grass                    GBA palette / dirt',font=font,fill='#c2d0d9')
    for row,key in enumerate(['P08','P09','P12']):
        record=next(r for r in records if r['id']==key);y=82+row*200
        d.text((20,y),key+'  '+record['label'],font=font,fill='white')
        for col in range(4):
            filename=('inputs/'+key+'.png') if col==0 else ('source/'+key+('.idx.png' if col==3 else '.png'))
            im=Image.open(P/filename).convert('RGBA')
            if record.get('preview_box'):im=im.crop(tuple(record['preview_box']))
            bg=Image.new('RGBA',(80,48));pixels=bg.load()
            for yy in range(48):
                for xx in range(80):pixels[xx,yy]=(65,78,89,255) if (xx//4+yy//4)%2 else (49,62,73,255)
            tex=textures[1] if col==2 else textures[2] if col==3 else None
            if tex:
                for yy in range(0,48,tex.height):
                    for xx in range(0,80,tex.width):bg.paste(tex,(xx,yy))
            bg.alpha_composite(im,((80-im.width)//2,(48-im.height)//2))
            sheet.paste(bg.resize((240,144),Image.Resampling.NEAREST),(20+col*255,y+30))
    sheet.save(P/'review/fence-mailbox-signpost.png')
    sheet=Image.new('RGB',(1040,520),'#202833');d=ImageDraw.Draw(sheet)
    d.text((20,14),'JOHTO / DIAGONAL EAST–WEST STAIRS',font=font,fill='white')
    d.text((20,46),'HGSS source               Transparent                 On grass                    GBA palette / dirt',font=font,fill='#c2d0d9')
    for row,key in enumerate(['S04','S05']):
        y=82+row*210;r=next(r for r in records if r['id']==key)
        d.text((20,y),key+'  '+r['label'],font=font,fill='white')
        for col in range(4):
            file=('inputs/'+key+'.png') if col==0 else ('source/'+key+('.idx.png' if col==3 else '.png'))
            im=Image.open(P/file).convert('RGBA');bg=Image.new('RGBA',(80,56));pixels=bg.load()
            for yy in range(56):
                for xx in range(80):pixels[xx,yy]=(65,78,89,255) if (xx//4+yy//4)%2 else (49,62,73,255)
            tex=textures[1] if col==2 else textures[2] if col==3 else None
            if tex:
                for yy in range(0,56,tex.height):
                    for xx in range(0,80,tex.width):bg.paste(tex,(xx,yy))
            bg.alpha_composite(im,((80-im.width)//2,4))
            sheet.paste(bg.resize((240,168),Image.Resampling.NEAREST),(20+col*255,y+28))
    sheet.save(P/'review/diagonal-stairs.png')


if __name__=='__main__':main()
