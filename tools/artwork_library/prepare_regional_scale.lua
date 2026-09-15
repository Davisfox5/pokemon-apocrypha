-- Native Aseprite conversion and targeted pixel row/column reduction.
-- Original costume colors, faces and lower foot rows are preserved.
local root=app.params.root
local out=root..'/gba/art/regional-scale-v1/prepared/'
local pc=app.pixelColor
local function q(v) local n=math.floor(v*31/255+0.5); return (n<<3)|(n>>2) end
local jobs={
 {name='gold',file='gba/art/johto-cast-v1/prepared/gold.png',rows={13,25},cols={9,10,20}},
 {name='silver',file='gba/art/johto-cast-v1/prepared/silver.png',rows={7,11,16,26,28},cols={9,11,19,23}},
 {name='kestra',file='gba/art/johto-cast-v1/prepared/kestra.png',rows={6,10,14,25,28},cols={9,11,19,23}},
 {name='hoenn',file='artwork-library/emerald-hoenn/overworld-people/man_1.png',gen3=true},
 {name='kanto',file='artwork-library/firered-kanto/overworld-people/youngster.png',gen3=true},
 {name='johto',file='artwork-library/heartgold-johto/overworld-sprites/0115_gsboy2.png',dy=1,rows={11,15,25},cols={10,21}},
 {name='sinnoh',file='gba/art/regional-scale-v1/sources/platinum-model-4.png',dy=1,rows={10,14,25},cols={10,21}},
 {name='unova',file='gba/art/regional-scale-v1/sources/bw-npcs.png',bw=true,rows={5,7,10,12,14,24,27},cols={9,11,19,23}}
}
for _,job in ipairs(jobs) do
 local src=Sprite{fromFile=root..'/'..job.file}; local im=src.cels[1].image;local pos=src.cels[1].position
 local function rgba(x,y)
  x=x-pos.x;y=y-pos.y
  if x<0 or x>=im.width or y<0 or y>=im.height then return 0 end
  local v=im:getPixel(x,y)
  if src.colorMode==ColorMode.INDEXED then
   if v==src.transparentColor then return 0 end
   local c=src.palettes[1]:getColor(v);return pc.rgba(q(c.red),q(c.green),q(c.blue),255)
  end
  if pc.rgbaA(v)==0 then return 0 end
  return pc.rgba(q(pc.rgbaR(v)),q(pc.rgbaG(v)),q(pc.rgbaB(v)),255)
 end
 local bg=rgba(0,0)
 local sheet=Image(32,384,ColorMode.RGB);local original=Image(32,384,ColorMode.RGB)
 local cr,rr={},{};for _,x in ipairs(job.cols or {}) do cr[x]=true end;for _,y in ipairs(job.rows or {}) do rr[y]=true end
 for f=0,11 do
  local raw=Image(32,32,ColorMode.RGB)
  for y=0,31 do for x=0,31 do
   local sx,sy=x,f*32+y;local valid=true
   if job.gen3 then
    local map={1,2,7,8,2,7,8,5,6,0,3,4};local mir=(f>=4 and f<=6)
    local xx=x-8;if mir then xx=15-xx end
    valid=xx>=0 and xx<16;sx=map[f+1]*16+xx;sy=y
   elseif job.bw then
    local map={0,6,7,8,9,10,11,1,2,3,4,5};local n=map[f+1];sx=(n%3)*32+x;sy=math.floor(n/3)*32+y
   end
   local v=valid and rgba(sx,sy) or 0
   if job.bw and v==bg then v=0 end
   if y+(job.dy or 0)<32 then raw:drawPixel(x,y+(job.dy or 0),v) end
  end end
  original:drawImage(raw,Point(0,f*32))
  local yy=#(job.rows or {})
  for y=0,31 do if not rr[y] then
   local xx=math.floor(#(job.cols or {})/2)
   for x=0,31 do if not cr[x] then local dy=(job.name=='gold' and f==9) and 2 or 0;local v=raw:getPixel(x,y);if yy+dy<32 then sheet:drawPixel(xx,f*32+yy+dy,v) else assert(pc.rgbaA(v)==0,'Foot clipping') end;xx=xx+1 end end
   yy=yy+1
  end end
 end
 local orig=Sprite(32,384,ColorMode.RGB);orig.cels[1].image=original;orig:saveAs(root..'/gba/art/regional-scale-v1/sourceframes/'..job.name..'.png');orig:close()
 local dst=Sprite(32,384,ColorMode.RGB);dst.cels[1].image=sheet
 dst:saveAs(out..job.name..'.png');dst:saveAs(out..job.name..'.aseprite');dst:close();src:close()
 print(job.name..': prepared 12 anchored frames')
end
