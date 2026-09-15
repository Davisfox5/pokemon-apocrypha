// Porymap custom script: read CherrygroveCity back through Porymap's own parser and
// log a collision/metatile summary so it can be compared with the build's structure.json.
export function onMapOpened(mapName) {
    if (mapName !== 'CherrygroveCity') return;
    try { utility.setMapViewTab(1); } catch (e) {}
    var w = map.getWidth(), h = map.getHeight(), blocked = 0, sea = 0, seaBlocked = 0, secondary = 0;
    for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) {
        var c = map.getCollision(x, y), m = map.getMetatileId(x, y);
        if (c) blocked++;
        if (m >= 512) secondary++;
        if (m === 0x170) { sea++; if (c) seaBlocked++; }
    }
    var doors = [[50,17],[39,14],[29,11],[32,24],[36,7],[44,7]], d = [];
    for (var i = 0; i < doors.length; i++) d.push([doors[i][0], doors[i][1], map.getMetatileId(doors[i][0], doors[i][1]), map.getCollision(doors[i][0], doors[i][1]), map.getElevation(doors[i][0], doors[i][1])]);
    utility.log('claude-verify ' + JSON.stringify({width: w, height: h, blocked: blocked, passable: w * h - blocked, secondary_metatile_cells: secondary,
        sea_cells: sea, sea_blocked: seaBlocked, spawn_collision: map.getCollision(50, 18), doors: d}));
}
