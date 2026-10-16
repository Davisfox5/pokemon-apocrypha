"""Build a review-only rock/mountain inventory. Never writes engine/map assets."""
from pathlib import Path
import argparse,base64,hashlib,html,io,json,subprocess,sys,textwrap
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools/gba/maps'))
from johto_common.rock_native import Native
from johto_common.trees import rgba,sha
P=ROOT/'gba/art/johto-common/rocks';S=P/'source-data'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
SETS={'pokeemerald':[('MossdeepCity',(58,13,70,21)),('Route112',(13,36,25,44)),('MtChimney',(3,19,15,27)),('JaggedPass',(6,4,18,12)),('MeteorFalls_1F_1R',(6,7,18,15)),('RusturfTunnel',(10,1,22,9)),('GraniteCave_1F',(10,0,22,8)),('SootopolisCity',(17,8,29,16)),('ShoalCave_LowTideIceRoom',(4,4,16,12)),('VictoryRoad_1F',(10,10,22,18)),('NavelRock_Exterior',(4,4,16,12)),('TerraCave_Entrance',(4,3,16,11))],
'pokefirered':[('Route3',(20,0,32,8)),('MtMoon_1F',(10,8,22,16)),('RockTunnel_1F',(10,8,22,16)),('SeafoamIslands_1F',(4,5,16,13)),('VictoryRoad_1F',(2,3,14,11)),('MtEmber_Exterior',(15,21,27,29)),('CeruleanCave_1F',(5,3,17,11)),('SevenIsland_SevaultCanyon',(5,10,17,18)),('SevenIsland_TanobyRuins',(8,2,20,10))]}
CURRENT=[('J01','Cherrygrove: coastal cliff','CherrygroveCity',(4,5,16,13)),('J02','Route 29: southern cliff','CherrygroveRoute29Approach',(24,28,36,36)),('J03','Route 30: vertical rock divider','CherrygroveRoute30Approach',(10,10,22,18)),('J04','Route 31: Dark Cave mountain','JohtoRoute31',(46,7,58,15)),('J05','Route 31: divider and lower wall','JohtoRoute31',(28,22,40,30)),('J06','Route 36: warm Emerald rock','JohtoRoute36',(10,18,22,26))]
HGSS_CONTEXT=[('R01','HGSS Route 31 / Dark Cave','gba/art/hgss-connections/references/route31-hgss.png',(768,112,960,240)),('R02','HGSS Route 36 / side wall and stairs','gba/art/route36/source/hgss-reference.png',(160,288,352,416)),('R03','HGSS Cherrygrove / coastal face','gba/art/johto-v1/references/cherrygrove-hgss.png',(64,112,256,240))]
HIST=[('A01','Cherrygrove B / earlier HGSS conversion','gba/art/cherrygrove-synthesis/references/B/cliff.png'),('A02','Cherrygrove C / selected texture source','gba/art/cherrygrove-synthesis/references/C/cliff.png'),('A03','C / earlier cliff end','gba/art/cherrygrove-synthesis/references/C/cliff_end.png'),('A04','Earlier route conversion / cliff face','gba/art/johto-native-refinement/native/cliff.png'),('A05','Earlier route conversion / corner','gba/art/johto-native-refinement/native/cliff_corner.png'),('A06','Earlier Cherrygrove / custom cliff','gba/art/johto-restart/native/cliff.png'),('A07','Route 30 / current face module','gba/art/route30-hgss-blocks/source/materials/cliff-face-0.png'),('A08','Route 30 / east face module','gba/art/route30-hgss-blocks/source/materials/cliff-east-0.png'),('A09','Route 30 / mountain cap','gba/art/route30-hgss-blocks/source/materials/cliff-cap-0.png'),('A10','Route 36 / warm west face','gba/art/route36/source/materials/wall-west.png'),('A11','Route 36 / warm east face','gba/art/route36/source/materials/wall-east.png'),('A12','Route 36 / warm south face','gba/art/route36/source/materials/wall-south.png')]
FAMILIES=[('H-F01','Johto rounded exterior rock',['H001','H007','H009','H010','H011']),('H-F02','Alternate exterior rock / wallkn',['H002','H003','H004','H005']),('H-F03','Gray mountain exterior',['H012','H013','H014','H015']),('H-F04','Gray / olive cave walls',['H022','H024','H026','H028','H030','H032']),('H-F05','Purple cave walls',['H040','H043','H045','H047','H049','H051']),('H-F06','Blue ice cave walls',['H056','H059','H061','H063','H065','H072']),('H-F07','Slate cave walls',['H075','H078','H079','H081','H083']),('H-F08','Ochre cave walls',['H090','H092','H094','H096','H099']),('H-F09','Snow-capped exterior mountain',['H101','H114','H115']),('H-F10','Teal cave walls',['H103','H104','H107','H108','H110','H112']),('H-F11','Pale blue cave walls',['H116','H118','H120','H122','H124','H126']),('D-F01','Sinnoh exterior rock',['D006','D011','D016','D017','D023']),('D-F02','Sinnoh brown cave walls',['D027','D029','D034','D035','D036','D037','D038']),('D-F03','Sinnoh dark cave walls',['D042','D043','D044','D045','D046']),('D-F04','Sinnoh volcanic cave walls',['D057','D058','D060','D061','D062','D063']),('D-F05','Sinnoh layered purple walls',['D082','D084','D089','D091','D093','D095','D097']),('D-F06','Sinnoh pale wall variants',['D086','D090','D092','D094','D096','D098']),('D-F07','Sinnoh ochre / gray cave variants',['D105','D106','D107','D108','D117','D121','D122','D123','D124']),('D-F08','Sinnoh snow and ice surfaces',['D009','D010','D012','D077','D078','D079','D080','D081'])]

