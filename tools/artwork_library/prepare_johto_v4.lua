-- Native extraction masks for the HGSS reference's building silhouettes.
-- Existing authored roof/wall pixels are copied unchanged; scenery stays transparent.
local root=app.params.root;local pc=app.pixelColor
local src=Sprite{fromFile=root..'/gba/art/johto-v1/references/cherrygrove-hgss.png'}
local im=src.cels[1].image
local jobs={
 {name='sign',x=662,y=134,w=16,h=24,poly={{1,3},{15,3},{15,18},{9,18},{9,23},{4,23},{4,18},{1,18}}},
 {name='house',x=528,y=112,w=80,h=96,poly={{2,23},{40,6},{70,6},{70,65},{67,65},{67,79},{12,79},{12,77},{4,77}}},
 {name='gold_house',x=688,y=136,w=96,h=96,poly={{18,8},{28,3},{40,8},{45,6},{86,20},{89,79},{21,79},{21,84},{8,84},{8,57},{17,57}}},
 {name='mart',x=656,y=16,w=96,h=80,poly={{4,13},{13,6},{65,6},{72,12},{72,24},{91,20},{95,47},{73,52},{73,66},{63,72},{9,72},{3,65}}},
 {name='center',x=784,y=8,w=96,h=96,poly={{3,9},{9,4},{77,4},{83,10},{83,63},{71,72},{62,72},{62,87},{29,87},{23,79},{9,76},{3,69}}}
}
local function inside(x,y,p)
 local yes=false;local j=#p
 for i=1,#p do local a,b=p[i],p[j];if (a[2]>y)~=(b[2]>y) and x<(b[1]-a[1])*(y-a[2])/(b[2]-a[2])+a[1] then yes=not yes end;j=i end
 return yes
end
for _,j in ipairs(jobs) do
 local d=Sprite(j.w,j.h,ColorMode.RGB);local q=Image(j.w,j.h,ColorMode.RGB)
 for y=0,j.h-1 do for x=0,j.w-1 do if inside(x+0.5,y+0.5,j.poly) then local v=im:getPixel(j.x+x,j.y+y);local r,g,b=pc.rgbaR(v),pc.rgbaG(v),pc.rgbaB(v);local ground=(g>r*1.15 and g>b*1.08) or (r>180 and g>165 and b<170 and r-g<55);if not ground then q:drawPixel(x,y,v) end end end end
 -- Remove disconnected remnants of the reference's surrounding path/shadow.
 local seen,best={},{}
 for yy=0,j.h-1 do for xx=0,j.w-1 do local k=yy*j.w+xx
  if not seen[k] and pc.rgbaA(q:getPixel(xx,yy))>0 then
   local queue={k};local start=1;seen[k]=true
   while start<=#queue do local t=queue[start];start=start+1;local x=t%j.w;local y=math.floor(t/j.w)
    for _,off in ipairs({{-1,0},{1,0},{0,-1},{0,1}}) do local a,b=x+off[1],y+off[2];local v=b*j.w+a
     if a>=0 and a<j.w and b>=0 and b<j.h and not seen[v] and pc.rgbaA(q:getPixel(a,b))>0 then seen[v]=true;queue[#queue+1]=v end
    end
   end
   if #queue>#best then best=queue end
  end
 end end
 local keep={};for _,k in ipairs(best) do keep[k]=true end
 for y=0,j.h-1 do for x=0,j.w-1 do if not keep[y*j.w+x] then q:drawPixel(x,y,0) end end end
 d.cels[1].image=q;d:saveAs(root..'/gba/art/johto-v4/prepared/'..j.name..'.png');d:saveAs(root..'/gba/art/johto-v4/prepared/'..j.name..'.aseprite');d:close()
end
src:close()
