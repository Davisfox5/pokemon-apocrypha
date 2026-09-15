// Porymap custom script: when CherrygroveCity opens, show the collision view
// and save the map through Porymap itself, for an editor round-trip check.
function tryCall(label, fn) {
    try { fn(); utility.log('claude-roundtrip: ' + label + ' ok'); return true; }
    catch (e) { try { utility.log('claude-roundtrip: ' + label + ' failed: ' + e); } catch (e2) {} return false; }
}
export function onMapOpened(mapName) {
    if (mapName !== 'CherrygroveCity') return;
    tryCall('collision view', function () { utility.setMapViewTab(1); });
    tryCall('map.save', function () { map.save(); }) || tryCall('utility.save', function () { utility.save(); });
}