def make_sheet(title,entries,path,cols=3):
    rows=(len(entries)+cols-1)//cols;sheet=Image.new('RGB',(cols*420,rows*380+62),'#202d37');d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(FONT,15);d.text((16,15),title,font=ImageFont.truetype(FONT,21),fill='white')
    for i,(label,im) in enumerate(entries):
        x=i%cols*420+12;y=i//cols*380+62;d.multiline_text((x,y),'\n'.join(textwrap.wrap(label,44)),font=font,fill='white')
        im=im.convert('RGBA');z=max(1,min(4,396//im.width,312//im.height));im=im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST)
        sheet.paste(im,(x,y+48),im)
    sheet.save(path)

def data(im):
    b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def main(donors,engine):
    for f in ['contexts','pieces','review']:(P/f).mkdir(parents=True,exist_ok=True)
    records=[];images={};raw=json.loads((S/'records.json').read_text());raw_by={r['id']:r for r in raw}
    def add(key,title,group,im,source,note='',full=None):
        path=P/'pieces'/f'{key}.png';im=im.convert('RGBA');im.save(path)
        rec=dict(id=key,title=title,group=group,image=str(path.relative_to(P)),sha256=sha(path),size=list(im.size),source=source,note=note)
        if full:rec['full']=full
        records.append(rec);images[key]=im
    revisions={}
    for game,spec in SETS.items():
        root=donors/game;revisions[game]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        layouts=[l for l in json.loads((root/'data/layouts/layouts.json').read_text())['layouts'] if 'name'in l]
        for name,box in spec:
            l=next(l for l in layouts if l['name']==name+'_Layout');native=Native(root,l);im=native.map(l);full=f'contexts/{game}-{name}.png';im.save(P/full)
            key='E'+str(sum(r['group']=='Emerald' for r in records)+1).zfill(2) if game=='pokeemerald' else 'F'+str(sum(r['group']=='FireRed' for r in records)+1).zfill(2)
            crop=tuple(v*16 for v in box);add(key,name.replace('_',' / '),'Emerald' if game=='pokeemerald' else 'FireRed',im.crop(crop),dict(game=game,revision=revisions[game],layout=l['name'],tilesets=native.paths,crop_tiles=list(box),map_sha256=sha(root/l['blockdata_filepath'])), 'Original map layout and native palettes. 16x16 map cells; no recoloring.',full)
            grid=np.fromfile(root/l['blockdata_filepath'],dtype='<u2').reshape(l['height'],l['width'])&1023;x,y,x1,y1=box;mids=sorted(set(map(int,grid[y:y1,x:x1].ravel())))
            thumb=Image.new('RGB',(8*48,((len(mids)+7)//8)*48),'#202d37');draw=ImageDraw.Draw(thumb)
            for i,mid in enumerate(mids):
                tx=i%8*48;ty=i//8*48;thumb.paste(Image.fromarray(native.tile(mid)).resize((32,32),Image.Resampling.NEAREST),(tx,ty));draw.text((tx,ty+32),f'{mid:03X}',fill='white')
            thumb.save(P/'pieces'/f'{key}-metatiles.png');records[-1]['metatiles']=f'pieces/{key}-metatiles.png';records[-1]['metatile_ids']=mids
    expected='6fc9e98e42fcf6c566ced269dca6a76ddf6a7cbf';actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=engine,text=True).strip();assert actual==expected
    layouts=json.loads((engine/'data/layouts/layouts.json').read_text())['layouts'];maps={}
    for key,title,name,box in CURRENT:
        l=next(l for l in layouts if l['name']==name+'_Layout')
        if name not in maps:maps[name]=Native(engine,l).map(l);maps[name].save(P/f'contexts/current-{name}.png')
        add(key,title,'Current Johto',maps[name].crop(tuple(v*16 for v in box)),dict(engine_revision=actual,map=name,crop_tiles=list(box)), 'Current installed native art, decoded read-only.',f'contexts/current-{name}.png')
    for key,title,rel,box in HGSS_CONTEXT:
        im=Image.open(ROOT/rel);add(key,title,'HGSS map context',im.crop(box),dict(path=rel,sha256=sha(ROOT/rel),crop=list(box)), 'Original HGSS map render. Lighting/perspective differs from raw DS texture sheets.')
    for key,title,rel in HIST:
        if not (ROOT/rel).exists():continue
        add(key,title,'Existing conversions',Image.fromarray(rgba(ROOT/rel)),dict(path=rel,sha256=sha(ROOT/rel)), 'Comparison inventory only. Earlier versions are not newly approved masters.')
    for key,title,ids in FAMILIES:
        canvas=Image.new('RGBA',(240,((len(ids)+2)//3)*88));d=ImageDraw.Draw(canvas)
        for i,k in enumerate(ids):
            r=raw_by[k];im=Image.open(S/r['file']).convert('RGBA');x=i%3*80;y=i//3*88
            z=max(1,min(2,72//im.width,64//im.height));im=im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST)
            canvas.alpha_composite(im,(x,y));d.text((x,y+68),k,fill='white')
        add(key,title,'HGSS families' if key.startswith('H') else 'Sinnoh families',canvas,dict(source_piece_ids=ids),'Complete native texture samples. Open individual source pieces for dimensions and source locations. Raw DS colors are before map lighting.')
    # Full source pieces retain all texels. Local HGSS 106+ are earlier Sinnoh imports.
    for r in raw:
        imported=r['game']=='HGSS' and all(int(x['member'])>=106 for x in r['sources'])
        group='Earlier Sinnoh imports' if imported else 'HGSS source pieces' if r['game']=='HGSS' else 'Platinum source pieces'
        if r['game']=='Platinum' and r['name'] in ['wall01','wall02']:group='Related interior surfaces'
        add(r['id'],r['name']+' / '+r['palette'],group,Image.open(S/r['file']),dict(origins=r['sources'],pixel_sha256=r['pixel_sha256']), 'Raw texture; not yet a GBA metatile. Repeated identical images are collapsed; all source occurrences are recorded.')
    # Complete source-piece sheets are kept alongside the compact family overview.
    for group,filename in [('Emerald','emerald-rocks'),('FireRed','firered-rocks'),('Current Johto','current-johto'),('Existing conversions','existing-conversions'),('HGSS map context','hgss-map-context'),('HGSS families','hgss-families'),('Sinnoh families','sinnoh-families')]:
        rows=[r for r in records if r['group']==group];make_sheet(group+' / rock and mountain comparison',[(r['id']+'  '+r['title'],images[r['id']]) for r in rows],P/'review'/f'{filename}.png')
    make_sheet('START HERE / original GBA, current conversions, original HGSS',[(k+'  '+next(r['title'] for r in records if r['id']==k),images[k]) for k in ['E01','J01','R03','E02','J06','R02','E10','J04','R01']],P/'review/comparison.png')
    for donor in ['pokeheartgold','pokeplatinum']:revisions[donor]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=donors/donor,text=True).strip()
    manifest=dict(status='Read-only review inventory. No styles selected, no tiles parsed for installation, no maps/ROM modified.',credits='Game Freak / Nintendo / Creatures',engine_revision=actual,donor_revisions=revisions,coverage=dict(gen3_context_maps=21,johto_maps_audited=['New Bark','Route 29','Cherrygrove','Route 30','Route 31','Violet','Route 36'],no_tall_cliff_family=['New Bark','Violet'],hgss_texture_sets=119,hgss_original_set_count=106,platinum_texture_sets=len(list((donors/'pokeplatinum/res/field/maps/texture_sets').glob('*.nsbtx'))),raw_source_entries=len(raw),distinct_source_images=len({r["pixel_sha256"] for r in raw}),unresolved_palette_pairs=json.loads((S/'errors.json').read_text())),records=records)
    (P/'catalog.json').write_text(json.dumps(manifest,indent=2)+'\n')
    groups=['Start here','Current Johto','Existing conversions','Emerald','FireRed','HGSS map context','HGSS families','Sinnoh families','HGSS source pieces','Platinum source pieces','Earlier Sinnoh imports','Related interior surfaces']
    cards=[]
    for r in records:
        im=images[r['id']];z=max(1,min(4,384//im.width,256//im.height));source=html.escape(json.dumps(r['source'],indent=2));links=''
        if r.get('full'):links+=f'<a href="{r["full"]}" target="_blank">Full map</a> '
        if r.get('metatiles'):links+=f'<a href="{r["metatiles"]}" target="_blank">Source metatiles</a>'
        cards.append(f'<article data-group="{r["group"]}" data-id="{r["id"]}"><h2>{html.escape(r["id"]+" · "+r["title"])}</h2><div class="preview"><img src="{data(im)}" width="{im.width*z}" height="{im.height*z}" alt="{html.escape(r["title"])}"></div><p>{html.escape(r["note"])}</p><div>{links} <a href="{r["image"]}" target="_blank">Native image</a></div><details><summary>Source and dimensions · {im.width} × {im.height}</summary><pre>{source}</pre></details></article>')
    body='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Johto rock and mountain review</title><style>
*{box-sizing:border-box}body{margin:0;background:#15212b;color:#e8eef1;font:15px system-ui}header{padding:24px 28px;background:#20313e}h1{margin:0 0 10px;font-size:28px}p{line-height:1.5}header p{max-width:1100px;color:#c6d5df}nav{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0}button,input{font:inherit;border:1px solid #6c8495;border-radius:6px;padding:8px 10px;background:#2b4151;color:white}button{cursor:pointer}button[aria-pressed=true]{background:#c7dfcc;color:#12242a}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:18px;padding:24px}article{padding:18px;background:#223440;border:1px solid #425966;border-radius:10px}h2{font-size:17px;min-height:42px;margin:0 0 14px}.preview{min-height:270px;overflow:auto;display:flex;align-items:center;justify-content:center;background:repeating-conic-gradient(#34444e 0% 25%,#293842 0% 50%) 0/16px 16px}.preview img{image-rendering:pixelated;max-width:none}article p{font-size:13px;color:#bfd0da;min-height:56px}a{color:#a3d9ff;margin-right:10px}details{margin-top:16px;font-size:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere}article[hidden]{display:none}#intro{padding:20px 28px;background:#263c43}#intro img{width:min(100%,1212px);image-rendering:pixelated}#count{margin-left:14px;color:#d2e4d9}footer{padding:24px 28px;color:#b7cbd7}</style>
<header><h1>Rock faces & mountains</h1><p>Compare the original Gen 3 maps, our Johto conversions, and original Gen 4 source artwork. Start with the overview, then select a collection. Use the IDs when choosing a style. All images use nearest-neighbor enlargement.</p><p><strong>This is the comparison stage.</strong> No artwork has been standardized or installed. Raw DS textures show unlit source colors and texture layouts; they are not finished GBA tiles. Source maps show how the art looks in context.</p><nav>NAV</nav><input id="search" type="search" placeholder="Find an ID or texture name"><span id="count"></span></header>
<section id="intro"><p><strong>Read each row left to right:</strong> original GBA example → current Johto conversion → original HGSS map. Then compare the family sheets. We can choose a face, top/cap, edge, base transition and cave entrance separately.</p><img src="OVERVIEW" alt="Original GBA, current Johto and original HGSS map comparison"></section><main>CARDS</main><footer>Read-only reference collection. Original game artwork: Game Freak / Nintendo / Creatures. New Bark and Violet were audited but do not introduce a separate tall-cliff family. Interior-wall textures and earlier Sinnoh imports are separated from the natural Johto rock collections.</footer><script>
const cards=[...document.querySelectorAll('article')];let group='Start here';function show(){let q=document.querySelector('#search').value.toLowerCase(),n=0;for(let c of cards){let ok=(group==='Start here'?false:c.dataset.group===group)&&c.textContent.toLowerCase().includes(q);c.hidden=!ok;n+=ok}document.querySelector('#intro').hidden=group!=='Start here';document.querySelector('#count').textContent=group==='Start here'?'Compare shapes first; palettes can be chosen separately.':n+' entries'}document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{group=b.dataset.group;document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-pressed',x===b));show()});document.querySelector('#search').oninput=show;show();</script></html>'''
    nav=''.join(f'<button data-group="{g}" aria-pressed="{str(i==0).lower()}">{g}</button>' for i,g in enumerate(groups))
    body=body.replace('NAV',nav).replace('OVERVIEW',data(Image.open(P/'review/comparison.png'))).replace('CARDS',''.join(cards));(P/'review.html').write_text(body)
    print(json.dumps(dict(entries=len(records),source_pieces=len(raw),native_maps=21,families=len(FAMILIES)),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--donors',type=Path,required=True);parser.add_argument('--engine',type=Path,required=True);a=parser.parse_args();main(a.donors,a.engine)
