-- Preserve editable native-sized art alongside generated sources.
local root=app.params.root
for _,name in ipairs({'house','center','mart','tree','cliff','island'}) do
 local s=Sprite{fromFile=root..'/gba/art/johto-restart/native/'..name..'.png'}
 s:saveAs(root..'/gba/art/johto-restart/prepared/'..name..'.aseprite');s:close()
end
