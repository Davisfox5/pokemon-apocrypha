-- Native Aseprite cleanup and frame assembly. Originals remain untouched.
local root=app.params.root
local out=root..'/gba/art/johto-cast-v1/prepared/'
local jobs={
 {name='gold',file='gold_adult_ow_grid.png',cols=6,frames={0,1,2,3,4,5,6,7,8,11,12,13}},
 {name='silver',file='silver_adult_ow.png',cols=12,frames={0,1,2,3,4,5,6,7,8,9,10,11}},
 {name='kestra',file='kestra_ow.png',cols=12,frames={0,1,2,3,4,5,6,7,8,9,10,11}}
}
local function quant(v) local q=math.floor(v*31/255+0.5); return (q<<3)|(q>>2) end
for _,job in ipairs(jobs) do
 local src=Sprite{fromFile=root..'/assets/src/trainers/overworld/'..job.file}
 local im=src.cels[1].image
 local pos=src.cels[1].position
 local frames={}
 for _,f in ipairs(job.frames) do
  local data={}
  for y=0,31 do
   data[y]={}
   for x=0,31 do
    local sx=f%job.cols*32+x-pos.x
    local sy=math.floor(f/job.cols)*32+y-pos.y
    data[y][x]=(sx>=0 and sx<im.width and sy>=0 and sy<im.height) and im:getPixel(sx,sy) or 0
   end
  end
  frames[#frames+1]=data
 end
 local changed=0
 if job.name=='gold' then
  -- Consolidate the noisy front cap crown; retain its gold brim and outline.
  local idle=frames[10]
  for y=8,15 do for x=0,31 do
   if idle[y][x]==2 then idle[y][x]=5;changed=changed+1
   elseif idle[y][x]==9 then idle[y][x]=4;changed=changed+1 end
  end end
  -- Same cap/head across the two south steps, preserving the original bob
  -- and lateral sway. Face, arms, torso and feet below row 19 remain authored.
  for f=11,12 do
   local dx=(f==11) and -1 or 1
   for y=0,19 do for x=0,31 do
    local sx=x-dx;local value=(y>=1 and sx>=0 and sx<32) and idle[y-1][sx] or 0
    if frames[f][y][x]~=value then changed=changed+1 end
    frames[f][y][x]=value
   end end
  end
 elseif job.name=='silver' then
  -- Remove residual teen-Silver hair reds/purple from the lower coat and
  -- trousers. Hair and the intentionally crimson shoulder mantle are intact.
  for _,data in ipairs(frames) do for y=25,29 do for x=0,31 do
   local v=data[y][x]
   if v==3 then data[y][x]=12;changed=changed+1
   elseif v==2 or (v==8 and y>=26) then data[y][x]=13;changed=changed+1 end
  end end end
 end
 local dst=Sprite(32,384,ColorMode.RGB)
 local sheet=Image(32,384,ColorMode.RGB)
 local palette=src.palettes[1]
 for f,data in ipairs(frames) do for y=0,31 do for x=0,31 do
  local v=data[y][x]
  if v~=0 then
   assert(y+1<32,'Foot would be clipped')
   local c=palette:getColor(v)
   sheet:drawPixel(x,(f-1)*32+y+1,app.pixelColor.rgba(quant(c.red),quant(c.green),quant(c.blue),255))
  end
 end end end
 dst.cels[1].image=sheet
 dst:saveAs(out..job.name..'.png')
 dst:saveAs(out..job.name..'.aseprite')
 print(job.name..': '..changed..' indexed-pixel repairs; 12 frames; fixed +1px anchor; RGB555 palette')
 dst:close();src:close()
end
